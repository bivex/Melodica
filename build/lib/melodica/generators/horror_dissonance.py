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
generators/horror_dissonance.py — Horror game underscore generator.

Layer: Application / Domain
Style: Horror game audio, psychological horror, survival horror.

Generates specific horror scoring techniques:
  - Minor 2nd clusters (semitone friction)
  - Tritone intervals (diabolus in musica)
  - Chromatic crawls
  - Col legno/bowing drones
  - Sudden silence → impact
  - Pitch bends (detuned instruments)

Variants:
    "psychological" — subtle, unsettling (Silent Hill style)
    "jump_scare"    — sudden loud stabs
    "ambient_dread" — atmospheric dread
    "creature"      — creature approaching
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class HorrorDissonanceGenerator(PhraseGenerator):
    """
    Horror game underscore generator.

    variant:
        "psychological", "jump_scare", "ambient_dread", "creature"
    dissonance_level:
        How dissonant the material is (0.0-1.0).
        0 = mildly unsettling, 1 = maximally dissonant.
    silence_probability:
        Probability of sudden silence (0.0-1.0).
    pitch_drift:
        Amount of detuning/pitch drift (0.0-1.0).
    density:
        Note density (0.0-1.0). Lower = more sparse/creepy.
    """

    name: str = "Horror Dissonance Generator"
    variant: str = "psychological"
    dissonance_level: float = 0.7
    silence_probability: float = 0.15
    pitch_drift: float = 0.3
    density: float = 0.4
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "psychological",
        dissonance_level: float = 0.7,
        silence_probability: float = 0.15,
        pitch_drift: float = 0.3,
        density: float = 0.4,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.dissonance_level = max(0.0, min(1.0, dissonance_level))
        self.silence_probability = max(0.0, min(1.0, silence_probability))
        self.pitch_drift = max(0.0, min(1.0, pitch_drift))
        self.density = max(0.0, min(1.0, density))

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
        last_chord = chords[-1]
        bar_start = 0.0

        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            if self.variant == "psychological":
                self._render_psychological(notes, bar_start, duration_beats, chord)
            elif self.variant == "jump_scare":
                self._render_jump_scare(notes, bar_start, duration_beats, chord)
            elif self.variant == "ambient_dread":
                self._render_ambient_dread(notes, bar_start, duration_beats, chord)
            elif self.variant == "creature":
                self._render_creature(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_psychological(self, notes, bar_start, total, chord):
        """Subtle, unsettling — minor 2nd clusters, chromatic hints."""
        mid = 48
        root = chord.root
        # Minor 2nd cluster (root + b9)
        b9 = (root + 1) % 12
        tritone = (root + 6) % 12

        if random.random() > self.silence_probability:
            # Sustained cluster
            for pc in [root, b9]:
                if random.random() < self.density:
                    pitch = nearest_pitch(pc, mid)
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=35)
                    )
            # Random chromatic stabs
            t = bar_start
            while t < min(bar_start + 4.0, total):
                if random.random() < self.density * 0.3:
                    pc = (root + random.choice([1, 6, 11])) % 12
                    pitch = nearest_pitch(pc, mid + 12)
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(t, 6), duration=0.5, velocity=40)
                    )
                t += random.uniform(0.5, 1.5)

    def _render_jump_scare(self, notes, bar_start, total, chord):
        """Sudden loud stabs with silence before."""
        if random.random() < 0.3:
            return  # Silent bar (buildup)
        # Sudden cluster hit
        mid = 48
        root = chord.root
        vel = min(MIDI_MAX, int(90 + self.dissonance_level * 30))
        for interval in [0, 1, 6]:  # Root, minor 2nd, tritone
            pc = (root + interval) % 12
            pitch = nearest_pitch(pc, mid)
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=0.3, velocity=vel)
            )
        # Decay
        for interval in [0, 1]:
            pc = (root + interval) % 12
            pitch = nearest_pitch(pc, mid)
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start + 0.5, 6), duration=3.0, velocity=30)
            )

    def _render_ambient_dread(self, notes, bar_start, total, chord):
        """Low drones with dissonant overtones."""
        low = max(24, self.params.key_range_low)
        root_pitch = max(low, nearest_pitch(chord.root, low + 6))
        # Drone
        notes.append(
            NoteInfo(pitch=root_pitch, start=round(bar_start, 6), duration=3.8, velocity=45)
        )
        # Dissonant overtone
        if random.random() < self.dissonance_level:
            dissonant = (chord.root + random.choice([1, 6, 11])) % 12
            pitch = nearest_pitch(dissonant, root_pitch + 24)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(bar_start + random.uniform(0, 2), 6),
                    duration=2.0,
                    velocity=25,
                )
            )

    def _render_creature(self, notes, bar_start, total, chord):
        """Creature approaching — rising chromatic tension."""
        low = max(24, self.params.key_range_low)
        t = bar_start
        pitch = low
        while t < min(bar_start + 4.0, total):
            if random.random() < self.density:
                pitch = min(pitch + random.randint(0, 2), 84)
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=0.8, velocity=50))
            t += 0.5
