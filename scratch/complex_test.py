
import sys
import os

sys.path.append("/Volumes/External/Code/Melodica")

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.types import NoteInfo, Scale, Mode, BarGrid, Quality
from melodica.composer.harmonic_awareness import pitch_class_weights

def analyze_complex_harmony():
    # TEST MELODY: "The Jazz-ish Turn"
    # Bar 1: Plain C Major
    # Bar 2: Intro of Bb (Mixolydian/Dominant hint)
    # Bar 3: F# (Secondary Dominant D7 hint)
    # Bar 4: Return to G
    melody = [
        # Bar 1 (0-4)
        NoteInfo(pitch=60, start=0.0, duration=1.0), # C
        NoteInfo(pitch=64, start=1.0, duration=1.0), # E
        NoteInfo(pitch=67, start=2.0, duration=1.0), # G
        NoteInfo(pitch=72, start=3.0, duration=1.0), # C
        
        # Bar 2 (4-8) - Introduction of Bb
        NoteInfo(pitch=72, start=4.0, duration=1.0), # C
        NoteInfo(pitch=70, start=5.0, duration=1.0), # Bb <--- Chromatic!
        NoteInfo(pitch=69, start=6.0, duration=1.0), # A
        NoteInfo(pitch=67, start=7.0, duration=1.0), # G
        
        # Bar 3 (8-12) - Introduction of F#
        NoteInfo(pitch=62, start=8.0, duration=1.0), # D
        NoteInfo(pitch=66, start=9.0, duration=1.0), # F# <--- Chromatic!
        NoteInfo(pitch=69, start=10.0, duration=1.0), # A
        NoteInfo(pitch=72, start=11.0, duration=1.0), # C
        
        # Bar 4 (12-16) - Resolution
        NoteInfo(pitch=67, start=12.0, duration=2.0), # G
        NoteInfo(pitch=55, start=14.0, duration=2.0), # G (low)
    ]
    
    scale = Scale(root=0, mode=Mode.MAJOR)
    grid = BarGrid(numerator=4, denominator=4)
    harmonizer = CoupledHMMHarmonizer(bar_grid=grid, chord_change="bars")
    
    print("RUNNING COMPLEX HARMONIZATION TEST")
    print("-" * 40)
    print("Target: Detect Bb (Bar 2) and F# (Bar 3) as functional changes.")
    
    chords = harmonizer.harmonize(melody, scale, duration_beats=16.0)
    
    roots = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    
    for i, c in enumerate(chords):
        c_name = f"{roots[c.root]} {c.quality.name}"
        pcs = [roots[p] for p in c.pitch_classes()]
        
        # Calculate how well the melody fits this specific chord choice
        bar_notes = [n for n in melody if c.start <= n.start < c.start + c.duration]
        weights = pitch_class_weights(c.root, c.quality)
        
        avg_fit = sum(weights.get(n.pitch % 12, 0.5) for n in bar_notes) / len(bar_notes) if bar_notes else 0
        
        print(f"Bar {i+1} ({c.start}-{c.end}):")
        print(f"  Chosen: {c_name}")
        print(f"  Pitches: {', '.join(pcs)}")
        print(f"  Melodic Alignment Score: {avg_fit:.2f}")
        
        # Analysis
        if i == 1: # Bar 2
            if 'A#' in pcs or 'Bb' in pcs or c.quality == Quality.DOMINANT7:
                print("  => SUCCESS: Detected Bb/Dominant shift.")
            else:
                print("  => FAILED: Missed the Bb color.")
        
        if i == 2: # Bar 3
            if roots[c.root] == 'D' and c.quality in (Quality.MAJOR, Quality.DOMINANT7):
                print("  => SUCCESS: Identified D Major/Secondary Dominant (F#).")
            else:
                print("  => FAILED: Stayed diatonic (D minor) or picked wrong root.")
        print()

if __name__ == "__main__":
    analyze_complex_harmony()
