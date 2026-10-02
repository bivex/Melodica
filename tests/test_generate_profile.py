# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.generate.profile import (
    parse_pitch,
    InstrumentProfile,
    load_profile,
    get_profile,
    list_profiles,
)


def test_parse_pitch():
    assert parse_pitch(60) == 60
    assert parse_pitch("60") == 60
    assert parse_pitch("C4") == 60
    assert parse_pitch("A4") == 69
    assert parse_pitch("F#3") == 54
    assert parse_pitch("Gb3") == 54
    assert parse_pitch("B-flat5") == 82
    assert parse_pitch("C-sharp4") == 61

    with pytest.raises(ValueError):
        parse_pitch("invalid_pitch_name")


def test_get_profile():
    celesta = get_profile("celesta")
    assert celesta.id == "celesta"
    assert celesta.family == "mallet"
    assert celesta.gm_program == 8
    assert celesta.range_low == 60
    assert celesta.range_high == 108
    assert celesta.sustain_pedal is True
    assert celesta.pitch_in_range(72) is True
    assert celesta.pitch_in_range(40) is False


def test_list_profiles():
    profiles = list_profiles()
    assert "celesta" in profiles
    assert "glockenspiel" in profiles
    assert "vibraphone" in profiles
    assert "marimba" in profiles
    assert "xylophone" in profiles
    assert "music_box" in profiles
    assert "dulcimer" in profiles


def test_load_profile_dict():
    data = {
        "id": "custom_bell",
        "family": "mallet",
        "gm_program": 14,
        "range": {"low": "C4", "high": "C7"},
        "max_polyphony": 2,
    }
    prof = load_profile(data)
    assert prof.id == "custom_bell"
    assert prof.gm_program == 14
    assert prof.range_low == 60
    assert prof.range_high == 96
    assert prof.max_polyphony == 2
