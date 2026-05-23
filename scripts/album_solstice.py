# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_solstice.py — "Solstice: The Belladonna Mission"
A dark psychological thriller album inspired by the mafia noir novel.
Features icy baroque logic, industrial tension, and tragic romanticism.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator

def generate_solstice():
    album_dir = Path("output/album_solstice")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        S O L S T I C E   /   С О Л Н Ц Е С Т О Я Н И Е")
    print("        A Psychological Mafia Thriller Symphony")
    print("=" * 80)

    tracks_configs = [
        {
            "name": "01_Silver_Barrel",
            "description": "The Prologue. Metal in the mouth. Death as liberation.",
            "tempo": 54,
            "scale": Scale(root=1, mode=Mode.PHRYGIAN), # C# Phrygian
            "bars": 40
        },
        {
            "name": "02_River_Winstead_Noir",
            "description": "The broken agent. Rain, trauma, and cold coffee.",
            "tempo": 65,
            "scale": Scale(root=1, mode=Mode.AEOLIAN), # C# Minor
            "bars": 48
        },
        {
            "name": "03_Alessandro_Michele_Ranieri",
            "description": "The Ice Prince. Baroque intelligence. Flawless cruelty.",
            "tempo": 74,
            "scale": Scale(root=8, mode=Mode.HARMONIC_MINOR), # G# Harmonic Minor
            "bars": 56
        },
        {
            "name": "04_Belladonna_Infiltration",
            "description": "Deception protocol. Seduction layered with poison.",
            "tempo": 102,
            "scale": Scale(root=1, mode=Mode.DORIAN), # C# Dorian
            "bars": 64
        },
        {
            "name": "05_Ranieri_Legacy",
            "description": "The shadow of Antonio. Imperial mafia power.",
            "tempo": 138,
            "scale": Scale(root=1, mode=Mode.PHRYGIAN_DOMINANT), # C# Phrygian Dom
            "bars": 80
        }
    ]

    for cfg in tracks_configs:
        print(f"\n--- Scoring Movement: {cfg['name']} ---")
        print(f"  {cfg['description']}")
        
        parts = [IdeaPart(
            name=cfg['name'], 
            bars=cfg['bars'], 
            scale=cfg['scale'], 
            tempo=cfg['tempo'],
            progression_type="coupled_hmm"
        )]

        # Custom Orchestration for Mafia Thriller
        track_list = [
            # 1. The Deep Unconscious (Trauma)
            TrackConfig(
                name="Sub_Deep_Contrabass", 
                generator=ContrabassGenerator(), 
                instrument="dark_bass", 
                arrangement="AABB",
                density=0.85, octave_shift=-1
            ),
            
            # 2. Modern Tension (Industrial Beats)
            TrackConfig(
                name="Nervous_Pulse", 
                generator=ElectronicDrumsGenerator(kit="industrial"), 
                instrument="drums", 
                arrangement="AABB",
                density=0.7 if cfg['tempo'] > 100 else 0.4
            ),
            TrackConfig(
                name="Metallic_Impacts", 
                generator=FXImpactGenerator(), 
                instrument="percussion", 
                arrangement="ABCD", density=0.5
            ),
            
            # 3. Emotional Core
            TrackConfig(
                name="Wounded_Cello", 
                generator=CelloGenerator(), 
                instrument="cello", 
                arrangement="ABCD", density=0.6, mpe=True
            ),
            TrackConfig(
                name="Icy_Piano", 
                generator=PianoCompGenerator(), 
                instrument="piano", 
                arrangement="AABB", density=0.55
            ),
            
            # 4. The Aristocratic Threat
            TrackConfig(
                name="Empire_Brass", 
                generator=BrassSectionGenerator(), 
                instrument="brass", 
                arrangement="AABC", density=0.6, octave_shift=-1
            ),
            TrackConfig(
                name="Betrayal_Choir", 
                generator=ChoirAahsGenerator(), 
                instrument="choir", 
                arrangement="ABCD", density=0.4, mpe=True
            ),

            # 5. Paranoia Layer
            TrackConfig(
                name="Abyss_Drones", 
                generator=DroneGenerator(), 
                instrument="synth_pad", 
                arrangement="AAAA",
                density=0.9, octave_shift=-1
            ),
            TrackConfig(
                name="Cipher_Noise", 
                generator=SciFiUnderscoreGenerator(), 
                instrument="synth_fx", 
                arrangement="ABCD", density=0.4
            )
        ]

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-14.0, # Higher dynamic range for tension
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
        print(f"    Completed: {cfg['name']} ({note_count} notes). Tension maintained.")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: SOLSTICE (THE BELLADONNA MISSION)")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_solstice()
