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
generators/strings_legato.py — Legato string section generator.

Layer: Application / Domain
Style: Film scoring, classical, romantic, ambient.

Legato strings connect notes with smooth portamento, creating the
singing quality essential for cinematic string writing. Each note
leads into the next with minimal attack re-articulation.

Section sizes:
    "solo"     — single instrument (violin, cello)
    "ensemble" — small section (3–5 players)
    "full"     — full string section (12+ players)
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class StringsLegatoGenerator(PhraseGenerator):
    """
    Legato string section generator.

    section_size:
        "solo", "ensemble", "full"
    portamento_speed:
        Duration of the slide between notes (in beats). 0 = no slide.
    dynamic_shape:
        "crescendo", "diminuendo", "cresc_dim", "flat"
    interval_preference:
        Preferred intervals between consecutive notes: "step" (1–2 semitones),
        "leap" (3–7), "wide" (8+), "mixed"
    vibrato_amount:
        0.0–1.0, velocity variation to simulate vibrato.
    """

    name: str = "Strings Legato Generator"
    section_size: str = "ensemble"
    portamento_speed: float = 0.15
    dynamic_shape: str = "cresc_dim"
    interval_preference: str = "step"
    vibrato_amount: float = 0.1
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        section_size: str = "ensemble",
        portamento_speed: float = 0.15,
        dynamic_shape: str = "cresc_dim",
        interval_preference: str = "step",
        vibrato_amount: float = 0.1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.section_size = section_size
        self.portamento_speed = max(0.0, min(0.5, portamento_speed))
        self.dynamic_shape = dynamic_shape
        self.interval_preference = interval_preference
        self.vibrato_amount = max(0.0, min(1.0, vibrato_amount))
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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else mid
        last_chord: ChordLabel | None = None
        total_events = len(events)

        for i, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitch = self._pick_pitch(chord, key, prev_pitch)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            # Dynamic shape
            progress = i / max(total_events - 1, 1)
            vel = self._dynamic_velocity(progress)
            # Vibrato simulation
            vel += random.randint(-int(self.vibrato_amount * 8), int(self.vibrato_amount * 8))
            vel = max(1, min(127, vel))

            # Portamento: slide note before target
            expression = {}
            if self.portamento_speed > 0 and abs(pitch - prev_pitch) > 1:
                slide_dur = min(self.portamento_speed, event.duration * 0.5)
                pb_range = 12
                diff_semitones = prev_pitch - pitch
                steps = 10
                pb_list = []
                for s in range(steps + 1):
                    t_rel = (s / steps) * slide_dur
                    factor = 1.0 - (s / steps)
                    bend = int(diff_semitones * factor * (8192.0 / pb_range))
                    bend = max(-8192, min(8191, bend))
                    pb_list.append((t_rel, bend))
                expression["pitch_bend"] = pb_list

            # Add dynamic vibrato LFO sweep on CC 1 (Modulation Wheel) for long notes
            if event.duration >= 1.0:
                lfo_freq = 6.0  # 6Hz typical vibrato speed
                steps = int(event.duration * 20)
                steps = max(5, steps)
                cc1_list = []
                for s in range(steps + 1):
                    t_rel = (s / steps) * event.duration
                    # Vibrato builds up: fades in over the first 1.0 second, then oscillates
                    vibrato_fade_in = min(1.0, t_rel)
                    val = int(vibrato_fade_in * 30 * (0.5 + 0.5 * math.sin(2 * math.pi * lfo_freq * t_rel)))
                    cc1_list.append((t_rel, max(0, min(127, val))))
                expression[1] = cc1_list

            note = NoteInfo(
                pitch=pitch,
                start=round(event.onset, 6),
                duration=event.duration,
                velocity=vel,
            )
            if expression:
                note.expression = expression
            notes.append(note)

            # Ensemble/full: add divisi voices
            if self.section_size in ("ensemble", "full"):
                divisi_count = 2 if self.section_size == "ensemble" else 3
                for d in range(1, divisi_count):
                    div_pitch = pitch + random.choice([-3, -4, 3, 4]) * d
                    div_pitch = max(
                        self.params.key_range_low, min(self.params.key_range_high, div_pitch)
                    )
                    
                    # Humanize onset start times and durations to prevent Harmonic Fusion / Masking
                    div_jitter = random.uniform(-0.015, 0.015)
                    div_start = max(0.0, event.onset + div_jitter)
                    div_duration = max(0.05, event.duration + random.uniform(-0.02, 0.02))
                    
                    notes.append(
                        NoteInfo(
                            pitch=div_pitch,
                            start=round(div_start, 6),
                            duration=round(div_duration, 6),
                            velocity=max(1, int(vel * 0.7)),
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

    def _pick_pitch(self, chord: ChordLabel, key: Scale, prev: int) -> int:
        pcs = chord.pitch_classes()
        if not pcs:
            return prev

        if self.interval_preference == "step":
            # Nearest chord tone within a step of prev
            candidates = [nearest_pitch(int(pc), prev) for pc in pcs]
            candidates = [p for p in candidates if abs(p - prev) <= 2]
            if candidates:
                return random.choice(candidates)
        elif self.interval_preference == "leap":
            candidates = [
                nearest_pitch(int(pc), prev + random.choice([-5, -3, 3, 5])) for pc in pcs
            ]
            return min(candidates, key=lambda p: abs(p - prev))
        elif self.interval_preference == "wide":
            candidates = [
                nearest_pitch(int(pc), prev + random.choice([-12, -8, 8, 12])) for pc in pcs
            ]
            return min(candidates, key=lambda p: abs(p - prev))

        # Mixed
        pc = random.choice(pcs)
        return nearest_pitch(int(pc), prev)

    def _dynamic_velocity(self, progress: float) -> int:
        base = int(45 + self.params.density * 25)
        if self.dynamic_shape == "crescendo":
            return int(base * (0.6 + 0.4 * progress))
        elif self.dynamic_shape == "diminuendo":
            return int(base * (1.0 - 0.4 * progress))
        elif self.dynamic_shape == "cresc_dim":
            factor = 0.6 + 0.4 * (1.0 - abs(2.0 * progress - 1.0))
            return int(base * factor)
        return base

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(2.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += 2.0
        return events
