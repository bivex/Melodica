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
generators/filter_sweep.py — Filter cutoff sweep simulation via velocity contour.

Layer: Application / Domain
Style: Electronic, ambient, synth design, sound design.

Simulates filter cutoff automation by producing sustained notes with
a velocity envelope that mirrors how a filter sweep would affect
perceived loudness. Opening a lowpass filter increases brightness
and apparent volume; closing it reduces both.

Sweep types:
    "lowpass_open"  — velocity rises (filter opens)
    "lowpass_close" — velocity falls (filter closes)
    "bandpass"      — velocity peaks in the middle (bandpass sweep)
    "highpass"      — velocity rises from low to high (highpass opens)

Curves:
    "linear"      — even rate of change
    "exponential" — faster change at the start/end
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class FilterSweepGenerator(PhraseGenerator):
    """
    Filter sweep simulation via velocity contour.

    sweep_type:
        Type of filter sweep: "lowpass_open", "lowpass_close", "bandpass", "highpass".
    resonance:
        Simulated resonance amount (0.0–1.0), adds velocity boost at peak.
    duration:
        Duration of each sustained sweep note in beats.
    curve:
        Envelope curve shape: "linear" or "exponential".
    """

    name: str = "Filter Sweep Generator"
    sweep_type: str = "lowpass_open"
    resonance: float = 0.5
    duration: float = 4.0
    curve: str = "linear"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        sweep_type: str = "lowpass_open",
        resonance: float = 0.5,
        duration: float = 4.0,
        curve: str = "linear",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if sweep_type not in ("lowpass_open", "lowpass_close", "bandpass", "highpass"):
            raise ValueError(
                f"sweep_type must be 'lowpass_open', 'lowpass_close', 'bandpass', or 'highpass'; "
                f"got {sweep_type!r}"
            )
        self.sweep_type = sweep_type
        self.resonance = max(0.0, min(1.0, resonance))
        self.duration = max(0.5, min(16.0, duration))
        if curve not in ("linear", "exponential"):
            raise ValueError(f"curve must be 'linear' or 'exponential'; got {curve!r}")
        self.curve = curve
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

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pcs = chord.pitch_classes()
            if not pcs:
                continue
            pc = random.choice(pcs)
            pitch = nearest_pitch(int(pc), prev_pitch)
            pitch = max(low, min(high, pitch))

            dur = min(self.duration, duration_beats - event.onset)
            if dur <= 0:
                continue

            sub_steps = max(1, int(dur / 0.25))
            sub_dur = dur / sub_steps

            for s in range(sub_steps):
                t_pos = s / max(sub_steps - 1, 1)
                vel_mod = self._sweep_value(t_pos)
                vel = self._velocity(vel_mod)
                onset = event.onset + s * sub_dur
                if onset >= duration_beats:
                    break
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=sub_dur * 0.95,
                        velocity=max(1, min(127, vel)),
                    )
                )
            prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _sweep_value(self, t: float) -> float:
        if self.curve == "exponential":
            if self.sweep_type == "lowpass_open":
                val = t**2
            elif self.sweep_type == "lowpass_close":
                val = (1.0 - t) ** 2
            elif self.sweep_type == "bandpass":
                val = 1.0 - abs(2.0 * t - 1.0) ** 0.5
            else:
                val = 1.0 - (1.0 - t) ** 2
        else:
            if self.sweep_type == "lowpass_open":
                val = t
            elif self.sweep_type == "lowpass_close":
                val = 1.0 - t
            elif self.sweep_type == "bandpass":
                val = 1.0 - abs(2.0 * t - 1.0)
            else:
                val = t

        if self.sweep_type == "bandpass":
            peak_boost = self.resonance * 0.3
            val = min(1.0, val + peak_boost * (1.0 - abs(2.0 * t - 1.0)))

        return max(0.05, min(1.0, val))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=self.duration))
            t += self.duration
        return events

    def _velocity(self, vel_mod: float) -> int:
        base = int(50 + self.params.density * 40)
        return max(1, min(127, int(base * vel_mod)))
