# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/tubular_bells.py -- Melodic resonant metallic chimes generator.

Layer: Application / Domain
Style: Classical, cinematic, ceremonial, liturgical.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


class TubularBellsGenerator(PhraseGenerator):
    """
    TubularBellsGenerator: Resonant metallic chimes.
    Enforces the natural orchestral register (F3 to G5, MIDI 53 to 79).
    
    stroke_pattern:
        "single" -- Striking the root/fifth note at chord changes with a long ring.
        "roll"   -- Rapid alternating tremolo roll between two bell pitches.
        "chime"  -- Melodic arpeggiated patterns highlighting chord changes.
    dampen:
        If True, applies a faster CC 11 decay curve representing chimes dampening.
    """

    name: str = "Tubular Bells Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        stroke_pattern: str = "single",
        dampen: bool = False,
    ) -> None:
        if params is None:
            params = GeneratorParams(key_range_low=53, key_range_high=79)
        super().__init__(params)
        self.stroke_pattern = stroke_pattern
        self.dampen = dampen
        
        # Ensure bounds are respected if custom params are passed
        self.params.key_range_low = max(self.params.key_range_low, 53)
        self.params.key_range_high = min(self.params.key_range_high, 79)
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
            anchor = 65  # Center of chimes range (F3-G5)
            pitch = nearest_pitch(root_pc, anchor)
            pitch = snap_to_scale(pitch, key)
            
            # Enforce range limits
            while pitch < self.params.key_range_low:
                pitch += 12
            while pitch > self.params.key_range_high:
                pitch -= 12
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            if self.stroke_pattern == "roll":
                # Rapid alternating roll between root and fifth (7 semitones)
                fifth_pc = pcs[1] if len(pcs) > 1 else (root_pc + 7) % 12
                fifth_pitch = nearest_pitch(fifth_pc, pitch)
                fifth_pitch = snap_to_scale(fifth_pitch, key)
                fifth_pitch = max(self.params.key_range_low, min(self.params.key_range_high, fifth_pitch))

                step = 0.125  # 16th notes
                t = chord.start
                step_idx = 0
                
                # Dynamic crescendo for rolls
                steps = int(chord.duration / step)
                cc11_list = []
                for s in range(steps):
                    cc11_list.append((s * step, int(40 + 80 * (s / steps))))

                while t < chord.start + chord.duration:
                    curr_pitch = pitch if step_idx % 2 == 0 else fifth_pitch
                    # Rolls are hit softer than single strikes
                    vel = int(65 + (step_idx / steps) * 20 + random.randint(-4, 4))
                    
                    note = NoteInfo(
                        pitch=curr_pitch,
                        start=round(t, 6),
                        duration=step * 1.5,  # Overlap slightly for resonating roll blend
                        velocity=max(1, min(127, vel)),
                    )
                    note.expression = {11: cc11_list}
                    notes.append(note)
                    t += step
                    step_idx += 1

            elif self.stroke_pattern == "chime":
                # Beautiful arpeggiated melodic motifs
                step = 1.0  # Quarter notes or half notes based on density
                if self.params.density < 0.4:
                    step = 2.0
                t = chord.start
                step_idx = 0
                
                while t < chord.start + chord.duration:
                    # Select pitches from chord tones
                    target_pc = pcs[step_idx % len(pcs)]
                    chime_pitch = nearest_pitch(target_pc, anchor + (step_idx % 3) * 3)
                    chime_pitch = snap_to_scale(chime_pitch, key)
                    chime_pitch = max(self.params.key_range_low, min(self.params.key_range_high, chime_pitch))

                    vel = int(95 + random.randint(-8, 8))
                    ring_dur = max(2.0, step * 2.0)
                    
                    note = NoteInfo(
                        pitch=chime_pitch,
                        start=round(t, 6),
                        duration=ring_dur,
                        velocity=max(1, min(127, vel)),
                    )
                    
                    # Ringing decay tail
                    decay_steps = 8
                    cc11_list = []
                    max_decay = 100 if self.dampen else 50
                    for s in range(decay_steps + 1):
                        cc11_list.append(((s / decay_steps) * ring_dur, int(127 - max_decay * (s / decay_steps))))
                    note.expression = {11: cc11_list}
                    
                    notes.append(note)
                    t += step
                    step_idx += 1

            else:  # "single" bell strike
                # Strong initial impact on chord change, rings throughout the chord
                vel = int(115 + random.randint(-5, 8))  # High-velocity impact
                ring_dur = max(4.0, chord.duration * 1.2)
                
                note = NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=ring_dur,
                    velocity=max(1, min(127, vel)),
                )
                
                # Exponential/linear decay automation on CC 11 to simulate metal resonance decay
                steps = 15
                cc11_list = []
                # If dampened, chimes decay very quickly (damping felt applied to tubes)
                max_damp = 115 if self.dampen else 70
                for s in range(steps + 1):
                    progress = s / steps
                    val = int(127 - max_damp * (progress ** 0.7))
                    cc11_list.append(((s / steps) * ring_dur, val))
                
                note.expression = {11: cc11_list}
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
