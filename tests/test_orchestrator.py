# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.form import MusicalForm
from melodica.dynamics_arc import DynamicsArc
from melodica.orchestrator import OrchestralLayer, Orchestrator
from melodica.generators.orchestral_strings import ViolinGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_orchestrator_rendering():
    # Set up some simple layers
    violin = ViolinGenerator()
    flute = FluteGenerator()
    
    layer1 = OrchestralLayer(
        name="violin_solo",
        generator=violin,
        family="strings",
        role="melody",
        density_curve="sparse_to_dense",
    )
    
    layer2 = OrchestralLayer(
        name="flute_solo",
        generator=flute,
        family="woodwinds",
        role="solo",
        density_curve="constant",
    )
    
    form = MusicalForm.ternary(C_MAJOR, 20.0)
    arc = DynamicsArc.from_form(form)
    
    orchestrator = Orchestrator(
        layers=[layer1, layer2],
        form=form,
        dynamics=arc,
    )
    
    chords = [
        ChordLabel(root=0, quality="maj", start=0.0, duration=4.0),
        ChordLabel(root=5, quality="maj", start=4.0, duration=4.0),
        ChordLabel(root=7, quality="maj", start=8.0, duration=4.0),
        ChordLabel(root=0, quality="maj", start=12.0, duration=8.0),
    ]
    
    rendered = orchestrator.render(chords, C_MAJOR, 20.0)
    
    assert "violin_solo" in rendered
    assert "flute_solo" in rendered
    
    # Active families test:
    # Section 1 (A): start=0, duration=8. Active: ["strings", "woodwinds"].
    # Section 2 (B): start=8, duration=6. Active: ["strings", "woodwinds", "choir"].
    # Section 3 (A_prime): start=14, duration=6. Active: ["strings", "brass", "woodwinds", "percussion"].
    # So strings and woodwinds are active in all sections.
    assert len(rendered["violin_solo"]) > 0
    assert len(rendered["flute_solo"]) > 0


def test_note_density_effect():
    violin_low = ViolinGenerator(note_density=0.5)
    violin_high = ViolinGenerator(note_density=2.0)
    
    chords = [ChordLabel(root=0, quality="maj", start=0.0, duration=4.0)]
    
    notes_low = violin_low.render(chords, C_MAJOR, 4.0)
    notes_high = violin_high.render(chords, C_MAJOR, 4.0)
    
    # Higher note density should produce significantly more notes!
    assert len(notes_high) >= 2 * len(notes_low)


def test_ensemble_mode_effect():
    strings_solo = StringsLegatoGenerator(ensemble_mode="solo")
    strings_tutti = StringsLegatoGenerator(ensemble_mode="tutti")
    
    chords = [ChordLabel(root=0, quality="maj", start=0.0, duration=4.0)]
    
    notes_solo = strings_solo.render(chords, C_MAJOR, 4.0)
    notes_tutti = strings_tutti.render(chords, C_MAJOR, 4.0)
    
    # Tutti should generate divisi/unison voices, producing more note entries
    assert len(notes_tutti) > len(notes_solo)
