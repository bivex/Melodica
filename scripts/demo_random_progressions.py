#!/usr/bin/env python3
"""
scripts/demo_random_progressions.py — Generate MIDI arrangements with random chord progressions
using LeadSynthGenerator (melody) + CountermelodyGenerator + Bass + Pad.

All progressions are diatonic to the chosen scale (default C major).
Each arrangement produces a multi-track MIDI file.

Usage:
    python3.11 scripts/demo_random_progressions.py \
        --key 0 --mode major \
        --progression jazz_ii_V_I circle_fifths doowop_50s \
        --repeat 4 --bpm 120 \
        --output-dir output/random_progressions
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Dict, List, Tuple

from melodica.generators import (
    BassGenerator,
    CountermelodyGenerator,
    GeneratorParams,
    AmbientPadGenerator,
    LeadSynthGenerator,
)
from melodica.types import ChordLabel, Quality, Scale
from melodica.theory import Mode, get_mode_intervals
from melodica.midi import export_multitrack_midi


# ── Helper: map degree (1–7) to root pitch class within given mode/key ────────
def degree_root(degree: int, key_root: int, mode: Mode) -> int:
    """Return pitch class (0–11) for scale degree in given mode."""
    intervals = get_mode_intervals(mode)  # e.g. [0,2,4,5,7,9,11] for major
    if degree < 1 or degree > len(intervals):
        raise ValueError(f"degree must be 1–{len(intervals)}; got {degree}")
    return (key_root + int(round(intervals[degree - 1]))) % 12


# ── Quality map ────────────────────────────────────────────────────────────────
QUALITY_MAP = {
    "maj": Quality.MAJOR,
    "m": Quality.MINOR,
    "dim": Quality.DIMINISHED,
    "aug": Quality.AUGMENTED,
    "maj7": Quality.MAJOR7,
    "m7": Quality.MINOR7,
    "dom7": Quality.DOMINANT7,
}

# ── Progression definitions (degree + quality key, diatonic to their mode) ─────
PROGRESSIONS: Dict[str, dict] = {
    # Major-key progressions
    "jazz_ii_V_I": {
        "key_root": 0,
        "mode": Mode.MAJOR,
        "chords": [
            (2, "m7"),
            (5, "dom7"),
            (1, "maj7"),
            (6, "m7"),
        ],
    },
    "circle_fifths": {
        "key_root": 0,
        "mode": Mode.MAJOR,
        "chords": [
            (6, "m7"),
            (2, "m7"),
            (5, "dom7"),
            (1, "maj7"),
        ],
    },
    "doowop_50s": {
        "key_root": 0,
        "mode": Mode.MAJOR,
        "chords": [
            (1, "maj7"),
            (6, "m7"),
            (4, "maj7"),
            (5, "dom7"),
        ],
    },
    "I_vi_ii_V": {
        "key_root": 0,
        "mode": Mode.MAJOR,
        "chords": [
            (1, "maj"),
            (6, "m"),
            (2, "m"),
            (5, "maj"),
        ],
    },
    "iii_vi_ii_V": {
        "key_root": 0,
        "mode": Mode.MAJOR,
        "chords": [
            (3, "m"),
            (6, "m"),
            (2, "m"),
            (5, "maj"),
        ],
    },
    "I_IV_vii°_iii": {
        "key_root": 0,
        "mode": Mode.MAJOR,
        "chords": [
            (1, "maj"),
            (4, "maj"),
            (7, "dim"),
            (3, "m"),
        ],
    },
    # Natural minor progression (A minor)
    "andalucian_nat": {
        "key_root": 9,  # A
        "mode": Mode.NATURAL_MINOR,
        "chords": [
            (1, "m"),  # Am i
            (7, "maj"),  # G (VII)
            (6, "maj"),  # F (VI)
            (5, "m"),  # Em (v)
        ],
    },
}

# ── Track instrument mapping (General MIDI) ───────────────────────────────────
TRACK_INSTRUMENTS = {
    "Pad": 90,  # Warm Pad
    "Bass": 33,  # Electric Bass (finger)
    "Lead": 81,  # Synth Lead 1 (sawtooth)
    "Countermelody": 89,  # Pad 1 (new age)
}


# ── Generator parameter presets ────────────────────────────────────────────────
def random_lead_params():
    return GeneratorParams(
        density=random.uniform(0.5, 0.8),
        key_range_low=random.randint(48, 60),  # C3–C5
        key_range_high=random.randint(72, 84),  # C5–C7
    )


def random_lead_style():
    return random.choice(["retro", "techno", "trance", "supersaw"])


def random_lead_note_length():
    return random.choice(["legato", "staccato", "mixed"])


def countermelody_params():
    return GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)


def bass_params():
    return GeneratorParams(density=0.4, key_range_low=28, key_range_high=60)


def pad_params():
    return GeneratorParams(density=0.3, key_range_low=36, key_range_high=72)


# ── Build chords for given progression ────────────────────────────────────────
def build_chords(
    prog_def: dict,
    bar_length: int = 4,
    chord_duration: float = 4.0,
) -> Tuple[List[ChordLabel], Scale]:
    """
    Expand chord definition into ChordLabel list and Scale object.
    Each chord occupies `chord_duration` beats (default 1 bar = 4 beats).
    """
    key_root = prog_def["key_root"]
    mode = prog_def["mode"]
    scale = Scale(root=key_root, mode=mode)
    chords_raw = prog_def["chords"]
    total = len(chords_raw)
    chords: List[ChordLabel] = []
    for i, (degree, qual_key) in enumerate(chords_raw):
        root_pc = degree_root(degree, key_root, mode)
        quality = QUALITY_MAP[qual_key]
        start = i * chord_duration
        chords.append(
            ChordLabel(
                root=root_pc,
                quality=quality,
                start=start,
                duration=chord_duration,
            )
        )
    return chords, scale


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Generate random-progression MIDI arrangements using Melodica SDK"
    )
    parser.add_argument(
        "--key",
        type=int,
        default=0,
        help="Tonic pitch class 0–11 (0=C, 2=D, 9=A, …). Default 0 (C).",
    )
    parser.add_argument(
        "--mode",
        default="major",
        choices=[m.value for m in Mode],
        help="Scale mode (default major).",
    )
    parser.add_argument(
        "--progression",
        nargs="+",
        default=list(PROGRESSIONS.keys()),
        help="Which progression(s) to generate. Default: all defined.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=4,
        help="Times to repeat chord sequence (default 4 × 4 bars = 16 bars).",
    )
    parser.add_argument("--bpm", type=int, default=120, help="Tempo in BPM (default 120).")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/random_progressions",
        help="Directory to write MIDI files.",
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility.")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    mode_enum = Mode(args.mode)

    for prog_name in args.progression:
        if prog_name not in PROGRESSIONS:
            print(f"⚠️  Unknown progression '{prog_name}', skipping.")
            continue
        print(f"\n🎼 Generating: {prog_name}")

        # ── Build chord loop (repeat pattern) ────────────────────────────────────
        base_def = PROGRESSIONS[prog_name]
        base_chords, scale = build_chords(base_def)
        # Expand by repeating the pattern
        expanded_chords: List[ChordLabel] = []
        for rep in range(args.repeat):
            for ch in base_chords:
                # Recalculate start time per repetition
                new_start = rep * (len(base_chords) * ch.duration) + ch.start
                expanded_chords.append(
                    ChordLabel(
                        root=ch.root,
                        quality=ch.quality,
                        start=new_start,
                        duration=ch.duration,
                    )
                )
        total_beats = expanded_chords[-1].end if expanded_chords else 0.0

        # ── Lead ────────────────────────────────────────────────────────────────
        lead_gen = LeadSynthGenerator(
            params=random_lead_params(),
            style=random_lead_style(),
            note_length=random_lead_note_length(),
            portamento=random.uniform(0.1, 0.3),
            vibrato_rate=random.uniform(0.2, 0.6),
            vibrato_depth=random.uniform(0.2, 0.4),
        )
        lead_notes = lead_gen.render(expanded_chords, scale, total_beats, None)

        # ── Countermelody ───────────────────────────────────────────────────────
        counter_gen = CountermelodyGenerator(
            params=countermelody_params(),
            primary_melody=lead_notes,
            motion_preference=random.choice(["contrary", "oblique", "mixed"]),
            interval_limit=7,
        )
        counter_notes = counter_gen.render(expanded_chords, scale, total_beats, None)

        # ── Bass ────────────────────────────────────────────────────────────────
        bass_gen = BassGenerator(
            params=bass_params(),
            style="root_only",
        )
        bass_notes = bass_gen.render(expanded_chords, scale, total_beats, None)

        # ── Pad ─────────────────────────────────────────────────────────────────
        pad_gen = AmbientPadGenerator(
            params=pad_params(),
            voicing="spread",
            overlap=0.05,
            rhythm=None,
        )
        pad_notes = pad_gen.render(expanded_chords, scale, total_beats, None)

        # ── Collect tracks ───────────────────────────────────────────────────────
        tracks = {
            "Pad": pad_notes,
            "Bass": bass_notes,
            "Countermelody": counter_notes,
            "Lead": lead_notes,
        }

        # ── Export ───────────────────────────────────────────────────────────────
        out_name = f"{prog_name}_seed{args.seed if args.seed else 'rand'}.mid"
        out_path = output_dir / out_name
        export_multitrack_midi(
            tracks_data=tracks,
            path=out_path,
            bpm=args.bpm,
            key=scale,
            time_sig=(4, 4),
            instruments=TRACK_INSTRUMENTS,
        )
        print(
            f"✅  {out_path}  "
            f"| Lead: {random_lead_style()} {random_lead_note_length()}, "
            f"BPM={args.bpm}, bars={int(total_beats // 4)}, "
            f"notes: L={len(lead_notes)}, C={len(counter_notes)}, "
            f"B={len(bass_notes)}, P={len(pad_notes)}"
        )


if __name__ == "__main__":
    main()
