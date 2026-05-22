#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scratch/verify_modern_bass.py — Detailed validation script for all 20 styles in ModernBass2025Generator.
"""

import sys
import os

# Add the workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators import GeneratorParams
from melodica.types import ChordLabel, Scale, Mode, Quality

ALL_20_STYLES = [
    "walking", "slap", "pop", "ghost_note", "synth", 
    "saw", "sub", "hybrid_slap", "fingerstyle", "adaptive",
    "procedural", "generative", "euclidean", "spectral_morphing",
    "sidechain_reactive", "self_modifying", "cinematic", "tape",
    "harmonic", "envelope"
]


def run_tests():
    print("=" * 80)
    print("        VERIFYING ALL 20 ADVANCED MODERN BASS STYLES (2025 MODEL)")
    print("=" * 80)

    # Setup sample key/chords
    key = Scale(root=7, mode=Mode.DORIAN)  # G Dorian
    chords = [
        ChordLabel(start=0.0, duration=4.0, root=7, quality=Quality.MINOR, degree=1),
        ChordLabel(start=4.0, duration=4.0, root=0, quality=Quality.MINOR, degree=4),
        ChordLabel(start=8.0, duration=4.0, root=10, quality=Quality.MAJOR, degree=7),
        ChordLabel(start=12.0, duration=4.0, root=5, quality=Quality.MINOR, degree=5),
    ]
    duration_beats = 16.0

    params = GeneratorParams(
        density=0.7,
        key_range_low=24,
        key_range_high=84,
    )

    passed_count = 0

    for style in ALL_20_STYLES:
        print(f"\n⚡ Testing style: '{style}'...")
        gen = ModernBass2025Generator(params, style=style)
        notes = gen.render(chords, key, duration_beats)
        
        # 1. Base assertions
        assert len(notes) > 0, f"Error: No notes generated for style '{style}'!"
        
        vels = [n.velocity for n in notes]
        avg_vel = sum(vels) / len(vels)
        max_vel = max(vels)
        min_vel = min(vels)
        
        print(f"   Notes Count: {len(notes)}")
        print(f"   Velocities  — Min: {min_vel}, Max: {max_vel}, Avg: {avg_vel:.2f}")
        
        # Style presets definitions for confirmation matching
        target_avg = 63.0
        target_max = 84.0
        if style == "walking":
            target_avg, target_max = 68.0, 88.0
        elif style == "slap":
            target_avg, target_max = 64.0, 95.0
        elif style == "pop":
            target_avg, target_max = 68.0, 90.0
        elif style == "ghost_note":
            target_avg, target_max = 42.0, 75.0
        elif style == "synth":
            target_avg, target_max = 64.0, 85.0
        elif style == "saw":
            target_avg, target_max = 75.0, 98.0
        elif style == "sub":
            target_avg, target_max = 58.0, 78.0
        elif style == "hybrid_slap":
            target_avg, target_max = 59.0, 92.0
        elif style == "fingerstyle":
            target_avg, target_max = 63.0, 84.0
        elif style == "adaptive":
            target_avg, target_max = 65.0, 88.0
        elif style == "procedural":
            target_avg, target_max = 63.0, 85.0
        elif style == "generative":
            target_avg, target_max = 64.0, 86.0
        elif style == "euclidean":
            target_avg, target_max = 65.0, 88.0
        elif style == "spectral_morphing":
            target_avg, target_max = 63.0, 84.0
        elif style == "sidechain_reactive":
            target_avg, target_max = 60.0, 84.0
        elif style == "self_modifying":
            target_avg, target_max = 66.0, 90.0
        elif style == "cinematic":
            target_avg, target_max = 60.0, 82.0
        elif style == "tape":
            target_avg, target_max = 62.0, 82.0
        elif style == "harmonic":
            target_avg, target_max = 68.0, 92.0
        elif style == "envelope":
            target_avg, target_max = 63.0, 85.0

        # Assert max velocity is exactly locked
        assert max_vel == int(target_max), f"[{style}] Expected max velocity {target_max}, got {max_vel}"
        # Assert average velocity is extremely close (clamping offset threshold)
        assert abs(avg_vel - target_avg) < 0.2, f"[{style}] Expected average velocity {target_avg}, got {avg_vel:.2f}"
        
        # Style specific validation checks
        if style == "sub":
            # Low register only
            for n in notes:
                assert n.pitch <= 38, f"Sub bass note pitch too high: {n.pitch}"
        elif style == "sidechain_reactive":
            # Sidechain reaction
            for n in notes:
                assert 7 in n.expression, f"Sidechain volume controller (CC 7) missing from note!"
        elif style == "spectral_morphing":
            # Spectral sweep modulation
            for n in notes:
                assert 74 in n.expression, f"Cutoff controller (CC 74) missing from spectral note!"

        print(f"   ✓ Style '{style}' PASSED dynamic bounds and constraint validation!")
        passed_count += 1

    print("\n" + "=" * 80)
    print(f" SUCCESS: ALL {passed_count}/{len(ALL_20_STYLES)} MODERN BASS STYLES VALIDATED!")
    print("=" * 80)


if __name__ == "__main__":
    run_tests()
