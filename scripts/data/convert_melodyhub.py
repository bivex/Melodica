# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
convert_melodyhub.py — Convert sander-wood/melodyhub harmonization task to .ntc2

Source: HuggingFace sander-wood/melodyhub, task=harmonization
Format: ABC notation, output has chord symbols "X" inline before notes.

Each output .ntc2 line:
  <beat> <meter> <key_root> <key_mode> [<root> <type> <bass>] [<pc>,...]

Only the harmonization task is used (melody + chord labels = pnote gold data).
The input (melody without chords) is ignored; we parse the output (with chords).

Run:
  .venv_dd/bin/python scripts/data/convert_melodyhub.py \
      --limit 50000 --out-dir melodica/harmonize/corpus_melodyhub

  # full dataset (~120k harmonization rows):
  .venv_dd/bin/python scripts/data/convert_melodyhub.py \
      --out-dir melodica/harmonize/corpus_melodyhub
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Note / chord parsing helpers
# ---------------------------------------------------------------------------

# ABC note → semitone offset from C (octave-agnostic)
_ABC_NOTE_PC: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
    "c": 0, "d": 2, "e": 4, "f": 5, "g": 7, "a": 9, "b": 11,
}

# Accidental modifiers
_ACC: dict[str, int] = {"^": 1, "^^": 2, "_": -1, "__": -2, "=": 0}

# ABC key signature → (root_pc, mode_str, accidentals_dict {note_upper: delta})
_KEY_RE = re.compile(r"K:\s*([A-G][#b]?)\s*(m(?:in(?:or)?)?|maj(?:or)?|dor|phr|lyd|mix|loc)?", re.I)
_KEY_ACCIDENTALS: dict[str, dict[str, int]] = {
    # major keys
    "C":  {}, "G":  {"F": 1}, "D":  {"F": 1, "C": 1},
    "A":  {"F": 1, "C": 1, "G": 1}, "E": {"F": 1, "C": 1, "G": 1, "D": 1},
    "B":  {"F": 1, "C": 1, "G": 1, "D": 1, "A": 1},
    "F#": {"F": 1, "C": 1, "G": 1, "D": 1, "A": 1, "E": 1},
    "C#": {"F": 1, "C": 1, "G": 1, "D": 1, "A": 1, "E": 1, "B": 1},
    "F":  {"B": -1}, "Bb": {"B": -1, "E": -1},
    "Eb": {"B": -1, "E": -1, "A": -1}, "Ab": {"B": -1, "E": -1, "A": -1, "D": -1},
    "Db": {"B": -1, "E": -1, "A": -1, "D": -1, "G": -1},
    "Gb": {"B": -1, "E": -1, "A": -1, "D": -1, "G": -1, "C": -1},
    "Cb": {"B": -1, "E": -1, "A": -1, "D": -1, "G": -1, "C": -1, "F": -1},
}
_NOTE_PC: dict[str, int] = {
    "C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11,
    "C#": 1, "D#": 3, "F#": 6, "G#": 8, "A#": 10,
    "Cb": 11, "Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10,
}

# Chord quality → type index (matches coupled_hmm N_TYPES=12)
# 0=Maj 1=Min 2=Dim 3=Aug 4=sus2 5=sus4 6=Maj7 7=Min7 8=Dom7 9=HalfDim 10=FullDim 11=Add9
_QUALITY_MAP: dict[str, int] = {
    # major
    "": 0, "maj": 0, "major": 0, "M": 0,
    # minor
    "m": 1, "min": 1, "minor": 1, "-": 1,
    # diminished
    "dim": 2, "o": 2,
    # augmented
    "aug": 3, "+": 3,
    # sus
    "sus2": 4, "sus4": 5,
    # major 7
    "maj7": 6, "M7": 6, "Δ": 6, "Δ7": 6, "maj9": 6, "M9": 6,
    # minor 7
    "m7": 7, "min7": 7, "-7": 7, "m9": 7, "min9": 7,
    # dominant 7
    "7": 8, "9": 8, "11": 8, "13": 8,
    "7sus4": 8, "7sus2": 8,
    # half-diminished
    "m7b5": 9, "ø": 9, "ø7": 9, "hdim7": 9, "dim7b5": 9,
    # full-diminished
    "dim7": 10, "o7": 10,
    # add9
    "add9": 11, "add2": 11, "madd9": 11,
    # fallbacks
    "6": 0, "m6": 1, "5": 0,
}

_CHORD_RE = re.compile(r'"([^"]*)"')
_NOTE_RE  = re.compile(r'(\^{1,2}|_{1,2}|=)?([A-Ga-g])(/{1,4}|\d*/?(?:\d+)?)?')


def _parse_key(abc_text: str) -> tuple[int, int, dict[str, int]]:
    """Return (root_pc, mode_idx, key_accidentals) from ABC text.
    mode_idx: 0=major, 1=minor (simplified).
    """
    m = _KEY_RE.search(abc_text)
    if not m:
        return 0, 0, {}
    root_str = m.group(1)  # e.g. "G", "Bb", "F#"
    mode_raw = (m.group(2) or "").lower()
    root_pc  = _NOTE_PC.get(root_str, 0)
    mode_idx = 1 if mode_raw.startswith("m") else 0
    # key accidentals: use relative major for minor keys
    if mode_idx == 1:
        # relative major is 3 semitones up
        rel_major_pc = (root_pc + 3) % 12
        rel_str = next((k for k, v in _NOTE_PC.items() if v == rel_major_pc and len(k) <= 2), root_str)
        key_acc = _KEY_ACCIDENTALS.get(rel_str, {})
    else:
        key_acc = _KEY_ACCIDENTALS.get(root_str, {})
    return root_pc, mode_idx, key_acc


def _parse_chord_symbol(chord_str: str) -> tuple[int, int] | None:
    """Parse ABC chord symbol string like 'Am7', 'G7', 'Bb', 'F#m'.
    Returns (root_pc, type_idx) or None if unparseable.
    """
    chord_str = chord_str.strip()
    if not chord_str or chord_str.startswith("^") or chord_str.startswith("_"):
        # annotation, not chord
        return None
    # root note
    m = re.match(r"^([A-G][#b]?)", chord_str)
    if not m:
        return None
    root_str = m.group(1)
    root_pc  = _NOTE_PC.get(root_str)
    if root_pc is None:
        return None
    quality_str = chord_str[len(root_str):]
    # strip bass note /X
    quality_str = re.sub(r"/[A-G][#b]?$", "", quality_str)
    type_idx = _QUALITY_MAP.get(quality_str)
    if type_idx is None:
        # try lowercase
        type_idx = _QUALITY_MAP.get(quality_str.lower())
    if type_idx is None:
        return None
    return root_pc, type_idx


def _abc_notes_in_bar(bar_text: str, key_acc: dict[str, int]) -> list[int]:
    """Extract pitch classes (0-11) from a bar of ABC notation."""
    pcs: list[int] = []
    local_acc: dict[str, int] = {}  # accidentals reset per bar
    for acc_str, note_char, _ in _NOTE_RE.findall(bar_text):
        note_upper = note_char.upper()
        base_pc = _ABC_NOTE_PC.get(note_char)
        if base_pc is None:
            continue
        if acc_str:
            delta = _ACC.get(acc_str, 0)
            local_acc[note_upper] = delta
        elif note_upper in local_acc:
            delta = local_acc[note_upper]
        else:
            delta = key_acc.get(note_upper, 0)
        pc = (base_pc + delta) % 12
        pcs.append(pc)
    return pcs


def _parse_harmonization_output(abc_output: str) -> list[tuple[int, int, list[int]]]:
    """Parse harmonization output ABC → list of (chord_root, chord_type, [melody_pcs]).

    Strategy: split into bars, track current chord (changes at "X" inline),
    collect melody notes per chord span, emit one frame per chord.
    """
    # strip E: field and task header
    lines = [l for l in abc_output.splitlines()
             if not l.startswith("E:") and not l.startswith("%%")]

    # find key
    _, _, key_acc = _parse_key(abc_output)

    # join body lines (after header fields)
    header_fields = {"L:", "M:", "K:", "Q:", "T:", "X:", "C:", "Z:", "N:", "S:", "B:"}
    body_lines = []
    in_body = False
    for line in lines:
        if any(line.startswith(f) for f in header_fields):
            if line.startswith("K:"):
                # key may change mid-score — update key_acc
                _, _, key_acc = _parse_key(line)
                in_body = True
            continue
        if in_body or (line and not line[0].isalpha()):
            in_body = True
            body_lines.append(line)

    body = " ".join(body_lines)

    # tokenize: split on | keeping chord annotations
    frames: list[tuple[int, int, list[int]]] = []
    current_chord: tuple[int, int] | None = None
    current_notes: list[int] = []

    # iterate token by token
    pos = 0
    while pos < len(body):
        # chord annotation
        if body[pos] == '"':
            end = body.find('"', pos + 1)
            if end == -1:
                pos += 1
                continue
            chord_str = body[pos+1:end]
            parsed = _parse_chord_symbol(chord_str)
            if parsed is not None:
                # flush previous chord span
                if current_chord is not None and current_notes:
                    frames.append((*current_chord, current_notes))
                    current_notes = []
                current_chord = parsed
            pos = end + 1
            continue

        # bar line — flush on bar boundary only if no chord change came
        if body[pos] in "|:[]" or body[pos:pos+2] in ("||", "|]", ":|", "[|"):
            pos += 1
            continue

        # note
        m = _NOTE_RE.match(body, pos)
        if m:
            acc_str   = m.group(1) or ""
            note_char = m.group(2)
            note_upper = note_char.upper()
            base_pc = _ABC_NOTE_PC.get(note_char)
            if base_pc is not None and current_chord is not None:
                delta = _ACC.get(acc_str, key_acc.get(note_upper, 0)) if acc_str else key_acc.get(note_upper, 0)
                pc = (base_pc + delta) % 12
                current_notes.append(pc)
            pos = m.end()
            continue

        pos += 1

    # flush last span
    if current_chord is not None and current_notes:
        frames.append((*current_chord, current_notes))

    return frames


def _frames_to_ntc2(frames: list[tuple[int, int, list[int]]], key_root: int, key_mode: int) -> list[str]:
    """Convert frames to .ntc2 lines."""
    lines = []
    beat = 0
    for chord_root, chord_type, mel_pcs in frames:
        mel_str = ",".join(str(pc) for pc in sorted(set(mel_pcs)))
        lines.append(f"{beat} 4 {key_root} {key_mode} [{chord_root} {chord_type} {chord_root}] [{mel_str}]")
        beat += 1
    return lines


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Convert melodyhub harmonization → .ntc2")
    parser.add_argument("--out-dir", default="melodica/harmonize/corpus_melodyhub")
    parser.add_argument("--limit", type=int, default=0, help="Max rows (0=all)")
    parser.add_argument("--split", default="train", choices=["train", "validation"])
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # load existing to skip
    songlist_path = out_dir / "songlist.txt"
    existing: set[str] = set()
    if songlist_path.exists():
        existing = set(songlist_path.read_text().splitlines())

    try:
        from datasets import load_dataset
    except ImportError:
        print("pip install datasets", file=sys.stderr)
        sys.exit(1)

    print(f"Loading melodyhub harmonization (split={args.split}, limit={args.limit or 'all'})...")
    ds = load_dataset("sander-wood/melodyhub", split=args.split, streaming=True)

    converted = 0
    skipped   = 0
    empty     = 0
    unmapped  = 0
    new_names: list[str] = []
    idx = 0

    for row in ds:
        if row["task"] != "harmonization":
            continue

        idx += 1
        if args.limit and idx > args.limit:
            break

        name = f"melodyhub_{idx}"
        if name in existing:
            skipped += 1
            continue

        abc_out = row["output"]
        # parse key from output
        key_root, key_mode, _ = _parse_key(abc_out)

        try:
            frames = _parse_harmonization_output(abc_out)
        except Exception:
            empty += 1
            continue

        if not frames:
            empty += 1
            continue

        lines = _frames_to_ntc2(frames, key_root, key_mode)
        if not lines:
            empty += 1
            continue

        (out_dir / f"{name}.ntc2").write_text("\n".join(lines) + "\n")
        new_names.append(name)
        converted += 1

        if converted % 10_000 == 0:
            print(f"  {converted:,} songs converted...")

        if args.limit and converted >= args.limit:
            break

    # append to songlist
    if new_names:
        with songlist_path.open("a") as f:
            for n in new_names:
                f.write(n + "\n")

    total_frames = sum(
        len(open(out_dir / f"{n}.ntc2").readlines())
        for n in new_names[:100]
    ) * (len(new_names) // max(len(new_names[:100]), 1))

    print(f"\n  Converted : {converted:,} files")
    print(f"  Skipped   : {skipped:,} (already exist)")
    print(f"  Empty     : {empty:,}")
    print(f"  Output    : {out_dir.absolute()}")


if __name__ == "__main__":
    main()
