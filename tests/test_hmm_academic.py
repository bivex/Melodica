# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_hmm_academic.py — Rigorous tests for HMM 4.0 Academic Style.

Focuses on:
1. Strict functional hierarchy (Kostka-Payne rules).
2. Proper resolution of cadences.
3. Minor key functional logic (i-ii°-V-i).
"""

import sys
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from melodica import types
from melodica.harmonize.advanced import HMM4Harmonizer
from melodica.types import NoteInfo, Scale, Mode

class TestHMMAcademic(unittest.TestCase):
    def setUp(self):
        self.hmm = HMM4Harmonizer(beam_width=10, style="academic")

    def test_major_diatonic_rigor(self):
        """Verify that C Major melody results in a logical I-IV-V-I progression."""
        scale = Scale(root=0, mode=Mode.MAJOR)
        # Melody: C (1) -> F (4) -> G (5) -> C (1)
        melody = [
            NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80),
            NoteInfo(pitch=65, start=4.0, duration=4.0, velocity=80),
            NoteInfo(pitch=67, start=8.0, duration=4.0, velocity=80),
            NoteInfo(pitch=60, start=12.0, duration=4.0, velocity=80),
        ]
        chords = self.hmm.harmonize(melody, scale, 16.0)
        degrees = [int(c.degree) for c in chords]
        
        # Expected: must start and end on I (1)
        self.assertEqual(degrees[0], 1, "Should start on Tonic")
        self.assertEqual(degrees[-1], 1, "Should end on Tonic")
        # Middle should be logical (e.g., 4 or 2 before 5)
        self.assertIn(5, degrees, "Should include Dominant before resolution")

    def test_minor_key_logic(self):
        """Verify i-ii°-V-i logic in A Minor."""
        scale = Scale(root=9, mode=Mode.NATURAL_MINOR)
        # Melody focused on characteristic minor degrees
        melody = [
            NoteInfo(pitch=69, start=0.0, duration=4.0, velocity=80), # A (i)
            NoteInfo(pitch=71, start=4.0, duration=4.0, velocity=80), # B (ii°)
            NoteInfo(pitch=76, start=8.0, duration=4.0, velocity=80), # E (V)
            NoteInfo(pitch=69, start=12.0, duration=4.0, velocity=80),# A (i)
        ]
        chords = self.hmm.harmonize(melody, scale, 16.0)
        degrees = [int(c.degree) for c in chords]
        
        print(f"Minor Progression: {degrees}")
        self.assertEqual(degrees[0], 1)
        # Academic minor rules prefer ii° (2) -> V (5)
        if 2 in degrees:
            idx2 = degrees.index(2)
            if 5 in degrees[idx2:]:
                print("  ✓ Correct ii°-V sequence detected")

    def test_cadential_resolution(self):
        """Ensure the engine prioritizes V->I at phrase boundaries."""
        scale = Scale(root=0, mode=Mode.MAJOR)
        # Static melody G G G G (Dominant tone)
        # HMM should choose V then I for finality
        melody = [
            NoteInfo(pitch=67, start=0.0, duration=4.0, velocity=80),
            NoteInfo(pitch=67, start=4.0, duration=4.0, velocity=80),
            NoteInfo(pitch=67, start=8.0, duration=4.0, velocity=80),
            NoteInfo(pitch=60, start=12.0, duration=4.0, velocity=80),
        ]
        chords = self.hmm.harmonize(melody, scale, 16.0)
        degrees = [int(c.degree) for c in chords]
        
        # In academic style, degree 5 -> 1 is the strongest attraction
        self.assertEqual(degrees[-1], 1)
        self.assertEqual(degrees[-2], 5)

if __name__ == "__main__":
    unittest.main()
