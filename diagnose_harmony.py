
import sys
import os

# Add the project root to sys.path
sys.path.append("/Volumes/External/Code/Melodica")

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.types import NoteInfo, Scale, Mode, BarGrid, Quality

def test_harmonization(melody, scale, name):
    print(f"\n{'='*60}")
    print(f"   TESTING: {name}")
    print(f"{'='*60}")
    print(f"Scale Context: {['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][scale.root]} {scale.mode.value}")
    
    # Setup 4/4 grid
    grid = BarGrid(numerator=4, denominator=4)
    # Instantiate harmonizer
    harmonizer = CoupledHMMHarmonizer(bar_grid=grid, chord_change="bars")
    
    # Calculate duration
    max_beat = max((n.start + n.duration) for n in melody) if melody else 16.0
    duration = max(16.0, (max_beat + 3) // 4 * 4) # round up to full bar
    
    chords = harmonizer.harmonize(melody, scale, duration_beats=duration)
    
    print(f"\nResults (One chord per bar):")
    print(f"{'Bar':<5} | {'Start':<6} | {'Chord':<15} | {'Pitch Classes'}")
    print(f"{'-'*60}")
    for i, c in enumerate(chords):
        bar = int(c.start // 4) + 1
        root_name = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][c.root]
        chord_name = f"{root_name} {c.quality.name}"
        pcs = c.pitch_classes()
        pc_names = [ ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][p] for p in pcs ]
        print(f"{bar:<5} | {c.start:<6.1f} | {chord_name:<15} | {', '.join(pc_names)}")

# 1. Classical C-D-E-F-G
melody_major = [
    NoteInfo(pitch=60, start=0, duration=2), # C
    NoteInfo(pitch=62, start=2, duration=2), # D
    NoteInfo(pitch=64, start=4, duration=2), # E
    NoteInfo(pitch=65, start=6, duration=2), # F
    NoteInfo(pitch=67, start=8, duration=2), # G
    NoteInfo(pitch=65, start=10, duration=2), # F
    NoteInfo(pitch=64, start=12, duration=4), # E
]

# 2. Minor Melancholic (A Minor)
melody_minor = [
    NoteInfo(pitch=69, start=0, duration=2), # A
    NoteInfo(pitch=71, start=2, duration=2), # B
    NoteInfo(pitch=72, start=4, duration=2), # C
    NoteInfo(pitch=74, start=6, duration=2), # D
    NoteInfo(pitch=76, start=8, duration=2), # E
    NoteInfo(pitch=72, start=10, duration=2), # C
    NoteInfo(pitch=69, start=12, duration=4), # A
]

# 3. Phrygian Dominant (E-F-G#-A-B)
melody_phrygian = [
    NoteInfo(pitch=64, start=0, duration=2), # E
    NoteInfo(pitch=65, start=2, duration=2), # F
    NoteInfo(pitch=68, start=4, duration=2), # G#
    NoteInfo(pitch=69, start=6, duration=2), # A
    NoteInfo(pitch=71, start=8, duration=2), # B
    NoteInfo(pitch=65, start=10, duration=2), # F
    NoteInfo(pitch=64, start=12, duration=4), # E
]

if __name__ == "__main__":
    test_harmonization(melody_major, Scale(root=0, mode=Mode.MAJOR), "Ionian (Major) - Tonal Balance")
    test_harmonization(melody_minor, Scale(root=9, mode=Mode.NATURAL_MINOR), "Aeolian (Minor) - Modal Stability")
    test_harmonization(melody_phrygian, Scale(root=4, mode=Mode.PHRYGIAN_DOMINANT), "Phrygian Dominant - Exotic Tension")
