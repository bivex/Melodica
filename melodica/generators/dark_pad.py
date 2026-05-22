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
generators/dark_pad.py — Dark ambient pad generator.

Style: Downtempo, dark ambient, trip-hop, industrial, witch house, darkwave.

Creates slow, evolving pad textures with dissonant intervals, minor tonalities,
and sustained drones. Designed for dark atmospheric backgrounds.

Modes:
    "minor_pad"      — sustained minor chord tones, low velocity
    "dim_cluster"    — diminished clusters with semitone tension
    "tritone_drone"  — tritone-based sustained texture
    "chromatic_pad"  — slow chromatic movement within a dark register
    "phrygian_pad"   — Phrygian mode emphasis (b2 dark color)
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


# Dark intervals from root: minor 2nd, tritone, minor 7th, minor 3rd, minor 6th
_DARK_INTERVALS = [1, 6, 10, 3, 8]


def _dark_pitches(chord: ChordLabel, key: Scale, mode: str, count: int) -> list[int]:
    """Generate dark-sounding pitches from chord context."""
    pcs = chord.pitch_classes()
    root = pcs[0] if pcs else key.root
    base = root + 36  # Low register for pads

    if mode == "minor_pad":
        intervals = [0, 3, 7, 10]  # minor 7th chord
    elif mode == "dim_cluster":
        intervals = [0, 3, 6, 9]  # diminished
    elif mode == "tritone_drone":
        intervals = [0, 6]  # tritone
    elif mode == "chromatic_pad":
        intervals = list(range(0, min(count, 5)))  # chromatic cluster
    elif mode == "phrygian_pad":
        intervals = [0, 1, 3, 7, 8]  # Phrygian: root, b2, b3, 5, b6
    else:
        intervals = [0, 3, 7]

    pitches = []
    for i in intervals[:count]:
        p = nearest_pitch((root + i) % 12, base + i)
        p = max(0, min(127, p))
        pitches.append(p)
    return sorted(pitches)


@dataclass
class DarkPadGenerator(PhraseGenerator):
    """
    Dark ambient pad generator.

    mode:
        Pad texture type. See module docstring.
    chord_dur:
        Duration of each sustained chord in beats.
    velocity_level:
        Base velocity (0.0-1.0). Pads are typically quiet.
    register:
        "low" (C2-C3), "mid" (C3-C4), "high" (C4-C5).
    overlap:
        Overlap between chord changes (0.0-1.0 fraction of chord_dur).
    """

    name: str = "Dark Pad Generator"
    mode: str = "minor_pad"
    chord_dur: float = 8.0
    velocity_level: float = 0.35
    register: str = "low"
    overlap: float = 0.3
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "minor_pad",
        chord_dur: float = 8.0,
        velocity_level: float = 0.35,
        register: str = "low",
        overlap: float = 0.3,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if mode not in (
            "minor_pad",
            "dim_cluster",
            "tritone_drone",
            "chromatic_pad",
            "phrygian_pad",
        ):
            raise ValueError(f"Unknown dark pad mode: {mode!r}")
        self.mode = mode
        self.chord_dur = max(2.0, min(32.0, chord_dur))
        self.velocity_level = max(0.05, min(0.8, velocity_level))
        self.register = register
        self.overlap = max(0.0, min(0.9, overlap))
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
        reg_offset = {"low": 0, "mid": 12, "high": 24}.get(self.register, 0)
        t = 0.0

        while t < duration_beats:
            chord = chord_at(chords, t)
            pitches = _dark_pitches(chord, key, self.mode, 4)
            pitches = [max(0, min(127, p + reg_offset)) for p in pitches]

            dur = min(self.chord_dur, duration_beats - t)
            vel = int(self.velocity_level * 100)

            # Micro-timing onset staggering & LFO modulation for physical realism
            for i, p in enumerate(pitches):
                # 1. Timing Jitter & Divisi Phase Staggering
                onset_delay = i * 0.015  # Sequential blooming
                jitter = random.uniform(-0.003, 0.003)
                start_h = max(0.0, t + onset_delay + jitter)
                
                # Check bounds
                if start_h >= duration_beats:
                    continue
                
                note_dur = dur + dur * self.overlap  # overlap into next chord
                note_dur_h = min(note_dur, duration_beats - start_h)
                if note_dur_h <= 0.01:
                    continue

                v = max(10, min(127, vel + random.randint(-8, 8)))

                # 2. Continuous CC Modulations
                expression = {}
                steps = 12
                
                # CC 11: Dynamic volume breathing LFO (phase & freq offset per note)
                freq_11 = 0.1 + (i * 0.02)
                phase_11 = i * 0.5
                cc11_list = []
                for s in range(steps + 1):
                    progress_t = s / steps
                    t_rel = progress_t * note_dur_h
                    lfo_factor = 0.85 + 0.15 * math.sin(2 * math.pi * freq_11 * t_rel + phase_11)
                    cc11_list.append((round(t_rel, 6), max(1, min(127, int(127 * lfo_factor)))))
                expression[11] = cc11_list

                # CC 74: Evolving resonant cutoff sweep LFO
                freq_74 = 0.05 + (i * 0.01)
                phase_74 = i * 0.8
                cc74_list = []
                base_cutoff = 55 if self.mode == "minor_pad" else 45
                for s in range(steps + 1):
                    progress_t = s / steps
                    t_rel = progress_t * note_dur_h
                    lfo_val = base_cutoff + int(20 * math.sin(2 * math.pi * freq_74 * t_rel + phase_74))
                    cc74_list.append((round(t_rel, 6), max(1, min(127, lfo_val))))
                expression[74] = cc74_list

                # Pitch Bend: Subtle analog tape drift / vibrato
                freq_pb = 0.12
                phase_pb = i * (math.pi / 2)
                pb_list = []
                for s in range(steps + 1):
                    progress_t = s / steps
                    t_rel = progress_t * note_dur_h
                    pb_val = int(500 * math.sin(2 * math.pi * freq_pb * t_rel + phase_pb))
                    pb_list.append((round(t_rel, 6), pb_val))
                expression["pitch_bend"] = pb_list

                note = NoteInfo(
                    pitch=p,
                    start=round(start_h, 6),
                    duration=round(note_dur_h, 6),
                    velocity=v,
                )
                note.expression = expression
                notes.append(note)

                # 3. Glassy Resonant Overtones (Octave or Fifth) for high complexity or specific modes
                if (self.params.complexity >= 0.5 or self.mode in ("dim_cluster", "phrygian_pad")) and random.random() < 0.6:
                    overtone_pitch = p + (19 if i % 2 == 1 else 12)  # Fifth or Octave
                    if 0 <= overtone_pitch <= 127:
                        overtone_vel = max(5, int(v * 0.35))
                        overtone_start = round(start_h + 0.03, 6)  # Delayed strike
                        overtone_dur = round(note_dur_h * 0.7, 6)
                        
                        overtone_expr = {}
                        # Soft CC 11 fade out for glassy overtone shimmer
                        cc11_overtone = []
                        for s in range(steps + 1):
                            t_rel = (s / steps) * overtone_dur
                            val = int(80 * (1.0 - (s / steps) ** 1.5))
                            cc11_overtone.append((round(t_rel, 6), max(0, val)))
                        overtone_expr[11] = cc11_overtone
                        
                        # Soft CC 74 cutoff
                        overtone_expr[74] = 40
                        
                        overtone_note = NoteInfo(
                            pitch=overtone_pitch,
                            start=overtone_start,
                            duration=overtone_dur,
                            velocity=overtone_vel,
                        )
                        overtone_note.expression = overtone_expr
                        notes.append(overtone_note)

            t += self.chord_dur

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes
