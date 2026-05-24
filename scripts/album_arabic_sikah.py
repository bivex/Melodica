# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_arabic_sikah.py — "Arabic Sikah: The Voice of the Desert"
A microtonal ethnic album based on Arabic Sikah scale (including quarter-tones).
Inspired by classical Arabic poetry.
Uses CoupledHMM with microtonal support.
Bar-aware: 6/8 (3 quarter-note beats per bar) via BarGrid.
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.types import Scale, Mode, BarGrid
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

# Generators
from melodica.generators.orchestral_strings import CelloGenerator, ContrabassGenerator, ViolinGenerator, ViolaGenerator
from melodica.generators.orchestral_brass import TrumpetGenerator
from melodica.generators.orchestral_woodwinds import OboeGenerator
from melodica.generators.orchestral_percussion import MalletPercussionGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.chromatic_percussion import CelestaGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.wind_brass_solo import WoodwindSoloGenerator
from melodica.generators.plucked_solo import EthnicPluckedGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.scifi_underscore import SciFiUnderscoreGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.ethnic_world import EthnicWorldGenerator
from melodica.generators.melody import MelodyGenerator

def generate_arabic_sikah():
    album_dir = Path("output/album_arabic_sikah")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("        A R A B I C   S I K A H   :   P O E T R Y   I N   M O T I O N")
    print("        Microtonal Masterpiece based on Classical Verse")
    print("=" * 80)

    # Scale: Arabic Sikah
    sikah_scale = Scale(root=4, mode=Mode.ARABIC_SIKAH)

    tracks_configs = [
        {"name": "01_The_Watchers_Gaze", "poet": "ابн شعواء الفزاري", "tempo": 92},
        {"name": "02_Beauty_in_Strands", "poet": "ابн إدريس التжиبي", "tempo": 78},
        {"name": "03_Raising_the_Banner", "poet": "ابн الرعلاء", "tempo": 124},
        {"name": "04_Beyond_the_Houses", "poet": "هند الأيادية", "tempo": 68},
        {"name": "05_The_Chosen_Pot", "poet": "لقيط بن زرارة", "tempo": 110}
    ]

    # Unique instrumentation per movement
    tracks_map = {
        "01_The_Watchers_Gaze": [
            TrackConfig(name="Desert_Drone", generator=DroneGenerator(), instrument="dark_pad", density=0.9, octave_shift=-1),
            TrackConfig(name="Oud_Solo", generator=EthnicWorldGenerator(instrument="shamisen"), instrument="shamisen", density=0.6, mpe=True),
            TrackConfig(name="Ney_Flute", generator=EthnicWorldGenerator(instrument="shanai"), instrument="shanai", density=0.5, mpe=True),
            TrackConfig(name="Cello_Sustain", generator=CelloGenerator(articulation="sustained"), instrument="cello", density=0.4),
            TrackConfig(name="Sand_Texture", generator=SciFiUnderscoreGenerator(), instrument="synth_fx", density=0.3),
        ],
        "02_Beauty_in_Strands": [
            TrackConfig(name="Harp_Arpeggio", generator=ArpeggiatorGenerator(pattern="up", note_duration=0.5), instrument="harp", density=0.7),
            TrackConfig(name="Kanun_Trill", generator=EthnicPluckedGenerator(instrument="koto"), instrument="koto", density=0.5, mpe=True),
            TrackConfig(name="Clarinet_Melody", generator=MelodyGenerator(phrase_length=8.0), instrument="clarinet", density=0.5, mpe=True),
            TrackConfig(name="Viola_Pad", generator=ViolaGenerator(articulation="sustained"), instrument="viola", density=0.4),
            TrackConfig(name="Gentle_Perc", generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="steel_drums", density=0.3),
        ],
        "03_Raising_the_Banner": [
            TrackConfig(name="War_Drums", generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="taiko", density=0.8),
            TrackConfig(name="Brass_Fanfare", generator=TrumpetGenerator(articulation="sustained", fanfare_mode=True), instrument="trumpet", density=0.6),
            TrackConfig(name="Oud_Drive", generator=EthnicWorldGenerator(instrument="shamisen"), instrument="shamisen", density=0.7, mpe=True),
            TrackConfig(name="Violin_Lead", generator=ViolinGenerator(articulation="detache"), instrument="violin", density=0.6, mpe=True),
            TrackConfig(name="Impact_Hits", generator=FXImpactGenerator(), instrument="orchestra_hit", density=0.2),
        ],
        "04_Beyond_the_Houses": [
            TrackConfig(name="Night_Drone", generator=DroneGenerator(variant="tonic"), instrument="dark_pad", density=0.9, octave_shift=-1),
            TrackConfig(name="Shakuhachi_Breath", generator=WoodwindSoloGenerator(instrument="recorder", breath_vibrato=True), instrument="shakuhachi", density=0.4, mpe=True),
            TrackConfig(name="Contrabass_Deep", generator=ContrabassGenerator(), instrument="contrabass", density=0.3),
            TrackConfig(name="Kalimba_Sparkle", generator=CelestaGenerator(note_density=0.5), instrument="kalimba", density=0.4),
            TrackConfig(name="Ambient_Texture", generator=SciFiUnderscoreGenerator(variant="blade_runner"), instrument="synth_fx", density=0.3),
        ],
        "05_The_Chosen_Pot": [
            TrackConfig(name="Sitar_Riff", generator=EthnicPluckedGenerator(instrument="sitar"), instrument="sitar", density=0.6, mpe=True),
            TrackConfig(name="Tribal_Perc", generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="steel_drums", density=0.7),
            TrackConfig(name="Vocal_Chant", generator=MelodyGenerator(phrase_length=8.0), instrument="voice", density=0.4, mpe=True),
            TrackConfig(name="Strings_Ensemble", generator=StringsEnsembleGenerator(section_size="full"), instrument="strings", density=0.5),
            TrackConfig(name="Oboe_Counter", generator=OboeGenerator(), instrument="oboe", density=0.4, mpe=True),
        ],
    }

    for cfg in tracks_configs:
        print(f"\n--- Composing Movement: {cfg['name']} ---")

        parts = [IdeaPart(
            name=cfg['name'], bars=48, scale=sikah_scale, tempo=cfg['tempo'],
            time_signature=(6, 8),
            progression_type="coupled_hmm"
        )]

        track_list = tracks_map[cfg['name']]

        tool_config = IdeaToolConfig(
            style="cinematic_hybrid",
            time_signature=(6, 8),
            use_tension_curve=True,
            use_harmonic_verifier=True,
            parts=parts,
            tracks=track_list
        )

        # Get GM instrument mapping
        from melodica.idea_tool import _GM_PROGRAMS
        instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in track_list}

        notes_dict = IdeaTool(tool_config).generate()
        tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}
        
        export_multitrack_midi(
            tracks_data, str(album_dir / f"{cfg['name']}.mid"),
            bpm=cfg['tempo'], key=sikah_scale,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set())
        )
        print(f"    Exported {cfg['name']}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: ARABIC SIKAH")
    print(f"  Output folder: {album_dir.resolve()}")
    print("=" * 80)

if __name__ == "__main__":
    generate_arabic_sikah()
