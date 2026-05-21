# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-21 12:40
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/accent.py — RhythmicAccentGenerator.

Customizable rhythmic accent and percussion pattern generator.
Supports march, gallop, waltz, heavy, syncopated, and custom sequences.
Pitches can be custom-fixed or mapped dynamically to chord roots with octave shifting.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import chord_at

# Presets mapping pattern names to a list of tuples: (relative_beat, base_velocity, duration)
# Cycle duration is the length of one loop (e.g. 4.0 for standard bar, 3.0 for waltz).
PRESETS: dict[str, dict[str, any]] = {
    "march": {
        "cycle": 4.0,
        "pattern": [
            (0.0, 100, 0.4),
            (0.5, 70, 0.25),
            (1.0, 85, 0.4),
            (1.5, 70, 0.25),
            (2.0, 100, 0.4),
            (2.5, 70, 0.25),
            (3.0, 85, 0.4),
            (3.5, 70, 0.25),
        ],
    },
    "gallop": {
        "cycle": 2.0,
        "pattern": [
            (0.0, 100, 0.35),
            (0.5, 60, 0.15),
            (0.75, 80, 0.15),
            (1.0, 95, 0.35),
            (1.5, 60, 0.15),
            (1.75, 80, 0.15),
        ],
    },
    "waltz": {
        "cycle": 3.0,
        "pattern": [
            (0.0, 105, 0.6),
            (1.0, 75, 0.4),
            (2.0, 75, 0.4),
        ],
    },
    "heavy": {
        "cycle": 4.0,
        "pattern": [
            (0.0, 120, 0.8),
            (2.0, 100, 0.6),
        ],
    },
    "syncopated": {
        "cycle": 4.0,
        "pattern": [
            (0.5, 100, 0.4),
            (1.5, 100, 0.4),
            (2.5, 100, 0.4),
            (3.5, 100, 0.4),
        ],
    },
}

@dataclass
class RhythmicAccentGenerator(PhraseGenerator):
    """
    Rhythmic accent and percussion pattern generator.
    Creates structured patterns (timpani rolls, march beats, gallops, etc.).
    
    preset: Preset pattern name ('march', 'gallop', 'waltz', 'heavy', 'syncopated')
    pitch: Optional static MIDI pitch. If None, dynamically maps to chord roots.
    octave: Octave transpose for chord root mapping (used if pitch is None). Default 3.
    velocity_humanize: Random velocity jitter added/subtracted from accents.
    accent_strength: Global multiplier to scale velocities (0.0 to 2.0).
    custom_sequence: Custom list of (relative_beat, velocity, duration) to override presets.
    custom_cycle: Length of custom sequence cycle (defaults to max beat if custom_sequence is set).
    """
    
    preset: str = "march"
    pitch: int | None = None
    octave: int = 3
    velocity_humanize: int = 10
    accent_strength: float = 1.0
    custom_sequence: list[tuple[float, int, float]] | None = None
    custom_cycle: float | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        preset: str = "march",
        pitch: int | None = None,
        octave: int = 3,
        velocity_humanize: int = 10,
        accent_strength: float = 1.0,
        custom_sequence: list[tuple[float, int, float]] | None = None,
        custom_cycle: float | None = None,
    ) -> None:
        super().__init__(params)
        self.preset = preset
        self.pitch = pitch
        self.octave = octave
        self.velocity_humanize = max(0, velocity_humanize)
        self.accent_strength = accent_strength
        self.custom_sequence = custom_sequence
        self.custom_cycle = custom_cycle

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        # Determine the pattern and cycle length
        if self.custom_sequence is not None:
            pattern = self.custom_sequence
            if self.custom_cycle is not None:
                cycle_len = self.custom_cycle
            else:
                cycle_len = max((b for b, _, _ in self.custom_sequence), default=4.0)
                if cycle_len == 0.0:
                    cycle_len = 4.0
        else:
            preset_data = PRESETS.get(self.preset, PRESETS["march"])
            pattern = preset_data["pattern"]
            cycle_len = preset_data["cycle"]

        notes: list[NoteInfo] = []
        
        # Loop over the total duration_beats
        current_beat = 0.0
        while current_beat < duration_beats:
            # We want to fill the current cycle
            for rel_beat, base_vel, dur in pattern:
                note_start = current_beat + rel_beat
                if note_start >= duration_beats:
                    continue

                # Find chord at the note start to get dynamically mapped pitch
                chord = chord_at(chords, note_start)
                if chord is None:
                    chord = chords[-1]

                # Pitch logic
                if self.pitch is not None:
                    final_pitch = self.pitch
                else:
                    # Map to chord root + octave transpose
                    final_pitch = (chord.root % 12) + (self.octave * 12)

                # Clamp final pitch to MIDI ranges
                final_pitch = max(0, min(127, final_pitch))

                # Velocity logic
                vel = int(base_vel * self.accent_strength)
                if self.velocity_humanize > 0:
                    vel += random.randint(-self.velocity_humanize, self.velocity_humanize)
                final_vel = max(1, min(127, vel))

                notes.append(
                    NoteInfo(
                        pitch=final_pitch,
                        start=round(note_start, 6),
                        duration=round(dur, 6),
                        velocity=final_vel,
                    )
                )

            current_beat += cycle_len

        # Sort notes by start beat to ensure chronological order
        notes.sort(key=lambda n: n.start)
        return notes
