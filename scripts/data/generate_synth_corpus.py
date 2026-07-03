#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
generate_synth_corpus.py — rich multi-genre SYNTHETIC chord corpus for
supervised CoupledHMM training. Replaces the old single-script Tymoczko
synth_data (harmonize_todo.md issue #4: "limits harmonic vocabulary, biggest
lever for pchange quality").

Design directly addresses issue #4's two weaknesses:

1. **pchange (transitions)** — encodes REAL multi-genre progression patterns
   so transitions carry genuine voice-leading diversity, not one script's bias:
     jazz ii-V-I (maj & min), turnarounds, pop axis (I-V-vi-IV), 12-bar blues
     (maj & minor), classical I-IV-V-I + deceptive cadence + diminished passing,
     circle-of-5ths, neo-soul i-iv-i-V, sus/add9 color, aug color, 9th jazz.
   Progressions are transposed through all 12 keys (major + minor) so the
   `(prev_type, root_interval, cur_type)` pchange cells populate across every
   interval, not just one key.

2. **pnote (chord-tone profiles) + type coverage** — every chord frame carries
   a melody bracket of its own chord-tone pcs, giving each type a sharp pnote
   profile (matches the chord-tone contour inference technique). A balance pass
   vamps every type across all 12 roots so NONE is a ghost type (sus2/aug/maj9
   etc. get real frames, unlike real corpora where they're ~0%).

.ntc2 line (same format train_full_modes.py parses):
    <beat> <meter> <key_root> <key_mode> [<root> <type> <bass>] [<pc,pc,...>]
type indices: 0 Maj 1 Min 2 Dim 3 Aug 4 sus2 5 sus4 6 Maj7 7 Min7 8 Dom7 9 Maj9 10 Min9 11 Add9

Output: melodica/harmonize/corpus_synth_balanced/
Train:  .venv_dd/bin/python scripts/generators/train_full_modes.py \
            --corpus-dir melodica/harmonize/corpus_synth_balanced --supervised auto
"""
from __future__ import annotations

import argparse
from pathlib import Path

N_TYPES = 12
TYPE_NAMES = ["Maj", "Min", "Dim", "Aug", "sus2", "sus4", "Maj7", "Min7", "Dom7", "Maj9", "Min9", "Add9"]

# type -> chord-tone pcs (root = 0). Melody bracket is filled with these.
TYPE_PCS: dict[int, list[int]] = {
    0: [0, 4, 7], 1: [0, 3, 7], 2: [0, 3, 6], 3: [0, 4, 8],
    4: [0, 2, 7], 5: [0, 5, 7], 6: [0, 4, 7, 11], 7: [0, 3, 7, 10],
    8: [0, 4, 7, 10], 9: [0, 4, 7, 11, 2], 10: [0, 3, 7, 10, 2], 11: [0, 4, 7, 2],
}

# scale-degree semitones (idx 0..6)
MAJ = [0, 2, 4, 5, 7, 9, 11]   # I ii iii IV V vi vii
MIN = [0, 2, 3, 5, 7, 8, 10]   # i ii bIII iv v bVI bVII

# Genre progression templates: (mode, [(degree_idx, type), ...])
GENRES: list[tuple[str, list[tuple[int, int]]]] = [
    ("maj", [(1, 7), (4, 8), (0, 6)]),                       # jazz ii-V-I
    ("min", [(1, 7), (4, 8), (0, 7)]),                       # jazz ii-V-i
    ("maj", [(0, 6), (5, 7), (1, 7), (4, 8)]),               # Imaj7-vim7-iim7-V7 turnaround
    ("maj", [(0, 6), (3, 6), (4, 8), (0, 6)]),               # Imaj7-IVmaj7-V7-Imaj7
    ("maj", [(0, 0), (4, 0), (5, 1), (3, 0)]),               # pop I-V-vi-IV
    ("maj", [(0, 6), (4, 8), (5, 7), (3, 6)]),               # pop 7ths
    ("maj", [(0, 8)] * 4 + [(3, 8)] * 2 + [(0, 8)] * 2 + [(4, 8), (3, 8), (0, 8), (4, 8)]),  # 12-bar blues
    ("min", [(0, 7)] * 4 + [(3, 7)] * 2 + [(0, 7)] * 2 + [(4, 8), (3, 7), (0, 7), (4, 8)]),  # minor blues
    ("maj", [(0, 0), (3, 0), (4, 0), (0, 0)]),               # classical I-IV-V-I
    ("maj", [(0, 0), (3, 0), (4, 0), (5, 1)]),               # classical deceptive (V-vi)
    ("maj", [(0, 0), (6, 2), (5, 1), (4, 0), (0, 0)]),       # I-vii°-vi-V-I (dim passing)
    ("maj", [(0, 6), (4, 8), (1, 7), (5, 8), (3, 6)]),       # circle-of-5ths chain
    ("min", [(0, 7), (3, 7), (0, 7), (4, 8)]),               # neo-soul i-iv-i-V
    ("maj", [(0, 11), (3, 5), (4, 4), (0, 9)]),              # Iadd9-IVsus4-Vsus2-Imaj9 (color)
    ("maj", [(0, 3), (3, 0), (4, 3), (0, 0)]),               # Iaug-IV-Vaug-I (aug color)
    ("maj", [(1, 10), (4, 8), (0, 9)]),                      # iim9-V7-Imaj9 (9th jazz)
    ("min", [(0, 10), (3, 7), (0, 7), (4, 8)]),              # im9-iv7-i7-V7
    ("maj", [(0, 0), (1, 7), (4, 8), (0, 6)]),               # I-iim7-V7-Imaj7
]

# types that are rare in real corpora and need a coverage top-up here
RARE_TYPES = [2, 3, 4, 5, 9, 10, 11]


def _emit(lines: list[str], key_root: int, mode: str, seq: list[tuple[int, int]],
          beats_per_chord: int = 4, meter: int = 4, start_beat: int = 1) -> None:
    scale = MAJ if mode == "maj" else MIN
    kmode = 0 if mode == "maj" else 1
    beat = start_beat
    for deg, ctype in seq:
        root = (key_root + scale[deg]) % 12
        mel = ",".join(str((root + pc) % 12) for pc in TYPE_PCS[ctype])
        lines.append(f"{beat} {meter} {key_root} {kmode} [{root} {ctype} {root}] [{mel}]")
        beat += beats_per_chord


def build(out_dir: Path, repeats: int, balance_target: int) -> dict[str, int]:
    out_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, int] = {"songs": 0, "frames": 0, "types": {t: 0 for t in range(N_TYPES)}}

    def write_song(stem: str, lines: list[str]) -> None:
        if not lines:
            return
        (out_dir / f"{stem}.ntc2").write_text("\n".join(lines) + "\n", encoding="utf-8")
        stats["songs"] += 1
        stats["frames"] += len(lines)
        for ln in lines:
            br = ln.split("] [")[1].rstrip("]") if "] [" in ln else ""
            for tok in br.split(","):
                tok = tok.strip()
                # chord type is the 2nd token inside the first bracket
            # count type from the chord bracket
            cbr = ln.split("[")[1].split("]")[0].split()
            stats["types"][int(cbr[1])] += 1

    # --- 1. genre songs: every key × every matching-mode template, repeated ---
    n = 0
    for key in range(12):
        for gi, (mode, seq) in enumerate(GENRES):
            lines: list[str] = []
            _emit(lines, key, mode, seq * repeats)
            write_song(f"synth_{key:02d}_{mode}_g{gi:02d}", lines)
            n += 1
        # medley: chain all templates of each mode in one key (rich transitions)
        for mode in ("maj", "min"):
            medley = [step for m, s in GENRES if m == mode for step in s]
            lines = []
            _emit(lines, key, mode, medley)
            write_song(f"synth_{key:02d}_{mode}_medley", lines)

    # --- 2. balance pass: vamp every rare type, alternating with a SPREAD of
    #     underrepresented common types (V7/Imaj7/vi-min/ii-min7), so rare types
    #     get coverage AND Dom7/Maj7/Min/Min7 get boosted — without flooding Maj.
    ANCHORS = [(0, 0), (0, 0), (0, 0), (4, 8), (0, 6), (5, 1), (5, 1), (1, 7)]
    # 3× Maj, 2× Min, + Dom7/Maj7/Min7 — plain triads dominate like real music
    for t in RARE_TYPES:
        d = _rare_degree(t)
        vamp = [step for a in ANCHORS for step in (a, (d, t))]
        files = 0
        while stats["types"][t] < balance_target:
            lines: list[str] = []
            for key in range(12):
                _emit(lines, key, "maj", vamp)
            write_song(f"synth_balance_t{t}_{files}", lines)
            files += 1
    return stats


def _rare_degree(t: int) -> int:
    # pick a musically natural scale-degree for the rare type's vamp
    return {2: 6, 3: 0, 4: 4, 5: 3, 9: 0, 10: 1, 11: 0}.get(t, 0)  # vii°/I/V/IV/I/ii/I


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="melodica/harmonize/corpus_synth_balanced")
    ap.add_argument("--repeats", type=int, default=3, help="chorus repeats per genre song")
    ap.add_argument("--balance-target", type=int, default=2400,
                    help="min frames per rare type (coverage floor)")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    stats = build(out_dir, args.repeats, args.balance_target)

    (out_dir / "songlist.txt").write_text(
        "\n".join(p.stem for p in sorted(out_dir.glob("*.ntc2"))) + "\n", encoding="utf-8")

    tot = stats["frames"]
    print(f"=== synthetic corpus: {stats['songs']} songs | {tot} frames ===")
    print(f"  output: {out_dir.absolute()}")
    print("  type coverage:")
    for t in range(N_TYPES):
        n = stats["types"][t]
        flag = "  ← UNDER" if n < args.balance_target else ""
        print(f"    {t:>2} {TYPE_NAMES[t]:<5} {n:>6}  {100*n/tot:5.1f}%{flag}")


if __name__ == "__main__":
    main()
