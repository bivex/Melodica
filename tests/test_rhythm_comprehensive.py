import pytest
import math
from melodica.rhythm import (
    EuclideanRhythmGenerator,
    ProbabilisticRhythmGenerator,
    SubdivisionGenerator,
    RhythmEvent
)
from melodica.rhythm.schillinger import SchillingerGenerator
from melodica.rhythm.motif import MotifRhythmGenerator
from melodica.rhythm.library import get_rhythm, StaticRhythmGenerator

class TestSchillingerRhythm:
    def test_basic_3_4(self):
        # 3 vs 4 pattern. Pattern length is LCM(3, 4) = 12 units.
        # With units_per_beat=4, this is 3 beats.
        gen = SchillingerGenerator(a=3, b=4, units_per_beat=4)
        events = gen.generate(3.0)
        
        # Onsets: 0, 3, 4, 6, 8, 9 (and 12 is end)
        assert len(events) == 6
        assert events[0].onset == 0.0
        assert events[1].onset == 0.75 # 3/4
        assert events[2].onset == 1.0  # 4/4
        assert events[3].onset == 1.5  # 6/4
        assert events[4].onset == 2.0  # 8/4
        assert events[5].onset == 2.25 # 9/4

    def test_identical_numbers(self):
        # 4 vs 4 should just be straight 4/4 (every 4 units)
        gen = SchillingerGenerator(a=4, b=4, units_per_beat=4)
        events = gen.generate(4.0)
        # Onsets: 0, 4, 8, 12 ... 
        # Every 4 units = 1 beat. 
        assert len(events) == 4
        for i, ev in enumerate(events):
            assert ev.onset == float(i)

    def test_large_numbers_lcm(self):
        # 2 vs 5. LCM = 10. Pattern: 0, 2, 4, 5, 6, 8, 10
        gen = SchillingerGenerator(a=2, b=5, units_per_beat=4)
        events = gen.generate(2.5) # 10 units = 2.5 beats
        assert len(events) == 6
        assert events[5].onset == 2.0 # 8/4

class TestMotifRhythm:
    def test_looping_behavior(self):
        # Inner: hit at 0.0 and 0.5 in a 1.0 motif
        # Disable internal looping of StaticRhythmGenerator so MotifRhythmGenerator handles it.
        inner = StaticRhythmGenerator(events=[RhythmEvent(0.0, 0.2), RhythmEvent(0.5, 0.2)], loop=False)
        motif = MotifRhythmGenerator(inner, motif_length=1.0)
        
        # Generate 4.0 beats (should have 2 hits per beat * 4 beats = 8 hits)
        events = motif.generate(4.0)
        assert len(events) == 8
        onsets = [e.onset for e in events]
        assert 0.0 in onsets
        assert 0.5 in onsets
        assert 1.0 in onsets
        assert 3.5 in onsets

    def test_truncation_at_motif_boundary(self):
        # Inner: hit at 0.0 with 2.0 duration in a 1.0 motif
        inner = StaticRhythmGenerator(events=[RhythmEvent(0.0, 2.0)], loop=False)
        motif = MotifRhythmGenerator(inner, motif_length=1.0)
        
        events = motif.generate(3.0)
        assert len(events) == 3
        # Every note must be exactly 1.0 long due to motif boundary truncation
        for e in events:
            assert e.duration == 1.0

class TestRhythmLibrary:
    def test_get_valid_rhythm(self):
        gen = get_rhythm("straight_8_triplets")
        events = gen.generate(1.0)
        assert len(events) == 3

    def test_fallback_rhythm(self):
        # Should fallback to straight quarters for unknown name
        gen = get_rhythm("non_existent_preset_name_123")
        events = gen.generate(1.0)
        assert len(events) == 1
        assert events[0].onset == 0.0

class TestEuclideanEdgeCases:
    def test_max_hits(self):
        # hits >= slots means every slot is hit
        gen = EuclideanRhythmGenerator(hits_per_bar=20, slots_per_beat=4)
        # default bar is 4 beats = 16 slots.
        events = gen.generate(4.0)
        assert len(events) == 16

    def test_one_hit_per_bar(self):
        gen = EuclideanRhythmGenerator(hits_per_bar=1, slots_per_beat=4)
        events = gen.generate(8.0) # 2 bars
        assert len(events) == 2
        assert events[0].onset == 0.0
        assert events[1].onset == 4.0

class TestSubdivisionAdvanced:
    def test_tie_across_multi_beats(self):
        # 100% tie chance with 1 div/beat
        gen = SubdivisionGenerator(divisions_per_beat=1, skip_chance=0.0, tie_chance=1.0)
        events = gen.generate(4.0)
        assert len(events) == 1
        # 4.0 beats x 0.95 gate
        assert events[0].duration == pytest.approx(3.8)

    def test_alternating_skips(self):
        # Hard to test random, but we can verify seed or logic
        import random
        random.seed(42)
        gen = SubdivisionGenerator(divisions_per_beat=4, skip_chance=0.5)
        events = gen.generate(4.0)
        # Should have roughly 8 events (out of 16 slots)
        assert 0 < len(events) < 16

class TestProbabilisticAdvanced:
    def test_high_density_downbeats(self):
        """
        Verify that with 0 density but high downbeat weight, 
        notes only occur on downbeats? No, prob = density * (1+weight).
        So if density is 0, prob is always 0. 
        But if density is 1.0, prob is 1.0. 
        Let's test if density=1.0 gives a hit on every slot.
        """
        gen = ProbabilisticRhythmGenerator(density=1.0, grid_resolution=0.25)
        events = gen.generate(4.0)
        assert len(events) == 16
        
    def test_zero_density(self):
        gen = ProbabilisticRhythmGenerator(density=0.0)
        events = gen.generate(4.0)
        assert len(events) == 0

    def test_downbeat_weight_logic(self):
        """
        Test that downbeat_weight increases probability on beats 0, 1, 2, 3.
        We'll use a seed to make it deterministic.
        """
        import random
        random.seed(1337)
        # Low density but high downbeat weight
        gen = ProbabilisticRhythmGenerator(density=0.2, downbeat_weight=4.0, grid_resolution=1.0)
        # Prob for downbeat = 0.2 * (1 + 4) = 1.0
        events = gen.generate(4.0)
        # Should have exactly 4 events (one on each quarter beat)
        assert len(events) == 4
        assert [e.onset for e in events] == [0.0, 1.0, 2.0, 3.0]

    def test_syncopation_logic(self):
        """
        Syncopation adds weight to offbeats.
        Offbeats are slots like 0.25, 0.75, etc.
        """
        import random
        random.seed(12345)
        # Density 0.1. Offbeat prob = 0.1 * (0.5 + syncopation)
        # If syncopation = 9.5, prob = 0.1 * (10.0) = 1.0
        gen = ProbabilisticRhythmGenerator(density=0.1, syncopation=9.5, grid_resolution=0.25)
        events = gen.generate(1.0) # 4 slots
        # onsets: 0.0(down), 0.25(off), 0.5(up), 0.75(off)
        # offbeats are 0.25 and 0.75. 
        # prob(down) = 0.1 * 1.3 = 0.13
        # prob(up) = 0.1 * 0.8 = 0.08
        # prob(off) = 1.0
        
        # We expect hits on 0.25 and 0.75 for sure. 
        # Others depend on randomness but with seed 12345:
        onsets = [e.onset for e in events]
        assert 0.25 in onsets
        assert 0.75 in onsets
