# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.east_asian_ensemble import ErhuGenerator, ShamisenGenerator, KotoGenerator
from melodica.generators.wind_brass_solo import WoodwindSoloGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_erhu_generator():
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
    ]
    
    gen = ErhuGenerator(glide_probability=1.0, vibrato_depth=0.3)
    notes = gen.render(chords, C_MAJOR, 8.0)
    
    assert len(notes) >= 2
    # Check pitch bend for slides and LFO vibrato
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)


def test_shamisen_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = ShamisenGenerator(sawari_buzz=0.6, strike_velocity=90)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check sawari buzz CC 12 is present
    assert any(n.expression is not None and 12 in n.expression for n in notes)


def test_koto_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Koto double pluck
    gen = KotoGenerator(tremolo_probability=0.0, double_pluck=True)
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 2

    # Koto tremolo plucks
    gen_trem = KotoGenerator(tremolo_probability=1.0, double_pluck=False)
    notes_trem = gen_trem.render(chords, C_MAJOR, 4.0)
    assert len(notes_trem) >= 3


def test_shakuhachi_factory_registration():
    # Verify that WoodwindSoloGenerator can be initialized as shakuhachi
    gen = WoodwindSoloGenerator(instrument="shakuhachi")
    assert gen.instrument == "shakuhachi"
