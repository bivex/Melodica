# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_going_postal.py — "Going Postal: The Great Leveler"
A steampunk-orchestral hybrid album inspired by Terry Pratchett.
Uses the advanced CoupledHMM engine with high-fidelity Bach weights.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_impact import FXImpactGenerator

def generate_going_postal():
    album_dir = Path("output/album_going_postal")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        G O I N G   P O S T A L   /   Д Е Р Ж И   М А Р К У !")
    print("        A Steampunk-Orchestral Symphony")
    print("=" * 80)

    tracks_configs = [
        {
            "name": "01_9000_Years_Below",
            "description": "Anghammarad's depth. Viscous water, ancient silence.",
            "tempo": 52,
            "scale": Scale(root=2, mode=Mode.LOCRIAN), # D Locrian
            "bars": 40
        },
        {
            "name": "02_The_Clacks_Rhythm",
            "description": "The mechanical pulse of semaphore towers. Wind and light.",
            "tempo": 128,
            "scale": Scale(root=0, mode=Mode.LYDIAN), # C Lydian
            "bars": 64
        },
        {
            "name": "03_Vetinaris_Angel",
            "description": "The Patrician's office. Baroque intelligence and hidden menace.",
            "tempo": 76,
            "scale": Scale(root=7, mode=Mode.HARMONIC_MINOR), # G Harmonic Minor
            "bars": 48
        },
        {
            "name": "04_Deliver_or_Die",
            "description": "Moist von Lipwig's run. Heroic bureaucracy and high speed.",
            "tempo": 144,
            "scale": Scale(root=2, mode=Mode.DORIAN), # D Dorian
            "bars": 80
        }
    ]

    for cfg in tracks_configs:
        print(f"\n--- {cfg['name']} ---")
        print(f"  {cfg['description']}")
        
        parts = [IdeaPart(
            name=cfg['name'], 
            bars=cfg['bars'], 
            scale=cfg['scale'], 
            tempo=cfg['tempo'],
            progression_type="coupled_hmm"
        )]

        # Tailored track list for the "steampunk/bureaucracy" aesthetic
        track_list = [
            # 1. Foundation
            TrackConfig(
                name="Deep Contrabass", 
                generator=ContrabassGenerator(), 
                instrument="contrabass", 
                arrangement="AABB",
                density=0.8,
                octave_shift=-1
            ),
            
            # 2. Percussion (The "Clacks" mechanism)
            TrackConfig(
                name="Mechanical Snare", 
                generator=SnareDrumGenerator(pattern_type="march"), 
                instrument="drums", 
                arrangement="AABB",
                density=0.6 if cfg['name'] != "02_The_Clacks_Rhythm" else 0.9
            ),
            TrackConfig(
                name="Orchestral Hits", 
                generator=FXImpactGenerator(), 
                instrument="percussion", 
                arrangement="ABCD",
                density=0.4
            ),
            
            # 3. Melodic/Keyboard (Clockwork feel)
            TrackConfig(
                name="Staccato Violin", 
                generator=ViolinGenerator(), 
                instrument="violin", 
                arrangement="AABC",
                density=0.7,
                mpe=True
            ),
            TrackConfig(
                name="Harpsichord/Piano", 
                generator=PianoCompGenerator(), 
                instrument="piano", 
                arrangement="AABB",
                density=0.7 if "Vetinari" in cfg['name'] else 0.5
            ),
            
            # 4. Brass (Power of the State)
            TrackConfig(
                name="Government Horns", 
                generator=FrenchHornGenerator(), 
                instrument="french_horn", 
                arrangement="AABC",
                density=0.5
            ),
            
            # 5. Atmosphere
            TrackConfig(
                name="Aether Pad", 
                generator=DroneGenerator(), 
                instrument="synth_pad", 
                arrangement="AAAA",
                density=0.8,
                octave_shift=-1
            ),
            TrackConfig(
                name="Wind Static", 
                generator=SciFiUnderscoreGenerator(), 
                instrument="synth_fx", 
                arrangement="ABCD",
                density=0.3
            )
        ]

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-13.0,
            parts=parts,
            tracks=track_list
        )

        # Execution
        notes_dict = IdeaTool(tool_config).generate()
        
        # MIDI Extraction
        tracks_data = {
            k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)
        }
        
        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['name']}.mid"),
            bpm=cfg['tempo'],
            key=cfg['scale'],
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set())
        )
        
        note_count = sum(len(n) for n in tracks_data.values())
        print(f"    Exported {cfg['name']}.mid ({note_count} notes)")

    print("\n" + "=" * 80)
    print(f"  PRODUCTION COMPLETE: Going Postal Album")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_going_postal()
