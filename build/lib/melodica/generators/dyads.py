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
generators/dyads.py — DyadGenerator.

Layer: Application / Domain

motion_mode:
    "random"     — independent stepwise motion for each voice
    "parallel"   — top voice moves, bottom follows at fixed interval
    "contrary"   — voices move in opposite directions
    "oblique"    — one voice stays, other moves
"""

from __future__ import annotations

import math
import random as _random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at

MOTION_MODES = {"random", "parallel", "contrary", "oblique"}


def _snap_to_scale(pitch: int, key: Scale) -> int:
    """Snap a MIDI pitch to the nearest scale tone."""
    scale_pcs = key.degrees()
    pc = pitch % 12
    # Use circular distance to handle wraparound (e.g. C→B is 1, not 11)
    best = min(scale_pcs, key=lambda p: min(abs(pc - p), 12 - abs(pc - p)))
    return nearest_pitch(int(best), pitch)


@dataclass
class DyadGenerator(PhraseGenerator):
    """
    Generates two-voiced melodies (intervals).
    Common for horn sections or guitar double-stops.

    interval_pref: list of preferred semitones between voices (e.g. [3, 4, 7] for 3rds/5ths).
    min_interval:  minimum semitone distance between the two voices.
    motion_mode:   "random" | "parallel" | "contrary" | "oblique"
    note_range_low/high: override key range
    """

    name: str = "Dyad Generator"
    interval_pref: list[int] = field(default_factory=lambda: [3, 4, 7, 8, 12])
    min_interval: int = 3
    motion_mode: str = "random"
    note_range_low: int | None = None
    note_range_high: int | None = None
    rhythm: RhythmGenerator | None = None
    seed: int | None = None
    chord_tone_anchor: bool = True

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        interval_pref: list[int] | None = None,
        min_interval: int = 3,
        motion_mode: str = "random",
        note_range_low: int | None = None,
        note_range_high: int | None = None,
        rhythm: RhythmGenerator | None = None,
        seed: int | None = None,
        chord_tone_anchor: bool = True,
    ) -> None:
        super().__init__(params)
        self.interval_pref = interval_pref if interval_pref else [3, 4, 7, 8, 12]
        self.min_interval = min_interval
        if motion_mode not in MOTION_MODES:
            raise ValueError(
                f"motion_mode must be one of {sorted(MOTION_MODES)}; got {motion_mode!r}"
            )
        self.motion_mode = motion_mode
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self.rhythm = rhythm
        self.seed = seed
        self.chord_tone_anchor = chord_tone_anchor
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        rng = _random.Random(self.seed)

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        last_chord = chords[0]
        prev_chord: ChordLabel | None = None

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        # Start anchor
        if context is not None and context.prev_pitch is not None:
            last_top = context.prev_pitch
        else:
            last_top = nearest_pitch(chords[0].root, (low + high) // 2 + 6)
        last_bot = last_top - rng.choice(self.interval_pref)
        last_bot = max(low, last_bot)

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # 1. Move top voice
            step = rng.choice([-2, -1, 0, 1, 2])
            target_top = last_top + step

            # Chord-tone anchor
            if self.chord_tone_anchor and chord != prev_chord:
                anchored = _snap_to_scale(nearest_pitch(chord.root, target_top), key)
                if low <= anchored <= high:
                    target_top = anchored

            if not key.contains(target_top % 12):
                target_top = _snap_to_scale(target_top, key)

            # Clamp top
            if target_top < low + 12:
                target_top += 12
            if target_top > high:
                target_top -= 12

            # 2. Move bottom voice based on motion_mode
            if self.motion_mode == "parallel":
                interval = rng.choice(self.interval_pref)
                target_bot = target_top - interval
            elif self.motion_mode == "contrary":
                step_bot = -step  # opposite direction
                target_bot = last_bot + step_bot
                if not key.contains(target_bot % 12):
                    target_bot = _snap_to_scale(target_bot, key)
            elif self.motion_mode == "oblique":
                target_bot = last_bot  # stays put
            else:  # random
                interval = rng.choice(self.interval_pref)
                target_bot = target_top - interval

            # Ensure minimum separation
            if abs(target_top - target_bot) < self.min_interval:
                target_bot = target_top - self.min_interval

            # Snap bottom to key
            if not key.contains(target_bot % 12):
                target_bot = _snap_to_scale(target_bot, key)

            # Clamp bottom
            target_bot = max(low, min(high, target_bot))

            base_vel = int(60 + self.params.density * 40)
            vel = int(base_vel * event.velocity_factor)

            for p in [target_top, target_bot]:
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, vel)),
                    )
                )

            last_top = target_top
            last_bot = target_bot
            prev_chord = chord

        # Phrase arch
        notes = self._apply_phrase_arch(
            notes, duration_beats, context.phrase_position if context else 0.0
        )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.45))
            t += 0.5
        return events

    def _apply_phrase_arch(
        self,
        notes: list[NoteInfo],
        duration_beats: float,
        phrase_position: float = 0.0,
    ) -> list[NoteInfo]:
        if not notes or duration_beats <= 0:
            return notes
        arch_height = 0.3 + 0.2 * phrase_position
        for note in notes:
            progress = note.start / duration_beats
            arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
            note.velocity = max(1, min(127, int(note.velocity * arch)))
        return notes
