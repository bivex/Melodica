# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.synth_effects import SynthEffectsGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_synth_effects_rain():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="rain")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 10 in note.expression
    # Verify panning values are between 0 and 127
    for t, val in note.expression[10]:
        assert 0 <= val <= 127


def test_synth_effects_soundtrack():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="soundtrack")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 11 in note.expression
    assert 74 in note.expression


def test_synth_effects_crystal():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="crystal")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 93 in note.expression
    assert note.expression[93][0][1] == 110


def test_synth_effects_atmosphere():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="atmosphere")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 11 in note.expression


def test_synth_effects_brightness():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="brightness")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Pitch should be higher (+24 semitones)
    assert notes[0].pitch > 50


def test_synth_effects_goblins():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="goblins")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.duration < 2.0  # staccato
    assert note.expression is not None
    assert 74 in note.expression


def test_synth_effects_echoes():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="echoes")
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Renders 1 main note + 2 echoes
    assert len(notes) == 3
    # Check start times are staggered
    assert notes[0].start < notes[1].start < notes[2].start
    # Check velocities decay
    assert notes[0].velocity > notes[1].velocity > notes[2].velocity


def test_synth_effects_sci_fi():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = SynthEffectsGenerator(fx_type="sci_fi")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 1 in note.expression
    assert 74 in note.expression
