#!/usr/bin/env python3
"""
scripts/inspect_melody.py — Inspect LeadSynthGenerator output in detail.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.composer import ArticulationEngine


PROGRESSION = [
    (0, Quality.MAJOR),  # C
    (7, Quality.MAJOR),  # G
    (9, Quality.MINOR),  # Am
    (5, Quality.MAJOR),  # F
]


def harmonize(bars: int, bpb: int = 4):
    chords: list[ChordLabel] = []
    for i in range(bars):
        root, qual = PROGRESSION[i % 4]
        chords.append(ChordLabel(root=root, quality=qual, start=i * bpb, duration=bpb))
    return chords


def note_name(pitch: int) -> str:
    notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    octave = (pitch // 12) - 1
    name = notes[pitch % 12]
    return f"{name}{octave}"


def print_melody(notes: list[NoteInfo], title: str):
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print(f"{'=' * 60}")
    print(f"{'Time':>8} | {'Note':>5} | {'Vel':>3} | {'Dur':>6}")
    print(f"{'-':-^8} | {'-':-^5} | {'-':-^3} | {'-':-^6}")
    for n in notes[:32]:  # first 32 notes
        time = f"{n.start:.2f}"
        note = note_name(n.pitch)
        vel = n.velocity
        dur = f"{n.duration:.3f}"
        print(f"{time:>8} | {note:>5} | {vel:>3} | {dur:>6}")
    if len(notes) > 32:
        print(f"... and {len(notes) - 32} more notes")


def main():
    bpm = 140
    bpb = 4
    bars = 8
    chords = harmonize(bars, bpb)
    scale = Scale(root=0, mode=Mode.MAJOR)

    styles = ["retro", "techno", "trance", "supersaw"]
    note_lengths = ["staccato", "legato", "mixed"]

    print(f"\n🎼 LeadSynthGenerator Demo — {bars} bars, {bpm} BPM, C major")
    print(f"Chord progression: I–V–vi–IV (C–G–Am–F)")

    for style in styles:
        for nl in note_lengths:
            try:
                gen = LeadSynthGenerator(
                    params=GeneratorParams(density=0.6),
                    style=style,
                    note_length=nl,
                    portamento=0.1,
                    vibrato_rate=0.5,
                    vibrato_depth=0.3,
                )
                notes = gen.render(chords, scale, bars * bpb, context=None)
                art = ArticulationEngine()
                notes = art.apply(notes, "lead", bars * bpb)

                print_melody(notes, f"Style: {style.upper()} | Note length: {nl}")
                print(f"Total notes: {len(notes)}")
                print(
                    f"Velocity range: {min(n.velocity for n in notes)}–{max(n.velocity for n in notes)}"
                )
                print(
                    f"Pitch range: {note_name(min(n.pitch for n in notes))}–{note_name(max(n.pitch for n in notes))}"
                )

            except Exception as e:
                print(f"❌ {style}/{nl}: {e}")

    print("\n\n📊 Summary:")
    print("  retro    — 80s style, slower attack, melodic phrasing")
    print("  techno   — high-energy, staccato, rhythmic patterns")
    print("  trance   — flowing, legato, sustained notes with portamento")
    print("  supersaw — bright, detuned sawtooth, richer harmonics")
    print("\nNote length:")
    print("  staccato — short, separated notes")
    print("  legato   — smooth, connected notes")
    print("  mixed    — combination of both")


if __name__ == "__main__":
    sys.exit(main())
