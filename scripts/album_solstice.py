# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_solstice.py — "Solstice: The Belladonna Mission"
A high-contrast psychological thriller album.
Completely redesigned for sonic diversity by the Master Composer.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator, ViolaGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator

def generate_solstice_v2():
    album_dir = Path("output/album_solstice")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        S O L S T I C E   :   T H E   B E L L A D O N N A   M I S S I O N")
    print("        Master-Level Orchestration Pass (High Contrast)")
    print("=" * 80)

    tracks_configs = [
        {
            "id": "01",
            "name": "Death_as_Liberation",
            "description": "Prologue. Dissonance and silence. Only low registers and metal.",
            "tempo": 46,
            "scale": Scale(root=1, mode=Mode.LOCRIAN),
            "bars": 32
        },
        {
            "id": "02",
            "name": "Rain_in_Detroit",
            "description": "The trauma. Solitary piano and violin. Minimalist noir.",
            "tempo": 62,
            "scale": Scale(root=1, mode=Mode.AEOLIAN),
            "bars": 48
        },
        {
            "id": "03_Ice_Prince_Baroque",
            "name": "Ice_Prince_Logic",
            "description": "Alessandro's theme. Harpsichord, Oboe, and cold strings.",
            "tempo": 74,
            "scale": Scale(root=8, mode=Mode.HARMONIC_MINOR),
            "bars": 40
        },
        {
            "id": "04",
            "name": "Belladonna_Pulse",
            "description": "Infiltration. Rhythmic synth bass and choir whispers.",
            "tempo": 108,
            "scale": Scale(root=1, mode=Mode.DORIAN),
            "bars": 64
        },
        {
            "id": "05",
            "name": "Ranieri_Imperial_Power",
            "description": "The finale. Full orchestra. Maximum density and brass.",
            "tempo": 142,
            "scale": Scale(root=1, mode=Mode.PHRYGIAN_DOMINANT),
            "bars": 80
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
        
        if "Death" in cfg['name']:
            # 01: Minimal, terrifying depth
            track_list.append(TrackConfig(name="Trauma_Bass", generator=ContrabassGenerator(), instrument="dark_bass", density=0.9, octave_shift=-2))
            track_list.append(TrackConfig(name="Gun_Mechanism", generator=FXImpactGenerator(), instrument="percussion", density=0.6))
            track_list.append(TrackConfig(name="Suffocating_Pad", generator=DroneGenerator(), instrument="synth_pad", density=1.0, octave_shift=-1))
            
        elif "Rain" in cfg['name']:
            # 02: Sparse, weeping noir
            track_list.append(TrackConfig(name="Broken_Piano", generator=PianoCompGenerator(), instrument="piano", density=0.4))
            track_list.append(TrackConfig(name="Weeping_Violin", generator=ViolinGenerator(), instrument="violin", density=0.5, mpe=True))
            track_list.append(TrackConfig(name="Rain_Ambience", generator=SciFiUnderscoreGenerator(), instrument="synth_fx", density=0.6))

        elif "Logic" in cfg['name']:
            # 03: Intellectual baroque
            track_list.append(TrackConfig(name="Logic_Harpsichord", generator=PianoCompGenerator(), instrument="piano", density=0.75, octave_shift=1))
            track_list.append(TrackConfig(name="Cold_Oboe", generator=WoodwindsEnsembleGenerator(), instrument="oboe", density=0.6))
            track_list.append(TrackConfig(name="Order_Celli", generator=CelloGenerator(), instrument="cello", arrangement="AABB", density=0.55))
            track_list.append(TrackConfig(name="Anchor_Bass", generator=ContrabassGenerator(), instrument="contrabass", density=0.6))

        elif "Pulse" in cfg['name']:
            # 04: Seductive, rhythmic tension
            track_list.append(TrackConfig(name="Lure_Pulse", generator=ElectronicDrumsGenerator(kit="industrial"), instrument="drums", density=0.85))
            track_list.append(TrackConfig(name="Whisper_Choir", generator=ChoirAahsGenerator(), instrument="choir", density=0.7, mpe=True))
            track_list.append(TrackConfig(name="Secret_Viola", generator=ViolaGenerator(), instrument="viola", density=0.6))
            track_list.append(TrackConfig(name="Depth_Pad", generator=DroneGenerator(), instrument="synth_pad", density=0.8, octave_shift=-1))

        elif "Ranieri" in cfg['name']:
            # 05: Imperial orchestral power
            track_list.append(TrackConfig(name="War_Timpani", generator=TimpaniGenerator(), instrument="timpani", density=1.0))
            track_list.append(TrackConfig(name="Empire_Brass", generator=BrassSectionGenerator(), instrument="brass", density=0.9))
            track_list.append(TrackConfig(name="Furious_Violins", generator=OstinatoGenerator(pattern="driving"), instrument="violin", density=0.9))
            track_list.append(TrackConfig(name="Power_Bass", generator=ContrabassGenerator(), instrument="contrabass", density=1.0, octave_shift=-1))
            track_list.append(TrackConfig(name="Judgment_Choir", generator=ChoirAahsGenerator(), instrument="choir", density=0.7))

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-12.0 if "Ranieri" in cfg['name'] else -15.0,
            parts=parts,
            tracks=track_list
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
        
        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['id']}_{cfg['name']}.mid"),
            bpm=cfg['tempo'],
            key=cfg['scale'],
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set())
        )
        
        print(f"    Movement '{cfg['name']}' finalized with unique sonic signature.")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: SOLSTICE (HIGH CONTRAST EDITION)")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_solstice_v2()
