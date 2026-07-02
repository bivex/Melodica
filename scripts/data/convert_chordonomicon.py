# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
convert_chordonomicon.py — Convert Chordonomicon HuggingFace dataset to .ntc2

Source: ailsntua/Chordonomicon (666k songs, chord progressions with section tags)
Format: 'chords' field = '<section_tag> C F G Am <section_tag> ...'
Notation: standard chord symbols, 's' = sharp (Cs=C#, Fs=F#), 'min'=minor suffix

Output: melodica/harmonize/corpus_chordonomicon/*.ntc2
  - No melody bracket (lead sheet — pchange only)
  - [root type bass] labels for supervised pchange estimation

Run:
  .venv_dd/bin/python scripts/data/convert_chordonomicon.py [--limit N] [--out-dir ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Chord symbol parsing
# ---------------------------------------------------------------------------

ROOT_PC: dict[str, int] = {
    "C": 0, "Cs": 1, "C#": 1, "Db": 1,
    "D": 2, "Ds": 3, "D#": 3, "Eb": 3,
    "E": 4, "Es": 5, "Fb": 4,
    "F": 5, "Fs": 6, "F#": 6, "Gb": 6,
    "G": 7, "Gs": 8, "G#": 8, "Ab": 8,
    "A": 9, "As": 10, "A#": 10, "Bb": 10, "Bmin": 11,
    "B": 11, "Bs": 0, "Cb": 11,
}

# Match root (letter + optional s/b/# suffix) then quality
_ROOT_RE = re.compile(r"^([A-G][sb#]?)(.*)")
# Section tags like <verse_1>, <chorus_2>
_TAG_RE = re.compile(r"<[^>]+>")

N_TYPES = 12


def _quality_to_type(q: str) -> int | None:
    """Map quality suffix to our type index 0-11."""
    q = q.strip().split("/")[0]  # strip bass

    if q == "":
        return 0  # plain major
    if q in ("min", "m", "-"):
        return 1
    if q in ("dim", "o", "dim7", "o7"):
        return 2
    if q in ("aug", "+"):
        return 3
    if q in ("sus2",):
        return 4
    if q in ("sus4", "sus"):
        return 5
    if q in ("maj7", "M7", "^7", "Maj7"):
        return 6
    if q in ("min7", "m7", "-7", "min7b5", "m7b5", "%7", "ø7"):
        return 7
    if re.match(r"^(7|9|11|13|7b|7s|7alt|b7)", q):
        return 8  # dom7 family
    if q in ("maj9", "M9", "^9", "6", "add9", "maj6", "69"):
        return 9
    if q in ("min9", "m9", "-9", "min6", "m6"):
        return 10
    if q in ("add9", "2", "madd9"):
        return 11
    # power / no-third chords → major
    if re.match(r"^no3", q) or q in ("5", "no3d", "no3"):
        return 0
    # add/extended with known quality prefix
    if re.match(r"^add", q):
        return 11  # add9 family
    if re.match(r"^(gadd|fadd|cadd|dadd|eadd|badd|aadd)", q, re.I):
        return 11

    # extended / altered — collapse to nearest
    if re.match(r"^(min|m|-)", q):
        return 1
    if re.match(r"^(maj|M|\^)", q):
        return 6
    if re.match(r"^(aug|\+)", q):
        return 3
    if re.match(r"^dim", q):
        return 2
    if re.match(r"^sus", q):
        return 5

    return None  # truly unmapped


def parse_chord(token: str) -> tuple[int, int] | None:
    """Parse a chord token like 'C', 'Fsmin', 'A/Cs', 'Bb7' → (root_pc, type)."""
    token = token.strip()
    if not token or token in ("N", "NC", "X", "n"):
        return None
    # strip bass
    token = token.split("/")[0]
    m = _ROOT_RE.match(token)
    if not m:
        return None
    root_str, quality = m.group(1), m.group(2)
    # Chordonomicon uses 's' for sharp: Cs=C#, Fs=F#, Bmin→special (already in ROOT_PC)
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

def convert_song(chords_str: str, song_id: int, out_dir: Path, stats: dict) -> bool:
    """Convert one Chordonomicon chords string to a .ntc2 file."""
    # strip section tags
    clean = _TAG_RE.sub(" ", chords_str).strip()
    tokens = clean.split()

    lines = []
    beat = 1
    prev: tuple[int, int] | None = None

    for token in tokens:
        parsed = parse_chord(token)
        if parsed is None:
            if token not in ("N", "NC", "X", "n", ""):
                stats["unmapped"] += 1
            beat += 1
            prev = None
            continue
        root_pc, ctype = parsed
        lines.append(f"{beat} 4 0 0 [{root_pc} {ctype} {root_pc}] []")
        beat += 1
        stats["chords"] += 1
        prev = (root_pc, ctype)

    if not lines:
        stats["empty"] += 1
        return False

    out_path = out_dir / f"chordonomicon_{song_id}.ntc2"
    out_path.write_text("\n".join(lines) + "\n")
    stats["files"] += 1
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50000,
                    help="Max songs to convert (default 50000; use 0 for all 666k)")
    ap.add_argument("--out-dir", default="melodica/harmonize/corpus_chordonomicon")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        from datasets import load_dataset
    except ImportError:
        print("ERROR: pip install datasets")
        sys.exit(1)

    out_dir = Path(args.out_dir)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    stats: dict = {"files": 0, "chords": 0, "unmapped": 0, "empty": 0}
    limit = args.limit or 10**9

    print(f"Loading Chordonomicon (streaming, limit={limit})...")
    ds = load_dataset("ailsntua/Chordonomicon", split="train", streaming=True)

    songlist = []
    for i, row in enumerate(ds):
        if i >= limit:
            break
        sid = row.get("id", i)
        chords_str = row.get("chords", "")
        if not chords_str:
            stats["empty"] += 1
            continue
        if args.dry_run:
            # count only
            clean = _TAG_RE.sub(" ", chords_str)
            for tok in clean.split():
                p = parse_chord(tok)
                if p is None and tok not in ("N", "NC", "X", "n", ""):
                    stats["unmapped"] += 1
                elif p is not None:
                    stats["chords"] += 1
            stats["files"] += 1
        else:
            if convert_song(chords_str, sid, out_dir, stats):
                songlist.append(f"chordonomicon_{sid}")

        if (i + 1) % 10000 == 0:
            print(f"  {i+1:,} songs processed...")

    if not args.dry_run and songlist:
        (out_dir / "songlist.txt").write_text("\n".join(songlist) + "\n")

    print(f"\n  Converted : {stats['files']:,} files  |  {stats['chords']:,} chord frames")
    print(f"  Unmapped  : {stats['unmapped']:,} shorthands skipped")
    print(f"  Empty     : {stats['empty']:,}")
    if args.dry_run:
        print("  (dry-run — no files written)")
    else:
        print(f"  Output    : {out_dir.absolute()}")


if __name__ == "__main__":
    main()
