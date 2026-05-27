# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_akhmatova.py — "The Silver Age: Akhmatova"
A symphonic song cycle based on 5 poems by Anna Akhmatova.
Orchestrated by the Master Composer using the CoupledHMM engine.
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
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator

def generate_akhmatova_album():
    album_dir = Path("output/album_akhmatova")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        T H E   S I L V E R   A G E   :   A K H M A T O V A")
    print("        A Symphonic Poetry Cycle")
    print("=" * 80)

    # 1. SATAN'S DIALOGUE (1960) - Mystical, Late style
    # 2. THE TIGHTROPE DANCER (1911) - Bitter irony, Orchestral mask
    # 3. THE WILD CAT (1911) - Suffocating heat, Waiting
    # 4. ASCENSION (1943) - War-time illness, Soul meeting the sun
    # 5. SMELL OF BURNING (1914) - Prophecy of war, Apocalypse

    tracks_configs = [
        {
            "name": "01_Satans_Dialogue",
            "tempo": 60,
            "scale": Scale(root=2, mode=Mode.PHRYGIAN), # D Phrygian - Dark, mystical
            "bars": 48,
            "style": "mystic_dark"
        },
        {
            "name": "02_Tightrope_Dancer",
            "tempo": 132,
            "scale": Scale(root=9, mode=Mode.DORIAN), # A Dorian - Bitter orchestral waltz feel
            "bars": 64,
            "style": "ironic_waltz"
        },
        {
            "name": "03_Wild_Cat_Heat",
            "tempo": 54,
            "scale": Scale(root=7, mode=Mode.LOCRIAN), # G Locrian - Dissonant, unstable heat
            "bars": 40,
            "style": "minimal_tense"
        },
        {
            "name": "04_Ascension_1943",
            "tempo": 72,
            "scale": Scale(root=0, mode=Mode.LYDIAN), # C Lydian - Bright, rising, transcendental
            "bars": 56,
            "style": "ethereal_hope"
        },
        {
            "name": "05_Smell_of_Burning_1914",
            "tempo": 112,
            "scale": Scale(root=2, mode=Mode.AEOLIAN), # D Minor - Heavy, prophetic
            "bars": 72,
            "style": "apocalyptic_march"
        }
    ]

    for cfg in tracks_configs:
        print(f"\n--- Composing: {cfg['name']} ---")
        
        parts = [IdeaPart(
            name=cfg['name'], 
            bars=cfg['bars'], 
            scale=cfg['scale'], 
            tempo=cfg['tempo'],
            progression_type="coupled_hmm"
        )]

        track_list = []
        
        # Base: Low Strings for everyone
        track_list.append(TrackConfig(
            name="Orchestral_Bass", 
            generator=ContrabassGenerator(), 
            instrument="contrabass", 
            density=0.8, octave_shift=-1
        ))

        if cfg['style'] == "mystic_dark":
            track_list.append(TrackConfig(name="Devil_Cello", generator=CelloGenerator(), instrument="cello", density=0.65, mpe=True))
            track_list.append(TrackConfig(name="Garnet_Pad", generator=DroneGenerator(), instrument="synth_pad", density=0.9, octave_shift=-1))
            track_list.append(TrackConfig(name="Voice_of_Satan", generator=MelodyGenerator(phrase_length=8.0, syncopation=0.2), instrument="voice", density=0.45, mpe=True))
            
        elif cfg['style'] == "ironic_waltz":
            track_list.append(TrackConfig(name="Fake_Smile_Violin", generator=ViolinGenerator(), instrument="violin", density=0.75, mpe=True))
            track_list.append(TrackConfig(name="Theater_Piano", generator=PianoCompGenerator(), instrument="piano", density=0.7))
            track_list.append(TrackConfig(name="Mocking_Horns", generator=FrenchHornGenerator(), instrument="french_horn", density=0.6))
            
        elif cfg['style'] == "minimal_tense":
            track_list.append(TrackConfig(name="Heat_Drone", generator=DroneGenerator(), instrument="synth_pad", density=1.0))
            track_list.append(TrackConfig(name="Ticking_Clock", generator=FXImpactGenerator(), instrument="percussion", density=0.3))
            track_list.append(TrackConfig(name="Cat_Oboe", generator=WoodwindsEnsembleGenerator(), instrument="oboe", density=0.5))

        elif cfg['style'] == "ethereal_hope":
            track_list.append(TrackConfig(name="Rising_Violins", generator=ViolinGenerator(), instrument="violin", density=0.7))
            track_list.append(TrackConfig(name="Sun_Choir", generator=ChoirAahsGenerator(), instrument="choir", density=0.65, mpe=True))
            track_list.append(TrackConfig(name="Crystal_Piano", generator=PianoCompGenerator(), instrument="piano", density=0.5, octave_shift=1))

        elif cfg['style'] == "apocalyptic_march":
            track_list.append(TrackConfig(name="War_Timpani", generator=TimpaniGenerator(), instrument="timpani", density=0.9))
            track_list.append(TrackConfig(name="Heavy_Trombones", generator=TromboneGenerator(), instrument="trombone", density=0.8, octave_shift=-1))
            track_list.append(TrackConfig(name="Prophecy_Voice", generator=ChoirAahsGenerator(), instrument="choir", density=0.55))
            track_list.append(TrackConfig(name="Smoke_Static", generator=SciFiUnderscoreGenerator(), instrument="synth_fx", density=0.4))

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            workflow="generate_all",
            use_tension_curve=True,
            use_harmonic_verifier=True,
            target_lufs=-13.0,
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
        
        print(f"    Movement '{cfg['name']}' exported successfully.")

    print("\n" + "=" * 80)
    print("  ALBUM COMPLETE: THE SILVER AGE (AKHMATOVA)")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_akhmatova_album()
