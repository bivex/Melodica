# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/train_full_modes.py — Train Coupled HMM on synthetic corpus (all 78 modes).
Uses Metal GPU acceleration via PyTorch.
Vectorized Baum-Welch to maximize MPS throughput.
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
    all_songs = [s.to(device) for s in all_songs]
    print(f"  Total: {len(all_songs)} songs")

    # Initialize parameters
    pnote = torch.rand(N_TONES, N_TYPES, device=device) * 0.5 + 0.1

    # Seed with music-theoretic priors
    pnote[0, 0] = 0.95   # root
    pnote[4, 0] = 0.85   # major 3rd
    pnote[7, 0] = 0.90   # perfect 5th

    pnote[0, 1] = 0.95
    pnote[3, 1] = 0.85
    pnote[7, 1] = 0.90

    pnote[0, 2] = 0.90
    pnote[3, 2] = 0.85
    pnote[6, 2] = 0.80

    pnote[0, 3] = 0.90
    pnote[4, 3] = 0.85
    pnote[8, 3] = 0.80

    pnote[0, 4] = 0.90
    pnote[2, 4] = 0.75
    pnote[7, 4] = 0.85

    pnote[0, 5] = 0.90
    pnote[5, 5] = 0.80
    pnote[7, 5] = 0.85

    pchord = torch.ones(N_TYPES, device=device)
    pchord[0] = 2.0  # Major
    pchord[1] = 2.0  # Minor
    pchord[2] = 1.0  # Dim
    pchord[3] = 0.5  # Aug
    pchord[4] = 0.3  # sus2
    pchord[5] = 0.3  # sus4
    pchord /= pchord.sum()

    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)

    # Seed transitions
    for t in range(N_TYPES):
        pchange[t, 0, t] = 2.0
    pchange[0, 7, 0] = 2.0
    pchange[0, 5, 1] = 1.5
    pchange[1, 7, 0] = 1.5
    pchange[1, 3, 0] = 1.0
    pchange /= pchange.sum(dim=(1, 2), keepdim=True)

    # Pre-calculate index tensors for vectorization
    # r_idx[r_next, interval] = r_prev = (r_next - interval) % 12
    r_next_indices = torch.arange(N_TONES, device=device).view(N_TONES, 1)
    interval_indices = torch.arange(N_TONES, device=device).view(1, N_TONES)
    r_prev_indices = (r_next_indices - interval_indices) % N_TONES

    # Baum-Welch training
    print(f"\n  Training: {N_TYPES} chord types, {MAX_ITER} max iterations")
    start_time = time.time()
    pbar_outer = tqdm(range(MAX_ITER), desc="BW Training")

    eps = 1e-8

    for iter_idx in pbar_outer:
        note_hist = torch.zeros_like(pnote)
        chord_hist = torch.zeros(N_TYPES, device=device)
        change_hist = torch.zeros_like(pchange)
        total_ll = 0.0

        log_pnote = torch.log(pnote + eps)
        log_not_pnote = torch.log(1.0 - pnote + eps)

        for song_vec in tqdm(all_songs, desc=f"  Iter {iter_idx+1}", leave=False):
            T = song_vec.shape[0]

            # 1. Emission probabilities [T, N_TONES, N_TYPES]
            # Vectorized over R: instead of 12 loops, we shift pnote
            # heard_p[T, 12, 12] where heard_p[t, r, p] = song_vec[t, (p+r)%12]
            # Actually simpler:
            psets_log = torch.zeros(T, N_TONES, N_TYPES, device=device)
            for r in range(N_TONES):
                # This roll is still a bit slow, but it's only 12 times per song
                # and much faster than the inner loops.
                heard = torch.roll(song_vec, shifts=-r, dims=1)
                p_emit = heard @ log_pnote + (1.0 - heard) @ log_not_pnote
                psets_log[:, r, :] = p_emit
            psets = torch.exp(psets_log)

            # 2. Forward pass
            alpha = torch.zeros(T, N_TONES, N_TYPES, device=device)
            alpha[0] = (pchord / N_TONES) * psets[0]
            norm = alpha[0].sum()
            alpha[0] /= (norm + eps)
            total_ll += torch.log(norm + eps)

            for t_step in range(1, T):
                # combined_prev[r_n, t_n] = sum_{i, t_p} alpha[t-1, (r_n - i)%12, t_p] * pchange[t_p, i, t_n]
                prev = alpha[t_step - 1] # [12, N_TYPES]
                # Use indexing to get [12, 12, N_TYPES] where [r_n, i, t_p]
                prev_expanded = prev[r_prev_indices] # [12, 12, N_TYPES]
                # prev_expanded: [r_next, interval, t_prev]
                # pchange: [t_prev, interval, t_next]
                combined_prev = torch.einsum('rit,tir->rt', prev_expanded, pchange)
                
                alpha[t_step] = combined_prev * psets[t_step]
                norm = alpha[t_step].sum()
                alpha[t_step] /= (norm + eps)
                total_ll += torch.log(norm + eps)

            # 3. Backward pass
            beta = torch.zeros(T, N_TONES, N_TYPES, device=device)
            beta[T - 1] = 1.0
            for t_step in range(T - 2, -1, -1):
                # combined_next[r_p, t_p] = sum_{i, t_n} (psets*beta)[t+1, (r_p + i)%12, t_n] * pchange[t_p, i, t_n]
                next_val = psets[t_step + 1] * beta[t_step + 1] # [12, N_TYPES]
                
                # r_next = (r_prev + interval) % 12
                # r_p_indices[r_prev, interval]
                r_p_indices = (r_next_indices + interval_indices) % N_TONES
                next_expanded = next_val[r_p_indices] # [r_p, i, t_n]
                
                combined_next = torch.einsum('rit,tit->rt', next_expanded, pchange)
                beta[t_step] = combined_next
                beta[t_step] /= (beta[t_step].sum() + eps)

            # 4. Expectations
            gamma = alpha * beta
            gamma /= (gamma.sum(dim=(1, 2), keepdim=True) + eps)
            chord_hist += gamma.sum(dim=(0, 1))

            # note_hist calculation (Vectorized)
            # note_hist[p, t] += sum_{t_step, r} song_vec[t_step, (p+r)%12] * gamma[t_step, r, t]
            # This can be seen as a sum over t_step of (song_vec_shifted.T @ gamma_at_t_step)
            for r in range(N_TONES):
                heard = torch.roll(song_vec, shifts=-r, dims=1)
                note_hist += heard.T @ gamma[:, r, :]

            # change_hist calculation (Vectorized)
            # change_hist[t_p, i, t_n] += sum_{t_step, r_n} alpha[t_step, (r_n-i)%12, t_p] * (psets*beta)[t_step+1, r_n, t_n]
            term_next = psets[1:] * beta[1:] # [T-1, 12, N_TYPES]
            term_prev = alpha[:-1] # [T-1, 12, N_TYPES]
            
            # We want change_hist[t_p, i, t_n]
            # term_prev_expanded: [T-1, r_n, i, t_p]
            term_prev_expanded = term_prev[:, r_prev_indices] # [T-1, 12, 12, N_TYPES]
            # einsum: sum over T-1 and r_n
            change_hist += torch.einsum('trip,trn->pin', term_prev_expanded, term_next)

        # 5. M-step
        old_pnote = pnote.clone()
        pnote = note_hist / (chord_hist.view(1, N_TYPES) + eps)
        pnote = torch.clamp(pnote, 0.001, 0.999)
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

    # Summary display (optional)
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


if __name__ == "__main__":
    main()
