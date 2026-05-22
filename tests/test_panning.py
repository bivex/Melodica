# Copyright (c) 2026 Bivex — MIT License
# Tests for spatial panning system: genre profiles, spread, validation.

from __future__ import annotations

import pytest

from melodica.composer.album_pipeline import (
    PanValidator,
    _auto_spread_panning,
    _get_role_pan_map,
    _ROLE_PAN_PROFILES,
    _TrackProfile,
    Role,
    _get_pan_for_role,
)


# ---------------------------------------------------------------------------
# Layer 1: Genre profiles
# ---------------------------------------------------------------------------

class TestGenrePanProfiles:
    """Each genre must have a complete Role → pan_norm mapping."""

    @pytest.mark.parametrize("genre", ["techno", "rnb", "trap"])
    def test_all_roles_covered(self, genre: str):
        rp = _get_role_pan_map(genre)
        # Minimum required roles — PERC/FX/STRINGS/CHOIR are optional per genre
        assert Role.BASS in rp, f"BASS missing in {genre}"
        assert Role.LEAD in rp, f"LEAD missing in {genre}"
        assert Role.PAD  in rp, f"PAD  missing in {genre}"
        # Techno is the complete reference profile
        if genre == "techno":
            assert Role.PERC   in rp, "PERC missing in techno"
            assert Role.FX     in rp, "FX missing in techno"
            assert Role.STRINGS in rp, "STRINGS missing in techno"
            assert Role.CHOIR  in rp, "CHOIR missing in techno"

    def test_fallback_is_techno(self):
        assert _get_role_pan_map(None) == _get_role_pan_map("techno")
        assert _get_role_pan_map("unknown_genre") == _get_role_pan_map("techno")

    @pytest.mark.parametrize("genre,pad_range", [
        ("techno", (-0.30,  0.00)),   # default: -0.30
        ("rnb",    (-0.30, -0.10)),   # warm but wide
        ("trap",   (-0.45, -0.35)),   # very wide left
    ])
    def test_pad_position_per_genre(self, genre: str, pad_range):
        pan = _get_pan_for_role(Role.PAD, genre)
        assert pad_range[0] <= pan <= pad_range[1], \
            f"{genre}: PAD pan={pan:.2f} вне {pad_range}"

    @pytest.mark.parametrize("genre", ["techno", "rnb", "trap"])
    def test_bass_always_center_in_genre_profile(self, genre: str):
        assert _get_pan_for_role(Role.BASS, genre) == 0.0

    @pytest.mark.parametrize("genre", ["techno", "rnb", "trap"])
    def test_lead_always_center_in_genre_profile(self, genre: str):
        assert _get_pan_for_role(Role.LEAD, genre) == 0.0


# ---------------------------------------------------------------------------
# Layer 3: _auto_spread_panning
# ---------------------------------------------------------------------------

class TestAutoSpreadPanning:
    """Priority rules:
    1. BASS/PERC → centre, never moved.
    2. 2 PADs in same register → ±0.40 wide.
    3. FX → alternating outer edges ±0.60.
    4. LEAD/STRINGS/CHOIR → genre default pan.
    """

    @pytest.fixture
    def profiles(self):
        base = dict(
            bass=_TrackProfile(avg_pitch=44.0, pitch_range=12.0, density=0.2,
                               rms_velocity=90.0, role=Role.BASS),
            lead=_TrackProfile(avg_pitch=62.0, pitch_range=24.0, density=0.15,
                               rms_velocity=80.0, role=Role.LEAD),
            pad_a=_TrackProfile(avg_pitch=58.0, pitch_range=8.0,  density=0.04,
                                rms_velocity=55.0, role=Role.PAD),
            pad_b=_TrackProfile(avg_pitch=56.0, pitch_range=10.0, density=0.06,
                                rms_velocity=60.0, role=Role.PAD),
            fx_whoosh=_TrackProfile(avg_pitch=86.0, pitch_range=4.0, density=0.01,
                                    rms_velocity=50.0, role=Role.FX),
            strings=_TrackProfile(avg_pitch=55.0, pitch_range=30.0, density=0.08,
                                  rms_velocity=65.0, role=Role.STRINGS),
        )
        return base

    def _run(self, profiles, genre="techno"):
        role_map = _get_role_pan_map(genre)
        tracks = {n: [] for n in profiles}
        return _auto_spread_panning(tracks, profiles, role_map)

    def test_bass_always_center(self, profiles):
        result = self._run(profiles)
        assert result["bass"] == 0.0

    def test_lead_gets_default_pan(self, profiles):
        result = self._run(profiles)
        assert result["lead"] == 0.0  # techno LEAD default

    def test_pads_wide_spread_when_same_register(self, profiles):
        result = self._run(profiles)
        assert abs(result["pad_a"]) == 0.40
        assert abs(result["pad_b"]) == 0.40
        assert result["pad_a"] != result["pad_b"]  # opposite sides

    def test_fx_outer_position(self, profiles):
        result = self._run(profiles)
        assert abs(result["fx_whoosh"]) == 0.60

    def test_no_role_keys_in_return(self, profiles):
        """Output must use plain string keys for MasteringDesk compatibility."""
        result = self._run(profiles)
        for k in result:
            assert isinstance(k, str), f"Expected str key, got {type(k)}: {k}"

    @pytest.mark.parametrize("genre,strings_pan", [
        ("techno",  0.20),
        ("rnb",     0.25),
        ("trap",     0.0),   # no STRINGS in trap → falls back to Role default (0.0)
    ])
    def test_strings_respects_genre_profile(self, genre, strings_pan, profiles):
        result = self._run(profiles, genre=genre)
        assert result["strings"] == pytest.approx(strings_pan, abs=0.01)

    def test_pads_far_apart_no_overlap(self, profiles):
        result = self._run(profiles)
        # pad_a at -0.40 and pad_b at +0.40 — no clash possible
        assert abs(result["pad_a"] - result["pad_b"]) > 0.75


# ---------------------------------------------------------------------------
# Layer 4: PanValidator
# ---------------------------------------------------------------------------

class TestPanValidator:
    validator = PanValidator()

    @pytest.mark.parametrize("genre", ["techno", "rnb", "trap"])
    def test_balanced_pan_map_passes(self, genre: str):
        roles = {
            "bass":   Role.BASS,
            "lead":   Role.LEAD,
            "pad":    Role.PAD,
            "fx":     Role.FX,
            "strings":Role.STRINGS,
        }
        profile_dummy = lambda name, role: _TrackProfile(
            avg_pitch=60.0, pitch_range=12.0, density=0.1,
            rms_velocity=80.0, role=role
        )
        profiles = {name: profile_dummy(name, role) for name, role in roles.items()}
        pan_map = {
            "bass":   0.0,
            "lead":   0.0,
            "pad":   -0.30,
            "fx":     0.30,
            "strings":0.20,
        }
        warns = self.validator.validate(pan_map, profiles)
        assert warns == [], f"Unexpected warnings: {warns}"

    @pytest.mark.parametrize("name,role_bad,pan_bad", [
        ("my_bass", Role.BASS,  0.50),   # bass should be centre
        ("my_lead", Role.LEAD,  0.50),   # lead should be near centre
        ("my_pad",  Role.PAD,   0.20),   # pad should be left of centre
        ("my_fx",   Role.FX,   -0.10),   # fx should be right
    ])
    def test_violations_detected(self, name, role_bad, pan_bad):
        profiles = {name: _TrackProfile(
            avg_pitch=60.0, pitch_range=12.0, density=0.1,
            rms_velocity=80.0, role=role_bad,
        )}
        warns = self.validator.validate({name: pan_bad}, profiles)
        assert len(warns) >= 1

    def test_empty_inputs_no_crash(self):
        warns = self.validator.validate({}, {})
        assert warns == []

    def test_same_position_except_center_reports(self):
        profiles = {
            "a": _TrackProfile(avg_pitch=60.0, pitch_range=12.0, density=0.1,
                               rms_velocity=80.0, role=Role.STRINGS),
            "b": _TrackProfile(avg_pitch=61.0, pitch_range=12.0, density=0.1,
                               rms_velocity=80.0, role=Role.CHOIR),
        }
        pan_map = {"a": 0.20, "b": 0.20}
        warns = self.validator.validate(pan_map, profiles)
        assert any("одной точке" in w for w in warns)


# ---------------------------------------------------------------------------
# Layer 2: _hat_pan_value — width parameter and random mode
# ---------------------------------------------------------------------------

from melodica.generators.electronic_drums import ElectronicDrumsGenerator


class TestHatPanValue:
    @pytest.mark.parametrize("width,expected_spread", [
        (0.0,  0),    # no spread → always centre
        (0.20, 12),   # ±12 CC units
        (1.0,  63),   # full edge-to-edge
    ])
    def test_width_scales_spread(self, width, expected_spread):
        vals = [
            ElectronicDrumsGenerator._hat_pan_value("sweep_lr", i, 0.5, width)
            for i in range(4)
        ]
        assert max(vals) <= 64 + expected_spread
        assert min(vals) >= 64 - expected_spread

    def test_random_mode_varies(self):
        """random mode must produce a range, not a constant."""
        import random
        seen = {ElectronicDrumsGenerator._hat_pan_value(
            "random", i, 0.5, 1.0
        ) for i in range(40)}
        assert len(seen) > 1, "random mode should vary"

    def test_mono_and_off_are_center(self):
        assert ElectronicDrumsGenerator._hat_pan_value("mono",  0, 0.5, 0.35) == 64
        assert ElectronicDrumsGenerator._hat_pan_value("off",   0, 0.5, 0.35) == 64

    def test_alternate_flips(self):
        a = ElectronicDrumsGenerator._hat_pan_value("alternate", 0, 0.5, 0.20)
        b = ElectronicDrumsGenerator._hat_pan_value("alternate", 1, 0.5, 0.20)
        assert a != b

    def test_width_zero_still_center(self):
        for mode in ("alternate", "sweep_lr", "sweep_rl"):
            v = ElectronicDrumsGenerator._hat_pan_value(mode, 5, 0.5, 0.0)
            assert v == 64
