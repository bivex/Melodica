# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
train_supervised_t5.py — SUPERVISED HMM weight estimator from t5harmony gold labels.

Fixes the degenerate-pnote problem at the source. The deployed train_full_modes.py
learns pnote *unsupervised* (it ignores the [root type bass] bracket and rediscovers
chord types via EM), which self-reinforces deterministic spikes
(pnote[2,sus2]=pnote[5,sus4]=pnote[3,dim]=1.0) and kills 7th chords. Real t5harmony
data has the true chord label per beat — this script uses it directly:

  pnote[offset, type]  = P(melody pc at `offset` from root | labeled type)
  pchange[tp, int, tn] = P(next type tn, root interval int | prev type tp)

Both estimated by direct counting with template/Dirichlet smoothing, no EM. For
types absent from the corpus (sus2/sus4/Aug/Maj7 ≈ 0% of real music), the template
prior keeps them usable but never dominant.

Writes melodica/harmonize/weights/pnote_full.txt + pchange_full.npy (backs up the
existing _full files to *_unsup.txt/.npy once).
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

N_TONES, N_TYPES = 12, 12
TYPES = ["Maj", "Min", "Dim", "Aug", "sus2", "sus4", "Maj7", "Min7", "Dom7", "Maj9", "Min9", "Add9"]
CHORD_NOTES = {  # mirror of train_full_modes.py
    0: {0, 4, 7}, 1: {0, 3, 7}, 2: {0, 3, 6}, 3: {0, 4, 8}, 4: {0, 2, 7},
    5: {0, 5, 7}, 6: {0, 4, 7, 11}, 7: {0, 3, 7, 10}, 8: {0, 4, 7, 10},
    9: {0, 4, 7, 11, 2}, 10: {0, 3, 7, 10, 2}, 11: {0, 4, 7, 2},
}
TEMPLATE = np.array(
    # Chord-tone prior for un-attested types set just BELOW the empirical chord-tone
    # rate of data-rich types (~0.27-0.34, e.g. Maj root, Min m3) so ghost types
    # (sus2/sus4/Aug/Maj7 — ~0% of real music) stay pickable but never dominate.
    [[0.22 if off in CHORD_NOTES[k] else 0.06 for off in range(N_TONES)] for k in range(N_TYPES)],
    dtype=np.float64,
).T  # shape [offset, type]

CORPUS = Path("melodica/harmonize/corpus_t5harmony")
WEIGHTS = Path("melodica/harmonize/weights")
BRACKET = re.compile(r"\[([^\]]*)\]")

PNOTE_ALPHA = 3.0      # template-prior strength (empirical dominates once frames >> α)
PCHANGE_PRIOR = 0.5    # Dirichlet strength on pchange
MAX_SELF_LOOP = 0.20   # cap same-(type) repeats, as in the EM trainer


def iter_labeled_frames(files):
    """Yield (root, type, melody_pc_set) for every beat with a chord label + melody."""
    for f in files:
        try:
            text = f.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        for line in text.splitlines():
            brackets = BRACKET.findall(line)
            if len(brackets) < 2:
                continue
            parts = brackets[0].split()
            if len(parts) < 2:
                continue
            try:
                root, ctype = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            if not (0 <= root < 12 and 0 <= ctype < N_TYPES):
                continue
            mel = [int(x.strip()) for x in brackets[1].split(",") if x.strip() != ""]
            if not mel:
                continue
            yield root, ctype, {pc % 12 for pc in mel}


def estimate_pnote(files):
    counts = np.zeros((N_TONES, N_TYPES), dtype=np.float64)
    frames = np.zeros(N_TYPES, dtype=np.float64)
    for root, ctype, pcs in iter_labeled_frames(files):
        frames[ctype] += 1
        for pc in pcs:
            counts[(pc - root) % 12, ctype] += 1
    pnote = (counts + PNOTE_ALPHA * TEMPLATE) / (frames + PNOTE_ALPHA)
    return np.clip(pnote, 0.001, 0.999), frames


def estimate_pchange(files):
    """Supervised transitions over chord-CHANGE points (consecutive identical chords collapsed)."""
    counts = np.zeros((N_TYPES, N_TONES, N_TYPES), dtype=np.float64)
    prev = None  # (root, type) of last *distinct* chord
    for root, ctype, _pcs in iter_labeled_frames(files):
        cur = (root, ctype)
        if prev is not None and cur != prev:
            interval = (root - prev[0]) % 12
            counts[prev[1], interval, ctype] += 1
        prev = cur
    uni = np.ones_like(counts) / (N_TONES * N_TYPES)
    pchange = (counts + PCHANGE_PRIOR * uni)
    pchange /= pchange.sum(axis=(1, 2), keepdims=True)
    # Cap self-loops (same type, interval 0), redistribute — mirrors the EM trainer.
    for t in range(N_TYPES):
        if pchange[t, 0, t] > MAX_SELF_LOOP:
            excess = pchange[t, 0, t] - MAX_SELF_LOOP
            pchange[t, 0, t] = MAX_SELF_LOOP
            others = pchange[t].sum() - MAX_SELF_LOOP
            if others > 1e-9:
                pchange[t] *= 1.0 + excess / others
                pchange[t, 0, t] = MAX_SELF_LOOP
    pchange /= pchange.sum(axis=(1, 2), keepdims=True)
    return pchange


def backup_once():
    for name in ("pnote_full.txt", "pchange_full.npy"):
        src = WEIGHTS / name
        bak = WEIGHTS / name.replace("_full", "_full_unsup")
        if src.exists() and not bak.exists():
            src.replace(bak)
            print(f"  backed up {name} -> {bak.name}")


def main() -> None:
    files = sorted(CORPUS.glob("*.ntc2"))
    print(f"Supervised training on {len(files)} t5harmony songs...")
    pnote, frames = estimate_pnote(files)
    pchange = estimate_pchange(files)

    tot = frames.sum()
    print("Type distribution (frames%):", {TYPES[k]: round(100 * frames[k] / tot, 1) for k in range(N_TYPES) if frames[k] > 0})
    print("Spikes (were 1.00 in deployed):",
          {f"{TYPES[k]}@{off}": round(float(pnote[off, k]), 2)
           for off, k in [(2, 4), (5, 5), (3, 2)]})

    backup_once()
    np.savetxt(WEIGHTS / "pnote_full.txt", pnote)
    np.save(WEIGHTS / "pchange_full.npy", pchange)
    print(f"Wrote {WEIGHTS}/pnote_full.txt + pchange_full.npy (supervised)")


if __name__ == "__main__":
    main()
