#!/usr/bin/env python3
"""
scripts/demo_melody_generator.py — Demonstrate LeadSynthGenerator from Melodica SDK.

Generates a standalone melody MIDI using various styles and parameters.
"""

import sys, random, argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, MusicTimeline
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.utils import chord_at


# ── Chord progression ────────────────────────────────────────────────────────
PROGRESSION = [
    (0, Quality.MAJOR),  # C
    (7, Quality.MAJOR),  # G
    (9, Quality.MINOR),  # Am
    (5, Quality.MAJOR),  # F
]


def harmonize(bars: int, bpb: int = 4) -> list[ChordLabel]:
    chords: list[ChordLabel] = []
    for i in range(bars):
        root, qual = PROGRESSION[i % 4]
        chords.append(ChordLabel(root=root, quality=qual, start=i * bpb, duration=bpb))
    return chords


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Demo: LeadSynthGenerator melody only")
    parser.add_argument(
        "--style",
        default="techno",
        choices=["retro", "techno", "trance", "supersaw"],
        help="Lead synth style (retro=80s, techno=staccato, trance= flowing, supersaw=bright)",
    )
    parser.add_argument(
        "--note-length",
        default="staccato",
        choices=["legato", "staccato", "mixed"],
        help="Note articulation: legato=smooth, staccato=short, mixed=variable",
    )
    parser.add_argument("--bars", type=int, default=16, help="Number of bars")
    parser.add_argument("--bpm", type=int, default=140, help="Tempo")
    parser.add_argument("--output", type=str, default="melody_demo.mid", help="Output MIDI file")
    args = parser.parse_args()

    bpm = args.bpm
    bpb = 4
    total_bars = args.bars
    chords = harmonize(total_bars, bpb)

    # Create lead generator
    params = GeneratorParams(density=0.6)
    lead_gen = LeadSynthGenerator(
        params=params,
        style=args.style,
        note_length=args.note_length,
        portamento=0.15,
        vibrato_rate=0.5,
        vibrato_depth=0.3,
    )

    # Render lead phrase
    scale = Scale(root=0, mode=Mode.MAJOR)  # C major
    lead_notes = lead_gen.render(chords, scale, total_bars * bpb, context=None)

    # Apply articulation (slides, expression)
    art = ArticulationEngine()
    lead_notes_artic = art.apply(lead_notes, "lead", total_bars * bpb)

    # Prepare single-track output
    tracks = {"lead": lead_notes_artic}

    # Export
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    instruments = {"lead": 81}  # Sawtooth Lead
    export_multitrack_midi(
        tracks,
        output_path,
        bpm=bpm,
        key="C",
        instruments=instruments,
    )

    print(f"✅ Melody generated: {output_path}")
    print(f"   Style: {args.style} | Note length: {args.note_length}")
    print(f"   Bars: {total_bars} | BPM: {bpm}")
    print(f"   Notes: {len(lead_notes_artic)}")
    print(f"\n🎵 Chord progression: I–V–vi–IV (C–G–Am–F) cycling")
    print(f"   Lead: Sawtooth (GM 81), C major scale")


if __name__ == "__main__":
    sys.exit(main())
