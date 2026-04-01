"""
generators/ragtime.py — Ragtime piano pattern generator.

Layer: Application / Domain
Style: Ragtime (Scott Joplin, James Scott, Joseph Lamb).

Ragtime combines a syncopated right-hand melody with a stride-style
left hand: bass note on beats 1 and 3, chord on beats 2 and 4.

This generator produces BOTH hands interleaved, creating a complete
ragtime texture.

Patterns:
    "classic"    — standard Joplin ragtime
    "novelty"    — novelty ragtime (more chromatic, wider range)
    "march"      — march-style ragtime (Sousa influence)
    "slow_drag"  — slow drag ragtime
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed


# Syncopation patterns: (beat_offset, duration) for right hand
SYNC_PATTERNS: dict[str, list[tuple[float, float]]] = {
    "classic": [(0.0, 0.5), (1.5, 0.5), (2.0, 0.5), (3.5, 0.5)],
    "novelty": [(0.0, 0.25), (0.75, 0.25), (1.5, 0.25), (2.0, 0.25), (2.75, 0.25), (3.5, 0.25)],
    "march": [(0.0, 0.5), (1.0, 0.5), (2.0, 0.5), (3.0, 0.5)],
    "slow_drag": [(0.0, 1.0), (1.5, 0.5), (2.5, 0.5), (3.5, 0.5)],
}


@dataclass
class RagtimeGenerator(PhraseGenerator):
    """
    Ragtime piano pattern generator.

    pattern:
        "classic", "novelty", "march", "slow_drag"
    melody_density:
        How many of the RH slots get filled (0.0–1.0).
    left_hand:
        Include left hand (bass + chord).
    right_hand:
        Include right hand (syncopated melody).
    chromatic_approach:
        Use chromatic approach notes in RH.
    """

    name: str = "Ragtime Generator"
    pattern: str = "classic"
    melody_density: float = 0.8
    left_hand: bool = True
    right_hand: bool = True
    chromatic_approach: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "classic",
        melody_density: float = 0.8,
        left_hand: bool = True,
        right_hand: bool = True,
        chromatic_approach: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.melody_density = max(0.0, min(1.0, melody_density))
        self.left_hand = left_hand
        self.right_hand = right_hand
        self.chromatic_approach = chromatic_approach
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

        notes: list[NoteInfo] = []
        low = max(28, self.params.key_range_low)
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        high = self.params.key_range_high

        prev_bass = low + 12
        prev_rh = mid
        last_chord: ChordLabel | None = None

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue
            last_chord = chord

            # Left hand: bass(1) - chord(2) - bass(3) - chord(4)
            if self.left_hand:
                for beat in range(4):
                    onset = bar_start + beat
                    if onset >= duration_beats:
                        break
                    is_bass = beat % 2 == 0
                    vel = int(self._velocity() * (1.1 if is_bass else 0.9))

                    if is_bass:
                        bass = nearest_pitch(chord.root, prev_bass)
                        bass = max(low, min(mid - 5, bass))
                        notes.append(
                            NoteInfo(
                                pitch=bass,
                                start=round(onset, 6),
                                duration=0.9,
                                velocity=max(1, min(127, vel)),
                            )
                        )
                        # Octave double
                        notes.append(
                            NoteInfo(
                                pitch=max(low, bass - 12),
                                start=round(onset, 6),
                                duration=0.9,
                                velocity=max(1, min(127, int(vel * 0.7))),
                            )
                        )
                        prev_bass = bass
                    else:
                        voicing = chord_pitches_closed(chord, mid)
                        for p in voicing:
                            notes.append(
                                NoteInfo(
                                    pitch=max(mid - 5, min(mid + 12, p)),
                                    start=round(onset, 6),
                                    duration=0.4,
                                    velocity=max(1, min(127, vel)),
                                )
                            )

            # Right hand: syncopated melody
            if self.right_hand:
                sync = SYNC_PATTERNS.get(self.pattern, SYNC_PATTERNS["classic"])
                rh_pcs = chord.pitch_classes() + [chord.root]

                for offset, dur in sync:
                    onset = bar_start + offset
                    if onset >= duration_beats:
                        break
                    if random.random() > self.melody_density:
                        continue

                    pc = random.choice(rh_pcs)
                    pitch = nearest_pitch(int(pc), prev_rh)

                    # Keep RH above mid
                    while pitch < mid + 5:
                        pitch += 12
                    pitch = min(high, pitch)

                    # Chromatic approach
                    if self.chromatic_approach and offset > 0 and random.random() < 0.3:
                        approach_pitch = pitch - 1
                        if approach_pitch >= mid:
                            notes.append(
                                NoteInfo(
                                    pitch=approach_pitch,
                                    start=round(onset - 0.12, 6),
                                    duration=0.1,
                                    velocity=max(1, int(self._velocity() * 0.6)),
                                )
                            )

                    vel = int(self._velocity() * 1.05)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=dur * 0.9,
                            velocity=max(1, min(127, vel)),
                        )
                    )
                    prev_rh = pitch

            bar_start += 4.0

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _velocity(self) -> int:
        return int(60 + self.params.density * 35)
