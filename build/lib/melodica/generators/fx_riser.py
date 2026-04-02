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
generators/fx_riser.py — FX riser / transition builder generator.

Layer: Application / Domain
Style: EDM, film scoring, pop production.

Risers build tension before a section change: ascending pitch sweeps,
noise builds, or accelerating arpeggio patterns.

Types:
    "noise"      — white noise sweep (represented as rapid random notes)
    "synth"      — synth pitch sweep (ascending chromatic)
    "orchestra"  — orchestral crescendo (strings + brass swell)
    "arp"        — accelerating arpeggio riser
    "sub_drop"   — descending sub-bass drop
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
class FXRiserGenerator(PhraseGenerator):
    """
    FX riser / transition builder generator.

    riser_type:
        "noise", "synth", "orchestra", "arp", "sub_drop"
    length_beats:
        Duration of the riser in beats.
    pitch_curve:
        "linear" — even pitch increase
        "exponential" — slow start, fast end
        "logarithmic" — fast start, slow end
    peak_velocity:
        Maximum velocity at the climax of the riser.
    """

    name: str = "FX Riser Generator"
    riser_type: str = "synth"
    length_beats: float = 4.0
    pitch_curve: str = "exponential"
    peak_velocity: int = 110
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        riser_type: str = "synth",
        length_beats: float = 4.0,
        pitch_curve: str = "exponential",
        peak_velocity: int = 110,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.riser_type = riser_type
        self.length_beats = max(1.0, min(16.0, length_beats))
        self.pitch_curve = pitch_curve
        self.peak_velocity = max(60, min(127, peak_velocity))
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
        high = self.params.key_range_high
        mid = (low + high) // 2
        last_chord = chords[-1]

        # Place risers at bar boundaries
        t = 0.0
        while t < duration_beats:
            # Find the section boundary (every 4 or 8 bars)
            riser_start = t
            riser_dur = min(self.length_beats, duration_beats - riser_start)
            if riser_dur < 1.0:
                break

            chord = chord_at(chords, riser_start)
            if chord is None:
                t += 4.0
                continue

            riser_notes = self._render_riser(chord, key, riser_start, riser_dur, low, high, mid)
            notes.extend(riser_notes)

            t += max(self.length_beats, 4.0)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_riser(
        self,
        chord: ChordLabel,
        key: Scale,
        onset: float,
        dur: float,
        low: int,
        high: int,
        mid: int,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        end = onset + dur

        if self.riser_type == "noise":
            # Rapid random notes simulating noise buildup
            t = onset
            step = 0.5
            while t < end:
                progress = (t - onset) / dur
                step = max(0.03125, 0.5 * (1.0 - progress))  # Accelerating
                vel = int(20 + (self.peak_velocity - 20) * progress)
                pitch = random.randint(mid, high)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=step * 0.8,
                        velocity=max(1, vel),
                    )
                )
                t += step

        elif self.riser_type == "synth":
            # Ascending chromatic sweep
            start_pitch = low + 12
            end_pitch = high - 12
            num_notes = max(8, int(dur / 0.125))
            t = onset
            step = dur / num_notes
            for i in range(num_notes):
                progress = i / max(num_notes - 1, 1)
                pitch = self._apply_curve(start_pitch, end_pitch, progress)
                vel = int(15 + (self.peak_velocity - 15) * progress)
                notes.append(
                    NoteInfo(
                        pitch=int(pitch),
                        start=round(t, 6),
                        duration=step * 0.9,
                        velocity=max(1, vel),
                    )
                )
                t += step

        elif self.riser_type == "orchestra":
            # String-like sustained crescendo
            root = nearest_pitch(chord.root, mid)
            for interval in [0, 7, 12]:
                pitch = root + interval
                pitch = max(low, min(high, pitch))
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=onset,
                        duration=dur,
                        velocity=max(1, int(self.peak_velocity * 0.4)),
                    )
                )

        elif self.riser_type == "arp":
            # Accelerating arpeggio
            pcs = chord.pitch_classes()
            t = onset
            step = 0.5
            idx = 0
            while t < end:
                progress = (t - onset) / dur
                step = max(0.0625, 0.5 * (1.0 - progress))
                pc = pcs[idx % len(pcs)] if pcs else chord.root
                pitch = nearest_pitch(int(pc), mid + int(progress * 24))
                pitch = max(low, min(high, pitch))
                vel = int(30 + (self.peak_velocity - 30) * progress)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=step * 0.8,
                        velocity=max(1, vel),
                    )
                )
                t += step
                idx += 1

        elif self.riser_type == "sub_drop":
            # Descending pitch sweep (drop)
            start_pitch = high - 12
            end_pitch = low
            num_notes = max(8, int(dur / 0.0625))
            t = onset
            step = dur / num_notes
            for i in range(num_notes):
                progress = i / max(num_notes - 1, 1)
                pitch = self._apply_curve(start_pitch, end_pitch, progress)
                vel = int(self.peak_velocity * (1.0 - progress * 0.3))
                notes.append(
                    NoteInfo(
                        pitch=int(pitch),
                        start=round(t, 6),
                        duration=step * 0.9,
                        velocity=max(1, int(vel)),
                    )
                )
                t += step

        return notes

    def _apply_curve(self, start: float, end: float, progress: float) -> float:
        if self.pitch_curve == "exponential":
            progress = progress**2
        elif self.pitch_curve == "logarithmic":
            progress = progress**0.5
        return start + (end - start) * progress
