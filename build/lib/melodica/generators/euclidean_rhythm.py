"""
generators/euclidean_rhythm.py — Euclidean rhythm generator (Bjorklund algorithm).

Layer: Application / Domain
Style: World music, electronic, minimalism, polyrhythmic textures.

Distributes a given number of pulses as evenly as possible across a
number of steps using Bjorklund's algorithm. This produces rhythms
found in many world music traditions: Cuban clave, West African
bell patterns, Brazilian samba, and Turkish aksak rhythms.

Pitch selection:
    "chord_root" — play the root of the current chord
    "fifth"      — play the fifth
    "octave"     — play an octave above the root

When velocity_accent is True, the first pulse of each cycle and
pulses following longer rests receive a higher velocity.
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
class EuclideanRhythmGenerator(PhraseGenerator):
    """
    Euclidean rhythm generator using Bjorklund's algorithm.

    pulses:
        Number of onset pulses to distribute (1–32).
    steps:
        Total number of steps in the pattern (1–64).
    pitch:
        Pitch strategy: "chord_root", "fifth", or "octave".
    velocity_accent:
        If True, accent pulses that follow longer rests.
    """

    name: str = "Euclidean Rhythm Generator"
    pulses: int = 5
    steps: int = 8
    pitch: str = "chord_root"
    velocity_accent: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pulses: int = 5,
        steps: int = 8,
        pitch: str = "chord_root",
        velocity_accent: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pulses = max(1, min(32, pulses))
        self.steps = max(1, min(64, steps))
        if pitch not in ("chord_root", "fifth", "octave"):
            raise ValueError(f"pitch must be 'chord_root', 'fifth', or 'octave'; got {pitch!r}")
        self.pitch = pitch
        self.velocity_accent = velocity_accent
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

        pattern = self._bjorklund(self.pulses, self.steps)
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        step_dur = duration_beats / self.steps
        cycle_dur = step_dur * self.steps
        t = 0.0

        while t < duration_beats:
            for step_idx, is_pulse in enumerate(pattern):
                onset = t + step_idx * step_dur
                if onset >= duration_beats:
                    break
                if not is_pulse:
                    continue

                chord = chord_at(chords, onset)
                if chord is None:
                    continue
                last_chord = chord

                pitch = self._pick_pitch(chord, anchor)
                pitch = max(low, min(high, pitch))

                if self.velocity_accent:
                    vel = self._accented_velocity(pattern, step_idx)
                else:
                    vel = self._velocity(False)

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=step_dur * 0.8,
                        velocity=max(1, min(127, vel)),
                    )
                )
                prev_pitch = pitch

            t += cycle_dur

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, anchor: int) -> int:
        if self.pitch == "chord_root":
            return nearest_pitch(chord.root, anchor)
        elif self.pitch == "fifth":
            return nearest_pitch((chord.root + 7) % 12, anchor)
        elif self.pitch == "octave":
            return nearest_pitch(chord.root, anchor + 12)
        return nearest_pitch(chord.root, anchor)

    def _accented_velocity(self, pattern: list[int], step_idx: int) -> int:
        prev_idx = (step_idx - 1) % len(pattern)
        is_first = step_idx == 0
        follows_rest = pattern[prev_idx] == 0

        if is_first or follows_rest:
            return self._velocity(True)
        return self._velocity(False)

    @staticmethod
    def _bjorklund(pulses: int, steps: int) -> list[int]:
        if pulses <= 0:
            return [0] * steps
        if pulses >= steps:
            return [1] * steps

        counts = []
        remainders = []
        divisor = steps - pulses
        remainders.append(pulses)
        level = 0

        while True:
            counts.append(divisor // remainders[level])
            remainders.append(divisor % remainders[level])
            divisor = remainders[level]
            level += 1
            if remainders[level] <= 1:
                break

        counts.append(divisor)

        def _build(lv: int) -> list[int]:
            if lv == -1:
                return [0]
            if lv == -2:
                return [1]
            result: list[int] = []
            for i in range(counts[lv]):
                result.extend(_build(lv - 1))
            if remainders[lv] != 0:
                result.extend(_build(lv - 2))
            return result

        pattern = _build(level)
        while len(pattern) < steps:
            pattern.append(0)
        return pattern[:steps]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        step = duration_beats / max(self.steps, 1)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=step * 0.8))
            t += step
        return events

    def _velocity(self, accented: bool) -> int:
        base = int(55 + self.params.density * 30)
        if accented:
            return min(127, int(base * 1.2))
        return base
