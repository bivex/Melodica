# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.plucked_solo import PianoSoloGenerator, AcousticGuitarGenerator, EthnicPluckedGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_piano_solo_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Grand Piano (default)
    gen = PianoSoloGenerator(instrument="grand_piano", pedal=True)
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 1

    # 2. Bright Acoustic Piano
    gen_bright = PianoSoloGenerator(instrument="bright_piano", pedal=True)
    notes_bright = gen_bright.render(chords, C_MAJOR, 4.0)
    assert len(notes_bright) >= 1
    # Check that average velocity tends to be higher for bright piano
    assert any(n.velocity > 80 for n in notes_bright if n.pitch > 45)

    # 3. Electric Grand
    gen_egrand = PianoSoloGenerator(instrument="electric_grand", pedal=True)
    notes_egrand = gen_egrand.render(chords, C_MAJOR, 4.0)
    assert len(notes_egrand) >= 1
    # Electric grand should have chorus (93) and expression (11)
    assert any(n.expression is not None and 93 in n.expression for n in notes_egrand)

    # 4. Honky-tonk Piano
    gen_honky = PianoSoloGenerator(instrument="honky_tonk", pedal=True)
    notes_honky = gen_honky.render(chords, C_MAJOR, 4.0)
    # Honky-tonk produces double strike companion notes, so it should have more notes
    assert len(notes_honky) >= 2
    # Check chorus send 93
    assert any(n.expression is not None and 93 in n.expression for n in notes_honky)

    # 5. Electric Piano 2
    gen_ep2 = PianoSoloGenerator(instrument="electric_piano_2", pedal=True)
    notes_ep2 = gen_ep2.render(chords, C_MAJOR, 4.0)
    assert len(notes_ep2) >= 1
    # EP 2 has highly active chorus (93) and expression tremolo (11)
    assert any(n.expression is not None and 93 in n.expression and 11 in n.expression for n in notes_ep2)


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
