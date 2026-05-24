# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_prince_of_persia.py — "Prince of Persia: Sands of Destiny"
Cinematic Arabic Sikah hybrid — adventure score.
Ethnic soloists + orchestral power + mystical atmosphere + heroic-tragic drive.

Track 1: Sands of Time      — mysterious intro, drone, distant ney
Track 2: The Prince's Theme  — heroic lyricism, duduk, qanun, strings
Track 3: Palace Pursuit      — 7/8 action, taiko, ostinato, brass stabs
Track 4: Hidden Sanctum      — ethereal breakdown, choir, crystal FX
Track 5: Destiny and Sand    — full orchestra climax, choir fortissimo, dissolve
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


def generate_prince_of_persia():
    album_dir = Path("output/album_prince_of_persia")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("  P R I N C E   O F   P E R S I A  :  S A N D S   O F   D E S T I N Y")
    print("  Cinematic Arabic Sikah  —  Adventure Score")
    print("=" * 80)

    sikah = Scale(root=4, mode=Mode.ARABIC_SIKAH)

    configs = [
        {"name": "01_Sands_of_Time",    "tempo": 72,  "ts": (4, 4), "bars": 52},
        {"name": "02_The_Princes_Theme", "tempo": 88,  "ts": (4, 4), "bars": 56},
        {"name": "03_Palace_Pursuit",    "tempo": 120, "ts": (7, 8), "bars": 48},
        {"name": "04_Hidden_Sanctum",    "tempo": 64,  "ts": (4, 4), "bars": 48},
        {"name": "05_Destiny_and_Sand",  "tempo": 108, "ts": (4, 4), "bars": 64},
    ]

    # ── 01: Sands of Time — mysterious intro ─────────────────────────────
    # Drone on E. Distant ney over reversed-cymbal texture.
    # Low choir whispers. Kalimba like falling sand grains.
    # Vibraphone halos. Sub bass pedal.
    tracks_map = {
        "01_Sands_of_Time": [
            TrackConfig(name="Desert_Drone",     generator=DroneGenerator(variant="tonic", fade_in=6.0, fade_out=4.0), instrument="dark_pad", density=0.9, octave_shift=-1),
            TrackConfig(name="Distant_Ney",      generator=WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True), instrument="shakuhachi", density=0.3, mpe=True),
            TrackConfig(name="Sand_Grains",      generator=VibraphoneGenerator(note_density=0.2), instrument="vibraphone", density=0.25),
            TrackConfig(name="Sub_Pedal",        generator=PedalBassGenerator(pedal_note="root", sustain=0.9, velocity_level=0.7), instrument="contrabass", density=0.7),
            TrackConfig(name="Choir_Whispers",   generator=ChoirAahsGenerator(voice_count=4, dynamics="pp", syllable="aah", vibrato=0.15), instrument="choir", density=0.25),
            TrackConfig(name="Cymbal_Swell",     generator=OrchestralCymbalGenerator(pattern_type="crash"), instrument="synth_fx", density=0.1),
        ],

        # ── 02: The Prince's Theme — heroic lyricism ─────────────────────
        # Solo duduk carries the melody. Qanun ornaments behind.
        # Sustained strings swell. Harp arpeggios. Gentle frame drum.
        # French horn enters in second half for nobility.
        "02_The_Princes_Theme": [
            TrackConfig(name="Duduk_Melody",    generator=MelodyGenerator(phrase_length=8.0, mode="downbeat_chord", random_movement=0.2, climax="up_5th", direction_bias=0.15), instrument="shakuhachi", density=0.5, mpe=True),
            TrackConfig(name="Qanun_Ornaments", generator=EthnicPluckedGenerator(instrument="sitar", note_density=0.8), instrument="sitar", density=0.4, mpe=True),
            TrackConfig(name="String_Swell",    generator=StringsEnsembleGenerator(section_size="full", articulation="sustained", dynamic_curve="crescendo", divisi=4), instrument="strings", density=0.5),
            TrackConfig(name="Harp_Cascade",    generator=HarpGenerator(), instrument="harp", density=0.35),
            TrackConfig(name="Frame_Drum",      generator=PercussionEnsembleGenerator(density=0.5, polyrhythm_ratio="3x2"), instrument="steel_drums", density=0.4),
            TrackConfig(name="Noble_Horn",      generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell"), instrument="french_horn", density=0.3),
        ],

        # ── 03: Palace Pursuit — 7/8 action chase ────────────────────────
        # Asymmetric 7/8 groove. Taiko thunder. String ostinato pizzicato.
        # Trombone threats. Oud drives. Darbuka at double speed.
        # Impact hits on downbeats. Bass octave movement.
        "03_Palace_Pursuit": [
            TrackConfig(name="Taiko_Thunder",   generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="taiko", density=0.8),
            TrackConfig(name="Ostinato_Strings", generator=StringsPizzicatoGenerator(pattern="ostinato", staccato_length=0.12, velocity_variation=0.4), instrument="pizzicato", density=0.7),
            TrackConfig(name="Oud_Drive",       generator=EthnicWorldGenerator(instrument="shamisen"), instrument="shamisen", density=0.65, mpe=True),
            TrackConfig(name="Trombone_Threat", generator=TromboneGenerator(articulation="staccato", register=1, bass_voice=True), instrument="trombone", density=0.4),
            TrackConfig(name="Action_Bass",     generator=BassGenerator(style="root_only", global_movement="up_down"), instrument="bass", density=0.6),
            TrackConfig(name="Impact_Hits",     generator=FXImpactGenerator(impact_type="boom", tail_length=1.5, pitch_drop=7, placement="downbeat"), instrument="orchestra_hit", density=0.15),
        ],

        # ── 04: Hidden Sanctum — ethereal breakdown ──────────────────────
        # Solo ney floats. Crystal FX shimmer. Female choir as air.
        # Ambient pad spread wide. Cello sustains a single tone.
        # Almost nothing — space and silence.
        "04_Hidden_Sanctum": [
            TrackConfig(name="Sanctum_Pad",     generator=AmbientPadGenerator(voicing="spread", overlap=0.4), instrument="dark_pad", density=0.8, octave_shift=-1),
            TrackConfig(name="Ney_Float",       generator=WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True), instrument="shakuhachi", density=0.3, mpe=True),
            TrackConfig(name="Crystal_Shimmer", generator=SynthEffectsGenerator(fx_type="crystal"), instrument="synth_fx", density=0.2),
            TrackConfig(name="Cello_Drone",     generator=CelloGenerator(articulation="sustained", vibrato=True), instrument="cello", density=0.25),
            TrackConfig(name="Airy_Choir",      generator=VocalOohsGenerator(syllable="ooh", harmony_count=3, vibrato=0.5, breath_phasing=True), instrument="voice", density=0.2),
        ],

        # ── 05: Destiny and Sand — full orchestra climax ──────────────────
        # Tremolo strings build tension. Full choir fortissimo.
        # Horns + violins double the melody. Darbuka accelerates.
        # French horns for heroism. Low trombones for doom.
        # Final dissolving — drone fades to nothing.
        "05_Destiny_and_Sand": [
            TrackConfig(name="Tremolo_Build",   generator=TremoloStringsGenerator(variant="chord", dynamic_swell=True, attack_time=0.4, decay_time=0.6), instrument="tremolo_strings", density=0.6),
            TrackConfig(name="Heroic_Horns",    generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="crescendo", fanfare_mode=False), instrument="french_horn", density=0.45),
            TrackConfig(name="Doom_Trombones",  generator=TromboneGenerator(articulation="sustained", register=1, bass_voice=True), instrument="trombone", density=0.35),
            TrackConfig(name="Final_Duduk",     generator=MelodyGenerator(phrase_length=8.0, mode="downbeat_chord", random_movement=0.15, climax="up_5th", direction_bias=0.1), instrument="shakuhachi", density=0.45, mpe=True),
            TrackConfig(name="Choir_Fortissimo", generator=ChoirAahsGenerator(voice_count=4, dynamics="f", syllable="aah", vibrato=0.4), instrument="choir", density=0.4),
            TrackConfig(name="War_Perucssion",  generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="taiko", density=0.7),
            TrackConfig(name="Fade_Drone",      generator=DroneGenerator(variant="tonic", fade_in=2.0, fade_out=8.0), instrument="dark_pad", density=0.8, octave_shift=-1),
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
        print(f"    Exported {cfg['name']}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: PRINCE OF PERSIA — SANDS OF DESTINY")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_prince_of_persia()
