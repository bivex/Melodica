
# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
midi_doctor.py — MIDI diagnostic tool.

Analyzes a MIDI file or generates from a script and reports:
- Psychoacoustic issues (masking, fusion, blur)
- Harmonic clashes (cross-track dissonance)
- Track statistics (note count, register, velocity range)
- Timeline overview (which tracks play when)

Usage:
    python3 midi_doctor.py output/df_downtempo.mid
    python3 midi_doctor.py --script scripts/df_downtempo.py --duration 1 --tempo 68 --key 2 --seed 42
"""

import sys
import argparse
from pathlib import Path
from collections import Counter

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

import mido
from melodica.types import NoteInfo
from melodica.composer.psychoacoustic import (
    detect_frequency_masking,
    detect_temporal_masking,
    detect_fusion,
    detect_blur,
    detect_register_masking,
    detect_brightness_overload,
)
from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig


# ---------------------------------------------------------------------------
# MIDI → tracks dict
# ---------------------------------------------------------------------------
def midi_to_tracks(path: str) -> dict[str, list[NoteInfo]]:
    """Parse MIDI file into {track_name: [NoteInfo]}."""
    mid = mido.MidiFile(path)
    tracks = {}

    for track in mid.tracks:
        name = None
        channel = None
        notes_on = {}  # (pitch, channel) → (tick, velocity)
        note_list = []

        tick = 0
        for msg in track:
            tick += msg.time
            if msg.type == "track_name":
                name = msg.name
            elif msg.type == "program_change":
                channel = msg.channel
            elif msg.type == "note_on" and msg.velocity > 0:
                key = (msg.note, msg.channel)
                notes_on[key] = (tick, msg.velocity)
            elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
                key = (msg.note, msg.channel)
                if key in notes_on:
                    on_tick, vel = notes_on.pop(key)
                    duration = (tick - on_tick) / mid.ticks_per_beat
                    start = on_tick / mid.ticks_per_beat
                    note_list.append(
                        NoteInfo(
                            pitch=msg.note,
                            start=round(start, 6),
                            duration=round(duration, 6),
                            velocity=vel,
                        )
                    )

        if name and note_list:
            tracks[name] = sorted(note_list, key=lambda n: n.start)

    return tracks, mid


# ---------------------------------------------------------------------------
# Report generators
# ---------------------------------------------------------------------------
def report_header(path: str, mid, tracks: dict):
    total = sum(len(n) for n in tracks.values())
    dur = mid.length
    print(f"{'=' * 70}")
    print(f"  MIDI DOCTOR: {path}")
    print(
        f"  Duration: {dur:.1f}s = {dur / 60:.1f}min  |  Tracks: {len(tracks)}  |  Notes: {total}"
    )
    print(f"  Ticks/beat: {mid.ticks_per_beat}")
    print(f"{'=' * 70}")


def report_tracks(tracks: dict):
    print(f"\n{'─' * 70}")
    print(f"  TRACKS")
    print(f"{'─' * 70}")
    print(
        f"  {'Track':20s} {'Notes':>6s} {'Pitch Lo':>8s} {'Pitch Hi':>8s} {'Vel Lo':>6s} {'Vel Hi':>6s} {'Dur Min':>8s} {'Dur Max':>8s}"
    )
    print(f"  {'─' * 20} {'─' * 6} {'─' * 8} {'─' * 8} {'─' * 6} {'─' * 6} {'─' * 8} {'─' * 8}")

    for name, notes in sorted(tracks.items()):
        if not notes:
            continue
        pitches = [n.pitch for n in notes]
        vels = [n.velocity for n in notes]
        durs = [n.duration for n in notes]
        print(
            f"  {name:20s} {len(notes):6d} {min(pitches):8d} {max(pitches):8d} "
            f"{min(vels):6d} {max(vels):6d} {min(durs):8.3f} {max(durs):8.3f}"
        )


def report_psychoacoustic(tracks: dict):
    print(f"\n{'─' * 70}")
    print(f"  PSYCHOACOUSTIC ANALYSIS")
    print(f"{'─' * 70}")

    checks = [
        ("Frequency masking", detect_frequency_masking(tracks)),
        ("Temporal masking", detect_temporal_masking(tracks)),
        ("Harmonic fusion", detect_fusion(tracks)),
        ("Rhythmic blur", detect_blur(tracks)),
        ("Register masking", detect_register_masking(tracks)),
        ("Brightness overload", detect_brightness_overload(tracks)),
    ]

    total = sum(len(evts) for _, evts in checks)
    print(f"  Total issues: {total}\n")

    for name, evts in checks:
        print(f"  {name:25s}: {len(evts):5d}", end="")
        if evts:
            # Show first 3
            print("  ", end="")
            for e in evts[:3]:
                note_b = f" vs {e.track_b}/{e.note_b.pitch}" if e.note_b else ""
                print(f" {e.track_a}/{e.note_a.pitch}{note_b}@{e.beat:.1f}", end="")
            if len(evts) > 3:
                print(f"  ... +{len(evts) - 3} more", end="")
        print()


def report_harmonic(tracks: dict):
    print(f"\n{'─' * 70}")
    print(f"  HARMONIC ANALYSIS")
    print(f"{'─' * 70}")

    config = VerifierConfig(dissonance_tolerance=0.5)
    clashes = detect_clashes(tracks, config)

    by_type = Counter()
    by_track_pair = Counter()
    for c in clashes:
        by_type[c.interval] += 1
        pair = f"{c.track_a}↔{c.track_b}"
        by_track_pair[pair] += 1

    print(f"  Clashes (tolerance=0.5): {len(clashes)}")
    if by_type:
        interval_names = {
            1: "m2",
            2: "M2",
            3: "m3",
            4: "M3",
            5: "P4",
            6: "TT",
            7: "P5",
            8: "m6",
            9: "M6",
            10: "m7",
            11: "M7",
        }
        print(f"\n  By interval:")
        for iv, count in sorted(by_type.items()):
            name = interval_names.get(iv, f"{iv}st")
            bar = "█" * min(count // 5, 40)
            print(f"    {name:4s} ({iv:2d}st): {count:5d}  {bar}")

    if by_track_pair:
        print(f"\n  By track pair:")
        for pair, count in by_track_pair.most_common(10):
            print(f"    {pair:30s}: {count:5d}")


def report_timeline(tracks: dict, total_dur: float):
    """Show which tracks are active in each quarter of the piece."""
    print(f"\n{'─' * 70}")
    print(f"  TIMELINE (track activity)")
    print(f"{'─' * 70}")

    quarters = [0, total_dur * 0.25, total_dur * 0.5, total_dur * 0.75, total_dur]
    labels = ["Q1", "Q2", "Q3", "Q4"]

    for qi in range(4):
        q_start, q_end = quarters[qi], quarters[qi + 1]
        active = []
        for name, notes in sorted(tracks.items()):
            has_notes = any(n.start < q_end and (n.start + n.duration) > q_start for n in notes)
            if has_notes:
                count = sum(
                    1 for n in notes if n.start < q_end and (n.start + n.duration) > q_start
                )
                active.append(f"{name}({count})")
        print(f"  {labels[qi]} ({q_start:.0f}-{q_end:.0f}s): {'  '.join(active)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="MIDI Doctor — diagnose issues")
    p.add_argument("midi_file", nargs="?", help="Path to MIDI file")
    p.add_argument("--script", help="Generate from script instead of reading MIDI")
    p.add_argument("--duration", type=float, default=1.0)
    p.add_argument("--tempo", type=int, default=68)
    p.add_argument("--key", type=int, default=2)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--no-psycho", action="store_true", help="Skip psychoacoustic analysis")
    p.add_argument("--no-harmonic", action="store_true", help="Skip harmonic analysis")
    args = p.parse_args()

    if args.script:
        # Generate from script
        import importlib.util

        spec = importlib.util.spec_from_file_location("script", args.script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        if hasattr(mod, "generate"):
            if hasattr(mod, "build_sections"):
                tracks, _ = mod.generate(args.duration, args.tempo, args.key, args.seed)
            else:
                tool = mod.IdeaTool(
                    mod.IdeaToolConfig(
                        bars=int(args.duration * args.tempo / 4),
                        tempo=args.tempo,
                    )
                )
                result = tool.generate()
                tracks = {k: v for k, v in result.items() if not k.startswith("_")}

        # Fake mido.MidiFile for header
        class FakeMid:
            ticks_per_beat = 480
            length = args.duration * 60

        mid = FakeMid()
        midi_path = args.script
    elif args.midi_file:
        midi_path = args.midi_file
        tracks, mid = midi_to_tracks(midi_path)
    else:
        p.error("Provide a MIDI file or --script")
        return

    # Reports
    report_header(midi_path, mid, tracks)
    report_tracks(tracks)

    if not args.no_psycho:
        report_psychoacoustic(tracks)

    if not args.no_harmonic:
        report_harmonic(tracks)

    report_timeline(tracks, mid.length)

    print(f"\n{'=' * 70}")
    print(f"  Done.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
