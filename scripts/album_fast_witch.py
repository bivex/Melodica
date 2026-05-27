# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/album_fast_witch.py — Fast Witch House Album Generator.

Album: "S T A T I C   P R A Y E R"
Fast, hooky witch house — 130-160 BPM with half-time feel.

Formula per track:
  Intro  — noise + pad + vocal sample
  Build  — hats rise, bass swells
  Drop   — massive distorted bass + short synth hook (3-5 notes)
  Break  — atmosphere, reverse/echo, sudden silence
  Final  — everything collapses into noise

Key principles:
  - Half-time drums over fast tempo (feels slow, drives fast)
  - Simple hooks: 3-5 note dark motifs, repetition + variation
  - Contrast: silence before drop, clean before dirty
  - Sound design: detune, chorus, long reverb, cassette grit
  - Pitched vocals, reverse textures

Artists: Sidewalks and Skeletons, BLVCK CEILING, Crystal Castles, Salem
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
from melodica.generators.drone import DroneGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.witch_house import WitchHouseGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.rhythm import get_rhythm
from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.midi import export_multitrack_midi


def generate_track(name, parts, tracks, out_dir, bpm):
    print(f"  > {name}")
    config = IdeaToolConfig(
        style="cinematic",
        parts=parts,
        tracks=tracks,
        use_voice_leading=True,
        run_doctor=True,
        doctor_register=True,
    )
    notes_dict = IdeaTool(config).generate()
    tracks_data = {k: v for k, v in notes_dict.items() if not k.startswith("_") and isinstance(v, list)}

    instruments_map = {t.name: FLUID_R3_PROGRAMS.get(t.instrument, 0) for t in tracks}

    safe = name.translate(str.maketrans("", "", "▲▼✝")).strip().replace(" ", "_")
    file_path = out_dir / f"{safe}.mid"
    export_multitrack_midi(tracks_data, str(file_path), bpm=bpm, instruments=instruments_map)
    return file_path


def main():
    print("=" * 80)
    print("  S T A T I C   P R A Y E R")
    print("  10 tracks — fast witch house (130-160 BPM)")
    print("=" * 80)

    out_dir = Path("output/album_fast_witch")
    out_dir.mkdir(exist_ok=True, parents=True)

    # Dark scales — Phrygian / Locrian / Harmonic Minor dominate
    scales = {
        "static":     Scale(9, Mode.PHRYGIAN),           # A Phrygian
        "void":       Scale(0, Mode.LOCRIAN),             # C Locrian
        "cassette":   Scale(2, Mode.HARMONIC_MINOR),      # D harmonic minor
        "pitched":    Scale(4, Mode.PHRYGIAN),            # E Phrygian
        "filter":     Scale(7, Mode.NATURAL_MINOR),       # G natural minor
        "tape":       Scale(9, Mode.HARMONIC_MINOR),      # A harmonic minor
        "noise":      Scale(0, Mode.DOUBLE_HARMONIC),     # C double harmonic
        "reverse":    Scale(5, Mode.LOCRIAN),             # F Locrian
        "distorted":  Scale(2, Mode.PHRYGIAN),            # D Phrygian
        "broken":     Scale(9, Mode.HUNGARIAN_MINOR),     # A Hungarian minor
    }

    # ==================================================================
    # Track 1: S T A T I C   P R A Y E R — The manifesto
    # Intro → Build → Drop → Break → Final
    # ==================================================================
    generate_track("1 STATIC PRAYER",
        parts=[
            # Intro: noise + pad + vocal
            IdeaPart("Intro", 8, scales["static"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Vocal":    structure_to_schedule("R A", 4),
                    "Noise":    structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            # Build: hats + bass swell
            IdeaPart("Build", 8, scales["static"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            # Drop: distorted bass + hook
            IdeaPart("Drop", 16, scales["static"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var B", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Pad":      structure_to_schedule("A", 16),
                    "Vocal":    structure_to_schedule("R R A R", 4),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            # Break: atmosphere, reverse
            IdeaPart("Break", 8, scales["static"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Reverse":  structure_to_schedule("R R R A", 4),
                    "Vocal":    structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            # Final: collapse
            IdeaPart("Final", 8, scales["static"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A R", 4),
                    "Noise":    structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.5, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="phrygian_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Vocal", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.2, octave_shift=1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="open_hi_hat", density=0.6, octave_shift=2),
            TrackConfig(name="Noise", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.2, octave_shift=-2),
            TrackConfig(name="Reverse", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sweep_pad", density=0.2, octave_shift=2),
        ],
        out_dir=out_dir, bpm=140)

    # ==================================================================
    # Track 2: V O I D   F R E Q U E N C Y — Sub-bass worship
    # ==================================================================
    generate_track("2 VOID FREQUENCY",
        parts=[
            IdeaPart("Intro", 8, scales["void"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Sub":      structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["void"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Sub":      structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["void"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A A:var A B", 4),
                    "Sub":      structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Pad":      structure_to_schedule("A", 16),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["void"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Sub":      structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["void"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Sub":      structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A R", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="pluck", density=0.3, octave_shift=1),
            TrackConfig(name="Sub", generator=DarkBassGenerator(mode="doom"),
                instrument="synth_bass", density=0.5, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="tritone_drone"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="closed_hi_hat", density=0.6, octave_shift=2),
        ],
        out_dir=out_dir, bpm=150)

    # ==================================================================
    # Track 3: C A S S E T T E   R I T U A L — Lo-fi texture
    # ==================================================================
    generate_track("3 CASSETTE RITUAL",
        parts=[
            IdeaPart("Intro", 8, scales["cassette"], 135,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Noise":    structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                    "Vocal":    structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["cassette"], 135,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["cassette"], 135,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var A", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Vocal":    structure_to_schedule("R R A B", 4),
                    "Pad":      structure_to_schedule("A", 16),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["cassette"], 135,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Vocal":    structure_to_schedule("A R", 4),
                    "Noise":    structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["cassette"], 135,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Noise":    structure_to_schedule("A", 8),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.3, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.5, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="drag"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="minor_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Vocal", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.2, octave_shift=0),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="closed_hi_hat", density=0.6, octave_shift=2),
            TrackConfig(name="Noise", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.2, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=135)

    # ==================================================================
    # Track 4: P I T C H E D   G H O S T S — Pitched vocal ritual
    # ==================================================================
    generate_track("4 PITCHED GHOSTS",
        parts=[
            IdeaPart("Intro", 8, scales["pitched"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Vocal":    structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["pitched"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Vocal":    structure_to_schedule("A B", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["pitched"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var B", 4),
                    "Vocal":    structure_to_schedule("A B A R", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Pad":      structure_to_schedule("A", 16),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["pitched"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Vocal":    structure_to_schedule("A R", 4),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["pitched"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Vocal":    structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A R", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.3, octave_shift=1),
            TrackConfig(name="Vocal", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.3, octave_shift=-1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.5, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="occult"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="chromatic_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="open_hi_hat", density=0.6, octave_shift=2),
        ],
        out_dir=out_dir, bpm=145)

    # ==================================================================
    # Track 5: F I L T E R   D R O P — Filter sweep into massive drop
    # ==================================================================
    generate_track("5 FILTER DROP",
        parts=[
            IdeaPart("Intro", 8, scales["filter"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Arp":      structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["filter"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Arp":      structure_to_schedule("A B", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["filter"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A A:var B A:var", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Pad":      structure_to_schedule("A", 16),
                    "Arp":      structure_to_schedule("A B", 8),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["filter"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Arp":      structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["filter"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A R", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="industrial"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="occult"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="dim_cluster"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Arp", generator=ArpeggiatorGenerator(pattern="up",
                rhythm=get_rhythm("straight_16ths")), instrument="bright_piano", density=0.4, octave_shift=1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="closed_hi_hat", density=0.6, octave_shift=2),
        ],
        out_dir=out_dir, bpm=140)

    # ==================================================================
    # Track 6: T A P E   S A T U R A T I N — Overdriven saturation
    # ==================================================================
    generate_track("6 TAPE SATURATION",
        parts=[
            IdeaPart("Intro", 8, scales["tape"], 155,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Noise":    structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["tape"], 155,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["tape"], 155,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var B", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Lead":     structure_to_schedule("R A R B", 4),
                    "Pad":      structure_to_schedule("A", 16),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["tape"], 155,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Noise":    structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["tape"], 155,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A R", 4),
                    "Noise":    structure_to_schedule("A", 8),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Lead", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("straight_8ths")), instrument="sawtooth", density=0.3, octave_shift=1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="phrygian_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="open_hi_hat", density=0.6, octave_shift=2),
            TrackConfig(name="Noise", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.2, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=155)

    # ==================================================================
    # Track 7: N O I S E   C O L L A P S E — Peak intensity
    # ==================================================================
    generate_track("7 NOISE COLLAPSE",
        parts=[
            IdeaPart("Intro", 8, scales["noise"], 160,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Noise":    structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["noise"], 160,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["noise"], 160,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var B", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Lead":     structure_to_schedule("A B", 8),
                    "Pad":      structure_to_schedule("A", 16),
                    "Choir":    structure_to_schedule("R A R B", 4),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["noise"], 160,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Noise":    structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["noise"], 160,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A A", 4),
                    "Noise":    structure_to_schedule("A A", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.5, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="industrial"),
                instrument="synth_bass", density=0.7, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="occult"),
                instrument="percussion", density=0.6, octave_shift=-1),
            TrackConfig(name="Lead", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("straight_8ths")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="dim_cluster"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.3, octave_shift=1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="open_hi_hat", density=0.7, octave_shift=2),
            TrackConfig(name="Noise", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.3, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=160)

    # ==================================================================
    # Track 8: R E V E R S E   S P E L L — Reverse textures
    # ==================================================================
    generate_track("8 REVERSE SPELL",
        parts=[
            IdeaPart("Intro", 8, scales["reverse"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Reverse":  structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["reverse"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["reverse"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A A:var B A:var", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Reverse":  structure_to_schedule("R A R B", 4),
                    "Pad":      structure_to_schedule("A", 16),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["reverse"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Reverse":  structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["reverse"], 140,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A R", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Reverse":  structure_to_schedule("A R", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.5, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="drag"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Reverse", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="sweep_pad", density=0.3, octave_shift=1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="minor_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="closed_hi_hat", density=0.6, octave_shift=2),
        ],
        out_dir=out_dir, bpm=140)

    # ==================================================================
    # Track 9: D I S T O R T E D   H Y M N — Overdriven melody
    # ==================================================================
    generate_track("9 DISTORTED HYMN",
        parts=[
            IdeaPart("Intro", 8, scales["distorted"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Vocal":    structure_to_schedule("R A", 4),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["distorted"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["distorted"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var B", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Vocal":    structure_to_schedule("A B R R", 4),
                    "Pad":      structure_to_schedule("A", 16),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["distorted"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Vocal":    structure_to_schedule("A R", 4),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 8, scales["distorted"], 145,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Drums":    structure_to_schedule("A R", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="dark_pulse"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="occult"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Vocal", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("half_note")), instrument="choir", density=0.3, octave_shift=0),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="phrygian_pad"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="open_hi_hat", density=0.6, octave_shift=2),
        ],
        out_dir=out_dir, bpm=145)

    # ==================================================================
    # Track 10: B R O K E N   L O O P — The cycle breaks
    # ==================================================================
    generate_track("10 BROKEN LOOP",
        parts=[
            IdeaPart("Intro", 8, scales["broken"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Noise":    structure_to_schedule("A", 8),
                    "Pad":      structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTRO,
                section_function=SectionFunction.SUSTAIN,
            ),
            IdeaPart("Build", 8, scales["broken"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("R A", 4),
                    "Bass":     structure_to_schedule("A", 8),
                    "Hats":     structure_to_schedule("A", 8),
                },
                section_type=SectionRole.BREAKDOWN,
                section_function=SectionFunction.BUILD,
            ),
            IdeaPart("Drop", 16, scales["broken"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A B A:var B", 4),
                    "Bass":     structure_to_schedule("A B", 8),
                    "Drums":    structure_to_schedule("A B", 8),
                    "Lead":     structure_to_schedule("R A R B", 4),
                    "Pad":      structure_to_schedule("A", 16),
                    "Choir":    structure_to_schedule("R A R B", 4),
                },
                section_type=SectionRole.DROP,
                section_function=SectionFunction.RELEASE,
            ),
            IdeaPart("Break", 8, scales["broken"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Pad":      structure_to_schedule("A", 8),
                    "Noise":    structure_to_schedule("A", 8),
                },
                section_type=SectionRole.INTERLUDE,
                section_function=SectionFunction.BREAK,
            ),
            IdeaPart("Final", 12, scales["broken"], 150,
                progression_type="functional_hmm",
                track_phrase_schedules={
                    "Hook":     structure_to_schedule("A A A R", 3),
                    "Bass":     structure_to_schedule("A", 12),
                    "Drums":    structure_to_schedule("A A R", 4),
                    "Noise":    structure_to_schedule("R R A", 4),
                },
                section_type=SectionRole.CODA,
                section_function=SectionFunction.FADE,
            ),
        ],
        tracks=[
            TrackConfig(name="Hook", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("half_note")), instrument="sawtooth", density=0.4, octave_shift=1),
            TrackConfig(name="Bass", generator=DarkBassGenerator(mode="industrial"),
                instrument="synth_bass", density=0.6, octave_shift=-2),
            TrackConfig(name="Drums", generator=WitchHouseGenerator(variant="classic"),
                instrument="percussion", density=0.5, octave_shift=-1),
            TrackConfig(name="Lead", generator=MelodyGenerator(mode="scale_walk",
                rhythm=get_rhythm("straight_8ths")), instrument="sawtooth", density=0.3, octave_shift=1),
            TrackConfig(name="Pad", generator=DarkPadGenerator(mode="dim_cluster"),
                instrument="dark_pad", density=0.3, octave_shift=-1),
            TrackConfig(name="Choir", generator=ChordGenerator(voicing="closed",
                rhythm=get_rhythm("whole_note")), instrument="choir", density=0.3, octave_shift=1),
            TrackConfig(name="Hats", generator=MelodyGenerator(mode="chord_tones",
                rhythm=get_rhythm("straight_16ths")), instrument="open_hi_hat", density=0.6, octave_shift=2),
            TrackConfig(name="Noise", generator=DroneGenerator(variant="tonic"),
                instrument="dark_pad", density=0.3, octave_shift=-2),
        ],
        out_dir=out_dir, bpm=150)

    print("\n" + "=" * 80)
    print("  S T A T I C   P R A Y E R   C O M P L E T E")
    print(f"  Output: {out_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
