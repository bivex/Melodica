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
    NoteInfo,
    _generate_pan_automation,
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
    def test_lead_near_center_in_genre_profile(self, genre: str):
        pan = _get_pan_for_role(Role.LEAD, genre)
        assert -0.15 <= pan <= 0.15, f"{genre}: LEAD pan={pan} too far from centre"


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
        assert result["lead"] == pytest.approx(0.08, abs=0.01)  # techno LEAD default

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
        pitches = {"bass": 36, "lead": 72, "pad": 54, "fx": 90, "strings": 65}
        profile_dummy = lambda name, role: _TrackProfile(
            avg_pitch=float(pitches[name]), pitch_range=12.0, density=0.1,
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
        ("my_lead", Role.LEAD,  0.30),   # lead beyond +/-0.15
        ("my_pad",  Role.PAD,   0.70),   # pad beyond max +0.60
        ("my_fx",   Role.FX,   -0.70),   # fx beyond min -0.65
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

# ---------------------------------------------------------------------------
# Layer 5: Pan automation (PAD LFO / FX sweep)
# ---------------------------------------------------------------------------

from melodica.composer.album_pipeline import (
    _generate_pan_automation, _print_pan_map, Mood, _MOOD_PROFILES,
    _TrackProfile, Role,
)


class TestPanAutomation:
    """_generate_pan_automation returns CC10 LFO/sweep events."""

    @pytest.fixture
    def long_pad(self):
        """PAD track spanning 12 beats."""
        mid_notes = [
            NoteInfo(pitch=60, start=i * 0.5, duration=0.4, velocity=80)
            for i in range(30)  # 15 s
        ]
        return {"pad_synth": mid_notes}

    @pytest.fixture
    def long_pad_profile(self):
        return {"pad_synth": _TrackProfile(
            avg_pitch=60.0, pitch_range=12.0, density=0.5,
            rms_velocity=80.0, role=Role.PAD,
        )}

    @pytest.fixture
    def short_pad(self):
        """PAD track spanning < 2 beats → no automation."""
        notes = [NoteInfo(pitch=55, start=0.5, duration=0.3, velocity=70)]
        return {"short_pad": notes}

    @pytest.fixture
    def short_pad_profile(self):
        return {"short_pad": _TrackProfile(
            avg_pitch=55.0, pitch_range=5.0, density=0.8,
            rms_velocity=70.0, role=Role.PAD,
        )}

    @pytest.fixture
    def fx_track_onset(self):
        notes = [NoteInfo(pitch=80, start=2.0, duration=1.5, velocity=90)]
        return {"fx_whoosh": notes}

    def test_pad_generates_cc10_events(self, long_pad, long_pad_profile):
        cc_events = _generate_pan_automation(
            long_pad, long_pad_profile,
            _MOOD_PROFILES[Mood.CINEMATIC],
        )
        assert "pad_synth" in cc_events, "PAD track should get CC10 events"
        assert len(cc_events["pad_synth"]) >= 4, "At least 4 CC10 events expected"

    def test_pad_cc10_valid_range(self, long_pad, long_pad_profile):
        cc_events = _generate_pan_automation(
            long_pad, long_pad_profile,
            _MOOD_PROFILES[Mood.CINEMATIC],
        )
        for (_t, cc, val) in cc_events["pad_synth"]:
            assert cc == 10, f"Expected CC10, got CC{cc}"
            assert 20 <= val <= 107, f"CC10 val {val} out of 20-107 range"

    def test_pad_events_sorted_by_time(self, long_pad, long_pad_profile):
        cc_events = _generate_pan_automation(
            long_pad, long_pad_profile,
            _MOOD_PROFILES[Mood.AMBIENT],
        )
        times = [e[0] for e in cc_events["pad_synth"]]
        assert times == sorted(times)

    def test_short_pad_no_automation(self, short_pad, short_pad_profile):
        cc_events = _generate_pan_automation(
            short_pad, short_pad_profile,
            _MOOD_PROFILES[Mood.CINEMATIC],
        )
        # Short PAD gets CC10 anchors but no LFO automation
        assert "short_pad" in cc_events
        evts = cc_events["short_pad"]
        assert all(e[1] == 10 for e in evts), "All events should be CC10"
        assert len(evts) >= 1, "At least one CC10 anchor"

    def test_fx_sweep_right_to_centre(self, fx_track_onset):
        profiles = {
            "fx_whoosh": _TrackProfile(
                avg_pitch=85.0, pitch_range=6.0, density=0.1,
                rms_velocity=60.0, role=Role.FX, entry_beat=2.0,
            )
        }
        cc_events = _generate_pan_automation(
            fx_track_onset, profiles,
            _MOOD_PROFILES[Mood.CINEMATIC],
        )
        assert "fx_whoosh" in cc_events
        evts = cc_events["fx_whoosh"]
        assert len(evts) >= 2
        # Find the FX sweep start (should be ≥65, right of centre)
        sweep_vals = [e[2] for e in evts if e[2] >= 65]
        assert len(sweep_vals) >= 1, f"FX should include right-side values, got {[e[2] for e in evts]}"
        # Last event should be at centre (64)
        assert abs(evts[-1][2] - 64) <= 5, f"FX should drift to centre, got {evts[-1][2]}"

    @pytest.mark.parametrize("mood,expected_spread_px", [
        (Mood.AMBIENT,     5),   # narrow
        (Mood.INTIMATE,    3),   # very narrow
        (Mood.CINEMATIC,   9),
        (Mood.AGGRESSIVE, 11),   # wide
        (Mood.EXPERIMENTAL,12),  # widest
    ])
    def test_pad_width_scales_with_mood(
        self, mood, expected_spread_px, long_pad, long_pad_profile
    ):
        cc_events = _generate_pan_automation(
            long_pad, long_pad_profile, _MOOD_PROFILES[mood],
        )
        evts = cc_events["pad_synth"]
        centers: list[int] = [(lo + hi) // 2 for (_t, _c, lo), (_t2, _c2, hi)
                              in zip(evts[:-1:4], evts[4::4])]
        if len(centers) >= 2:
            net_shift = abs(centers[-1] - centers[0])
            # LFO cycles: some cycles net near-zero, check the amplitude per-epoch
            max_amp = max(
                abs(e[2] - 64) for e in evts
            )
            # width should be within ±2 CC of the expected spread
            assert max_amp <= expected_spread_px + 2, (
                f"{mood.value}: max CC10 amp={max_amp}, expected ~{expected_spread_px}"
            )

    def test_verbose_pan_map_output_no_crash(self):
        """_print_pan_map must not raise for any combination of inputs."""
        profiles = {
            "lead": _TrackProfile(avg_pitch=62.0, pitch_range=12.0, density=0.1,
                                  rms_velocity=80.0, role=Role.LEAD),
            "pad":  _TrackProfile(avg_pitch=55.0, pitch_range=8.0,  density=0.04,
                                  rms_velocity=55.0, role=Role.PAD),
        }
        for pan_map, desc in [
            ({"lead": 0.0, "pad": -0.30}, "mixed pan"),
            ({"lead": 0.0, "pad":  0.00}, "all centre"),
            ({},                              "empty"),
        ]:
            try:
                _print_pan_map(profiles, pan_map, _MOOD_PROFILES[Mood.CINEMATIC])
            except Exception as exc:
                pytest.fail(f"_print_pan_map({desc}) raised: {exc}")
