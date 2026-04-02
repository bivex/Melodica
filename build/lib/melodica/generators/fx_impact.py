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
generators/fx_impact.py — FX impact / transition hit generator.

Layer: Application / Domain
Style: EDM, film scoring, trailers, pop production.

Impacts are sharp, dramatic sounds at section transitions:
booms, hits, reverse cymbals, downlifters.

Types:
    "boom"            — deep sub-bass boom
    "hit"             — orchestral/percussion hit
    "reverse_cymbal"  — reversed cymbal leading into the beat
    "downlifter"      — descending pitch sweep + noise burst
    "riser_hit"       — combination: riser + impact
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class FXImpactGenerator(PhraseGenerator):
    """
    FX impact / transition hit generator.

    impact_type:
        "boom", "hit", "reverse_cymbal", "downlifter", "riser_hit"
    tail_length:
        How long the tail/reverb of the impact lasts (in beats).
    pitch_drop:
        Semitone drop for boom/downlifter effects.
    placement:
        "downbeat" — place on beat 1 of each bar group
        "pickup" — place just before the downbeat
    """

    name: str = "FX Impact Generator"
    impact_type: str = "boom"
    tail_length: float = 2.0
    pitch_drop: int = 12
    placement: str = "downbeat"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        impact_type: str = "boom",
        tail_length: float = 2.0,
        pitch_drop: int = 12,
        placement: str = "downbeat",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.impact_type = impact_type
        self.tail_length = max(0.5, min(8.0, tail_length))
        self.pitch_drop = max(1, min(24, pitch_drop))
        self.placement = placement
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
        low = self.params.key_range_low
        last_chord = chords[-1]

        # Place impacts at section boundaries (every 4 bars)
        interval = 16.0  # every 4 bars
        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += interval
                continue

            onset = t if self.placement == "downbeat" else t - 0.5
            if onset < 0:
                t += interval
                continue

            impact_notes = self._render_impact(chord, onset, low, duration_beats)
            notes.extend(impact_notes)
            t += interval

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_impact(
        self, chord: ChordLabel, onset: float, low: int, total: float
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        vel = int(70 + self.params.density * 40)

        if self.impact_type == "boom":
            # Deep sub hit
            pitch = max(low, nearest_pitch(chord.root, low + 6))
            # Main hit
            notes.append(
                NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.5, velocity=min(127, vel))
            )
            # Pitch drop tail
            t = onset + 0.5
            for i in range(self.pitch_drop):
                if t >= total:
                    break
                drop_p = max(low, pitch - i - 1)
                notes.append(
                    NoteInfo(
                        pitch=drop_p, start=round(t, 6), duration=0.15, velocity=max(1, vel - i * 3)
                    )
                )
                t += 0.1

        elif self.impact_type == "hit":
            # Orchestral hit: multiple chord tones simultaneously
            pcs = chord.pitch_classes()
            mid = (low + self.params.key_range_high) // 2
            for pc in pcs[:4]:
                p = nearest_pitch(int(pc), mid)
                p = max(low, min(self.params.key_range_high, p))
                notes.append(
                    NoteInfo(pitch=p, start=round(onset, 6), duration=0.3, velocity=min(127, vel))
                )

        elif self.impact_type == "reverse_cymbal":
            # Build-up of noise before the hit
            t = onset - self.tail_length
            if t < 0:
                t = 0
            step = 0.0625
            while t < onset:
                progress = (t - (onset - self.tail_length)) / self.tail_length
                n_vel = int(10 + vel * 0.7 * progress)
                pitch = random.randint(70, 90)  # High metallic range
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=step,
                        velocity=max(1, n_vel),
                    )
                )
                t += step
            # The hit itself
            mid = (low + self.params.key_range_high) // 2
            notes.append(NoteInfo(pitch=mid, start=round(onset, 6), duration=0.3, velocity=vel))

        elif self.impact_type == "downlifter":
            # Descending sweep + noise burst
            start_pitch = self.params.key_range_high - 12
            end_pitch = low
            t = onset
            num_steps = self.pitch_drop
            step_dur = self.tail_length / num_steps
            for i in range(num_steps):
                if t >= total:
                    break
                progress = i / max(num_steps - 1, 1)
                pitch = int(start_pitch + (end_pitch - start_pitch) * progress)
                n_vel = int(vel * (1.0 - progress * 0.5))
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=step_dur * 0.9,
                        velocity=max(1, n_vel),
                    )
                )
                t += step_dur
                # Add noise hits
                if random.random() < 0.5:
                    noise_p = random.randint(low, self.params.key_range_high)
                    notes.append(
                        NoteInfo(
                            pitch=noise_p,
                            start=round(t, 6),
                            duration=0.05,
                            velocity=max(1, n_vel // 2),
                        )
                    )

        elif self.impact_type == "riser_hit":
            # Short riser + boom
            # Riser portion
            t = onset - self.tail_length * 0.5
            if t < 0:
                t = 0
            mid = (low + self.params.key_range_high) // 2
            while t < onset:
                pitch = random.randint(mid, self.params.key_range_high)
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=0.1, velocity=40))
                t += 0.125
            # Boom
            pitch = max(low, nearest_pitch(chord.root, low + 6))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=self.tail_length,
                    velocity=min(127, vel),
                )
            )

        return notes
