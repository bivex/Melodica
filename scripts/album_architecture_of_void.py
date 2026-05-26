# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_architecture_of_void.py — Non-Standard Dramatic Album Generator.

Album: "Architecture of the Void"
Music for impossible buildings — each track is a room that shouldn't exist.

Tracks:
1.  Spiral Staircase    — 5/4 Messiaen mode 2, ascending into nowhere
2.  Glass Cathedral     — 3/2 Whole tone, transparent and cold
3.  The Clock Room      — 7/8 Suspense, ticking mechanism
4.  Flooded Library     — 6/8 Quarter-tone minor, water rising
5.  Burning Garden      — 9/8 Enigmatic, flames on alien flowers
6.  The Mirror Hall     — 5/4 Augmented, infinite reflections
7.  Collision           — 11/8 Altered → Horror Cluster, walls collapsing
8.  Atrium Of Rain      — 7/4 Lydian augmented, water from no ceiling
9.  The Last Room       — 4/4 Pedal minor, back where we started

Each track uses a non-standard time signature and an exotic mode.
Track 7 has a dramatic 2-phase structure with mode shift.
All functional_hmm with phrase-based structures.

Powered by Functional HMM, FluidR3, and architectural madness.
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
    print("  A R C H I T E C T U R E   O F   T H E   V O I D")
    print("  9 tracks — non-standard dramatic album")
    print("=" * 80)

    out_dir = Path("output/album_architecture_of_void")
    out_dir.mkdir(exist_ok=True, parents=True)

    # ------------------------------------------------------------------
    # Track 1: Spiral Staircase — 5/4 Messiaen mode 2, ascending nowhere
    # ------------------------------------------------------------------
    generate_track("1 Spiral Staircase",
        parts=[IdeaPart(
            name="Ascent", bars=16,
            scale=Scale(2, Mode.MESSIAEN_2),
            tempo=72, time_signature=(5, 4),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano":   structure_to_schedule("A B A:var C", 4),
                "Strings": structure_to_schedule("A", 16),
                "Harp":    structure_to_schedule("R A B A:var", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.6),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.7),
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="harp", density=0.4, octave_shift=1),
        ],
        out_dir=out_dir, bpm=72)

    # ------------------------------------------------------------------
    # Track 2: Glass Cathedral — 3/2 Whole tone, transparent cold
    # ------------------------------------------------------------------
    generate_track("2 Glass Cathedral",
        parts=[IdeaPart(
            name="Transparency", bars=12,
            scale=Scale(2, Mode.WHOLE_TONE),
            tempo=55, time_signature=(3, 2),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Organ": structure_to_schedule("A B", 6),
                "Choir": structure_to_schedule("R A B", 4),
                "Bells": structure_to_schedule("A", 12),
            },
        )],
        tracks=[
            TrackConfig(name="Organ", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="organ", density=0.6),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.5),
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="tubular_bells", density=0.2),
        ],
        out_dir=out_dir, bpm=55)

    # ------------------------------------------------------------------
    # Track 3: The Clock Room — 7/8 Suspense, ticking mechanism
    # ------------------------------------------------------------------
    generate_track("3 The Clock Room",
        parts=[IdeaPart(
            name="Ticking", bars=16,
            scale=Scale(2, Mode.SUSPENSE),
            tempo=88, time_signature=(7, 8),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harpsichord": structure_to_schedule("A B A:var C", 4),
                "MusicBox":    structure_to_schedule("A", 16),
                "Bass":        structure_to_schedule("R A", 8),
            },
        )],
        tracks=[
            TrackConfig(name="Harpsichord", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:dense")), instrument="harpsichord", density=0.7),
            TrackConfig(name="MusicBox", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="music_box", density=0.6, octave_shift=1),
            TrackConfig(name="Bass", generator=BassGenerator(style="walking"),
                instrument="cello", density=0.5, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=88)

    # ------------------------------------------------------------------
    # Track 4: Flooded Library — 6/8 Quarter-tone minor, water rising
    # ------------------------------------------------------------------
    generate_track("4 Flooded Library",
        parts=[IdeaPart(
            name="Rising", bars=16,
            scale=Scale(2, Mode.QUARTER_TONE_MINOR),
            tempo=62, time_signature=(6, 8),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Cello": structure_to_schedule("A B C B:var", 4),
                "Flute": structure_to_schedule("R A R B", 4),
                "Drone": structure_to_schedule("A", 16),
                "Pad":   structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Cello", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="cello", density=0.6),
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="flute", density=0.4),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5, octave_shift=-1),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.25),
        ],
        out_dir=out_dir, bpm=62)

    # ------------------------------------------------------------------
    # Track 5: Burning Garden — 9/8 Enigmatic, flames on alien flowers
    # ------------------------------------------------------------------
    generate_track("5 Burning Garden",
        parts=[IdeaPart(
            name="Flames", bars=16,
            scale=Scale(2, Mode.ENIGMATIC),
            tempo=78, time_signature=(9, 8),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":     structure_to_schedule("A B A:var C", 4),
                "Strings": structure_to_schedule("A B", 8),
                "Taiko":   structure_to_schedule("R A", 8),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="sitar", density=0.6),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="tremolo",
                rhythm=get_rhythm("whole_note")), instrument="tremolo_strings", density=0.8),
            TrackConfig(name="Taiko", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=0.5),
        ],
        out_dir=out_dir, bpm=78)

    # ------------------------------------------------------------------
    # Track 6: The Mirror Hall — 5/4 Augmented, infinite reflections
    # ------------------------------------------------------------------
    generate_track("6 The Mirror Hall",
        parts=[IdeaPart(
            name="Reflections", bars=16,
            scale=Scale(2, Mode.AUGMENTED),
            tempo=65, time_signature=(5, 4),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano": structure_to_schedule("A B C B:var", 4),
                "Choir": structure_to_schedule("R A B A:var", 4),
                "Pad":   structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("markov:ballad")), instrument="bright_piano", density=0.6),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.5),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="pad", density=0.35),
        ],
        out_dir=out_dir, bpm=65)

    # ------------------------------------------------------------------
    # Track 7: Collision — 11/8 Altered → Horror Cluster, walls collapse
    # 2-phase: creeping dread → violent destruction with mode shift
    # ------------------------------------------------------------------
    generate_track("7 Collision",
        parts=[
            IdeaPart("Creeping", 12,
                scale=Scale(2, Mode.ALTERED),
                tempo=80, time_signature=(11, 8),
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings": structure_to_schedule("A B", 6),
                    "Brass":   structure_to_schedule("R A B", 4),
                    "Perc":    structure_to_schedule("R A", 6),
                }),
            IdeaPart("Collapse", 12,
                scale=Scale(2, Mode.HORROR_CLUSTER),
                tempo=120, time_signature=(11, 8),
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings": structure_to_schedule("C D E", 4),
                    "Brass":   structure_to_schedule("C D E", 4),
                    "Perc":    structure_to_schedule("C D E", 4),
                }),
        ],
        tracks=[
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="staccato",
                rhythm=get_rhythm("straight_quarters")), instrument="strings", density=0.9),
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_quarters")), instrument="brass", density=0.8),
            TrackConfig(name="Perc", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=0.9),
        ],
        out_dir=out_dir, bpm=80)

    # ------------------------------------------------------------------
    # Track 8: Atrium Of Rain — 7/4 Lydian augmented, rain from no sky
    # ------------------------------------------------------------------
    generate_track("8 Atrium Of Rain",
        parts=[IdeaPart(
            name="Rainfall", bars=16,
            scale=Scale(2, Mode.LYDIAN_AUG_MODE),
            tempo=58, time_signature=(7, 4),
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harp":    structure_to_schedule("A B A:var C", 4),
                "Strings": structure_to_schedule("A", 16),
                "Flute":   structure_to_schedule("R A B A:var", 4),
                "Pad":     structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="harp", density=0.7, octave_shift=1),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="chamber", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.7),
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="flute", density=0.4),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="pad", density=0.3),
        ],
        out_dir=out_dir, bpm=58)

    # ------------------------------------------------------------------
    # Track 9: The Last Room — 4/4 Pedal minor, back where we started
    # ------------------------------------------------------------------
    generate_track("9 The Last Room",
        parts=[IdeaPart(
            name="Return", bars=20,
            scale=Scale(2, Mode.PEDAL_MINOR),
            tempo=44,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Piano": structure_to_schedule("A B A:var C D", 4),
                "Drone": structure_to_schedule("A", 20),
                "Echo":  structure_to_schedule("R A R B R A", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Piano", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="piano", density=0.4),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5, octave_shift=-1),
            TrackConfig(name="Echo", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.2),
        ],
        out_dir=out_dir, bpm=44)

    print()
    print("  Album 'Architecture of the Void' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
