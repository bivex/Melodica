# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
import math
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.wind_brass_solo import (
    MutedTrumpetGenerator,
    SynthBrassGenerator,
    WoodwindSoloGenerator,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_muted_trumpet_generator():
    gen = MutedTrumpetGenerator(plunger_wah=True)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Pitch should be within Bb3 (58) to C6 (84)
    assert 58 <= notes[0].pitch <= 84
    # Plunger wah on CC 74 and CC 11
    assert notes[0].expression is not None
    assert 74 in notes[0].expression
    assert 11 in notes[0].expression


def test_synth_brass_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Synth Brass 1: sharp CC 74 analog envelope snap
    gen_1 = SynthBrassGenerator(brass_type="synth_brass_1", harmony_count=3)
    notes_1 = gen_1.render(chords, C_MAJOR, 4.0)
    assert len(notes_1) == 3
    assert all(n.expression is not None and 74 in n.expression for n in notes_1)
    
    # Synth Brass 2: warm detuned pad with CC 93 chorus send
    gen_2 = SynthBrassGenerator(brass_type="synth_brass_2", harmony_count=2)
    notes_2 = gen_2.render(chords, C_MAJOR, 4.0)
    assert len(notes_2) == 2
    assert all(n.expression is not None and 93 in n.expression for n in notes_2)


def test_woodwind_solo_generator_recorder():
    gen = WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    # Recorder key range Bb4 (60) to C6 (84)
    assert 60 <= notes[0].pitch <= 84
    # Breath vibrato LFO sweep on CC 11
    assert notes[0].expression is not None
    assert 11 in notes[0].expression
    assert len(notes[0].expression[11]) > 10


def test_woodwind_solo_generator_piccolo():
    gen = WoodwindSoloGenerator(instrument="piccolo")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # May generate high-register grace note ornaments, so >= 1
    assert len(notes) >= 1
    # Piccolo key range C5 (72) to C8 (108)
    assert 72 <= notes[0].pitch <= 108


def test_woodwind_solo_generator_pan_flute():
    # Force breath puff to occur
    import random
    random.seed(42)
    
    gen = WoodwindSoloGenerator(instrument="pan_flute")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Pan flute generates main note + optional high breath puff transient note
    assert len(notes) >= 1
    puffs = [n for n in notes if n.duration == 0.05]
    if puffs:
        assert puffs[0].velocity > notes[0].velocity


def test_woodwind_solo_generator_others():
    for inst in ("blown_bottle", "shakuhachi", "whistle", "ocarina"):
        gen = WoodwindSoloGenerator(instrument=inst)
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        notes = gen.render(chords, C_MAJOR, 4.0)
        assert len(notes) >= 1
