# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.folk_ensemble import BandoneonGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_bandoneon_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = BandoneonGenerator(bellows_accents=0.7)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check bellows shake Expression CC 11 is present
    assert any(n.expression is not None and 11 in n.expression for n in notes)
