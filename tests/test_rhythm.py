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

import pytest

from melodica.rhythm import (
    EuclideanRhythmGenerator,
    ProbabilisticRhythmGenerator,
    SubdivisionGenerator,
)


def test_euclidean_generator_basic():
    # E(5, 16) over 4 beats with 4 slots/beat -> 5 events
    gen = EuclideanRhythmGenerator(slots_per_beat=4, hits_per_bar=5)
    events = gen.generate(duration_beats=4.0)
    
    assert len(events) == 5
    # The sum of slots is 16. In E(5, 16), patterns are formed like 100 100 100 100 1000
    # Let's just check the onsets are monotonically increasing
    for i in range(4):
        assert events[i].onset < events[i+1].onset
        
    onsets = [e.onset for e in events]
    assert 0.0 in onsets


def test_euclidean_generator_empty_and_full():
    gen_empty = EuclideanRhythmGenerator(hits_per_bar=0)
    assert len(gen_empty.generate(4.0)) == 0
    
    gen_full = EuclideanRhythmGenerator(hits_per_bar=16, slots_per_beat=4)
    # 16 hits over 16 slots -> every slot is a hit
    events = gen_full.generate(4.0)
    assert len(events) == 16
    assert events[0].onset == 0.0
    assert events[1].onset == 0.25


def test_euclidean_generator_offset():
    gen = EuclideanRhythmGenerator(hits_per_bar=1, slots_per_beat=4, offset=1)
    # The only hit should be shifted to the second slot
    events = gen.generate(1.0) # 1 beat = 4 slots
    assert len(events) == 1
    # Without offset it's slot 0. With offset 1, it's rotated right?
    # Actually wait - E(1,4) is [1, 0, 0, 0]. Rotated offset: pattern [-1:] + pattern [:-1] -> [0, 1, 0, 0]
    assert events[0].onset == 0.25


def test_probabilistic_generator():
    # Density 1.0 means every slot should hit
    gen_full = ProbabilisticRhythmGenerator(grid_resolution=0.25, density=1.0)
    events = gen_full.generate(1.0)
    assert len(events) == 4
    for i, ev in enumerate(events):
        assert ev.onset == i * 0.25
        
    # Density 0.0 means no slots should hit
    gen_empty = ProbabilisticRhythmGenerator(grid_resolution=0.25, density=0.0)
    assert len(gen_empty.generate(1.0)) == 0


def test_subdivision_generator():
    # Straight quarter notes
    gen = SubdivisionGenerator(divisions_per_beat=1, skip_chance=0.0, tie_chance=0.0)
    events = gen.generate(duration_beats=4.0)
    assert len(events) == 4
    assert events[0].duration == 0.95  # due to 0.95 gate
    assert events[0].onset == 0.0
    assert events[1].onset == 1.0
    
    # Empty generator
    assert len(gen.generate(0.0)) == 0


def test_subdivision_generator_ties_and_skips():
    # With 100% skip chance, 0 events
    gen_skip = SubdivisionGenerator(divisions_per_beat=2, skip_chance=1.0)
    assert len(gen_skip.generate(4.0)) == 0
    
    # With 100% tie chance, it should tie into a single large note
    gen_tie = SubdivisionGenerator(divisions_per_beat=4, skip_chance=0.0, tie_chance=1.0)
    events = gen_tie.generate(2.0)
    # Wait, the first division starts the note. The remaining 7 divisions tie.
    # We should get exactly 1 event
    assert len(events) == 1
    assert events[0].onset == 0.0
    assert events[0].duration == pytest.approx(2.0 * 0.95)
