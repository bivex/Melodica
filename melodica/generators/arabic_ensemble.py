# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/arabic_ensemble.py — Traditional Arabic/maqam classical instruments.
Implements highly realistic Oud, Ney, and Darbuka generators with microtonal capability.
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.plucked_solo import _PluckedSoloBase
from melodica.generators.wind_brass_solo import _WindBrassSoloBase
from melodica.engines.microtuning import MicrotuningEngine
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class OudGenerator(_PluckedSoloBase):
    """
    Oud (Lute) Generator.
    Features microtonal maqam snapping, double-string chorus simulation,
    and automatic tremolo (rss) plucking on long sustained notes.
    """
    name: str = "Oud Solo"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        tremolo_density: float = 0.3,
        risha_style: str = "standard",  # standard, aggressive, soft
        chorus_detune: float = 0.1,    # detune offset for double strings
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.tremolo_density = max(0.0, min(1.0, tremolo_density))
        self.risha_style = risha_style
        self.chorus_detune = max(0.0, min(0.5, chorus_detune))
        self.note_density = note_density
        self._tuning = MicrotuningEngine(bend_range=2)

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = mid

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Pick pitch and snap to scale degree (including microtones)
            pc = random.choice(pcs)
            raw_pitch = nearest_pitch(pc, prev_pitch)
            snapped_pitch = self._tuning.snap_to_scale(float(raw_pitch), key)
            snapped_pitch = max(float(self.params.key_range_low), min(float(self.params.key_range_high), snapped_pitch))
            
            # Base velocity depending on plectrum (risha) style
            if self.risha_style == "aggressive":
                vel = self._velocity(82)
            elif self.risha_style == "soft":
                vel = self._velocity(60)
            else:
                vel = self._velocity(72)

            dur = chord.duration * 0.8
            prev_pitch = int(round(snapped_pitch))

            # Helper to generate a single oud pluck (with microtuning pitch bend)
            def add_pluck(start_t: float, pluck_dur: float, pluck_vel: int):
                # Snap to pitch and get microtonal bend
                midi_int, expr = self._tuning.quantize_pitch(snapped_pitch, key)
                
                # Double string chorus effect: trigger a second slightly detuned note
                if self.chorus_detune > 0:
                    detune_val = int(self.chorus_detune * 400.0)  # bend units
                    detuned_expr = {"pitch_bend": [(0.0, expr.get("pitch_bend", [(0.0, 0)])[0][1] + detune_val)]}
                    notes.append(
                        NoteInfo(
                            pitch=midi_int,
                            start=round(start_t + 0.012, 6),  # 12ms delay
                            duration=round(pluck_dur, 6),
                            velocity=max(1, pluck_vel - 10),
                            articulation="sustain",
                            expression=detuned_expr,
                        )
                    )

                notes.append(
                    NoteInfo(
                        pitch=midi_int,
                        start=round(start_t, 6),
                        duration=round(pluck_dur, 6),
                        velocity=pluck_vel,
                        articulation="sustain",
                        expression=expr,
                    )
                )

            # Tremolo (rss) logic for longer notes
            if dur >= 0.75 and random.random() < self.tremolo_density:
                # Subdivide the note duration into rapid tremolo strokes
                tremolo_rate = 0.125  # 32nd notes speed
                t_offset = 0.0
                stroke_count = 0
                while t_offset < dur:
                    stroke_dur = min(tremolo_rate * 1.5, dur - t_offset)
                    # Alternate up/down strokes velocity
                    stroke_vel = vel if stroke_count % 2 == 0 else int(vel * 0.8)
                    add_pluck(chord.start + t_offset, stroke_dur, stroke_vel)
                    t_offset += tremolo_rate
                    stroke_count += 1
            else:
                add_pluck(chord.start, dur, vel)

        return sorted(notes, key=lambda n: n.start)


class NeyGenerator(_WindBrassSoloBase):
    """
    Ney (Reed Flute) Generator.
    Produces highly breathy solo lines, supporting microtonal scales,
    legato portamento glides, and breath noise expression swells.
    """
    name: str = "Ney Flute"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        breath_noise: float = 0.4,
        vibrato_depth: float = 0.3,
        legato_glide: float = 0.25,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.breath_noise = max(0.0, min(1.0, breath_noise))
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        self.legato_glide = max(0.0, min(1.0, legato_glide))
        self.note_density = note_density
        self._tuning = MicrotuningEngine(bend_range=2)

        # Ney standard register range: D3 (50) to D6 (86)
        self.params.key_range_low = max(50, self.params.key_range_low)
        self.params.key_range_high = min(86, self.params.key_range_high)

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = float(mid)

        for i, chord in enumerate(chords):
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Pick pitch and snap to scale degree (including microtones)
            pc = random.choice(pcs)
            raw_pitch = nearest_pitch(pc, int(round(prev_pitch)))
            snapped_pitch = self._tuning.snap_to_scale(float(raw_pitch), key)
            snapped_pitch = max(float(self.params.key_range_low), min(float(self.params.key_range_high), snapped_pitch))

            vel = self._velocity(68)  # soft, breathy attack
            dur = chord.duration * 0.95

            # Get target pitch bend and MIDI integer pitch
            midi_int, expr = self._tuning.quantize_pitch(snapped_pitch, key)
            expression = dict(expr)

            # 1. Legato Glide (Portamento)
            # Glide from prev_pitch to snapped_pitch
            if i > 0 and self.legato_glide > 0:
                pitch_diff = prev_pitch - snapped_pitch
                if 0 < abs(pitch_diff) <= 3:  # realistic legato step
                    # Combine existing tuning bend with portamento slide
                    tuning_bend = expr.get("pitch_bend", [(0.0, 0)])[0][1]
                    start_bend = tuning_bend + int(pitch_diff * 4096.0)
                    glide_t = min(self.legato_glide, dur * 0.4)
                    
                    expression["pitch_bend"] = [
                        (0.0, start_bend),
                        (glide_t, tuning_bend)
                    ]

            # 2. Breath-vibrato & breath noise expression (CC 11 / CC 2)
            # Modulate Expression to simulate human lung pressure fluctuation
            expr_points = []
            step = 0.08
            t_offset = 0.0
            
            # Base modulation depth
            depth = 12 * self.vibrato_depth
            speed = 5.0
            
            while t_offset < dur:
                # Breath swell at note start, vibrato in middle, decay at end
                phase = t_offset / dur
                env = math.sin(phase * math.pi)  # hump envelope
                
                # Sine vibrato + random breath noise flutter
                osc = math.sin(t_offset * speed * 2.0 * math.pi) * depth * env
                flutter = random.uniform(-6, 6) * self.breath_noise
                
                val = int(80 + osc + flutter)
                expr_points.append((round(t_offset, 3), max(0, min(127, val))))
                t_offset += step
                
            if expr_points:
                expression[11] = expr_points  # Expression controller

            notes.append(
                NoteInfo(
                    pitch=midi_int,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="sustain",
                    expression=expression,
                )
            )

            prev_pitch = snapped_pitch

        return sorted(notes, key=lambda n: n.start)


class DarbukaGenerator(PhraseGenerator):
    """
    Darbuka Goblet Drum Generator.
    Generates traditional Middle Eastern rhythms (Maqsoum, Baladi, Saidi, Ayyoub).
    Includes rapid decorative rolls/slaps (sak).
    """
    name: str = "Darbuka Percussion"

    # MIDI Stroke Map (General MIDI percussion mapping)
    # Doum (Bass center): 36 (Kick)
    # Tek (High edge right hand): 38 (Snare rim)
    # Ka (High edge left hand): 40 (Tom/snare snare)
    # Sak (Slap / closed hand): 39 (Clap/slap)
    STROKES = {
        "doum": 36,
        "tek": 38,
        "ka": 40,
        "sak": 39,
    }

    # Traditional Rhythm Patterns (grid sequences)
    PATTERNS = {
        "maqsoum": [
            ["doum"], ["tek"], ["ka"], ["tek"],
            ["doum"], ["ka"], ["tek"], ["ka"]
        ],
        "baladi": [
            ["doum"], ["doum"], ["ka"], ["tek"],
            ["doum"], ["ka"], ["tek"], ["ka"]
        ],
        "saidi": [
            ["doum"], ["tek"], ["ka"], ["doum"],
            ["doum"], ["ka"], ["tek"], ["ka"]
        ],
        "ayyoub": [
            ["doum"], ["ka"], ["doum"], ["tek"]
        ]
    }

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        rhythm_pattern: str = "maqsoum",
        rolls_probability: float = 0.2,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.rhythm_pattern = rhythm_pattern
        self.rolls_probability = max(0.0, min(1.0, rolls_probability))
        self.note_density = note_density

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if duration_beats <= 0:
            return []

        pattern = self.PATTERNS.get(self.rhythm_pattern, self.PATTERNS["maqsoum"])
        notes: list[NoteInfo] = []
        
        # Step duration is 0.5 beats (8th notes) for standard tempo,
        # Ayyoub is half length (2 beats loop), others are 4 beats loop.
        step_dur = 0.5

        t = 0.0
        step_idx = 0

        while t < duration_beats:
            # Apply density gating
            if random.random() <= self.note_density:
                strokes = pattern[step_idx % len(pattern)]
                
                # Check for decorative roll substitution on Tek/Ka beats
                is_roll = (
                    self.rolls_probability > 0
                    and ("tek" in strokes or "ka" in strokes)
                    and random.random() < self.rolls_probability
                )
                
                if is_roll:
                    # Replace a single step with a rapid 32nd note triplet roll (Ka - Tek - Ka)
                    roll_step = step_dur / 3
                    roll_strokes = ["ka", "tek", "ka"]
                    for idx, r_stroke in enumerate(roll_strokes):
                        pitch = self.STROKES.get(r_stroke, 38)
                        vel = int(60 + random.uniform(-10, 5))
                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(t + idx * roll_step, 6),
                                duration=round(roll_step * 0.8, 6),
                                velocity=max(1, min(127, vel)),
                                absolute=True,
                            )
                        )
                else:
                    # Standard play
                    for stroke in strokes:
                        # Sak/Slap random substitution
                        stroke_name = stroke
                        if stroke_name == "tek" and random.random() < 0.15:
                            stroke_name = "sak"  # substitute slap

                        pitch = self.STROKES.get(stroke_name, 36)
                        
                        # Downbeat accentuation
                        is_downbeat = (step_idx % len(pattern) == 0)
                        base_vel = 92 if is_downbeat else 74
                        vel = max(1, min(127, base_vel + random.randint(-8, 8)))

                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(t, 6),
                                duration=round(step_dur * 0.85, 6),
                                velocity=vel,
                                absolute=True,
                            )
                        )

            t += step_dur
            step_idx += 1

        return sorted(notes, key=lambda n: n.start)
