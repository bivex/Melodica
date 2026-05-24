# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_tandumi_ruins.py — "Sikhs in the Ruins of Tandumi"
Epic Sikh warrior saga — ancient ruins, fallen glory, undying resolve.

Sikah maqam as spiritual core (E half-flat), blended with Punjabi warrior
energy and the weight of crumbling stone temples.

Track 1: The Ruins Breathe       — desolate intro, ruined bells, drone winds
Track 2: Warriors of the Khalsa  — martial Bhangra-driven heroic theme
Track 3: The Temple Falls        — brutal 5/4 battle, taiko + brass + chaos
Track 4: Requiem of the Fallen   — grief elegy, sarangi solo, string lament
Track 5: Undying Light           — full orchestral resurrection, choir triumph
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.plucked_solo import EthnicPluckedGenerator
from melodica.generators.wind_brass_solo import WoodwindSoloGenerator
from melodica.generators.chromatic_percussion import VibraphoneGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.synth_effects import SynthEffectsGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.percussion_ensemble import PercussionEnsembleGenerator
from melodica.generators.ethnic_world import EthnicWorldGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
from melodica.generators.tubular_bells import TubularBellsGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator


def generate_tandumi_ruins():
    album_dir = Path("output/album_tandumi_ruins")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("  С И К Х И   В   Р У И Н А Х   Т А Н Д У М И")
    print("  SIKHS IN THE RUINS OF TANDUMI  —  Epic Warrior Saga")
    print("  Scale: Arabic Sikah (E½♭)  |  Punjabi Soul × Orchestral Power")
    print("=" * 80)

    # Sikah — духовная основа, та же что в Prince of Persia,
    # но интерпретируем её через призму сикхской воинской традиции
    sikah = Scale(root=4, mode=Mode.ARABIC_SIKAH)

    configs = [
        {"name": "01_The_Ruins_Breathe",      "tempo": 58,  "ts": (4, 4), "bars": 48},
        {"name": "02_Warriors_of_the_Khalsa", "tempo": 104, "ts": (4, 4), "bars": 60},
        {"name": "03_The_Temple_Falls",        "tempo": 132, "ts": (5, 4), "bars": 52},
        {"name": "04_Requiem_of_the_Fallen",   "tempo": 66,  "ts": (3, 4), "bars": 56},
        {"name": "05_Undying_Light",           "tempo": 96,  "ts": (4, 4), "bars": 72},
    ]

    tracks_map = {

        # ── 01: The Ruins Breathe — desolate opening ─────────────────────
        # The ruins of Tandumi. Wind through cracked stone.
        # Tubular bells echo in empty corridors.
        # Sub-bass rumble of collapsed columns. Distant choir whisper.
        # No pulse — only stillness and memory.
        "01_The_Ruins_Breathe": [
            TrackConfig(
                name="Ruin_Drone",
                generator=DroneGenerator(variant="fifth", fade_in=8.0, fade_out=6.0),
                instrument="dark_pad", density=0.85, octave_shift=-2,
            ),
            TrackConfig(
                name="Stone_Bells",
                generator=TubularBellsGenerator(stroke_pattern="single", dampen=True),
                instrument="tubular_bells", density=0.18, octave_shift=1,
            ),
            TrackConfig(
                name="Wind_Through_Ruins",
                generator=WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True),
                instrument="shakuhachi", density=0.22, octave_shift=0, mpe=True,
            ),
            TrackConfig(
                name="Deep_Rumble",
                generator=PedalBassGenerator(pedal_note="root", sustain=0.95, velocity_level=0.85),
                instrument="contrabass", density=0.65, octave_shift=-2,
            ),
            TrackConfig(
                name="Ghost_Choir",
                generator=VocalOohsGenerator(syllable="ooh", harmony_count=3, vibrato=0.3, breath_phasing=True),
                instrument="voice", density=0.18,
            ),
            TrackConfig(
                name="Ruin_Shimmer",
                generator=SynthEffectsGenerator(fx_type="crystal"),
                instrument="synth_fx", density=0.12, octave_shift=2,
            ),
        ],

        # ── 02: Warriors of the Khalsa — martial heroic theme ────────────
        # The Sikh warriors emerge from the dust.
        # Dhol-driven pulse. Sarangi-style solo over fierce strings.
        # Brass stabs signal battle readiness.
        # Heroic but weighted — they fight knowing the temple is already lost.
        "02_Warriors_of_the_Khalsa": [
            TrackConfig(
                name="Warrior_Melody",
                generator=MelodyGenerator(
                    phrase_length=8.0, mode="downbeat_chord",
                    random_movement=0.25, climax="up_5th", direction_bias=0.2,
                ),
                instrument="shakuhachi", density=0.55, octave_shift=2, mpe=True,
            ),
            TrackConfig(
                name="Dhol_Pulse",
                generator=ElectronicDrumsGenerator(kit="ethnic"),
                instrument="taiko", density=0.75,
            ),
            TrackConfig(
                name="String_Power",
                generator=StringsEnsembleGenerator(
                    section_size="full", articulation="marcato",
                    dynamic_curve="crescendo", divisi=4,
                ),
                instrument="strings", density=0.6,
            ),
            TrackConfig(
                name="Sitar_Counter",
                generator=EthnicPluckedGenerator(instrument="sitar", note_density=0.7),
                instrument="sitar", density=0.45, octave_shift=1, mpe=True,
            ),
            TrackConfig(
                name="Brass_Stabs",
                generator=BrassSectionGenerator(
                    voicing="closed", articulation="sforzando", intensity=0.9,
                ),
                instrument="french_horn", density=0.35, octave_shift=-1,
            ),
            TrackConfig(
                name="Battle_Bass",
                generator=BassGenerator(style="root_fifth", global_movement="up_down"),
                instrument="bass", density=0.65, octave_shift=-2,
            ),
            TrackConfig(
                name="Warrior_Choir",
                generator=ChoirAahsGenerator(voice_count=4, dynamics="mf", syllable="aah", vibrato=0.25),
                instrument="choir", density=0.3,
            ),
        ],

        # ── 03: The Temple Falls — brutal 5/4 battle chaos ───────────────
        # Asymmetric 5/4 — the rhythm of collapse.
        # Taiko thunder. Ostinato strings like falling stones.
        # Low trombone doom. Brass fanfare cut short by chaos.
        # Shrill piccolo shrieks over the destruction.
        "03_The_Temple_Falls": [
            TrackConfig(
                name="Chaos_Taiko",
                generator=ElectronicDrumsGenerator(kit="ethnic"),
                instrument="taiko", density=0.88, octave_shift=-2,
            ),
            TrackConfig(
                name="Falling_Stones",
                generator=StringsPizzicatoGenerator(
                    pattern="ostinato", staccato_length=0.10, velocity_variation=0.5,
                ),
                instrument="pizzicato", density=0.75,
            ),
            TrackConfig(
                name="Doom_Bass",
                generator=TromboneGenerator(articulation="staccato", register=1, bass_voice=True),
                instrument="trombone", density=0.5, octave_shift=-2,
            ),
            TrackConfig(
                name="Collapse_Brass",
                generator=FrenchHornGenerator(articulation="sforzando", dynamic_curve="crescendo"),
                instrument="french_horn", density=0.45, octave_shift=-1,
            ),
            TrackConfig(
                name="Ostinato_Low",
                generator=OstinatoGenerator(pattern="1-5-1-5"),
                instrument="contrabass", density=0.7, octave_shift=-2,
            ),
            TrackConfig(
                name="Shriek_High",
                generator=WoodwindSoloGenerator(instrument="piccolo", breath_vibrato=False),
                instrument="shakuhachi", density=0.38, octave_shift=2, mpe=True,
            ),
            TrackConfig(
                name="Impact_Crashes",
                generator=FXImpactGenerator(impact_type="boom", tail_length=2.0, pitch_drop=12, placement="downbeat"),
                instrument="orchestra_hit", density=0.18,
            ),
            TrackConfig(
                name="Timpani_Crash",
                generator=TimpaniGenerator(),
                instrument="taiko", density=0.4, octave_shift=-1,
            ),
        ],

        # ── 04: Requiem of the Fallen — grief elegy ───────────────────────
        # After the battle. The temple is rubble.
        # Slow 3/4 — a funeral waltz of sorts.
        # Solo melody (sarangi-like) weeps over sustained strings.
        # Cello carries the lowest grief. Harp drops single tears.
        # Quiet choir hums. Nothing loud. Just loss.
        "04_Requiem_of_the_Fallen": [
            TrackConfig(
                name="Grief_Melody",
                generator=MelodyGenerator(
                    phrase_length=12.0, mode="downbeat_chord",
                    random_movement=0.1, climax="none", direction_bias=-0.2,
                ),
                instrument="shakuhachi", density=0.42, octave_shift=0, mpe=True,
            ),
            TrackConfig(
                name="String_Lament",
                generator=StringsLegatoGenerator(
                    dynamic_shape="diminuendo", vibrato_amount=0.6,
                ),
                instrument="strings", density=0.5,
            ),
            TrackConfig(
                name="Cello_Grief",
                generator=CelloGenerator(articulation="sustained", vibrato=True),
                instrument="cello", density=0.4, octave_shift=-2,
            ),
            TrackConfig(
                name="Contrabass_Ground",
                generator=PedalBassGenerator(pedal_note="root", sustain=0.95, velocity_level=0.85),
                instrument="contrabass", density=0.7, octave_shift=-2,
            ),
            TrackConfig(
                name="Sorrow_Pizzicato",
                generator=StringsPizzicatoGenerator(pattern="ostinato", staccato_length=0.15, velocity_variation=0.3),
                instrument="pizzicato", density=0.35, octave_shift=-2,
            ),
            TrackConfig(
                name="Funeral_Timpani",
                generator=TimpaniGenerator(),
                instrument="taiko", density=0.5, octave_shift=-1,
            ),
            TrackConfig(
                name="Harp_Tears",
                generator=HarpGenerator(),
                instrument="harp", density=0.25, octave_shift=0,
            ),
            TrackConfig(
                name="Mourning_Choir",
                generator=VocalOohsGenerator(syllable="mm", harmony_count=4, vibrato=0.6, breath_phasing=True),
                instrument="choir", density=0.22,
            ),
            TrackConfig(
                name="Requiem_Pad",
                generator=AmbientPadGenerator(voicing="close", overlap=0.5),
                instrument="dark_pad", density=0.45, octave_shift=-2,
            ),
        ],

        # ── 05: Undying Light — resurrection triumph ──────────────────────
        # The Khalsa does not die. From the ashes.
        # Full orchestra swells. Tremolo strings build to breaking point.
        # Choir sings fortissimo. Horns of glory.
        # Dhol pounds. Sitar sings the Sikah theme one final time.
        # Bells ring. The light is undying.
        "05_Undying_Light": [
            TrackConfig(
                name="Tremolo_Rise",
                generator=TremoloStringsGenerator(
                    variant="single", dynamic_swell=True, attack_time=0.5, decay_time=1.5, bow_speed=0.2,
                ),
                instrument="tremolo_strings", density=0.12, octave_shift=-1,
            ),
            TrackConfig(
                name="Glory_Horns",
                generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="crescendo", fanfare_mode=False),
                instrument="french_horn", density=0.5, octave_shift=0,
            ),
            TrackConfig(
                name="Victory_Trombones",
                generator=TromboneGenerator(articulation="sustained", register=1, bass_voice=False),
                instrument="trombone", density=0.4, octave_shift=0,
            ),
            TrackConfig(
                name="Final_Sitar",
                generator=EthnicPluckedGenerator(instrument="sitar", note_density=0.6),
                instrument="sitar", density=0.5, octave_shift=2, mpe=True,
            ),
            TrackConfig(
                name="Triumph_Choir",
                generator=ChoirAahsGenerator(voice_count=6, dynamics="ff", syllable="aah", vibrato=0.5),
                instrument="choir", density=0.5, octave_shift=2,
            ),
            TrackConfig(
                name="Resurrection_Dhol",
                generator=ElectronicDrumsGenerator(kit="ethnic"),
                instrument="taiko", density=0.72, octave_shift=-1,
            ),
            TrackConfig(
                name="Victory_Bells",
                generator=TubularBellsGenerator(stroke_pattern="single", dampen=False),
                instrument="tubular_bells", density=0.3, octave_shift=2,
            ),
            TrackConfig(
                name="Bass_Foundation",
                generator=PedalBassGenerator(pedal_note="root", sustain=0.75, velocity_level=0.85),
                instrument="contrabass", density=0.7, octave_shift=-2,
            ),
            TrackConfig(
                name="Light_Drone",
                generator=DroneGenerator(variant="tonic", fade_in=4.0, fade_out=10.0),
                instrument="dark_pad", density=0.75, octave_shift=-2,
            ),
        ],
    }

    for cfg in configs:
        print(f"\n--- Composing: {cfg['name']} ({cfg['ts'][0]}/{cfg['ts'][1]}, {cfg['tempo']} BPM) ---")

        parts = [IdeaPart(
            name=cfg["name"], bars=cfg["bars"],
            scale=sikah, tempo=cfg["tempo"],
            time_signature=cfg["ts"],
            progression_type="coupled_hmm",
        )]

        track_list = tracks_map[cfg["name"]]
        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=cfg["ts"],
            use_tension_curve=True,
            use_harmonic_verifier=True,
            parts=parts,
            tracks=track_list,
        )

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

        export_multitrack_midi(
            tracks_data, str(album_dir / f"{cfg['name']}.mid"),
            bpm=cfg["tempo"], key=sikah,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )
        print(f"    ✓ Exported {cfg['name']}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: SIKHS IN THE RUINS OF TANDUMI")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_tandumi_ruins()
