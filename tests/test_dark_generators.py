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

"""Tests for downtempo / dark texture generators: DarkPad, Tension, DarkBass."""

from __future__ import annotations

import pytest

from melodica.generators import GeneratorParams
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.types import ChordLabel, Scale, Mode


@pytest.fixture()
def a_minor():
    return Scale(root=9, mode=Mode.NATURAL_MINOR)


@pytest.fixture()
def am_chord():
    return ChordLabel(root=9, quality="minor", start=0.0, duration=8.0)


@pytest.fixture()
def dm_chord():
    return ChordLabel(root=2, quality="minor", start=8.0, duration=8.0)


@pytest.fixture()
def dark_chords(am_chord, dm_chord):
    return [am_chord, dm_chord]


@pytest.fixture()
def params():
    return GeneratorParams(density=0.5)


# ===================================================================
# DarkPadGenerator
# ===================================================================


class TestDarkPadGenerator:
    @pytest.mark.parametrize(
        "mode", ["minor_pad", "dim_cluster", "tritone_drone", "chromatic_pad", "phrygian_pad"]
    )
    def test_all_modes(self, params, dark_chords, a_minor, mode):
        gen = DarkPadGenerator(params, mode=mode)
        notes = gen.render(dark_chords, a_minor, 16.0)
        assert len(notes) > 0
        for n in notes:
            assert 0 <= n.pitch <= 127
            assert 1 <= n.velocity <= 127

    def test_low_register(self, params, dark_chords, a_minor):
        gen = DarkPadGenerator(params, mode="minor_pad", register="low")
        notes = gen.render(dark_chords, a_minor, 16.0)
        avg_pitch = sum(n.pitch for n in notes) / len(notes)
        assert avg_pitch < 60  # low register

    def test_low_velocity(self, params, dark_chords, a_minor):
        gen = DarkPadGenerator(params, velocity_level=0.2)
        notes = gen.render(dark_chords, a_minor, 8.0)
        for n in notes:
            assert n.velocity < 40

    def test_overlap(self, params, am_chord, a_minor):
        gen = DarkPadGenerator(params, chord_dur=4.0, overlap=0.5)
        notes = gen.render([am_chord], a_minor, 4.0)
        assert len(notes) > 0

    def test_empty_chords(self, params, a_minor):
        assert DarkPadGenerator(params).render([], a_minor, 4.0) == []

    def test_invalid_mode(self, params):
        with pytest.raises(ValueError, match="Unknown dark pad mode"):
            DarkPadGenerator(params, mode="invalid")


# ===================================================================
# TensionGenerator
# ===================================================================


class TestTensionGenerator:
    @pytest.mark.parametrize(
        "mode",
        [
            "semitone_cluster",
            "tritone_pulse",
            "major7_tension",
            "chromatic_rise",
            "chromatic_fall",
            "atonal_scatter",
        ],
    )
    def test_all_modes(self, params, dark_chords, a_minor, mode):
        gen = TensionGenerator(params, mode=mode)
        notes = gen.render(dark_chords, a_minor, 8.0)
        assert len(notes) > 0

    def test_chromatic_rise_ascends(self, params, a_minor):
        gen = TensionGenerator(params, mode="chromatic_rise", note_duration=1.0)
        notes = gen.render([], a_minor, 8.0)
        if len(notes) > 2:
            assert notes[-1].pitch > notes[0].pitch

    def test_chromatic_fall_descends(self, params, a_minor):
        gen = TensionGenerator(params, mode="chromatic_fall", note_duration=1.0)
        notes = gen.render([], a_minor, 8.0)
        if len(notes) > 2:
            assert notes[-1].pitch < notes[0].pitch

    def test_tritone_pulse_pairs(self, params, a_minor):
        gen = TensionGenerator(params, mode="tritone_pulse", note_duration=2.0, density=1.0)
        notes = gen.render([], a_minor, 4.0)
        assert len(notes) >= 2
        # Notes should be in pairs with tritone interval
        gap = abs(notes[1].pitch - notes[0].pitch)
        assert gap == 6  # tritone

    def test_semitone_cluster_has_close_notes(self, params, a_minor):
        gen = TensionGenerator(params, mode="semitone_cluster")
        notes = gen.render([], a_minor, 4.0)
        if len(notes) >= 2:
            gap = abs(notes[1].pitch - notes[0].pitch)
            assert gap <= 2  # semitone or wholetone cluster

    def test_low_velocity(self, params, a_minor):
        gen = TensionGenerator(params, velocity_level=0.3)
        notes = gen.render([], a_minor, 4.0)
        for n in notes:
            assert n.velocity < 50

    def test_empty_with_no_density(self, a_minor):
        gen = TensionGenerator(GeneratorParams(density=0.01), density=0.01)
        # Very low density, might be empty but shouldn't crash
        notes = gen.render([], a_minor, 2.0)
        assert isinstance(notes, list)

    def test_invalid_mode(self, params):
        with pytest.raises(ValueError, match="Unknown tension mode"):
            TensionGenerator(params, mode="invalid")


# ===================================================================
# DarkBassGenerator
# ===================================================================


class TestDarkBassGenerator:
    @pytest.mark.parametrize("mode", ["doom", "trip_hop", "industrial", "dub", "dark_pulse"])
    def test_all_modes(self, params, dark_chords, a_minor, mode):
        gen = DarkBassGenerator(params, mode=mode)
        notes = gen.render(dark_chords, a_minor, 16.0)
        assert len(notes) > 0
        for n in notes:
            assert 0 <= n.pitch <= 127

    def test_low_register(self, params, dark_chords, a_minor):
        gen = DarkBassGenerator(params, octave=2)
        notes = gen.render(dark_chords, a_minor, 8.0)
        for n in notes:
            assert n.pitch < 60  # should be in bass register

    def test_doom_slow(self, params, dark_chords, a_minor):
        gen = DarkBassGenerator(params, mode="doom", note_duration=8.0)
        notes = gen.render(dark_chords, a_minor, 16.0)
        assert len(notes) <= 4  # very few notes

    def test_industrial_fast(self, params, dark_chords, a_minor):
        gen = DarkBassGenerator(params, mode="industrial", note_duration=1.0)
        notes = gen.render(dark_chords, a_minor, 8.0)
        assert len(notes) >= 4  # more notes than doom

    def test_trip_hop_ghost_notes(self, params, am_chord, a_minor):
        gen = DarkBassGenerator(params, mode="trip_hop", note_duration=2.0)
        notes = gen.render([am_chord], a_minor, 8.0)
        # Should have velocity variation (ghost notes)
        vels = [n.velocity for n in notes]
        assert max(vels) != min(vels)  # not all same velocity

    @pytest.mark.parametrize("movement", ["root_only", "root_fifth", "chromatic", "tritone_walk"])
    def test_all_movements(self, params, dark_chords, a_minor, movement):
        gen = DarkBassGenerator(params, movement=movement)
        notes = gen.render(dark_chords, a_minor, 8.0)
        assert len(notes) > 0

    def test_tritone_walk_has_tritone(self, params, am_chord, a_minor):
        gen = DarkBassGenerator(params, movement="tritone_walk", note_duration=2.0)
        notes = gen.render([am_chord], a_minor, 8.0)
        if len(notes) >= 2:
            gap = abs(notes[1].pitch - notes[0].pitch) % 12
            assert gap == 6  # tritone

    def test_empty_chords(self, params, a_minor):
        assert DarkBassGenerator(params).render([], a_minor, 4.0) == []

    def test_invalid_mode(self, params):
        with pytest.raises(ValueError, match="Unknown dark bass mode"):
            DarkBassGenerator(params, mode="invalid")


# ===================================================================
# Factory integration
# ===================================================================


class TestDarkFactoryIntegration:
    @pytest.mark.parametrize(
        "gen_type,config",
        [
            ("dark_pad", {"mode": "minor_pad"}),
            ("tension", {"mode": "semitone_cluster"}),
            ("dark_bass", {"mode": "doom"}),
        ],
    )
    def test_factory_creates_dark(self, gen_type, config, dark_chords, a_minor):
        from melodica.factory import create_generator

        gen = create_generator(gen_type, GeneratorParams(density=0.5), config)
        assert gen is not None
        notes = gen.render(dark_chords, a_minor, 8.0)
        assert len(notes) > 0
