# check_wash_pitches.py
import mido

mid = mido.MidiFile("output/album_soft_machines_continuous/temp_0.mid")
for i, track in enumerate(mid.tracks):
    track_name = f"Track {i}"
    for msg in track:
        if msg.type == "track_name":
            track_name = msg.name
        if msg.type == "note_on" and msg.velocity > 0:
            if "analog_wash" in track_name:
                print(f"analog_wash note: pitch={msg.note}")
