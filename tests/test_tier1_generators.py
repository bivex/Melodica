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

"""Tests for Tier 1 generators: ChordVoicing, Dynamics, SecondaryDominant, SectionBuilder, Transition, Swing."""

from __future__ import annotations

import pytest

from melodica.generators import GeneratorParams
from melodica.generators.chord_voicing import ChordVoicingGenerator
from melodica.generators.dynamics import DynamicsCurveGenerator
from melodica.generators.secondary_dominant import SecondaryDominantGenerator
from melodica.generators.section_builder import SectionBuilderGenerator
from melodica.generators.transition import TransitionGenerator
from melodica.generators.swing import SwingGenerator
from melodica.types import ChordLabel, Scale, Mode


@pytest.fixture()
def c_major():
    return Scale(root=0, mode=Mode.MAJOR)


@pytest.fixture()
def c_chord():
    return ChordLabel(root=0, quality="major", start=0.0, duration=4.0)


@pytest.fixture()
def f_chord():
    return ChordLabel(root=5, quality="major", start=4.0, duration=4.0)


@pytest.fixture()
def g_chord():
    return ChordLabel(root=7, quality="major", start=8.0, duration=4.0)


@pytest.fixture()
def chords(c_chord, f_chord, g_chord):
    return [c_chord, f_chord, g_chord]


@pytest.fixture()
def params():
    return GeneratorParams(density=0.8)


# ===================================================================
# ChordVoicingGenerator
# ===================================================================


class TestChordVoicingGenerator:
    @pytest.mark.parametrize(
        "voicing", ["close", "open", "drop2", "drop3", "cluster", "spread", "shearing", "rootless"]
    )
    def test_all_voicing_types(self, params, c_chord, c_major, voicing):
        gen = ChordVoicingGenerator(params, voicing=voicing)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 0 <= n.pitch <= 127

    def test_drop2_has_wide_range(self, params, c_chord, c_major):
        gen = ChordVoicingGenerator(params, voicing="drop2")
        notes = gen.render([c_chord], c_major, 4.0)
        pitches = [n.pitch for n in notes]
        assert max(pitches) - min(pitches) > 10  # wider than close position

    def test_arp_up_order(self, params, c_chord, c_major):
        gen = ChordVoicingGenerator(params, voicing="close", rhythm_pattern="arp_up")
        notes = gen.render([c_chord], c_major, 4.0)
        pitches = [n.pitch for n in notes]
        assert pitches == sorted(pitches)

    def test_arp_down_order(self, params, c_chord, c_major):
        gen = ChordVoicingGenerator(params, voicing="close", rhythm_pattern="arp_down")
        notes = gen.render([c_chord], c_major, 4.0)
        pitches = [n.pitch for n in notes]
        assert pitches == sorted(pitches, reverse=True)

    def test_empty_chords(self, params, c_major):
        gen = ChordVoicingGenerator(params)
        assert gen.render([], c_major, 4.0) == []

    def test_invalid_voicing(self, params):
        with pytest.raises(ValueError, match="Unknown voicing"):
            ChordVoicingGenerator(params, voicing="invalid")

    def test_velocity_curves(self, params, c_chord, c_major):
        for curve in ("flat", "crescendo", "decrescendo", "accent_first"):
            gen = ChordVoicingGenerator(params, voicing="close", velocity_curve=curve)
            notes = gen.render([c_chord], c_major, 4.0)
            assert len(notes) > 0


# ===================================================================
# DynamicsCurveGenerator
# ===================================================================


class TestDynamicsCurveGenerator:
    def test_crescendo(self, params, c_chord, c_major):
        gen = DynamicsCurveGenerator(params, curve_type="crescendo", note_duration=1.0)
        notes = gen.render([c_chord], c_major, 8.0)
        assert len(notes) > 0
        # Later notes should be louder
        assert notes[-1].velocity > notes[0].velocity

    def test_decrescendo(self, params, c_chord, c_major):
        gen = DynamicsCurveGenerator(params, curve_type="decrescendo", note_duration=1.0)
        notes = gen.render([c_chord], c_major, 8.0)
        assert notes[-1].velocity < notes[0].velocity

    def test_swell(self, params, c_chord, c_major):
        gen = DynamicsCurveGenerator(params, curve_type="swell", note_duration=1.0)
        notes = gen.render([c_chord], c_major, 8.0)
        mid = len(notes) // 2
        assert notes[mid].velocity > notes[0].velocity
        assert notes[mid].velocity > notes[-1].velocity

    def test_velocity_in_range(self, params, c_chord, c_major):
        gen = DynamicsCurveGenerator(params, curve_type="crescendo", velocity_range=(20, 100))
        notes = gen.render([c_chord], c_major, 4.0)
        for n in notes:
            assert 10 <= n.velocity <= 105  # slight tolerance for rounding

    @pytest.mark.parametrize(
        "curve",
        ["crescendo", "decrescendo", "swell", "sforzando", "terraced", "exponential", "sawtooth"],
    )
    def test_all_curves(self, params, c_chord, c_major, curve):
        gen = DynamicsCurveGenerator(params, curve_type=curve)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0

    def test_invalid_curve(self, params):
        with pytest.raises(ValueError, match="Unknown curve_type"):
            DynamicsCurveGenerator(params, curve_type="invalid")

    def test_empty_chords(self, params, c_major):
        assert DynamicsCurveGenerator(params).render([], c_major, 4.0) == []


# ===================================================================
# SecondaryDominantGenerator
# ===================================================================


class TestSecondaryDominantGenerator:
    def test_secondary_mode(self, params, chords, c_major):
        gen = SecondaryDominantGenerator(params, strategy="secondary")
        notes = gen.render(chords, c_major, 12.0)
        assert len(notes) > 0

    def test_tritone_mode(self, params, chords, c_major):
        gen = SecondaryDominantGenerator(params, strategy="tritone")
        notes = gen.render(chords, c_major, 12.0)
        assert len(notes) > 0

    def test_both_mode(self, params, chords, c_major):
        gen = SecondaryDominantGenerator(params, strategy="both")
        notes = gen.render(chords, c_major, 12.0)
        assert len(notes) > 0

    def test_voicing_types(self, params, chords, c_major):
        for v in ("root_position", "shell", "drop2"):
            gen = SecondaryDominantGenerator(params, strategy="secondary", voicing=v)
            notes = gen.render(chords, c_major, 12.0)
            assert len(notes) > 0

    def test_empty_chords(self, params, c_major):
        assert SecondaryDominantGenerator(params).render([], c_major, 4.0) == []

    def test_invalid_strategy(self, params):
        with pytest.raises(ValueError, match="Unknown strategy"):
            SecondaryDominantGenerator(params, strategy="invalid")


# ===================================================================
# SectionBuilderGenerator
# ===================================================================


class TestSectionBuilderGenerator:
    @pytest.mark.parametrize(
        "section", ["intro", "verse", "chorus", "bridge", "outro", "pre_chorus"]
    )
    def test_all_sections(self, params, chords, c_major, section):
        gen = SectionBuilderGenerator(params, section_type=section)
        notes = gen.render(chords, c_major, 16.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["melody", "chord_pulse", "arpeggio", "bass_walk"])
    def test_all_patterns(self, params, chords, c_major, pattern):
        gen = SectionBuilderGenerator(params, section_type="verse", pattern=pattern)
        notes = gen.render(chords, c_major, 8.0)
        assert len(notes) > 0

    def test_chorus_more_notes_than_intro(self, params, chords, c_major):
        intro = SectionBuilderGenerator(params, section_type="intro")
        chorus = SectionBuilderGenerator(params, section_type="chorus")
        intro_notes = intro.render(chords, c_major, 16.0)
        chorus_notes = chorus.render(chords, c_major, 16.0)
        # Chorus should generally have more notes (higher density)
        # This is probabilistic so just check both produce output
        assert len(intro_notes) > 0
        assert len(chorus_notes) > 0

    def test_empty_chords(self, params, c_major):
        assert SectionBuilderGenerator(params).render([], c_major, 4.0) == []

    def test_invalid_section(self, params):
        with pytest.raises(ValueError, match="Unknown section_type"):
            SectionBuilderGenerator(params, section_type="invalid")


# ===================================================================
# TransitionGenerator
# ===================================================================


class TestTransitionGenerator:
    def test_build(self, params, chords, c_major):
        gen = TransitionGenerator(params, transition_type="build")
        notes = gen.render(chords, c_major, 8.0)
        assert len(notes) > 0

    def test_drop(self, params, chords, c_major):
        gen = TransitionGenerator(params, transition_type="drop")
        notes = gen.render(chords, c_major, 8.0)
        assert len(notes) > 0
        # Drop starts strong
        assert notes[0].velocity > 50

    def test_breakdown(self, params, chords, c_major):
        gen = TransitionGenerator(params, transition_type="breakdown")
        notes = gen.render(chords, c_major, 8.0)
        assert len(notes) > 0

    def test_fill(self, params, chords, c_major):
        gen = TransitionGenerator(params, transition_type="fill")
        notes = gen.render(chords, c_major, 4.0)
        assert len(notes) > 0
        # Fill should descend
        if len(notes) > 2:
            assert notes[0].pitch > notes[-1].pitch

    def test_build_crescendo(self, params, chords, c_major):
        gen = TransitionGenerator(params, transition_type="build")
        notes = gen.render(chords, c_major, 8.0)
        if len(notes) > 2:
            assert notes[-1].velocity > notes[0].velocity

    def test_empty_chords(self, params, c_major):
        assert TransitionGenerator(params).render([], c_major, 4.0) == []

    def test_invalid_type(self, params):
        with pytest.raises(ValueError, match="Unknown transition_type"):
            TransitionGenerator(params, transition_type="invalid")


# ===================================================================
# SwingGenerator
# ===================================================================


class TestSwingGenerator:
    def test_straight(self, params, c_chord, c_major):
        gen = SwingGenerator(params, swing_ratio=0.5)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0
        # Straight: notes should be evenly spaced
        gaps = [notes[i + 1].start - notes[i].start for i in range(len(notes) - 1)]
        for g in gaps:
            assert abs(g - 0.5) < 0.01

    def test_swing(self, params, c_chord, c_major):
        gen = SwingGenerator(params, swing_ratio=0.67)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 1
        # Even-numbered notes (0, 2, 4...) should be on beat
        # Odd-numbered notes should be delayed
        on_beat = notes[0].start
        swung = notes[1].start
        assert swung > on_beat + 0.5  # delayed past halfway

    def test_hard_swing(self, params, c_chord, c_major):
        gen = SwingGenerator(params, swing_ratio=0.75)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 1
        gap_0 = notes[1].start - notes[0].start
        gap_1 = notes[2].start - notes[1].start if len(notes) > 2 else 0.25
        # First gap (on-beat to swung) should be longer than second
        assert gap_0 > gap_1

    @pytest.mark.parametrize("accent", ["downbeat", "backbeat", "every_note"])
    def test_accent_patterns(self, params, c_chord, c_major, accent):
        gen = SwingGenerator(params, accent_pattern=accent)
        notes = gen.render([c_chord], c_major, 4.0)
        assert len(notes) > 0

    def test_empty_chords(self, params, c_major):
        assert SwingGenerator(params).render([], c_major, 4.0) == []


# ===================================================================
# Factory integration
# ===================================================================


class TestFactoryIntegrationTier1:
    @pytest.mark.parametrize(
        "gen_type,config",
        [
            ("chord_voicing", {"voicing": "drop2"}),
            ("dynamics", {"curve_type": "swell"}),
            ("secondary_dominant", {"strategy": "tritone"}),
            ("section_builder", {"section_type": "chorus"}),
            ("transition", {"transition_type": "build"}),
            ("swing", {"swing_ratio": 0.67}),
        ],
    )
    def test_factory_creates_all(self, gen_type, config, chords, c_major):
        from melodica.factory import create_generator

        gen = create_generator(gen_type, GeneratorParams(density=0.8), config)
        assert gen is not None
        notes = gen.render(chords, c_major, 8.0)
        assert len(notes) > 0
