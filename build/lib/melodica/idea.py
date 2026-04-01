"""
idea.py — Idea Tool: six-stage composition pipeline (§9).

Layer: Application

Rules:
  - Orchestrates generators and arrangement; no I/O.
  - Raises ValueError("lack of phrases!") if seed_phrases is empty .
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.types import (
    ArrangementSlot,
    ChordLabel,
    IdeaTrack,
    NoteInfo,
    PhraseInstance,
    Scale,
    StaticPhrase,
)
from melodica.generators import PhraseGenerator
from melodica.render_context import RenderContext


# ---------------------------------------------------------------------------
# §9.2 Main pipeline
# ---------------------------------------------------------------------------


def generate_idea(
    track: IdeaTrack,
    chords: list[ChordLabel],
    key: Scale,
    beats_per_slot: float = 8.0,
) -> list[ArrangementSlot]:
    """
    Full six-stage Idea Tool pipeline.

    Raises: ValueError if track.seed_phrases is empty.
    """
    # Stage 1 — Source collection
    if not track.seed_phrases:
        raise ValueError("lack of phrases!")
    seeds = list(track.seed_phrases)

    # Stage 2 — Selection & randomization
    if track.random_order:
        seeds = _random_rank(seeds)

    # Stage 3 — Parameter injection (already on track.generator.params by caller)

    # Stage 4 & 5 — Render each position and arrange with context threading
    total_phrases = len(track.phrase_order)
    slots: list[ArrangementSlot] = []
    render_ctx: RenderContext | None = None

    for position, label in enumerate(track.phrase_order):
        phrase_position = position / max(1, total_phrases - 1)

        ctx = RenderContext(
            prev_pitch=render_ctx.prev_pitch if render_ctx else None,
            prev_velocity=render_ctx.prev_velocity if render_ctx else None,
            phrase_position=phrase_position,
            prev_chord=render_ctx.prev_chord if render_ctx else None,
            prev_pitches=list(render_ctx.prev_pitches) if render_ctx else [],
        )

        slot_chords = _chords_for_slot(chords, position, beats_per_slot)
        notes = track.generator.render(
            chords=slot_chords,
            key=key,
            duration_beats=beats_per_slot,
            context=ctx,
        )

        # Update context from generator's end state
        gen = track.generator
        if hasattr(gen, '_last_context') and gen._last_context is not None:
            render_ctx = gen._last_context
        else:
            # Fallback: compute from notes
            if notes:
                render_ctx = ctx.with_end_state(
                    last_pitch=notes[-1].pitch,
                    last_velocity=notes[-1].velocity,
                    last_chord=slot_chords[-1] if slot_chords else None,
                )

        slots.append(ArrangementSlot(
            phrase=PhraseInstance(static=StaticPhrase(notes=notes)),
            start_beat=position * beats_per_slot,
            label=label,
        ))

    # Stage 6 — Playback handoff: return slots; caller calls notes_to_midi()
    return slots


# ---------------------------------------------------------------------------
# §9.2 Stage 2 helper
# ---------------------------------------------------------------------------


def _random_rank(items: list) -> list:
    """
    Weighted shuffle: assign each item a random score, sort descending.
    Modeled after Melodica's find_n_biggest_random_value — variety without strict uniformity.
    """
    scores = [random.random() for _ in items]
    return [x for _, x in sorted(zip(scores, items), reverse=True)]


# ---------------------------------------------------------------------------
# §9.3 Slot chord slicer
# ---------------------------------------------------------------------------


def _chords_for_slot(
    chords: list[ChordLabel],
    slot_index: int,
    beats_per_slot: float,
) -> list[ChordLabel]:
    """
    Return the subset of chords that overlap the slot window
    [slot_index * beats_per_slot, (slot_index+1) * beats_per_slot).
    Adjusts ChordLabel.start relative to slot start.
    """
    slot_start = slot_index * beats_per_slot
    slot_end = slot_start + beats_per_slot
    result: list[ChordLabel] = []

    for c in chords:
        if c.end <= slot_start or c.start >= slot_end:
            continue
        adj = ChordLabel(
            root=c.root,
            quality=c.quality,
            extensions=list(c.extensions),
            bass=c.bass,
            inversion=c.inversion,
            start=max(c.start - slot_start, 0.0),
            duration=min(c.end, slot_end) - max(c.start, slot_start),
            degree=c.degree,
            function=c.function,
        )
        result.append(adj)

    if not result and chords:
        # Fallback: use last chord before slot
        last = max(
            (c for c in chords if c.start < slot_end),
            key=lambda c: c.start,
            default=chords[0],
        )
        result = [ChordLabel(
            root=last.root,
            quality=last.quality,
            extensions=list(last.extensions),
            start=0.0,
            duration=beats_per_slot,
        )]

    return result


# ---------------------------------------------------------------------------
# §9.2 Stage 6 utility — flatten slots to NoteInfo list for MIDI export
# ---------------------------------------------------------------------------


def slots_to_notes(slots: list[ArrangementSlot]) -> list[NoteInfo]:
    """
    Flatten all ArrangementSlot phrases to an absolute-time NoteInfo list.
    Caller feeds this to notes_to_midi().
    """
    notes: list[NoteInfo] = []
    for slot in slots:
        assert slot.phrase.static is not None, (
            "slots_to_notes() expects frozen (static) phrases; "
            "call freeze() first if still parametric."
        )
        for note in slot.phrase.static.notes:
            from melodica.types import NoteInfo as NI
            notes.append(NI(
                pitch=note.pitch,
                start=note.start + slot.start_beat,
                duration=note.duration,
                velocity=note.velocity,
                absolute=note.absolute,
            ))
    return sorted(notes, key=lambda n: n.start)
