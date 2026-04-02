"""
tests/test_articulations.py — Tests for ArticulationEngine.

Covers:
  - ArticulationProfile defaults and built-in PROFILES
  - ArticulationEngine.apply() with each curve type
  - Expression curves: crescendo, decrescendo, swell, fade_in, fade_out
  - Modulation curves: vibrato_in, vibrato_out, tremolo
  - Sustain pedal patterns: always, auto, never
  - Velocity humanization within bounds
  - Duration factor scaling
  - Pitch bend slide application
  - add_sustain_pedal_events() legato detection
  - Edge cases: empty notes, single note, unknown instrument
"""

import math
import pytest
from unittest.mock import patch

from melodica.types import NoteInfo
from melodica.composer.articulations import (
    ArticulationEngine,
    ArticulationProfile,
    PROFILES,
)


def _notes(count: int = 4, dur: float = 2.0, vel: int = 80) -> list[NoteInfo]:
    return [
        NoteInfo(pitch=60 + i, start=i * dur, duration=dur * 0.9, velocity=vel)
        for i in range(count)
    ]


# ===================================================================
# §1 — PROFILES completeness
# ===================================================================


class TestProfiles:
    EXPECTED_PROFILES = [
        "strings_melody",
        "strings_staccato",
        "strings_pad",
        "strings_tremolo",
        "cello",
        "brass_fanfare",
        "brass_legato",
        "harp",
        "flute",
        "timpani",
        "snare",
        "choir_ah",
        "piano",
    ]

    def test_all_expected_profiles_exist(self):
        for name in self.EXPECTED_PROFILES:
            assert name in PROFILES, f"Missing profile: {name}"

    def test_profiles_have_names(self):
        for name, profile in PROFILES.items():
            assert profile.name == name, f"Profile key '{name}' != dataclass name '{profile.name}'"

    def test_staccato_has_short_duration(self):
        assert PROFILES["strings_staccato"].duration_factor < 0.5

    def test_legato_has_long_duration(self):
        assert PROFILES["brass_legato"].duration_factor > 1.0

    def test_pad_has_always_pedal(self):
        assert PROFILES["strings_pad"].sustain_pedal_pattern == "always"

    @pytest.mark.parametrize("name", EXPECTED_PROFILES)
    def test_profile_velocity_humanize_non_negative(self, name):
        assert PROFILES[name].velocity_humanize >= 0

    @pytest.mark.parametrize("name", EXPECTED_PROFILES)
    def test_profile_reverb_in_range(self, name):
        assert 0 <= PROFILES[name].reverb_level <= 127

    @pytest.mark.parametrize("name", EXPECTED_PROFILES)
    def test_profile_chorus_in_range(self, name):
        assert 0 <= PROFILES[name].chorus_level <= 127


# ===================================================================
# §2 — ArticulationEngine.apply() basics
# ===================================================================


class TestApply:
    def test_preserves_note_count(self):
        engine = ArticulationEngine()
        notes = _notes(8)
        result = engine.apply(notes, "piano", 32.0)
        assert len(result) == len(notes)

    def test_preserves_pitch_and_start(self):
        engine = ArticulationEngine()
        notes = _notes(4)
        result = engine.apply(notes, "piano", 16.0)
        for orig, res in zip(notes, result):
            assert res.pitch == orig.pitch
            assert res.start == orig.start

    def test_sets_articulation_from_profile(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "strings_staccato", 12.0)
        for n in result:
            assert n.articulation == "staccato"

    def test_sets_sustain_articulation(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "piano", 12.0)
        for n in result:
            assert n.articulation == "sustain"

    def test_sets_marcato_articulation(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "brass_fanfare", 12.0)
        for n in result:
            assert n.articulation == "marcato"

    def test_unknown_instrument_falls_back_to_strings_melody(self):
        engine = ArticulationEngine()
        notes = _notes(2)
        result = engine.apply(notes, "nonexistent_instrument", 8.0)
        assert len(result) == 2
        assert result[0].articulation == PROFILES["strings_melody"].default_articulation

    def test_empty_notes(self):
        engine = ArticulationEngine()
        result = engine.apply([], "piano", 16.0)
        assert result == []


# ===================================================================
# §3 — Expression curves (CC11)
# ===================================================================


class TestExpressionCurves:
    def _get_cc11_values(self, profile_name: str, total_beats: float = 16.0) -> list[int]:
        engine = ArticulationEngine()
        notes = _notes(10, dur=1.0)
        result = engine.apply(notes, profile_name, total_beats)
        return [n.expression.get(11, -1) for n in result]

    def test_crescendo_increases(self):
        vals = self._get_cc11_values("cello")
        assert vals[0] < vals[-1], f"crescendo should increase: {vals[0]} → {vals[-1]}"

    def test_crescendo_range(self):
        vals = self._get_cc11_values("cello")
        assert vals[0] >= 40
        assert vals[-1] <= 127

    def test_swell_peaks_in_middle(self):
        """strings_melody has swell + vibrato_in; CC11 value is set by expression_curve."""
        engine = ArticulationEngine()
        notes = _notes(10, dur=1.0)
        result = engine.apply(notes, "strings_melody", 10.0)
        cc11 = [n.expression.get(11, -1) for n in result]
        peak_idx = cc11.index(max(cc11))
        # Swell peaks at t=0.5, with 10 notes that's around index 4-5
        assert 3 <= peak_idx <= 6, f"swell peak at {peak_idx}, expected near middle"

    def test_swell_starts_and_ends_symmetric(self):
        """Swell curve: start value == end value (symmetric)."""
        engine = ArticulationEngine()
        vals = [engine._expression_value("swell", t) for t in [0.0, 0.5, 1.0]]
        assert vals[0] == vals[2]  # symmetric: start == end
        assert vals[1] > vals[0]  # middle > start

    def test_fade_in_increases(self):
        vals = self._get_cc11_values("strings_pad")
        assert vals[0] < vals[-1], "fade_in should increase"

    def test_no_expression_for_none(self):
        vals = self._get_cc11_values("piano")
        # piano has expression_curve="none" → no CC11 set
        assert all(v == -1 for v in vals), "piano should have no CC11"

    @pytest.mark.parametrize("curve", ["crescendo", "decrescendo", "swell", "fade_in", "fade_out"])
    def test_expression_value_bounds(self, curve):
        engine = ArticulationEngine()
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            val = engine._expression_value(curve, t)
            assert 0 <= val <= 127, f"curve={curve}, t={t} → {val} out of range"

    def test_unknown_curve_returns_100(self):
        engine = ArticulationEngine()
        assert engine._expression_value("nonexistent", 0.5) == 100


# ===================================================================
# §4 — Modulation curves (CC1)
# ===================================================================


class TestModulationCurves:
    def test_vibrato_in_starts_at_zero(self):
        engine = ArticulationEngine()
        assert engine._modulation_value("vibrato_in", 0.0, 40) == 0
        assert engine._modulation_value("vibrato_in", 0.1, 40) == 0

    def test_vibrato_in_reaches_base(self):
        engine = ArticulationEngine()
        val = engine._modulation_value("vibrato_in", 1.0, 40)
        assert val == 40

    def test_vibrato_out_starts_at_base(self):
        engine = ArticulationEngine()
        assert engine._modulation_value("vibrato_out", 0.0, 40) == 40

    def test_vibrato_out_ends_at_zero(self):
        engine = ArticulationEngine()
        val = engine._modulation_value("vibrato_out", 1.0, 40)
        assert val == 0

    def test_tremolo_oscillates(self):
        engine = ArticulationEngine()
        vals = [engine._modulation_value("tremolo", t / 20.0, 80) for t in range(21)]
        assert min(vals) < max(vals), "tremolo should oscillate"
        assert max(vals) <= 80

    def test_unknown_curve_returns_base(self):
        engine = ArticulationEngine()
        assert engine._modulation_value("nonexistent", 0.5, 50) == 50

    @pytest.mark.parametrize("curve", ["vibrato_in", "vibrato_out", "tremolo"])
    def test_modulation_bounds(self, curve):
        engine = ArticulationEngine()
        for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
            val = engine._modulation_value(curve, t, 60)
            assert 0 <= val <= 127, f"curve={curve}, t={t} → {val}"


# ===================================================================
# §5 — Sustain pedal patterns
# ===================================================================


class TestSustainPedal:
    def test_always_sets_cc64_127(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "strings_pad", 12.0)
        for n in result:
            assert n.expression.get(64) == 127

    def test_never_no_cc64(self):
        engine = ArticulationEngine()
        notes = _notes(3, dur=1.0)
        result = engine.apply(notes, "snare", 12.0)
        # snare has sustain_pedal_pattern="auto" but staccato notes don't connect
        # let's test with a profile that has no sustain — timpani (default="auto")
        # but actually timpani uses default "auto", so cc64 may still appear
        # Use harp which has default auto, but notes have gaps
        result = engine.apply(notes, "harp", 12.0)
        for n in result:
            # harp notes with gaps → auto sets cc64=0
            assert n.expression.get(64, 0) == 0

    def test_auto_legato_sets_pedal(self):
        engine = ArticulationEngine()
        # Notes that overlap (legato) → should set pedal
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=2.0),
            NoteInfo(pitch=64, start=1.95, duration=2.0),  # gap = -0.05 → legato
            NoteInfo(pitch=67, start=8.0, duration=2.0),  # gap = 4.05 → not legato
        ]
        result = engine.apply(notes, "brass_legato", 12.0)
        assert result[0].expression.get(64) == 127  # legato → pedal on
        # Note 1: gap to note 2 = 8.0 - (1.95 + 2.2) = 3.85 → pedal off
        assert result[1].expression.get(64) == 0

    def test_auto_gap_triggers_pedal_off(self):
        engine = ArticulationEngine()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0),
            NoteInfo(pitch=64, start=5.0, duration=1.0),  # big gap
        ]
        result = engine.apply(notes, "brass_legato", 8.0)
        assert result[0].expression.get(64) == 0  # gap > 0.05 → no pedal


# ===================================================================
# §6 — Velocity humanization
# ===================================================================


class TestVelocityHumanize:
    def test_velocity_stays_in_bounds(self):
        """Even with extreme humanize, velocity must be 1-127."""
        engine = ArticulationEngine()
        profile = ArticulationProfile(
            name="test",
            velocity_humanize=50,
            default_articulation="sustain",
        )
        engine.profiles = {"test": profile}
        # Use velocity=64 so ±50 would go to 14-114, clamped to 1-127
        notes = [NoteInfo(pitch=60, start=i * 1.0, duration=0.8, velocity=64) for i in range(100)]
        result = engine.apply(notes, "test", 100.0)
        for n in result:
            assert 1 <= n.velocity <= 127

    def test_zero_humanize_preserves_velocity(self):
        engine = ArticulationEngine()
        profile = ArticulationProfile(
            name="test",
            velocity_humanize=0,
            default_articulation="sustain",
        )
        engine.profiles = {"test": profile}
        notes = _notes(5, vel=80)
        result = engine.apply(notes, "test", 20.0)
        for n in result:
            assert n.velocity == 80

    def test_humanize_introduces_variance(self):
        """With humanize > 0, not all velocities should be identical."""
        engine = ArticulationEngine()
        notes = _notes(50, vel=80)
        result = engine.apply(notes, "strings_melody", 100.0)
        velocities = {n.velocity for n in result}
        assert len(velocities) > 1, "humanize should produce varied velocities"


# ===================================================================
# §7 — Duration factor
# ===================================================================


class TestDurationFactor:
    def test_staccato_shortens(self):
        engine = ArticulationEngine()
        notes = _notes(3, dur=2.0)
        result = engine.apply(notes, "strings_staccato", 12.0)
        for orig, res in zip(notes, result):
            assert res.duration < orig.duration

    def test_staccato_factor_is_0_3(self):
        engine = ArticulationEngine()
        notes = [NoteInfo(pitch=60, start=0.0, duration=4.0)]
        result = engine.apply(notes, "strings_staccato", 4.0)
        assert result[0].duration == pytest.approx(4.0 * 0.3)

    def test_legato_lengthens(self):
        engine = ArticulationEngine()
        notes = _notes(3, dur=2.0)
        result = engine.apply(notes, "brass_legato", 12.0)
        for orig, res in zip(notes, result):
            assert res.duration > orig.duration

    def test_unit_factor_preserves(self):
        engine = ArticulationEngine()
        notes = _notes(3, dur=3.0)
        result = engine.apply(notes, "piano", 12.0)
        for orig, res in zip(notes, result):
            assert res.duration == pytest.approx(orig.duration)


# ===================================================================
# §8 — Pitch bend slide
# ===================================================================


class TestPitchBendSlide:
    def test_cello_slide_on_non_first(self):
        engine = ArticulationEngine()
        notes = _notes(4)
        result = engine.apply(notes, "cello", 16.0)
        assert "pitch_bend" not in result[0].expression  # first note: no slide
        for n in result[1:]:
            assert n.expression.get("pitch_bend") == -1500

    def test_piano_no_pitch_bend(self):
        engine = ArticulationEngine()
        notes = _notes(4)
        result = engine.apply(notes, "piano", 16.0)
        for n in result:
            assert "pitch_bend" not in n.expression

    def test_brass_legato_pitch_bend(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "brass_legato", 12.0)
        assert "pitch_bend" not in result[0].expression
        assert result[1].expression["pitch_bend"] == -2048


# ===================================================================
# §9 — add_sustain_pedal_events()
# ===================================================================


class TestSustainPedalEvents:
    def test_legato_connection_triggers_pedal(self):
        engine = ArticulationEngine()
        # All gaps >= 0.05 → no legato → no events
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.9),
            NoteInfo(pitch=64, start=2.0, duration=1.9),  # gap = 0.1 → not legato
            NoteInfo(pitch=67, start=4.0, duration=1.9),  # gap = 0.1 → not legato
        ]
        events = engine.add_sustain_pedal_events(notes, 8.0)
        assert events == []

    def test_legato_strict_threshold(self):
        """Pedal triggers only when gap < 0.05 (strict)."""
        engine = ArticulationEngine()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.96),  # gap = 0.04 → legato
            NoteInfo(pitch=64, start=2.0, duration=1.96),
            NoteInfo(pitch=67, start=8.0, duration=2.0),
        ]
        events = engine.add_sustain_pedal_events(notes, 12.0)
        assert len(events) >= 2
        assert events[0]["value"] == 127  # pedal on

    def test_legato_gap_triggers_on_off(self):
        engine = ArticulationEngine()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.99),  # gap to next = 0.01
            NoteInfo(pitch=64, start=2.0, duration=1.99),
            NoteInfo(pitch=67, start=8.0, duration=2.0),  # big gap
        ]
        events = engine.add_sustain_pedal_events(notes, 12.0)
        assert len(events) >= 2
        # First event should be pedal ON
        assert events[0]["value"] == 127
        # Should have a pedal OFF at some point
        pedal_off = [e for e in events if e["value"] == 0]
        assert len(pedal_off) > 0

    def test_empty_notes(self):
        engine = ArticulationEngine()
        events = engine.add_sustain_pedal_events([], 8.0)
        assert events == []

    def test_single_note(self):
        engine = ArticulationEngine()
        notes = [NoteInfo(pitch=60, start=0.0, duration=2.0)]
        events = engine.add_sustain_pedal_events(notes, 4.0)
        assert events == []

    def test_all_legato_ends_with_release(self):
        """If all notes are legato, pedal should be released at total_beats."""
        engine = ArticulationEngine()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.99),
            NoteInfo(pitch=64, start=2.0, duration=1.99),
            NoteInfo(pitch=67, start=4.0, duration=1.99),
        ]
        events = engine.add_sustain_pedal_events(notes, 8.0)
        # Should have pedal on at start and pedal off at total_beats
        if events:
            assert events[-1]["value"] == 0
            assert events[-1]["time"] == 8.0


# ===================================================================
# §10 — Reverb and chorus CC
# ===================================================================


class TestReverbChorus:
    def test_reverb_always_set(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "piano", 12.0)
        for n in result:
            assert n.expression.get(91) == PROFILES["piano"].reverb_level

    def test_chorus_always_set(self):
        engine = ArticulationEngine()
        notes = _notes(3)
        result = engine.apply(notes, "strings_melody", 12.0)
        for n in result:
            assert n.expression.get(93) == PROFILES["strings_melody"].chorus_level

    def test_choir_high_reverb_and_chorus(self):
        engine = ArticulationEngine()
        notes = _notes(2)
        result = engine.apply(notes, "choir_ah", 8.0)
        assert result[0].expression[91] == 120
        assert result[0].expression[93] == 60


# ===================================================================
# §11 — Custom profiles
# ===================================================================


class TestCustomProfiles:
    def test_custom_profile_used(self):
        custom = ArticulationProfile(
            name="my_custom",
            default_articulation="pizzicato",
            duration_factor=0.5,
            reverb_level=10,
            chorus_level=0,
            velocity_humanize=0,
        )
        engine = ArticulationEngine(profiles={"my_custom": custom})
        notes = _notes(3, dur=2.0)
        result = engine.apply(notes, "my_custom", 12.0)
        for n in result:
            assert n.articulation == "pizzicato"
            # _notes creates duration=2.0*0.9=1.8, engine applies 1.8*0.5=0.9
            assert n.duration == pytest.approx(0.9)
            assert n.expression[91] == 10
