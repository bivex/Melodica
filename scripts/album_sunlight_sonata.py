# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_sunlight_sonata.py — Major Key Album Generator.

Album: "Sunlight Sonata"
A day of light — from sunrise to golden hour to starlit night.

Tracks:
1.  Sunrise        — Piano + strings, dawn breaks
2.  Morning Light  — Flute + harp, warm morning
3.  Meadow Walk    — Guitar + strings + bass, countryside
4.  River Song     — Piano + celesta, flowing water
5.  Afternoon Heat — Brass + organ + bass, Mediterranean sun
6.  Lemonade       — Vibraphone + piano + bass, lazy afternoon
7.  Golden Hour    — Strings + harp + choir, magic light
8.  Sunset Waltz   — Piano + strings + flute, 3/4 time
9.  Starlight      — Choir + piano + celesta, night sky

All tracks use major modes (Ionian, Lydian, Mixolydian, Major Pentatonic)
with functional_hmm progressions.

Powered by Functional HMM, FluidR3, and sunlight.
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
from melodica.types import Scale, Mode, BarGrid
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
    print("  S U N L I G H T   S O N A T A")
    print("  9 tracks — Major key album")
    print("=" * 80)

    out_dir = Path("output/album_sunlight_sonata")
    out_dir.mkdir(exist_ok=True, parents=True)

    scales = {
        "C_ion":    Scale(0, Mode.IONIAN),              # C Major
        "G_lyd":    Scale(7, Mode.LYDIAN),              # G Lydian
        "D_mixo":   Scale(2, Mode.MIXOLYDIAN),          # D Mixolydian
        "F_ion":    Scale(5, Mode.IONIAN),              # F Major
        "A_pent":   Scale(9, Mode.MAJOR_PENTATONIC),    # A Major Pentatonic
        "E_lyd":    Scale(4, Mode.LYDIAN),              # E Lydian
        "Bb_ion":   Scale(10, Mode.IONIAN),             # Bb Major
        "C_mixo":   Scale(0, Mode.MIXOLYDIAN),          # C Mixolydian
        "D_ion":    Scale(2, Mode.IONIAN),              # D Major
    }

    # ------------------------------------------------------------------
    # Track 1: Sunrise — Piano + strings, dawn breaks
    # ------------------------------------------------------------------
    generate_track("1 Sunrise",
        parts=[IdeaPart(
            name="Dawn", bars=16, scale=scales["C_ion"], tempo=52,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":   structure_to_schedule("A B A:var C", 4),
                "Strings": structure_to_schedule("R A B A:var", 4),
                "Pad":     structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.6),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.6),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="pad", density=0.3),
        ],
        out_dir=out_dir, bpm=52)

    # ------------------------------------------------------------------
    # Track 2: Morning Light — Flute + harp, warm morning
    # ------------------------------------------------------------------
    generate_track("2 Morning Light",
        parts=[IdeaPart(
            name="Warmth", bars=16, scale=scales["G_lyd"], tempo=68,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Flute": structure_to_schedule("A B C B:var", 4),
                "Harp":  structure_to_schedule("A", 16),
                "Pad":   structure_to_schedule("A A:var A B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="flute", density=0.55),
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="harp", density=0.5, octave_shift=1),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.3),
        ],
        out_dir=out_dir, bpm=68)

    # ------------------------------------------------------------------
    # Track 3: Meadow Walk — Guitar + strings + bass, countryside
    # ------------------------------------------------------------------
    generate_track("3 Meadow Walk",
        parts=[IdeaPart(
            name="Fields", bars=16, scale=scales["D_mixo"], tempo=100,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Guitar":  structure_to_schedule("A B A:var C", 4),
                "Strings": structure_to_schedule("R A B A", 4),
                "Bass":    structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Guitar", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:swing")), instrument="nylon_guitar", density=0.65),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.5),
            TrackConfig(name="Bass", generator=BassGenerator(
                rhythm=get_rhythm("straight_quarters")), instrument="acoustic_bass", density=0.5, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=100)

    # ------------------------------------------------------------------
    # Track 4: River Song — Piano + celesta, flowing water
    # ------------------------------------------------------------------
    generate_track("4 River Song",
        parts=[IdeaPart(
            name="Water", bars=16, scale=scales["F_ion"], tempo=76,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":    structure_to_schedule("A B A:var C", 4),
                "Celesta":  structure_to_schedule("R A R B", 4),
                "Strings":  structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.6),
            TrackConfig(name="Celesta", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="celesta", density=0.5, octave_shift=1),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.5),
        ],
        out_dir=out_dir, bpm=76)

    # ------------------------------------------------------------------
    # Track 5: Afternoon Heat — Brass + organ + bass, Mediterranean
    # ------------------------------------------------------------------
    generate_track("5 Afternoon Heat",
        parts=[IdeaPart(
            name="Sun", bars=16, scale=scales["A_pent"], tempo=88,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Brass":  structure_to_schedule("A B C B:var", 4),
                "Organ":  structure_to_schedule("A", 16),
                "Bass":   structure_to_schedule("A B R B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_quarters")), instrument="french_horn", density=0.5),
            TrackConfig(name="Organ", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="organ", density=0.5),
            TrackConfig(name="Bass", generator=BassGenerator(
                rhythm=get_rhythm("straight_quarters")), instrument="bass", density=0.5, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=88)

    # ------------------------------------------------------------------
    # Track 6: Lemonade — Vibraphone + piano + bass, lazy afternoon
    # ------------------------------------------------------------------
    generate_track("6 Lemonade",
        parts=[IdeaPart(
            name="Lazy", bars=16, scale=scales["E_lyd"], tempo=72,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Vibes": structure_to_schedule("A B A:var C", 4),
                "Piano": structure_to_schedule("R A B A:var", 4),
                "Bass":  structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Vibes", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:swing")), instrument="vibraphone", density=0.55),
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="piano", density=0.45),
            TrackConfig(name="Bass", generator=BassGenerator(
                rhythm=get_rhythm("half_note")), instrument="fretless_bass", density=0.4, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=72)

    # ------------------------------------------------------------------
    # Track 7: Golden Hour — Strings + harp + choir, magic light
    # ------------------------------------------------------------------
    generate_track("7 Golden Hour",
        parts=[IdeaPart(
            name="Magic", bars=16, scale=scales["Bb_ion"], tempo=58,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Strings": structure_to_schedule("A B A:var C", 4),
                "Harp":    structure_to_schedule("A", 16),
                "Choir":   structure_to_schedule("R A B A:var", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.7),
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="harp", density=0.5, octave_shift=1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.5),
        ],
        out_dir=out_dir, bpm=58)

    # ------------------------------------------------------------------
    # Track 8: Sunset Waltz — Piano + strings + flute, 3/4 time
    # ------------------------------------------------------------------
    generate_track("8 Sunset Waltz",
        parts=[IdeaPart(
            name="Waltz", bars=20, scale=scales["C_mixo"], tempo=64,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":   structure_to_schedule("A B C B:var D", 4),
                "Strings": structure_to_schedule("A B A:var C D", 4),
                "Flute":   structure_to_schedule("R A R B A", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("waltz_basic")), instrument="piano", density=0.6),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("waltz_basic")), instrument="strings", density=0.6),
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="flute", density=0.4),
        ],
        out_dir=out_dir, bpm=64)

    # ------------------------------------------------------------------
    # Track 9: Starlight — Choir + piano + celesta, night sky
    # ------------------------------------------------------------------
    generate_track("9 Starlight",
        parts=[IdeaPart(
            name="Night", bars=20, scale=scales["D_ion"], tempo=48,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Choir":   structure_to_schedule("A B A:var C D", 4),
                "Piano":   structure_to_schedule("R A B A:var C", 4),
                "Celesta": structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.6),
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.5),
            TrackConfig(name="Celesta", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="celesta", density=0.3, octave_shift=1),
        ],
        out_dir=out_dir, bpm=48)

    print()
    print("  Album 'Sunlight Sonata' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
