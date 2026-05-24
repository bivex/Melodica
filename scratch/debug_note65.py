import sys
sys.path.append('.')
from melodica.midi import export_multitrack_midi
from melodica.types import NoteInfo

notes = [
    NoteInfo(pitch=65, start=0.0, duration=3.8),
    NoteInfo(pitch=65, start=4.002, duration=3.8)
]

export_multitrack_midi({"test": notes}, "scratch/test5.mid", humanize=False)

import mido
mid = mido.MidiFile("scratch/test5.mid")
abs_time = 0
for msg in mid.tracks[1]:
    abs_time += msg.time
    if getattr(msg, 'note', -1) == 65:
        print(f"ABS={abs_time} TICK={msg.time} -> {msg}")
