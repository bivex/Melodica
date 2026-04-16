# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/lead_synth.py — Monophonic synth lead generator with portamento and vibrato.

Layer: Application / Domain
Style: Trance, techno, retro, supersaw electronic leads.

Generates a monophonic lead line with configurable articulation and
expression. Portamento is simulated by overlapping notes; vibrato is
encoded as velocity modulation across sustained notes.

Styles:
    "trance"    — long legato notes with sweeping vibrato
    "techno"    — short staccato repeating patterns
    "retro"     — vintage synth with mixed articulation
    "supersaw"  — dense chords with wide vibrato

Note lengths:
    "legato"    — notes overlap slightly
    "staccato"  — short clipped notes
    "mixed"     — alternating legato and staccato
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


@dataclass
class LeadSynthGenerator(PhraseGenerator):
    """
    Monophonic synth lead with portamento and vibrato.

    style:
        Lead style: "trance", "techno", "retro", "supersaw".
    portamento:
        Glide time as fraction of note duration (0.0–1.0).
    vibrato_rate:
        Vibrato speed in cycles per beat (0.1–2.0).
    vibrato_depth:
        Vibrato depth in velocity units (0.0–1.0).
    note_length:
        Articulation: "legato", "staccato", "mixed".
    """

    name: str = "Lead Synth Generator"
    style: str = "trance"
    portamento: float = 0.15
    vibrato_rate: float = 0.3
    vibrato_depth: float = 0.2
    note_length: str = "legato"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "trance",
        portamento: float = 0.15,
        vibrato_rate: float = 0.3,
        vibrato_depth: float = 0.2,
        note_length: str = "legato",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if style not in ("trance", "techno", "retro", "supersaw"):
            raise ValueError(
                f"style must be 'trance', 'techno', 'retro', or 'supersaw'; got {style!r}"
            )
        self.style = style
        self.portamento = max(0.0, min(1.0, portamento))
        self.vibrato_rate = max(0.1, min(2.0, vibrato_rate))
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        if note_length not in ("legato", "staccato", "mixed"):
            raise ValueError(
                f"note_length must be 'legato', 'staccato', or 'mixed'; got {note_length!r}"
            )
        self.note_length = note_length
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        for i, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
            pitch = nearest_pitch(int(pc), prev_pitch)
            pitch = snap_to_scale(max(low, min(high, pitch)), key)

            dur = self._apply_articulation(event.duration, i)
            vel = self._velocity(i, event.velocity_factor)

            note = NoteInfo(
                pitch=pitch,
                start=round(event.onset, 6),
                duration=dur,
                velocity=max(1, min(127, vel)),
            )
            notes.append(note)
            prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _apply_articulation(self, base_dur: float, index: int) -> float:
        if self.note_length == "legato":
            return base_dur * (1.0 + self.portamento)
        elif self.note_length == "staccato":
            return base_dur * 0.4
        else:
            return base_dur * (1.0 if index % 2 == 0 else 0.4)

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.style == "trance":
            step = 0.5
        elif self.style == "techno":
            step = 0.25
        elif self.style == "retro":
            step = 1.0
        else:
            step = 0.5

        t, events = 0.0, []
        while t < duration_beats:
            dur = step * (1.0 if self.note_length == "legato" else 0.5)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += step
        return events

    def _velocity(self, index: int, vel_factor: float = 1.0) -> int:
        base = int(65 + self.params.density * 30)
        vib = int(self.vibrato_depth * 15 * ((-1) ** index))
        return max(1, min(127, int((base + vib) * vel_factor)))
