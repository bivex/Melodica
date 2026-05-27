# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/demo_japanese_vibe.py — Japanese Music Style Generator.

Showcases:
1. Traditional Hogaku (Koto + Shamisen)
2. City Pop / Modern J-Pop rhythms.
3. High-energy JRPG / Touhou battle patterns.
4. J-Rock / Visual Kei energy.
"""

from pathlib import Path
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS,
    structure_to_schedule,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

def run_demo():
    print("================================================================================")
    print("  J A P A N E S E   V I B E   G E N E R A T O R")
    print("================================================================================")

    out_dir = Path("output/demo_japanese_vibe")
    out_dir.mkdir(exist_ok=True, parents=True)

    # 1. Traditional Hogaku (Sakura/Shamisen)
    print("\n  [1/4] Generating Traditional Hogaku...")
    hogaku_tracks = [
        TrackConfig(
            name="Koto_Main",
            generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("koto_sakura_sakura")),
            instrument="koto", density=1.0
        ),
        TrackConfig(
            name="Shamisen_Jongara",
            generator=MelodyGenerator(mode="scale_walk", rhythm=get_rhythm("shamisen_jongara")),
            instrument="shamisen", density=0.8, octave_shift=-1
        )
    ]
    hogaku_parts = [IdeaPart(name="Traditional", bars=8, scale=Scale(9, Mode.NATURAL_MINOR), tempo=84)]
    hogaku_notes = IdeaTool(IdeaToolConfig(parts=hogaku_parts, tracks=hogaku_tracks)).generate()
    export_multitrack_midi({k:v for k,v in hogaku_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Japanese_Traditional.mid"), bpm=84)

    # 2. City Pop Groove
    print("  [2/4] Generating 80s City Pop Vibe...")
    city_pop_tracks = [
        TrackConfig(
            name="Electric_Piano",
            generator=ChordGenerator(voicing="spread", rhythm=get_rhythm("city_pop_groove")),
            instrument="electric_piano", density=1.0
        ),
        TrackConfig(
            name="Funk_Bass",
            generator=BassGenerator(style="walking"),
            instrument="synth_bass", density=0.8, octave_shift=-1
        ),
        TrackConfig(
            name="City_Lead",
            generator=MelodyGenerator(mode="downbeat_chord", rhythm=get_rhythm("markov:swing")),
            instrument="bright_piano", density=0.6
        )
    ]
    city_pop_parts = [IdeaPart(name="CityPop", bars=8, scale=Scale(5, Mode.DORIAN), tempo=118)]
    city_pop_notes = IdeaTool(IdeaToolConfig(parts=city_pop_parts, tracks=city_pop_tracks)).generate()
    export_multitrack_midi({k:v for k,v in city_pop_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Japanese_CityPop.mid"), bpm=118)

    # 3. JRPG Battle / Touhou
    print("  [3/4] Generating JRPG / Touhou Battle Energy...")
    battle_tracks = [
        TrackConfig(
            name="Fast_Strings",
            generator=MelodyGenerator(mode="scale_walk", rhythm=get_rhythm("jrpg_battle")),
            instrument="strings", density=1.0, octave_shift=0
        ),
        TrackConfig(
            name="ZUN_Trumpet",
            generator=MelodyGenerator(mode="downbeat_chord", rhythm=get_rhythm("touhou_boss_theme")),
            instrument="trumpet", density=0.7, octave_shift=1
        ),
        TrackConfig(
            name="Power_Drums",
            generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("anime_op_8th")),
            instrument="drums", density=1.0
        )
    ]
    battle_parts = [IdeaPart(name="Battle", bars=8, scale=Scale(2, Mode.NATURAL_MINOR), tempo=165)]
    battle_notes = IdeaTool(IdeaToolConfig(parts=battle_parts, tracks=battle_tracks)).generate()
    export_multitrack_midi({k:v for k,v in battle_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Japanese_Battle.mid"), bpm=165)

    # 4. J-Rock / Visual Kei
    print("  [4/4] Generating J-Rock / Visual Kei Stomp...")
    jrock_tracks = [
        TrackConfig(
            name="Dist_Guitar_Gallop",
            generator=MelodyGenerator(mode="chord_tones", rhythm=get_rhythm("jrock_gallop")),
            instrument="overdriven_guitar", density=1.0, octave_shift=-1
        ),
        TrackConfig(
            name="Visual_Tremolo",
            generator=MelodyGenerator(mode="scale_walk", rhythm=get_rhythm("visual_kei_tremolo")),
            instrument="electric_guitar_clean", density=0.8
        ),
        TrackConfig(
            name="Heavy_Bass",
            generator=BassGenerator(style="root_fifth"),
            instrument="synth_bass", density=1.0, octave_shift=-1
        )
    ]
    jrock_parts = [IdeaPart(name="JRock", bars=8, scale=Scale(4, Mode.NATURAL_MINOR), tempo=180)]
    jrock_notes = IdeaTool(IdeaToolConfig(parts=jrock_parts, tracks=jrock_tracks, style="rock")).generate()
    export_multitrack_midi({k:v for k,v in jrock_notes.items() if not k.startswith("_")}, 
                           str(out_dir / "Japanese_JRock.mid"), bpm=180)

    print("\n  SUCCESS! Japanese style presets exported to:")
    print(f"  {out_dir.absolute()}/")
    print("================================================================================")

if __name__ == "__main__":
    run_demo()
