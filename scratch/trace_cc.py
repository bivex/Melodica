import mido
import sys
from pathlib import Path
from collections import defaultdict

def trace_midi_ccs(file_path):
    print(f"Tracing CCs in: {file_path}")
    mid = mido.MidiFile(file_path)
    
    track_ccs = defaultdict(set)
    cc_names = {
        1: "Modulation",
        3: "Vibrato Depth",
        6: "Pitch Bend Range (Data Entry)",
        7: "Volume",
        10: "Pan",
        11: "Expression",
        38: "Data Entry LSB",
        64: "Sustain Pedal",
        72: "Release Time",
        73: "Attack Time",
        74: "Brightness (Cutoff)",
        91: "Reverb",
        93: "Chorus",
        100: "RPN LSB",
        101: "RPN MSB",
    }
    
    for track in mid.tracks:
        track_name = "Unknown Track"
        for msg in track:
            if msg.type == 'track_name':
                track_name = msg.name
                
        for msg in track:
            if msg.type == 'control_change':
                track_ccs[track_name].add(msg.control)
                
    for track_name, ccs in track_ccs.items():
        print(f"  Track: '{track_name}'")
        if not ccs:
            print("    No CCs")
        for cc in sorted(list(ccs)):
            name = cc_names.get(cc, "Unknown")
            print(f"    CC {cc} ({name})")
            
if __name__ == "__main__":
    folder = Path("output/album_black_prince")
    if not folder.exists():
        print("Folder not found")
        sys.exit(1)
        
    for f in sorted(folder.glob("*.mid")):
        trace_midi_ccs(f)
        print("-" * 40)
