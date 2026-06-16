# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.arabic_ensemble import OudGenerator, NeyGenerator, DarbukaGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_oud_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Standard Oud (with double-strings chorus)
    gen = OudGenerator(tremolo_density=0.0, chorus_detune=0.15)
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 2  # due to double string plucks
    # Check pitch bend expression
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)

    # 2. Tremolo Oud
    gen_tremolo = OudGenerator(tremolo_density=1.0)
    notes_trem = gen_tremolo.render(chords, C_MAJOR, 4.0)
    assert len(notes_trem) >= 4  # multiple rapid plucks


def test_ney_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = NeyGenerator(breath_noise=0.5, vibrato_depth=0.6, legato_glide=0.3)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check Expression CC 11 points are generated
    assert any(n.expression is not None and 11 in n.expression for n in notes)


def test_darbuka_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Standard Darbuka pattern
    gen = DarbukaGenerator(rhythm_pattern="maqsoum", rolls_probability=0.0)
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 4
    assert all(n.absolute for n in notes)

    # Darbuka with rolls
    gen_rolls = DarbukaGenerator(rhythm_pattern="maqsoum", rolls_probability=1.0)
    notes_rolls = gen_rolls.render(chords, C_MAJOR, 4.0)
    assert len(notes_rolls) > len(notes)  # rolls subdivide steps, creating more notes
