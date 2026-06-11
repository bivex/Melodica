
import sys
import os

sys.path.append("/Volumes/External/Code/Melodica")

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.types import NoteInfo, Scale, Mode, BarGrid, Quality
from melodica.composer.harmonic_awareness import pitch_class_weights

def run_long_melody_test():
    # MELODY: A 32-bar symphonic-style theme
    # Structure: 
    # 0-8:   Theme A (C Major, diatonic)
    # 8-16:  Theme A' (Slightly more active)
    # 16-24: Bridge (Developing tension, modulation hints)
    # 24-32: Climax & Resolution
    
    melody = []
    
    # 0-4: C-E-G-C (Arpeggio)
    melody += [NoteInfo(pitch=60, start=0.0, duration=1.0), NoteInfo(pitch=64, start=1.0, duration=1.0),
               NoteInfo(pitch=67, start=2.0, duration=1.0), NoteInfo(pitch=72, start=3.0, duration=1.0)]
    # 4-8: F-G-A-B-C (Scale up)
    melody += [NoteInfo(pitch=65, start=4.0, duration=1.0), NoteInfo(pitch=67, start=5.0, duration=1.0),
               NoteInfo(pitch=69, start=6.0, duration=1.0), NoteInfo(pitch=71, start=7.0, duration=1.0)]
    
    # 8-12: High C down to G with chromatic Bb
    melody += [NoteInfo(pitch=72, start=8.0, duration=1.0), NoteInfo(pitch=70, start=9.0, duration=1.0),
               NoteInfo(pitch=69, start=10.0, duration=1.0), NoteInfo(pitch=67, start=11.0, duration=1.0)]
    # 12-16: D-F#-A-C (D7 Arpeggio)
    melody += [NoteInfo(pitch=62, start=12.0, duration=1.0), NoteInfo(pitch=66, start=13.0, duration=1.0),
               NoteInfo(pitch=69, start=14.0, duration=1.0), NoteInfo(pitch=72, start=15.0, duration=1.0)]

    # 16-20: Bridge - Eb and Ab (Hinting at C Minor or Ab Major)
    melody += [NoteInfo(pitch=63, start=16.0, duration=2.0), NoteInfo(pitch=68, start=18.0, duration=2.0)]
    # 20-24: Tension - G# and B (Diminished feel)
    melody += [NoteInfo(pitch=68, start=20.0, duration=1.5), NoteInfo(pitch=71, start=21.5, duration=0.5),
               NoteInfo(pitch=74, start=22.0, duration=2.0)]
               
    # 24-28: Climax - High G-F-E-D
    melody += [NoteInfo(pitch=79, start=24.0, duration=1.0), NoteInfo(pitch=77, start=25.0, duration=1.0),
               NoteInfo(pitch=76, start=26.0, duration=1.0), NoteInfo(pitch=74, start=27.0, duration=1.0)]
    # 28-32: Resolution - C-G-C
    melody += [NoteInfo(pitch=72, start=28.0, duration=2.0), NoteInfo(pitch=67, start=30.0, duration=1.0),
               NoteInfo(pitch=60, start=31.0, duration=1.0)]

    scale = Scale(root=0, mode=Mode.MAJOR)
    grid = BarGrid(numerator=4, denominator=4)
    # We change chord every bar
    harmonizer = CoupledHMMHarmonizer(bar_grid=grid, chord_change="bars")
    
    print(f"RUNNING LONG MELODY HARMONIZATION (32 BEATS / 8 BARS)")
    print("-" * 60)
    
    chords = harmonizer.harmonize(melody, scale, duration_beats=32.0)
    
    roots = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    
    for i, c in enumerate(chords):
        bar = int(c.start // 4) + 1
        beat = c.start % 4 + 1
        c_name = f"{roots[c.root]} {c.quality.name}"
        
        # Calculate alignment
        bar_notes = [n for n in melody if c.start <= n.start < c.start + c.duration]
        weights = pitch_class_weights(c.root, c.quality)
        avg_fit = sum(weights.get(n.pitch % 12, 0.5) for n in bar_notes) / len(bar_notes) if bar_notes else 0
        
        status = "✅" if avg_fit > 1.1 else "△" if avg_fit > 0.8 else "❗"
        
        print(f"Bar {bar}.{int(beat)} | {c_name:<15} | Score: {avg_fit:.2f} {status}")

if __name__ == "__main__":
    run_long_melody_test()
