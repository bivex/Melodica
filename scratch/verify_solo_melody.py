#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scratch/verify_solo_melody.py — Validation script for all styles in SoloMelodyGenerator.
"""

import sys
import os

# Add the workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators import GeneratorParams
from melodica.types import ChordLabel, Scale, Mode, Quality

ALL_SOLO_STYLES = ["blues_lick", "shred_guitar", "jazz_fusion", "space_synth"]


def run_tests():
    print("=" * 80)
    print("         VERIFYING EXPRESSIVE SOLO MELODY GENERATOR STYLES")
    print("=" * 80)

    # Setup sample key/chords
    key = Scale(root=0, mode=Mode.AEOLIAN)  # C Aeolian
    chords = [
        ChordLabel(start=0.0, duration=4.0, root=0, quality=Quality.MINOR, degree=1),
        ChordLabel(start=4.0, duration=4.0, root=8, quality=Quality.MAJOR, degree=6),
        ChordLabel(start=8.0, duration=4.0, root=5, quality=Quality.MINOR, degree=4),
        ChordLabel(start=12.0, duration=4.0, root=7, quality=Quality.MINOR, degree=5),
    ]
    duration_beats = 16.0

    params = GeneratorParams(
        density=0.7,
        key_range_low=48,
        key_range_high=88,
    )

    passed_count = 0

    for style in ALL_SOLO_STYLES:
        print(f"\n⚡ Testing style: '{style}'...")
        gen = SoloMelodyGenerator(params, style=style, vibrato_depth=0.8)
        notes = gen.render(chords, key, duration_beats)
        
        # 1. Base assertions
        assert len(notes) > 0, f"Error: No notes generated for style '{style}'!"
        
        vels = [n.velocity for n in notes]
        avg_vel = sum(vels) / len(vels)
        max_vel = max(vels)
        min_vel = min(vels)
        
        print(f"   Notes Count: {len(notes)}")
        print(f"   Velocities  — Min: {min_vel}, Max: {max_vel}, Avg: {avg_vel:.2f}")
        
        # Check range bounds
        for n in notes:
            assert 48 <= n.pitch <= 88, f"[{style}] Note pitch {n.pitch} out of bounds (48-88)!"

        # Style-specific checks
        if style == "space_synth":
            # Must contain CC 74 sweeping filter
            has_cutoff = any(74 in n.expression for n in notes)
            assert has_cutoff, "Space synth style should generate CC 74 expressions!"
        elif style == "blues_lick":
            # Must contain CC 1 vibrato on sustained notes
            has_vibrato = any(1 in n.expression for n in notes if n.duration > 0.6)
            assert has_vibrato, "Blues lick style should generate CC 1 vibrato on sustained notes!"

        print(f"   ✓ Style '{style}' PASSED dynamic register and expressive modulation validation!")
        passed_count += 1

    print("\n" + "=" * 80)
    print(f" SUCCESS: ALL {passed_count}/{len(ALL_SOLO_STYLES)} SOLO MELODY STYLES VALIDATED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
