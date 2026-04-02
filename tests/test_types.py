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
    Scale,
    StaticPhrase,
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
