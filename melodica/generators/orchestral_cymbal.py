# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_cymbal.py -- Orchestral cymbals generator.

Layer: Application / Domain
Style: Classical, cinematic, orchestral percussion.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale

# GM Cymbal pitches
CYMBAL_CRASH = 49    # Crash Cymbal 1
CYMBAL_CHINESE = 52  # Chinese Cymbal
CYMBAL_RIDE = 51     # Ride Cymbal 1 (Sizzle/Sustain)
CYMBAL_SPLASH = 55   # Splash Cymbal


class OrchestralCymbalGenerator(PhraseGenerator):
    """
    OrchestralCymbalGenerator: Generates high-fidelity orchestral cymbal events.
    
    pattern_type:
        "crash"  -- Loud accented hits at phrase boundaries with long ringing tails.
        "rolls"  -- Suspended cymbal crescendo rolls using rapid subdivisions & CC 11 swells.
        "sizzle" -- Sustained sizzle ride textures supporting the groove.
    """

    name: str = "Orchestral Cymbal Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern_type: str = "crash",
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
        
        # Render cymbals per segment
        for i, chord in enumerate(chords):
            is_first = (i == 0)
            is_last = (i == len(chords) - 1)
            
            if self.pattern_type == "crash":
                notes.extend(self._render_crash(chord.start, chord.duration, is_first, is_last))
            elif self.pattern_type == "rolls":
                notes.extend(self._render_rolls(chord.start, chord.duration))
            else:  # sizzle
                notes.extend(self._render_sizzle(chord.start, chord.duration))

        if notes:
            notes.sort(key=lambda n: n.start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )

        return notes

    def _render_crash(self, start: float, duration: float, is_first: bool, is_last: bool) -> list[NoteInfo]:
        """Generates powerful, ringing crash hits at the start of sections."""
        notes: list[NoteInfo] = []
        
        # A crash typically occurs at the very beginning of a phrase/section
        # Or occasionally on beat 3 of a bar if intensity is high
        prob = 1.0 if is_first else (self.params.density * 0.4)
        if random.random() < prob:
            vel = int(105 + random.randint(5, 20))
            # Large ringing duration (reverb tail)
            ring_dur = max(4.0, duration * 1.5)
            
            note = NoteInfo(
                pitch=CYMBAL_CRASH,
                start=round(start, 6),
                duration=ring_dur,
                velocity=max(1, min(127, vel)),
            )
            
            # Decay automation via CC 11 to simulate fade-out tail
            steps = 10
            cc11_list = []
            for s in range(steps + 1):
                t_rel = (s / steps) * ring_dur
                val = int(127 - 110 * (s / steps) ** 0.5)
                cc11_list.append((t_rel, val))
            
            note.expression = {11: cc11_list}
            notes.append(note)

        # Chinese cymbal accent at the end of a big phrase
        if is_last and random.random() < 0.5:
            notes.append(NoteInfo(
                pitch=CYMBAL_CHINESE,
                start=round(start + duration - 0.5, 6),
                duration=2.0,
                velocity=115,
            ))

        return notes

    def _render_rolls(self, start: float, duration: float) -> list[NoteInfo]:
        """Generates suspended cymbal crescendo rolls using a rapid note stream and CC 11 swells."""
        notes: list[NoteInfo] = []
        step = 0.125  # 16th notes
        t = start

        cc11_list = []
        steps = int(duration / step)
        steps = max(4, steps)

        for s in range(steps):
            curr_t = start + s * step
            if curr_t >= start + duration:
                break
            
            progress = s / steps
            # Exponential crescendo shape
            cc11_val = int(15 + 105 * (progress ** 1.8))
            cc11_list.append((s * step, cc11_val))

            # Alternate hit intensity
            hand_variation = int(random.uniform(-4, 4))
            base_vel = int(40 + 50 * progress)
            vel = base_vel + hand_variation

            # Add subtle timing jitter
            jitter = random.uniform(-0.006, 0.006)

            note = NoteInfo(
                pitch=CYMBAL_SPLASH,
                start=round(curr_t + jitter, 6),
                duration=step * 1.2,  # Let notes overlap slightly to blend
                velocity=max(1, min(127, vel)),
            )
            notes.append(note)

        # Attach CC 11 swell curves to all notes in the roll
        for note in notes:
            note.expression = {11: cc11_list}

        # Accent crash hit at the very peak of the roll
        if notes:
            notes.append(NoteInfo(
                pitch=CYMBAL_CRASH,
                start=round(start + duration - 0.05, 6),
                duration=4.0,
                velocity=120,
            ))

        return notes

    def _render_sizzle(self, start: float, duration: float) -> list[NoteInfo]:
        """Generates sustained sizzle/ride patterns supporting the harmonic rhythm."""
        notes: list[NoteInfo] = []
        t = start
        step = 0.5  # 8th notes
        density = self.params.density

        while t < start + duration:
            beat_num = int(t) % 4
            
            # Higher probability on strong beats (downbeats)
            prob = 0.85 if (t - int(t) == 0.0) else (density * 0.5)
            if random.random() < prob:
                is_downbeat = (t - int(t) == 0.0)
                vel = int((75 if is_downbeat else 50) + random.randint(-6, 6))
                
                # Alternate between Ride and Splash to create dynamic texture
                pitch = CYMBAL_RIDE if (beat_num in (0, 2)) else CYMBAL_SPLASH
                
                note = NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=0.4,
                    velocity=max(1, min(127, vel)),
                )
                
                # A subtle sizzle filter sweep
                note.expression = {74: [(0.0, 70), (0.3, 90)]}
                notes.append(note)

            t += step

        return notes
