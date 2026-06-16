# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.indian_ensemble import TanpuraGenerator, SitarGenerator, TablaGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_tanpura_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Standard Sa-Pa Tanpura
    gen = TanpuraGenerator(tuning="Sa-Pa", jivari=0.6, pluck_pattern="standard")
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 3
    # Check Jivari CC 12 is present
    assert any(n.expression is not None and 12 in n.expression for n in notes)
    # Check pitch bend contains micro-detuning
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)

    # 2. Sa-Ma Tanpura
    gen_ma = TanpuraGenerator(tuning="Sa-Ma", jivari=0.0)
    notes_ma = gen_ma.render(chords, C_MAJOR, 4.0)
    assert len(notes_ma) >= 3


def test_sitar_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = SitarGenerator(sympathetic_resonance=0.5, meend_probability=1.0, krintan_probability=1.0)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check Krintan / ornament note is generated
    assert any(n.articulation == "staccato" for n in notes)
    # Check primary note with meend pitch bend is generated
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)


def test_tabla_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = TablaGenerator(tala="teental", bayan_modulation=0.7)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 4
    # All notes should be marked absolute=True for percussion mapping
    assert all(n.absolute for n in notes)
    # Ghe strokes (MIDI 36) should have pitch_bend expression for slides
    ghe_notes = [n for n in notes if n.pitch == 36]
    if ghe_notes:
        assert any(n.expression is not None and "pitch_bend" in n.expression for n in ghe_notes)
