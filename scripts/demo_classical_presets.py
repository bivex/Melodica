# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_classical_presets.py — Showcase of Classical Rhythm Presets.

Generates 3 short snippets:
1. Baroque Gavotte (using gavotte.json)
2. Classical Alberti Bass (using alberti_bass.json)
3. Orchestral Bolero (using bolero_ravel.json)
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def run_demo():
    print("================================================================================")
    print("  C L A S S I C A L   P R E S E T S   S H O W C A S E")
    print("================================================================================")

    out_dir = Path("output/demo_classical_presets")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Snippet 1: Baroque Gavotte (C Major)
    print("\n  [1/3] Generating Baroque Gavotte...")
    gavotte_tracks = [
        TrackConfig(
            name="Harpsichord_Lead",
            generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("gavotte")),
            instrument="harpsichord", density=1.0
        ),
        TrackConfig(
            name="Cello_Bass",
            generator=BassGenerator(style="root_only"),
            instrument="cello", density=0.5, octave_shift=-1
        )
    ]
    gavotte_parts = [IdeaPart(name="Gavotte", bars=4, scale=Scale(0, Mode.MAJOR), tempo=90)]
    gavotte_notes = IdeaTool(IdeaToolConfig(parts=gavotte_parts, tracks=gavotte_tracks, style="baroque")).generate()
    export_multitrack_midi({k:v for k,v in gavotte_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Classical_Gavotte.mid"), bpm=90)

    # Snippet 2: Classical Alberti Bass (G Major)
    print("  [2/3] Generating Classical Alberti Bass...")
    alberti_tracks = [
        TrackConfig(
            name="Piano_RH",
            generator=MelodyGenerator(mode="scale_walk", density=0.6),
            instrument="piano", density=0.6
        ),
        TrackConfig(
            name="Piano_LH_Alberti",
            generator=ChordGenerator(voicing="closed", rhythm=get_rhythm("alberti_bass")),
            instrument="piano", density=1.0, octave_shift=-1
        )
    ]
    alberti_parts = [IdeaPart(name="Alberti", bars=4, scale=Scale(7, Mode.MAJOR), tempo=110)]
    alberti_notes = IdeaTool(IdeaToolConfig(parts=alberti_parts, tracks=alberti_tracks, style="classical")).generate()
    export_multitrack_midi({k:v for k,v in alberti_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Classical_Alberti.mid"), bpm=110)

    # Snippet 3: Orchestral Bolero (C Major)
    print("  [3/3] Generating Orchestral Bolero Rhythms...")
    bolero_tracks = [
        TrackConfig(
            name="Snare_Drum",
            generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("bolero_ravel")),
            instrument="drums", density=1.0
        ),
        TrackConfig(
            name="String_Section",
            generator=StringsEnsembleGenerator(section_size="full", rhythm=get_rhythm("straight_quarters")),
            instrument="strings", density=0.8, octave_shift=-1
        ),
        TrackConfig(
            name="Flute_Solo",
            generator=MelodyGenerator(mode="downbeat_chord", rhythm=get_rhythm("markov:ballad")),
            instrument="flute", density=0.5
        )
    ]
    bolero_parts = [IdeaPart(name="Bolero", bars=8, scale=Scale(0, Mode.MAJOR), tempo=72)]
    bolero_notes = IdeaTool(IdeaToolConfig(parts=bolero_parts, tracks=bolero_tracks, style="cinematic")).generate()
    export_multitrack_midi({k:v for k,v in bolero_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Classical_Bolero.mid"), bpm=72)

    print("\n  SUCCESS! Classical presets exported to:")
    print(f"  {out_dir}/")
    print("================================================================================")

if __name__ == "__main__":
    run_demo()
