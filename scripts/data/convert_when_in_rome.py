#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
convert_when_in_rome.py — Convert the When-in-Rome ChoCo partition
(chord_roman JAMS) to .ntc2 format for supervised HMM training.

Source: /Volumes/External/Code/choco/partitions/when-in-rome/choco/jams/*.jams
Output: melodica/harmonize/corpus_when_in_rome/

When-in-Rome is KEY-AWARE Roman-numeral analysis of classical music (~898
pieces: sonatas, quartets, orchestral, lieder, choral). Each chord observation
is "<local key>:<roman>" — e.g. "Bb major:V7", "C minor:viiø7", "D major:V/V" —
so every chord carries its own local key (modulations handled per-chord).

We resolve each "<key>:<roman>" to (root_pc, type_idx) and write the same .ntc2
line format as convert_choco_jazz.py:

    <beat> <meter> <key_root> <key_mode> [<root> <type> <bass>] []

Type indices (matches train_full_modes.py N_TYPES=12, "Cinematic Expanded"):
    0=Maj 1=Min 2=Dim 3=Aug 4=sus2 5=sus4 6=Maj7 7=Min7 8=Dom7 9=Maj9 10=Min9 11=Add9

NOTE — halfdim/fulldim collapse (consistent with the trained model's 12 types):
  viiø7 / iiø7 (half-dim) -> Min7 (7)   [m7b5 has no distinct type]
  vii°7 (full-dim)        -> Dim (2)
To retain halfdim as its own quality you must first EXTEND the vocabulary
(N_TYPES 12->13 + pnote/pchange templates + retrain); see docs/TONALITY_COVERAGE.md
Limitations. Inversions are read but bass is set to the chord root (matches the
lead-sheet converters, which carry no separate bass).

Run:
    .venv_dd/bin/python scripts/data/convert_when_in_rome.py --dry-run
    .venv_dd/bin/python scripts/data/convert_when_in_rome.py
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# pitch-class map
# ---------------------------------------------------------------------------
ROOT_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0,
}

# Scale-degree -> semitone offset from tonic.
DEG_MAJ = {"i": 0, "ii": 2, "iii": 4, "iv": 5, "v": 7, "vi": 9, "vii": 11}
DEG_MIN = {"i": 0, "ii": 2, "iii": 3, "iv": 5, "v": 7, "vi": 8, "vii": 10}

_NUM_RE = re.compile(r"^([b#]?)([iIvV]+)(.*)$")


def _parse_key(key_str: str) -> tuple[int, bool] | None:
    """'Bb major' / 'F# minor' / 'C' -> (key_root_pc, is_minor). None if unparseable."""
    parts = key_str.strip().split()
    root_str = parts[0]
    root_pc = ROOT_PC.get(root_str)
    if root_pc is None:
        return None
    is_minor = len(parts) > 1 and "minor" in parts[1].lower()
    return root_pc, is_minor


def _quality_and_root(key_root: int, is_minor: bool, roman: str) -> tuple[int, int] | None:
    """Resolve one roman numeral (no '/') to (root_pc, type_idx), or None.

    type: 0 Maj 1 Min 2 Dim 3 Aug 5 sus4 6 Maj7 7 Min7 8 Dom7
    (sus2/4, 9ths etc. mapped where they appear; halfdim->Min7, fulldim->Dim.)
    """
    m = _NUM_RE.match(roman)
    if not m:
        return None
    acc, numeral, rest = m.group(1), m.group(2), m.group(3)
    low = numeral.lower()
    if low not in DEG_MAJ:
        return None

    deg_map = DEG_MIN if is_minor else DEG_MAJ
    deg = deg_map[low]
    # raised leading tone in minor: vii°/viiø sits on the leading tone (#7)
    if is_minor and low == "vii" and ("°" in rest or "o" in rest or "ø" in rest):
        deg = 11
    if acc == "b":
        deg -= 1
    elif acc == "#":
        deg += 1
    root_pc = (key_root + deg) % 12

    is_upper = numeral[0].isupper()  # major-quality triad
    r = rest
    # diminished / half-diminished / augmented symbols
    if "°" in r or re.search(r"(?<![a-z])o(?!ct)", r):   # ° or bare 'o' = diminished
        return root_pc, 2                                  # dim (dim7 collapses here)
    if "ø" in r or "ø" in r:                              # half-diminished
        return root_pc, 7                                  # collapse -> Min7
    if "+" in r:                                          # augmented
        return root_pc, 3

    # strip figured-bass inversion digits, keep a standalone 7 = seventh chord
    has_7 = bool(re.search(r"(?<![1-9])7(?![0-9])", r))
    if has_7:
        return root_pc, (8 if is_upper else 7)            # V7->Dom7, ii7->Min7
    # plain triad
    return root_pc, (0 if is_upper else 1)


def resolve_roman(key_root: int, is_minor: bool, roman: str) -> tuple[int, int] | None:
    """Resolve '<roman>' possibly with a secondary-dominant slash 'V/V', 'vii°7/IV'.
    The denominator is a roman in the CURRENT key whose root becomes a temporary
    (major) key for the numerator."""
    roman = roman.strip()
    if not roman or roman in ("N", "NC", "X"):
        return None
    if "/" in roman:
        num, denom = roman.split("/", 1)
        d = _quality_and_root(key_root, is_minor, denom.strip())
        if d is None:
            return None
        # denominator's root = temporary key (treat as major for secondary doms)
        return _quality_and_root(d[0], False, num.strip())
    return _quality_and_root(key_root, is_minor, roman)


def convert_jams(jams_path: Path, out_dir: Path, stats: dict) -> bool:
    try:
        d = json.loads(jams_path.read_text(encoding="utf-8"))
    except Exception:
        stats["read_error"] += 1
        return False

    chord_ann = timesig_ann = None
    for a in d.get("annotations", []):
        ns = a.get("namespace", "")
        if chord_ann is None and ns == "chord_roman":
            chord_ann = a
        elif timesig_ann is None and ns == "timesig":
            timesig_ann = a
    if chord_ann is None or not chord_ann.get("data"):
        stats["no_chords"] += 1
        return False

    meter = 4
    if timesig_ann and timesig_ann.get("data"):
        ts = timesig_ann["data"][0].get("value", {})
        if isinstance(ts, dict):
            meter = ts.get("numerator", 4)

    lines = []
    beat = 1
    # global key fallback (from first chord's key prefix, refined per-chord)
    g_root, g_min = 0, False
    for obs in chord_ann["data"]:
        val = obs.get("value", "").strip()
        beat += 1
        if not val or val in ("N", "NC", "X"):
            continue
        if ":" not in val:
            stats["unmapped"] += 1
            continue
        key_str, roman = val.split(":", 1)
        kp = _parse_key(key_str)
        if kp is None:
            stats["bad_key"] += 1
            continue
        k_root, k_min = kp
        g_root, g_min = k_root, k_min  # track local key for the line's key_root/mode
        res = resolve_roman(k_root, k_min, roman)
        if res is None:
            stats["unmapped"] += 1
            continue
        root_pc, ctype = res
        if not (0 <= ctype < 12):
            stats["unmapped"] += 1
            continue
        bass_pc = root_pc
        key_mode = 1 if k_min else 0
        lines.append(f"{beat} {meter} {k_root} {key_mode} [{root_pc} {ctype} {bass_pc}] []")
        stats["chords"] += 1
        # type histogram
        stats["types"][ctype] += 1

    if not lines:
        stats["empty"] += 1
        return False
    if not stats.get("_dry"):
        out_path = out_dir / f"{jams_path.stem}.ntc2"
        out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stats["files"] += 1
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--choco-dir", default="/Volumes/External/Code/choco/partitions")
    ap.add_argument("--partitions", nargs="+", default=["when-in-rome"])
    ap.add_argument("--out-dir", default="melodica/harmonize/corpus_when_in_rome")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    stats: dict = {"files": 0, "chords": 0, "unmapped": 0, "no_chords": 0,
                   "empty": 0, "bad_key": 0, "read_error": 0,
                   "types": {i: 0 for i in range(12)}, "_dry": args.dry_run}
    songlist: list[str] = []

    names = ["Maj", "Min", "Dim", "Aug", "sus2", "sus4", "Maj7", "Min7", "Dom7", "Maj9", "Min9", "Add9"]
    for part in args.partitions:
        jams_dir = Path(args.choco_dir) / part / "choco" / "jams"
        if not jams_dir.exists():
            print(f"  [WARN] not found: {jams_dir}")
            continue
        files = sorted(jams_dir.glob("*.jams"))
        print(f"  {part}: {len(files)} JAMS files")
        for f in files:
            if convert_jams(f, out_dir, stats):
                songlist.append(f.stem)

    if not args.dry_run and songlist:
        (out_dir / "songlist.txt").write_text("\n".join(songlist) + "\n")

    total = stats["chords"]
    print(f"\n  Converted : {stats['files']} files  |  {total} chord frames")
    print(f"  Unmapped  : {stats['unmapped']} roman numerals skipped")
    print(f"  Bad key   : {stats['bad_key']}  |  No chords: {stats['no_chords']}  |  Empty: {stats['empty']}")
    if total:
        print("  Type histogram:")
        for t in range(12):
            if stats["types"][t]:
                pct = 100.0 * stats["types"][t] / total
                print(f"    {t:>2} {names[t]:<5} {stats['types'][t]:>7}  {pct:5.1f}%")
    if args.dry_run:
        print("  (dry-run — no files written)")
    else:
        print(f"  Output    : {out_dir.absolute()}")


if __name__ == "__main__":
    main()
