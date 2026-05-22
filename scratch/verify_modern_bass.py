#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
scratch/verify_modern_bass.py — Test suite and metric validator for ModernBass2025Generator.
"""

import sys
import os

# Add the workspace root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators import GeneratorParams
from melodica.types import ChordLabel, Scale, Mode, Quality


def run_tests():
    print("=" * 60)
    print("VERIFYING MODERN BASS 2025 GENERATORS")
    print("=" * 60)

    # 1. Setup sample key/chords
    key = Scale(root=0, mode=Mode.MAJOR)  # C Major
    chords = [
        ChordLabel(start=0.0, duration=4.0, root=0, quality=Quality.MAJOR, degree=1),  # C Major
        ChordLabel(start=4.0, duration=4.0, root=5, quality=Quality.MAJOR, degree=4),  # F Major
        ChordLabel(start=8.0, duration=4.0, root=7, quality=Quality.MAJOR, degree=5),  # G Major
        ChordLabel(start=12.0, duration=4.0, root=9, quality=Quality.MINOR, degree=6),  # A Minor
    ]
    duration_beats = 16.0

    params = GeneratorParams(
        density=0.7,
        key_range_low=36,
        key_range_high=72,
    )

    # 2. Test Velvet Soul style
    print("\n--- Test 1: Velvet Soul style ---")
    gen_velvet = ModernBass2025Generator(params, style="velvet_soul")
    notes_velvet = gen_velvet.render(chords, key, duration_beats)
    
    assert len(notes_velvet) > 0, "No notes generated for velvet_soul!"
    vels = [n.velocity for n in notes_velvet]
    avg_vel = sum(vels) / len(vels)
    max_vel = max(vels)
    min_vel = min(vels)
    
    print(f"Notes Count: {len(notes_velvet)}")
    print(f"Velocities - Min: {min_vel}, Max: {max_vel}, Avg: {avg_vel:.2f}")
    print(f"Target metrics - Expected Max: 84, Expected Avg: ~63.0")
    
    # Assertions
    assert max_vel == 84, f"Velvet Soul max velocity should be exactly 84, got {max_vel}"
    assert abs(avg_vel - 63.0) < 0.2, f"Velvet Soul avg velocity should be around 63, got {avg_vel:.2f}"
    print("✓ Velvet Soul velocity bounds validation PASSED!")

    # 3. Test Hybrid Slap style
    print("\n--- Test 2: Hybrid Slap style ---")
    gen_slap = ModernBass2025Generator(params, style="hybrid_slap")
    notes_slap = gen_slap.render(chords, key, duration_beats)
    
    assert len(notes_slap) > 0, "No notes generated for hybrid_slap!"
    vels_slap = [n.velocity for n in notes_slap]
    avg_slap = sum(vels_slap) / len(vels_slap)
    max_slap = max(vels_slap)
    min_slap = min(vels_slap)
    
    articulations = set(n.articulation for n in notes_slap)
    
    print(f"Notes Count: {len(notes_slap)}")
    print(f"Velocities - Min: {min_slap}, Max: {max_slap}, Avg: {avg_slap:.2f}")
    print(f"Articulations present: {articulations}")
    print(f"Target metrics - Expected Max: 92, Expected Avg: ~59.0")
    
    # Assertions
    assert max_slap == 92, f"Hybrid Slap max velocity should be exactly 92, got {max_slap}"
    assert abs(avg_slap - 59.0) < 0.2, f"Hybrid Slap avg velocity should be around 59, got {avg_slap:.2f}"
    assert "slap" in articulations or "pop" in articulations, "Slap/pop articulations missing!"
    print("✓ Hybrid Slap velocity bounds and articulation validation PASSED!")

    # 4. Test Analog Pluck style
    print("\n--- Test 3: Analog Pluck style ---")
    gen_pluck = ModernBass2025Generator(params, style="analog_pluck")
    notes_pluck = gen_pluck.render(chords, key, duration_beats)
    
    assert len(notes_pluck) > 0, "No notes generated for analog_pluck!"
    vels_pluck = [n.velocity for n in notes_pluck]
    avg_pluck = sum(vels_pluck) / len(vels_pluck)
    max_pluck = max(vels_pluck)
    min_pluck = min(vels_pluck)
    
    durations = [n.duration for n in notes_pluck]
    max_dur = max(durations)
    
    print(f"Notes Count: {len(notes_pluck)}")
    print(f"Velocities - Min: {min_pluck}, Max: {max_pluck}, Avg: {avg_pluck:.2f}")
    print(f"Durations - Max note duration: {max_dur}")
    print(f"Target metrics - Expected Max: 84, Expected Avg: ~63.0, Short decay (< 0.25)")
    
    # Assertions
    assert max_pluck == 84, f"Analog Pluck max velocity should be exactly 84, got {max_pluck}"
    assert abs(avg_pluck - 63.0) < 0.2, f"Analog Pluck avg velocity should be around 63, got {avg_pluck:.2f}"
    assert max_dur <= 0.25, f"Analog Pluck durations should be short (<= 0.25), got {max_dur}"
    print("✓ Analog Pluck velocity bounds and pluck decay validation PASSED!")

    # 5. Test Crescendo Return style
    print("\n--- Test 4: Crescendo Return style ---")
    gen_crescendo = ModernBass2025Generator(params, style="crescendo_return")
    notes_crescendo = gen_crescendo.render(chords, key, duration_beats)
    
    assert len(notes_crescendo) > 0, "No notes generated for crescendo_return!"
    vels_crescendo = [n.velocity for n in notes_crescendo]
    
    print(f"Notes Count: {len(notes_crescendo)}")
    print(f"Start Velocity: {vels_crescendo[0]}, Peak Velocity: {vels_crescendo[-1]}")
    print(f"Expression sweeps on CC 74 (LPF):")
    for idx, n in enumerate(notes_crescendo[:3] + notes_crescendo[-3:]):
        label = "Start Note" if idx < 3 else "End Note"
        print(f"  [{label}] onset: {n.start:.2f}, velocity: {n.velocity}, CC 74: {n.expression.get(74)}")
    
    # Assertions
    assert vels_crescendo[0] == 31, f"Crescendo should start at velocity 31, got {vels_crescendo[0]}"
    assert vels_crescendo[-1] == 68, f"Crescendo should peak at velocity 68, got {vels_crescendo[-1]}"
    assert notes_crescendo[0].expression[74] < notes_crescendo[-1].expression[74], "LPF sweep is not opening up!"
    print("✓ Crescendo Return dynamic ramp and expression sweeps validation PASSED!")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
