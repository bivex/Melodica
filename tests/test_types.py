# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""tests/test_types.py — Unit tests for domain model invariants."""

import pytest
from melodica.types import (
    ChordLabel,
    HarmonizationRequest,
    IdeaTrack,
    Mode,
    Note,
    NoteInfo,
    PhraseInstance,
    Quality,
    RomanNumeral,
    Scale,
    StaticPhrase,
    parse_progression,
    parse_progression_structured,
)


# ---------------------------------------------------------------------------
# Note
# ---------------------------------------------------------------------------

class TestNote:
    def test_valid(self):
        n = Note(pitch=60, start=0.0, duration=1.0)
        assert n.pitch_class == 0
        assert n.end == 1.0

    def test_pitch_out_of_range(self):
        with pytest.raises(ValueError):
            Note(pitch=128, start=0.0, duration=1.0)

    def test_negative_duration(self):
        with pytest.raises(ValueError):
            Note(pitch=60, start=0.0, duration=0.0)


# ---------------------------------------------------------------------------
# Scale
# ---------------------------------------------------------------------------

class TestScale:
    def test_c_major_degrees(self):
        s = Scale(root=0, mode=Mode.MAJOR)
        assert s.degrees() == [0, 2, 4, 5, 7, 9, 11]

    def test_a_natural_minor_degrees(self):
        s = Scale(root=9, mode=Mode.NATURAL_MINOR)
        degs = s.degrees()
        assert 9 in degs  # A
        assert 11 in degs  # B

    def test_degree_of(self):
        s = Scale(root=0, mode=Mode.MAJOR)
        assert s.degree_of(0) == 1   # C = I
        assert s.degree_of(7) == 5   # G = V
        assert s.degree_of(1) is None  # C# not in C major

    def test_diatonic_chord_i(self):
        s = Scale(root=0, mode=Mode.MAJOR)
        chord = s.diatonic_chord(1)
        assert chord.root == 0
        assert chord.quality == Quality.MAJOR

    def test_diatonic_chord_v(self):
        s = Scale(root=0, mode=Mode.MAJOR)
        chord = s.diatonic_chord(5)
        assert chord.root == 7  # G
        assert chord.quality == Quality.MAJOR

    def test_diatonic_chord_vii_diminished(self):
        s = Scale(root=0, mode=Mode.MAJOR)
        chord = s.diatonic_chord(7)
        assert chord.quality == Quality.DIMINISHED

    def test_scale_min_interval_validation(self):
        from melodica.theory.exotic_database import EXOTIC_SCALE_DATABASE
        EXOTIC_SCALE_DATABASE["microtonal_clash"] = [0.0, 0.3, 1.0, 2.0]
        try:
            with pytest.raises(AssertionError):
                Scale(root=0, mode="microtonal_clash")
        finally:
            EXOTIC_SCALE_DATABASE.pop("microtonal_clash", None)

    def test_scale_partch_bypass_validation(self):
        s = Scale(root=0, mode="partch_43_tone")
        assert len(s.intervals()) == 41


# ---------------------------------------------------------------------------
# ChordLabel
# ---------------------------------------------------------------------------

class TestChordLabel:
    def test_pitch_classes_major(self):
        c = ChordLabel(root=0, quality=Quality.MAJOR)
        assert set(c.pitch_classes()) == {0, 4, 7}

    def test_pitch_classes_minor7(self):
        c = ChordLabel(root=0, quality=Quality.MINOR7)
        assert set(c.pitch_classes()) == {0, 3, 7, 10}

    def test_end_property(self):
        c = ChordLabel(root=0, quality=Quality.MAJOR, start=2.0, duration=2.0)
        assert c.end == 4.0

    def test_invalid_root(self):
        with pytest.raises(ValueError):
            ChordLabel(root=12, quality=Quality.MAJOR)


# ---------------------------------------------------------------------------
# PhraseInstance invariant
# ---------------------------------------------------------------------------

class TestPhraseInstance:
    def test_static_only(self):
        pi = PhraseInstance(static=StaticPhrase(notes=[]))
        assert not pi.is_parametric()

    def test_neither_raises(self):
        with pytest.raises(ValueError):
            PhraseInstance(generator=None, static=None)

    def test_both_raises(self):
        from melodica.generators.melody import MelodyGenerator
        gen = MelodyGenerator()
        with pytest.raises(ValueError):
            PhraseInstance(generator=gen, static=StaticPhrase(notes=[]))


# ---------------------------------------------------------------------------
# HarmonizationRequest
# ---------------------------------------------------------------------------

class TestHarmonizationRequest:
    def test_empty_melody_raises(self):
        with pytest.raises(ValueError):
            HarmonizationRequest(
                melody=[],
                key=Scale(root=0, mode=Mode.MAJOR),
            )

    def test_invalid_engine_raises(self):
        with pytest.raises(ValueError):
            HarmonizationRequest(
                melody=[Note(60, 0, 1)],
                key=Scale(root=0, mode=Mode.MAJOR),
                engine=5,
            )


class TestRomanNumeral:
    def test_basic_major(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        romans = [
            RomanNumeral("I", duration=4.0),
            RomanNumeral("V", duration=4.0),
        ]
        chords = parse_progression_structured(romans, key)
        assert len(chords) == 2
        assert chords[0].root == 0  # C
        assert chords[1].root == 7  # G

    def test_quality_suffix(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        romans = [
            RomanNumeral("ii", quality_suffix="m", duration=2.0),
        ]
        chords = parse_progression_structured(romans, key)
        assert len(chords) == 1
        assert chords[0].root == 2  # D

    def test_backward_compat_string_parser(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        structured = parse_progression_structured(
            [RomanNumeral("I"), RomanNumeral("IV"), RomanNumeral("V")],
            key,
        )
        string_parsed = parse_progression("I IV V", key)
        assert [c.root for c in structured] == [c.root for c in string_parsed]

    def test_roman_str_property(self):
        rn = RomanNumeral("iv", quality_suffix="m", duration=4.0, slash_bass="V")
        assert rn.roman_str == "ivm/V"

    def test_staggered_start_times(self):
        key = Scale(root=0, mode=Mode.MAJOR)
        romans = [
            RomanNumeral("I", duration=2.0),
            RomanNumeral("IV", duration=3.0),
            RomanNumeral("V", duration=1.0),
        ]
        chords = parse_progression_structured(romans, key)
        assert chords[0].start == 0.0
        assert chords[1].start == 2.0
        assert chords[2].start == 5.0


class TestModeDatabaseValidation:
    def test_all_modes_start_at_zero(self):
        from melodica.theory.modes import MODE_DATABASE
        for mode, defn in MODE_DATABASE.items():
            assert defn.intervals[0] == 0, f"{mode.name} doesn't start at 0"

    def test_intervals_sorted_ascending(self):
        from melodica.theory.modes import MODE_DATABASE
        for mode, defn in MODE_DATABASE.items():
            assert defn.intervals == sorted(defn.intervals), f"{mode.name} intervals not sorted"

    def test_no_unintentional_duplicates(self):
        from melodica.theory.modes import _validate_mode_database
        warnings = _validate_mode_database()
        assert warnings == [], "Unintentional duplicates found:\n" + "\n".join(warnings)
