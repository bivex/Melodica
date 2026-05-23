# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
import math
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.synth_choir_strings import (
    SynthStringsGenerator,
    VoiceOohsGMGenerator,
    SynthChoirGenerator,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_synth_strings_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Synth Strings 1
    gen_strings_1 = SynthStringsGenerator(string_type="synth_strings_1", harmony_count=3)
    notes_1 = gen_strings_1.render(chords, C_MAJOR, 4.0)
    # Harmony count 3 produces 3 notes
    assert len(notes_1) == 3
    assert all(n.expression is not None and 11 in n.expression for n in notes_1)

    # Synth Strings 2
    gen_strings_2 = SynthStringsGenerator(string_type="synth_strings_2", harmony_count=2)
    notes_2 = gen_strings_2.render(chords, C_MAJOR, 4.0)
    assert len(notes_2) == 2
    # Synth Strings 2 should have Chorus (93) and Modulation Wheel (1)
    for note in notes_2:
        assert note.expression is not None
        assert 93 in note.expression
        assert 1 in note.expression


def test_voice_oohs_gm_generator():
    gen_oohs = VoiceOohsGMGenerator(harmony_count=3, vibrato_depth=5)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen_oohs.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 3
    # Verify CC 1 expression vibrato pad sweep
    for note in notes:
        assert note.expression is not None
        assert 1 in note.expression
        # Breath phasing adds randomized start times
        assert note.start >= 0.0


def test_synth_choir_generator():
    gen = SynthChoirGenerator(harmony_count=3)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 3
    # Synth Choir has CC 74 vocoder LFO sweep and CC 11 swells
    for note in notes:
        assert note.expression is not None
        assert 74 in note.expression
        assert 11 in note.expression
        lfo_74 = note.expression[74]
        assert len(lfo_74) > 10
