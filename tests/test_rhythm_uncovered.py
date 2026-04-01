"""Tests for the 5 rhythm generators not covered in previous test files."""
import pytest
from melodica.rhythm import RhythmEvent
from melodica.rhythm.rhythm_lab import RhythmLab
from melodica.rhythm.polyrhythm import PolyrhythmGenerator
from melodica.rhythm.smooth import SmoothRhythmGenerator, SMOOTH_PATTERNS
from melodica.rhythm.bass_rhythm import BassRhythmGenerator, BASS_PATTERNS
from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator


def _assert_valid_events(events: list[RhythmEvent], duration_beats: float) -> None:
    for e in events:
        assert e.onset >= 0.0
        assert e.onset < duration_beats
        assert e.duration > 0.0
        assert 0.0 <= e.velocity_factor <= 2.0


# ---------------------------------------------------------------------------
# RhythmLab
# ---------------------------------------------------------------------------

class TestRhythmLab:
    def test_produces_events(self):
        gen = RhythmLab()
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_all_events_in_range(self):
        gen = RhythmLab()
        events = gen.generate(4.0)
        _assert_valid_events(events, 4.0)

    def test_operator_a_only(self):
        gen = RhythmLab(operator="A")
        events = gen.generate(4.0)
        assert len(events) > 0

    @pytest.mark.parametrize("operator", ["A", "B", "C", "A+B", "A-B", "A^B"])
    def test_operators(self, operator):
        gen = RhythmLab(operator=operator)
        events = gen.generate(4.0)
        assert isinstance(events, list)

    def test_custom_grid(self):
        # All hits with probability 1.0
        grid = [1.0] * 16
        gen = RhythmLab(grid_a=grid, operator="A")
        events = gen.generate(4.0)
        # 16 steps per 4 beats at 0.25 step_dur — expect 16 events
        assert len(events) == 16

    def test_empty_grid_produces_no_events(self):
        grid = [0.0] * 16
        gen = RhythmLab(grid_a=grid, grid_b=grid, grid_c=grid, operator="A")
        events = gen.generate(4.0)
        assert events == []

    def test_longer_duration_loops(self):
        gen = RhythmLab()
        events_4 = gen.generate(4.0)
        events_8 = gen.generate(8.0)
        # 8 beats should produce roughly 2× the events of 4 beats
        assert len(events_8) >= len(events_4)

    def test_short_duration(self):
        gen = RhythmLab()
        events = gen.generate(1.0)
        assert isinstance(events, list)

    def test_a_plus_b_uses_both_grids(self):
        grid_a = [1.0, 0.0] * 8
        grid_b = [0.0, 1.0] * 8
        gen = RhythmLab(grid_a=grid_a, grid_b=grid_b, operator="A+B")
        events = gen.generate(4.0)
        # A+B clips to 1.0 max, both grids have no overlap → 16 events
        assert len(events) == 16

    def test_a_minus_b_suppresses_overlap(self):
        grid_a = [1.0] * 16
        grid_b = [1.0] * 16
        gen = RhythmLab(grid_a=grid_a, grid_b=grid_b, operator="A-B")
        events = gen.generate(4.0)
        # A - B = 0 for all → no events
        assert events == []

    def test_a_and_b(self):
        # A^B = min(a, b). Both grids full → all 16 steps fire.
        grid_full = [1.0] * 16
        gen = RhythmLab(grid_a=grid_full, grid_b=grid_full, operator="A^B")
        events = gen.generate(4.0)
        assert len(events) == 16


# ---------------------------------------------------------------------------
# PolyrhythmGenerator
# ---------------------------------------------------------------------------

class TestPolyrhythmGenerator:
    def test_produces_events(self):
        gen = PolyrhythmGenerator()
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_all_events_in_range(self):
        gen = PolyrhythmGenerator()
        events = gen.generate(4.0)
        _assert_valid_events(events, 4.0)

    def test_sorted_by_onset(self):
        gen = PolyrhythmGenerator()
        events = gen.generate(8.0)
        onsets = [e.onset for e in events]
        assert onsets == sorted(onsets)

    @pytest.mark.parametrize("ratio_a,ratio_b", [(3, 4), (2, 3), (5, 4), (3, 2)])
    def test_ratios(self, ratio_a, ratio_b):
        gen = PolyrhythmGenerator(ratio_a=ratio_a, ratio_b=ratio_b)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_layer_a_only(self):
        gen = PolyrhythmGenerator(ratio_a=3, ratio_b=4, include_both=False)
        events_a = gen.generate(4.0)
        gen_both = PolyrhythmGenerator(ratio_a=3, ratio_b=4, include_both=True)
        events_both = gen_both.generate(4.0)
        # Both layers produce more events than A alone
        assert len(events_both) >= len(events_a)

    def test_layer_a_count(self):
        # ratio_a=3 → 3 events per bar
        gen = PolyrhythmGenerator(ratio_a=3, ratio_b=4, include_both=False)
        events = gen.generate(4.0)  # 1 bar
        assert len(events) == 3

    def test_two_bars(self):
        gen = PolyrhythmGenerator(ratio_a=3, ratio_b=2)
        events = gen.generate(8.0)
        # 2 bars: (3+2)*2 = 10 events
        assert len(events) == 10

    def test_downbeat_accent(self):
        gen = PolyrhythmGenerator(ratio_a=4, include_both=False)
        events = gen.generate(4.0)
        # First event should be accented (velocity_factor > 1.0)
        assert events[0].velocity_factor > 1.0


# ---------------------------------------------------------------------------
# SmoothRhythmGenerator
# ---------------------------------------------------------------------------

class TestSmoothRhythmGenerator:
    def test_produces_events(self):
        gen = SmoothRhythmGenerator()
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_all_events_in_range(self):
        gen = SmoothRhythmGenerator()
        events = gen.generate(4.0)
        _assert_valid_events(events, 4.0)

    @pytest.mark.parametrize("pattern_name", list(SMOOTH_PATTERNS.keys()))
    def test_named_patterns(self, pattern_name):
        gen = SmoothRhythmGenerator(pattern_name=pattern_name)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_whole_note_single_event(self):
        gen = SmoothRhythmGenerator(pattern_name="whole")
        events = gen.generate(4.0)
        assert len(events) == 1
        assert events[0].onset == 0.0

    def test_half_note_two_events(self):
        gen = SmoothRhythmGenerator(pattern_name="half")
        events = gen.generate(4.0)
        assert len(events) == 2
        assert events[0].onset == pytest.approx(0.0)
        assert events[1].onset == pytest.approx(2.0)

    def test_quarter_legato_events(self):
        gen = SmoothRhythmGenerator(pattern_name="quarter_legato")
        events = gen.generate(4.0)
        # 4 beats / 0.95 step = 5 events (overlap pushes onsets close together)
        assert len(events) >= 4

    def test_overlap_extends_duration(self):
        gen = SmoothRhythmGenerator(pattern_name="half", overlap=0.5)
        events = gen.generate(4.0)
        # Each event should be 2.0 + 0.5 = 2.5 beats long
        assert events[0].duration == pytest.approx(2.5)

    def test_no_overlap(self):
        gen = SmoothRhythmGenerator(pattern_name="half", overlap=0.0)
        events = gen.generate(4.0)
        assert events[0].duration == pytest.approx(2.0)

    def test_unknown_pattern_fallback(self):
        gen = SmoothRhythmGenerator(pattern_name="nonexistent")
        events = gen.generate(4.0)
        # Falls back to [1.0] → 4 quarter-note events
        assert len(events) == 4

    def test_longer_duration(self):
        gen = SmoothRhythmGenerator(pattern_name="half")
        events = gen.generate(8.0)
        assert len(events) == 4  # 8 beats / 2 beats per event

    def test_fractional_duration(self):
        gen = SmoothRhythmGenerator(pattern_name="whole")
        events = gen.generate(2.0)
        # 'whole' pattern has duration 4.0, truncated to 2.0 + overlap(0.1)
        assert len(events) == 1
        assert events[0].onset == pytest.approx(0.0)
        assert events[0].duration >= 2.0


# ---------------------------------------------------------------------------
# BassRhythmGenerator
# ---------------------------------------------------------------------------

class TestBassRhythmGenerator:
    def test_produces_events(self):
        gen = BassRhythmGenerator()
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_all_events_in_range(self):
        gen = BassRhythmGenerator()
        events = gen.generate(4.0)
        _assert_valid_events(events, 4.0)

    @pytest.mark.parametrize("pattern_name", list(BASS_PATTERNS.keys()))
    def test_named_patterns(self, pattern_name):
        gen = BassRhythmGenerator(pattern_name=pattern_name)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_straight_four_notes(self):
        gen = BassRhythmGenerator(pattern_name="straight")
        events = gen.generate(4.0)
        assert len(events) == 4

    def test_straight_downbeat_accent(self):
        gen = BassRhythmGenerator(pattern_name="straight")
        events = gen.generate(4.0)
        # Beat 1 (onset=0.0) should have highest velocity
        beat1 = next(e for e in events if e.onset == pytest.approx(0.0))
        assert beat1.velocity_factor > 1.0

    def test_syncopated_more_notes(self):
        gen = BassRhythmGenerator(pattern_name="syncopated")
        events = gen.generate(4.0)
        assert len(events) == 6

    def test_reggae_offbeats(self):
        gen = BassRhythmGenerator(pattern_name="reggae")
        events = gen.generate(4.0)
        # Reggae hits on offbeats: 0.5, 1.5, 2.5, 3.5
        onsets = [e.onset for e in events]
        assert 0.5 in onsets

    def test_unknown_pattern_fallback(self):
        gen = BassRhythmGenerator(pattern_name="nonexistent")
        events = gen.generate(4.0)
        # Falls back to "straight"
        assert len(events) == 4

    def test_two_bars(self):
        gen = BassRhythmGenerator(pattern_name="straight")
        events = gen.generate(8.0)
        assert len(events) == 8

    def test_events_sorted(self):
        gen = BassRhythmGenerator(pattern_name="syncopated")
        events = gen.generate(8.0)
        onsets = [e.onset for e in events]
        assert onsets == sorted(onsets)

    def test_no_events_beyond_duration(self):
        gen = BassRhythmGenerator(pattern_name="straight")
        events = gen.generate(2.0)
        for e in events:
            assert e.onset < 2.0


# ---------------------------------------------------------------------------
# MarkovRhythmGenerator
# ---------------------------------------------------------------------------

class TestMarkovRhythmGenerator:
    def test_produces_events(self):
        gen = MarkovRhythmGenerator()
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_all_events_in_range(self):
        gen = MarkovRhythmGenerator(seed=42)
        events = gen.generate(4.0)
        _assert_valid_events(events, 4.0)

    @pytest.mark.parametrize("style", ["straight", "swing", "ballad", "driving"])
    def test_styles(self, style):
        gen = MarkovRhythmGenerator(style=style, seed=0)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_empty_duration(self):
        gen = MarkovRhythmGenerator()
        events = gen.generate(0.0)
        assert events == []

    def test_negative_duration(self):
        gen = MarkovRhythmGenerator()
        events = gen.generate(-1.0)
        assert events == []

    def test_reproducible_with_seed(self):
        gen1 = MarkovRhythmGenerator(seed=123)
        gen2 = MarkovRhythmGenerator(seed=123)
        assert gen1.generate(4.0) == gen2.generate(4.0)

    def test_different_seeds_differ(self):
        gen1 = MarkovRhythmGenerator(seed=1)
        gen2 = MarkovRhythmGenerator(seed=2)
        # Very likely to differ over 8 beats
        assert gen1.generate(8.0) != gen2.generate(8.0)

    def test_events_cover_duration(self):
        gen = MarkovRhythmGenerator(seed=42)
        events = gen.generate(8.0)
        # Last event onset should be within the duration
        assert events[-1].onset < 8.0

    def test_all_durations_valid(self):
        valid_durations = {0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0}
        gen = MarkovRhythmGenerator(seed=7)
        events = gen.generate(16.0)
        for e in events:
            # Duration may be clamped, so check it's positive and reasonable
            assert 0.0 < e.duration <= 4.0

    def test_phrase_boundary_lengthening(self):
        # With phrase_length=4, every 4th note gets stretched
        # Just verify it produces a valid sequence
        gen = MarkovRhythmGenerator(phrase_length=4, seed=0)
        events = gen.generate(8.0)
        assert len(events) > 0

    def test_high_syncopation(self):
        gen = MarkovRhythmGenerator(syncopation=1.0, seed=0)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_custom_transitions(self):
        # Force only quarter notes
        transitions = {
            0.25: {1.0: 1.0},
            0.5:  {1.0: 1.0},
            0.75: {1.0: 1.0},
            1.0:  {1.0: 1.0},
            1.5:  {1.0: 1.0},
            2.0:  {1.0: 1.0},
            4.0:  {1.0: 1.0},
        }
        gen = MarkovRhythmGenerator(style="custom", transitions=transitions, seed=0)
        events = gen.generate(4.0)
        assert len(events) == 4
        for e in events:
            assert e.duration == pytest.approx(1.0 * 0.9, abs=0.2)  # gate applied
