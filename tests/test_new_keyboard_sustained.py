# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.keyboard_sustained import (
    ChurchOrganGenerator,
    AccordionGenerator,
    HarmonicaGenerator,
    PercussiveOrganGenerator,
    RockOrganGenerator,
    ReedOrganGenerator,
)

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


def test_percussive_organ_generator():
    gen = PercussiveOrganGenerator(click_octave_offset=2)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Generates main sustained drawbar chord tones + short percussive key click note
    assert len(notes) >= 2
    # Find the percussive click note (should be duration 0.08)
    clicks = [n for n in notes if n.duration == 0.08]
    assert len(clicks) == 1
    # Click should be higher velocity
    main_organ_notes = [n for n in notes if n.duration > 0.5]
    assert len(main_organ_notes) >= 1
    assert clicks[0].velocity > main_organ_notes[0].velocity


def test_rock_organ_generator():
    gen = RockOrganGenerator(leslie_speed_hz=6.0)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Fat 3-voice voicing (Root, 5th, Octave)
    assert len(notes) >= 3
    # Rotary Leslie speaker sweep on CC 11 and CC 1
    for note in notes:
        assert note.expression is not None
        assert 11 in note.expression
        assert 1 in note.expression
        lfo_list = note.expression[11]
        assert len(lfo_list) > 10


def test_reed_organ_generator():
    gen = ReedOrganGenerator()
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # 2-voice reed stops
    assert len(notes) == 2
    # Slow harmonium air pump curve on CC 11
    assert all(n.expression is not None and 11 in n.expression for n in notes)
