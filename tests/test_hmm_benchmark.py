# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_hmm_benchmark.py — Comprehensive HMM 3.0 vs 4.0 Benchmark.

This test suite runs both harmonization engines against a wide variety of modes
and generates a report showing the harmonic logic, cadential resolution, and
stylistic fit for each.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from melodica import types
from melodica.harmonize.advanced import HMM3Harmonizer, HMM4Harmonizer
from melodica.types import NoteInfo, Scale, Mode

def generate_test_melody(scale: Scale, length_beats: float = 16.0) -> list[NoteInfo]:
    """Generates a simple ascending/descending scale-based melody for testing."""
    notes = []
    degrees = scale.degrees()
    for b in range(int(length_beats)):
        # 1. Strong beat (root or fifth)
        pc = degrees[0] if b % 4 == 0 else degrees[b % len(degrees)]
        notes.append(NoteInfo(pitch=60 + pc, start=float(b), duration=1.0, velocity=80))
    return notes

def benchmark_mode(mode: Mode, style: str = "cinematic"):
    """Run benchmark for a specific mode."""
    root = 0 # C
    scale = Scale(root=root, mode=mode)
    melody = generate_test_melody(scale)
    duration = 16.0
    
    print(f"\n[BENCHMARK] Mode: {mode.value} | Style: {style}")
    print("-" * 60)
    
    # HMM 3.0
    hmm3 = HMM3Harmonizer(beam_width=5)
    chords3 = hmm3.harmonize(melody, scale, duration)
    
    # HMM 4.0
    hmm4 = HMM4Harmonizer(beam_width=8, style=style)
    chords4 = hmm4.harmonize(melody, scale, duration)
    
    def fmt_chords(chords):
        return " -> ".join([f"{c.root}{str(c.quality.value)[:3]} ({int(c.degree)})" for c in chords[:8]])
    
    print(f" HMM 3.0: {fmt_chords(chords3)}")
    print(f" HMM 4.0: {fmt_chords(chords4)}")
    
    # Analysis: check for common patterns
    def analyze(chords):
        degs = [c.degree for c in chords]
        # Check for ii-V-I or similar
        cadences = 0
        for i in range(len(degs)-2):
            # 2nd order patterns
            if degs[i:i+3] == [2, 5, 1] or degs[i:i+3] == [4, 5, 1]:
                cadences += 1
            if degs[i:i+3] == [6, 2, 5]: # Predominant chain
                cadences += 1
        return cadences

    c3 = analyze(chords3)
    c4 = analyze(chords4)
    print(f" Logical Chains Detected: HMM3={c3}, HMM4={c4}")

def main():
    test_modes = [
        Mode.MAJOR,
        Mode.NATURAL_MINOR,
        Mode.DORIAN,
        Mode.PHRYGIAN,
        Mode.HIROJOSHI, # Japanese
        Mode.BYZANTINE, # Exotic
        Mode.HUNGARIAN_MINOR, # Gothic
        Mode.MESSIAEN_2, # Diminished
    ]
    
    for m in test_modes:
        benchmark_mode(m, style="cinematic")
        benchmark_mode(m, style="academic")

if __name__ == "__main__":
    main()
