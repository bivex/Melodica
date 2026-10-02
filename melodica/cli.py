# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.cli — Official Command Line Interface for Melodica.

Commands:
    melodica build <score.song> [-o output.mid] [--play] [--verbose]
    melodica check <score.song>
    melodica list-instruments [--family <family>]
    melodica inspect <file.mid>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from melodica.generate.profile import get_profile, list_profiles
from melodica.score.compiler import compile_song_to_midi, compile_song_to_tracks
from melodica.score.parser import parse_song, parse_song_file


def _build_command(args: argparse.Namespace) -> int:
    song_path = Path(args.song_file)
    if not song_path.is_file():
        print(f"Error: Song file not found: {song_path}", file=sys.stderr)
        return 1

    try:
        song = parse_song_file(song_path)
    except Exception as e:
        print(f"Error parsing {song_path}: {e}", file=sys.stderr)
        return 1

    output_path = Path(args.output) if args.output else song_path.with_suffix(".mid")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tracks_data, markers = compile_song_to_tracks(song)
    compile_song_to_midi(song, output_path)

    total_notes = sum(len(notes) for notes in tracks_data.values())

    print(f"✓ Built: {song.title or song_path.stem}")
    print(f"  Key: {song.key} | Tempo: {song.tempo} BPM | Time: {song.time_signature} | Feel: {song.feel or 'straight'}")
    print(f"  Form: {' -> '.join(song.form)} ({song.total_bars()} bars total)")
    print(f"  Tracks ({len(tracks_data)}): {', '.join(tracks_data.keys())} ({total_notes} notes total)")
    print(f"  Output MIDI: {output_path.resolve()}")

    if getattr(args, "play", False):
        _play_midi(output_path)

    return 0


def _check_command(args: argparse.Namespace) -> int:
    song_path = Path(args.song_file)
    if not song_path.is_file():
        print(f"Error: File not found: {song_path}", file=sys.stderr)
        return 1

    try:
        song = parse_song_file(song_path)
    except Exception as e:
        print(f"✗ Validation failed for {song_path}: {e}", file=sys.stderr)
        return 1

    markers, all_chords = song.unrolled_timeline()
    missing_sections = [s for s in song.form if s not in song.sections]

    if missing_sections:
        print(f"✗ Error: Sections defined in form but missing in song: {missing_sections}", file=sys.stderr)
        return 1

    print(f"✓ Valid score: {song.title or song_path.stem}")
    print(f"  Key: {song.key} | Tempo: {song.tempo} BPM | Time: {song.time_signature}")
    print(f"  Sections defined: {list(song.sections.keys())}")
    print(f"  Total bars: {song.total_bars()} | Chords: {len(all_chords)} | Duration: {song.total_beats()} beats")
    print(f"  Arranged tracks: {list(song.arrange.keys())}")
    return 0


def _list_instruments_command(args: argparse.Namespace) -> int:
    profiles = list_profiles()
    target_family = (args.family or "").lower().strip()

    print(f"Available Melodica Instruments ({len(profiles)} total):")
    print(f"{'ID':24s} {'Family':12s} {'GM':4s} {'Range':12s} {'Poly':5s} {'Name'}")
    print("-" * 75)

    count = 0
    for pid in profiles:
        prof = get_profile(pid)
        if target_family and prof.family.lower() != target_family:
            continue
        count += 1
        rng = f"{prof.range_low}..{prof.range_high}"
        print(f"{prof.id:24s} {prof.family:12s} {prof.gm_program:3d}  {rng:12s} {prof.max_polyphony:4d}  {prof.name}")

    if target_family:
        print(f"\nFiltered by family '{target_family}': {count} instruments.")
    return 0


def _summarize_track(i: int, track: Any) -> str:
    name = getattr(track, "name", "") or f"Track {i}"
    note_ons = sum(1 for m in track if m.type == "note_on" and m.velocity > 0)
    markers = [m.text for m in track if m.type in ("marker", "text")]
    suffix = f" | Markers: {', '.join(markers[:3])}" if markers else ""
    return f"  [{i}] {name:20s}: {note_ons:4d} note events{suffix}"


def _inspect_command(args: argparse.Namespace) -> int:
    import mido

    midi_path = Path(args.midi_file)
    if not midi_path.is_file():
        print(f"Error: MIDI file not found: {midi_path}", file=sys.stderr)
        return 1

    mid = mido.MidiFile(str(midi_path))
    print(f"MIDI Inspection: {midi_path.name}")
    print(f"  Type: {mid.type} | Ticks per beat: {mid.ticks_per_beat} | Tracks: {len(mid.tracks)}")

    for i, track in enumerate(mid.tracks):
        print(_summarize_track(i, track))
    return 0


def _play_midi(midi_path: Path) -> None:
    """Attempt playback using platform tools or birka."""
    import shutil
    import subprocess

    # On macOS, check for afplay or timidity
    if shutil.which("timidity"):
        subprocess.run(["timidity", str(midi_path)])
    else:
        print(f"Note: playback requested, file is ready at {midi_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="melodica",
        description="Melodica — Algorithmic Music Composition & Score Compiler CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # build
    build_p = subparsers.add_parser("build", help="Compile a .song score into multi-track MIDI")
    build_p.add_argument("song_file", help="Path to .song file")
    build_p.add_argument("-o", "--output", help="Path to destination .mid file")
    build_p.add_argument("--play", action="store_true", help="Play MIDI after building")
    build_p.add_argument("-v", "--verbose", action="store_true", help="Verbose output")

    # check
    check_p = subparsers.add_parser("check", help="Validate a .song file syntax and structure")
    check_p.add_argument("song_file", help="Path to .song file")

    # list-instruments
    list_p = subparsers.add_parser("list-instruments", help="List available TOML instrument profiles")
    list_p.add_argument("-f", "--family", help="Filter by family (e.g. mallet, plucked, wind_brass)")

    # inspect
    inspect_p = subparsers.add_parser("inspect", help="Inspect an exported MIDI file structure")
    inspect_p.add_argument("midi_file", help="Path to .mid file")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "build": _build_command,
        "check": _check_command,
        "list-instruments": _list_instruments_command,
        "inspect": _inspect_command,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
