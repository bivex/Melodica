import sys
import os
sys.path.append('.')

from melodica.midi import export_multitrack_midi
from melodica.types import NoteInfo

notes = [
    NoteInfo(pitch=50, start=0.0, duration=4.0229),
    NoteInfo(pitch=50, start=4.01458, duration=4.0)
]

export_multitrack_midi({"Orchestral_Strings": notes}, "scratch/test.mid", humanize=False)

import mido
mid = mido.MidiFile("scratch/test.mid")
for msg in mid.tracks[1]:
    print(msg)
