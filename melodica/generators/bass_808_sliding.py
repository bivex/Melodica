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
generators/bass_808_sliding.py — 808 sliding bass generator for trap/drill.

Layer: Application / Domain
Style: Trap, drill, hip-hop, modern rap.

Produces 808 bass patterns with characteristic pitch slides (glissando
via overlapping notes and pitch bend events). Essential for modern
trap/drill production.

Patterns:
    "trap_basic"     — standard trap 808 (beats 1, 2&, 3)
    "trap_syncopated" — displaced 808 hits with ghost notes
    "drill_sliding"  — drill-style long slides between notes
    "half_time"      — half-time 808 pattern
    "rolling"        — continuous 808 rolls

Slide types:
    "overlap"        — notes overlap creating legato slides
    "chromatic"      — chromatic walk between pitches
    "octave_jump"    — octave displacement slides
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


PATTERN_OFFSETS: dict[str, list[tuple[float, float, str]]] = {
    "trap_basic": [
        (0.0, 3.5, "hold"),
        (2.0, 1.5, "hold"),
        (2.75, 0.5, "ghost"),
    ],
    "trap_syncopated": [
        (0.0, 3.5, "hold"),
        (1.5, 0.5, "ghost"),
        (2.5, 1.0, "hold"),
        (3.5, 0.4, "ghost"),
    ],
    "drill_sliding": [
        (0.0, 1.8, "slide"),
        (2.0, 0.8, "hold"),
        (3.0, 0.8, "slide"),
    ],
    "half_time": [
        (0.0, 3.8, "hold"),
        (3.0, 0.8, "ghost"),
    ],
    "rolling": [
        (0.0, 0.9, "hold"),
        (1.0, 0.9, "hold"),
        (2.0, 0.9, "hold"),
        (3.0, 0.9, "hold"),
    ],
}


@dataclass
class Bass808SlidingGenerator(PhraseGenerator):
    """
    808 sliding bass generator for trap/drill.

    pattern:
        "trap_basic", "trap_syncopated", "drill_sliding", "half_time", "rolling"
    slide_type:
        "overlap", "chromatic", "octave_jump"
    slide_probability:
        Probability of applying a slide between consecutive notes (0.0-1.0).
    octave_range:
        Number of octaves available for the 808 (1-3).
    accent_velocity:
        Velocity multiplier for accented notes.
    ghost_velocity_ratio:
        Velocity ratio for ghost notes vs main hits.
    """

    name: str = "808 Sliding Bass Generator"
    pattern: str = "trap_basic"
    slide_type: str = "overlap"
    slide_probability: float = 0.4
    octave_range: int = 2
    accent_velocity: float = 1.1
    ghost_velocity_ratio: float = 0.55
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "trap_basic",
        slide_type: str = "overlap",
        slide_probability: float = 0.4,
        octave_range: int = 2,
        accent_velocity: float = 1.1,
        ghost_velocity_ratio: float = 0.55,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.slide_type = slide_type
        self.slide_probability = max(0.0, min(1.0, slide_probability))
        self.octave_range = max(1, min(3, octave_range))
        self.accent_velocity = max(1.0, min(1.3, accent_velocity))
        self.ghost_velocity_ratio = max(0.2, min(0.8, ghost_velocity_ratio))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(24, self.params.key_range_low)
        last_chord = chords[-1]
        prev_pitch: int | None = None

        pattern_def = PATTERN_OFFSETS.get(self.pattern, PATTERN_OFFSETS["trap_basic"])

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            root_pc = chord.root
            # 808 typically uses root, sometimes fifth
            base_pitch = max(low, min(low + 12, nearest_pitch(root_pc, low + 6)))

            for offset, dur, note_type in pattern_def:
                onset = bar_start + offset
                if onset >= duration_beats:
                    continue

                pitch = base_pitch
                # Occasional fifth variation
                if note_type == "hold" and random.random() < 0.2:
                    fifth_pc = (root_pc + 7) % 12
                    pitch = max(low, min(low + 12, nearest_pitch(fifth_pc, low + 6)))

                # Octave jump variation
                if self.slide_type == "octave_jump" and random.random() < 0.25:
                    pitch += random.choice([0, OCTAVE])
                    pitch = snap_to_scale(pitch, key)

                # Velocity
                if note_type == "ghost":
                    vel = int(80 * self.ghost_velocity_ratio)
                elif note_type == "hold" and random.random() < 0.3:
                    vel = min(MIDI_MAX, int(95 * self.accent_velocity))
                else:
                    vel = 95

                # Slide: extend note and optionally create overlap
                actual_dur = dur
                if note_type == "slide" or (
                    self.slide_type == "overlap"
                    and prev_pitch is not None
                    and prev_pitch != pitch
                    and random.random() < self.slide_probability
                ):
                    # Extend duration for slide feel
                    actual_dur = min(dur * 1.5, 3.8)
                    # Chromatic walk
                    if self.slide_type == "chromatic" and prev_pitch is not None:
                        walk_start = min(prev_pitch, pitch)
                        walk_end = max(prev_pitch, pitch)
                        step = 1 if walk_end > walk_start else -1
                        pos = walk_start
                        walk_onset = onset
                        while pos != walk_end:
                            walk_dur = actual_dur / max(1, abs(walk_end - walk_start))
                            notes.append(
                                NoteInfo(
                                    pitch=max(low, pos),
                                    start=round(walk_onset, 6),
                                    duration=walk_dur * 0.5,
                                    velocity=max(1, vel - 20),
                                )
                            )
                            pos += step
                            walk_onset += walk_dur

                notes.append(
                    NoteInfo(
                        pitch=max(low, pitch),
                        start=round(onset, 6),
                        duration=actual_dur,
                        velocity=max(1, min(MIDI_MAX, vel)),
                    )
                )
                prev_pitch = pitch

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
