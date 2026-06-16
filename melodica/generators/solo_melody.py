# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/solo_melody.py — Expressive Solo Melody Generator.

Layer: Application / Domain
Style: Improvised virtuoso solos (Shred, Fusion, Synth, Blues, Neo-Soul, Vocal, Strings, Horn, Ambient).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale

SOLO_STYLES = {
    "shred_guitar", "jazz_fusion", "space_synth", "blues_lick",
    "neo_soul_keys", "vocal_mimic", "cinematic_strings", "bebop_horn",
    "modal_ambient"
}


@dataclass
class SoloMelodyGenerator(PhraseGenerator):
    """
    Expressive Solo Melody Generator.
    Simulates a live musician improvising high-fidelity solos across 9 genres.
    """

    name: str = "Solo Melody"
    style: str = "blues_lick"
    vibrato_depth: float = 0.5
    blues_notes: bool = True
    chromaticism: float = 0.4
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "blues_lick",
        vibrato_depth: float = 0.5,
        blues_notes: bool = True,
        chromaticism: float = 0.4,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if style not in SOLO_STYLES:
            raise ValueError(f"style must be one of {SOLO_STYLES}; got {style!r}")
        self.style = style
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        self.blues_notes = blues_notes
        self.chromaticism = max(0.0, min(1.0, chromaticism))
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

        # 1. Build rhythmic solo events
        events = self._build_events(duration_beats)
        if not events:
            return []

        notes: list[NoteInfo] = []
        low = max(48, self.params.key_range_low)
        high = min(88, self.params.key_range_high)
        mid = (low + high) // 2

        prev_pitch = (
            context.prev_pitch
            if context and context.prev_pitch is not None
            else mid
        )
        last_chord: ChordLabel | None = None
        was_high_tension = False

        for idx, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            root_pc = chord.root
            pcs = chord.pitch_classes()
            
            pitch = prev_pitch
            expression: dict[int | str, any] = {}
            articulation = "sustain"
            dur = event.duration

            # 0. Timing & Velocity Humanization (utilizes global intelligence config if available)
            time_human = 0.015
            vel_human = 0.15
            if self.params.intel:
                if hasattr(self.params.intel, "time_humanization"):
                    time_human = self.params.intel.time_humanization
                if hasattr(self.params.intel, "velocity_humanization"):
                    vel_human = self.params.intel.velocity_humanization
            
            onset_delay = random.uniform(-time_human, time_human)
            start_time = max(0.0, event.onset + onset_delay)

            # ---------------------------------------------------------------
            # Pitch Selection & Expressive Modulation Algorithms per Style
            # ---------------------------------------------------------------
            if self.style == "blues_lick":
                blues_steps = [0, 3, 5, 6, 7, 10]
                if not self.blues_notes:
                    blues_steps = [0, 3, 5, 7, 10]
                
                selected_step = random.choice(blues_steps)
                target_pitch = root_pc + selected_step
                
                is_enclosure = random.random() < self.chromaticism and idx > 0
                if is_enclosure:
                    offset = 1 if random.random() < 0.5 else -1
                    pitch = nearest_pitch(target_pitch + offset, prev_pitch)
                    articulation = "staccato"
                else:
                    pitch = nearest_pitch(target_pitch, prev_pitch)
                
                # Dynamic expression & pitch bends
                expression = {}
                if selected_step == 6:  # flat 5th (blue note) -> slow bend up
                    expression["pitch_bend"] = [(0.0, -1500), (0.12, 0)]
                elif dur > 0.6:
                    expression[1] = int(40 + 50 * self.vibrato_depth)

            elif self.style == "shred_guitar":
                is_fast_run = (event.duration < 0.25)
                if is_fast_run:
                    step = random.choice([-2, -1, 1, 2])
                    pitch = prev_pitch + step
                else:
                    leap_pc = random.choice(pcs) if pcs else root_pc
                    pitch = nearest_pitch(leap_pc, prev_pitch + 12)
                
                expression = {}
                if not is_fast_run:
                    expression = {74: 105, 1: int(60 * self.vibrato_depth)}
                    # Quick slide-in bend for accented notes
                    expression["pitch_bend"] = [(0.0, -2048), (0.05, 0)]
                    articulation = "accent"
                else:
                    articulation = "legato"

            elif self.style == "jazz_fusion":
                is_enclosure = (idx % 3 == 0) and idx > 0
                if is_enclosure:
                    target_tone = root_pc
                    if random.random() < 0.5 and len(pcs) > 2:
                        target_tone = pcs[2]
                    pitch = nearest_pitch(target_tone + 1, prev_pitch)
                    articulation = "legato"
                else:
                    chord_tone = random.choice(pcs) if pcs else root_pc
                    pitch = nearest_pitch(chord_tone, prev_pitch)
                
                pitch = max(low - 6, min(high + 6, pitch))
                expression = {}

            elif self.style == "space_synth":
                pitch = nearest_pitch(root_pc, prev_pitch)
                if random.random() < 0.4 and len(pcs) > 1:
                    pitch = nearest_pitch(pcs[-1], prev_pitch)
                
                lfo_val = int(55 + 40 * math.sin(event.onset * 1.5))
                expression = {74: lfo_val}
                if dur > 1.0:
                    expression[1] = int(50 + 40 * self.vibrato_depth)
                    # Swelling CC 11 filter/volume sweep
                    expression[11] = [(0.0, 50), (dur * 0.4, 110), (dur, 60)]

            elif self.style == "neo_soul_keys":
                # Stepwise R&B leads
                pitch = nearest_pitch(root_pc, prev_pitch)
                if random.random() < 0.3 and len(pcs) > 1:
                    pitch = nearest_pitch(pcs[1], prev_pitch)
                pitch = max(low + 6, min(high - 6, pitch))
                articulation = "sustain"
                expression = {}

            elif self.style == "vocal_mimic":
                # Lyrical, melismatic vocal line
                pitch = nearest_pitch(root_pc, prev_pitch)
                if random.random() < 0.3 and len(pcs) > 2:
                    pitch = nearest_pitch(pcs[2], prev_pitch)
                articulation = "legato"
                expression = {74: 85}  # warm vocal formants
                
                # Vocal CC 11 swells
                expr_11 = []
                steps = int(dur / 0.1)
                for s in range(steps + 1):
                    t_rel = s * 0.1
                    if t_rel <= dur:
                        phase = t_rel / dur
                        val = int(55 + 60 * math.sin(phase * math.pi))
                        expr_11.append((round(t_rel, 3), val))
                if expr_11:
                    expression[11] = expr_11
                
                # Vocal scoop bend
                if dur > 0.4:
                    expression["pitch_bend"] = [(0.0, -1500), (0.12, 0)]

            elif self.style == "cinematic_strings":
                # Tension/Release Algorithm
                if was_high_tension:
                    # Resolve down stepwise to stable chord tone
                    stable_tone = pcs[0] if pcs else root_pc
                    pitch = nearest_pitch(stable_tone, prev_pitch)
                    was_high_tension = False
                else:
                    # Occasional high tension intervals (e.g. major 7th or tritone relative to root)
                    if random.random() < 0.4:
                        tension_offset = random.choice([6, 11])  # sharp 11th or major 7th
                        pitch = nearest_pitch(root_pc + tension_offset, prev_pitch)
                        was_high_tension = True
                    else:
                        pitch = nearest_pitch(random.choice(pcs) if pcs else root_pc, prev_pitch)
                
                expression = {}
                # Mod-wheel CC 1 tremolo sweeps
                tremolo_val = int(80 + 35 * math.sin(event.onset * 2.0))
                expression[1] = tremolo_val
                
                # CC 11 crescendo/decrescendo swells
                expr_11 = []
                steps = int(dur / 0.1)
                for s in range(steps + 1):
                    t_rel = s * 0.1
                    if t_rel <= dur:
                        phase = t_rel / dur
                        val = int(45 + 75 * math.sin(phase * math.pi))
                        expr_11.append((round(t_rel, 3), val))
                if expr_11:
                    expression[11] = expr_11
                
                # Legato slide-in bends
                if dur > 0.8:
                    expression["pitch_bend"] = [(0.0, -1000), (0.1, 0)]

            elif self.style == "bebop_horn":
                # Triplet-displaced double enclosures
                is_enclosure = (idx % 2 == 0) and idx > 0
                if is_enclosure:
                    target_tone = pcs[0] if pcs else root_pc
                    # Play half-step above, then resolve to target
                    pitch = nearest_pitch(target_tone + 1, prev_pitch)
                    articulation = "staccato"
                else:
                    pitch = nearest_pitch(random.choice(pcs) if pcs else root_pc, prev_pitch)
                expression = {}

            elif self.style == "modal_ambient":
                # Long modal Lydian/Dorian drone
                pitch = nearest_pitch(root_pc, prev_pitch)
                if random.random() < 0.3:
                    pitch = nearest_pitch(root_pc + 6, prev_pitch) # sharp 4th Lydian tension
                
                # Detuning vibrato fine-pitch bends
                detune_offset = random.randint(-15, 15)
                expression = {1: 30, 98: 64 + detune_offset}
                articulation = "sustain"
                
                # Ethereal volume swells
                expression[11] = [(0.0, 40), (dur * 0.5, 95), (dur, 30)]
                
                # Microtonal pitch bend drift LFO
                pb_points = []
                steps = int(dur / 0.25)
                for s in range(steps + 1):
                    t_rel = s * 0.25
                    if t_rel <= dur:
                        val = int(250 * math.sin(t_rel * 1.5 * 2.0 * math.pi))
                        pb_points.append((round(t_rel, 3), val))
                if pb_points:
                    expression["pitch_bend"] = pb_points

            # Clamp and snap to scale bounds
            pitch = snap_to_scale(pitch, key)
            pitch = max(low, min(high, pitch))

            # Dynamic velocity mapping
            vel = 72
            if articulation == "accent":
                vel = 110
            elif articulation == "legato":
                vel = 65
            elif articulation == "staccato":
                vel = 48
            else:
                vel = 80

            # Velocity humanization
            vel += int(vel * random.uniform(-vel_human, vel_human))
            vel = max(1, min(127, vel))

            # ---------------------------------------------------------------
            # Premium Articulation & Ornaments Pre-Rendering
            # ---------------------------------------------------------------
            if self.style == "vocal_mimic" and (event.onset % 1.0 < 0.1) and idx > 0:
                # Prepend rapid 2-note chromatic melisma grace notes
                notes.append(
                    NoteInfo(
                        pitch=snap_to_scale(pitch - 2, key),
                        start=round(start_time - 0.16, 6),
                        duration=0.07,
                        velocity=max(1, vel - 15),
                        articulation="legato"
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=snap_to_scale(pitch - 1, key),
                        start=round(start_time - 0.08, 6),
                        duration=0.07,
                        velocity=max(1, vel - 8),
                        articulation="legato"
                    )
                )

            # Main note
            main_note = NoteInfo(
                pitch=pitch,
                start=round(start_time, 6),
                duration=round(dur, 6),
                velocity=vel,
                articulation=articulation,
                expression=expression,
            )
            notes.append(main_note)


            # Neo-Soul Chord stab backing chords on syncopated offbeats
            if self.style == "neo_soul_keys" and (event.onset % 1.0 > 0.1) and random.random() < 0.6:
                # Layer a 3-voice stab (lower octaves and chord tones) at the exact same start time
                stab_intervals = [-12, -7, -4]
                for offset in stab_intervals:
                    stab_pitch = snap_to_scale(pitch + offset, key)
                    if low <= stab_pitch <= high:
                        notes.append(
                            NoteInfo(
                                pitch=stab_pitch,
                                start=round(event.onset, 6),
                                duration=round(dur * 0.8, 6),
                                velocity=max(1, vel - 15),
                                articulation="staccato"
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

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        events: list[RhythmEvent] = []
        t = 0.0

        if self.style == "blues_lick":
            while t < duration_beats:
                bar_offset = t % 4.0
                if bar_offset == 0.0:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.45, velocity_factor=0.8))
                    t += 1.0
                elif bar_offset == 1.0:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.9, velocity_factor=1.1))
                    t += 1.0
                elif bar_offset == 2.0:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.45, velocity_factor=0.8))
                    t += 1.0
                else:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.3, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.33, 6), duration=0.3, velocity_factor=0.85))
                    events.append(RhythmEvent(onset=round(t + 0.66, 6), duration=0.3, velocity_factor=0.9))
                    t += 1.0

        elif self.style == "shred_guitar":
            while t < duration_beats:
                run_offsets = [0.0, 0.166, 0.33, 0.5, 0.66, 0.83, 1.0, 1.25, 1.5, 1.75]
                for off in run_offsets:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.15, velocity_factor=1.0))
                onset = t + 2.0
                if onset < duration_beats:
                    events.append(RhythmEvent(onset=round(onset, 6), duration=1.7, velocity_factor=1.1))
                t += 4.0

        elif self.style == "jazz_fusion":
            while t < duration_beats:
                for off in [0.0, 0.33, 0.66, 1.0, 1.5, 1.83, 2.0, 2.5, 2.83, 3.0]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.25, velocity_factor=1.0))
                t += 4.0

        elif self.style in ("space_synth", "modal_ambient"):
            # Slower spacious drones
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=2.2, velocity_factor=1.0))
                if self.style == "space_synth":
                    events.append(RhythmEvent(onset=round(t + 2.5, 6), duration=0.3, velocity_factor=0.85))
                    events.append(RhythmEvent(onset=round(t + 3.25, 6), duration=0.3, velocity_factor=0.9))
                t += 4.0

        elif self.style in ("neo_soul_keys", "vocal_mimic"):
            # Syncopated 16th/8th R&B grooves
            while t < duration_beats:
                for off in [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.2, velocity_factor=1.0))
                t += 4.0

        elif self.style == "cinematic_strings":
            # Deep string bows mixed with rapid sweeps
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=1.8, velocity_factor=1.0))
                # sudden rapid runs
                events.append(RhythmEvent(onset=round(t + 2.0, 6), duration=0.2, velocity_factor=0.85))
                events.append(RhythmEvent(onset=round(t + 2.25, 6), duration=0.2, velocity_factor=0.85))
                events.append(RhythmEvent(onset=round(t + 2.5, 6), duration=1.3, velocity_factor=1.0))
                t += 4.0

        elif self.style == "bebop_horn":
            # eighth note runs with triplet displacement timing shifts
            while t < duration_beats:
                for off in [0.0, 0.5, 1.0, 1.33, 1.66, 2.0, 2.5, 3.0, 3.33]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.25, velocity_factor=1.0))
                t += 4.0

        return events
