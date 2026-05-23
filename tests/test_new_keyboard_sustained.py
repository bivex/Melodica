# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.keyboard_sustained import ChurchOrganGenerator, AccordionGenerator, HarmonicaGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_church_organ_generator():
    gen = ChurchOrganGenerator(stops="full")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Mixture stop generates doubled registers
    assert len(notes) >= 2


def test_accordion_generator():
    gen = AccordionGenerator(register="master")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 2
    # Bellows pressure sweep on CC 11
    assert notes[0].expression is not None


def test_harmonica_generator():
    gen = HarmonicaGenerator(blues_harp=True)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 1
