#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
scripts/piano_roll.py — Lightweight piano-roll visualizer for Melodica MIDI files.

Usage:
    python3 scripts/piano_roll.py output/album_rave_metal/
    python3 scripts/piano_roll.py output/album_rave_metal/ --dark
    python3 scripts/piano_roll.py output/album_rave_metal/ --format md
    python3 scripts/piano_roll.py output/album_rave_metal/ --format png+md
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


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _pitch_name(p: int) -> str:
    return f"{NOTE_NAMES[p % 12]}{p // 12 - 1}"


def _fmt_dur(d: float) -> str:
    if d < 0.01:
        return "<0.01s"
    if d < 1.0:
        return f"{d:.2f}s"
    return f"{d:.1f}s"


def _ascii_roll(tracks: list[dict], width: int = 72, height: int = 16) -> str:
    """Generate a compact ASCII piano roll representation."""
    all_notes = [(n["start_s"], n["pitch"], n["end_s"], ti)
                 for ti, t in enumerate(tracks) for n in t["notes"]]
    if not all_notes:
        return "  (no notes)"

    t_min = min(n[0] for n in all_notes)
    t_max = max(n[2] for n in all_notes)
    p_min = min(n[1] for n in all_notes)
    p_max = max(n[1] for n in all_notes)
    t_range = max(t_max - t_min, 0.01)
    p_range = max(p_max - p_min, 1)

    symbols = ["█", "▓", "░", "▪", "●", "◆", "▲", "■", "◇", "△", "○", "□"]
    grid = [[" " for _ in range(width)] for _ in range(height)]

    for start, pitch, end, ti in all_notes:
        col_s = int((start - t_min) / t_range * (width - 1))
        col_e = int((end - t_min) / t_range * (width - 1))
        row = height - 1 - int((pitch - p_min) / p_range * (height - 1))
        row = max(0, min(height - 1, row))
        for c in range(max(0, col_s), min(width, col_e + 1)):
            grid[row][c] = symbols[ti % len(symbols)]

    lines = []
    for r in range(height):
        pitch_at_row = p_max - int(r / (height - 1) * p_range) if height > 1 else p_min
        label = _pitch_name(pitch_at_row) if r % 4 == 0 else "   "
        lines.append(f"  {label} │{''.join(grid[r])}│")
    lines.append(f"      └{'─' * width}┘")
    lines.append(f"       {'0s':<{width // 2}}  {t_range:.1f}s")
    return "\n".join(lines)


def _detect_geometry(tracks: list[dict]) -> list[dict]:
    """Classify each track's geometric pattern on the piano roll."""
    results = []
    for t in sorted(tracks, key=lambda x: x["index"]):
        notes = t["notes"]
        n = len(notes)
        if n == 0:
            continue

        pitches = [nn["pitch"] for nn in notes]
        durs = [nn["dur_s"] for nn in notes]
        starts = [nn["start_s"] for nn in notes]
        vel = [nn["velocity"] for nn in notes]

        p_range = max(pitches) - min(pitches)
        dur_range = max(durs) - min(durs)
        avg_dur = sum(durs) / n
        avg_vel = sum(vel) / n

        # Pitch motion: how much pitch changes between consecutive notes
        if n > 1:
            deltas = [abs(pitches[i + 1] - pitches[i]) for i in range(n - 1)]
            avg_delta = sum(deltas) / len(deltas)
            direction_changes = sum(
                1 for i in range(1, len(deltas))
                if (pitches[i + 1] - pitches[i]) * (pitches[i] - pitches[i - 1]) < 0
            )
        else:
            avg_delta = 0
            direction_changes = 0

        # Rhythm regularity
        if n > 1:
            gaps = [starts[i + 1] - starts[i] for i in range(n - 1)]
            gap_std = (sum((g - sum(gaps) / len(gaps)) ** 2 for g in gaps) / len(gaps)) ** 0.5
        else:
            gaps = []
            gap_std = 0

        # Classify geometry
        shape = "unknown"
        if p_range <= 2 and avg_dur < 0.1 and n > 50:
            shape = "horizontal stripe"
        elif p_range <= 2 and avg_dur > 2.0:
            shape = "sustained bar"
        elif avg_delta > 5 and direction_changes > n * 0.3:
            shape = "zigzag / wave"
        elif avg_delta > 3 and direction_changes < n * 0.15:
            shape = "diagonal sweep"
        elif direction_changes > n * 0.2 and avg_delta > 2:
            shape = "staircase"
        elif p_range <= 8 and gap_std < 0.05 and n > 20:
            shape = "regular grid"
        elif p_range >= 20 and avg_dur > 1.5:
            shape = "wall of sound"
        elif p_range <= 4 and avg_dur < 0.5:
            shape = "rhythmic dots"
        elif p_range <= 12 and avg_dur < 0.2:
            shape = "scatter"
        elif avg_dur > 1.0:
            shape = "block chords"
        else:
            shape = "mixed pattern"

        results.append({
            "name": t["name"],
            "notes": n,
            "pitch_lo": min(pitches),
            "pitch_hi": max(pitches),
            "pitch_range": p_range,
            "dur_min": min(durs),
            "dur_max": max(durs),
            "dur_avg": avg_dur,
            "vel_min": min(vel),
            "vel_max": max(vel),
            "vel_avg": avg_vel,
            "shape": shape,
            "density": n / max(starts[-1] - starts[0], 0.01) if n > 1 else 0,
        })
    return results


def generate_markdown(album_data: list[dict], output_path: str, dark: bool = False):
    """Generate a markdown report for all processed MIDI files."""
    lines = []
    lines.append("# Piano Roll Analysis\n")
    lines.append(f"Theme: {'dark' if dark else 'light'} | "
                 f"Files: {len(album_data)}\n")

    for entry in album_data:
        title = entry["title"]
        tracks = entry["tracks"]
        geo = _detect_geometry(tracks)
        total_notes = sum(g["notes"] for g in geo)
        all_starts = [n["start_s"] for t in tracks for n in t["notes"]]
        all_ends = [n["end_s"] for t in tracks for n in t["notes"]]
        duration = max(all_ends) - min(all_starts) if all_ends else 0
        bpm = tracks[0].get("bpm", 120) if tracks else 0

        lines.append(f"## {title}\n")
        lines.append(f"**{total_notes} notes** | **{bpm:.0f} BPM** | "
                     f"**{duration:.1f}s** | **{len(tracks)} tracks**\n")

        # ASCII piano roll
        lines.append("### Overview\n")
        lines.append("```")
        lines.append(_ascii_roll(tracks))
        lines.append("```\n")

        # Track details table
        lines.append("### Tracks\n")
        lines.append("| Track | Shape | Notes | Pitch | Duration | Vel | Density |")
        lines.append("|-------|-------|------:|-------|----------|-----|--------:|")
        for g in geo:
            pitch_str = f"{_pitch_name(g['pitch_lo'])}–{_pitch_name(g['pitch_hi'])} ({g['pitch_range']})"
            dur_str = f"{_fmt_dur(g['dur_min'])}–{_fmt_dur(g['dur_max'])} (avg {_fmt_dur(g['dur_avg'])})"
            vel_str = f"{g['vel_min']}–{g['vel_max']} ({g['vel_avg']:.0f})"
            lines.append(f"| {g['name']} | {g['shape']} | {g['notes']} "
                         f"| {pitch_str} | {dur_str} | {vel_str} "
                         f"| {g['density']:.1f} n/s |")
        lines.append("")

        # PNG reference
        png_name = entry.get("png_name", "")
        if png_name:
            lines.append(f"![{title}]({png_name})\n")

        lines.append("---\n")

    text = "\n".join(lines)
    Path(output_path).write_text(text, encoding="utf-8")
    print(f"  Saved: {output_path}")


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
            tracks.append({
                "name": track.name or f"Track {i}",
                "notes": notes,
                "index": i,
                "bpm": 0,
            })

    # Find global tempo from any track (conductor track usually has it)
    if tracks:
        tempo = 500000
        for track in mid.tracks:
            for msg in track:
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                    break
            if tempo != 500000:
                break

        bpm = 60_000_000 / tempo if tempo else 120
        sec_per_tick = (tempo / 1_000_000) / ticks_per_beat

        for t in tracks:
            t["bpm"] = bpm
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
    parser.add_argument("--format", "-f", default="png",
                        choices=["png", "md", "png+md"],
                        help="Output format: png, md, or png+md (default: png)")
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

    do_png = args.format in ("png", "png+md")
    do_md = args.format in ("md", "png+md")
    theme = "dark" if args.dark else "light"
    fmt_label = args.format.upper()

    print(f"Piano Roll Visualizer ({theme}, {fmt_label})")
    print(f"  Processing {len(midis)} file(s)...\n")

    album_data = []
    for midi_path in midis:
        print(f"  {midi_path.name}")
        tracks, tpq = parse_midi(str(midi_path))
        title = midi_path.stem.replace("_", " ")
        png_name = ""

        if do_png:
            png_name = midi_path.stem + "_pianoroll.png"
            plot_piano_roll(tracks, str(out_dir / png_name), title, dark=args.dark)

        album_data.append({
            "title": title,
            "tracks": tracks,
            "png_name": png_name,
        })

    if do_md:
        md_name = (src.stem if src.is_dir() else src.stem) + "_pianoroll.md"
        generate_markdown(album_data, str(out_dir / md_name), dark=args.dark)

    print(f"\n  Done. Output: {out_dir.resolve()}")


if __name__ == "__main__":
    main()
