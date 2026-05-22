# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/tuba.py -- Deep low-frequency brass generator.

Layer: Application / Domain
Style: Classical, cinematic, orchestral, march.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


class TubaGenerator(PhraseGenerator):
    """
    TubaGenerator: Deep low-frequency brass generator.
    Enforces a natural tuba register (F1 to F4, MIDI 29 to 65).
    
    articulation:
        "staccato"  -- Heavy, explosive, short staccato bursts.
        "sustained" -- Powerful, warm sustained support.
        "walking"   -- Walking bass/march style support.
        "swell"     -- CC 11 dynamic swell.
    mute:
        If True, darkens the sound by lowering the CC 74 filter cutoff.
    growl:
        If True, introduces a physical model growl via a rapid CC 74 LFO modulation on sustained notes.
    """

    name: str = "Tuba Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        mute: bool = False,
        growl: bool = False,
        breath_gap: float = 0.3,
    ) -> None:
        if params is None:
            params = GeneratorParams(key_range_low=29, key_range_high=65)
        super().__init__(params)
        self.articulation = articulation
        self.mute = mute
        self.growl = growl
        self.breath_gap = max(0.0, min(1.0, breath_gap))
        
        # Ensure bounds are respected if custom params are passed
        self.params.key_range_low = max(self.params.key_range_low, 29)
        self.params.key_range_high = min(self.params.key_range_high, 65)
        self._last_context: RenderContext | None = None

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
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            root_pc = pcs[0]
            # Center the pitch in the lower end of our range (around C3 = 48)
            anchor = 40
            pitch = nearest_pitch(root_pc, anchor)
            pitch = snap_to_scale(pitch, key)
            
            # Enforce range limits
            while pitch < self.params.key_range_low:
                pitch += 12
            while pitch > self.params.key_range_high:
                pitch -= 12
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            # Render based on articulation
            if self.articulation == "staccato":
                # Render heavy staccato notes
                step = 1.0 if chord.duration >= 1.0 else chord.duration
                t = chord.start
                while t < chord.start + chord.duration:
                    note_dur = step * 0.35
                    vel = int(85 + random.randint(5, 20))
                    # Staccato stabs have high initial velocity
                    note = NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=max(0.1, note_dur),
                        velocity=max(1, min(127, vel)),
                    )
                    # CC 74 filter decay for sharp staccato attack
                    expression = {}
                    if self.mute:
                        expression[74] = 40
                    else:
                        expression[74] = [(0.0, 95), (note_dur * 0.8, 60)]
                    note.expression = expression
                    notes.append(note)
                    t += step

            elif self.articulation == "walking":
                # Generates classic walking bass or steady march support
                step = 1.0  # Quarter notes
                t = chord.start
                step_idx = 0
                while t < chord.start + chord.duration:
                    note_dur = 0.7  # Marcato-like duration
                    vel = int(75 + (15 if step_idx % 2 == 0 else 0) + random.randint(-5, 5))
                    
                    # Pitch can walk or alternate to the 5th (7 semitones)
                    walk_pitch = pitch
                    if step_idx % 4 == 2 and len(pcs) > 1:
                        fifth_pc = pcs[1]
                        walk_pitch = nearest_pitch(fifth_pc, pitch)
                        walk_pitch = snap_to_scale(walk_pitch, key)
                        walk_pitch = max(self.params.key_range_low, min(self.params.key_range_high, walk_pitch))

                    note = NoteInfo(
                        pitch=walk_pitch,
                        start=round(t, 6),
                        duration=max(0.1, note_dur),
                        velocity=max(1, min(127, vel)),
                    )
                    expression = {}
                    if self.mute:
                        expression[74] = 45
                    else:
                        expression[74] = 75
                    note.expression = expression
                    notes.append(note)
                    t += step
                    step_idx += 1

            elif self.articulation == "swell":
                # Continuous CC 11 swell + pitch fall at end
                vel = int(45)  # Start soft
                note_dur = max(0.2, chord.duration - self.breath_gap)
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=note_dur,
                    velocity=vel,
                )
                expression = {}
                
                # CC 11 crescendo
                steps = 16
                cc11_list = []
                for s in range(steps + 1):
                    t_rel = (s / steps) * note_dur
                    val = int(25 + 90 * (s / steps) ** 1.6)
                    cc11_list.append((t_rel, val))
                expression[11] = cc11_list

                # CC 74 filter swell
                cc74_list = []
                for s in range(steps + 1):
                    t_rel = (s / steps) * note_dur
                    base_cutoff = 40 if self.mute else 55
                    val = int(base_cutoff + 35 * (s / steps))
                    cc74_list.append((t_rel, val))
                expression[74] = cc74_list

                # Continuous pitch bend fall at the very end
                fall_start_t = note_dur * 0.8
                pitch_bend = [
                    (0.0, 0),
                    (fall_start_t, 0),
                    (note_dur * 0.9, -1500),
                    (note_dur, -4000),
                ]
                expression["pitch_bend"] = pitch_bend

                note.expression = expression
                notes.append(note)

            else:  # sustained
                vel = int(80 + random.randint(-5, 5))
                note_dur = max(0.2, chord.duration - self.breath_gap)
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=note_dur,
                    velocity=vel,
                )
                expression = {}
                
                # Base CC 74 filter mutes
                base_val = 45 if self.mute else 80
                
                # Apply rapid LFO growl on CC 74 if requested
                if self.growl:
                    # Physics-inspired LFO: 8Hz speed
                    lfo_freq = 8.0  # Hz
                    steps = int(note_dur * 20)  # sample points
                    steps = max(5, steps)
                    cc74_list = []
                    for s in range(steps + 1):
                        t_rel = (s / steps) * note_dur
                        # Oscillation amplitude of 15 around the base_val
                        lfo_val = base_val + int(15 * math.sin(2 * math.pi * lfo_freq * t_rel))
                        cc74_list.append((t_rel, max(1, min(127, lfo_val))))
                    expression[74] = cc74_list
                else:
                    expression[74] = base_val

                # Smooth pitch fall at the very end
                fall_start_t = note_dur * 0.85
                pitch_bend = [
                    (0.0, 0),
                    (fall_start_t, 0),
                    (note_dur * 0.95, -1000),
                    (note_dur, -3000),
                ]
                expression["pitch_bend"] = pitch_bend

                note.expression = expression
                notes.append(note)

            elapsed += chord.duration

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )

        return notes
