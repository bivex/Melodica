from melodica.composer.psychoacoustic import detect_frequency_masking, _freq_masked
from melodica.types import NoteInfo

notes_a = [NoteInfo(pitch=60, velocity=100, start=0.0, duration=1.0)]
notes_b = [NoteInfo(pitch=61, velocity=40, start=0.0, duration=1.0)]
tracks = {"a": notes_a, "b": notes_b}

events = detect_frequency_masking(tracks)
print(events)
