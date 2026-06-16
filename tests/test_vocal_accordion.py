# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.vocal_accordion import VocalScatGenerator, GregorianChantGenerator, MusetteAccordionGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_vocal_scat_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = VocalScatGenerator(scat_complexity=0.7)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Pitch bend scoop is randomly generated (tested statistically or via existence check)


def test_gregorian_chant_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = GregorianChantGenerator(reverb_presence=0.8)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check CC 91 (reverb send) and CC 11 (bellows swell)
    assert any(n.expression is not None and 91 in n.expression for n in notes)
    assert any(n.expression is not None and 11 in n.expression for n in notes)


def test_musette_accordion_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = MusetteAccordionGenerator(detune_cents=12.0)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    # Trigger 2 detuned notes per voiced pitch class
    assert len(notes) >= 2
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)
