import sys
sys.path.append('.')
from melodica.midi import export_multitrack_midi
from melodica.types import NoteInfo

notes = [
    NoteInfo(pitch=60, start=0.0, duration=4.02),
    NoteInfo(pitch=60, start=3.99, duration=4.0)
]

export_multitrack_midi({"test": notes}, "scratch/test4.mid", humanize=False)

import mido
mid = mido.MidiFile("scratch/test4.mid")
abs_time = 0
for msg in mid.tracks[1]:
    abs_time += msg.time
    if getattr(msg, 'note', -1) == 60:
        print(f"ABS={abs_time} TICK={msg.time} -> {msg}")
