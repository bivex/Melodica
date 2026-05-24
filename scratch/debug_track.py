import mido

mid = mido.MidiFile("output/demo_pro_structure/Pro_Structure_Masterclass.mid")
for track in mid.tracks:
    if track.name == "Orchestral_Strings":
        abs_time = 0
        active = {}
        for msg in track:
            abs_time += msg.time
            if getattr(msg, 'note', -1) == 50:
                print(f"{abs_time}: {msg}")
