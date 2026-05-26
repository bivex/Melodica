# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_fallen_empire.py — Tragic Cinematic Album Generator.

Album: "The Fallen Empire"
A journey through ruins — from silence to remembrance to acceptance.

Tracks:
1.  Epitaph          — Solo piano, empty hall, grief
2.  The Hollow Crown — Slow orchestral march, fallen kingdom
3.  Ashen Bells      — Music box + choir, lost innocence
4.  Winter Siege     — Strings + brass, desperate defense
5.  Lament           — Cello + oboe duet, mourning the dead
6.  Pyre             — Full orchestra, rage and fire
7.  Aftermath        — Ambient drones + piano, smoking ruins
8.  Requiem          — Choir + organ, funeral mass
9.  Dawn             — Harp + strings, faint hope after loss

Powered by Functional HMM, FluidR3, and 9 dark modes.
"""

from pathlib import Path

from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart,
    structure_to_schedule,
)
from melodica.fluid_r3_profile import FLUID_R3_PROGRAMS
from melodica.generators.melody import MelodyGenerator
from melodica.generators.chord_gen import ChordGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


def generate_track(name, parts, tracks, out_dir, bpm):
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="cinematic",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    instruments_map = {t.name: FLUID_R3_PROGRAMS.get(t.instrument, 0) for t in tracks}

    file_path = out_dir / f"{name.replace(' ', '_')}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  T H E   F A L L E N   E M P I R E")
    print("  9 tracks — tragic cinematic album")
    print("=" * 80)

    out_dir = Path("output/album_fallen_empire")
    out_dir.mkdir(exist_ok=True, parents=True)

    scales = {
        "epitaph":    Scale(2, Mode.NATURAL_MINOR),
        "crown":      Scale(2, Mode.PHRYGIAN),
        "bells":      Scale(2, Mode.HARMONIC_MINOR),
        "siege":      Scale(2, Mode.DORIAN),
        "lament":     Scale(7, Mode.AEOLIAN),
        "pyre":       Scale(2, Mode.HUNGARIAN_MINOR),
        "aftermath":  Scale(0, Mode.LOCRIAN),
        "requiem":    Scale(2, Mode.DOUBLE_HARMONIC),
        "dawn":       Scale(2, Mode.MELODIC_MINOR),
    }

    # ------------------------------------------------------------------
    # Track 1: Epitaph — Solo piano, empty hall
    # ------------------------------------------------------------------
    generate_track("1 Epitaph",
        parts=[IdeaPart(
            name="Grief", bars=16, scale=scales["epitaph"], tempo=52,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":   structure_to_schedule("A B A:var C", 4),
                "Echo":    structure_to_schedule("A", 16),
                "Cello":   structure_to_schedule("R R A B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_tragic_piano_8ths")), instrument="piano", density=0.6),
            TrackConfig(name="Echo", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("ds_shrine_silence")), instrument="dark_pad", density=0.3),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:slow")), instrument="cello", density=0.4),
        ],
        out_dir=out_dir, bpm=52)

    # ------------------------------------------------------------------
    # Track 2: The Hollow Crown — Slow march, fallen kingdom
    # ------------------------------------------------------------------
    generate_track("2 The Hollow Crown",
        parts=[IdeaPart(
            name="March", bars=16, scale=scales["crown"], tempo=65,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Horns":     structure_to_schedule("A B", 8),
                "LowStrings": structure_to_schedule("A", 16),
                "Drums":     structure_to_schedule("R A", 8),
                "Bass":      structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Horns", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_grim_steady_8th")), instrument="french_horn", density=0.7),
            TrackConfig(name="LowStrings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.8),
            TrackConfig(name="Drums", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_steady_16th_charge")), instrument="timpani", density=0.5),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.7, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=65)

    # ------------------------------------------------------------------
    # Track 3: Ashen Bells — Music box + choir, lost innocence
    # ------------------------------------------------------------------
    generate_track("3 Ashen Bells",
        parts=[IdeaPart(
            name="Innocence", bars=16, scale=scales["bells"], tempo=72,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "MusicBox": structure_to_schedule("A B A:var C", 4),
                "Choir":    structure_to_schedule("R A", 8),
                "Bells":    structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="MusicBox", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("ds_frozen_city_swing")), instrument="music_box", density=0.8, octave_shift=1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.6),
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="tubular_bells", density=0.3),
        ],
        out_dir=out_dir, bpm=72)

    # ------------------------------------------------------------------
    # Track 4: Winter Siege — Strings + brass, desperate defense
    # ------------------------------------------------------------------
    generate_track("4 Winter Siege",
        parts=[
            IdeaPart("Phase1_Siege", 16, scales["siege"], 88,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Violins":   structure_to_schedule("A B", 8),
                    "Brass":     structure_to_schedule("R A", 8),
                    "Tremolo":   structure_to_schedule("A", 16),
                    "BassDrum":  structure_to_schedule("A B", 8),
                }),
            IdeaPart("Phase2_Breach", 8, scales["siege"], 100,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Violins":   structure_to_schedule("C D", 4),
                    "Brass":     structure_to_schedule("B C", 4),
                    "Tremolo":   structure_to_schedule("C", 8),
                    "BassDrum":  structure_to_schedule("C D", 4),
                }),
        ],
        tracks=[
            TrackConfig(name="Violins", generator=StringsEnsembleGenerator(
                section_size="full", articulation="staccato",
                rhythm=get_rhythm("ds_relentless_combo_16th")), instrument="violin", density=0.9),
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_grim_steady_8th")), instrument="brass", density=0.7),
            TrackConfig(name="Tremolo", generator=StringsEnsembleGenerator(
                section_size="full", articulation="tremolo"), instrument="tremolo_strings", density=0.9),
            TrackConfig(name="BassDrum", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_steady_16th_charge")), instrument="timpani", density=0.8),
        ],
        out_dir=out_dir, bpm=88)

    # ------------------------------------------------------------------
    # Track 5: Lament — Cello + oboe duet, mourning
    # ------------------------------------------------------------------
    generate_track("5 Lament",
        parts=[IdeaPart(
            name="Mourning", bars=20, scale=scales["lament"], tempo=58,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Cello":  structure_to_schedule("A B C B:var", 5),
                "Oboe":   structure_to_schedule("R A R B", 5),
                "Pad":    structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:dirge")), instrument="cello", density=0.7),
            TrackConfig(name="Oboe", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:slow")), instrument="oboe", density=0.5),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("drone")), instrument="dark_pad", density=0.4),
        ],
        out_dir=out_dir, bpm=58)

    # ------------------------------------------------------------------
    # Track 6: Pyre — Full orchestra, rage and fire
    # ------------------------------------------------------------------
    generate_track("6 Pyre",
        parts=[
            IdeaPart("Phase1_Fury", 16, scales["pyre"], 110,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings":  structure_to_schedule("A B", 8),
                    "Brass":    structure_to_schedule("R A", 8),
                    "Choir":    structure_to_schedule("A", 16),
                    "Perc":     structure_to_schedule("A B", 8),
                }),
            IdeaPart("Phase2_Burn", 12, scales["pyre"], 128,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings":  structure_to_schedule("C D E", 4),
                    "Brass":    structure_to_schedule("B C D", 4),
                    "Choir":    structure_to_schedule("C D", 6),
                    "Perc":     structure_to_schedule("C D E", 4),
                }),
        ],
        tracks=[
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="staccato",
                rhythm=get_rhythm("ds_final_assault_mixed")), instrument="strings", density=1.0),
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_relentless_32nd")), instrument="brass", density=0.9),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("ds_grim_steady_8th")), instrument="choir", density=0.8),
            TrackConfig(name="Perc", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_relentless_combo_16th")), instrument="timpani", density=1.0),
        ],
        out_dir=out_dir, bpm=110)

    # ------------------------------------------------------------------
    # Track 7: Aftermath — Ambient drones + piano, smoking ruins
    # ------------------------------------------------------------------
    generate_track("7 Aftermath",
        parts=[IdeaPart(
            name="Ruins", bars=16, scale=scales["aftermath"], tempo=48,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":  structure_to_schedule("R A B A:var", 4),
                "Drone":  structure_to_schedule("A", 16),
                "Fragments": structure_to_schedule("R R R A", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:slow")), instrument="piano", density=0.4),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.6, octave_shift=-1),
            TrackConfig(name="Fragments", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("ambient")), instrument="sweep_pad", density=0.3),
        ],
        out_dir=out_dir, bpm=48)

    # ------------------------------------------------------------------
    # Track 8: Requiem — Choir + organ, funeral mass
    # ------------------------------------------------------------------
    generate_track("8 Requiem",
        parts=[IdeaPart(
            name="Mass", bars=20, scale=scales["requiem"], tempo=55,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Organ":   structure_to_schedule("A B C B:var D", 4),
                "Choir":   structure_to_schedule("A B C D A:var", 4),
                "Bells":   structure_to_schedule("R A R A", 5),
            },
        )],
        tracks=[
            TrackConfig(name="Organ", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="organ", density=0.8),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.7),
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="tubular_bells", density=0.2),
        ],
        out_dir=out_dir, bpm=55)

    # ------------------------------------------------------------------
    # Track 9: Dawn — Harp + strings, faint hope after loss
    # ------------------------------------------------------------------
    generate_track("9 Dawn",
        parts=[IdeaPart(
            name="Hope", bars=20, scale=scales["dawn"], tempo=60,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harp":      structure_to_schedule("A B A:var C", 5),
                "Strings":   structure_to_schedule("R A B A:var", 5),
                "Melody":    structure_to_schedule("R R A B", 5),
                "Pad":       structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("arpeggio:slow")), instrument="harp", density=0.8),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.7),
            TrackConfig(name="Melody", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="oboe", density=0.5),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("drone")), instrument="pad", density=0.3),
        ],
        out_dir=out_dir, bpm=60)

    print()
    print("  Album 'The Fallen Empire' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
