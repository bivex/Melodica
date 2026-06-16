# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.wind_brass_solo import EuphoniumGenerator, AltoFluteGenerator
from melodica.generators.plucked_solo import KalimbaGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_euphonium_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = EuphoniumGenerator(note_density=1.0)
    notes = gen.render(chords, C_MAJOR, 4.0)

    assert len(notes) >= 1
    # Check that it produces notes within Bb1 (34) to Bb4 (70)
    for note in notes:
        assert 34 <= note.pitch <= 70
        # Check slow marcato swell on CC 11
        assert note.expression is not None
        assert 11 in note.expression


def test_alto_flute_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = AltoFluteGenerator(breath_vibrato=True, note_density=1.0)
    notes = gen.render(chords, C_MAJOR, 4.0)

    assert len(notes) >= 1
    # Check that it produces notes within G3 (55) to G6 (91)
    for note in notes:
        assert 55 <= note.pitch <= 91
        # Check breath vibrato on CC 11
        assert note.expression is not None
        assert 11 in note.expression


def test_kalimba_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    # Set high pop_intensity to guarantee we get harmonic pop transients
    gen = KalimbaGenerator(pop_intensity=0.9, note_density=1.0)
    
    # Run a few times to account for random chance of pop transient (0.7 probability)
    notes = []
    for _ in range(5):
        notes = gen.render(chords, C_MAJOR, 4.0)
        if len(notes) > 1:
            break

    assert len(notes) >= 1
    # Check key range C3 (48) to C6 (84)
    for note in notes:
        assert 48 <= note.pitch <= 84
