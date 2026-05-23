# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/battle_dust.py — "Battle Dust: Doomed Survival Symphony"
A massive 8-minute industrial/orchestral hybrid track.
Features dynamic Tempo Maps, Scale Modulations (Aeolian, Phrygian, Locrian),
and a mix of cinematic textures, military marches, and intimate laments.
"""

from pathlib import Path

from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import (
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
)
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.orchestral_brass import (
    FrenchHornGenerator,
    TrumpetGenerator,
    TromboneGenerator,
)
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.woodwinds_ensemble import WoodwindsEnsembleGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.horror_dissonance import HorrorDissonanceGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.combat_escalation import CombatEscalationGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.melody import MelodyGenerator


# ---------------------------------------------------------------------------
# Track Builder
# ---------------------------------------------------------------------------

def generate_battle_dust():
    """
    Battle Dust / Боевая пыль
    D-moll, Phrygian, Locrian shades.
    """
    print("  -> Generating: Battle Dust")

    parts = [
        # I. Nashville Opens Fire (0:00 - 1:10) - 70s @ 68 BPM -> ~20 bars
        IdeaPart(name="Nashville Opens Fire", bars=20, scale=Scale(root=2, mode=Mode.AEOLIAN), tempo=68),
        
        # II. S.Y.A. (1:10 - 2:20) - 70s @ 112 BPM -> ~32 bars
        IdeaPart(name="Save Your Ass", bars=32, scale=Scale(root=2, mode=Mode.PHRYGIAN), tempo=112),
        
        # III. Mirror Troopers (2:20 - 4:00) - 100s @ 148 BPM -> ~62 bars
        IdeaPart(name="Mirror Troopers", bars=62, scale=Scale(root=2, mode=Mode.LOCRIAN), tempo=148),
        
        # IV. Shiobhan (4:00 - 5:40) - 100s @ 80 BPM -> ~33 bars
        IdeaPart(name="Shiobhan", bars=33, scale=Scale(root=2, mode=Mode.AEOLIAN), tempo=80),
        
        # V. Ishogi Maru (5:40 - 6:50) - 70s @ 100 BPM -> ~29 bars
        IdeaPart(name="Ishogi Maru", bars=29, scale=Scale(root=2, mode=Mode.PHRYGIAN), tempo=100),
        
        # VI. Promise (6:50 - End) - 90s @ 54 BPM -> ~20 bars
        IdeaPart(name="Promise", bars=20, scale=Scale(root=2, mode=Mode.AEOLIAN), tempo=54),
    ]

    config = IdeaToolConfig(
        style="cinematic_hybrid",
        workflow="generate_all",
        use_tension_curve=True,
        use_voice_leading=True,
        use_texture_control=True,
        use_mixing=True,
        use_mastering=True,
        target_lufs=-12.0,
        progression_type="hmm3",
        parts=parts,
        tracks=[
            # Hybrid / Sound Design Layer
            TrackConfig(
                name="Industrial Drones",
                generator=DroneGenerator(),
                instrument="synth_pad",
                arrangement="AAAA",
                density=0.9,
                octave_shift=-2,
            ),
            TrackConfig(
                name="Metallic Impacts",
                generator=FXImpactGenerator(),
                instrument="percussion",
                arrangement="ABCD",
                density=0.6,
                variations=["humanize"],
            ),
            TrackConfig(
                name="Radio Chatter",
                generator=SciFiUnderscoreGenerator(),
                instrument="synth_fx",
                arrangement="AABB",
                density=0.4,
                rhythm_rests=0.8,
            ),
            TrackConfig(
                name="Industrial Percussion",
                generator=ElectronicDrumsGenerator(kit="industrial"),
                instrument="drums",
                arrangement="AABB",
                density=0.8,
            ),
            
            # Orchestral Layer - Strings
            TrackConfig(
                name="Violins I",
                generator=ViolinGenerator(),
                instrument="violin",
                arrangement="AABC",
                density=0.7,
                mpe=True,
            ),
            TrackConfig(
                name="Violas Ostinato",
                generator=OstinatoGenerator(pattern="driving"),
                instrument="viola",
                arrangement="ABAB",
                density=0.9,
            ),
            TrackConfig(
                name="Cello Solo",
                generator=CelloGenerator(),
                instrument="cello",
                arrangement="ABCD",
                density=0.6,
                mpe=True,
            ),
            TrackConfig(
                name="Contrabass Sub",
                generator=ContrabassGenerator(),
                instrument="contrabass",
                arrangement="AABB",
                density=1.0,
                octave_shift=-1,
            ),
            
            # Orchestral Layer - Brass
            TrackConfig(
                name="French Horns",
                generator=FrenchHornGenerator(),
                instrument="french_horn",
                arrangement="AABB",
                density=0.7,
            ),
            TrackConfig(
                name="Trombone Section",
                generator=TromboneGenerator(),
                instrument="trombone",
                arrangement="AABB",
                density=0.8,
                octave_shift=-1,
            ),
            TrackConfig(
                name="Cimbasso Low",
                generator=BrassSectionGenerator(),
                instrument="tuba",
                arrangement="AABB",
                density=0.9,
                octave_shift=-1,
            ),

            # Percussion Layer
            TrackConfig(
                name="Taiko Ensemble",
                generator=TimpaniGenerator(),
                instrument="taiko",
                arrangement="ABAB",
                density=0.8,
            ),
            
            # Vocal Layer
            TrackConfig(
                name="Choir Epic",
                generator=ChoirAahsGenerator(),
                instrument="choir",
                arrangement="AABC",
                density=0.6,
                mpe=True,
            ),
            TrackConfig(
                name="Female Solo",
                generator=MelodyGenerator(
                    phrase_length=8.0,
                    phrase_rest_probability=0.4,
                    syncopation=0.3,
                    ornament_probability=0.3,
                ),
                instrument="voice",
                arrangement="ABCD",
                density=0.4,
                mpe=True,
            ),

            # Piano / Ambient
            TrackConfig(
                name="Piano Felt",
                generator=PianoCompGenerator(),
                instrument="piano",
                arrangement="AABB",
                density=0.5,
            ),
            TrackConfig(
                name="Tinnitus Tone",
                generator=SciFiUnderscoreGenerator(),
                instrument="synth_fx",
                arrangement="A",
                density=0.1,
                octave_shift=4, # High pitch
            ),
        ],
    )

    return IdeaTool(config).generate(), parts


# ---------------------------------------------------------------------------
# Main Builder
# ---------------------------------------------------------------------------

def main():
    output_dir = Path("output/album_battle_dust")
    output_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("        B A T T L E   D U S T   /   Б О Е В А Я   П Ы Л Ь")
    print("        Doomed Survival Symphony")
    print("=" * 80)

    filename = "Battle_Dust_Symphony.mid"
    time_signature = (4, 4)

    with EngineTracer(show_private=False, show_duration=True, max_depth=2, use_colors=True):
        print("-" * 80)
        notes_dict, parts_config = generate_battle_dust()

        # Construct Tempo Map for automation
        tempo_map = []
        current_beat = 0.0
        for p in parts_config:
            tempo_map.append((current_beat, p.tempo))
            current_beat += p.bars * time_signature[0]

        # Filter out non-track keys
        tracks_data = {
            k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)
        }

        # Extract CC automation events
        cc_events = notes_dict.get("_cc_events", {})
        
        # Add custom tinnitus silence automation (conceptual for now)
        # In a real scenario, we'd inject silence or CC volume drops at specific beat offsets
        
        # Extract MPE track names
        mpe_tracks = notes_dict.get("_mpe_tracks", set())

        # Export with tempo automation and CC events!
        export_multitrack_midi(
            tracks_data,
            str(output_dir / filename),
            bpm=parts_config[0].tempo,  # Base BPM
            tempo_events=tempo_map,
            cc_events=cc_events,
            mpe_tracks=mpe_tracks,
        )

        # Count notes
        note_count = sum(len(n) for k, n in tracks_data.items())
        print(f"    Exported {filename}")
        print(f"      - Notes: {note_count}")
        print(f"      - Tempo Map: {', '.join(f'{bpm}bpm@{beat}b' for beat, bpm in tempo_map)}")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Battle Dust Symphony — {note_count} total notes")
    print(f"  Output folder: {output_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
