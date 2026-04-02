"""
tests/test_orchestration.py — Tests for OrchestralBalancer.

Covers:
  - apply_balancing() sets pan/volume/reverb from profiles
  - shift_octaves_into_range() shifts notes into instrument range
  - scale_velocities() scales by spectral priority
  - Edge cases: unknown track name, empty notes, boost parameter
"""

import pytest
from melodica.types import NoteInfo
from melodica.types_pkg._phrases import Track
from melodica.application.orchestration import OrchestralBalancer, ORCHESTRAL_PROFILES


def _track(name: str, pitches: list[int] | None = None) -> Track:
    t = Track(name=name)
    if pitches is None:
        pitches = [60, 64, 67]
    t.notes = [
        NoteInfo(pitch=p, start=i * 1.0, duration=0.8, velocity=80) for i, p in enumerate(pitches)
    ]
    return t


# ===================================================================
# §1 — apply_balancing
# ===================================================================


class TestApplyBalancing:
    def test_sets_pan_from_profile(self):
        tracks = [_track("Violins_I")]
        result = OrchestralBalancer.apply_balancing(tracks)
        assert result[0].pan == ORCHESTRAL_PROFILES["Violins_I"].default_pan

    def test_sets_volume_from_profile(self):
        tracks = [_track("Cello")]
        result = OrchestralBalancer.apply_balancing(tracks)
        assert result[0].volume == ORCHESTRAL_PROFILES["Cello"].default_volume

    def test_sets_reverb_from_profile(self):
        tracks = [_track("Harp")]
        result = OrchestralBalancer.apply_balancing(tracks)
        assert result[0].reverb == ORCHESTRAL_PROFILES["Harp"].default_reverb

    def test_sets_instrument_name(self):
        tracks = [_track("Trumpet")]
        result = OrchestralBalancer.apply_balancing(tracks)
        assert result[0].instrument_name == ORCHESTRAL_PROFILES["Trumpet"].name

    def test_skips_unknown_track(self):
        t = _track("Unknown_Instrument")
        orig_pan = t.pan
        result = OrchestralBalancer.apply_balancing([t])
        assert result[0].pan == orig_pan  # unchanged

    def test_expression_set_to_127(self):
        tracks = [_track("Flute")]
        result = OrchestralBalancer.apply_balancing(tracks)
        assert result[0].expression == 127

    def test_multiple_tracks(self):
        tracks = [_track("Violins_I"), _track("Cello"), _track("Contrabass")]
        result = OrchestralBalancer.apply_balancing(tracks)
        assert len(result) == 3
        for t in result:
            assert t.instrument_name != ""


# ===================================================================
# §2 — shift_octaves_into_range
# ===================================================================


class TestShiftOctaves:
    def test_shifts_low_notes_up(self):
        # Cello range is 36-64. Notes at pitch 30 should shift up.
        t = _track("Cello", [30, 32, 34])
        result = OrchestralBalancer.shift_octaves_into_range([t])
        avg = sum(n.pitch for n in result[0].notes) / len(result[0].notes)
        assert avg >= 36

    def test_shifts_high_notes_down(self):
        # Cello range is 36-64. Notes at pitch 80 should shift down.
        t = _track("Cello", [80, 82, 84])
        result = OrchestralBalancer.shift_octaves_into_range([t])
        avg = sum(n.pitch for n in result[0].notes) / len(result[0].notes)
        assert avg <= 64

    def test_within_range_unchanged(self):
        # Notes already in range should stay
        t = _track("Cello", [48, 52, 56])
        original_pitches = [n.pitch for n in t.notes]
        result = OrchestralBalancer.shift_octaves_into_range([t])
        new_pitches = [n.pitch for n in result[0].notes]
        assert original_pitches == new_pitches

    def test_empty_track_skipped(self):
        t = _track("Cello")
        t.notes = []
        result = OrchestralBalancer.shift_octaves_into_range([t])
        assert result[0].notes == []

    def test_unknown_track_skipped(self):
        t = _track("Unknown", [30, 32, 34])
        original_pitches = [n.pitch for n in t.notes]
        result = OrchestralBalancer.shift_octaves_into_range([t])
        assert [n.pitch for n in result[0].notes] == original_pitches


# ===================================================================
# §3 — scale_velocities
# ===================================================================


class TestScaleVelocities:
    def test_scales_by_priority(self):
        t = _track("Timpani")  # priority=100
        original_vel = t.notes[0].velocity
        result = OrchestralBalancer.scale_velocities([t])
        # priority=100, factor=1.0 → velocity * 1.0 = same
        assert result[0].notes[0].velocity == original_vel

    def test_lower_priority_reduces_velocity(self):
        t = _track("Harp")  # priority=70
        original_vel = t.notes[0].velocity
        result = OrchestralBalancer.scale_velocities([t])
        assert result[0].notes[0].velocity <= original_vel

    def test_boost_increases(self):
        t = _track("Cello")  # priority=85
        base = OrchestralBalancer.scale_velocities([_track("Cello")])
        boosted = OrchestralBalancer.scale_velocities([_track("Cello")], boost=1.5)
        assert boosted[0].notes[0].velocity >= base[0].notes[0].velocity

    def test_velocity_capped_at_127(self):
        t = _track("Timpani")  # priority=100
        for n in t.notes:
            n.velocity = 120
        result = OrchestralBalancer.scale_velocities([t], boost=2.0)
        for n in result[0].notes:
            assert n.velocity <= 127

    def test_empty_track_skipped(self):
        t = _track("Cello")
        t.notes = []
        result = OrchestralBalancer.scale_velocities([t])
        assert result[0].notes == []
