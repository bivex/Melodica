# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica/orchestrator.py — Central orchestral orchestrator and layer coordinator.
Aligns multitrack generation with musical form and macro-dynamics.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.form import FormSection, MusicalForm
from melodica.dynamics_arc import DynamicsArc


@dataclass
class OrchestralLayer:
    name: str                    # "violins", "horns", "choir", ...
    generator: PhraseGenerator
    family: str                  # "strings", "brass", "woodwinds", "percussion", "choir"
    role: str                    # "melody", "harmony", "bass", "rhythm", "pad", "solo"
    density_curve: str           # "constant", "sparse_to_dense", "dense_to_sparse"
    default_params: dict = field(default_factory=dict)  # default constructor/param settings


@dataclass
class Orchestrator:
    layers: list[OrchestralLayer]
    form: MusicalForm
    dynamics: DynamicsArc

    def render(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float
    ) -> dict[str, list[NoteInfo]]:
        """Renders all layers, aligning notes with musical form, dynamics, and tempo maps."""
        tracks: dict[str, list[NoteInfo]] = {layer.name: [] for layer in self.layers}

        for section in self.form.sections:
            active = self._active_layers(section)
            section_chords = self._chords_in_section(chords, section)

            for layer in active:
                # Modify generator density parameters
                params = self._apply_density_curve(layer, section)
                
                # Apply extra defaults if configured
                for k, v in layer.default_params.items():
                    if hasattr(layer.generator, k):
                        setattr(layer.generator, k, v)
                
                # Render section phrase
                # The generator expects relative chords and duration
                notes = layer.generator.render(
                    section_chords, key, section.duration_beats
                )

                # Offset onset to start_beat of the section
                self._offset_notes(notes, section.start_beat)

                # Apply macro-dynamics (DynamicsArc)
                self._apply_section_dynamics(notes, section)

                # Apply tempo stretching/squeezing
                self._apply_tempo(notes, section.tempo_multiplier, section.start_beat)

                tracks[layer.name].extend(notes)

        # Sort all generated notes by start time
        for name in tracks:
            tracks[name] = sorted(tracks[name], key=lambda x: x.start)

        return tracks

    def _active_layers(self, section: FormSection) -> list[OrchestralLayer]:
        """Returns the layers that are active in the given section."""
        # A layer is active if its family is enabled in the section's active_families list
        return [
            layer for layer in self.layers
            if layer.family in section.active_families
        ]

    def _chords_in_section(self, chords: list[ChordLabel], section: FormSection) -> list[ChordLabel]:
        """Slices and shifts chords to be 0-based relative to the section start beat."""
        sec_start = section.start_beat
        sec_end = section.end_beat
        sliced: list[ChordLabel] = []

        for chord in chords:
            c_start = chord.start
            c_end = chord.start + chord.duration

            overlap_start = max(c_start, sec_start)
            overlap_end = min(c_end, sec_end)

            if overlap_start < overlap_end:
                # Shift start to 0-based relative to section
                new_start = overlap_start - sec_start
                new_dur = overlap_end - overlap_start

                sliced.append(
                    dataclasses.replace(
                        chord,
                        start=round(new_start, 6),
                        duration=round(new_dur, 6)
                    )
                )
        return sliced

    def _apply_density_curve(self, layer: OrchestralLayer, section: FormSection) -> GeneratorParams:
        """Modifies density and note_density parameters based on the section and role."""
        gen = layer.generator
        curve = layer.density_curve

        # Baseline density
        density = 0.5
        if curve == "sparse_to_dense":
            # Scale up through the sections
            total_sections = len(self.form.sections)
            try:
                idx = self.form.sections.index(section)
            except ValueError:
                idx = 0
            # From 0.3 to 0.9
            density = 0.3 + (idx / max(total_sections - 1, 1)) * 0.6
        elif curve == "dense_to_sparse":
            total_sections = len(self.form.sections)
            try:
                idx = self.form.sections.index(section)
            except ValueError:
                idx = 0
            # From 0.9 down to 0.3
            density = 0.9 - (idx / max(total_sections - 1, 1)) * 0.6
        else:
            # Constant density: check default config or fallback to 0.6
            density = gen.params.density if gen.params else 0.6

        # Set the density on the generator parameters
        if gen.params:
            gen.params.density = max(0.01, min(1.0, density))

        # Also set note_density attribute if supported by the generator
        if hasattr(gen, "note_density"):
            # Set note_density based on roles and section density
            if layer.role in ("melody", "solo"):
                setattr(gen, "note_density", round(density * 2.0, 2))
            else:
                setattr(gen, "note_density", round(density * 1.5, 2))

        return gen.params

    def _offset_notes(self, notes: list[NoteInfo], offset: float) -> None:
        """Offsets the start of each note by the given amount."""
        for note in notes:
            note.start = round(note.start + offset, 6)

    def _apply_section_dynamics(self, notes: list[NoteInfo], section: FormSection) -> list[NoteInfo]:
        """Scales velocity of notes using the global DynamicsArc curve."""
        for note in notes:
            # Query the dynamics multiplier at this note's absolute start beat
            mult = self.dynamics.velocity_at(note.start)
            note.velocity = max(1, min(127, int(note.velocity * mult)))
        return notes

    def _apply_tempo(self, notes: list[NoteInfo], multiplier: float, section_start: float) -> None:
        """Stretches/squeezes note onsets and durations inside the section."""
        if multiplier == 1.0:
            return
        
        for note in notes:
            # Relative onset within the section
            rel_onset = note.start - section_start
            # Scale start and duration
            note.start = round(section_start + rel_onset * multiplier, 6)
            note.duration = round(note.duration * multiplier, 6)
