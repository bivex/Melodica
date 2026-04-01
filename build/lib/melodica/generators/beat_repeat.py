"""
generators/beat_repeat.py — Beat repeat / stutter generator.

Layer: Application / Domain
Style: Electronic, EDM, glitch, hip-hop, pop production.

Beat repeat chops a note into rapid repetitions that accelerate or
decelerate, creating the "stutter" effect common in electronic music.

Types:
    "accelerate"  — repetitions speed up (quarter → eighth → sixteenth)
    "decelerate"  — repetitions slow down
    "constant"    — steady rapid repetition
    "gate"        — rhythmic gate pattern
    "glitch"      — random stutter lengths
    "reverse"     — decelerating into a sustained note
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
class BeatRepeatGenerator(PhraseGenerator):
    """
    Beat repeat / stutter effect generator.

    repeat_type:
        Type of stutter pattern.
    stutter_length:
        Total duration of each stutter event in beats.
    min_subdivision:
        Minimum note length in the stutter (0.03125 = very fast).
    pitch_shift:
        If True, each repeat shifts pitch slightly (vinyl stop effect).
    gate_pattern:
        For "gate" type: list of on/off durations.
    """

    name: str = "Beat Repeat Generator"
    repeat_type: str = "accelerate"
    stutter_length: float = 2.0
    min_subdivision: float = 0.0625
    pitch_shift: bool = False
    gate_pattern: list[float] = field(default_factory=lambda: [0.25, 0.25, 0.125, 0.125])
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        repeat_type: str = "accelerate",
        stutter_length: float = 2.0,
        min_subdivision: float = 0.0625,
        pitch_shift: bool = False,
        gate_pattern: list[float] | None = None,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.repeat_type = repeat_type
        self.stutter_length = max(0.5, min(8.0, stutter_length))
        self.min_subdivision = max(0.02, min(0.25, min_subdivision))
        self.pitch_shift = pitch_shift
        self.gate_pattern = gate_pattern if gate_pattern is not None else [0.25, 0.25, 0.125, 0.125]
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

            # Pick pitch
            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
            pitch = nearest_pitch(int(pc), prev_pitch)
            pitch = max(low, min(high, pitch))

            dur = min(self.stutter_length, duration_beats - event.onset)
            if dur <= 0:
                continue

            stutter_notes = self._render_stutter(pitch, event.onset, dur, low, high)
            notes.extend(stutter_notes)
            if stutter_notes:
                prev_pitch = stutter_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_stutter(
        self, pitch: int, onset: float, dur: float, low: int, high: int
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        vel = self._velocity()
        t = onset
        end = onset + dur

        if self.repeat_type == "accelerate":
            subdivisions = [0.5, 0.25, 0.125, 0.0625]
            for sd in subdivisions:
                if t >= end:
                    break
                n_dur = min(sd, end - t)
                p = pitch
                if self.pitch_shift:
                    p = max(low, min(high, p + random.randint(-1, 1)))
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.8, velocity=vel)
                )
                t += sd

        elif self.repeat_type == "decelerate":
            subdivisions = [0.0625, 0.125, 0.25, 0.5]
            for sd in subdivisions:
                if t >= end:
                    break
                n_dur = min(sd, end - t)
                p = pitch
                if self.pitch_shift:
                    p = max(low, min(high, p + random.randint(-1, 1)))
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.8, velocity=vel)
                )
                t += sd

        elif self.repeat_type == "constant":
            sd = self.min_subdivision
            while t < end:
                n_dur = min(sd, end - t)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(t, 6), duration=n_dur * 0.8, velocity=vel)
                )
                t += sd

        elif self.repeat_type == "gate":
            pat_idx = 0
            while t < end:
                gate_dur = self.gate_pattern[pat_idx % len(self.gate_pattern)]
                n_dur = min(gate_dur, end - t)
                # Alternate: note on, note off
                if pat_idx % 2 == 0:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(t, 6), duration=n_dur * 0.8, velocity=vel)
                    )
                t += gate_dur
                pat_idx += 1

        elif self.repeat_type == "glitch":
            while t < end:
                sd = random.choice([0.0625, 0.125, 0.125, 0.25, 0.25, 0.5])
                n_dur = min(sd, end - t)
                p = pitch
                if self.pitch_shift:
                    p = max(low, min(high, p + random.choice([-2, -1, 0, 0, 1, 2])))
                v = max(1, vel + random.randint(-10, 10))
                notes.append(
                    NoteInfo(pitch=p, start=round(t, 6), duration=n_dur * 0.75, velocity=v)
                )
                t += sd

        elif self.repeat_type == "reverse":
            subdivisions = [0.0625, 0.0625, 0.125, 0.125, 0.25, 0.25, 0.5]
            for sd in subdivisions:
                if t >= end:
                    break
                n_dur = min(sd, end - t)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(t, 6), duration=n_dur * 0.9, velocity=vel)
                )
                t += sd
            # Sustained note at the end
            if t < end:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(t, 6), duration=end - t, velocity=vel)
                )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            gap = random.uniform(2.0, 4.0)
            events.append(RhythmEvent(onset=round(t, 6), duration=self.stutter_length))
            t += self.stutter_length + gap
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 35)
