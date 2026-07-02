# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
convert_choco_jazz.py — Convert ChoCo JAMS (Harte notation) to .ntc2 format
for supervised HMM training in Melodica.

Partitions converted: real-book, jaah, ireal-pro
Source: /Volumes/External/Code/choco/partitions/*/choco/jams/*.jams
Output: melodica/harmonize/corpus_choco_jazz/

.ntc2 format (one line per beat/chord):
  <beat> <meter> <key_root> <key_mode> [<root> <type> <bass>] []

The melody bracket [] is always empty — ChoCo lead sheets have no melody.
Chord bracket [root type bass] uses the same type indices as t5harmony:
  0=Maj 1=Min 2=Dim 3=Aug 4=sus2 5=sus4 6=Maj7 7=Min7 8=Dom7 9=Maj9 10=Min9 11=Add9

Harte shorthand mapping covers 106 unique types found in ChoCo jazz.
Complex extensions are collapsed to their base triad/7th quality.

Run:
    .venv_dd/bin/python scripts/data/convert_choco_jazz.py
    .venv_dd/bin/python scripts/data/convert_choco_jazz.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Harte root → pitch class
# ---------------------------------------------------------------------------
ROOT_PC: dict[str, int] = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
    "E": 4, "Fb": 4, "E#": 5, "F": 5, "F#": 6, "Gb": 6,
    "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11, "Cb": 11, "B#": 0,
}

KEY_PC: dict[str, int] = {**ROOT_PC}

# ---------------------------------------------------------------------------
# Harte shorthand → our type index
# 0=Maj 1=Min 2=Dim 3=Aug 4=sus2 5=sus4 6=Maj7 7=Min7 8=Dom7 9=Maj9 10=Min9 11=Add9
# ---------------------------------------------------------------------------
# Rules (applied in order, most-specific first):
#   1. Strip bass note (/X) from shorthand
#   2. Map by prefix/content

# Namespaces to accept as chord annotations (in priority order)
CHORD_NAMESPACES = [
    "chord",               # real-book, jaah (standard Harte root:quality)
    "chord_harte",
    "chord_jparser_harte", # jazz-corpus
    "chord_m21_leadsheet", # wikifonia
    "chord_m21_abc",       # nottingham
    "chord_weimar",        # weimar (Ej=Eb notation, NC=no chord)
    # skip chord_roman (when-in-rome) — Roman numeral needs key resolution
    # skip chord_jparser_functional — redundant with harte in jazz-corpus
]

# Weimar enharmonic spellings: j = b (Ej=Eb, Bj=Bb etc.)
_WEIMAR_FIX = str.maketrans("j", "b")

_ROOT_RE = re.compile(r"^([A-G][b#]?)(.*)")


def _parse_no_colon(val: str) -> tuple[int, int] | None:
    """Parse chord strings WITHOUT colon: 'C', 'G7', 'Cm', 'Fm7', 'EbM7', 'A7'.
    Also handles:
      - Weimar/ABC flat notation: 'B-' = Bb, 'E-' = Eb (single '-' after root = flat)
      - Slash chords: 'G/B', 'F/A' → take root only, ignore bass
    Returns (root_pc, type_idx) or None.
    """
    val = val.translate(_WEIMAR_FIX).strip()
    if val in ("N", "NC", "X", "n", ""):
        return None  # no chord

    # strip bass from slash chord before root parsing
    val = val.split("/")[0]

    # ABC/Lilypond flat: root letter + '-' with no other quality suffix
    # e.g. 'B-' → 'Bb', 'E-' → 'Eb', 'B-7' → 'Bb7', 'E-7' → 'Eb7'
    # Only when '-' immediately follows root note (A-G + optional b/#)
    val = re.sub(r'^([A-G][b#]?)-', r'\1b', val)

    m = _ROOT_RE.match(val)
    if not m:
        return None
    root_str, quality = m.group(1), m.group(2)
    root_pc = ROOT_PC.get(root_str)
    if root_pc is None:
        return None
    # normalise quality suffixes to Harte-like for reuse of _harte_to_type
    quality = quality.strip("/").split("/")[0]  # strip bass
    t = _harte_to_type(quality)
    if t is None:
        return None
    return root_pc, t


def _harte_to_type(shorthand: str) -> int | None:
    """Map a Harte chord shorthand to our type index. Returns None for N/X."""
    s = shorthand.strip()

    # silence / no chord / unknown
    if s in ("N", "X", "1"):
        return None

    # empty quality = plain major triad
    if s == "":
        return 0

    # strip bass note
    if "/" in s:
        s = s.split("/")[0]

    # --- explicit interval list (1,b3,b5) style ---
    if s.startswith("("):
        inner = s[1:s.rfind(")")].replace(" ", "")
        tones = set(t.strip() for t in inner.split(","))
        has_b3  = "b3" in tones
        has_3   = "3" in tones
        has_b5  = "b5" in tones
        has_s5  = any(x in tones for x in ("#5", "s5"))
        has_5   = "5" in tones
        has_b7  = "b7" in tones
        has_7   = "7" in tones
        has_4   = "4" in tones
        has_2   = "2" in tones or "9" in tones
        has_sus = has_4 or has_2
        if has_b3 and has_b5 and not has_b7:
            return 2  # dim
        if has_b3 and has_b5 and has_b7:
            return 7  # min7 (half-dim collapsed to min7)
        if has_3 and has_s5 and not has_b7:
            return 3  # aug
        if has_3 and has_s5 and has_b7:
            return 8  # dom7 alt (aug dom7)
        if has_b3 and has_b7:
            return 7  # min7
        if has_b3:
            return 1  # min
        if has_3 and has_b7:
            return 8  # dom7
        if has_3 and has_7:
            return 6  # maj7
        if has_3:
            return 0  # maj
        if has_4 and not has_3 and not has_b3:
            return 5  # sus4
        if has_2 and not has_3 and not has_b3:
            return 4  # sus2
        return 0  # fallback maj

    # --- named shorthands ---

    # Maj7 family
    if re.match(r"^maj7", s) or s in ("maj(7)", "maj7", "maj(7,9)", "maj(7,9,11)",
                                       "maj(7,9,11,13)", "maj(7,9,s11,13)",
                                       "maj(7,b9,11,13)", "maj(7,9,#11)"):
        return 6
    # Maj9/Maj6/add9
    if s in ("maj9", "maj6", "6", "6(9)", "maj(2,*3)", "add9", "maj(9)"):
        return 11  # add9 / Maj9 → collapse to add9
    # Maj
    if s in ("maj", "maj(6)", "maj6"):
        return 0

    # Min7 family
    if re.match(r"^min7", s) or s in ("min7", "m7"):
        return 7
    # Min9
    if s in ("min9", "min(9)", "m9"):
        return 10
    # Min (plain)
    if re.match(r"^min", s) or s in ("m", "min"):
        return 1

    # Dom7 family (7, 9, 11, 13 and alterations)
    if re.match(r"^7", s) or re.match(r"^9", s) or re.match(r"^11", s) or re.match(r"^13", s):
        return 8
    # aug dom7
    if re.match(r"^aug\(b7\)", s) or re.match(r"^aug\(7\)", s):
        return 8
    # aug triad
    if re.match(r"^aug", s):
        return 3

    # Diminished
    if s in ("dim", "dim7", "o", "o7"):
        return 2
    # Half-dim → min7
    if re.match(r"^hdim", s):
        return 7

    # Sus
    if re.match(r"^sus4", s) or s in ("sus", "(1,4)"):
        return 5
    if re.match(r"^sus2", s) or s in ("(1,2)", "(1,2,5)"):
        return 4

    # maj(b7,...) = dom7
    if re.match(r"^maj\(b7", s):
        return 8

    # maj variants not caught above
    if re.match(r"^maj", s):
        return 0

    # power chord / bare 5th
    if s in ("5", "(1,5)"):
        return 0  # treat as maj

    # Additional jazz/extended shorthands from wikifonia/nottingham/weimar
    # Half-dim variants
    if s in ("%7", "ø7", "ø", "hdim7", "hdim", "m7b5", "-m7", "-7b5"):
        return 7  # min7 (half-dim)
    # Dom7 alterations not caught by ^7 prefix
    if s in ("b7", "79", "79b", "79#", "79b", "7+", "7alt", "7 add b9",
             "7911#", "b7911#", "sus7", "sus7913", "sus4,7", "+7", "aug7",
             "mab7", "-mab7", "d"):
        return 8
    # Min variants
    if s in ("-6", "m6", "-m", "-9", "min6"):
        return 1
    # Maj6 / add9 extras
    if s in ("maj(6,9)", "69", "add(9)"):
        return 11
    # Pedal / misc → treat as maj
    if s in ("pedal", "sus2sus4", "1"):
        return 0

    return None  # unmapped


def _parse_key(key_str: str) -> tuple[int, int]:
    """Parse 'F' or 'F:minor' → (root_pc, mode_idx). mode 0=major 1=minor."""
    if not key_str:
        return 0, 0
    parts = key_str.split(":")
    root_str = parts[0].strip()
    mode_str = parts[1].strip().lower() if len(parts) > 1 else "major"
    root_pc  = ROOT_PC.get(root_str, 0)
    mode_idx = 1 if "minor" in mode_str or mode_str == "min" else 0
    return root_pc, mode_idx


def convert_jams(jams_path: Path, out_dir: Path, stats: dict) -> bool:
    """Convert one JAMS file to one .ntc2 file. Returns True on success."""
    try:
        d = json.loads(jams_path.read_text(encoding="utf-8"))
    except Exception:
        stats["read_error"] += 1
        return False

    # --- extract chord and key annotations ---
    chord_ann = key_ann = timesig_ann = None
    for a in d.get("annotations", []):
        ns = a.get("namespace", "")
        if chord_ann is None and ns in CHORD_NAMESPACES:
            chord_ann = a
        elif ns == "key_mode" and key_ann is None:
            key_ann = a
        elif ns == "timesig" and timesig_ann is None:
            timesig_ann = a

    if chord_ann is None or not chord_ann.get("data"):
        stats["no_chords"] += 1
        return False

    # --- key ---
    key_root_pc, key_mode = 0, 0
    if key_ann and key_ann.get("data"):
        key_root_pc, key_mode = _parse_key(key_ann["data"][0].get("value", "C"))

    # --- time signature ---
    meter = 4
    if timesig_ann and timesig_ann.get("data"):
        ts = timesig_ann["data"][0].get("value", {})
        if isinstance(ts, dict):
            meter = ts.get("numerator", 4)

    # --- build lines from chord sequence ---
    lines = []
    beat = 1
    prev_type = None
    for obs in chord_ann["data"]:
        val = obs.get("value", "N")
        if not val or val in ("N", "NC", "X", "n"):
            beat += 1
            prev_type = None
            continue

        if ":" in val:
            # Standard Harte: root:quality or "F minor:V" (roman — skip)
            root_str, shorthand = val.split(":", 1)
            if root_str not in ROOT_PC:
                # Roman numeral like "F minor:V" — skip
                beat += 1
                prev_type = None
                continue
            shorthand = shorthand.split("/")[0]
            root_pc = ROOT_PC.get(root_str)
            chord_type = _harte_to_type(shorthand)
        else:
            # No-colon format: "C", "G7", "Cm", "Fm7", "EbM7" etc.
            parsed = _parse_no_colon(val)
            if parsed is None:
                beat += 1
                prev_type = None
                continue
            root_pc, chord_type = parsed

        if root_pc is None or chord_type is None:
            stats["unmapped"] += 1
            beat += 1
            prev_type = None
            continue

        bass_pc = root_pc  # no separate bass info in lead sheets
        chord_bracket = f"[{root_pc} {chord_type} {bass_pc}]"
        mel_bracket   = "[]"
        lines.append(f"{beat} {meter} {key_root_pc} {key_mode} {chord_bracket} {mel_bracket}")
        beat += 1
        stats["chords"] += 1

    if not lines:
        stats["empty"] += 1
        return False

    stem = jams_path.stem
    out_path = out_dir / f"{stem}.ntc2"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    stats["files"] += 1
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--choco-dir", default="/Volumes/External/Code/choco/partitions",
                    help="Path to ChoCo partitions dir")
    ap.add_argument("--out-dir",   default="melodica/harmonize/corpus_choco_jazz",
                    help="Output .ntc2 corpus directory")
    ap.add_argument("--partitions", nargs="+",
                    default=["real-book", "jaah", "ireal-pro"],
                    help="Which partitions to convert")
    ap.add_argument("--dry-run", action="store_true",
                    help="Parse but don't write files")
    args = ap.parse_args()

    choco_dir = Path(args.choco_dir)
    out_dir   = Path(args.out_dir)
    if not args.dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    stats: dict = {"files": 0, "chords": 0, "unmapped": 0,
                   "no_chords": 0, "empty": 0, "read_error": 0}

    songlist: list[str] = []

    for part in args.partitions:
        jams_dir = choco_dir / part / "choco" / "jams"
        if not jams_dir.exists():
            print(f"  [WARN] not found: {jams_dir}")
            continue
        files = sorted(jams_dir.glob("*.jams"))
        print(f"  {part}: {len(files)} JAMS files")
        for f in files:
            ok = convert_jams(f, out_dir, stats) if not args.dry_run else _dry(f, stats)
            if ok:
                songlist.append(f.stem)

    if not args.dry_run and songlist:
        (out_dir / "songlist.txt").write_text("\n".join(songlist) + "\n")

    total = stats["chords"]
    print(f"\n  Converted : {stats['files']} files  |  {total} chord frames")
    print(f"  Unmapped  : {stats['unmapped']} shorthands skipped")
    print(f"  No chords : {stats['no_chords']}  |  Empty: {stats['empty']}")
    if args.dry_run:
        print("  (dry-run — no files written)")
    else:
        print(f"  Output    : {out_dir.absolute()}")


def _dry(jams_path: Path, stats: dict) -> bool:
    """Dry-run: parse without writing."""
    try:
        d = json.loads(jams_path.read_text(encoding="utf-8"))
    except Exception:
        stats["read_error"] += 1
        return False
    for a in d.get("annotations", []):
        ns = a.get("namespace", "")
        if ns not in CHORD_NAMESPACES:
            continue
        found = 0
        for obs in a.get("data", []):
            val = obs.get("value", "N")
            if not val or val in ("N", "NC", "X", "n"):
                continue
            if ":" in val:
                root_str, sh = val.split(":", 1)
                if root_str not in ROOT_PC:
                    continue
                sh = sh.split("/")[0]
                t = _harte_to_type(sh)
            else:
                parsed = _parse_no_colon(val)
                t = parsed[1] if parsed else None
            if t is None:
                stats["unmapped"] += 1
            else:
                found += 1
                stats["chords"] += 1
        if found:
            stats["files"] += 1
            return True
    stats["no_chords"] += 1
    return False


if __name__ == "__main__":
    main()
