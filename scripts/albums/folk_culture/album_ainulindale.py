# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/album_ainulindale.py — "Ainulindalë: The Music of the Ainur"
Tolkien's creation myth set to Hungarian Minor.
Epic choral-orchestral cycle in 5 movements.

I.  The Theme of Eru       — Iluvatar speaks the first theme
II. The Great Music        — Ainur sing in harmony, voices intertwine
III. Discord of Melkor     — darkness enters, chaos and dissonance
IV. The Three Themes       — Iluvatar's right hand: tender, growing, unstoppable
V. Ea — The World That Is  — vision made real, Valar descend into Arda
"""

from pathlib import Path
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, _GM_PROGRAMS
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator, OboeGenerator, BassoonGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
from melodica.generators.orchestral_hit import OrchestralHitGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.synth_effects import SynthEffectsGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.canon import CanonGenerator
from melodica.generators.tension import TensionGenerator


def generate_ainulindale():
    album_dir = Path("output/album_ainulindale")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 80)
    print("  A I N U L I N D A L E")
    print("  The Music of the Ainur  —  Hungarian Minor")
    print("  Iluvatar. Melkor. Ea.")
    print("=" * 80)

    scale = Scale(root=4, mode=Mode.HUNGARIAN_MINOR)

    configs = [
        {"name": "I_The_Theme_of_Eru",    "tempo": 60,  "ts": (4, 4), "bars": 56},
        {"name": "II_The_Great_Music",     "tempo": 80,  "ts": (4, 4), "bars": 52},
        {"name": "III_Discord_of_Melkor",  "tempo": 112, "ts": (4, 4), "bars": 48},
        {"name": "IV_The_Three_Themes",    "tempo": 76,  "ts": (3, 4), "bars": 60},
        {"name": "V_Ea_The_World_That_Is", "tempo": 96,  "ts": (4, 4), "bars": 64},
    ]

    # ── I: The Theme of Eru — before time, a single voice in void ────────
    # Iluvatar alone. Drone from nothing. Solo flute as the Voice of God.
    # Harp as celestial light. Single sustained cello tone. Choir pp.
    # Pad like formless void. Almost silence.
    tracks_map = {
        "I_The_Theme_of_Eru": [
            TrackConfig(name="Void_Drone",        generator=DroneGenerator(variant="tonic", fade_in=8.0, fade_out=6.0), instrument="dark_pad", density=0.85, octave_shift=-1),
            TrackConfig(name="Voice_of_Eru",       generator=MelodyGenerator(phrase_length=12.0, mode="downbeat_chord", random_movement=0.1, direction_bias=0.2, climax="up_5th"), instrument="flute", density=0.35, mpe=True),
            TrackConfig(name="Celestial_Harp",     generator=HarpGenerator(), instrument="harp", density=0.25),
            TrackConfig(name="Eternal_Tone",       generator=CelloGenerator(articulation="sustained", vibrato=True), instrument="cello", density=0.3),
            TrackConfig(name="Choir_of_Ainur",     generator=ChoirAahsGenerator(voice_count=4, dynamics="pp", syllable="aah", vibrato=0.15), instrument="choir", density=0.2),
        ],

        # ── II: The Great Music — all Ainur sing together ─────────────────
        # Counterpoint of voices. Violin + Oboe as two Ainur intertwining.
        # Full strings sustain. Horn nobility. Harp cascades.
        # Choir grows from pp to mf. Organ-like pad.
        "II_The_Great_Music": [
            TrackConfig(name="Ainur_Violin",       generator=ViolinGenerator(articulation="legato", vibrato=True), instrument="violin", density=0.5, octave_shift=1, mpe=True),
            TrackConfig(name="Ainur_Oboe",          generator=OboeGenerator(articulation="legato"), instrument="oboe", density=0.45, octave_shift=1, mpe=True),
            TrackConfig(name="Harmony_Strings",     generator=StringsEnsembleGenerator(section_size="full", articulation="sustained", dynamic_curve="crescendo", divisi=4), instrument="strings", density=0.4),
            TrackConfig(name="Harp_of_Light",       generator=HarpGenerator(), instrument="harp", density=0.3, octave_shift=1),
            TrackConfig(name="Noble_Horn",          generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="swell"), instrument="french_horn", density=0.3, octave_shift=-1),
            TrackConfig(name="Growing_Choir",       generator=ChoirAahsGenerator(voice_count=4, dynamics="mf", syllable="aah", vibrato=0.3), instrument="choir", density=0.25),
        ],

        # ── III: Discord of Melkor — darkness enters the music ────────────
        # Aggressive, turbulent. Low trombones as Melkor's voice.
        # Tremolo strings = chaos. Tension clusters. Brass stabs.
        # Percussion like thunder. Dark pad underneath. Horns of defiance.
        "III_Discord_of_Melkor": [
            TrackConfig(name="Melkors_Voice",      generator=TromboneGenerator(articulation="staccato", register=1, bass_voice=True), instrument="trombone", density=0.45, octave_shift=-1),
            TrackConfig(name="Chaos_Tremolo",       generator=TremoloStringsGenerator(variant="chord", dynamic_swell=True, attack_time=0.3, decay_time=0.4, bow_speed=0.15), instrument="tremolo_strings", density=0.35),
            TrackConfig(name="Thunder_Perucssion",  generator=ElectronicDrumsGenerator(kit="ethnic"), instrument="taiko", density=0.6),
            TrackConfig(name="Darkness_Pad",        generator=DarkPadGenerator(mode="minor_pad", chord_dur=4.0), instrument="dark_pad", density=0.6, octave_shift=-2),
            TrackConfig(name="Tension_Cluster",     generator=TensionGenerator(mode="semitone_cluster", note_duration=2.0), instrument="synth_fx", density=0.3, octave_shift=1),
            TrackConfig(name="Defiant_Brass",       generator=FrenchHornGenerator(articulation="staccato"), instrument="french_horn", density=0.3, octave_shift=1),
        ],

        # ── IV: The Three Themes — Iluvatar's quiet, growing response ────
        # 3/4 waltz of creation. Begins tender: solo flute + ambient pad.
        # Violin enters as second theme. Choir grows as third theme.
        # Bassoon as ancient wisdom. Contrabass pedal. Organ drone.
        # The music cannot be silenced — it absorbs all discord.
        "IV_The_Three_Themes": [
            TrackConfig(name="Tender_Flute",       generator=FluteGenerator(articulation="legato", vibrato=True, breath_phrase=True, register=2), instrument="flute", density=0.4, mpe=True),
            TrackConfig(name="Second_Voice",        generator=ViolinGenerator(articulation="legato", vibrato=True), instrument="violin", density=0.4, mpe=True),
            TrackConfig(name="Wisdom_Bassoon",      generator=BassoonGenerator(vibrato=False, register=1), instrument="bassoon", density=0.3),
            TrackConfig(name="Creation_Choir",      generator=VocalOohsGenerator(syllable="ooh", harmony_count=3, vibrato=0.4, breath_phasing=True), instrument="voice", density=0.3),
            TrackConfig(name="Unstoppable_Pad",      generator=AmbientPadGenerator(voicing="spread", overlap=0.5), instrument="dark_pad", density=0.7, octave_shift=-1),
            TrackConfig(name="Foundation_Pedal",     generator=PedalBassGenerator(pedal_note="root", sustain=0.9, velocity_level=0.6), instrument="contrabass", density=0.6),
        ],

        # ── V: Ea — The World That Is — vision made real ──────────────────
        # Full orchestra. Strings sweep. Horns proclaim. Choir fortissimo.
        # Harp of stars. Contrabass depth. Cymbal crash = the chord of ending.
        # Orchestral hits = mountains rising. Oboe = Children of Iluvatar.
        # Everything crescendos, then dissolves into reverent silence.
        "V_Ea_The_World_That_Is": [
            TrackConfig(name="World_Strings",      generator=StringsEnsembleGenerator(section_size="full", articulation="legato", dynamic_curve="crescendo", divisi=4), instrument="strings", density=0.6),
            TrackConfig(name="Proclamation_Horns",  generator=FrenchHornGenerator(articulation="sustained", dynamic_curve="crescendo", fanfare_mode=True), instrument="french_horn", density=0.45),
            TrackConfig(name="Doom_Trombones",      generator=TromboneGenerator(articulation="sustained", register=2, bass_voice=True), instrument="trombone", density=0.35),
            TrackConfig(name="Children_of_Eru",     generator=OboeGenerator(articulation="legato"), instrument="oboe", density=0.4, mpe=True),
            TrackConfig(name="Stars_Harp",          generator=HarpGenerator(), instrument="harp", density=0.35),
            TrackConfig(name="Final_Choir",         generator=ChoirAahsGenerator(voice_count=4, dynamics="f", syllable="aah", vibrato=0.5), instrument="choir", density=0.45),
            TrackConfig(name="Abyss_Bass",          generator=ContrabassGenerator(vibrato=False, bass_voice=True), instrument="contrabass", density=0.3),
            TrackConfig(name="Creation_Impact",     generator=OrchestralCymbalGenerator(pattern_type="crash"), instrument="synth_fx", density=0.1),
        ],
    }

    for cfg in configs:
        print(f"\n--- Composing: {cfg['name']} ({cfg['ts'][0]}/{cfg['ts'][1]}, {cfg['tempo']} BPM) ---")

        parts = [IdeaPart(
            name=cfg["name"], bars=cfg["bars"],
            scale=scale, tempo=cfg["tempo"],
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
            bpm=cfg["tempo"], key=scale,
            instruments=instruments_map,
            cc_events=notes_dict.get("_cc_events", {}),
            mpe_tracks=notes_dict.get("_mpe_tracks", set()),
        )
        print(f"    Exported {cfg['name']}.mid")

    print("\n" + "=" * 80)
    print("  PRODUCTION COMPLETE: AINULINDALE")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    generate_ainulindale()
