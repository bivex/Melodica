import sys
sys.path.append('.')
from melodica.midi import export_multitrack_midi
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, PhraseSlot, PhraseSchedule
from melodica.types import Scale, Mode
from melodica.generators import StringsEnsembleGenerator

scale = Scale(2, Mode.DORIAN)
parts = [
    IdeaPart(name="Intro", bars=4, scale=scale, tempo=75, track_phrase_schedules={"Orchestral_Strings": PhraseSchedule([PhraseSlot("play", 4)])}),
    IdeaPart(name="Verse", bars=4, scale=scale, tempo=75, track_phrase_schedules={"Orchestral_Strings": PhraseSchedule([PhraseSlot("play", 4)])}),
]
tracks = [TrackConfig(name="Orchestral_Strings", generator=StringsEnsembleGenerator())]
config = IdeaToolConfig(parts=parts, tracks=tracks)
notes_dict = IdeaTool(config).generate()
tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

export_multitrack_midi(tracks_data, "scratch/test3.mid", humanize=True)
import mido
mid = mido.MidiFile("scratch/test3.mid")
abs_time = 0
active = {}
anomalies = []
for msg in mid.tracks[1]:
    abs_time += msg.time
    if msg.type == 'note_on' and msg.velocity > 0:
        if msg.note in active:
            anomalies.append(f"Anomaly: Note {msg.note} started at {abs_time}, but previous started at {active[msg.note]}")
        active[msg.note] = abs_time
    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
        if msg.note in active:
            del active[msg.note]

for a in anomalies:
    print(a)

