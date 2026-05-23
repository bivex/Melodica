# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.ethnic_world import EthnicWorldGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_ethnic_world_banjo():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Banjo with low complexity (triplets)
    gen_low = EthnicWorldGenerator(instrument="banjo")
    gen_low.params.complexity = 0.3
    notes_low = gen_low.render(chords, C_MAJOR, 4.0)
    assert len(notes_low) == 3
    # Check start times are spaced out by 1.33 beats
    assert notes_low[1].start == pytest.approx(1.333333, abs=1e-3)

    # 2. Banjo with high complexity (quadruplets/rolls)
    gen_high = EthnicWorldGenerator(instrument="banjo")
    gen_high.params.complexity = 0.8
    notes_high = gen_high.render(chords, C_MAJOR, 4.0)
    assert len(notes_high) == 4
    # Check start times are spaced out by 1.0 beats
    assert notes_high[1].start == pytest.approx(1.0, abs=1e-3)


def test_ethnic_world_shamisen():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = EthnicWorldGenerator(instrument="shamisen")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.duration < 3.0  # Decays quickly
    assert note.expression is not None
    assert 11 in note.expression
    assert "pitch_bend" in note.expression


def test_ethnic_world_bagpipe():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = EthnicWorldGenerator(instrument="bagpipe")
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Drone note + Melody note = 2 notes
    assert len(notes) == 2
    # One note is a low drone note (pitch in 30-60 range)
    drone = notes[0]
    pipe = notes[1]
    assert drone.pitch < pipe.pitch
    assert drone.duration == 4.0
    assert 11 in drone.expression


def test_ethnic_world_fiddle():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = EthnicWorldGenerator(instrument="fiddle")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 11 in note.expression
    assert 1 in note.expression
    assert "pitch_bend" in note.expression


def test_ethnic_world_shanai():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    gen = EthnicWorldGenerator(instrument="shanai")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 1
    note = notes[0]
    assert note.expression is not None
    assert 11 in note.expression
    assert 74 in note.expression
    assert "pitch_bend" in note.expression
