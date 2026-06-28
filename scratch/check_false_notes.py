# check_false_notes.py
import mido
from pathlib import Path
from melodica.types import Scale, Mode
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule

# Map files to their scale
SCALES = {
    "01_Velvet_Circuit.mid": Scale(9, Mode.AEOLIAN),   # A Minor
    "02_Static_Bloom.mid": Scale(2, Mode.DORIAN),     # D Dorian
    "03_Memory_Foam.mid": Scale(4, Mode.PHRYGIAN),    # E Phrygian
    "04_Velvet_Return.mid": Scale(9, Mode.AEOLIAN),   # A Minor
}

def analyze_false_notes(filepath: Path, scale: Scale):
    print(f"\nAnalyzing false notes for: {filepath.name} (Scale: {scale.mode.value} on {scale.root})")
    mid = mido.MidiFile(filepath)
    
    # Let's extract all chords from the '_chords' track or metadata if available
    # Wait, the chords are stored in tracks as text/marker events, or we can read them from a companion track.
    # In Melodica, the chord track is exported as a MIDI track named "_chords" containing chord text/markers,
    # or we can read it. Let's find out if there's a track with name "_chords" or "chords".
    chords_track = None
    for track in mid.tracks:
        for msg in track:
            if msg.type == "track_name" and "chord" in msg.name.lower():
                chords_track = track
                break
                
    # If no chord track, we will just check scale conformity
    scale_pcs = set(scale.degrees())
    
    # We will accumulate all notes with their absolute start time (in beats)
    # Since MIDI messages use delta time in ticks, we need to convert ticks to beats.
    tpb = mid.ticks_per_beat
    
    false_notes_count = 0
    total_notes_count = 0
    
    for i, track in enumerate(mid.tracks):
        track_name = f"Track {i}"
        current_time_ticks = 0
        
        for msg in track:
            current_time_ticks += msg.time
            if msg.type == "track_name":
                track_name = msg.name
                
            if msg.type == "note_on" and msg.velocity > 0:
                total_notes_count += 1
                pitch = msg.note
                pc = pitch % 12
                
                # Check if pitch class is in scale
                # (We use a fuzzy check because scale degrees can be floats for microtonality)
                in_scale = any(abs(pc - d) < 0.01 or abs(pc - d - 12) < 0.01 or abs(pc - d + 12) < 0.01 for d in scale_pcs)
                
                if not in_scale:
                    false_notes_count += 1
                    beat = current_time_ticks / tpb
                    print(f"    ❌ False note in {track_name}: Pitch {pitch} (PC {pc}) at beat {beat:.2f}")
                    
    print(f"  Summary: {false_notes_count} out-of-scale notes out of {total_notes_count} total notes ({false_notes_count/max(1, total_notes_count)*100:.1f}%)")

if __name__ == "__main__":
    out_dir = Path("output/album_soft_machines_continuous")
    for f in sorted(out_dir.glob("*.mid")):
        if f.name in SCALES:
            analyze_false_notes(out_dir / f.name, SCALES[f.name])
