# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/train_full_modes.py — Train Coupled HMM on synthetic corpus (all 78 modes).
Uses Metal GPU acceleration via PyTorch.
Expands from 3 chord types to 6 (Major, Minor, Dim, Aug, sus2, sus4).
"""

import torch
import numpy as np
from pathlib import Path
import time
from tqdm import tqdm


N_TONES = 12
N_TYPES = 6  # Expanded from 3
MAX_ITER = 25
TARGET_DELTA = 1e-4


def load_ntc_songs(data_dir: Path, songlist_file: str = "songlist.txt"):
    """Load .ntc files from a directory."""
    songs = []
    songlist_path = data_dir / songlist_file
    if not songlist_path.exists():
        # Load all .ntc files
        names = [p.stem for p in sorted(data_dir.glob("*.ntc"))]
    else:
        names = [line.strip() for line in songlist_path.read_text().splitlines() if line.strip()]

    for name in names:
        filepath = data_dir / f"{name}.ntc"
        if not filepath.exists():
            continue
        song_steps = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if "[" not in line:
                    continue
                notes_str = line[line.find("[") + 1 : line.find("]")]
                notes = [int(n.strip()) for n in notes_str.split(",") if n.strip()]
                vec = torch.zeros(N_TONES)
                for n in notes:
                    vec[n % N_TONES] = 1.0
                song_steps.append(vec)
        if song_steps:
            songs.append(torch.stack(song_steps))
    return songs


def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"  Device: {device}")

    # Load both corpora
    synth_dir = Path("tymoczko_code/Code/First step/synth_data")
    bach_dir = Path("tymoczko_code/Code/First step/ntc_data")

    print("  Loading synthetic corpus...")
    synth_songs = load_ntc_songs(synth_dir)
    print(f"    Synthetic: {len(synth_songs)} songs")

    bach_songs = []
    if bach_dir.exists():
        print("  Loading Bach corpus...")
        bach_songs = load_ntc_songs(bach_dir)
        print(f"    Bach: {len(bach_songs)} songs")

    all_songs = synth_songs
    # Optionally blend with Bach for Western foundation:
    # all_songs = synth_songs + bach_songs
    all_songs = [s.to(device) for s in all_songs]
    print(f"  Total: {len(all_songs)} songs")

    # Initialize parameters
    # pnote[12, N_TYPES]: P(pitch class | chord type)
    pnote = torch.rand(N_TONES, N_TYPES, device=device) * 0.5 + 0.1

    # Seed with music-theoretic priors
    # Type 0: Major — strong root, M3, P5
    pnote[0, 0] = 0.95   # root
    pnote[4, 0] = 0.85   # major 3rd
    pnote[7, 0] = 0.90   # perfect 5th

    # Type 1: Minor — strong root, m3, P5
    pnote[0, 1] = 0.95
    pnote[3, 1] = 0.85
    pnote[7, 1] = 0.90

    # Type 2: Diminished — root, m3, tritone
    pnote[0, 2] = 0.90
    pnote[3, 2] = 0.85
    pnote[6, 2] = 0.80

    # Type 3: Augmented — root, M3, aug5
    pnote[0, 3] = 0.90
    pnote[4, 3] = 0.85
    pnote[8, 3] = 0.80

    # Type 4: sus2 — root, M2, P5
    pnote[0, 4] = 0.90
    pnote[2, 4] = 0.75
    pnote[7, 4] = 0.85

    # Type 5: sus4 — root, P4, P5
    pnote[0, 5] = 0.90
    pnote[5, 5] = 0.80
    pnote[7, 5] = 0.85

    # pchord[N_TYPES]: initial chord type probability
    # Major and Minor most common
    pchord = torch.ones(N_TYPES, device=device)
    pchord[0] = 2.0  # Major
    pchord[1] = 2.0  # Minor
    pchord[2] = 1.0  # Dim
    pchord[3] = 0.5  # Aug
    pchord[4] = 0.3  # sus2
    pchord[5] = 0.3  # sus4
    pchord /= pchord.sum()

    # pchange[N_TYPES, N_TONES, N_TYPES]: transition probabilities
    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)

    # Seed transitions with musical priors
    # Same-type transitions (common to stay in major or minor)
    for t in range(N_TYPES):
        pchange[t, 0, t] = 2.0  # same root, same type (repetition)
    # Major → V (interval 7) common
    pchange[0, 7, 0] = 2.0
    pchange[0, 5, 1] = 1.5  # Major → relative minor (interval 5)
    pchange[1, 7, 0] = 1.5  # Minor → relative major (interval 7)
    pchange[1, 3, 0] = 1.0  # Minor → major (interval 3)
    # Normalize
    for t1 in range(N_TYPES):
        for t2 in range(N_TYPES):
            s = pchange[t1, :, t2].sum()
            if s > 0:
                pchange[t1, :, t2] /= s

    # Baum-Welch training
    print(f"\n  Training: {N_TYPES} chord types, {MAX_ITER} max iterations")
    start_time = time.time()
    pbar_outer = tqdm(range(MAX_ITER), desc="BW Training")

    for iter_idx in pbar_outer:
        note_hist = torch.zeros_like(pnote)
        chord_hist = torch.zeros(N_TYPES, device=device)
        change_hist = torch.zeros_like(pchange)
        total_ll = 0.0

        eps = 1e-8
        log_pnote = torch.log(pnote + eps)
        log_not_pnote = torch.log(1.0 - pnote + eps)

        for song_vec in tqdm(all_songs, desc=f"  Iter {iter_idx+1}", leave=False):
            T = song_vec.shape[0]

            # 1. Emission probabilities [T, N_TONES, N_TYPES]
            psets_log = torch.zeros(T, N_TONES, N_TYPES, device=device)
            for r in range(N_TONES):
                heard = torch.roll(song_vec, shifts=-r, dims=1)
                not_heard = 1.0 - heard
                p_emit = heard @ log_pnote + not_heard @ log_not_pnote
                psets_log[:, r, :] = p_emit

            psets = torch.exp(psets_log)

            # 2. Forward pass
            alpha = torch.zeros(T, N_TONES, N_TYPES, device=device)
            alpha[0] = (pchord / N_TONES) * psets[0]
            norm = alpha[0].sum()
            alpha[0] /= (norm + eps)
            total_ll += torch.log(norm + eps)

            for t_step in range(1, T):
                prev = alpha[t_step - 1]
                combined_prev = torch.zeros(N_TONES, N_TYPES, device=device)
                for i in range(N_TONES):
                    prev_shifted = torch.roll(prev, shifts=i, dims=0)
                    combined_prev += prev_shifted @ pchange[:, i, :]

                alpha[t_step] = combined_prev * psets[t_step]
                norm = alpha[t_step].sum()
                alpha[t_step] /= (norm + eps)
                total_ll += torch.log(norm + eps)

            # 3. Backward pass
            beta = torch.zeros(T, N_TONES, N_TYPES, device=device)
            beta[T - 1] = 1.0
            for t_step in range(T - 2, -1, -1):
                next_val = psets[t_step + 1] * beta[t_step + 1]
                combined_next = torch.zeros(N_TONES, N_TYPES, device=device)
                for i in range(N_TONES):
                    next_shifted = torch.roll(next_val, shifts=-i, dims=0)
                    combined_next += next_shifted @ pchange[:, i, :].T
                beta[t_step] = combined_next
                beta[t_step] /= (beta[t_step].sum() + eps)

            # 4. Expectations
            gamma = alpha * beta
            gamma /= (gamma.sum(dim=(1, 2), keepdim=True) + eps)
            chord_hist += gamma.sum(dim=(0, 1))

            for r in range(N_TONES):
                heard = torch.roll(song_vec, shifts=-r, dims=1)
                note_hist += heard.T @ gamma[:, r, :]

            for t_step in range(T - 1):
                term_next = psets[t_step + 1] * beta[t_step + 1]
                for i in range(N_TONES):
                    term_prev = alpha[t_step]
                    next_shifted = torch.roll(term_next, shifts=-i, dims=0)
                    change_hist[:, i, :] += term_prev.T @ next_shifted

        # 5. M-step
        old_pnote = pnote.clone()
        pnote = note_hist / (chord_hist.view(1, N_TYPES) + eps)
        pnote = torch.clamp(pnote, 0.001, 0.999)

        # Keep root strong
        pnote[0, :] = torch.clamp(pnote[0, :], 0.5, 0.999)

        pchange = change_hist / (change_hist.sum(dim=(1, 2), keepdim=True) + eps)

        delta = torch.abs(pnote - old_pnote).max().item()
        pbar_outer.set_postfix({"Delta": f"{delta:.6f}", "LL": f"{total_ll:.1f}"})

        if delta < TARGET_DELTA:
            print(f"  Converged at iteration {iter_idx + 1}")
            break

    end_time = time.time()
    print(f"\n  Training finished in {end_time - start_time:.1f}s on {device}")

    # Save weights
    out_dir = Path("melodica/harmonize/weights")
    out_dir.mkdir(exist_ok=True, parents=True)

    np.savetxt(out_dir / "pnote_full.txt", pnote.cpu().numpy())
    np.save(out_dir / "pchange_full.npy", pchange.cpu().numpy())

    # Also save human-readable summary
    type_names = ["Major", "Minor", "Dim", "Aug", "sus2", "sus4"]
    print("\n  === CHORD NOTE EMISSIONS (pnote) ===")
    print(f"  {'PC':>4s}", end="")
    for tn in type_names:
        print(f"  {tn:>8s}", end="")
    print()
    for pc in range(N_TONES):
        print(f"  {pc:4d}", end="")
        for t in range(N_TYPES):
            print(f"  {pnote[pc, t].item():8.4f}", end="")
        print()

    print(f"\n  Saved weights to {out_dir}/")
    print(f"    pnote_full.txt  shape: ({N_TONES}, {N_TYPES})")
    print(f"    pchange_full.npy shape: ({N_TYPES}, {N_TONES}, {N_TYPES})")


if __name__ == "__main__":
    main()
