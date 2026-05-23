#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/piano_roll.py — Lightweight piano-roll visualizer for Melodica MIDI files.

Usage:
    python3 scripts/piano_roll.py output/album_rave_metal/
    python3 scripts/piano_roll.py output/album_rave_metal/ --dark
    python3 scripts/piano_roll.py some_file.mid
"""

import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from mido import MidiFile


# Track colors — 12 distinct hues, cycling
PALETTE = [
    "#FF3B3B",  # red
    "#3BFF6F",  # green
    "#3B9FFF",  # blue
    "#FFD93B",  # yellow
    "#FF3BFF",  # magenta
    "#3BFFFF",  # cyan
    "#FF8C3B",  # orange
    "#8C3BFF",  # purple
    "#3BFF8C",  # mint
    "#FF3B8C",  # pink
    "#8CFF3B",  # lime
    "#3B8CFF",  # sky
]

DARK_PALETTE = [
    "#FF5555",
    "#55FF99",
    "#5599FF",
    "#FFE055",
    "#FF55FF",
    "#55FFFF",
    "#FF9955",
    "#9955FF",
    "#55FF99",
    "#FF5599",
    "#99FF55",
    "#5599FF",
]


def parse_midi(path: str) -> list[dict]:
    """Parse MIDI file into list of track dicts with notes."""
    mid = MidiFile(path)
    ticks_per_beat = mid.ticks_per_beat

    tracks = []
    for i, track in enumerate(mid.tracks):
        notes = []
        abs_tick = 0
        # {pitch: [(start_tick, velocity)]}
        active = {}

        for msg in track:
            abs_tick += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                active.setdefault(msg.note, []).append((abs_tick, msg.velocity))
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if msg.note in active and active[msg.note]:
                    start_tick, vel = active[msg.note].pop(0)
                    notes.append({
                        "pitch": msg.note,
                        "start": start_tick,
                        "end": abs_tick,
                        "velocity": vel,
                    })

        if notes:
            tempo_msgs = [m for m in track if m.type == "set_tempo"]
            tempo = tempo_msgs[0].tempo if tempo_msgs else 500000
            bpm = 60_000_000 / tempo if tempo else 120
            tracks.append({
                "name": track.name or f"Track {i}",
                "notes": notes,
                "index": i,
                "bpm": bpm,
            })

    # Convert ticks to seconds using first track's tempo
    if tracks:
        tempo = 500000
        for track in mid.tracks:
            for msg in track:
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                    break
            if tempo != 500000:
                break

        sec_per_tick = (tempo / 1_000_000) / ticks_per_beat / ticks_per_beat
        # mido uses absolute ticks — convert via cumsum
        for t in tracks:
            for n in t["notes"]:
                n["start_s"] = n["start"] * sec_per_tick
                n["end_s"] = n["end"] * sec_per_tick
                n["dur_s"] = n["end_s"] - n["start_s"]

    return tracks, ticks_per_beat


def plot_piano_roll(tracks: list[dict], output_path: str, title: str, dark: bool = False):
    """Render piano roll and save as PNG."""
    if not tracks:
        print(f"  No notes to plot for {title}")
        return

    palette = DARK_PALETTE if dark else PALETTE
    bg = "#0D0D0D" if dark else "#FFFFFF"
    text_col = "#CCCCCC" if dark else "#333333"
    grid_col = "#222222" if dark else "#E0E0E0"
    key_black = "#1A1A1A" if dark else "#F0F0F0"

    fig, ax = plt.subplots(figsize=(20, 8), facecolor=bg)
    ax.set_facecolor(bg)

    # Find global ranges
    all_starts = [n["start_s"] for t in tracks for n in t["notes"]]
    all_ends = [n["end_s"] for t in tracks for n in t["notes"]]
    all_pitches = [n["pitch"] for t in tracks for n in t["notes"]]

    t_min = min(all_starts)
    t_max = max(all_ends)
    p_min = min(all_pitches) - 2
    p_max = max(all_pitches) + 2
    dur = t_max - t_min

    # Draw keyboard background (black keys shaded)
    for pitch in range(int(p_min), int(p_max) + 1):
        note_in_octave = pitch % 12
        if note_in_octave in (1, 3, 6, 8, 10):
            ax.axhspan(pitch - 0.5, pitch + 0.5, color=key_black, alpha=0.4, zorder=0)

    # Draw beat grid
    bpm = tracks[0].get("bpm", 120)
    beat_sec = 60.0 / bpm
    bar_sec = beat_sec * 4
    bar_num = 0
    t = t_min
    while t <= t_max:
        alpha = 0.4 if bar_num % 4 == 0 else 0.15
        ax.axvline(x=t, color=grid_col, linewidth=0.5, alpha=alpha, zorder=0)
        t += bar_sec
        bar_num += 1

    # Draw notes per track
    for ti, track in enumerate(sorted(tracks, key=lambda x: x["index"])):
        color = palette[ti % len(palette)]
        for n in track["notes"]:
            s = n["start_s"]
            e = n["end_s"]
            d = max(e - s, 0.02)
            vel_alpha = 0.3 + 0.7 * (n["velocity"] / 127.0)
            rect = mpatches.FancyBboxPatch(
                (s, n["pitch"] - 0.4), d, 0.8,
                boxstyle="round,pad=0.02",
                facecolor=color, edgecolor="none",
                alpha=vel_alpha, zorder=2,
            )
            ax.add_patch(rect)

    # Note labels on left edge
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for pitch in range(int(p_min), int(p_max) + 1):
        if pitch % 12 == 0:
            octave = pitch // 12 - 1
            ax.text(t_min - dur * 0.01, pitch, f"C{octave}",
                    fontsize=7, color=text_col, ha="right", va="center")

    ax.set_xlim(t_min - dur * 0.02, t_max + dur * 0.01)
    ax.set_ylim(p_min, p_max)
    ax.set_xlabel("Time (seconds)", color=text_col, fontsize=10)
    ax.set_ylabel("MIDI Pitch", color=text_col, fontsize=10)
    ax.set_title(title, color=text_col, fontsize=14, fontweight="bold", pad=12)
    ax.tick_params(colors=text_col, labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(grid_col)

    # Legend
    handles = []
    for ti, track in enumerate(sorted(tracks, key=lambda x: x["index"])):
        color = palette[ti % len(palette)]
        n_count = len(track["notes"])
        label = f"{track['name']} ({n_count})"
        handles.append(mpatches.Patch(color=color, label=label))
    ax.legend(
        handles=handles, loc="upper right",
        fontsize=8, facecolor=bg, edgecolor=grid_col,
        labelcolor=text_col, framealpha=0.9,
    )

    # Stats text
    total_notes = sum(len(t["notes"]) for t in tracks)
    stats = f"{total_notes} notes | {bpm:.0f} BPM | {dur:.1f}s | {len(tracks)} tracks"
    ax.text(0.01, 0.01, stats, transform=ax.transAxes,
            fontsize=8, color=text_col, alpha=0.6, va="bottom")

    plt.tight_layout()
    fig.savefig(output_path, dpi=150, facecolor=bg, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Piano roll visualizer for Melodica MIDI")
    parser.add_argument("input", help="MIDI file or directory of MIDI files")
    parser.add_argument("--dark", action="store_true", help="Dark theme")
    parser.add_argument("--output", "-o", help="Output directory (default: same as input)")
    args = parser.parse_args()

    src = Path(args.input)
    if src.is_file() and src.suffix == ".mid":
        midis = [src]
    elif src.is_dir():
        midis = sorted(src.glob("*.mid"))
    else:
        print(f"Error: {args.input} is not a .mid file or directory")
        sys.exit(1)

    if not midis:
        print("No MIDI files found")
        sys.exit(1)

    out_dir = Path(args.output) if args.output else (src.parent if src.is_file() else src)
    out_dir.mkdir(exist_ok=True, parents=True)

    theme = "dark" if args.dark else "light"
    print(f"Piano Roll Visualizer ({theme} theme)")
    print(f"  Processing {len(midis)} file(s)...\n")

    for midi_path in midis:
        print(f"  {midi_path.name}")
        tracks, tpq = parse_midi(str(midi_path))
        out_name = midi_path.stem + "_pianoroll.png"
        out_path = out_dir / out_name
        plot_piano_roll(tracks, str(out_path), midi_path.stem.replace("_", " "), dark=args.dark)

    print(f"\n  Done. Output: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
