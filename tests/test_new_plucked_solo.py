# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.plucked_solo import PianoSoloGenerator, AcousticGuitarGenerator, EthnicPluckedGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_piano_solo_generator():
    gen = PianoSoloGenerator(instrument="grand_piano", pedal=True)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 1


def test_acoustic_guitar_generator():
    gen = AcousticGuitarGenerator(style="fingerpicking", acoustic_type="nylon")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Fingerpicking produces multiple arpeggiated notes
    assert len(notes) >= 2


def test_ethnic_plucked_generator():
    gen = EthnicPluckedGenerator(instrument="sitar")
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 1
    # Sitar should generate pitch expression bend mapping
    assert notes[0].expression is not None
