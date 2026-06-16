# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/snare_drum.py -- Orchestral snare drum percussion generator.

Layer: Application / Domain
Style: Classical, cinematic, military march, orchestral percussion.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale

# GM Snare pitches
SNARE_AC = 38       # Acoustic Snare
SNARE_SIDE = 37     # Side Stick / Rimshot accent
SNARE_ROLL = 40     # Electric/Roll snare or alternative brush/rim sound


class SnareDrumGenerator(PhraseGenerator):
    """
    SnareDrumGenerator: Generates high-fidelity orchestral snare drum patterns.
    
    pattern_type:
        "march"   -- Syncopated military grooves with flams and rolls.
        "roll"    -- Rapid continuous dynamic rolls using dynamic swells.
        "rimshot" -- Powerful accented rimshot hits on key beats.
    density:
        Determines the frequency of ghost notes and subdivisions (0.0 to 1.0).
    """

    name: str = "Snare Drum Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "march",
    ) -> None:
        super().__init__(params)
        self.pattern_type = pattern_type
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
            # Render patterns per chord segment
            if self.pattern_type == "roll":
                notes.extend(self._render_roll(chord.start, chord.duration))
            elif self.pattern_type == "rimshot":
                notes.extend(self._render_rimshot(chord.start, chord.duration))
            else:  # march
                notes.extend(self._render_march(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )

        return notes

    def _render_march(self, start: float, duration: float) -> list[NoteInfo]:
        """Generates authentic military march themes with flams and syncopations."""
        notes: list[NoteInfo] = []
        t = start
        beat_step = 0.25  # 16th notes
        
        # A march rhythm template per beat: 4 16th slots
        # We can randomize/syncopate based on density
        density = self.params.density

        while t < start + duration:
            rel_t = t - start
            beat_in_bar = t % 4.0
            
            # Flam on beat 1 or 3
            if abs(beat_in_bar - 0.0) < 0.01 or abs(beat_in_bar - 2.0) < 0.01:
                # Double hit (flam): soft grace note right before the main hit
                notes.append(NoteInfo(
                    pitch=SNARE_AC,
                    start=round(t - 0.04, 6),
                    duration=0.05,
                    velocity=max(1, min(127, int(50 + random.randint(-5, 5)))),
                ))
                notes.append(NoteInfo(
                    pitch=SNARE_AC,
                    start=round(t, 6),
                    duration=0.1,
                    velocity=max(1, min(127, int(100 + random.randint(-5, 5)))),
                ))
            else:
                # Deciding whether to place a note based on typical march accents
                prob = 0.8 if (t - int(t) == 0 or t - int(t) == 0.5) else (density * 0.6)
                if random.random() < prob:
                    # Accent weak/strong beats differently
                    is_accent = (t - int(t) == 0.0) or (t - int(t) == 0.75 and random.random() < 0.5)
                    vel = int((95 if is_accent else 70) + random.randint(-8, 8))
                    
                    notes.append(NoteInfo(
                        pitch=SNARE_AC,
                        start=round(t, 6),
                        duration=0.1,
                        velocity=max(1, min(127, vel)),
                    ))

            # Add occasional triplet/sextuplet fills on beat 4
            if abs(beat_in_bar - 3.0) < 0.01 and density > 0.5:
                # Add rapid triplet roll instead of regular steps
                for i in range(6):
                    triplet_t = t + i * (1.0 / 6.0)
                    if triplet_t < start + duration:
                        notes.append(NoteInfo(
                            pitch=SNARE_AC,
                            start=round(triplet_t, 6),
                            duration=0.06,
                            velocity=max(1, min(127, int(65 + i * 8 + random.randint(-5, 5)))),
                        ))
                t += 1.0
            else:
                t += beat_step

        return notes

    def _render_roll(self, start: float, duration: float) -> list[NoteInfo]:
        """Generates continuous dynamic rolls (crescendo swells) with micro-timing adjustments."""
        notes: list[NoteInfo] = []
        # Roll density: 32nd notes (0.0625 beats) or 16th notes (0.125 beats) based on density param
        step = 0.0625 if self.params.density > 0.5 else 0.125
        t = start

        # We will also add a continuous CC 11 swell
        cc11_list = []
        steps = int(duration / step)
        steps = max(5, steps)

        for s in range(steps):
            curr_t = start + s * step
            if curr_t >= start + duration:
                break
            
            # Dynamic crescendo shape
            progress = s / steps
            cc11_val = int(35 + 85 * (progress ** 1.5))
            cc11_list.append((s * step, cc11_val))

            # Left/right hand alternate volume variation (double strokes: L L R R)
            hand_variation = 6 if (s % 4 in (0, 1)) else -6
            base_vel = int(60 + 40 * progress)
            vel = base_vel + hand_variation + random.randint(-5, 5)

            # Micro-timing humanization/flurry
            jitter = random.uniform(-0.005, 0.005)
            
            note = NoteInfo(
                pitch=SNARE_ROLL,
                start=round(curr_t + jitter, 6),
                duration=step * 0.9,
                velocity=max(1, min(127, vel)),
            )
            notes.append(note)

        # Attach expression curves to notes to make them respond dynamically
        # Since these notes form a continuous roll, we can attach the CC 11 swell list to all of them
        for note in notes:
            note.expression = {11: cc11_list}

        return notes

    def _render_rimshot(self, start: float, duration: float) -> list[NoteInfo]:
        """Generates powerful rimshot hits on beat 1 and 3 with ghost note fills."""
        notes: list[NoteInfo] = []
        t = start
        density = self.params.density

        while t < start + duration:
            beat_in_bar = t % 4.0
            is_beat_1_or_3 = abs(beat_in_bar - 0.0) < 0.01 or abs(beat_in_bar - 2.0) < 0.01
            
            if is_beat_1_or_3:
                # Heavy rimshot
                notes.append(NoteInfo(
                    pitch=SNARE_SIDE,
                    start=round(t, 6),
                    duration=0.15,
                    velocity=127,  # Max impact
                ))
                # Add a flam or echo ghost note right after it
                if random.random() < 0.7:
                    notes.append(NoteInfo(
                        pitch=SNARE_AC,
                        start=round(t + 0.125, 6),
                        duration=0.08,
                        velocity=max(1, min(127, int(40 + density * 20))),
                    ))
            else:
                # Random ghost notes on other beats
                if random.random() < (density * 0.4):
                    notes.append(NoteInfo(
                        pitch=SNARE_AC,
                        start=round(t, 6),
                        duration=0.08,
                        velocity=max(1, min(127, int(30 + random.randint(5, 20)))),
                    ))

            t += 0.25  # step in 16ths

        return notes
