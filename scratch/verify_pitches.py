# verify_pitches.py
import mido
from pathlib import Path

# Set of allowed pitch classes (natural diatonic collection: C, D, E, F, G, A, B)
ALLOWED_PCS = {0, 2, 4, 5, 7, 9, 11}
PC_NAMES = {0: "C", 1: "C#", 2: "D", 3: "D#", 4: "E", 5: "F", 6: "F#", 7: "G", 8: "G#", 9: "A", 10: "A#", 11: "B"}

def verify_midi_file(filepath: Path):
    print(f"\nAnalyzing: {filepath.name}")
    mid = mido.MidiFile(filepath)
    
    out_of_scale = []
    pitch_classes = {}
    total_notes = 0
    
    for i, track in enumerate(mid.tracks):
        track_name = f"Track {i}"
        for msg in track:
            if msg.type == "track_name":
                track_name = msg.name
            elif msg.type == "note_on" and msg.velocity > 0:
                pitch = msg.note
                pc = pitch % 12
                total_notes += 1
                pitch_classes[pc] = pitch_classes.get(pc, 0) + 1
                
                if pc not in ALLOWED_PCS:
                    out_of_scale.append((track_name, pitch, PC_NAMES[pc]))
                    
    print(f"  Total notes: {total_notes}")
    print("  Pitch class distribution:")
    for pc in sorted(pitch_classes.keys()):
        pct = (pitch_classes[pc] / total_notes) * 100
        print(f"    {PC_NAMES[pc]}: {pitch_classes[pc]} ({pct:.1f}%)")
        
    if out_of_scale:
        print(f"  ❌ FOUND {len(out_of_scale)} OUT-OF-SCALE NOTES:")
        for tname, pitch, name in out_of_scale[:15]:
            print(f"    - {tname}: Pitch {pitch} ({name})")
        if len(out_of_scale) > 15:
            print(f"    ... and {len(out_of_scale) - 15} more.")
    else:
        print("  ✅ All notes are 100% diatonic (within the correct scale)!")

if __name__ == "__main__":
    out_dir = Path("output/album_soft_machines_continuous")
    for f in sorted(out_dir.glob("*.mid")):
        if f.name != "continuous_album.mid":
            verify_midi_file(f)
