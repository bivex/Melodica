# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_sikah_nights.py — Arabic Maqam Album Generator.

Album: "Sikah Nights"
A journey through desert nights — from dusk calls to palace dances to silence.

Tracks:
1.  Dunes At Dusk    — Oud + drone, endless sand
2.  Caravan          — Oud + strings + bass, slow march across desert
3.  Spice Market     — Oud + music box + percussion, bustling bazaar
4.  Sultan's Court   — Full ensemble, regal ceremony
5.  Snake Charmer    — Flute + sitar + drone, hypnotic melody
6.  Desert Storm     — Taiko + brass + strings, fury of sand
7.  Oasis            — Harp + flute + pad, water under palms
8.  Minaret          — Choir + organ + bells, call to prayer
9.  Sand And Stars   — Oud + flute, night returns to silence

All tracks use Arabic Sikah and related maqam modes with functional_hmm
progressions and phrase-based structure.

Powered by Functional HMM, FluidR3, and Maqam aesthetics.
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
from melodica.generators.harp import HarpGenerator
from melodica.generators.orchestral_woodwinds import FluteGenerator
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
    print("  S I K A H   N I G H T S")
    print("  9 tracks — Arabic maqam album")
    print("=" * 80)

    out_dir = Path("output/album_sikah_nights")
    out_dir.mkdir(exist_ok=True, parents=True)

    scales = {
        "sikah_d":    Scale(2, Mode.ARABIC_SIKAH),
        "sikah_e":    Scale(4, Mode.ARABIC_SIKAH),
        "sikah_a":    Scale(9, Mode.ARABIC_SIKAH),
        "bayati":     Scale(2, Mode.BAYATI),
        "phryg_dom":  Scale(2, Mode.PHRYGIAN_DOMINANT),
        "byzantine":  Scale(2, Mode.BYZANTINE),
        "persian":    Scale(2, Mode.PERSIAN),
        "dbl_harm":   Scale(2, Mode.DOUBLE_HARMONIC),
    }

    # ------------------------------------------------------------------
    # Track 1: Dunes At Dusk — Oud + drone + harp + flute, endless sand
    # ------------------------------------------------------------------
    generate_track("1 Dunes At Dusk",
        parts=[IdeaPart(
            name="Horizon", bars=16, scale=scales["sikah_d"], tempo=48,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":   structure_to_schedule("A B A:var C", 4),
                "Drone": structure_to_schedule("A", 16),
                "Wind":  structure_to_schedule("R A R B", 4),
                "Harp":  structure_to_schedule("R R A B", 4),
                "Flute": structure_to_schedule("R A R A:var", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="sitar", density=0.5),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5, octave_shift=-1),
            TrackConfig(name="Wind", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="sweep_pad", density=0.25),
            TrackConfig(name="Harp", generator=HarpGenerator(pattern="arpeggio",
                direction="up", octave_span=2), instrument="harp", density=0.4, octave_shift=1),
            TrackConfig(name="Flute", generator=FluteGenerator(articulation="sustained",
                vibrato=True, register=2), instrument="pan_flute", density=0.3, octave_shift=1),
        ],
        out_dir=out_dir, bpm=48)

    # ------------------------------------------------------------------
    # Track 2: Caravan — Oud + strings + bass + harp + flute, slow desert march
    # ------------------------------------------------------------------
    generate_track("2 Caravan",
        parts=[IdeaPart(
            name="March", bars=16, scale=scales["bayati"], tempo=62,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":     structure_to_schedule("A B", 8),
                "Strings": structure_to_schedule("A", 16),
                "Bass":    structure_to_schedule("A", 16),
                "Perc":    structure_to_schedule("R A", 8),
                "Harp":    structure_to_schedule("R A B A:var", 4),
                "Flute":   structure_to_schedule("R R A B", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="sitar", density=0.6),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("whole_note")), instrument="strings", density=0.7),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="cello", density=0.6, octave_shift=-1),
            TrackConfig(name="Perc", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="timpani", density=0.5),
            TrackConfig(name="Harp", generator=HarpGenerator(pattern="arpeggio",
                direction="up", octave_span=2), instrument="harp", density=0.45, octave_shift=1),
            TrackConfig(name="Flute", generator=FluteGenerator(articulation="sustained",
                vibrato=True, register=2), instrument="flute", density=0.35, octave_shift=1),
        ],
        out_dir=out_dir, bpm=62)

    # ------------------------------------------------------------------
    # Track 3: Spice Market — Oud + music box + perc, bustling bazaar
    # ------------------------------------------------------------------
    generate_track("3 Spice Market",
        parts=[IdeaPart(
            name="Bazaar", bars=16, scale=scales["phryg_dom"], tempo=85,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":      structure_to_schedule("A B A:var C", 4),
                "MusicBox": structure_to_schedule("R A B A:var", 4),
                "Perc":     structure_to_schedule("A B", 8),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:dense")), instrument="sitar", density=0.7),
            TrackConfig(name="MusicBox", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="music_box", density=0.5, octave_shift=1),
            TrackConfig(name="Perc", generator=MelodyGenerator(mode="downbeat_chord",
                rhythm=get_rhythm("straight_quarters")), instrument="taiko", density=0.7),
        ],
        out_dir=out_dir, bpm=85)

    # ------------------------------------------------------------------
    # Track 4: Sultan's Court — Full ensemble, regal ceremony
    # ------------------------------------------------------------------
    generate_track("4 Sultan's Court",
        parts=[
            IdeaPart("Procession", 12, scales["dbl_harm"], 72,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Brass":   structure_to_schedule("A B", 6),
                    "Strings": structure_to_schedule("A", 12),
                    "Choir":   structure_to_schedule("R A B", 4),
                    "Bass":    structure_to_schedule("A", 12),
                }),
            IdeaPart("Audience", 12, scales["dbl_harm"], 80,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Brass":   structure_to_schedule("C D", 6),
                    "Strings": structure_to_schedule("C D", 6),
                    "Choir":   structure_to_schedule("C D", 6),
                    "Bass":    structure_to_schedule("C D", 6),
                }),
        ],
        tracks=[
            TrackConfig(name="Brass", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_quarters")), instrument="french_horn", density=0.7),
            TrackConfig(name="Strings", generator=StringsEnsembleGenerator(
                section_size="full", articulation="sustained",
                rhythm=get_rhythm("half_note")), instrument="strings", density=0.8),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.6),
            TrackConfig(name="Bass", generator=BassGenerator(style="root_fifth"),
                instrument="tuba", density=0.6, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=72)

    # ------------------------------------------------------------------
    # Track 5: Snake Charmer — Flute + sitar + drone, hypnotic
    # ------------------------------------------------------------------
    generate_track("5 Snake Charmer",
        parts=[IdeaPart(
            name="Hypnosis", bars=16, scale=scales["sikah_e"], tempo=70,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Flute":  structure_to_schedule("A B C B:var", 4),
                "Sitar":  structure_to_schedule("R A R B", 4),
                "Drone":  structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="pan_flute", density=0.6, octave_shift=1),
            TrackConfig(name="Sitar", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="sitar", density=0.4),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.5, octave_shift=-1),
        ],
        out_dir=out_dir, bpm=70)

    # ------------------------------------------------------------------
    # Track 6: Desert Storm — Taiko + brass + strings, fury
    # ------------------------------------------------------------------
    generate_track("6 Desert Storm",
        parts=[
            IdeaPart("Gathering", 12, scales["persian"], 90,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings": structure_to_schedule("A B", 6),
                    "Brass":   structure_to_schedule("R A B", 4),
                    "Perc":    structure_to_schedule("R A", 6),
                }),
            IdeaPart("Fury", 12, scales["persian"], 115,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Strings": structure_to_schedule("C D E", 4),
                    "Brass":   structure_to_schedule("C D", 6),
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
        out_dir=out_dir, bpm=90)

    # ------------------------------------------------------------------
    # Track 7: Oasis — Harp + flute + pad, water under palms
    # ------------------------------------------------------------------
    generate_track("7 Oasis",
        parts=[IdeaPart(
            name="Water", bars=16, scale=scales["sikah_a"], tempo=55,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Harp":   structure_to_schedule("A B A:var C", 4),
                "Flute":  structure_to_schedule("R A B A:var", 4),
                "Pad":    structure_to_schedule("A", 16),
            },
        )],
        tracks=[
            TrackConfig(name="Harp", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="harp", density=0.7, octave_shift=1),
            TrackConfig(name="Flute", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("probabilistic:sparse")), instrument="flute", density=0.4),
            TrackConfig(name="Pad", generator=NebulaGenerator(variant="cloud",
                rhythm=get_rhythm("whole_note")), instrument="pad", density=0.3),
        ],
        out_dir=out_dir, bpm=55)

    # ------------------------------------------------------------------
    # Track 8: Minaret — Choir + organ + bells, call to prayer
    # ------------------------------------------------------------------
    generate_track("8 Minaret",
        parts=[IdeaPart(
            name="Prayer", bars=20, scale=scales["byzantine"], tempo=50,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Organ":  structure_to_schedule("A B C B:var D", 4),
                "Choir":  structure_to_schedule("A B C D A:var", 4),
                "Bells":  structure_to_schedule("R A R A", 5),
            },
        )],
        tracks=[
            TrackConfig(name="Organ", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="organ", density=0.7),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir_pad", density=0.6),
            TrackConfig(name="Bells", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("whole_note")), instrument="tubular_bells", density=0.2),
        ],
        out_dir=out_dir, bpm=50)

    # ------------------------------------------------------------------
    # Track 9: Sand And Stars — Oud + flute + harp + drone, night returns to silence
    # ------------------------------------------------------------------
    generate_track("9 Sand And Stars",
        parts=[IdeaPart(
            name="Return", bars=20, scale=scales["sikah_d"], tempo=42,
            progression_type="functional_hmm",
            track_phrase_schedules={
                "Oud":   structure_to_schedule("A B A:var C D", 4),
                "Flute": structure_to_schedule("R A B A:var C", 4),
                "Drone": structure_to_schedule("A", 20),
                "Harp":  structure_to_schedule("R R A B A:var", 4),
            },
        )],
        tracks=[
            TrackConfig(name="Oud", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("markov:ballad")), instrument="sitar", density=0.5),
            TrackConfig(name="Flute", generator=FluteGenerator(articulation="sustained",
                vibrato=True, register=2, note_density=0.7), instrument="shakuhachi",
                density=0.3, octave_shift=1),
            TrackConfig(name="Drone", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.4, octave_shift=-1),
            TrackConfig(name="Harp", generator=HarpGenerator(pattern="arpeggio",
                direction="up", octave_span=2, velocity_decay=0.88), instrument="harp",
                density=0.3, octave_shift=1),
        ],
        out_dir=out_dir, bpm=42)

    print()
    print("  Album 'Sikah Nights' generated.")
    print(f"  Files: {out_dir.absolute()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
