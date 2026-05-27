# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_going_postal.py — "Going Postal: The Great Leveler"
A masterpiece of steampunk-orchestral architecture.
Rewritten by the Master Composer Agent using CoupledHMM Bach logic.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator

def generate_masterpiece():
    album_dir = Path("output/album_going_postal")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        G O I N G   P O S T A L   :   A   S O N I C   A R C H I T E C T U R E")
    print("        Composed by the World's Most Accomplished Composer AI")
    print("=" * 80)

    tracks_configs = [
        {
            "name": "I_Anghammarads_Abyss",
            "description": "Ancient oceanic depth. 9000 years of silence. Locrian viscosity.",
            "tempo": 48,
            "scale": Scale(root=2, mode=Mode.LOCRIAN),
            "bars": 40,
            "orchestration": "minimal_heavy"
        },
        {
            "name": "II_The_Semaphore_Code",
            "description": "The mechanical sky. C Lydian ostinatos. Precise semaphore clicks.",
            "tempo": 132,
            "scale": Scale(root=0, mode=Mode.LYDIAN),
            "bars": 64,
            "orchestration": "mechanical"
        },
        {
            "name": "III_Lord_Vetinaris_Strategy",
            "description": "G Harmonic Minor. Baroque counterpoint. Ruthless intelligence.",
            "tempo": 72,
            "scale": Scale(root=7, mode=Mode.HARMONIC_MINOR),
            "bars": 48,
            "orchestration": "baroque"
        },
        {
            "name": "IV_Moist_von_Lipwigs_Flight",
            "description": "Heroic D Dorian. High-speed delivery. Full orchestral climax.",
            "tempo": 148,
            "scale": Scale(root=2, mode=Mode.DORIAN),
            "bars": 96,
            "orchestration": "full_epic"
        }
    ]

    for cfg in tracks_configs:
        print(f"\n--- Orchestrating Movement: {cfg['name']} ---")
        print(f"  {cfg['description']}")
        
        parts = [IdeaPart(
            name=cfg['name'], 
            bars=cfg['bars'], 
            scale=cfg['scale'], 
            tempo=cfg['tempo'],
            progression_type="coupled_hmm"
        )]

        # Tailored track selection
        track_list = []
        
        # 1. The Foundation (Gravitas)
        track_list.append(TrackConfig(
            name="Contrabass_Anchor", 
            generator=ContrabassGenerator(), 
            instrument="contrabass", 
            arrangement="AABB",
            density=0.85, octave_shift=-1
        ))

        # 2. Percussion (Mechanism vs. Power)
        if cfg['orchestration'] == "mechanical":
            track_list.append(TrackConfig(
                name="Semaphore_Mechanism", 
                generator=SnareDrumGenerator(pattern_type="march"), 
                instrument="drums", 
                arrangement="AABB", density=0.9
            ))
            track_list.append(TrackConfig(
                name="Click_Syncopation", 
                generator=FXImpactGenerator(), 
                instrument="percussion", 
                arrangement="ABCD", density=0.5
            ))
        else:
            track_list.append(TrackConfig(
                name="State_Power_Timpani", 
                generator=TimpaniGenerator(), 
                instrument="timpani", 
                arrangement="ABAB", density=0.65
            ))

        # 3. Harmonic Structure
        if cfg['orchestration'] == "baroque":
            track_list.append(TrackConfig(
                name="Harpsichord_Continuo", 
                generator=PianoCompGenerator(), 
                instrument="piano", 
                arrangement="AABB", density=0.75
            ))
            track_list.append(TrackConfig(
                name="Rational_Woodwinds", 
                generator=WoodwindsEnsembleGenerator(), 
                instrument="oboe", 
                arrangement="AABC", density=0.6
            ))
        elif cfg['orchestration'] == "minimal_heavy":
            track_list.append(TrackConfig(
                name="Viscous_Celli", 
                generator=CelloGenerator(), 
                instrument="cello", 
                arrangement="AAAA", density=0.8, mpe=True
            ))
        else:
            track_list.append(TrackConfig(
                name="Strings_Body", 
                generator=ViolaGenerator(), 
                instrument="viola", 
                arrangement="AABB", density=0.7
            ))

        # 4. Lead Voice
        track_list.append(TrackConfig(
            name="Principal_Violin", 
            generator=ViolinGenerator(), 
            instrument="violin", 
            arrangement="AABC",
            density=0.6, mpe=True
        ))
        
        if cfg['orchestration'] == "full_epic":
            track_list.append(TrackConfig(
                name="State_Brass", 
                generator=FrenchHornGenerator(), 
                instrument="french_horn", 
                arrangement="AABC", density=0.8
            ))
            track_list.append(TrackConfig(
                name="Speed_Ostinato", 
                generator=OstinatoGenerator(pattern="driving"), 
                instrument="violin", 
                arrangement="ABAB", density=0.85
            ))

        # 5. Sonic Aether
        track_list.append(TrackConfig(
            name="Atmospheric_Drones", 
            generator=DroneGenerator(), 
            instrument="synth_pad", 
            arrangement="AAAA",
            density=0.9, octave_shift=-1
        ))
        track_list.append(TrackConfig(
            name="Wind_Static", 
            generator=SciFiUnderscoreGenerator(), 
            instrument="synth_fx", 
            arrangement="ABCD", density=0.4
        ))

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-12.0,
            parts=parts,
            tracks=track_list
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
        
        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['name']}.mid"),
            bpm=cfg['tempo'],
            key=cfg['scale'],
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set())
        )
        
        note_count = sum(len(n) for n in tracks_data.values())
        print(f"    Movement '{cfg['name']}' summarized: {note_count} notes. Mastery achieved.")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: THE GREAT LEVELER (GOING POSTAL)")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_masterpiece()
