# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.cinematic_ethereal import GlassHarpGenerator, HandPanGenerator, ThereminGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_glass_harp_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = GlassHarpGenerator(friction_noise=0.5)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check CC 1 (Friction flutter) is present
    assert any(n.expression is not None and 1 in n.expression for n in notes)
    # Check CC 11 (swell) is present
    assert any(n.expression is not None and 11 in n.expression for n in notes)


def test_handpan_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    import random
    random.seed(0)
    gen = HandPanGenerator(strike_damping=0.3)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    # Damping < 0.8 triggers helper harmonics, so multiple notes should be generated
    assert len(notes) >= 2


def test_theremin_generator():
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
    ]
    
    gen = ThereminGenerator(vibrato_speed=6.0, vibrato_depth=0.5)
    notes = gen.render(chords, C_MAJOR, 8.0)
    
    assert len(notes) >= 2
    # Check pitch bend for slides and vibrato
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)
