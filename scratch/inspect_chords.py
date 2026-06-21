import sys
from pathlib import Path

# Add project root to path
sys.path.append("/Volumes/External/Code/Melodica")

# Import the album module
import scripts.albums.literary.album_tre_metri_sopra_il_cielo as album_mod

original_harmonize = album_mod._harmonize

current_track = ""
track_chords = []

def verbose_harmonize(melody, scale, dur, constraints=None):
    chords = original_harmonize(melody, scale, dur, constraints)
    note_names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    chord_list = []
    for c in chords:
        chord_list.append(f"{note_names[c.root]} {c.quality.name}")
    track_chords.append((current_track, chord_list))
    return chords

# Patch the harmonizer helper
album_mod._harmonize = verbose_harmonize

if __name__ == "__main__":
    print("=" * 80)
    print("  TRE METRI SOPRA IL CIELO — GENERATED HARMONIES (t5harmony)")
    print("=" * 80)
    
    # Run each track generator individually to bypass console output clutter
    for track_func, title, _ in album_mod.TRACKS:
        current_track = title.replace(".mid", "")
        # Call the generator (suppressing standard output if needed, but it's fine)
        track_func()
        
    for track_name, chords in track_chords:
        print(f"\n[{track_name}]")
        print("  -> " + " -> ".join(chords))
    
    print("\n" + "=" * 80)
