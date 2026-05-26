# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_hirojoshi_garden.py — Japanese Garden Album Generator.

Album: "Hirojoshi Garden"
A walk through a sacred garden — from misty dawn to temple bells to silence.

Tracks:
1.  Mist           — Shakuhachi + koto, morning fog over moss
2.  Stone Path     — Koto + strings, slow measured walk
3.  Bamboo Grove   — Shakuhachi + shamisen duet, wind in bamboo
4.  Koi Pond       — Music box + harp, rippling water
5.  Torii Gate     — Full ensemble, passing through sacred threshold
6.  Tea Ceremony   — Koto + choir pad, meditative stillness
7.  Cherry Blossoms — Harp + strings, petals falling
8.  Temple Bells   — Bells + taiko + choir, evening prayer
9.  Moonlit Garden — Shakuhachi + koto, night returns to mist

All tracks use Hirojoshi (0,2,3,7,8) and related Japanese pentatonic modes
with functional_hmm progressions and phrase-based structure.

Powered by Functional HMM, FluidR3, and Japanese aesthetics.
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
    print("  H I R O J O S H I   G A R D E N")
    print("  9 tracks — Japanese garden album")
    print("=" * 80)

    out_dir = Path("output/album_hirojoshi_garden")
    out_dir.mkdir(exist_ok=True, parents=True)

    scales = {
        "hirojoshi":  Scale(2, Mode.HIROJOSHI),      # D Hirojoshi
        "kumoi":      Scale(2, Mode.KUMOI),           # D Kumoi
        "japanese":   Scale(2, Mode.JAPANESE),         # D Japanese
        "hir_a":      Scale(0, Mode.HIROJOSHI),       # C Hirojoshi
        "hir_e":      Scale(4, Mode.HIROJOSHI),       # E Hirojoshi
        "hir_g":      Scale(7, Mode.HIROJOSHI),       # G Hirojoshi
        "kumoi_a":    Scale(9, Mode.KUMOI),            # A Kumoi
    }

    # ------------------------------------------------------------------
    # Track 1: Mist — Shakuhachi + koto, morning fog
    # ------------------------------------------------------------------
    generate_track("1 Mist",
        parts=[IdeaPart(
            name="Dawn", bars=16, scale=scales["hirojoshi"], tempo=48,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Shakuhachi": structure_to_schedule("A B A:var C", 4),
                "Koto":       structure_to_schedule("R A B A:var", 4),
                "Mist":       structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Shakuhachi", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="shakuhachi", density=0.5),
            TrackConfig(name="Koto", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="koto", density=0.4, octave_shift=1),
            TrackConfig(name="Mist", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="dark_pad", density=0.3),
        ],
        out_dir=out_dir, bpm=48)

    # ------------------------------------------------------------------
    # Track 2: Stone Path — Koto + strings, measured walk
    # ------------------------------------------------------------------
    generate_track("2 Stone Path",
        parts=[IdeaPart(
            name="Walk", bars=16, scale=scales["kumoi"], tempo=60,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Koto":     structure_to_schedule("A B A:var C", 4),
                "Strings":  structure_to_schedule("A", 16),
                "Cello":    structure_to_schedule("R R A B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Koto", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="koto", density=0.6, octave_shift=1),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.7),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("half_note")), instrument="cello", density=0.4),
        ],
        out_dir=out_dir, bpm=60)

    # ------------------------------------------------------------------
    # Track 3: Bamboo Grove — Shakuhachi + shamisen duet, wind
    # ------------------------------------------------------------------
    generate_track("3 Bamboo Grove",
        parts=[IdeaPart(
            name="Wind", bars=16, scale=scales["hirojoshi"], tempo=55,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Shakuhachi": structure_to_schedule("A B C B:var", 4),
                "Shamisen":   structure_to_schedule("R A R B", 4),
                "Rustle":     structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Shakuhachi", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="shakuhachi", density=0.6),
            TrackConfig(name="Shamisen", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="shamisen", density=0.5, octave_shift=1),
            TrackConfig(name="Rustle", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.3),
        ],
        out_dir=out_dir, bpm=55)

    # ------------------------------------------------------------------
    # Track 4: Koi Pond — Music box + harp, rippling water
    # ------------------------------------------------------------------
    generate_track("4 Koi Pond",
        parts=[IdeaPart(
            name="Water", bars=16, scale=scales["hir_a"], tempo=65,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "MusicBox": structure_to_schedule("A B A:var C", 4),
                "Harp":     structure_to_schedule("A", 16),
                "Ripple":   structure_to_schedule("R A R A", 4),
            },
        )],
        tracks=[
            TrackConfig(name="MusicBox", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="music_box", density=0.7, octave_shift=1),
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("markov:ballad")), instrument="harp", density=0.5, octave_shift=1),
            TrackConfig(name="Ripple", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="pad", density=0.25),
        ],
        out_dir=out_dir, bpm=65)

    # ------------------------------------------------------------------
    # Track 5: Torii Gate — Full ensemble, sacred threshold
    # ------------------------------------------------------------------
    generate_track("5 Torii Gate",
        parts=[
            IdeaPart("Approach", 12, scales["hir_g"], 72,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Koto":       structure_to_schedule("A B A:var", 4),
                    "Strings":    structure_to_schedule("A B", 6),
                    "Taiko":      structure_to_schedule("R A B", 4),
                    "Choir":      structure_to_schedule("R A", 6),
                }),
            IdeaPart("Passage", 8, scales["hirojoshi"], 80,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Koto":       structure_to_schedule("C D", 4),
                    "Strings":    structure_to_schedule("C D", 4),
                    "Taiko":      structure_to_schedule("C D", 4),
                    "Choir":      structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Koto", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="koto", density=0.7, octave_shift=1),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.8),
            TrackConfig(name="Taiko", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=0.6),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.6),
        ],
        out_dir=out_dir, bpm=72)

    # ------------------------------------------------------------------
    # Track 6: Tea Ceremony — Koto + pad, meditative stillness
    # ------------------------------------------------------------------
    generate_track("6 Tea Ceremony",
        parts=[IdeaPart(
            name="Stillness", bars=20, scale=scales["kumoi_a"], tempo=44,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Koto":    structure_to_schedule("A B C B:var D", 4),
                "Pad":     structure_to_schedule("A", 20),
                "Flute":   structure_to_schedule("R R A R B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Koto", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="koto", density=0.5, octave_shift=1),
            TrackConfig(name="Pad", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="flute", density=0.3),
        ],
        out_dir=out_dir, bpm=44)

    # ------------------------------------------------------------------
    # Track 7: Cherry Blossoms — Harp + strings, petals falling
    # ------------------------------------------------------------------
    generate_track("7 Cherry Blossoms",
        parts=[IdeaPart(
            name="Petals", bars=16, scale=scales["hir_e"], tempo=58,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harp":      structure_to_schedule("A B A:var C", 4),
                "Strings":   structure_to_schedule("R A B A:var", 4),
                "Koto":      structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="harp", density=0.7, octave_shift=1),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.7),
            TrackConfig(name="Koto", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="koto", density=0.3, octave_shift=1),
        ],
        out_dir=out_dir, bpm=58)

    # ------------------------------------------------------------------
    # Track 8: Temple Bells — Bells + taiko + choir, evening prayer
    # ------------------------------------------------------------------
    generate_track("8 Temple Bells",
        parts=[IdeaPart(
            name="Prayer", bars=16, scale=scales["hirojoshi"], tempo=52,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Bells":   structure_to_schedule("A B C B:var", 4),
                "Choir":   structure_to_schedule("R A B A:var", 4),
                "Taiko":   structure_to_schedule("R A R A", 4),
                "Organ":   structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="tubular_bells", density=0.25),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.6),
            TrackConfig(name="Taiko", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=0.4),
            TrackConfig(name="Organ", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="organ", density=0.5),
        ],
        out_dir=out_dir, bpm=52)

    # ------------------------------------------------------------------
    # Track 9: Moonlit Garden — Shakuhachi + koto, returns to mist
    # ------------------------------------------------------------------
    generate_track("9 Moonlit Garden",
        parts=[IdeaPart(
            name="Return", bars=20, scale=scales["hirojoshi"], tempo=45,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Shakuhachi": structure_to_schedule("A B A:var C D", 4),
                "Koto":       structure_to_schedule("R A B A:var C", 4),
                "Pad":        structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Shakuhachi", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="shakuhachi", density=0.5),
            TrackConfig(name="Koto", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="koto", density=0.4, octave_shift=1),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="dark_pad", density=0.25),
        ],
        out_dir=out_dir, bpm=45)

    print()
    print("  Album 'Hirojoshi Garden' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
