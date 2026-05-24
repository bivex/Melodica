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
notes = notes_dict["Orchestral_Strings"]

print("Original notes:")
for n in sorted(notes, key=lambda x: (x.pitch, x.start)):
    if n.pitch == 60:
        print(f"pitch={n.pitch} start={n.start} duration={n.duration}")
