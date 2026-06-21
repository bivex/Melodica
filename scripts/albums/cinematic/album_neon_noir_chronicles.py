# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/albums/cinematic/album_neon_noir_chronicles.py — "Neon Noir Chronicles"
A dystopian cinematic hybrid album leveraging the CoupledHMMHarmonizer.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import ViolinGenerator, ContrabassGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def generate_neon_noir_chronicles():
    album_dir = Path("output/album_neon_noir_chronicles")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        N E O N   N O I R   C H R O N I C L E S")
    print("        Cinematic Hybrid Album (HMM-based Progression Generation)")
    print("=" * 80)

    tracks_configs = [
        {
            "id": "01",
            "name": "Neon_Rain",
            "description": "Movement I: Neon Rain. Lone detective walking down a wet street. Minimalist piano/violin.",
            "tempo": 65,
            "scale": Scale(root=0, mode=Mode.DORIAN), # C Dorian
            "bars": 32
        },
        {
            "id": "02",
            "name": "Megacorp_Heist",
            "description": "Movement II: Megacorp Heist. Tension as data is extracted from the mainframe. Industrial synth pulse.",
            "tempo": 120,
            "scale": Scale(root=7, mode=Mode.LOCRIAN), # G Locrian
            "bars": 48
        },
        {
            "id": "03",
            "name": "Dystopian_Dawn",
            "description": "Movement III: Dystopian Dawn. Sun rises over the ruins of a mega-city. Melancholy orchestral brass and choir.",
            "tempo": 80,
            "scale": Scale(root=2, mode=Mode.LYDIAN), # D Lydian
            "bars": 40
        }
    ]

    for cfg in tracks_configs:
        print(f"\n--- Constructing Movement {cfg['id']}: {cfg['name']} ---")
        print(f"  {cfg['description']}")
        
        parts = [IdeaPart(
            name=cfg['name'], 
            bars=cfg['bars'], 
            scale=cfg['scale'], 
            tempo=cfg['tempo'],
            progression_type="coupled_hmm"
        )]

        track_list = []
        
        if "Rain" in cfg['name']:
            track_list.append(TrackConfig(name="Broken_Piano", generator=PianoCompGenerator(), instrument="piano", density=0.45))
            track_list.append(TrackConfig(name="Weeping_Violin", generator=ViolinGenerator(), instrument="violin", density=0.5))
            track_list.append(TrackConfig(name="Rain_FX", generator=SciFiUnderscoreGenerator(), instrument="synth_fx", density=0.6))
            track_list.append(TrackConfig(name="Dark_Bass", generator=ContrabassGenerator(), instrument="contrabass", density=0.55, octave_shift=-1))
            
        elif "Heist" in cfg['name']:
            track_list.append(TrackConfig(name="Industrial_Pulse", generator=ElectronicDrumsGenerator(kit="industrial"), instrument="drums", density=0.85))
            track_list.append(TrackConfig(name="Furious_Violins", generator=OstinatoGenerator(pattern="driving"), instrument="violin", density=0.85))
            track_list.append(TrackConfig(name="Power_Bass", generator=ContrabassGenerator(), instrument="contrabass", density=0.9, octave_shift=-1))
            track_list.append(TrackConfig(name="Suspense_Drone", generator=DroneGenerator(), instrument="synth_pad", density=0.75, octave_shift=-1))

        elif "Dawn" in cfg['name']:
            track_list.append(TrackConfig(name="Empire_Brass", generator=BrassSectionGenerator(), instrument="brass", density=0.85))
            track_list.append(TrackConfig(name="War_Timpani", generator=TimpaniGenerator(), instrument="timpani", density=0.9))
            track_list.append(TrackConfig(name="Judgment_Choir", generator=ChoirAahsGenerator(), instrument="choir", density=0.75))
            track_list.append(TrackConfig(name="Solo_Violin", generator=ViolinGenerator(), instrument="violin", density=0.6))

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-12.0 if "Heist" in cfg['name'] else -15.0,
            parts=parts,
            tracks=track_list
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
        
        # Display the generated HMM chords
        chords = notes_dict.get("_chords", [])
        chord_names = [f"{NOTE_NAMES[c.root]} {c.quality.name}" for c in chords]
        print(f"  ➔ Generated chords: {' ➔ '.join(chord_names)}")

        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['id']}_{cfg['name']}.mid"),
            bpm=cfg['tempo'],
            key=cfg['scale'],
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set())
        )
        
        print(f"  ➔ Movement '{cfg['name']}' finalized.")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: NEON NOIR CHRONICLES")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    generate_neon_noir_chronicles()
