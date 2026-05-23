# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
import math
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.chromatic_percussion import (
    CelestaGenerator,
    GlockenspielGenerator,
    MusicBoxGenerator,
    VibraphoneGenerator,
    MarimbaGenerator,
    XylophoneGenerator,
    DulcimerGenerator,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_celesta_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Arpeggio pattern
    gen_arp = CelestaGenerator(pattern="dreamy_arpeggio", pedal=True)
    notes_arp = gen_arp.render(chords, C_MAJOR, 4.0)
    assert len(notes_arp) >= 2
    # Pedal increases duration
    assert notes_arp[0].duration > 1.0

    # Sparkling chords
    gen_chords = CelestaGenerator(pattern="sparkling_chords", pedal=False)
    notes_chords = gen_chords.render(chords, C_MAJOR, 4.0)
    assert len(notes_chords) >= 1
    # Check that they start at 0.0
    assert all(n.start == 0.0 for n in notes_chords)


def test_glockenspiel_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Accent pattern
    gen_accent = GlockenspielGenerator(pattern="melodic_accent")
    notes_accent = gen_accent.render(chords, C_MAJOR, 4.0)
    assert len(notes_accent) == 1
    assert notes_accent[0].pitch >= 72

    # Sparkling run
    gen_run = GlockenspielGenerator(pattern="sparkling_run")
    notes_run = gen_run.render(chords, C_MAJOR, 4.0)
    assert len(notes_run) == 4


def test_music_box_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Ostinato pattern
    gen_ost = MusicBoxGenerator(pattern="clockwork_ostinato")
    notes_ost = gen_ost.render(chords, C_MAJOR, 4.0)
    # Eighth notes over 4 beats = 8 notes
    assert len(notes_ost) == 8
    # Rigid spacing
    for i in range(1, len(notes_ost)):
        assert math.isclose(notes_ost[i].start - notes_ost[i-1].start, 0.5)


def test_vibraphone_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Warm chords (includes motor dynamic LFO simulation on CC 11)
    gen_vib = VibraphoneGenerator(pattern="warm_chords", motor_speed_hz=5.0)
    notes_vib = gen_vib.render(chords, C_MAJOR, 4.0)
    assert len(notes_vib) >= 1
    assert notes_vib[0].expression is not None
    assert 11 in notes_vib[0].expression
    # Check that expression contains dynamic LFO list of tuples
    lfo_list = notes_vib[0].expression[11]
    assert len(lfo_list) > 5
    assert all(len(tup) == 2 for tup in lfo_list)


def test_marimba_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Woody arpeggio
    gen_arp = MarimbaGenerator(pattern="woody_arpeggio", mallets=4)
    notes_arp = gen_arp.render(chords, C_MAJOR, 4.0)
    assert len(notes_arp) == 4
    assert all(math.isclose(n.duration, 0.22) for n in notes_arp)

    # Rolling tremolo
    gen_roll = MarimbaGenerator(pattern="rolling_tremolo")
    notes_roll = gen_roll.render(chords, C_MAJOR, 4.0)
    # 0.125 steps over 4 beats = 32 notes
    assert len(notes_roll) == 32


def test_xylophone_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Dry staccato run
    gen_run = XylophoneGenerator(pattern="dry_staccato_run")
    notes_run = gen_run.render(chords, C_MAJOR, 4.0)
    # 0.25 steps over 4 beats = 16 notes
    assert len(notes_run) == 16
    assert all(math.isclose(n.duration, 0.12) for n in notes_run)


def test_dulcimer_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Hammered roll
    gen_roll = DulcimerGenerator(pattern="hammered_roll")
    notes_roll = gen_roll.render(chords, C_MAJOR, 4.0)
    assert len(notes_roll) == 32
    assert all(math.isclose(n.duration, 0.25) for n in notes_roll)
