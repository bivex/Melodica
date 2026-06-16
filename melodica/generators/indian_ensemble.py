# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/indian_ensemble.py — Traditional Indian classical instruments.
Implements highly realistic Tanpura, Sitar, and Tabla generators.
"""

from __future__ import annotations

import random
import math
from abc import ABC

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.plucked_solo import _PluckedSoloBase
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_at


class TanpuraGenerator(PhraseGenerator):
    """
    Tanpura Generator.
    Produces a continuous, rich, cyclical drone on the key's tonic (Sa),
    fifth (Pa), fourth (Ma), or seventh (Ni). Includes jivari overtone buzzing.
    """
    name: str = "Tanpura Drone"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        tuning: str = "Sa-Pa",  # Sa-Pa (I-V), Sa-Ma (I-IV), Sa-Ni (I-VII)
        jivari: float = 0.5,     # Buzzing/overtone intensity (0.0 to 1.0)
        pluck_pattern: str = "standard",  # standard, fast, slow
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.tuning = tuning
        self.jivari = max(0.0, min(1.0, jivari))
        self.pluck_pattern = pluck_pattern
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

        # Find Sa (tonic) pitch closest to the center of key range
        lo = self.params.key_range_low
        hi = self.params.key_range_high
        mid_range = (lo + hi) // 2
        
        # Calculate Sa in middle octave
        tonic_pc = key.root % 12
        sa_mid = nearest_pitch(tonic_pc, mid_range)
        sa_mid = max(lo, min(hi, sa_mid))
        sa_low = max(lo, min(hi, sa_mid - 12))

        # Calculate auxiliary string pitch based on tuning
        if self.tuning == "Sa-Ma":
            aux_pc = (tonic_pc + 5) % 12  # Fourth (Ma)
        elif self.tuning == "Sa-Ni":
            aux_pc = (tonic_pc + 11) % 12  # Seventh (Ni)
        else:
            aux_pc = (tonic_pc + 7) % 12  # Fifth (Pa)
            
        aux_pitch = nearest_pitch(aux_pc, sa_mid - 5)
        aux_pitch = max(lo, min(hi, aux_pitch))

        # Plucking intervals and cycle definition
        # Cycle: String 1 (Aux), String 2 (Sa Mid), String 3 (Sa Mid), String 4 (Sa Low)
        pitches = [aux_pitch, sa_mid, sa_mid, sa_low]
        
        if self.pluck_pattern == "fast":
            pluck_interval = 0.75
        elif self.pluck_pattern == "slow":
            pluck_interval = 2.0
        else:
            pluck_interval = 1.25  # standard meditative pluck rate

        notes: list[NoteInfo] = []
        t = 0.0
        cycle_idx = 0

        while t < duration_beats:
            pitch = pitches[cycle_idx % 4]
            dur = pluck_interval * 2.8  # strings ring out and overlap
            
            # Subtle random volume variation
            vel = int(65 + random.uniform(-6, 6))

            # Jivari overtone buzzing (CC 12)
            expression = {}
            if self.jivari > 0:
                buzz_points = []
                step = 0.1
                buzz_t = 0.0
                while buzz_t < dur:
                    # Buzzing rises quickly, oscillates, then decays
                    phase = buzz_t / dur
                    if phase < 0.2:
                        val = int(64 + (40 * self.jivari) * (phase / 0.2))
                    else:
                        osc = math.sin(buzz_t * 15.0) * 10.0 * (1.0 - phase)
                        val = int(64 + (30 * self.jivari) * (1.0 - phase) + osc)
                    buzz_points.append((round(buzz_t, 3), max(0, min(127, val))))
                    buzz_t += step
                expression[12] = buzz_points

            # Slight microtonal detuning per pluck
            detune = random.choice([-50, -25, 0, 25, 50])  # pitch bend units
            if "pitch_bend" not in expression:
                expression["pitch_bend"] = [(0.0, detune)]

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="sustain",
                    expression=expression,
                )
            )

            t += pluck_interval
            cycle_idx += 1

        return sorted(notes, key=lambda n: n.start)


class SitarGenerator(_PluckedSoloBase):
    """
    Sitar Generator.
    Implements true meend (glides), sympathetic resonance (tarab),
    and krintan (hammer-on/pull-off) rapid double-plucking.
    """
    name: str = "Sitar Solo"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        sympathetic_resonance: float = 0.4,
        meend_probability: float = 0.35,
        krintan_probability: float = 0.25,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.sympathetic_resonance = max(0.0, min(1.0, sympathetic_resonance))
        self.meend_probability = max(0.0, min(1.0, meend_probability))
        self.krintan_probability = max(0.0, min(1.0, krintan_probability))
        self.note_density = note_density

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

        for i, chord in enumerate(chords):
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Target pitch
            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            
            vel = self._velocity(72)
            dur = chord.duration * 0.85
            expression: dict[int | str, int | list[tuple[float, int]]] = {}

            # 1. Meend (Portamento Slide)
            # If sliding from a previous note, create a pitch bend curve ramping to the target pitch
            if i > 0 and random.random() < self.meend_probability:
                diff = prev_pitch - pitch
                if 0 < abs(diff) <= 4:  # typical meend range (up to 4 semitones)
                    # Convert semitones diff to 14-bit pitch bend units (assuming range +/- 2 semitones)
                    # For +/- 2 range: 1 semitone = 4096 units.
                    bend_range = 2
                    start_bend = max(-8192, min(8191, int(diff * (8192.0 / bend_range))))
                    
                    # Ramp from start_bend down to 0 over 0.2 beats or 30% of note duration
                    slide_dur = min(0.3, dur * 0.5)
                    expression["pitch_bend"] = [
                        (0.0, start_bend),
                        (slide_dur, 0)
                    ]
            
            # 2. Sympathetic Resonance (Tarab)
            # Spawns a soft, slightly delayed and detuned pitch class drone at an octave or fifth
            if self.sympathetic_resonance > 0 and random.random() < 0.7:
                tarab_pitch = pitch - 12 if pitch - 12 >= self.params.key_range_low else pitch + 12
                if self.params.key_range_low <= tarab_pitch <= self.params.key_range_high:
                    tarab_vel = max(5, int(vel * self.sympathetic_resonance * 0.6))
                    # detuned by +15 cents (approx 614 bend units on a +/-2 range)
                    tarab_expr = {"pitch_bend": [(0.0, 614)]}
                    notes.append(
                        NoteInfo(
                            pitch=tarab_pitch,
                            start=round(chord.start + 0.04, 6),
                            duration=round(dur * 1.5, 6),
                            velocity=tarab_vel,
                            articulation="sustain",
                            expression=tarab_expr,
                        )
                    )

            # 3. Krintan Ornamentation
            # A rapid hammer-on/pull-off stroke before/at the start of the note
            if random.random() < self.krintan_probability:
                ornament_pitch = snap_to_scale(pitch + random.choice([2, -1, -2]), key)
                ornament_pitch = max(self.params.key_range_low, min(self.params.key_range_high, ornament_pitch))
                
                # Grace note: short, slightly softer
                notes.append(
                    NoteInfo(
                        pitch=ornament_pitch,
                        start=round(chord.start, 6),
                        duration=0.08,
                        velocity=max(20, vel - 15),
                        articulation="staccato",
                    )
                )
                
                # Shift the main note start and shorten it slightly
                main_start = chord.start + 0.08
                main_dur = max(0.05, dur - 0.08)
            else:
                main_start = chord.start
                main_dur = dur

            note = NoteInfo(
                pitch=pitch,
                start=round(main_start, 6),
                duration=round(main_dur, 6),
                velocity=vel,
                articulation="sustain",
            )
            if expression:
                note.expression = expression
            notes.append(note)

            prev_pitch = pitch

        return sorted(notes, key=lambda n: n.start)


class TablaGenerator(PhraseGenerator):
    """
    Tabla Generator.
    Generates authentic Indian percussion patterns using standard talas:
    Teental (16), Ektal (12), Rupak (7), Kaharwa (8), Dadra (6).
    Applies bayan pitch-bend sliding (ghe).
    """
    name: str = "Tabla Ensemble"

    # MIDI Stroke Map (General MIDI percussion approximations)
    # Bayan (Bass): Ghe (36 - Kick), Ka/Kat (39 - Clap/Slap)
    # Dayan (Treble): Na/Ta (38 - Snare rim), Tin (40 - Snare/Tom), Tun (41 - Tom)
    STROKES = {
        "ghe": 36,
        "kat": 39,
        "na": 38,
        "tin": 40,
        "tun": 41,
    }

    # Tala Definitions (cycle of stroke lists)
    # Dha = Ghe + Na, Dhin = Ghe + Tin
    TALAS = {
        "teental": [
            ["ghe", "na"], ["ghe", "tin"], ["ghe", "tin"], ["ghe", "na"],  # Dha Dhin Dhin Dha
            ["ghe", "na"], ["ghe", "tin"], ["ghe", "tin"], ["ghe", "na"],  # Dha Dhin Dhin Dha
            ["ghe", "na"], ["tin"], ["tin"], ["na"],                      # Dha Tin Tin Ta
            ["na"], ["ghe", "tin"], ["ghe", "tin"], ["ghe", "na"],          # Ta Dhin Dhin Dha
        ],
        "ektal": [
            ["ghe", "tin"], ["ghe", "tin"],                                # Dhin Dhin
            ["ghe", "na"], ["na"],                                        # Dhage tirikit (simplified)
            ["tun"], ["na"],                                              # Tun Na
            ["kat"], ["na"],                                              # Kat Ta
            ["ghe", "na"], ["na"],                                        # Dhage tirikit
            ["ghe", "tin"], ["ghe", "tin"],                                # Dhin Dhin
        ],
        "rupak": [
            ["tin"], ["tin"], ["na"],                                      # Tin Tin Na
            ["ghe", "na"], ["na"],                                        # Dhin Na
            ["ghe", "na"], ["na"],                                        # Dhin Na
        ],
        "kaharwa": [
            ["ghe", "na"], ["ghe"], ["na"], ["tin"],                      # Dha Ge Na Ti
            ["na"], ["kat"], ["ghe", "tin"], ["na"],                      # Na Ka Dhin Na
        ],
        "dadra": [
            ["ghe", "na"], ["ghe", "tin"], ["na"],                        # Dha Dhi Na
            ["ghe", "na"], ["tun"], ["na"],                              # Dha Tu Na
        ],
    }

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        tala: str = "teental",
        bayan_modulation: float = 0.5,
        humanize_swing: float = 0.05,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.tala = tala
        self.bayan_modulation = max(0.0, min(1.0, bayan_modulation))
        self.humanize_swing = max(0.0, humanize_swing)
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

        cycle = self.TALAS.get(self.tala, self.TALAS["teental"])
        notes: list[NoteInfo] = []
        
        # Determine step subdivision based on tala length
        # Rupak and Dadra are usually in 3/8 or 6/8, Teental/Kaharwa/Ektal in 4/4
        step_dur = 0.5 if self.tala in ("teental", "ektal") else 0.5
        if self.tala == "kaharwa":
            step_dur = 0.25  # 16th notes speed up Kaharwa

        t = 0.0
        step_idx = 0

        while t < duration_beats:
            strokes = cycle[step_idx % len(cycle)]
            
            # Apply density gating
            if random.random() <= self.note_density:
                for stroke in strokes:
                    pitch = self.STROKES.get(stroke, 36)
                    
                    # Accent downbeats
                    is_downbeat = (step_idx % len(cycle) == 0)
                    base_vel = 95 if is_downbeat else (80 if "ghe" in strokes else 68)
                    vel = max(1, min(127, base_vel + random.randint(-8, 8)))

                    # Compute start time with swing/humanization
                    start_time = t
                    if self.humanize_swing > 0 and not is_downbeat:
                        # swing off-beats slightly
                        if step_idx % 2 != 0:
                            start_time += random.uniform(0.0, self.humanize_swing * step_dur)

                    dur = step_dur * 0.8
                    expression = {}

                    # Bayan modulation: characteristic pitch bend slide on ghe (Kick drum, 36)
                    if stroke == "ghe" and self.bayan_modulation > 0:
                        # Bayan bends up or down
                        bend_dir = random.choice([1, -1])
                        start_bend = int(bend_dir * 3000 * self.bayan_modulation)
                        mid_bend = int(-bend_dir * 1500 * self.bayan_modulation)
                        expression["pitch_bend"] = [
                            (0.0, start_bend),
                            (dur * 0.3, mid_bend),
                            (dur * 0.8, 0)
                        ]

                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(start_time, 6),
                            duration=round(dur, 6),
                            velocity=vel,
                            expression=expression,
                            absolute=True,  # percussion pitches are absolute
                        )
                    )

            t += step_dur
            step_idx += 1

        return sorted(notes, key=lambda n: n.start)
