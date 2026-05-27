import sys
sys.path.append('.')
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
from melodica.types import Scale, Mode
from melodica.generators import BassGenerator

scale = Scale(2, Mode.NATURAL_MINOR)  # D Minor

tracks = [
    TrackConfig(name="Sub_Bass", generator=BassGenerator(), instrument="contrabass", density=0.6),
]

parts = [
    IdeaPart(name="Intro", bars=8, scale=scale, tempo=85, progression_type="coupled_hmm", track_phrase_schedules={"Sub_Bass": structure_to_schedule("A", 8)}),
    IdeaPart(name="Build", bars=8, scale=scale, tempo=88, progression_type="coupled_hmm", track_phrase_schedules={"Sub_Bass": structure_to_schedule("B", 8)}),
    IdeaPart(name="Climax", bars=16, scale=scale, tempo=92, progression_type="coupled_hmm", track_phrase_schedules={"Sub_Bass": structure_to_schedule("C", 16)}),
    IdeaPart(name="Outro", bars=8, scale=scale, tempo=80, progression_type="coupled_hmm", track_phrase_schedules={"Sub_Bass": structure_to_schedule("A", 8)}),
]

config = IdeaToolConfig(style="cinematic_hybrid", parts=parts, tracks=tracks, use_tension_curve=True)
notes_dict = IdeaTool(config).generate()

timeline_chords = notes_dict["_chords"]
print("\n--- GENERATED CHORDS ---")
for c in timeline_chords:
    q = c.quality.name if hasattr(c.quality, 'name') else str(c.quality)
    print(f"{c.start:5.1f} - {c.end:5.1f} | Root: {c.root:2d} | Quality: {q}")
