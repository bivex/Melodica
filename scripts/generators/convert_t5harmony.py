# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
convert_t5harmony.py — t5-harmony JSONL → .ntc2 corpus converter

Converts the wrkzk/t5-harmony dataset (49,810 Hooktheory TheoryTab songs,
tokenized in Roman-numeral notation) into .ntc2 files for the HMM trainer.
This is the highest-quality corpus source found: real pop/rock/jazz/etc with
manually-separated melody and chord tracks, plus genre and scale labels.

Token format (from t5-harmony):
  melody: "GENRE_POP RHYTHM_SIMPLE BAR_1 REST DUR_1 NOTE_5-1 DUR_1 ..."
  chords: "SCALE_MAJOR BAR_1 vi DUR_4 BAR_2 IV DUR_4 ..."

  - NOTE_<degree>[<#|b>][+/-<octave>]: scale-degree pitch (relative to key).
      NOTE_1 = tonic, NOTE_5-1 = 5th degree one octave down, NOTE_#4+1 = #4 up
  - Roman numeral chords (I, ii, V7, IV/vi, viidim, etc.) with quality suffixes
  - DUR_<beats>: duration of preceding note/chord
  - BAR_<n>: bar markers (cumulative within song)

This converter:
  1. Decodes the key/scale to a tonic pitch class (assumed C if unknown)
  2. Decodes Roman-numeral chords to absolute (root_pc, type_index, bass_pc)
  3. Decodes NOTE_ scale-degrees to absolute pitch classes
  4. Lays out both onto a per-beat grid and writes .ntc2

Usage:
  python3 scripts/generators/convert_t5harmony.py \
      --src /tmp/t5-harmony/datasets/dataset_chords.jsonl \
      --dst melodica/harmonize/corpus_t5harmony \
      --analyze
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from collections import Counter

# ---------------------------------------------------------------------------
# Scale degree → semitone offset (for major; minor uses natural-minor offsets)
# ---------------------------------------------------------------------------
MAJOR_DEGREES = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
MINOR_DEGREES = {1: 0, 2: 2, 3: 3, 4: 5, 5: 7, 6: 8, 7: 10}
# Modal offsets (relative to major, applied as deltas)
MODE_OFFSETS = {
    'MAJOR': {},
    'MINOR': {3: -1, 6: -1, 7: -1},  # natural minor
    'DORIAN': {3: -1, 7: -1},
    'MIXOLYDIAN': {7: -1},
    'HARMONICMINOR': {3: -1, 6: -1},
    'LYDIAN': {4: 1},
    'PHRYGIAN': {2: -1, 3: -1, 6: -1, 7: -1},
    'PHRYGIANDOMINANT': {2: -1, 6: -1, 7: -1},
    'LOCRIAN': {2: -1, 3: -1, 5: -1, 6: -1, 7: -1},
}

# Roman numeral → scale degree (I=1, II=2, ..., VII=7)
ROMAN_TO_DEGREE = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7,
    'i': 1, 'ii': 2, 'iii': 3, 'iv': 4, 'v': 5, 'vi': 6, 'vii': 7,
}

# Melodica type indices: 0=Maj, 1=Min, 2=Dim, 3=Aug, 4=sus2, 5=sus4,
#   6=Maj7, 7=Min7, 8=Dom7, 9=Maj9, 10=Min9, 11=Add9

# Quality inference from Roman numeral case + suffix
def infer_quality(roman: str) -> int:
    """Infer Melodica chord type from a Roman-numeral token.

    Uppercase (I, IV, V) → major-based; lowercase (ii, vi) → minor-based.
    Suffixes: dim/o, aug/+, 7, maj7, 9, sus, 6, 11, 13.
    """
    s = roman
    # Strip inversion (e.g. IV/vi → IV)
    if '/' in s:
        s = s.split('/')[0]
    # Diminished
    if 'dim' in s.lower() or s.endswith('o'):
        if '7' in s: return 2  # treat dim7 as dim for our 12-type vocab
        return 2
    # Augmented
    if 'aug' in s.lower() or '+' in s:
        return 3
    # Suspended
    if 'sus2' in s: return 4
    if 'sus4' in s or 'sus' in s: return 5
    # Sevenths / ninths
    if 'maj7' in s.lower() or 'M7' in s:
        return 6  # Maj7
    if '9' in s:
        # Major9 vs Minor9 by case
        base = s.rstrip('0123456789')
        if base and base[0].islower():
            return 10  # Minor9
        return 9  # Major9
    if '7' in s:
        # Dom7 if uppercase base, Min7 if lowercase
        base = re.sub(r'[0-9]', '', s)
        if base and base[0].islower():
            return 7  # Min7
        return 8  # Dom7
    if '6' in s:
        # 6th chord — treat as major/minor triad (no 6th type in vocab)
        base = re.sub(r'[0-9]', '', s)
        if base and base[0].islower():
            return 1  # Minor
        return 0  # Major
    # Add9 / 11 / 13 with no 7
    if 'add9' in s.lower() or ('11' in s and '7' not in s) or ('13' in s and '7' not in s):
        return 11  # Add9
    # Plain triad: case determines major/minor
    base = re.sub(r'[^IiVv]', '', s)
    if base and base[0].islower():
        return 1  # Minor
    return 0  # Major


def degree_to_pc(degree: int, scale: str, tonic: int = 0) -> int:
    """Convert a scale degree (1-7) to an absolute pitch class under `scale`."""
    # Apply modal adjustments to major-scale base
    base = MAJOR_DEGREES[degree]
    deltas = MODE_OFFSETS.get(scale, {})
    if degree in deltas:
        base += deltas[degree]
    return (tonic + base) % 12


def parse_note_token(tok: str, scale: str, tonic: int = 0) -> int | None:
    """Parse a NOTE_ token to a pitch class (octave ignored for pc)."""
    # NOTE_#4+1, NOTE_5-1, NOTE_b3, NOTE_1
    m = re.match(r'NOTE_([#b]?)(\d+)([+-]\d+)?', tok)
    if not m:
        return None
    accidental, deg_str, _oct = m.group(1), m.group(2), m.group(3)
    degree = int(deg_str)
    if degree < 1 or degree > 7:
        return None
    pc = degree_to_pc(degree, scale, tonic)
    if accidental == '#':
        pc = (pc + 1) % 12
    elif accidental == 'b':
        pc = (pc - 1) % 12
    return pc


def parse_chord_token(tok: str, scale: str, tonic: int = 0) -> tuple[int, int, int] | None:
    """Parse a Roman-numeral chord token to (root_pc, type_index, bass_pc).

    Token examples: 'IV7/vi', 'viidim', 'I6', 'V7/V', 'IIIaug7', 'iv6'.

    The roman-numeral regex must match LONGEST-first to avoid 'vi' being
    captured as just 'v' (which would mis-parse vi as V). Alternatives are
    ordered by length descending so the regex engine prefers them.
    """
    # Match the roman-numeral portion. Order matters: III before II before I,
    # VII before VI before V, etc. The accidental prefix is optional.
    m = re.match(
        r'([#b]?(?:VII|VI{1,2}|IV|III{0,2}|I|V|vii|vi{1,2}|iv|iii{0,2}|i|v|bVII|bVI{1,2}|bV|bIV|bIII{0,2}|bII|bI|bvii|bvi{1,2}|bv|biv|biii{0,2}|bii|bi|#VII|#VI{1,2}|#V|#IV|#III{0,2}|#II|#I|#vii|#vi{1,2}|#v|#iv|#iii{0,2}|#ii|#i))',
        tok,
    )
    if not m:
        return None
    roman = m.group(1)
    degree = ROMAN_TO_DEGREE.get(roman.lstrip('#b'))
    if degree is None:
        return None
    root_pc = degree_to_pc(degree, scale, tonic)
    # Apply accidental to root
    if roman.startswith('#'):
        root_pc = (root_pc + 1) % 12
    elif roman.startswith('b'):
        root_pc = (root_pc - 1) % 12
    mtype = infer_quality(tok)
    bass_pc = root_pc  # default root position; inversions not parsed here
    return root_pc, mtype, bass_pc


# ---------------------------------------------------------------------------
# Beat-grid layout
# ---------------------------------------------------------------------------
def layout_song(melody_str: str, chord_str: str, scale: str,
                tonic: int = 0, beats_per_measure: int = 4) -> list[str]:
    """Lay out melody + chords on a per-beat grid and return .ntc2 lines."""
    # Parse melody into (start_beat, pc) events
    melody_events: list[tuple[float, int]] = []
    cur_beat = 0.0
    for tok in melody_str.split():
        if tok.startswith('BAR_'):
            bar = int(tok.split('_')[1])
            cur_beat = (bar - 1) * beats_per_measure
        elif tok.startswith('DUR_'):
            cur_beat += float(tok.split('_')[1])
        elif tok.startswith('NOTE_'):
            pc = parse_note_token(tok, scale, tonic)
            if pc is not None:
                melody_events.append((cur_beat, pc))
        elif tok == 'REST':
            pass  # duration handled by following DUR_
    # Parse chords into (start_beat, dur, root, type, bass)
    chord_events: list[tuple[float, float, int, int, int]] = []
    cur_beat = 0.0
    pending_chord = None
    for tok in chord_str.split():
        if tok.startswith('BAR_'):
            bar = int(tok.split('_')[1])
            cur_beat = (bar - 1) * beats_per_measure
        elif tok.startswith('DUR_'):
            dur = float(tok.split('_')[1])
            if pending_chord is not None:
                root, mtype, bass = pending_chord
                chord_events.append((cur_beat, dur, root, mtype, bass))
                cur_beat += dur
                pending_chord = None
            else:
                cur_beat += dur
        elif tok.startswith(('SCALE_', 'GENRE_', 'RHYTHM_')):
            continue
        else:
            parsed = parse_chord_token(tok, scale, tonic)
            if parsed is not None:
                pending_chord = parsed
    # Build per-beat grid
    if not chord_events:
        return []
    max_beat = int(max(b + d for b, d, *_ in chord_events))
    melody_grid: dict[int, list[int]] = {}
    for start, pc in melody_events:
        beat = int(round(start))
        melody_grid.setdefault(beat, []).append(pc)
    chord_grid: dict[int, tuple[int, int, int]] = {}
    for start, dur, root, mtype, bass in chord_events:
        for b in range(int(round(start)), int(round(start + dur))):
            chord_grid[b] = (root, mtype, bass)
    # Emit lines
    lines = []
    meter = f"{beats_per_measure}/4"
    key_mode = 'minor' if scale == 'MINOR' else 'major'
    for beat in range(max_beat + 1):
        pcs = sorted(set(melody_grid.get(beat, [])))
        pc_str = ', '.join(str(p) for p in pcs)
        chord = chord_grid.get(beat)
        if chord:
            chord_str_out = f"[{chord[0]} {chord[1]} {chord[2]}]"
        else:
            chord_str_out = "[- - -]"
        lines.append(
            f"{beat}.0 {meter} {tonic} {key_mode} {chord_str_out} [{pc_str}]"
        )
    return lines


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Convert t5-harmony JSONL → .ntc2 corpus")
    ap.add_argument('--src', required=True,
                    help='Path to dataset_chords.jsonl (or dataset_melody.jsonl)')
    ap.add_argument('--dst', required=True, help='Output directory for .ntc2 files')
    ap.add_argument('--limit', type=int, default=0,
                    help='Max songs to convert (0 = all)')
    ap.add_argument('--analyze', action='store_true',
                    help='Print corpus distribution stats after conversion')
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    print(f"Reading {src}...")
    songs = [json.loads(line) for line in src.read_text().splitlines() if line.strip()]
    if args.limit:
        songs = songs[:args.limit]
    print(f"  {len(songs)} songs")

    converted = 0
    skipped = 0
    type_names = ['Maj', 'Min', 'Dim', 'Aug', 'sus2', 'sus4',
                  'Maj7', 'Min7', 'Dom7', 'Maj9', 'Min9', 'Add9']
    chord_type_counts = Counter()

    for i, s in enumerate(songs):
        melody = s.get('melody', '')
        chords = s.get('chords', '')
        if not melody or not chords:
            skipped += 1
            continue
        # Extract scale. SCALE_X appears in BOTH melody and chords tokens in
        # the chords-prefixed dataset (dataset_chords.jsonl) but only in melody
        # for dataset_melody.jsonl. Search both to be robust.
        scale = 'MAJOR'
        for tok in (chords + ' ' + melody).split():
            if tok.startswith('SCALE_'):
                scale = tok.split('_', 1)[1]
                break
        # Assume tonic = C (0); the Roman-numeral notation is already
        # transposition-invariant so this is fine for HMM training.
        lines = layout_song(melody, chords, scale, tonic=0)
        if not lines:
            skipped += 1
            continue
        # Count chord types
        for line in lines:
            parts = line.split('[')
            for bracket in parts[1:]:
                content = bracket.rstrip(']').strip()
                if content and content != '- - -':
                    toks = content.split()
                    if len(toks) >= 2 and toks[1] != '-':
                        try:
                            chord_type_counts[int(toks[1])] += 1
                        except ValueError:
                            pass
        out_name = f"song_{converted:05d}"
        (dst / f"{out_name}.ntc2").write_text('\n'.join(lines) + '\n')
        converted += 1
        if (i + 1) % 5000 == 0:
            print(f"  ...{i+1}/{len(songs)} processed, {converted} converted")

    print(f"\nConverted: {converted}/{len(songs)}")
    print(f"Skipped: {skipped}")
    # Write songlist
    songs_out = sorted(p.stem for p in dst.glob('*.ntc2'))
    (dst / 'songlist.txt').write_text('\n'.join(songs_out) + '\n')
    print(f"Wrote songlist.txt with {len(songs_out)} entries")

    if args.analyze:
        print()
        print("=" * 60)
        print("CORPUS DISTRIBUTION (chord types)")
        print("=" * 60)
        total = sum(chord_type_counts.values())
        for idx in range(12):
            cnt = chord_type_counts.get(idx, 0)
            pct = cnt / max(total, 1) * 100
            bar = '#' * int(pct / 2)
            print(f"  {type_names[idx]:5s}: {cnt:7d} ({pct:5.1f}%) {bar}")


if __name__ == '__main__':
    main()
