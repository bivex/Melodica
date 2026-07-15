"""Dump the harmonized chords (tool._chords) for each movement."""
import importlib.util
from pathlib import Path

# load the album module without running main()
spec = importlib.util.spec_from_file_location(
    "album_hungarian_shadows",
    Path("scripts/albums/cinematic/album_hungarian_shadows.py"),
)
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.generators import (
    ChordGenerator, StringsEnsembleGenerator, AmbientPadGenerator,
    BassGenerator, MelodyGenerator,
)
from melodica.types import Scale, Mode

NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
QSHORT = {
    "MAJOR": "", "MINOR": "m", "DIMINISHED": "dim", "AUGMENTED": "+",
    "DOMINANT7": "7", "MAJOR7": "maj7", "MINOR7": "m7",
    "SUSPENDED4": "sus4", "SUSPENDED2": "sus2",
    "DIMINISHED7": "dim7", "HALF_DIMINISHED": "m7b5",
    "MINOR_MAJOR7": "mMaj7", "DOMINANT9": "9",
}

tracks_common = [
    TrackConfig(name="Geometry_Piano",
                generator=ChordGenerator(voicing="closed", add_bass_note=-2),
                instrument="piano", density=0.9),
    TrackConfig(name="String_Chorus",
                generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=4),
                instrument="strings", density=0.7),
    TrackConfig(name="Dark_Pad", generator=AmbientPadGenerator(voicing="spread"),
                instrument="dark_pad", density=0.6, octave_shift=-1),
    TrackConfig(name="Contrabass", generator=BassGenerator(style="root_only"),
                instrument="contrabass", density=0.6, octave_shift=-2),
    TrackConfig(name="Lead_Melody", generator_type="melody",
                generator=MelodyGenerator(prefer_chord_tones=0.7, note_range_low=74,
                                          note_range_high=96, allow_2nd=True, allow_7th=True),
                instrument="flute", density=0.6),
]

movements = [
    {"name": "01_Litany", "root": 2, "tempo": 60, "ts": (4, 4),
     "bars": {"intro": 2, "verse": 4, "climax": 4, "coda": 2}},
    {"name": "02_The_Magnetar", "root": 9, "tempo": 76, "ts": (4, 4),
     "bars": {"intro": 2, "verse": 4, "climax": 4, "coda": 2}},
    {"name": "03_Glass_Cartographer", "root": 0, "tempo": 88, "ts": (4, 4),
     "bars": {"intro": 2, "verse": 4, "climax": 4, "coda": 2}},
    {"name": "04_Augmented_Seconds", "root": 5, "tempo": 96, "ts": (4, 4),
     "bars": {"intro": 2, "verse": 4, "climax": 6, "coda": 2}},
    {"name": "05_Apocrypha", "root": 4, "tempo": 64, "ts": (3, 4),
     "bars": {"intro": 2, "verse": 3, "climax": 3, "coda": 2}},
]

def lab(c):
    q = QSHORT.get(c.quality.name, c.quality.name)
    inv = f"/{NOTE[c.bass]}" if getattr(c, "bass", None) and c.bass != c.root else ""
    return f"{NOTE[c.root]}{q}{inv}"

for m in movements:
    parts = A._movement_sections(m)
    cfg = IdeaToolConfig(
        style="cinematic_hybrid",
        workflow="generate_melody_then_harmonize",
        scale=Scale(m["root"], Mode.HUNGARIAN_MINOR),
        parts=parts, tracks=tracks_common,
        use_voice_leading=True, use_tension_curve=True,
    )
    tool = IdeaTool(cfg)
    tool.generate()
    chords = getattr(tool, "_chords", [])
    print(f"\n=== {m['name']}  (root={NOTE[m['root']]} Hungarian minor) ===")
    print("  " + " | ".join(lab(c) for c in chords))
