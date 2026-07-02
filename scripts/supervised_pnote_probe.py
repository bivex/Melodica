# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
supervised_pnote_probe.py — Cheap test: estimate pnote SUPERVISED from t5harmony
gold chord labels, compare to the deployed (unsupervised-EM) pnote_full.txt.

t5harmony .ntc2:  <beat> <meter> <key_root> <key_mode> [<root> <type> <bass>] [<pc>,...]
The deployed trainer ignores the chord bracket and learns pnote unsupervised via EM,
which self-reinforces degenerate spikes (pnote[2,sus2]=pnote[5,sus4]=1.0). Here we use
the labels directly:  pnote[offset, type] = P(melody offset | labeled type).
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

TYPES = ["Maj", "Min", "Dim", "Aug", "sus2", "sus4", "Maj7", "Min7", "Dom7", "Maj9", "Min9", "Add9"]
N_TONES, N_TYPES = 12, 12
CORPUS = Path("melodica/harmonize/corpus_t5harmony")
DEPLOYED = Path("melodica/harmonize/weights/pnote_full.txt")
BRACKET = re.compile(r"\[([^\]]*)\]")


def estimate_supervised(files: list[Path], smooth_alpha: float = 2.0, center: float = 0.3) -> tuple[np.ndarray, np.ndarray]:
    """Return (pnote[offset,type], per_type_frame_counts)."""
    counts = np.zeros((N_TONES, N_TYPES), dtype=np.float64)  # counts[offset, type]
    frames = np.zeros(N_TYPES, dtype=np.float64)              # frames per type
    for f in files:
        for line in f.read_text().splitlines():
            brackets = BRACKET.findall(line)
            if len(brackets) < 2:
                continue
            try:
                root, ctype, _bass = (int(x) for x in brackets[0].split())
            except ValueError:
                continue
            if not (0 <= root < 12 and 0 <= ctype < N_TYPES):
                continue
            mel = [int(x.strip()) for x in brackets[1].split(",") if x.strip() != ""]
            if not mel:
                continue  # skip rests / empty melody (don't inflate denominator)
            frames[ctype] += 1
            for pc in {pc % 12 for pc in mel}:  # dedup pcs within a frame
                counts[(pc - root) % 12, ctype] += 1
    # MLE + Beta-style smoothing toward `center`
    pnote = (counts + smooth_alpha * center) / (frames + smooth_alpha)
    return np.clip(pnote, 0.001, 0.999), frames


def show(label: str, pnote: np.ndarray, frames: np.ndarray | None = None) -> None:
    print(f"\n=== {label} ===")
    print("offset   " + "".join(f"{t:>6}" for t in TYPES))
    for off, name in [(0, "1"), (2, "2/9"), (3, "m3"), (4, "M3"), (5, "4"), (7, "5"), (10, "7")]:
        print(f"{name:>7}   " + "".join(f"{pnote[off, k]:6.2f}" for k in range(N_TYPES)))
    mass = pnote.sum(axis=0)
    print("mass     " + "".join(f"{m:6.2f}" for m in mass))
    if frames is not None:
        tot = frames.sum() + 1e-9
        print("frames%  " + "".join(f"{100*frames[k]/tot:6.1f}" for k in range(N_TYPES)))


def main() -> None:
    files = sorted(CORPUS.glob("*.ntc2"))
    sample = files[:8000]
    print(f"Corpus: {len(files)} files, probing first {len(sample)}")
    sup, fr = estimate_supervised(sample)
    deployed = np.loadtxt(DEPLOYED)
    show("DEPLOYED pnote_full.txt (unsupervised EM)", deployed)
    show("SUPERVISED from gold [root type] labels", sup, fr)

    print("\n=== Spike check (should shrink) ===")
    for off, tname in [(2, "sus2"), (5, "sus4"), (3, "Dim"), (4, "Aug")]:
        k = TYPES.index(tname)
        print(f"  pnote[{off},{tname}]:  deployed={deployed[off,k]:.2f}  supervised={sup[off,k]:.2f}")


if __name__ == "__main__":
    main()
