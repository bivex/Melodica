# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
demo_ultra_jazz.py — Demonstration of HMM 4.0 'Ultra Jazz' Style.

Showcases tritone substitutions, backdoor cadences, and advanced functional flow.
"""

import sys
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.composer.album_pipeline import produce_track, Mood

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

KEY_C_MAJOR = types.Scale(root=0, mode=types.Mode.MAJOR)

def generate_jazz_melody():
    # Simple melody with some chromatic potential
    bpm, dur = 110, 32.0
    prog = "I:4.0 - IV:4.0 - ii:4.0 - V:4.0" # Diatonic base
    chords = types.parse_progression(prog, KEY_C_MAJOR)
    
    # Loop chords for 32 beats
    full_chords = []
    for i in range(2):
        for c in chords:
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=c.start + i*16, duration=c.duration))

    melody = MelodyGenerator(
        GeneratorParams(density=0.6, complexity=0.6, key_range_low=60, key_range_high=84),
        phrase_length=8.0
    ).render(full_chords, KEY_C_MAJOR, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.4, key_range_low=36, key_range_high=48),
        style="walking"
    ).render(full_chords, KEY_C_MAJOR, dur)

    return {
        "tracks": {"lead": melody, "bass": bass},
        "bpm": bpm,
        "instruments": {"lead": 66, "bass": 32}, # Tenor Sax + Acoustic Bass
        "key": KEY_C_MAJOR,
        "chords": full_chords
    }

def main():
    print("Generating Ultra Jazz Demo...")
    data = generate_jazz_melody()
    
    produce_track(
        tracks=data["tracks"],
        bpm=data["bpm"],
        instruments=data["instruments"],
        path="output/demo_ultra_jazz.mid",
        mood=Mood.CHAMBER,
        key=data["key"],
        engine="hmm",
        style="ultra_jazz"
    )

if __name__ == "__main__":
    main()
