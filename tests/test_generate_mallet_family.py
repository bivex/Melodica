# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import math
import pytest
from melodica.types import ChordLabel, Scale, Mode
from melodica.theory.chords import Quality
from melodica.generate.family import MalletFamily
from melodica.generate.profile import get_profile

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_mallet_family_direct_instantiation():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Using profile ID string
    gen = MalletFamily("marimba", pattern="woody_arpeggio", mallets=4)
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) == 4
    assert all(math.isclose(n.duration, 0.22) for n in notes)

    # Using profile object
    prof = get_profile("vibraphone")
    gen_vib = MalletFamily(prof, pattern="warm_chords")
    notes_vib = gen_vib.render(chords, C_MAJOR, 4.0)
    assert len(notes_vib) >= 1
    assert 11 in notes_vib[0].expression
    assert 64 in notes_vib[0].expression


def test_mallet_family_empty_and_density():
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=2.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=2.0, duration=2.0),
    ]
    gen = MalletFamily("glockenspiel", note_density=0.5)
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Reduced by density
    assert len(notes) == 1

    # Empty chords
    assert gen.render([], C_MAJOR, 4.0) == []
