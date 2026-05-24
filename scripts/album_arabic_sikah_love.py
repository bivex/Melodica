# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_arabic_sikah_love.py — "Arabic Sikah: Love & Longing (الحب والشوق)"
A microtonal love album on the Arabic Sikah scale.
Emotional arc: Yearning → First Glance → Passion → Separation → Reunion.
Mixed time signatures. CoupledHMM progressions.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

from melodica.generators.orchestral_strings import (
    ViolinGenerator, ViolaGenerator, CelloGenerator, ContrabassGenerator,
)
from melodica.generators.orchestral_brass import FrenchHornGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator, OboeGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.plucked_solo import PianoSoloGenerator, EthnicPluckedGenerator
from melodica.generators.chromatic_percussion import VibraphoneGenerator, CelestaGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ethnic_world import EthnicWorldGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.wind_brass_solo import WoodwindSoloGenerator
from melodica.generators.ambient import AmbientPadGenerator


def generate_arabic_sikah_love():
    album_dir = Path("output/album_arabic_sikah_love")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("    A R A B I C   S I K A H   :   L O V E   &   L O N G I N G")
    print("    الحب والشوق  —  A Microtonal Love Story")
    print("=" * 80)

    sikah_scale = Scale(root=4, mode=Mode.ARABIC_SIKAH)

    tracks_configs = [
        {"name": "01_Yearning",     "tempo": 72,  "ts": (4, 4), "bars": 52},
        {"name": "02_First_Glance", "tempo": 88,  "ts": (6, 8), "bars": 48},
        {"name": "03_Passions_Fire", "tempo": 116, "ts": (4, 4), "bars": 44},
        {"name": "04_Separation",   "tempo": 60,  "ts": (3, 4), "bars": 56},
        {"name": "05_Reunion",      "tempo": 100, "ts": (6, 8), "bars": 48},
    ]

    # ── 01: Yearning (شوق) — the ache of distant love ────────────────────
    # Key: D Sikah. Sparse, spacious. Long sustains, microtonal bends.
    # Oud weeps over a pedal drone. Vibraphone halos. Cello aches below.
    tracks_map = {
        "01_Yearning": [
            TrackConfig(name="Longing_Drone",   generator=AmbientPadGenerator(voicing="spread"), instrument="dark_pad", density=0.85, octave_shift=-1),
            TrackConfig(name="Weeping_Oud",     generator=EthnicWorldGenerator(instrument="shamisen"), instrument="shamisen", density=0.5, mpe=True),
            TrackConfig(name="Aching_Cello",    generator=CelloGenerator(articulation="sustained", vibrato=True), instrument="cello", density=0.35),
            TrackConfig(name="Vibraphone_Halo", generator=VibraphoneGenerator(note_density=0.3), instrument="vibraphone", density=0.3),
            TrackConfig(name="Breath_Texture",  generator=WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True), instrument="shakuhachi", density=0.25, mpe=True),
        ],

        # ── 02: First Glance (لمحة) — eyes meeting across a courtyard ───
        # Harp cascades. Ney flute rises. Violin enters delicately.
        # Kalimba like scattered light. Gentle frame drum.
        "02_First_Glance": [
            TrackConfig(name="Harp_Cascade",   generator=ArpeggiatorGenerator(pattern="up", note_duration=0.375, voicing="spread"), instrument="harp", density=0.7),
            TrackConfig(name="Ney_Breath",     generator=EthnicWorldGenerator(instrument="shanai"), instrument="shanai", density=0.5, mpe=True),
            TrackConfig(name="Tender_Violin",  generator=ViolinGenerator(articulation="legato", vibrato=True), instrument="violin", density=0.45, mpe=True),
            TrackConfig(name="Kalimba_Light",  generator=CelestaGenerator(note_density=0.4), instrument="kalimba", density=0.35),
            TrackConfig(name="Frame_Drum",     generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="steel_drums", density=0.3),
        ],

        # ── 03: Passion's Fire (غرام) — burning desire, magnetic pull ───
        # Sitar riff drives. Heavy tribal drums. Trumpet yearns upward.
        # Full strings swell. Vocal chant as a heartbeat.
        "03_Passions_Fire": [
            TrackConfig(name="Sitar_Drive",    generator=EthnicPluckedGenerator(instrument="sitar"), instrument="sitar", density=0.65, mpe=True),
            TrackConfig(name="Tribal_Heart",   generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="taiko", density=0.75),
            TrackConfig(name="Yearning_Trumpet", generator=MelodyGenerator(phrase_length=6.0, direction_bias=0.3), instrument="trumpet", density=0.55, mpe=True),
            TrackConfig(name="Passion_Strings", generator=StringsLegatoGenerator(), instrument="strings", density=0.5),
            TrackConfig(name="Chant_Heartbeat", generator=VocalOohsGenerator(syllable="aah", harmony_count=3), instrument="voice", density=0.3),
        ],

        # ── 04: Separation (فراق) — the agony of parting ────────────────
        # 3/4 waltz of grief. Solo piano as a lone voice.
        # Contrabass drags the weight. Ethereal choir mourns.
        # Shakuhachi wails. Drone dissolves into silence.
        "04_Separation": [
            TrackConfig(name="Grief_Drone",     generator=DroneGenerator(variant="tonic", fade_in=4.0, fade_out=4.0), instrument="dark_pad", density=0.9, octave_shift=-1),
            TrackConfig(name="Lonely_Piano",    generator=PianoSoloGenerator(instrument="grand_piano", pedal=True, note_density=0.4), instrument="piano", density=0.45, mpe=True),
            TrackConfig(name="Wailing_Wind",    generator=EthnicWorldGenerator(instrument="shanai"), instrument="shanai", density=0.35, mpe=True),
            TrackConfig(name="Heavy_Bass",      generator=ContrabassGenerator(vibrato=False), instrument="contrabass", density=0.3),
            TrackConfig(name="Mourning_Choir",  generator=ChoirAahsGenerator(voice_count=4, dynamics="mp", syllable="aah"), instrument="choir", density=0.3),
        ],

        # ── 05: Reunion (وصال) — joyful, warm, resolving ────────────────
        # Full strings sweep. French horn warmth. Oud celebrates.
        # Flute dances. Frame drums accelerate. Choir rises.
        "05_Reunion": [
            TrackConfig(name="Sweeping_Strings", generator=StringsEnsembleGenerator(section_size="full", articulation="legato", dynamic_curve="crescendo"), instrument="strings", density=0.6),
            TrackConfig(name="Warm_Horn",        generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell"), instrument="french_horn", density=0.4),
            TrackConfig(name="Oud_Celebration",  generator=EthnicPluckedGenerator(instrument="sitar"), instrument="sitar", density=0.55, mpe=True),
            TrackConfig(name="Dancing_Flute",    generator=FluteGenerator(articulation="legato", vibrato=True, breath_phrase=True), instrument="flute", density=0.5, mpe=True),
            TrackConfig(name="Joyful_Drums",     generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="steel_drums", density=0.6),
            TrackConfig(name="Rising_Choir",     generator=ChoirAahsGenerator(voice_count=4, dynamics="f", syllable="aah"), instrument="choir", density=0.35),
        ],
    }

    for cfg in tracks_configs:
        print(f"\n--- Composing: {cfg['name']} ({cfg['ts'][0]}/{cfg['ts'][1]}, {cfg['tempo']} BPM) ---")

        parts = [IdeaPart(
            name=cfg["name"], bars=cfg["bars"],
            scale=sikah_scale, tempo=cfg["tempo"],
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
            bpm=cfg["tempo"], key=sikah_scale,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )
        print(f"    Exported {cfg['name']}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: ARABIC SIKAH — LOVE & LONGING")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_arabic_sikah_love()
