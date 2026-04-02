"""
tests/test_postprocess.py — Tests for _postprocess.py public functions.

Covers:
  - apply_velocity_shaping() — velocity scaling by tension curve
  - apply_track_modifiers() — modifier pipeline execution
  - apply_non_chord_tones() — NCT insertion
  - Edge cases: empty notes, falsy tension, no modifiers
"""

import pytest
from unittest.mock import MagicMock, patch
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica._postprocess import (
    apply_velocity_shaping,
    apply_track_modifiers,
    apply_non_chord_tones,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


class FakeTensionCurve:
    """Stub tension curve returning constant tension."""

    def __init__(self, value: float = 0.5):
        self._value = value

    def tension_at(self, t: float) -> float:
        return self._value

    def __bool__(self):
        return True


class FakeTrackCfg:
    def __init__(self, name="melody", modifiers=None):
        self.name = name
        self.modifiers = modifiers or []


def _notes(n=4):
    return [NoteInfo(pitch=60 + i, start=i * 1.0, duration=0.8, velocity=80) for i in range(n)]


# ===================================================================
# §1 — apply_velocity_shaping
# ===================================================================


class TestApplyVelocityShaping:
    def test_scales_velocity(self):
        result = {"melody": _notes(5)}
        curve = FakeTensionCurve(0.5)
        apply_velocity_shaping(result, [FakeTrackCfg("melody")], curve)
        # factor = 0.6 + 0.4 * 0.5 = 0.8, vel = 80 * 0.8 = 64
        assert result["melody"][0].velocity == 64

    def test_high_tension_max_velocity(self):
        result = {"melody": _notes(3)}
        curve = FakeTensionCurve(1.0)
        apply_velocity_shaping(result, [FakeTrackCfg("melody")], curve)
        # factor = 0.6 + 0.4 * 1.0 = 1.0 → unchanged
        assert result["melody"][0].velocity == 80

    def test_low_tension_reduces(self):
        result = {"melody": _notes(3)}
        curve = FakeTensionCurve(0.0)
        apply_velocity_shaping(result, [FakeTrackCfg("melody")], curve)
        # factor = 0.6 + 0.4 * 0.0 = 0.6, vel = 80 * 0.6 = 48
        assert result["melody"][0].velocity == 48

    def test_falsy_curve_skips(self):
        result = {"melody": _notes(3)}
        original_vel = result["melody"][0].velocity
        apply_velocity_shaping(result, [FakeTrackCfg("melody")], None)
        assert result["melody"][0].velocity == original_vel

    def test_velocity_clamped(self):
        result = {"melody": [NoteInfo(pitch=60, start=0, duration=1, velocity=120)]}
        curve = FakeTensionCurve(1.0)
        apply_velocity_shaping(result, [FakeTrackCfg("melody")], curve)
        assert result["melody"][0].velocity <= 127

    def test_skips_missing_track(self):
        result = {"bass": _notes(3)}
        curve = FakeTensionCurve(0.5)
        apply_velocity_shaping(result, [FakeTrackCfg("melody")], curve)
        # "melody" not in result → skipped, bass unchanged
        assert result["bass"][0].velocity == 80


# ===================================================================
# §2 — apply_track_modifiers
# ===================================================================


class TestApplyTrackModifiers:
    def test_no_modifiers_returns_unchanged(self):
        cfg = FakeTrackCfg(modifiers=[])
        notes = _notes(4)
        result = apply_track_modifiers(notes, cfg, [], C_MAJOR, (4, 4), 16.0)
        assert len(result) == 4

    def test_with_mock_modifier(self):
        mod = MagicMock()
        mod.modify.return_value = _notes(2)
        cfg = FakeTrackCfg(modifiers=[mod])
        notes = _notes(4)
        result = apply_track_modifiers(notes, cfg, [], C_MAJOR, (4, 4), 16.0)
        mod.modify.assert_called_once()
        assert len(result) == 2

    def test_modifier_exception_caught(self):
        mod = MagicMock()
        mod.modify.side_effect = RuntimeError("boom")
        cfg = FakeTrackCfg(modifiers=[mod])
        notes = _notes(4)
        # Should not raise — exception caught and logged
        result = apply_track_modifiers(notes, cfg, [], C_MAJOR, (4, 4), 16.0)
        assert len(result) == 4  # original notes returned


# ===================================================================
# §3 — apply_non_chord_tones
# ===================================================================


class TestApplyNonChordTones:
    def test_adds_notes(self):
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)]
        result = apply_non_chord_tones(notes, FakeTrackCfg(), chords, C_MAJOR)
        assert isinstance(result, list)
        assert len(result) >= 1

    def test_empty_notes(self):
        result = apply_non_chord_tones([], FakeTrackCfg(), [], C_MAJOR)
        assert result == []

    def test_exception_caught(self):
        """Bad chord data should not crash."""
        result = apply_non_chord_tones(
            [NoteInfo(pitch=60, start=0, duration=1)],
            FakeTrackCfg(),
            None,  # will cause exception inside NCT
            C_MAJOR,
        )
        assert isinstance(result, list)
