#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scratch/verify_solo_melody.py — Validation script for all 9 styles in SoloMelodyGenerator.
"""

import sys
import os

# Add the workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators import GeneratorParams
from melodica.types import ChordLabel, Scale, Mode, Quality

ALL_SOLO_STYLES = [
    "blues_lick", "shred_guitar", "jazz_fusion", "space_synth",
    "neo_soul_keys", "vocal_mimic", "cinematic_strings", "bebop_horn",
    "modal_ambient"
]


def run_tests():
    print("=" * 80)
    print("         VERIFYING ALL 9 EXPRESSIVE SOLO MELODY GENERATOR STYLES")
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
            has_cutoff = any(74 in n.expression for n in notes)
            assert has_cutoff, "Space synth style should generate CC 74 expressions!"
        elif style == "blues_lick":
            has_vibrato = any(1 in n.expression for n in notes if n.duration > 0.6)
            assert has_vibrato, "Blues lick style should generate CC 1 vibrato on sustained notes!"
        elif style == "neo_soul_keys":
            # Must generate backing chord stabs (multiple notes sharing same start onset)
            starts = [n.start for n in notes]
            has_stabs = len(starts) > len(set(starts))
            assert has_stabs, "Neo-Soul Keys style should generate chord stabs (overlapping notes)!"
        elif style == "vocal_mimic":
            # Must generate melisma grace notes (notes with very short duration, e.g., 0.07 beats)
            has_melisma = any(abs(n.duration - 0.07) < 0.01 for n in notes)
            assert has_melisma, "Vocal Mimic style should generate rapid melisma grace notes!"
        elif style == "cinematic_strings":
            # Must generate sweeping tremolo on CC 1
            has_tremolo = any(1 in n.expression for n in notes)
            assert has_tremolo, "Cinematic Strings style should generate tremolo on CC 1!"
        elif style == "modal_ambient":
            # Must generate detune fine-tuning values on CC 98
            has_detune = any(98 in n.expression for n in notes)
            assert has_detune, "Modal Ambient style should generate analog detune LFOs on CC 98!"

        print(f"   ✓ Style '{style}' PASSED dynamic register and expressive modulation validation!")
        passed_count += 1

    print("\n" + "=" * 80)
    print(f" SUCCESS: ALL {passed_count}/{len(ALL_SOLO_STYLES)} SOLO MELODY STYLES VALIDATED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
