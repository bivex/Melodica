import os
import mido

output_dir = "/Volumes/External/Code/Melodica/output"
files = sorted([f for f in os.listdir(output_dir) if f.endswith('.mid')])

for f in files:
    path = os.path.join(output_dir, f)
    print(f"--- {f} ---")
    mid = mido.MidiFile(path)
    print(f"Ticks per beat: {mid.ticks_per_beat}")
    for i, track in enumerate(mid.tracks):
        print(f"  Track {i}: {track.name}")
        for msg in track:
            if not msg.is_meta:
                print(f"    {msg}")
    print("\n")
