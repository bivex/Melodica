# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_witcher_contempt.py — "Time of Contempt: A Witcher Saga Symphony"
Inspired by Andrzej Sapkowski's fourth book.
Features Slavic folk elements, Imperial Nilfgaardian brass, and the tragic theme of Ciri.
Bar-aware: 4/4 via BarGrid.
"""

import random
from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode, BarGrid
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.orchestral_brass import (
    FrenchHornGenerator,
    TromboneGenerator,
)
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.snare_drum import SnareDrumGenerator
from melodica.generators.piano_comp import PianoCompGenerator


def generate_witcher_album():
    album_dir = Path("output/album_witcher_contempt")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        T I M E   O F   C O N T E M P T")
    print("        A Witcher Saga Symphony")
    print("=" * 80)

    # Full 7-track concept
    tracks_configs = [
        {
            "name": "01_Aplegatts_Ride",
            "tempo": 138,
            "scale": Scale(root=2, mode=Mode.DORIAN),
            "bars": 64,
            "description": "Fast, anxious path of the royal messenger. High-tension violins.",
            "style_hint": "frantic_strings",
            "progression_type": "coupled_hmm",
        },
        {
            "name": "02_Cintras_Legacy",
            "tempo": 68,
            "scale": Scale(root=2, mode=Mode.AEOLIAN),
            "bars": 48,
            "description": "Tragic theme for Ciri. Solo cello and breathy vocal.",
            "style_hint": "lyrical_tragedy",
            "progression_type": "coupled_hmm",
        },
        {
            "name": "03_The_Black_Wings",
            "tempo": 82,
            "scale": Scale(root=2, mode=Mode.PHRYGIAN),
            "bars": 56,
            "description": "Nilfgaardian theme. Heavy brass and industrial drones.",
            "style_hint": "imperial_industrial",
            "progression_type": "coupled_hmm",
        },
        {
            "name": "04_Thanedd_The_Coup",
            "tempo": 115,
            "scale": Scale(root=7, mode=Mode.LOCRIAN),
            "bars": 80,
            "description": "Magic betrayal. Dissonance, choir, and sharp hits.",
            "style_hint": "magic_chaos",
            "progression_type": "coupled_hmm",
        },
        {
            "name": "05_The_White_Wolf",
            "tempo": 142,
            "scale": Scale(root=2, mode=Mode.HARMONIC_MINOR),
            "bars": 72,
            "description": "Geralt's battle theme. Aggressive staccato and taiko.",
            "style_hint": "witcher_combat",
            "progression_type": "coupled_hmm",
        },
        {
            "name": "06_Falkas_Fire",
            "tempo": 62,
            "scale": Scale(root=4, mode=Mode.HUNGARIAN_MINOR),
            "bars": 48,
            "description": "Madness theme. Trembling vocal and dark pads.",
            "style_hint": "madness_folk",
            "progression_type": "coupled_hmm",
        },
        {
            "name": "07_The_Hour_of_Contempt",
            "tempo": 54,
            "scale": Scale(root=2, mode=Mode.PHRYGIAN),
            "bars": 64,
            "description": "Final requiem. Full orchestra, organ, and fading drone.",
            "style_hint": "epic_requiem",
            "progression_type": "coupled_hmm",
        },
    ]

    for cfg in tracks_configs:
        print(f"\n--- {cfg['name']} ---")
        print(f"  {cfg['description']}")

        parts = [
            IdeaPart(
                name=cfg["name"],
                bars=cfg["bars"],
                scale=cfg["scale"],
                tempo=cfg["tempo"],
                time_signature=(4, 4),
                progression_type=cfg.get("progression_type", "hmm3"),
            )
        ]

        # Dynamic track selection based on track intent
        track_list = []

        # 1. Foundation
        track_list.append(
            TrackConfig(
                name="Low Strings",
                generator=ContrabassGenerator(),
                instrument="contrabass",
                arrangement="AABB",
                density=0.8 if cfg["style_hint"] == "imperial_industrial" else 0.6,
                octave_shift=-2 if cfg["style_hint"] == "imperial_industrial" else -1,
            )
        )

        # 2. Percussion
        if cfg["style_hint"] == "witcher_combat":
            track_list.append(
                TrackConfig(
                    name="Taiko Drums",
                    generator=TimpaniGenerator(),
                    instrument="taiko",
                    arrangement="ABAB",
                    density=0.8,
                )
            )
        else:
            track_list.append(
                TrackConfig(
                    name="Orchestral Perc",
                    generator=TimpaniGenerator(),
                    instrument="timpani",
                    arrangement="ABAB",
                    density=0.5,
                )
            )

        if cfg["style_hint"] in ["frantic_strings", "witcher_combat"]:
            # Reduced density to fix register masking and blur
            track_list.append(
                TrackConfig(
                    name="Military Snare",
                    generator=SnareDrumGenerator(pattern_type="march"),
                    instrument="drums",
                    arrangement="AABB",
                    density=0.5,
                )
            )

        # 3. Melodic layers
        if cfg["style_hint"] == "lyrical_tragedy":
            track_list.append(
                TrackConfig(
                    name="Solo Cello",
                    generator=CelloGenerator(),
                    instrument="cello",
                    arrangement="ABCD",
                    density=0.5,
                    mpe=True,
                )
            )

        if cfg["style_hint"] == "frantic_strings":
            track_list.append(
                TrackConfig(
                    name="Fast Violins",
                    generator=ViolinGenerator(),
                    instrument="violin",
                    arrangement="AABC",
                    density=0.8,
                )
            )
        else:
            track_list.append(
                TrackConfig(
                    name="Violins Ensemble",
                    generator=ViolinGenerator(),
                    instrument="violin",
                    arrangement="AABC",
                    density=0.6,
                )
            )

        # 4. Brass & Choir
        if cfg["style_hint"] == "imperial_industrial":
            # Reduced density to fix rhythmic blur in low brass
            track_list.append(
                TrackConfig(
                    name="Cimbasso Heavy",
                    generator=BrassSectionGenerator(),
                    instrument="tuba",
                    arrangement="AABB",
                    density=0.5,
                    octave_shift=-1,
                )
            )
            track_list.append(
                TrackConfig(
                    name="Imperial Trombones",
                    generator=TromboneGenerator(),
                    instrument="trombone",
                    arrangement="AABB",
                    density=0.6,
                )
            )
        elif cfg["style_hint"] == "epic_requiem":
            track_list.append(
                TrackConfig(
                    name="Brass Majesty",
                    generator=BrassSectionGenerator(),
                    instrument="brass",
                    arrangement="AABC",
                    density=0.7,
                )
            )
            track_list.append(
                TrackConfig(
                    name="Cathedral Organ",
                    generator=PianoCompGenerator(),
                    instrument="organ",
                    arrangement="AAAA",
                    density=0.5,
                )
            )
        else:
            track_list.append(
                TrackConfig(
                    name="French Horns",
                    generator=FrenchHornGenerator(),
                    instrument="french_horn",
                    arrangement="AABC",
                    density=0.4,
                )
            )

        if cfg["style_hint"] in ["magic_chaos", "epic_requiem"]:
            track_list.append(
                TrackConfig(
                    name="Prophecy Choir",
                    generator=ChoirAahsGenerator(),
                    instrument="choir",
                    arrangement="ABCD",
                    density=0.6,
                    mpe=True,
                )
            )

        # 5. Specialized (Vocals, Industrial)
        if cfg["style_hint"] in ["lyrical_tragedy", "madness_folk"]:
            track_list.append(
                TrackConfig(
                    name="Vocal Lead",
                    generator=MelodyGenerator(
                        phrase_length=8.0,
                        phrase_rest_probability=0.5,
                        ornament_probability=0.4,
                        # Capping range to fix Brightness Overload (C3-C5 range roughly)
                        note_range_low=55,
                        note_range_high=82,
                    ),
                    instrument="voice",
                    arrangement="ABCD",
                    density=0.35,
                    mpe=True,
                )
            )

        if cfg["style_hint"] == "imperial_industrial":
            # Lower density for drones to prevent frequency masking
            track_list.append(
                TrackConfig(
                    name="War Drones",
                    generator=DroneGenerator(),
                    instrument="synth_pad",
                    arrangement="AAAA",
                    density=0.7,
                    octave_shift=-2,
                )
            )
        elif cfg["style_hint"] == "magic_chaos":
            track_list.append(
                TrackConfig(
                    name="Dissonant Magic",
                    generator=DroneGenerator(),
                    instrument="synth_fx",
                    arrangement="ABCD",
                    density=0.6,
                )
            )
            track_list.append(
                TrackConfig(
                    name="Magic Impacts",
                    generator=FXImpactGenerator(),
                    instrument="percussion",
                    arrangement="ABCD",
                    density=0.5,
                )
            )

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=(4, 4),
            workflow="generate_all",
            use_tension_curve=True,
            use_voice_leading=True,
            use_texture_control=True,
            use_mixing=True,
            use_mastering=True,
            target_lufs=-12.0,
            parts=parts,
            tracks=track_list,
        )

        # Get explicit GM instrument mapping for high-fidelity playback
        from melodica.idea_tool import _GM_PROGRAMS

        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        # Generate with the tool
        notes_dict = IdeaTool(tool_config).generate()

        # Filter tracks and export
        tracks_data = {
            k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)
        }

        export_multitrack_midi(
            tracks_data,
            str(album_dir / f"{cfg['name']}.mid"),
            bpm=cfg["tempo"],
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )

        note_count = sum(len(n) for n in tracks_data.values())
        print(f"    Exported {cfg['name']}.mid ({note_count} notes)")

    print("\n" + "=" * 80)
    print(f"  ALBUM COMPLETE: Time of Contempt")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    with EngineTracer(max_depth=1, use_colors=True):
        generate_witcher_album()
