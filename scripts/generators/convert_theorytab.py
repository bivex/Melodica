# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
convert_theorytab.py — Hooktheory TheoryTab → .ntc2 corpus converter

Converts the wayne391/lead-sheet-dataset TheoryTab export (symbol_key JSON
format) into .ntc2 files consumable by the HMM trainer. Each .ntc2 file is
backwards-compatible with the existing load_ntc_songs() loader (binary pc
presence per beat) but carries additional structured fields — chord root,
type, bass, key, meter — so the trainer can learn richer priors when it is
extended to use them.

Format (.ntc2), one line per beat:

    <beat> <meter_num>/<meter_den> <key_root> <key_mode> [<chord_root> <chord_type> <bass_pc>] [<pc>, ...]

Example:

    1.0 4/4 0 major [0 0 0] [0, 4, 7]
    2.0 4/4 0 major [0 0 0] [4, 7, 12]

The [<pc>, ...] bracket at line end is the legacy binary-pc field (the set of
pitch classes present in the melody at that beat). The [<chord_root>
<chord_type> <bass_pc>] bracket is new; legacy loaders ignore it (they only
parse the last bracket).

Usage:

    # Convert the sample corpus (20 songs bundled in the repo)
    python3 scripts/generators/convert_theorytab.py \
        --src /tmp/lead-sheet-dataset/datasets/event \
        --dst melodica/harmonize/corpus_theorytab

    # Convert a full local corpus (after manual download from Google Drive)
    python3 scripts/generators/convert_theorytab.py \
        --src /path/to/lead-sheet-dataset/datasets/event \
        --dst melodica/harmonize/corpus_theorytab

The full corpus (~4.9 GB) lives at:
    https://drive.google.com/file/d/13iB5Brk1hypKsw9TSf8_d4Ka3xU0XmFZ/
Google Drive blocks programmatic download of large files behind a virus-scan
confirmation page, so the full corpus must be downloaded via a browser.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from collections import Counter

# ---------------------------------------------------------------------------
# Chord-type inference
# ---------------------------------------------------------------------------
# IMPORTANT: TheoryTab's chord_type field is NOT a reliable type indicator.
# Empirical inspection of the sample corpus shows:
#   chord_type=5 covers [0,4,7] major (117x), [0,3,7] minor (26x), [0,2,7] sus2 (9x)
#   chord_type=7 covers [0,3,7,10] m7 (73x), [0,4,7,10] dom7 (9x), [0,4,7,11] maj7 (7x)
# So chord_type is a coarse category, not a specific quality. The reliable
# signal is the 'composition' field (the chord's actual pitch classes) — we
# infer the Melodica type from the intervals relative to the chord root.


def infer_melodica_type_from_composition(comp: list[int], root: int) -> int:
    """Infer Melodica chord-type index from a chord's pitch-class composition.

    `comp` is the TheoryTab 'composition' field — absolute MIDI pc values.
    `root` is the chord root pc. Returns a Melodica type index 0-11.

    Uses exact interval-pattern matching against the 12 Melodica chord types.
    Returns 0 (Major) as a default if the pattern doesn't match any known type.
    """
    # Normalize intervals relative to root, deduplicated and sorted
    intervals = tuple(sorted({(pc - root) % 12 for pc in comp}))

    # Triads
    if intervals == (0, 4, 7):
        return 0  # Major
    if intervals == (0, 3, 7):
        return 1  # Minor
    if intervals == (0, 3, 6):
        return 2  # Diminished
    if intervals == (0, 4, 8):
        return 3  # Augmented
    if intervals == (0, 2, 7):
        return 4  # sus2
    if intervals == (0, 5, 7):
        return 5  # sus4
    # Sevenths
    if intervals == (0, 4, 7, 11):
        return 6  # Maj7
    if intervals == (0, 3, 7, 10):
        return 7  # Min7
    if intervals == (0, 4, 7, 10):
        return 8  # Dom7
    # Ninths (sorted interval sets, so 2 comes before 4)
    if intervals == (0, 2, 4, 7, 11):
        return 9  # Maj9
    if intervals == (0, 2, 3, 7, 10):
        return 10  # Min9
    if intervals == (0, 2, 4, 7):
        return 11  # Add9
    # Default to major if pattern doesn't match a known type
    return 0


# ---------------------------------------------------------------------------
# Key name parsing
# ---------------------------------------------------------------------------
KEY_NAME_TO_PC = {
    'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
    'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10,
    'B': 11, 'Cb': 11,
}


def parse_key(key_str: str, mode_str: str) -> tuple[int, str]:
    """Parse TheoryTab key/mode strings into (root_pc, 'major'|'minor')."""
    root = KEY_NAME_TO_PC.get(key_str, 0)
    # mode: '1' = major, '2' = minor (TheoryTab convention)
    mode = 'minor' if str(mode_str) == '2' else 'major'
    return root, mode


# ---------------------------------------------------------------------------
# Beat-grid quantization
# ---------------------------------------------------------------------------
def quantize_to_beats(events: list[dict], num_measures: float,
                      beats_per_measure: int = 4) -> dict[int, list[int]]:
    """Quantize a list of melody events onto a per-beat grid.

    Each melody note is assigned to the beat on which its `event_on` falls.
    Returns {beat_index: [pitch_classes]}.
    """
    grid: dict[int, list[int]] = {}
    for ev in events:
        if not isinstance(ev, dict) or ev.get('isRest'):
            continue
        beat = int(round(ev['event_on']))
        pc = int(ev['pitch']) % 12
        grid.setdefault(beat, []).append(pc)
    return grid


def chords_to_beat_map(chords: list[dict]) -> dict[int, dict]:
    """Map each beat to the chord active on that beat.

    Returns {beat_index: {'root':, 'type':, 'bass':, 'symbol':}}.
    """
    beat_map: dict[int, dict] = {}
    for c in chords:
        if not isinstance(c, dict):
            continue
        start_beat = int(round(c['event_on']))
        duration = int(round(c['event_duration']))
        # Determine Melodica type from composition (chord_type field is unreliable)
        if c.get('composition'):
            m_type = infer_melodica_type_from_composition(
                c['composition'], c.get('root', 0) % 12)
        else:
            m_type = 0  # default major
        for b in range(start_beat, start_beat + duration):
            beat_map[b] = {
                'root': c.get('root', 0) % 12,
                'type': m_type,
                'bass': c.get('bass', c.get('root', 0)) % 12,
                'symbol': c.get('symbol', '?'),
            }
    return beat_map


# ---------------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------------
def convert_song(json_path: Path) -> str | None:
    """Convert one TheoryTab symbol_key.json to .ntc2 text.

    Returns the .ntc2 file contents as a string, or None if the song is
    unusable (no melody, no chords, parse failure).
    """
    try:
        with open(json_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    meta = data.get('metadata', {})
    tracks = data.get('tracks', {})
    melody = tracks.get('melody', [])
    chords = tracks.get('chord', [])
    if not melody or not chords:
        return None

    # Filter out null entries in melody (TheoryTab uses null for rests/ties)
    melody_events = [m for m in melody if isinstance(m, dict)]

    key_root, key_mode = parse_key(meta.get('key', 'C'), meta.get('mode', '1'))
    beats_per_measure = int(meta.get('beats_in_measure', 4))
    meter = f"{beats_per_measure}/4"
    num_measures = data.get('num_measures', 1)
    try:
        num_measures = float(num_measures)
    except (TypeError, ValueError):
        num_measures = 1.0
    total_beats = int(num_measures * beats_per_measure)

    melody_grid = quantize_to_beats(melody_events, num_measures, beats_per_measure)
    chord_map = chords_to_beat_map(chords)

    lines = []
    for beat in range(total_beats):
        pcs = sorted(set(melody_grid.get(beat, [])))
        pc_str = ', '.join(str(p) for p in pcs) if pcs else ''
        chord = chord_map.get(beat)
        if chord:
            chord_str = f"[{chord['root']} {chord['type']} {chord['bass']}]"
        else:
            chord_str = "[- - -]"
        lines.append(
            f"{beat}.0 {meter} {key_root} {key_mode} {chord_str} [{pc_str}]"
        )
    return '\n'.join(lines) + '\n'


def safe_stem(path: Path) -> str:
    """Build a flat, filesystem-safe filename from the nested TheoryTab path.

    Preserves the section name (verse/chorus/bridge/...) so that different
    sections of the same song don't collide. E.g.
        event/a/abba/dancing-queen/chorus_symbol_key.json
    →  abba_dancing-queen_chorus
    """
    parts = path.parts
    # Find 'event' and take everything after it, dropping the trailing filename
    try:
        idx = parts.index('event')
        relevant = list(parts[idx + 1:-1])
    except ValueError:
        relevant = list(path.parent.parts)
    # Append the section name (filename minus the _symbol_key.json suffix)
    section = path.name.replace('_symbol_key.json', '').replace('_roman_key.json', '')
    if section and section not in relevant:
        relevant.append(section)
    name = '_'.join(relevant)
    return re.sub(r'[^A-Za-z0-9_-]+', '-', name).strip('-')


# ---------------------------------------------------------------------------
# Validation & stats
# ---------------------------------------------------------------------------
def analyze_corpus(corpus_dir: Path) -> None:
    """Print distribution statistics for the converted corpus."""
    files = sorted(corpus_dir.glob('*.ntc2'))
    if not files:
        print("  (no .ntc2 files found)")
        return

    chord_types = Counter()
    key_roots = Counter()
    total_beats = 0
    total_songs = 0
    beats_with_chord = 0
    beats_with_melody = 0
    type_names = ['Maj', 'Min', 'Dim', 'Aug', 'sus2', 'sus4',
                  'Maj7', 'Min7', 'Dom7', 'Maj9', 'Min9', 'Add9']

    for f in files:
        total_songs += 1
        for line in f.read_text().splitlines():
            if '[' not in line:
                continue
            total_beats += 1
            # Parse chord bracket
            parts = line.split('[')
            for bracket in parts[1:]:
                content = bracket.rstrip(']').strip()
                if not content or content == '- - -':
                    continue
                tokens = content.split()
                if len(tokens) >= 2 and tokens[0] != '-' and tokens[1] != '-':
                    try:
                        chord_types[type_names[int(tokens[1])]] += 1
                        beats_with_chord += 1
                    except (ValueError, IndexError):
                        pass
            # Parse melody bracket (last one)
            last_bracket = parts[-1].rstrip(']').strip()
            if last_bracket:
                beats_with_melody += 1
            # Key root
            toks = line.split()
            if len(toks) >= 4:
                try:
                    key_roots[int(toks[2])] += 1
                except (ValueError, IndexError):
                    pass

    print(f"  Songs:                {total_songs}")
    print(f"  Total beats:          {total_beats}")
    print(f"  Beats with chord:     {beats_with_chord} ({beats_with_chord/max(total_beats,1):.0%})")
    print(f"  Beats with melody:    {beats_with_melody} ({beats_with_melody/max(total_beats,1):.0%})")
    print()
    print("  Chord type distribution:")
    for name in type_names:
        cnt = chord_types.get(name, 0)
        if cnt:
            pct = cnt / max(beats_with_chord, 1) * 100
            bar = '#' * int(pct / 2)
            print(f"    {name:5s}: {cnt:5d} ({pct:5.1f}%) {bar}")
    print()
    print(f"  Key root distribution (top 6):")
    NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    for pc, cnt in key_roots.most_common(6):
        pct = cnt / max(total_beats, 1) * 100
        print(f"    {NOTE_NAMES[pc]:2s} (pc {pc:2d}): {cnt:5d} ({pct:5.1f}%)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(
        description="Convert Hooktheory TheoryTab → .ntc2 corpus")
    ap.add_argument('--src', required=True,
                    help='Path to lead-sheet-dataset/datasets/event directory')
    ap.add_argument('--dst', required=True,
                    help='Output directory for .ntc2 files')
    ap.add_argument('--analyze', action='store_true',
                    help='Print corpus distribution stats after conversion')
    args = ap.parse_args()

    src = Path(args.src)
    dst = Path(args.dst)
    dst.mkdir(parents=True, exist_ok=True)

    # Find all symbol_key.json files (original key, chord-symbol notation)
    json_files = sorted(src.rglob('*_symbol_key.json'))
    print(f"Found {len(json_files)} symbol_key.json files in {src}")
    if not json_files:
        print("No files found. Expected *_symbol_key.json under --src.")
        return

    converted = 0
    skipped = 0
    for jf in json_files:
        result = convert_song(jf)
        if result is None:
            skipped += 1
            continue
        out_name = safe_stem(jf)
        (dst / f"{out_name}.ntc2").write_text(result)
        converted += 1

    print(f"Converted: {converted}/{len(json_files)}")
    print(f"Skipped (no melody/chords/parse error): {skipped}")
    print(f"Output: {dst}")

    # Write songlist.txt for the trainer
    songlist = dst / 'songlist.txt'
    songs = sorted(p.stem for p in dst.glob('*.ntc2'))
    songlist.write_text('\n'.join(songs) + '\n')
    print(f"Wrote songlist.txt with {len(songs)} entries")

    if args.analyze:
        print()
        print("=" * 60)
        print("CORPUS DISTRIBUTION")
        print("=" * 60)
        analyze_corpus(dst)


if __name__ == '__main__':
    main()
