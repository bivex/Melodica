# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, parse_progression
from melodica.generators.lorn_hook import LornHookGenerator


def test_lorn_hook_generator():
    key = Scale(root=0, mode=Mode.PHRYGIAN)
    chords = parse_progression("i:4 VI:4 iv:4 v:4", key)
    
    gen = LornHookGenerator(hook_length=5, octave=5, seed=42)
    notes = gen.render(chords, key, 16.0)  # 4 bars in 4/4
    
    # Check that we have generated some notes
    assert len(notes) > 0
    
    # Check that hook pitch range is within Lorn's range
    pitches = [n.pitch for n in notes]
    pitch_range = max(pitches) - min(pitches)
    assert pitch_range <= 16
    
    # Evaluate hook quality metrics
    diag = gen.evaluate_hook_quality(notes, pitches)
    assert diag["unique_notes"] <= 5
    assert diag["is_memorable"] is True
