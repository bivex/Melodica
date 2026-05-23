# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
import math
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.bass_solo import BassSoloGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_bass_solo_acoustic():
    gen = BassSoloGenerator(instrument="acoustic", style="groove")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Pitch should be standard low bass range
    assert 24 <= notes[0].pitch <= 55


def test_bass_solo_finger():
    gen = BassSoloGenerator(instrument="finger")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Check finger attack velocity (74 base)
    assert 68 <= notes[0].velocity <= 80


def test_bass_solo_pick():
    gen = BassSoloGenerator(instrument="pick")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Pick bass adds occasional high-octave click transients, so it may have 2 notes
    assert len(notes) >= 1
    # Check that click transient is extremely short and high octave
    clicks = [n for n in notes if n.duration == 0.04]
    if clicks:
        assert clicks[0].pitch > notes[0].pitch


def test_bass_solo_fretless():
    gen = BassSoloGenerator(instrument="fretless")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Fretless singing "mwah" CC 11 sweeps
    assert notes[0].expression is not None
    assert 11 in notes[0].expression
    assert len(notes[0].expression[11]) == 4


def test_bass_solo_slap():
    # Force popped octaves to occur
    random_seed = 42
    import random
    random.seed(random_seed)
    
    gen = BassSoloGenerator(instrument="slap_1")
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=2.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=2.0, duration=2.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=2.0),
        ChordLabel(root=0, quality=Quality.MAJOR, start=6.0, duration=2.0),
    ]
    
    notes = gen.render(chords, C_MAJOR, 8.0)
    # Slap & Pop renders primary slap note + short pop octave notes
    assert len(notes) >= 4
    # Pop notes have duration 0.1
    pops = [n for n in notes if n.duration == 0.1]
    assert len(pops) >= 1
    # Pop notes should be higher velocity and higher pitch
    slaps = [n for n in notes if n.duration > 0.5]
    assert pops[0].velocity > slaps[0].velocity
    assert pops[0].pitch == min(gen.params.key_range_high, slaps[0].pitch + 12)


def test_bass_solo_synth_1():
    gen = BassSoloGenerator(instrument="synth_1")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Synth 1 uses analog sweep CC 74
    assert notes[0].expression is not None
    assert 74 in notes[0].expression


def test_bass_solo_synth_2():
    gen = BassSoloGenerator(instrument="synth_2")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Synth 2 uses sub wobble CC 11
    assert notes[0].expression is not None
    assert 11 in notes[0].expression
    lfo = notes[0].expression[11]
    assert len(lfo) > 10
