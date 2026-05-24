import sys
sys.path.append('.')
from melodica.midi import export_multitrack_midi
from melodica.types import NoteInfo

notes = [
    NoteInfo(pitch=50, start=0.0, duration=4.0229),
    NoteInfo(pitch=50, start=0.0, duration=4.0)
]

export_multitrack_midi({"test": notes}, "scratch/test2.mid", humanize=False)

import mido
mid = mido.MidiFile("scratch/test2.mid")
for msg in mid.tracks[1]:
    if msg.type in ('note_on', 'note_off'):
        print(msg)
