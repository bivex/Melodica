# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators import GeneratorParams
from melodica.generators.sax_section import SaxophoneSectionGenerator
from melodica.generators.wind_brass_solo import FlugelhornGenerator, EnglishHornGenerator, BassClarinetGenerator
from melodica.generators.chromatic_percussion import VibraphoneGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_sax_section_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Block voicing
    gen_block = SaxophoneSectionGenerator(voicing_style="block", baritone_doubles_lead=True)
    notes_block = gen_block.render(chords, C_MAJOR, 4.0)
    # A 5-sax section should generate notes count as a multiple of 5
    assert len(notes_block) > 0 and len(notes_block) % 5 == 0

    # 2. Drop-2 voicing
    gen_drop2 = SaxophoneSectionGenerator(voicing_style="drop_2", baritone_doubles_lead=False)
    notes_drop2 = gen_drop2.render(chords, C_MAJOR, 4.0)
    assert len(notes_drop2) > 0 and len(notes_drop2) % 5 == 0


def test_solo_jazz_winds():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Flugelhorn
    gen_flugel = FlugelhornGenerator(breath_vibrato=True)
    notes_flugel = gen_flugel.render(chords, C_MAJOR, 4.0)
    assert len(notes_flugel) >= 1
    assert any(n.expression is not None and 11 in n.expression for n in notes_flugel)

    # English Horn
    gen_eh = EnglishHornGenerator(vibrato=True)
    notes_eh = gen_eh.render(chords, C_MAJOR, 4.0)
    assert len(notes_eh) >= 1
    assert any(n.expression is not None and 1 in n.expression for n in notes_eh)

    # Bass Clarinet
    gen_bc = BassClarinetGenerator()
    notes_bc = gen_bc.render(chords, C_MAJOR, 4.0)
    assert len(notes_bc) >= 1
    assert all(38 <= n.pitch <= 79 for n in notes_bc)


def test_vibraphone_upgrades():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Check sustain pedal injection
    gen = VibraphoneGenerator(pattern="warm_chords", pedal=True)
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 1
    assert any(n.expression is not None and 64 in n.expression for n in notes)
    pedal_events = [n.expression[64] for n in notes if n.expression and 64 in n.expression][0]
    assert pedal_events == [(0.0, 0), (0.04, 127)]
