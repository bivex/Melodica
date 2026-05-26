# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_echoes_of_ash.py — Tragic Cinematic Album Generator.

Album: "Echoes of Ash"
A kingdom reduced to ember — from the last breath of a king to the first seed
pushing through scorched earth.

Tracks:
 1. The Last Breath      — Solo piano, the king dies alone
 2. Ashes of the Crown   — String quartet, court mourning
 3. A Child's Lullaby    — Music box + celesta, orphaned innocence
 4. March of the Fallen  — Full orchestra march, the army returns empty-handed
 5. The Pyre             — Brass + timpani, burning the dead
 6. Lament for the Lost  — Cello + oboe duet, two lovers separated by war
 7. Smoke and Silence    — Ambient drones, the aftermath
 8. Requiem Mass         — Choir + organ, funeral procession
 9. The First Seed       — Harp + strings, fragile hope
10. Echoes               — Full orchestra reprise, the cycle begins again

Powered by Functional HMM, FluidR3, and 10 dark modes.
"""

import random
from pathlib import Path

random.seed(2026)  # Deterministic output for consistent register balance

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
from melodica.generators.tremolo_strings import TremoloStringsGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi


_track_counter = 0

def generate_track(name, parts, tracks, out_dir, bpm, seed=None):
    global _track_counter
    _track_counter += 1
    track_seed = seed if seed is not None else 2026 + _track_counter
    random.seed(track_seed)
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="cinematic",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        seed=track_seed,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    instruments_map = {t.name: FLUID_R3_PROGRAMS.get(t.instrument, 0) for t in tracks}

    file_path = out_dir / f"{name.replace(' ', '_')}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  E C H O E S   O F   A S H")
    print("  10 tracks — tragic cinematic album")
    print("=" * 80)

    out_dir = Path("output/album_echoes_of_ash")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Each track uses a different dark mode on D or related root
    scales = {
        "breath":     Scale(2, Mode.NATURAL_MINOR),       # D natural minor
        "crown":      Scale(2, Mode.HARMONIC_MINOR),      # D harmonic minor
        "lullaby":    Scale(9, Mode.NATURAL_MINOR),       # A natural minor
        "march":      Scale(2, Mode.DORIAN),              # D Dorian
        "pyre":       Scale(2, Mode.PHRYGIAN),            # D Phrygian
        "lament":     Scale(4, Mode.HARMONIC_MINOR),      # E harmonic minor
        "smoke":      Scale(0, Mode.LOCRIAN),             # C Locrian
        "requiem":    Scale(2, Mode.DOUBLE_HARMONIC),     # D double harmonic
        "seed":       Scale(2, Mode.MELODIC_MINOR),       # D melodic minor
        "echoes":     Scale(2, Mode.HUNGARIAN_MINOR),     # D Hungarian minor
    }

    # ------------------------------------------------------------------
    # Track 1: The Last Breath — Solo piano, the king dies alone
    # ------------------------------------------------------------------
    generate_track("1 The Last Breath",
        parts=[IdeaPart(
            name="Death", bars=16, scale=scales["breath"], tempo=48,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":    structure_to_schedule("A B A:var C", 4),
                "Cello":    structure_to_schedule("R R A B", 4),
                "Bass":     structure_to_schedule("A", 16),
                "Pad":      structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.5, octave_shift=1),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:slow")), instrument="cello", density=0.4),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.6, octave_shift=-2),
            TrackConfig(name="Pad", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=48)

    # ------------------------------------------------------------------
    # Track 2: Ashes of the Crown — String quartet, court mourning
    # ------------------------------------------------------------------
    generate_track("2 Ashes of the Crown",
        parts=[IdeaPart(
            name="Mourning", bars=16, scale=scales["crown"], tempo=56,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Violin1":  structure_to_schedule("A B A:var C", 4),
                "Violin2":  structure_to_schedule("R A B A:var", 4),
                "Viola":    structure_to_schedule("A B", 8),
                "Cello":    structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Violin1", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="violin", density=0.7, octave_shift=1),
            TrackConfig(name="Violin2", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="violin", density=0.5, octave_shift=1),
            TrackConfig(name="Viola", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="viola", density=0.6, octave_shift=-1),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:slow")), instrument="cello", density=0.5, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=56)

    # ------------------------------------------------------------------
    # Track 3: A Child's Lullaby — Music box + celesta, orphaned innocence
    # ------------------------------------------------------------------
    generate_track("3 A Child's Lullaby",
        parts=[IdeaPart(
            name="Innocence", bars=16, scale=scales["lullaby"], tempo=66,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "MusicBox": structure_to_schedule("A B A:var C", 4),
                "Celesta":  structure_to_schedule("R A R B", 4),
                "Pad":      structure_to_schedule("A", 16),
                "Bass":     structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="MusicBox", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("ds_frozen_city_swing")), instrument="music_box", density=0.15, octave_shift=1),
            TrackConfig(name="Celesta", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="celesta", density=0.1),
            TrackConfig(name="Pad", generator=DroneGenerator(variant="tonic"),
                instrument="pad", density=0.6, octave_shift=-1),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.6, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=66)

    # ------------------------------------------------------------------
    # Track 4: March of the Fallen — Full orchestra, the army returns
    # ------------------------------------------------------------------
    generate_track("4 March of the Fallen",
        parts=[
            IdeaPart("Phase1_March", 16, scales["march"], 76,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Horns":       structure_to_schedule("A B", 8),
                    "LowStrings":  structure_to_schedule("A", 16),
                    "Timpani":     structure_to_schedule("A B", 8),
                    "Bass":        structure_to_schedule("A", 16),
                }),
            IdeaPart("Phase2_Arrival", 8, scales["march"], 66,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Horns":       structure_to_schedule("C D", 4),
                    "LowStrings":  structure_to_schedule("C", 8),
                    "Timpani":     structure_to_schedule("C", 8),
                    "Bass":        structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Horns", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_grim_steady_8th")), instrument="french_horn", density=0.7, octave_shift=1),
            TrackConfig(name="LowStrings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.8, octave_shift=-1),
            TrackConfig(name="Timpani", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_steady_16th_charge")), instrument="timpani", density=0.5, octave_shift=-1),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.7, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=76)

    # ------------------------------------------------------------------
    # Track 5: The Pyre — Brass + timpani, burning the dead
    # ------------------------------------------------------------------
    generate_track("5 The Pyre",
        parts=[
            IdeaPart("Phase1_Flames", 12, scales["pyre"], 92,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Brass":     structure_to_schedule("A B", 6),
                    "Strings":   structure_to_schedule("A", 12),
                    "Timpani":   structure_to_schedule("A B", 6),
                    "Choir":     structure_to_schedule("R A", 6),
                    "Bass":      structure_to_schedule("A", 12),
                }),
            IdeaPart("Phase2_Inferno", 8, scales["pyre"], 108,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Brass":     structure_to_schedule("C D", 4),
                    "Strings":   structure_to_schedule("C", 8),
                    "Timpani":   structure_to_schedule("C D", 4),
                    "Choir":     structure_to_schedule("C", 8),
                    "Bass":      structure_to_schedule("C", 8),
                }),
        ],
        tracks=[
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_relentless_32nd")), instrument="brass", density=0.8, octave_shift=1),
            TrackConfig(name="Strings", generator=TremoloStringsGenerator(
                variant="single", bow_speed=0.15), instrument="tremolo_strings", density=0.7, octave_shift=-1),
            TrackConfig(name="Timpani", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("ds_steady_16th_charge")), instrument="timpani", density=0.7, octave_shift=-2),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.6, octave_shift=1),
            TrackConfig(name="Bass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="tuba", density=0.5, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=92)

    # ------------------------------------------------------------------
    # Track 6: Lament for the Lost — Cello + oboe duet, two lovers
    # ------------------------------------------------------------------
    generate_track("6 Lament for the Lost",
        parts=[IdeaPart(
            name="Separation", bars=20, scale=scales["lament"], tempo=54,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Cello":  structure_to_schedule("A B C B:var", 5),
                "Oboe":   structure_to_schedule("R A R B", 5),
                "Pad":    structure_to_schedule("A", 20),
                "Harp":   structure_to_schedule("R A R A", 5),
                "Bass":   structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:dirge")), instrument="cello", density=0.7, octave_shift=-1),
            TrackConfig(name="Oboe", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:slow")), instrument="oboe", density=0.5),
            TrackConfig(name="Pad", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.3, octave_shift=-2),
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("arpeggio:slow")), instrument="harp", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.2, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=54)

    # ------------------------------------------------------------------
    # Track 7: Smoke and Silence — Ambient drones, the aftermath
    # ------------------------------------------------------------------
    generate_track("7 Smoke and Silence",
        parts=[IdeaPart(
            name="Ruins", bars=16, scale=scales["smoke"], tempo=44,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":     structure_to_schedule("R A B A:var", 4),
                "Drone":     structure_to_schedule("A", 16),
                "Fragments": structure_to_schedule("R R R A", 4),
                "Bass":      structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:slow")), instrument="piano", density=0.4),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5),
            TrackConfig(name="Fragments", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("ambient")), instrument="sweep_pad", density=0.5, octave_shift=2),
            TrackConfig(name="Bass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="tuba", density=0.4, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=44)

    # ------------------------------------------------------------------
    # Track 8: Requiem Mass — Choir + organ, funeral procession
    # ------------------------------------------------------------------
    generate_track("8 Requiem Mass",
        parts=[IdeaPart(
            name="Mass", bars=20, scale=scales["requiem"], tempo=52,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Organ":   structure_to_schedule("A B C B:var D", 4),
                "Choir":   structure_to_schedule("A B C D A:var", 4),
                "Bells":   structure_to_schedule("R A R A", 5),
                "Cello":   structure_to_schedule("A", 20),
                "Bass":    structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Organ", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="organ", density=0.5, octave_shift=1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.4, octave_shift=1),
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="tubular_bells", density=0.4, octave_shift=2),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:slow")), instrument="cello", density=0.5, octave_shift=-2),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.5, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=52)

    # ------------------------------------------------------------------
    # Track 9: The First Seed — Harp + strings, fragile hope
    # ------------------------------------------------------------------
    generate_track("9 The First Seed",
        parts=[IdeaPart(
            name="Hope", bars=20, scale=scales["seed"], tempo=60,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harp":     structure_to_schedule("A B A:var C", 5),
                "Strings":  structure_to_schedule("R A B A:var", 5),
                "Oboe":     structure_to_schedule("R R A B", 5),
                "Pad":      structure_to_schedule("A", 20),
            },
        )],
        tracks=[
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("arpeggio:slow")), instrument="harp", density=0.5),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.5, octave_shift=-2),
            TrackConfig(name="Oboe", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="oboe", density=0.3, octave_shift=1),
            TrackConfig(name="Pad", generator=DroneGenerator(variant="tonic"),
                instrument="pad", density=0.3, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=60)

    # ------------------------------------------------------------------
    # Track 10: Echoes — Full orchestra reprise, the cycle begins again
    # ------------------------------------------------------------------
    generate_track("10 Echoes",
        parts=[
            IdeaPart("Phase1_Remnant", 16, scales["echoes"], 68,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Violins":   structure_to_schedule("A B", 8),
                    "Viola":     structure_to_schedule("R A", 8),
                    "Cello":     structure_to_schedule("A", 16),
                    "Harp":      structure_to_schedule("A B", 8),
                    "Pad":       structure_to_schedule("A", 16),
                }),
            IdeaPart("Phase2_Cycle", 12, scales["echoes"], 80,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Violins":   structure_to_schedule("C D E", 4),
                    "Viola":     structure_to_schedule("B C D", 4),
                    "Cello":     structure_to_schedule("C D", 6),
                    "Harp":      structure_to_schedule("C D E", 4),
                    "Pad":       structure_to_schedule("C", 12),
                }),
        ],
        tracks=[
            TrackConfig(name="Violins", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="violin", density=0.7),
            TrackConfig(name="Viola", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="viola", density=0.6, octave_shift=-1),
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("markov:ballad")), instrument="cello", density=0.7, octave_shift=-2),
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("arpeggio:slow")), instrument="harp", density=0.5),
            TrackConfig(name="Pad", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.1, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=68)

    print()
    print("  Album 'Echoes of Ash' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
