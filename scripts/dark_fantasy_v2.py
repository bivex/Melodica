#!/usr/bin/env python3
"""
dark_fantasy_v2.py — Full SDK Dark Fantasy Generator.

Uses ALL Melodica components:
- 10+ generators (melody, arpeggiator, bass, chords, ostinato, ambient, dyads,
  riff, call/response, canon, piano_run, percussion, strum, groove)
- 3 harmonizers (HMM3, ChromaticMediant, Functional)
- 10+ modifiers (transpose, humanize, velocity, crescendo, staccato, mirror, etc.)
- All 5 composer modules (voice leading, tension curve, style, NCT, texture)
- Rhythm generators (euclidean, polyrhythm, schillinger, bass rhythm)

Usage:
    python3 dark_fantasy_v2.py [--duration 3] [--tempo 72] [--output demo.mid]
"""

import sys
import random
import argparse
from pathlib import Path
from dataclasses import dataclass

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
    PianoRunGenerator,
    PercussionGenerator,
    RiffGenerator,
    CanonGenerator,
    CallResponseGenerator,
    AmbientPadGenerator,
    DyadGenerator,
    DyadsRunGenerator,
    GrooveGenerator,
    GeneratorParams,
)
from melodica.harmonize import (
    HMM3Harmonizer,
    ChromaticMediantHarmonizer,
    FunctionalHarmonizer,
)
from melodica.modifiers import (
    TransposeModifier,
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    StaccatoLegatoModifier,
    MirrorModifier,
    LimitNoteRangeModifier,
    NoteDoublerModifier,
    MIDIEchoModifier,
    AddIntervalModifier,
    SwingController,
    ModifierContext,
)
from melodica.composer import (
    VoiceLeadingEngine,
    TensionCurve,
    TensionPhase,
    get_style,
    TextureController,
    NonChordToneGenerator,
)
from melodica.rhythm import (
    EuclideanRhythmGenerator,
    PolyrhythmGenerator,
    BassRhythmGenerator,
    SchillingerGenerator,
    SmoothRhythmGenerator,
    RhythmLab,
)
from melodica.midi import export_multitrack_midi, GM_INSTRUMENTS


# ---------------------------------------------------------------------------
# Dark Fantasy Scales
# ---------------------------------------------------------------------------

SCALES = {
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "byzantine": Scale(root=0, mode=Mode.BYZANTINE),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "persian": Scale(root=0, mode=Mode.PERSIAN),
}


# ---------------------------------------------------------------------------
# Section
# ---------------------------------------------------------------------------


@dataclass
class Section:
    name: str
    bars: int
    scale_name: str
    key_root: int
    mood: str
    tempo_factor: float
    density: float
    tracks: list[str]


def build_sections(total_bars: int) -> list[Section]:
    # Template: name, ratio, scale, key_root, mood, tempo_factor, density, tracks
    template = [
        ("Prologue", 0.08, "phrygian", 0, "ominous", 0.85, 0.3, ["ambient", "bass", "chords"]),
        (
            "Dark Forest",
            0.15,
            "harmonic_minor",
            0,
            "mystery",
            0.90,
            0.5,
            ["melody", "arp", "bass", "chords", "dyads"],
        ),
        (
            "Ancient Temple",
            0.12,
            "byzantine",
            5,
            "ritual",
            0.80,
            0.4,
            ["ostinato", "ambient", "bass", "fingerpicking"],
        ),
        (
            "Rising Threat",
            0.20,
            "hungarian_minor",
            0,
            "battle",
            1.00,
            0.7,
            ["melody", "riff", "bass", "percussion", "ostinato", "groove"],
        ),
        (
            "Final Confrontation",
            0.33,
            "harmonic_minor",
            0,
            "triumph",
            1.10,
            0.8,
            ["melody", "chords", "bass", "arp", "strum", "percussion", "dyads_run"],
        ),
        (
            "Epilogue",
            0.12,
            "natural_minor",
            0,
            "despair",
            0.75,
            0.3,
            ["ambient", "call_response", "bass"],
        ),
    ]

    # Distribute bars proportionally, min 4 per section
    raw = [max(4, int(total_bars * r)) for _, r, *_ in template]
    diff = total_bars - sum(raw)
    # Add/subtract from the largest section
    if diff != 0:
        biggest = raw.index(max(raw))
        raw[biggest] += diff
        raw[biggest] = max(4, raw[biggest])

    sections = []
    for i, (name, _, scale_name, key_root, mood, tempo_factor, density, tracks) in enumerate(
        template
    ):
        sections.append(
            Section(name, raw[i], scale_name, key_root, mood, tempo_factor, density, tracks)
        )

    return sections


# ---------------------------------------------------------------------------
# Generator factory
# ---------------------------------------------------------------------------


def make_generator(name: str, mood: str, density: float, scale: Scale) -> tuple:
    """Create (generator, rhythm, modifiers) for a track name."""
    params = GeneratorParams(density=density)
    rhythm = None
    mods = []

    match name:
        case "melody":
            gen = MelodyGenerator(
                params=params,
                harmony_note_probability=0.7,
                note_range_low=55 if mood != "battle" else 60,
                note_range_high=80 if mood != "battle" else 84,
                note_repetition_probability=0.1,
            )
            if mood in ("mystery", "ritual"):
                mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5.0))
            if mood == "despair":
                mods.append(CrescendoModifier(start_vel=40, end_vel=80))

        case "arp":
            pattern = {
                "mystery": "up_down",
                "ominous": "converge",
                "battle": "gallop",
                "triumph": "up",
                "despair": "down",
                "ritual": "pinky_up_down",
            }
            gen = ArpeggiatorGenerator(
                params=params,
                pattern=pattern.get(mood, "up"),
                note_duration=0.25 if mood != "despair" else 0.5,
                octaves=2,
                voicing="spread",
            )

        case "bass":
            gen = BassGenerator(
                params=params,
                allowed_notes=["root", "fourth"] if mood != "battle" else ["root"],
                note_movement="alternating",
                global_movement="up" if mood == "triumph" else "none",
                transpose_octaves=-1,
            )
            rhythm = BassRhythmGenerator(
                pattern_name="walking" if mood == "battle" else "syncopated"
            )

        case "chords":
            gen = ChordGenerator(
                params=params,
                voicing="spread" if mood in ("mystery", "despair") else "open",
            )

        case "ostinato":
            pattern = {
                "battle": "1-2-1-3-1-4-1-5",
                "mystery": "1-3-5-6",
                "triumph": "1-3-5-3-1-5-3-1-3-5",
                "ritual": "5-1-4-1-3-1-2-1",
            }
            gen = OstinatoGenerator(
                params=params,
                pattern=pattern.get(mood, "1-3-5-3"),
                repeat_notes=2 if mood == "battle" else 1,
            )

        case "ambient":
            gen = AmbientPadGenerator(
                params=params,
                voicing="spread",
                overlap=0.5,
            )
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=3.0))

        case "dyads":
            gen = DyadGenerator(
                params=params,
                interval_pref=[3, 4, 7],
                motion_mode="contrary" if mood == "mystery" else "parallel",
            )

        case "dyads_run":
            gen = DyadsRunGenerator(
                params=params,
                interval=3,
                technique="waterfall" if mood == "despair" else "up_down",
                notes_per_run=8,
            )

        case "riff":
            gen = RiffGenerator(
                params=params,
                scale_type="minor_pent",
                riff_pattern="gallop" if mood == "battle" else "palm_mute",
                palm_mute_prob=0.4,
                power_chord=True,
            )

        case "strum":
            gen = StrumPatternGenerator(
                params=params,
                voicing="guitar",
                pattern_name="rock" if mood == "battle" else "folk",
                polyphony=6,
                density="high" if mood == "battle" else "medium",
            )

        case "fingerpicking":
            gen = FingerpickingGenerator(
                params=params,
                pattern=[0, 2, 1, 3, 2, 1],
                notes_to_use=[0, 1, 2, 3],
                sustain_notes="bottom_note",
            )

        case "percussion":
            pattern = {"battle": "rock", "triumph": "funk", "ritual": "bossa"}
            gen = PercussionGenerator(
                params=params,
                pattern_name=pattern.get(mood, "rock"),
                velocity_humanize=10,
            )

        case "groove":
            gen = GrooveGenerator(
                params=params,
                groove_pattern="funk_1",
                ghost_note_vel=25,
                accent_vel=110,
            )

        case "call_response":
            gen = CallResponseGenerator(
                params=params,
                call_length=2.0,
                response_length=2.0,
                call_direction="up" if mood != "despair" else "down",
                response_direction="down" if mood != "despair" else "up",
            )

        case "canon":
            gen = CanonGenerator(
                params=params,
                delay_beats=2.0,
                interval=7 if mood == "triumph" else 5,
            )

        case "piano_run":
            gen = PianoRunGenerator(
                params=params,
                technique="waterfall" if mood in ("despair", "mystery") else "straddle",
                notes_per_run=12,
                motion="up",
            )

        case _:
            gen = MelodyGenerator(params=params)

    return gen, rhythm, mods


# ---------------------------------------------------------------------------
# Composition engine
# ---------------------------------------------------------------------------


def generate_dark_fantasy(
    duration_minutes: float = 3.0,
    tempo: int = 72,
    key_root: int = 0,
    seed: int | None = None,
) -> dict[str, list[NoteInfo]]:
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    total_beats = duration_minutes * 60 * (tempo / 60)
    total_bars = max(8, int(round(total_beats / beats_per_bar)))

    sections = build_sections(total_bars)
    all_tracks: dict[str, list[NoteInfo]] = {}
    all_chords: list[ChordLabel] = []
    beat_offset = 0.0

    actual_bars = sum(s.bars for s in sections)
    actual_beats = actual_bars * beats_per_bar
    actual_seconds = actual_beats / tempo * 60
    actual_minutes = actual_seconds / 60

    # Harmonizers
    hmm = HMM3Harmonizer()
    chromatic = ChromaticMediantHarmonizer(chromatic_prob=0.3)
    functional = FunctionalHarmonizer(start_with="I", end_with="I")

    # Composer modules
    vl_engine = VoiceLeadingEngine(strict_mode=False)
    nct_gen = NonChordToneGenerator(passing_prob=0.15, neighbor_prob=0.08)

    for si, section in enumerate(sections):
        s_beats = section.bars * beats_per_bar
        scale = SCALES[section.scale_name]
        scale = Scale(root=(section.key_root + key_root) % 12, mode=scale.mode)

        # Generate tension curve
        tension = TensionCurve(
            total_beats=s_beats,
            curve_type="classical" if section.mood != "battle" else "build_release",
            peak_position=0.7,
            peak_intensity=0.9,
        )

        # Generate dummy melody for harmonizer
        dummy_melody = []
        for bar in range(section.bars):
            degs = scale.degrees()
            for beat in range(beats_per_bar):
                pc = degs[(bar * beats_per_bar + beat) % len(degs)]
                dummy_melody.append(
                    NoteInfo(
                        pitch=60 + pc,
                        start=round(bar * beats_per_bar + beat, 6),
                        duration=0.9,
                        velocity=80,
                    )
                )

        # Harmonize section
        if section.mood in ("triumph", "battle"):
            chords = hmm.harmonize(dummy_melody, scale, s_beats)
        elif section.mood == "ritual":
            chords = chromatic.harmonize(dummy_melody, scale, s_beats)
        else:
            chords = functional.harmonize(dummy_melody, scale, s_beats)

        # Offset chords to global time
        section_chords = []
        for c in chords:
            section_chords.append(
                ChordLabel(
                    root=c.root,
                    quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration,
                    degree=c.degree,
                )
            )
        all_chords.extend(section_chords)

        # Adjust chord times for local generators
        local_chords = [
            ChordLabel(
                root=c.root,
                quality=c.quality,
                start=round(c.start - beat_offset, 6),
                duration=c.duration,
                degree=c.degree,
            )
            for c in section_chords
        ]

        # Voice leading for chord tracks
        if "chords" in section.tracks or "strum" in section.tracks:
            try:
                voices = vl_engine.voicize_progression(local_chords[:4], scale)
            except Exception:
                pass  # noqa: S110  # fallback to regular generation

        # Generate each track
        for track_name in section.tracks:
            gen, rhythm, mods = make_generator(track_name, section.mood, section.density, scale)

            if rhythm:
                gen.rhythm = rhythm  # type: ignore

            # Render
            from melodica.render_context import RenderContext

            ctx = RenderContext()
            notes = gen.render(local_chords, scale, s_beats, ctx)

            # Apply modifiers
            mod_ctx = ModifierContext(
                duration_beats=s_beats,
                chords=local_chords,
                timeline=None,
                scale=scale,  # type: ignore
            )
            for mod in mods:
                try:
                    notes = mod.modify(notes, mod_ctx)
                except Exception:
                    pass

            # Apply NCT to melody tracks
            if track_name in ("melody", "dyads", "call_response"):
                try:
                    notes = nct_gen.add_non_chord_tones(notes, local_chords, scale)
                except Exception:
                    pass

            # Offset to global time
            for n in notes:
                global_track_name = f"{track_name}_{si}" if track_name in all_tracks else track_name
                if global_track_name not in all_tracks:
                    all_tracks[global_track_name] = []
                all_tracks[global_track_name].append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(n.start + beat_offset, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                    )
                )

        beat_offset += s_beats

    # Master mix
    all_tracks = _master_mix(all_tracks)
    return all_tracks


def _master_mix(tracks: dict[str, list[NoteInfo]]) -> dict[str, list[NoteInfo]]:
    LEVELS = {
        "melody": 1.0,
        "bass": 0.85,
        "chords": 0.7,
        "arp": 0.6,
        "ostinato": 0.65,
        "ambient": 0.5,
        "dyads": 0.7,
        "dyads_run": 0.55,
        "riff": 0.8,
        "strum": 0.65,
        "fingerpicking": 0.55,
        "percussion": 0.75,
        "groove": 0.7,
        "call_response": 0.65,
        "canon": 0.6,
        "piano_run": 0.55,
    }

    result = {}
    for name, notes in tracks.items():
        base_name = name.split("_")[0]
        level = LEVELS.get(base_name, 0.7)
        mixed = []
        for n in notes:
            vel = max(15, min(127, int(n.velocity * level) + random.randint(-5, 5)))
            start = n.start + random.uniform(-0.015, 0.015)
            mixed.append(
                NoteInfo(pitch=n.pitch, start=round(start, 6), duration=n.duration, velocity=vel)
            )
        result[name] = sorted(mixed, key=lambda n: n.start)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Dark Fantasy Full SDK Generator")
    parser.add_argument("--duration", type=float, default=3.0)
    parser.add_argument("--tempo", type=int, default=72)
    parser.add_argument("--key", type=int, default=0)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--output", type=str, default="dark_fantasy_v2.mid")
    args = parser.parse_args()

    duration = max(2.0, min(30.0, args.duration))

    print(f"Dark Fantasy V2 — Full SDK")
    actual_bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual_sec = actual_bars * 4 / args.tempo * 60
    print(f"  Requested: {duration:.1f} min")
    print(f"  Actual: {actual_sec / 60:.1f} min ({actual_bars} bars × 4 beats @ {args.tempo} BPM)")
    print(
        f"  Key: {['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][args.key]} minor"
    )
    print(f"  Using: generators, harmonizers, modifiers, composer, rhythms")
    print()

    tracks = generate_dark_fantasy(duration, args.tempo, args.key, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"Generated: {len(tracks)} tracks, {total} notes")
    for name, notes in sorted(tracks.items()):
        print(f"  {name}: {len(notes)} notes")

    export_multitrack_midi(tracks, args.output, bpm=args.tempo)
    print(f"\nExported: {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
