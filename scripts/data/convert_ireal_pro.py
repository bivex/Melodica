# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
convert_ireal_pro.py — Convert iReal Pro playlists to .ntc2 format
for supervised HMM training in Melodica.

Source: /Volumes/External/Code/choco/partitions/ireal-pro/raw/playlists/*.txt
Output: melodica/harmonize/corpus_ireal_pro/

Uses pyRealParser to decode the scrambled iReal Pro URL format, then maps
iReal chord quality strings to our 12 type indices (same as t5harmony/ChoCo).

.ntc2 format (one line per chord beat):
  <beat> <meter> <key_root> <key_mode> [<root> <type> <bass>] []

No melody — iReal Pro is lead sheets (chord charts only). Contributes to
pchange (jazz ii-V-I transitions) not pnote.

Run:
    .venv_dd/bin/python scripts/data/convert_ireal_pro.py
    .venv_dd/bin/python scripts/data/convert_ireal_pro.py --dry-run
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from pathlib import Path

try:
    from pyRealParser import Tune
except ImportError:
    raise ImportError("pip install pyRealParser")

from urllib.parse import unquote

# ---------------------------------------------------------------------------
# Root → pitch class
# ---------------------------------------------------------------------------
ROOT_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0,
}

# ---------------------------------------------------------------------------
# iReal chord quality → type index
# 0=Maj 1=Min 2=Dim 3=Aug 4=sus2 5=sus4 6=Maj7 7=Min7 8=Dom7 9=Maj9 10=Min9 11=Add9
# ---------------------------------------------------------------------------
# iReal quality suffixes (after root): ^7 ^  -7 - 7 + o h sus add9 69 etc.
def _quality_to_type(q: str) -> int:
    q = q.strip()
    # Maj7
    if q in ("^7", "^", "maj7", "M7", "Maj7", "^9", "^13"):
        return 6
    # Min7
    if q in ("-7", "m7", "min7", "-9", "-11", "-13", "-^7", "m9"):
        return 7
    # Dom7 and extensions
    if q in ("7", "9", "11", "13", "7b9", "7#9", "7b5", "7#5",
             "7alt", "7sus", "7b13", "7#11", "+7", "aug7"):
        return 8
    # Min
    if q in ("-", "m", "min", "-6"):
        return 1
    # Maj (plain or add extensions)
    if q in ("", "6", "69", "add9", "2", "sus2"):
        # disambiguate: sus2=4, add9/2=11, plain=0
        if q in ("sus2", "2"):
            return 4
        if q in ("add9", "69"):
            return 11
        return 0
    # Sus4
    if q in ("sus", "sus4", "7sus4", "sus9"):
        return 5
    # Dim
    if q in ("o", "dim", "o7", "dim7"):
        return 2
    # Half-dim
    if q in ("h7", "h", "hdim", "hdim7", "-7b5", "ø7", "ø"):
        return 7  # collapse half-dim → min7
    # Aug
    if q in ("+", "aug", "aug7"):
        return 3
    # Maj9/add9
    if q in ("^9", "M9", "Maj9", "add9"):
        return 11
    # Fallback — treat unknown as major
    return 0


# Regex to split a measure string like "F^7Ab7" into individual chords
_CHORD_RE = re.compile(
    r'([A-G][b#]?)'                  # root
    r'(\^7|\^|\-7|\-|\+7|\+|7b9|7#9|7b5|7#5|7b13|7#11|7alt|7sus4|7sus|'
    r'7|9|11|13|69|add9|sus4|sus2|sus|hdim7|hdim|dim7|dim|aug7|aug|'
    r'm9|m7|m|maj7|M7|h7|h|ø7|ø|-\^7|-9|-11|-13|-6|6|2)?'  # quality
)


def _parse_ireal_key(key_str: str) -> tuple[int, int]:
    """Parse iReal key like 'F', 'Bb', 'C-', 'Eb-' → (root_pc, mode)."""
    key_str = key_str.strip()
    # Minor keys end with '-'
    minor = key_str.endswith("-")
    root_str = key_str.rstrip("-")
    root_pc = ROOT_PC.get(root_str, 0)
    return root_pc, (1 if minor else 0)


def _measure_to_chords(measure: str) -> list[tuple[int, int]]:
    """Parse iReal measure string → list of (root_pc, type_idx) tuples."""
    chords = []
    for m in _CHORD_RE.finditer(measure):
        root_str = m.group(1)
        quality  = m.group(2) or ""
        root_pc  = ROOT_PC.get(root_str)
        if root_pc is None:
            continue
        ctype = _quality_to_type(quality)
        chords.append((root_pc, ctype))
    return chords


def _safe_stem(title: str) -> str:
    """Make a filesystem-safe stem from song title."""
    # normalize unicode
    s = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    s = re.sub(r'[^\w\s-]', '', s).strip()
    s = re.sub(r'[\s-]+', '_', s)
    return s[:80] or "untitled"


def convert_tune(tune: "Tune", out_dir: Path, stats: dict,
                 seen_stems: set) -> bool:
    """Convert one parsed Tune to a .ntc2 file."""
    try:
        measures = tune.measures_as_strings
    except Exception:
        stats["parse_error"] += 1
        return False

    if not measures:
        stats["empty"] += 1
        return False

    key_root_pc, key_mode = _parse_ireal_key(tune.key or "C")
    meter = tune.time_signature[0] if tune.time_signature else 4

    lines = []
    beat = 1
    prev = None

    for measure in measures:
        if not measure or measure in ("x", "r"):
            beat += meter
            continue
        chords = _measure_to_chords(measure)
        if not chords:
            beat += meter
            continue
        # Distribute chords evenly within the measure
        beats_each = max(1, meter // len(chords))
        for root_pc, ctype in chords:
            chord_bracket = f"[{root_pc} {ctype} {root_pc}]"
            lines.append(f"{beat} {meter} {key_root_pc} {key_mode} "
                         f"{chord_bracket} []")
            prev = (root_pc, ctype)
            beat += beats_each
            stats["chords"] += 1

    if not lines:
        stats["empty"] += 1
        return False

    # Unique stem
    stem = _safe_stem(tune.title)
    orig = stem
    i = 1
    while stem in seen_stems:
        stem = f"{orig}_{i}"
        i += 1
    seen_stems.add(stem)

    (out_dir / f"{stem}.ntc2").write_text("\n".join(lines) + "\n",
                                          encoding="utf-8")
    stats["files"] += 1
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ireal-dir",
                    default="/Volumes/External/Code/choco/partitions/ireal-pro/raw/playlists",
                    help="Directory with iReal Pro .txt playlists")
    ap.add_argument("--out-dir",
                    default="melodica/harmonize/corpus_ireal_pro",
                    help="Output .ntc2 corpus directory")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    ireal_dir = Path(args.ireal_dir)
    out_dir   = Path(args.out_dir)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    stats: dict = {"files": 0, "chords": 0, "parse_error": 0,
                   "empty": 0, "skipped": 0}
    seen_stems: set = set()
    songlist: list[str] = []

    playlist_files = sorted(ireal_dir.glob("*.txt"))
    print(f"Playlists: {len(playlist_files)}")

    for pf in playlist_files:
        try:
            raw = unquote(pf.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  [WARN] read error {pf.name}: {e}")
            continue

        try:
            tunes = Tune.parse_ireal_url(raw)
        except Exception as e:
            print(f"  [WARN] parse error {pf.name}: {e}")
            continue

        print(f"  {pf.name}: {len(tunes)} tunes")
        for tune in tunes:
            stem_before = len(seen_stems)
            ok = (convert_tune(tune, out_dir, stats, seen_stems)
                  if not args.dry_run
                  else _dry_tune(tune, stats, seen_stems))
            if ok:
                # last added stem
                new_stems = seen_stems - set(list(seen_stems)[:-1]) \
                    if len(seen_stems) > stem_before else set()
                if seen_stems:
                    songlist.append(sorted(seen_stems)[-1])

    # Rebuild songlist from seen_stems for correctness
    if not args.dry_run and seen_stems:
        # write songlist in insertion order — re-derive from out_dir
        names = sorted(p.stem for p in out_dir.glob("*.ntc2"))
        (out_dir / "songlist.txt").write_text("\n".join(names) + "\n")

    print(f"\n  Converted : {stats['files']} files  |  {stats['chords']} chord frames")
    print(f"  Errors    : parse={stats['parse_error']}  empty={stats['empty']}")
    if args.dry_run:
        print("  (dry-run — no files written)")
    else:
        print(f"  Output    : {out_dir.absolute()}")


def _dry_tune(tune, stats, seen_stems):
    try:
        measures = tune.measures_as_strings
    except Exception:
        stats["parse_error"] += 1
        return False
    if not measures:
        stats["empty"] += 1
        return False
    total = 0
    for m in measures:
        total += len(_measure_to_chords(m))
    if total == 0:
        stats["empty"] += 1
        return False
    stats["chords"] += total
    stem = _safe_stem(tune.title)
    seen_stems.add(stem)
    stats["files"] += 1
    return True


if __name__ == "__main__":
    main()
