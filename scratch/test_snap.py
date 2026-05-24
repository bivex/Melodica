import sys
sys.path.append('.')
from melodica.modifiers import ChordToneSnapModifier, ModifierContext
from melodica.types import NoteInfo, ChordLabel, Scale, Quality, MusicTimeline, Mode

# C Major chord
chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)
timeline = MusicTimeline(chords=[chord])

# Note D4 (62), which is NOT in C Major chord (C, E, G -> 0, 4, 7)
# Nearest to D (2) are C (0) and E (4).
note = NoteInfo(pitch=62, start=1.0, duration=1.0)

mod = ChordToneSnapModifier()
ctx = ModifierContext(duration_beats=4, chords=[chord], timeline=timeline, scale=Scale(0, Mode.MAJOR))

result = mod.modify([note], ctx)
print(f"Original pitch: {note.pitch} (D4)")
print(f"Snapped pitch: {result[0].pitch}")
