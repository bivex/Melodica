# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_generate_plucked_and_wind_family.py — Unit tests for PluckedFamily and WindBrassFamily.
"""

from __future__ import annotations

import pytest

from melodica.generate.family import PluckedFamily, WindBrassFamily
from melodica.generators.plucked_solo import (
    PianoSoloGenerator,
    AcousticGuitarGenerator,
    EthnicPluckedGenerator,
    KalimbaGenerator,
)
from melodica.generators.wind_brass_solo import (
    MutedTrumpetGenerator,
    SynthBrassGenerator,
    WoodwindSoloGenerator,
    FlugelhornGenerator,
    EnglishHornGenerator,
    BassClarinetGenerator,
    EuphoniumGenerator,
    AltoFluteGenerator,
)
from melodica.types import ChordLabel, Quality, Scale, Mode


@pytest.fixture
def standard_chords():
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
    ]


@pytest.fixture
def key_c_major():
    return Scale(0, Mode.MAJOR)


def test_plucked_family_direct(standard_chords, key_c_major):
    # Direct instantiation with TOML profiles
    pf_piano = PluckedFamily("grand_piano")
    notes = pf_piano.render(standard_chords, key_c_major, 8.0)
    assert len(notes) >= 2
    for n in notes:
        assert 21 <= n.pitch <= 108

    pf_guitar = PluckedFamily("nylon_guitar", style="fingerpicking")
    notes_g = pf_guitar.render(standard_chords, key_c_major, 8.0)
    assert len(notes_g) >= 2

    pf_kalimba = PluckedFamily("kalimba")
    notes_k = pf_kalimba.render(standard_chords, key_c_major, 8.0)
    assert len(notes_k) >= 2


def test_plucked_solo_classes_backward_compatibility(standard_chords, key_c_major):
    p_gen = PianoSoloGenerator(instrument="bright_piano", pedal=True)
    notes = p_gen.render(standard_chords, key_c_major, 8.0)
    assert len(notes) >= 2

    g_gen = AcousticGuitarGenerator(style="strumming", acoustic_type="distortion")
    notes_g = g_gen.render(standard_chords, key_c_major, 8.0)
    assert len(notes_g) >= 2

    e_gen = EthnicPluckedGenerator(instrument="sitar")
    notes_e = e_gen.render(standard_chords, key_c_major, 8.0)
    assert len(notes_e) >= 2

    k_gen = KalimbaGenerator(pop_intensity=0.8)
    notes_k = k_gen.render(standard_chords, key_c_major, 8.0)
    assert len(notes_k) >= 2


def test_wind_brass_family_direct(standard_chords, key_c_major):
    wf_trumpet = WindBrassFamily("muted_trumpet", plunger_wah=True)
    notes = wf_trumpet.render(standard_chords, key_c_major, 8.0)
    assert len(notes) >= 2
    for n in notes:
        assert 58 <= n.pitch <= 84
        if n.expression:
            assert 74 in n.expression

    wf_synth = WindBrassFamily("synth_brass_1", harmony_count=3)
    notes_s = wf_synth.render(standard_chords, key_c_major, 8.0)
    assert len(notes_s) >= 4

    wf_wood = WindBrassFamily("pan_flute")
    notes_w = wf_wood.render(standard_chords, key_c_major, 8.0)
    assert len(notes_w) >= 2


def test_wind_brass_solo_classes_backward_compatibility(standard_chords, key_c_major):
    gens = [
        MutedTrumpetGenerator(),
        SynthBrassGenerator(brass_type="synth_brass_2"),
        WoodwindSoloGenerator(instrument="piccolo"),
        FlugelhornGenerator(),
        EnglishHornGenerator(),
        BassClarinetGenerator(),
        EuphoniumGenerator(),
        AltoFluteGenerator(),
    ]
    for gen in gens:
        notes = gen.render(standard_chords, key_c_major, 8.0)
        assert len(notes) >= 1
