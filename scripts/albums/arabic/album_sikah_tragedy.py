# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_sikah_tragedy.py — Tragic Arabic Album Generator.

Album: "The Fallen Mosque"
From prayer to ruin — a civilization's last breath told in maqam.

Tracks:
1.  Last Prayer        — Solo oud, empty courtyard, grief
2.  Funeral March      — Low strings + timpani, bearing the dead
3.  Burning Library    — Harpsichord + strings, knowledge turned to ash
4.  Siege              — Brass + percussion + choir, walls crumbling
5.  Lament For Children — Oud + flute duet, innocence lost
6.  Rage Of The Fallen — Full orchestra, storm of vengeance
7.  Ashes And Silence  — Drone + piano, smoking ruins at dawn
8.  Requiem            — Choir + organ + bells, mass for the dead
9.  Epitaph In Sand    — Solo oud + wind, wind erases all names

Powered by Functional HMM, FluidR3, and 9 dark maqam modes.
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
from melodica.generators.horror_dissonance import HorrorDissonanceGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
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
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map,
                           postprocess_arr=True)
    return file_path


def main():
    print("=" * 80)
    print("  T H E   F A L L E N   M O S Q U E")
    print("  9 tracks — tragic Arabic album")
    print("=" * 80)

    out_dir = Path("output/album_sikah_tragedy")
    out_dir.mkdir(exist_ok=True, parents=True)

    scales = {
        "sikah":     Scale(2, Mode.ARABIC_SIKAH),
        "phrygian":  Scale(2, Mode.PHRYGIAN),
        "hmin":      Scale(2, Mode.HARMONIC_MINOR),
        "hung":      Scale(2, Mode.HUNGARIAN_MINOR),
        "dbl_harm":  Scale(2, Mode.DOUBLE_HARMONIC),
        "persian":   Scale(2, Mode.PERSIAN),
        "phryg_dom": Scale(2, Mode.PHRYGIAN_DOMINANT),
        "neap":      Scale(2, Mode.NEAPOLITAN_MINOR),
        "enigma":    Scale(2, Mode.ENIGMATIC),
    }

    # ------------------------------------------------------------------
    # Track 1: Last Prayer — Solo oud + horror dread + choir lament, empty courtyard
    # ------------------------------------------------------------------
    generate_track("1 Last Prayer",
        parts=[IdeaPart(
            name="Grief", bars=16, scale=scales["sikah"], tempo=46,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":    structure_to_schedule("A B A:var C", 4),
                "Echo":   structure_to_schedule("A", 16),
                "Cello":  structure_to_schedule("R R A B", 4),
                "Dread":  structure_to_schedule("R R R A", 4),
                "Choir":  structure_to_schedule("R R A B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="sitar", density=0.5),
            TrackConfig(name="Echo", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="dark_pad", density=0.3),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("half_note")), instrument="cello", density=0.3),
            TrackConfig(name="Dread", generator=HorrorDissonanceGenerator(
                variant="psychological", dissonance_level=0.6, silence_probability=0.25),
                instrument="dark_pad", density=0.2),
            TrackConfig(name="Choir", generator=ChoirAahsGenerator(
                voice_count=4, dynamics="pp", vibrato=0.2, syllable="aah"),
                instrument="choir_pad", density=0.25),
        ],
        out_dir=out_dir, bpm=46)

    # ------------------------------------------------------------------
    # Track 2: Funeral March — Low strings + timpani + choir + horror dread
    # ------------------------------------------------------------------
    generate_track("2 Funeral March",
        parts=[IdeaPart(
            name="Procession", bars=16, scale=scales["phrygian"], tempo=55,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "LowStrings": structure_to_schedule("A B", 8),
                "Timpani":    structure_to_schedule("R A", 8),
                "Bass":       structure_to_schedule("A", 16),
                "Drone":      structure_to_schedule("A", 16),
                "FuneralDrum": structure_to_schedule("R A B A", 4),
                "Lament":     structure_to_schedule("R R A B", 4),
                "Dread":      structure_to_schedule("R A", 8),
            },
        )],
        tracks=[
            TrackConfig(name="LowStrings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.7),
            TrackConfig(name="Timpani", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="timpani", density=0.4),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.6, octave_shift=-1),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="FuneralDrum", generator=TimpaniGenerator(
                stroke_pattern="single", drum_count=4, tuning_follows=True),
                instrument="timpani", density=0.5, octave_shift=-2),
            TrackConfig(name="Lament", generator=ChoirAahsGenerator(
                voice_count=4, dynamics="mp", vibrato=0.3, syllable="aah"),
                instrument="choir_pad", density=0.4),
            TrackConfig(name="Dread", generator=HorrorDissonanceGenerator(
                variant="psychological", dissonance_level=0.5, silence_probability=0.3),
                instrument="dark_pad", density=0.25),
        ],
        out_dir=out_dir, bpm=55)

    # ------------------------------------------------------------------
    # Track 3: Burning Library — Harpsichord + strings, knowledge to ash
    # ------------------------------------------------------------------
    generate_track("3 Burning Library",
        parts=[IdeaPart(
            name="Flames", bars=16, scale=scales["hmin"], tempo=68,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harpsichord": structure_to_schedule("A B A:var C", 4),
                "Strings":     structure_to_schedule("R A", 8),
                "Bass":        structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Harpsichord", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:dense")), instrument="harpsichord", density=0.7),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="tremolo",
                rhythm=get_rhythm("whole_note")), instrument="tremolo_strings", density=0.8),
            TrackConfig(name="Bass", generator=BassGenerator(style="walking"),
                instrument="cello", density=0.5, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=68)

    # ------------------------------------------------------------------
    # Track 4: Siege — Brass + percussion + choir, walls crumbling
    # ------------------------------------------------------------------
    generate_track("4 Siege",
        parts=[
            IdeaPart("Phase1_Assault", 12, scales["dbl_harm"], 85,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Brass":   structure_to_schedule("A B", 6),
                    "Choir":   structure_to_schedule("R A B", 4),
                    "Perc":    structure_to_schedule("A B", 6),
                    "Strings": structure_to_schedule("A", 12),
                }),
            IdeaPart("Phase2_Breach", 12, scales["dbl_harm"], 105,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Brass":   structure_to_schedule("C D E", 4),
                    "Choir":   structure_to_schedule("C D", 6),
                    "Perc":    structure_to_schedule("C D E", 4),
                    "Strings": structure_to_schedule("C D", 6),
                }),
        ],
        tracks=[
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_quarters")), instrument="french_horn", density=0.8),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.7),
            TrackConfig(name="Perc", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=0.9),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="staccato",
                rhythm=get_rhythm("straight_quarters")), instrument="strings", density=0.9),
        ],
        out_dir=out_dir, bpm=85)

    # ------------------------------------------------------------------
    # Track 5: Lament For Children — Oud + flute duet, innocence lost
    # ------------------------------------------------------------------
    generate_track("5 Lament For Children",
        parts=[IdeaPart(
            name="Mourning", bars=20, scale=scales["persian"], tempo=50,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":   structure_to_schedule("A B C B:var", 5),
                "Flute": structure_to_schedule("R A R B", 5),
                "Pad":   structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="sitar", density=0.6),
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="flute", density=0.4),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="dark_pad", density=0.3),
        ],
        out_dir=out_dir, bpm=50)

    # ------------------------------------------------------------------
    # Track 6: Rage Of The Fallen — Full orchestra, storm of vengeance
    # ------------------------------------------------------------------
    generate_track("6 Rage Of The Fallen",
        parts=[
            IdeaPart("Phase1_Fury", 12, scales["hung"], 100,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings":  structure_to_schedule("A B", 6),
                    "Brass":    structure_to_schedule("R A B", 4),
                    "Choir":    structure_to_schedule("A", 12),
                    "Perc":     structure_to_schedule("A B", 6),
                }),
            IdeaPart("Phase2_Storm", 16, scales["hung"], 130,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings":  structure_to_schedule("C D E F", 4),
                    "Brass":    structure_to_schedule("C D E F", 4),
                    "Choir":    structure_to_schedule("C D", 8),
                    "Perc":     structure_to_schedule("C D E F", 4),
                }),
        ],
        tracks=[
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="staccato",
                rhythm=get_rhythm("straight_quarters")), instrument="strings", density=1.0),
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_quarters")), instrument="brass", density=0.9),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.8),
            TrackConfig(name="Perc", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=1.0),
        ],
        out_dir=out_dir, bpm=100)

    # ------------------------------------------------------------------
    # Track 7: Ashes And Silence — Drone + piano + horror + choir + timpani, smoking ruins
    # ------------------------------------------------------------------
    generate_track("7 Ashes And Silence",
        parts=[IdeaPart(
            name="Ruins", bars=16, scale=scales["neap"], tempo=42,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":     structure_to_schedule("R A B A:var", 4),
                "Drone":     structure_to_schedule("A", 16),
                "Fragments": structure_to_schedule("R R R A", 4),
                "Dread":     structure_to_schedule("A", 16),
                "Requiem":   structure_to_schedule("R R A B", 4),
                "Toll":      structure_to_schedule("R A R A", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.35),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5, octave_shift=-1),
            TrackConfig(name="Fragments", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.2),
            TrackConfig(name="Dread", generator=HorrorDissonanceGenerator(
                variant="psychological", dissonance_level=0.75, silence_probability=0.2),
                instrument="dark_pad", density=0.3),
            TrackConfig(name="Requiem", generator=ChoirAahsGenerator(
                voice_count=4, dynamics="mf", vibrato=0.4, syllable="aah"),
                instrument="choir_pad", density=0.35),
            TrackConfig(name="Toll", generator=TimpaniGenerator(
                stroke_pattern="single", drum_count=2, tuning_follows=True),
                instrument="timpani", density=0.2, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=42)

    # ------------------------------------------------------------------
    # Track 8: Requiem — Choir + organ + bells, mass for the dead
    # ------------------------------------------------------------------
    generate_track("8 Requiem",
        parts=[IdeaPart(
            name="Mass", bars=20, scale=scales["phryg_dom"], tempo=48,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Organ": structure_to_schedule("A B C B:var D", 4),
                "Choir": structure_to_schedule("A B C D A:var", 4),
                "Bells": structure_to_schedule("R A R A", 5),
            },
        )],
        tracks=[
            TrackConfig(name="Organ", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="organ", density=0.7),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.6),
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="tubular_bells", density=0.15),
        ],
        out_dir=out_dir, bpm=48)

    # ------------------------------------------------------------------
    # Track 9: Epitaph In Sand — Solo oud + wind, erased names
    # ------------------------------------------------------------------
    generate_track("9 Epitaph In Sand",
        parts=[IdeaPart(
            name="Silence", bars=20, scale=scales["enigma"], tempo=40,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":  structure_to_schedule("A B A:var C D", 4),
                "Wind": structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="sitar", density=0.4),
            TrackConfig(name="Wind", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.15),
        ],
        out_dir=out_dir, bpm=40)

    print()
    print("  Album 'The Fallen Mosque' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
