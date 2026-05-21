# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from melodica.rhythm import RhythmEvent, GrooveTemplate, GrooveSlot, GROOVE_PRESETS
from melodica.rhythm.groove_template import STRAIGHT, SWING_60, HARD_SWING, SHUFFLE, LAID_BACK


class TestGrooveSlot:
    def test_creation(self):
        s = GrooveSlot(position=0.5, timing_offset=3.5, velocity_factor=0.88)
        assert s.position == 0.5
        assert s.timing_offset == 3.5
        assert s.velocity_factor == 0.88

    def test_frozen(self):
        s = GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0)
        try:
            s.position = 0.5
            assert False, "Should be frozen"
        except AttributeError:
            pass


class TestGrooveTemplate:
    def test_straight_no_change(self):
        events = [
            RhythmEvent(onset=0.0, duration=1.0, velocity_factor=1.0),
            RhythmEvent(onset=1.0, duration=1.0, velocity_factor=1.0),
        ]
        result = STRAIGHT.apply(events)
        assert len(result) == 2
        assert result[0].onset == 0.0
        assert result[1].onset == 1.0

    def test_empty_slots_returns_copy(self):
        gt = GrooveTemplate(name="empty")
        events = [RhythmEvent(onset=0.0, duration=1.0, velocity_factor=1.0)]
        result = gt.apply(events)
        assert result is not events
        assert len(result) == 1

    def test_swing_shifts_offbeats(self):
        events = [
            RhythmEvent(onset=0.0, duration=0.5, velocity_factor=1.0),
            RhythmEvent(onset=0.5, duration=0.5, velocity_factor=1.0),
        ]
        result = SWING_60.apply(events)
        assert len(result) == 2
        # On-beat (position 0.0) unchanged
        assert result[0].onset == 0.0
        # Off-beat (position 0.5) shifted later
        assert result[1].onset > 0.5

    def test_swing_reduces_velocity(self):
        events = [
            RhythmEvent(onset=0.5, duration=0.5, velocity_factor=1.0),
        ]
        result = SWING_60.apply(events)
        assert result[0].velocity_factor < 1.0

    def test_hard_swing_more_shift(self):
        events = [
            RhythmEvent(onset=0.5, duration=0.5, velocity_factor=1.0),
        ]
        swing_result = SWING_60.apply(events)
        hard_result = HARD_SWING.apply(events)
        assert hard_result[0].onset > swing_result[0].onset

    def test_empty_events(self):
        result = SWING_60.apply([])
        assert result == []

    def test_non_matching_position_unchanged(self):
        events = [
            RhythmEvent(onset=0.33, duration=0.5, velocity_factor=1.0),
        ]
        result = SWING_60.apply(events)
        assert result[0].onset == 0.33
        assert result[0].velocity_factor == 1.0


class TestGroovePresets:
    def test_all_presets_exist(self):
        assert "straight" in GROOVE_PRESETS
        assert "swing_60" in GROOVE_PRESETS
        assert "hard_swing" in GROOVE_PRESETS
        assert "shuffle" in GROOVE_PRESETS
        assert "laid_back" in GROOVE_PRESETS

    def test_preset_count(self):
        assert len(GROOVE_PRESETS) == 5

    def test_straight_has_no_slots(self):
        assert len(STRAIGHT.slots) == 0

    def test_swing_has_two_slots(self):
        assert len(SWING_60.slots) == 2

    def test_shuffle_has_three_slots(self):
        assert len(SHUFFLE.slots) == 3

    def test_laid_back_has_four_slots(self):
        assert len(LAID_BACK.slots) == 4
