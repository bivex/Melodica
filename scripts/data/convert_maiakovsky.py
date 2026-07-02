# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
convert_maiakovsky.py — Convert Maiakovsky/song_chord_changes HuggingFace dataset to .ntc2

Source: Maiakovsky/song_chord_changes (539k songs, chord progressions only)
Format: chord_changes column = "G,C,D,Am,..." comma-separated chord names

Since there is no melody, all songs go into corpus_chordonomicon (pchange-only aux).
pnote is NOT affected — these files have empty melody brackets [].

Chord names: "Am", "G7", "F#m7", "Bb", "D/F#" (slash = ignore bass)
Same parser as convert_chordonomicon.py (_parse_no_colon / _quality_to_type).

Usage:
    .venv_dd/bin/python scripts/data/convert_maiakovsky.py [--limit N] [--out-dir DIR] [--dry-run]

Output: one .ntc2 per song in out-dir (default: melodica/harmonize/corpus_chordonomicon)
        appended to existing songlist.txt so train_full_modes --pchange-aux-dir picks them up.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

# ---------------------------------------------------------------------------
# Root / quality tables (mirrors convert_chordonomicon.py)
# ---------------------------------------------------------------------------
ROOT_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4,
    "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8,
    "A": 9, "A#": 10, "Bb": 10, "B": 11,
}

_ROOT_RE = re.compile(
    r"^(C#|Db|D#|Eb|F#|Gb|G#|Ab|A#|Bb|[CDEFGAB])"
)


def _quality_to_type(q: str) -> int | None:
    """Map quality suffix to N_TYPES index (0-11)."""
    q = q.strip().lstrip("/").split("/")[0]  # strip slash bass
    if q == "":
        return 0
    if q in ("min", "m", "-", "mi"):
        return 1
    if q in ("dim", "o", "dim7", "o7", "°", "°7"):
        return 2
    if q in ("aug", "+", "aug7"):
        return 3
    if q in ("sus2",):
        return 4
    if q in ("sus4", "sus"):
        return 5
    if q in ("maj7", "M7", "ma7", "Maj7", "^7", "△7", "△"):
        return 6
    if q in ("7", "dom7", "dom"):
        return 8
    if q in ("m7", "min7", "-7", "mi7"):
        return 7
    if q in ("m7b5", "ø", "ø7", "half-dim", "hdim7", "min7b5"):
        return 9
    if q in ("dim7full", "°7full"):
        return 10
    if q in ("add9", "2", "madd9", "add2"):
        return 11
    # Extended — map to nearest base type
    if re.match(r"^(maj9|maj11|maj13|M9|M11|M13|\^9|\^11|\^13)", q):
        return 6   # Maj7 family
    if re.match(r"^(9|11|13|7sus|7#9|7b9|7#11|7b13|alt)", q):
        return 8   # Dom7 family
    if re.match(r"^(m9|m11|m13|min9|min11|-9|-11)", q):
        return 7   # Min7 family
    if re.match(r"^(6|add6|6/9)", q):
        return 0   # treat as maj
    if re.match(r"^(m6|min6)", q):
        return 1   # treat as min
    if q in ("5", "no3", "no3d", "power"):
        return 0
    return None


def _parse_chord(token: str) -> tuple[int, int] | None:
    """Parse chord token like 'Am', 'G7', 'F#m7', 'Bb', 'D/F#'.
    Returns (root_pc, type_idx) or None.
    """
    token = token.strip()
    if not token or token in ("N", "X", "NC", "%", "-"):
        return None
    # Strip slash bass
    if "/" in token:
        token = token.split("/")[0]
    m = _ROOT_RE.match(token)
    if not m:
        return None
    root_str = m.group(1)
    quality = token[len(root_str):]
    root_pc = ROOT_PC.get(root_str)
    if root_pc is None:
        return None
    t = _quality_to_type(quality)
    if t is None:
        return None
    return root_pc, t


# ---------------------------------------------------------------------------
# Converter
# ---------------------------------------------------------------------------

def convert(limit: int, out_dir: Path, dry_run: bool) -> None:
    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: 'datasets' not installed. Run: pip install datasets", file=sys.stderr)
        sys.exit(1)

    out_dir.mkdir(parents=True, exist_ok=True)
    songlist_path = out_dir / "songlist.txt"

    # Load existing names so we don't duplicate
    existing: set[str] = set()
    if songlist_path.exists():
        existing = {l.strip() for l in songlist_path.read_text().splitlines() if l.strip()}

    print(f"Loading Maiakovsky/song_chord_changes (streaming, limit={limit}) ...")
    ds = load_dataset("Maiakovsky/song_chord_changes", split="train", streaming=True)

    stats: Counter = Counter()
    new_names: list[str] = []
    written = 0

    for i, row in enumerate(ds):
        if written >= limit:
            break

        chord_str = (row.get("chord_changes") or "").strip()
        if not chord_str:
            stats["empty"] += 1
            continue

        tokens = [t.strip() for t in chord_str.split(",") if t.strip()]
        if len(tokens) < 2:
            stats["too_short"] += 1
            continue

        # Parse chord sequence
        parsed: list[tuple[int, int]] = []
        unmapped = 0
        for tok in tokens:
            r = _parse_chord(tok)
            if r:
                parsed.append(r)
            else:
                unmapped += 1

        if len(parsed) < 2:
            stats["no_chords"] += 1
            continue

        stats["mapped"] += len(parsed)
        stats["unmapped"] += unmapped

        name = f"maiakovsky_{i}"
        if name in existing:
            stats["skipped_dup"] += 1
            continue

        # Build .ntc2 lines: [root type bass] [] (no melody)
        lines = []
        beat = 1
        prev = None
        for root_pc, ctype in parsed:
            cur = (root_pc, ctype)
            if prev is not None and cur == prev:
                beat += 1
                prev = cur
                continue  # collapse repeated chords
            lines.append(f"{beat} 4/4 0 major [{root_pc} {ctype} {root_pc}] []")
            beat += 1
            prev = cur

        if len(lines) < 2:
            stats["too_short"] += 1
            continue

        if not dry_run:
            (out_dir / f"{name}.ntc2").write_text("\n".join(lines) + "\n")
            new_names.append(name)

        written += 1
        stats["written"] += 1

    if not dry_run and new_names:
        with open(songlist_path, "a") as f:
            for n in new_names:
                f.write(n + "\n")

    total_chords = stats["mapped"] + stats["unmapped"]
    coverage = 100 * stats["mapped"] / total_chords if total_chords > 0 else 0
    print(f"{'DRY-RUN ' if dry_run else ''}Written: {stats['written']} songs")
    print(f"Chord coverage: {stats['mapped']}/{total_chords} = {coverage:.1f}%")
    print(f"Unmapped: {stats['unmapped']}  empty: {stats['empty']}  too_short: {stats['too_short']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Maiakovsky/song_chord_changes to .ntc2")
    parser.add_argument("--limit", type=int, default=100000,
                        help="Max songs to convert (default: 100000)")
    parser.add_argument("--out-dir", type=str,
                        default="melodica/harmonize/corpus_chordonomicon",
                        help="Output directory (default: corpus_chordonomicon for pchange-only aux)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    convert(args.limit, Path(args.out_dir), args.dry_run)


if __name__ == "__main__":
    main()
