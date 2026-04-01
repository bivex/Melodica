#!/usr/bin/env python3
"""
dark_fantasy.py — Dark Fantasy Orchestral Composition Generator.

Generates a multi-section dark fantasy piece with:
- Ominous chord progressions
- Multiple orchestral layers
- Dynamic tension arcs
- Mastered output as MIDI

Usage:
    python3 dark_fantasy.py [--duration 3] [--tempo 72] [--output dark_fantasy.mid]
"""

import sys
import math
import random
import argparse
from pathlib import Path
from dataclasses import dataclass

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    StrumPatternGenerator,
    FingerpickingGenerator,
    PercussionGenerator,
    PianoRunGenerator,
    GeneratorParams,
)
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
from melodica.composer import TensionCurve, get_style
from melodica.midi import export_multitrack_midi


# ---------------------------------------------------------------------------
# Dark Fantasy Scales
# ---------------------------------------------------------------------------

SCALES = {
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "byzantine": Scale(root=0, mode=Mode.BYZANTINE),
    "persian": Scale(root=0, mode=Mode.PERSIAN),
}


# ---------------------------------------------------------------------------
# Section definitions
# ---------------------------------------------------------------------------


@dataclass
class Section:
    """A section of the composition."""

    name: str
    bars: int
    scale_name: str
    key_root: int
    progression: list[int]
    mood: str  # "ominous", "battle", "mystery", "triumph", "despair"
    tempo_factor: float = 1.0  # multiplier for base tempo


def build_sections(total_bars: int) -> list[Section]:
    """Build dark fantasy sections that fill total_bars."""
    sections = [
        Section("Prologue", max(4, total_bars // 8), "phrygian", 0, [1, 5, 6, 4], "ominous", 0.85),
        Section(
            "The Dark Forest",
            max(4, total_bars // 6),
            "harmonic_minor",
            0,
            [1, 4, 5, 1],
            "mystery",
            0.9,
        ),
        Section(
            "Rising Threat",
            max(4, total_bars // 6),
            "hungarian_minor",
            0,
            [1, 5, 6, 3],
            "battle",
            1.0,
        ),
        Section(
            "The Ancient Temple",
            max(4, total_bars // 8),
            "byzantine",
            5,
            [1, 4, 5, 1],
            "mystery",
            0.8,
        ),
        Section(
            "Final Confrontation",
            max(4, total_bars // 4),
            "harmonic_minor",
            0,
            [1, 5, 4, 5, 1],
            "triumph",
            1.1,
        ),
        Section(
            "Epilogue", max(4, total_bars // 8), "natural_minor", 0, [1, 4, 1, 5], "despair", 0.75
        ),
    ]

    # Adjust to fill total_bars
    total_section_bars = sum(s.bars for s in sections)
    if total_section_bars < total_bars:
        sections[-2].bars += total_bars - total_section_bars
    elif total_section_bars > total_bars:
        excess = total_section_bars - total_bars
        for s in reversed(sections):
            if s.bars > 4:
                cut = min(excess, s.bars - 4)
                s.bars -= cut
                excess -= cut
                if excess <= 0:
                    break

    return sections


# ---------------------------------------------------------------------------
# Track generators per mood
# ---------------------------------------------------------------------------


def make_melody_track(mood: str, params: GeneratorParams) -> TrackConfig:
    p = {"harmony_note_probability": 0.7}
    if mood == "battle":
        p["note_range_low"] = 60
        p["note_range_high"] = 84
    elif mood == "mystery":
        p["note_range_low"] = 55
        p["note_range_high"] = 76
    elif mood == "despair":
        p["note_range_low"] = 48
        p["note_range_high"] = 72
    else:
        p["note_range_low"] = 55
        p["note_range_high"] = 80

    return TrackConfig(
        name="melody",
        generator_type="melody",
        instrument="strings",
        density=0.5,
        arrangement="AABA" if mood != "battle" else "ABAB",
        params=p,
    )


def make_bass_track(mood: str) -> TrackConfig:
    return TrackConfig(
        name="bass",
        generator_type="bass",
        instrument="cello",
        density=0.6,
        octave_shift=-1,
        params={"allowed_notes": ["root", "fourth"], "note_movement": "alternating"},
    )


def make_chord_track(mood: str) -> TrackConfig:
    voicing = "spread" if mood in ("mystery", "despair") else "open"
    return TrackConfig(
        name="chords",
        generator_type="chord",
        instrument="strings_pad",
        density=0.4,
        params={"voicing": voicing},
    )


def make_arp_track(mood: str) -> TrackConfig:
    pattern = "up_down" if mood == "mystery" else "converge" if mood == "ominous" else "up"
    return TrackConfig(
        name="arpeggio",
        generator_type="arpeggiator",
        instrument="harp",
        density=0.3,
        params={"pattern": pattern, "note_duration": 0.25, "octaves": 2},
    )


def make_ostinato_track(mood: str) -> TrackConfig:
    pattern = "1-3-5-3" if mood != "battle" else "1-2-1-3-1-4-1-5"
    return TrackConfig(
        name="ostinato",
        generator_type="ostinato",
        instrument="strings_staccato",
        density=0.5,
        params={"pattern": pattern, "repeat_notes": 2},
    )


def make_percussion_track(mood: str) -> TrackConfig:
    pattern = "rock" if mood == "battle" else "bossa"
    return TrackConfig(
        name="percussion",
        generator_type="percussion",
        instrument="timpani",
        density=0.4,
        params={"pattern_name": pattern, "instruments": ["kick", "crash", "tom_hi"]},
    )


def make_piano_run_track(mood: str) -> TrackConfig:
    technique = "waterfall" if mood in ("despair", "mystery") else "straddle"
    return TrackConfig(
        name="piano_sweep",
        generator_type="piano_run",
        instrument="piano",
        density=0.3,
        arrangement="ABAB",
        params={"technique": technique, "notes_per_run": 12, "motion": "up"},
    )


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------


def generate_dark_fantasy(
    duration_minutes: float = 3.0,
    tempo: int = 72,
    key_root: int = 0,  # C
    seed: int | None = None,
) -> tuple[dict[str, list[NoteInfo]], list[ChordLabel], list[Section]]:
    """
    Generate a dark fantasy orchestral composition.

    Returns (tracks_dict, chords, sections).
    """
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    total_beats = duration_minutes * 60 * (tempo / 60)
    total_bars = max(8, int(total_beats / beats_per_bar))

    sections = build_sections(total_bars)
    all_tracks: dict[str, list[NoteInfo]] = {}
    all_chords: list[ChordLabel] = []
    beat_offset = 0.0

    for section in sections:
        section_beats = section.bars * beats_per_bar
        section_tempo = int(tempo * section.tempo_factor)
        scale = SCALES[section.scale_name]

        # Transpose scale to key_root
        scale = Scale(root=(section.key_root + key_root) % 12, mode=scale.mode)

        # Build chord progression
        chords = _build_section_chords(section, scale, beat_offset, beats_per_bar)
        all_chords.extend(chords)

        # Generate tracks for this section
        params = GeneratorParams(density=0.5)

        track_configs = {
            "melody": make_melody_track(section.mood, params),
            "bass": make_bass_track(section.mood),
            "chords": make_chord_track(section.mood),
            "arpeggio": make_arp_track(section.mood),
            "ostinato": make_ostinato_track(section.mood),
        }

        if section.mood == "battle":
            track_configs["percussion"] = make_percussion_track(section.mood)

        if section.mood in ("mystery", "despair"):
            track_configs["piano_sweep"] = make_piano_run_track(section.mood)

        # Create Idea Tool for this section
        config = IdeaToolConfig(
            scale=scale,
            style="cinematic",
            bars=section.bars,
            tempo=section_tempo,
            tracks=list(track_configs.values()),
            use_tension_curve=True,
            use_non_chord_tones=(section.mood != "battle"),
            progression_type="from_list",
            progression_list=[section.progression],
        )

        tool = IdeaTool(config)
        section_result = tool.generate()

        # Merge into all_tracks
        for track_name, notes in section_result.items():
            if track_name.startswith("_"):
                continue
            if track_name not in all_tracks:
                all_tracks[track_name] = []
            all_tracks[track_name].extend(notes)

        beat_offset += section_beats

    # Post-processing
    all_tracks = _master_mix(all_tracks, tempo)

    return all_tracks, all_chords, sections


def _build_section_chords(
    section: Section,
    scale: Scale,
    beat_offset: float,
    beats_per_bar: int,
) -> list[ChordLabel]:
    """Build chord labels for a section."""
    degs = scale.degrees()
    chords = []
    bars = section.bars
    prog = section.progression

    for i in range(bars):
        deg = prog[i % len(prog)]
        root_pc = degs[(deg - 1) % len(degs)]

        # Quality
        if deg in (1, 4, 5):
            quality = Quality.MAJOR
        elif deg in (2, 3, 6):
            quality = Quality.MINOR
        else:
            quality = Quality.DIMINISHED

        chords.append(
            ChordLabel(
                root=root_pc,
                quality=quality,
                start=round(beat_offset + i * beats_per_bar, 6),
                duration=round(beats_per_bar, 6),
                degree=deg,
            )
        )

    return chords


def _master_mix(
    tracks: dict[str, list[NoteInfo]],
    tempo: int,
) -> dict[str, list[NoteInfo]]:
    """Apply basic mastering: velocity balancing, EQ-like filtering."""
    MIX_LEVELS = {
        "melody": 1.0,  # loudest
        "bass": 0.85,
        "chords": 0.7,
        "arpeggio": 0.6,
        "ostinato": 0.65,
        "percussion": 0.75,
        "piano_sweep": 0.55,
    }

    result = {}
    for track_name, notes in tracks.items():
        level = MIX_LEVELS.get(track_name, 0.7)
        mixed = []
        for n in notes:
            # Velocity scaling
            vel = int(n.velocity * level)
            # Subtle humanize
            vel += random.randint(-5, 5)
            vel = max(20, min(127, vel))
            # Subtle timing humanize
            start = n.start + random.uniform(-0.02, 0.02)
            mixed.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=round(start, 6),
                    duration=n.duration,
                    velocity=vel,
                )
            )
        result[track_name] = sorted(mixed, key=lambda n: n.start)

    return result


# ---------------------------------------------------------------------------
# MIDI Export
# ---------------------------------------------------------------------------


def export_midi(
    tracks: dict[str, list[NoteInfo]],
    output_path: str,
    tempo: int = 72,
):
    """Export all tracks to a multi-channel MIDI file."""
    export_multitrack_midi(tracks, output_path, bpm=tempo)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Dark Fantasy Orchestral Generator")
    parser.add_argument("--duration", type=float, default=3.0, help="Duration in minutes (2-30)")
    parser.add_argument("--tempo", type=int, default=72, help="Base tempo BPM")
    parser.add_argument("--key", type=int, default=0, help="Key root (0=C, 2=D, 5=F, 7=G)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--output", type=str, default="dark_fantasy.mid", help="Output MIDI file")
    args = parser.parse_args()

    duration = max(2.0, min(30.0, args.duration))

    print(f"Dark Fantasy Generator")
    print(f"  Duration: {duration:.1f} minutes")
    print(f"  Tempo: {args.tempo} BPM")
    print(
        f"  Key: {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][args.key]} minor"
    )
    print(f"  Seed: {args.seed}")
    print()

    # Generate
    print("Generating composition...")
    tracks, chords, sections = generate_dark_fantasy(
        duration_minutes=duration,
        tempo=args.tempo,
        key_root=args.key,
        seed=args.seed,
    )

    # Stats
    total_notes = sum(len(notes) for notes in tracks.values())
    total_beats = duration * 60 * (args.tempo / 60)

    print(f"\nComposition generated:")
    print(f"  Sections: {len(sections)}")
    for s in sections:
        print(f"    {s.name}: {s.bars} bars, {s.mood}, {s.scale_name}")
    print(f"  Tracks: {len(tracks)}")
    for name, notes in sorted(tracks.items()):
        print(f"    {name}: {len(notes)} notes")
    print(f"  Total: {total_notes} notes, {total_beats:.0f} beats")

    # Export
    print(f"\nExporting to {args.output}...")
    export_midi(tracks, args.output, tempo=args.tempo)
    print(f"Done! {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
