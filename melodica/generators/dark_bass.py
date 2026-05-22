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
generators/dark_bass.py — Deep ominous bass generator.

Style: Downtempo, trip-hop, dark ambient, industrial, dub, dark techno.

Creates slow, heavy bass patterns in low registers with emphasis on
minor tonalities, tritone movement, and deliberate rhythmic weight.

Modes:
    "doom"        — ultra-slow root movement, heavy sustained notes
    "trip_hop"    — syncopated, sparse, half-time feel
    "industrial"  — mechanical, repetitive, percussive
    "dub"         — deep sub-bass with space and echo gaps
    "dark_pulse"  — rhythmic pulsing on minor intervals
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
class DarkBassGenerator(PhraseGenerator):
    """
    Deep ominous bass generator.

    mode:
        Bass style. See module docstring.
    octave:
        Base octave (2 = very deep, 3 = standard bass).
    note_duration:
        Base note duration in beats.
    velocity_level:
        Base velocity (0.0-1.0).
    movement:
        How pitches change between chords:
        "root_only" — always chord root
        "root_fifth" — alternate root and fifth
        "chromatic" — chromatic passing tones
        "tritone_walk" — tritone-based movement
    """

    name: str = "Dark Bass Generator"
    mode: str = "doom"
    octave: int = 2
    note_duration: float = 4.0
    velocity_level: float = 0.7
    movement: str = "root_only"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "doom",
        octave: int = 2,
        note_duration: float = 4.0,
        velocity_level: float = 0.7,
        movement: str = "root_only",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if mode not in ("doom", "trip_hop", "industrial", "dub", "dark_pulse"):
            raise ValueError(f"Unknown dark bass mode: {mode!r}")
        self.mode = mode
        self.octave = max(1, min(4, octave))
        self.note_duration = max(0.5, min(16.0, note_duration))
        self.velocity_level = max(0.1, min(1.0, velocity_level))
        self.movement = movement
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
        t = 0.0
        prev_pitch = key.root + self.octave * 12
        step = 0

        while t < duration_beats:
            chord = chord_at(chords, t)
            pcs = chord.pitch_classes()
            if not pcs:
                t += self.note_duration
                continue

            pitch = self._pick_pitch(pcs, prev_pitch, step)
            pitch = max(0, min(127, pitch))
            vel = self._vel(t, duration_beats, step)
            dur = self._dur(t, duration_beats)

            if t + dur > duration_beats:
                dur = duration_beats - t

            # 1. Timing Jitter (scaled by velocity)
            jitter = random.uniform(-0.005, 0.005) * (1.5 - vel / 127.0)
            start_h = max(0.0, t + jitter)
            dur_h = max(0.1, dur)

            # 2. Continuous Expression Modeling
            expression = {}
            steps = 12

            # CC 74: Low-End Growl LFO (Doom & Industrial) or decaying cutoff
            cc74_list = []
            base_cutoff = 40 if self.mode == "dub" else 65
            freq_growl = 7.5  # Growl speed in Hz
            for s in range(steps + 1):
                progress = s / steps
                t_rel = progress * dur_h
                if self.mode in ("doom", "industrial"):
                    # Low-end saturation growl LFO modulation
                    cutoff_val = base_cutoff + int(12 * math.sin(2 * math.pi * freq_growl * t_rel))
                elif self.mode == "trip_hop":
                    cutoff_val = base_cutoff + int(25 * (1.0 - progress ** 0.5))
                else:
                    cutoff_val = base_cutoff
                cc74_list.append((round(t_rel, 6), max(1, min(127, cutoff_val))))
            expression[74] = cc74_list

            # CC 11: Dynamic volume breathing sweeps
            cc11_list = []
            for s in range(steps + 1):
                progress = s / steps
                t_rel = progress * dur_h
                if self.mode == "doom":
                    # Swelling crescendo
                    val = int(60 + 55 * progress)
                elif self.mode == "dub":
                    # Rhythmic sub swell
                    val = int(80 + 35 * math.sin(math.pi * progress))
                elif self.mode == "trip_hop":
                    # Decay
                    val = int(120 - 70 * (progress ** 0.6))
                else:
                    val = 110
                cc11_list.append((round(t_rel, 6), max(1, min(127, val))))
            expression[11] = cc11_list

            # Pitch Bend: Subterranean release falls/slides
            pb_list = []
            slide_start_t = dur_h * 0.82
            for s in range(steps + 1):
                progress = s / steps
                t_rel = progress * dur_h
                if t_rel < slide_start_t:
                    pb_val = 0
                else:
                    # Slide down to -2400 units (almost a whole step down)
                    slide_progress = (t_rel - slide_start_t) / (dur_h - slide_start_t)
                    pb_val = int(-2400 * (slide_progress ** 1.8))
                pb_list.append((round(t_rel, 6), pb_val))
            expression["pitch_bend"] = pb_list

            note = NoteInfo(
                pitch=pitch,
                start=round(start_h, 6),
                duration=round(dur_h, 6),
                velocity=vel,
            )
            note.expression = expression
            notes.append(note)

            prev_pitch = pitch
            t += self._gap()
            step += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _pick_pitch(self, pcs: list[int], prev: int, step: int) -> int:
        root = pcs[0]
        base = root + self.octave * 12

        if self.movement == "root_only":
            return nearest_pitch(root, base)
        elif self.movement == "root_fifth":
            pc = root if step % 2 == 0 else (root + 7) % 12
            return nearest_pitch(pc, base)
        elif self.movement == "chromatic":
            offset = step % 3
            return nearest_pitch((root + offset) % 12, base)
        elif self.movement == "tritone_walk":
            pc = root if step % 2 == 0 else (root + 6) % 12
            return nearest_pitch(pc, base)
        return nearest_pitch(root, base)

    def _vel(self, t: float, dur: float, step: int) -> int:
        base = int(self.velocity_level * 100)
        if self.mode == "doom":
            return max(1, min(127, base + random.randint(-5, 5)))
        elif self.mode == "trip_hop":
            # Ghost notes on off-beats
            if step % 2 == 1:
                return max(1, min(127, int(base * 0.6)))
            return max(1, min(127, base))
        elif self.mode == "industrial":
            return max(1, min(127, base + random.randint(-15, 15)))
        elif self.mode == "dub":
            return max(1, min(127, base))
        elif self.mode == "dark_pulse":
            return max(1, min(127, base + (10 if step % 2 == 0 else -10)))
        return base

    def _dur(self, t: float, total: float) -> float:
        if self.mode == "doom":
            return self.note_duration
        elif self.mode == "trip_hop":
            return self.note_duration * 0.75
        elif self.mode == "industrial":
            return self.note_duration * 0.5
        elif self.mode == "dub":
            return self.note_duration * 1.5
        return self.note_duration

    def _gap(self) -> float:
        if self.mode == "doom":
            return self.note_duration
        elif self.mode == "trip_hop":
            return self.note_duration
        elif self.mode == "industrial":
            return self.note_duration * 0.5
        elif self.mode == "dub":
            return self.note_duration * 2.0
        elif self.mode == "dark_pulse":
            return self.note_duration * 0.5
        return self.note_duration
