# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/train_full_modes.py — Turbo HMM Training.
Full batching, no Python loops in core BW, maximized MPS utilization.
"""

import torch
import numpy as np
from pathlib import Path
import time
from tqdm import tqdm


N_TONES = 12
N_TYPES = 6  # Expanded from 3
MAX_ITER = 100
TARGET_DELTA = 1e-5


def load_ntc_songs(data_dir: Path, songlist_file: str = "songlist.txt"):
    """Load .ntc files and return as a list of tensors."""
    songs = []
    songlist_path = data_dir / songlist_file
    if not songlist_path.exists():
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

    # Load corpora
    synth_dir = Path("tymoczko_code/Code/First step/synth_data")
    print("  Loading synthetic corpus...")
    raw_songs = load_ntc_songs(synth_dir)
    print(f"    Loaded {len(raw_songs)} songs")

    # Batching: Pad to max length
    max_t = max(s.shape[0] for s in raw_songs)
    n_songs = len(raw_songs)

    songs_batched = torch.zeros(n_songs, max_t, N_TONES, device=device)
    mask = torch.zeros(n_songs, max_t, device=device)
    lengths = []

    for i, s in enumerate(raw_songs):
        t = s.shape[0]
        songs_batched[i, :t, :] = s.to(device)
        mask[i, :t] = 1.0
        lengths.append(t)

    # Pre-calculate circulant indices
    # shifts[r, p] = (p + r) % 12
    shifts = (
        torch.arange(N_TONES, device=device).view(1, N_TONES)
        + torch.arange(N_TONES, device=device).view(N_TONES, 1)
    ) % N_TONES

    # r_prev_indices[r_next, interval] = (r_next - interval) % 12
    r_next_indices = torch.arange(N_TONES, device=device).view(N_TONES, 1)
    interval_indices = torch.arange(N_TONES, device=device).view(1, N_TONES)
    r_prev_indices = (r_next_indices - interval_indices) % N_TONES

    # r_next_indices_for_beta[r_prev, interval] = (r_prev + interval) % 12
    r_next_indices_for_beta = (r_next_indices + interval_indices) % N_TONES

    # Initialize parameters
    pnote = torch.rand(N_TONES, N_TYPES, device=device) * 0.5 + 0.1
    pnote[0, 0], pnote[4, 0], pnote[7, 0] = 0.95, 0.85, 0.90  # Major
    pnote[0, 1], pnote[3, 1], pnote[7, 1] = 0.95, 0.85, 0.90  # Minor
    pnote[0, 2], pnote[3, 2], pnote[6, 2] = 0.90, 0.85, 0.80  # Dim
    pnote[0, 3], pnote[4, 3], pnote[8, 3] = 0.90, 0.85, 0.80  # Aug
    pnote[0, 4], pnote[2, 4], pnote[7, 4] = 0.90, 0.75, 0.85  # sus2
    pnote[0, 5], pnote[5, 5], pnote[7, 5] = 0.90, 0.80, 0.85  # sus4

    pchord = torch.tensor([2.0, 2.0, 1.0, 0.5, 0.3, 0.3], device=device)
    pchord /= pchord.sum()

    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)
    for t in range(N_TYPES):
        pchange[t, 0, t] = 2.0
    pchange[0, 7, 0], pchange[0, 5, 1], pchange[1, 7, 0], pchange[1, 3, 0] = 2.0, 1.5, 1.5, 1.0
    pchange /= pchange.sum(dim=(1, 2), keepdim=True)

    print(f"\n  Turbo Training: {n_songs} songs, {max_t} max steps, {MAX_ITER} iters")
    start_time = time.time()
    eps = 1e-8

    pbar = tqdm(range(MAX_ITER), desc="Training")
    for iter_idx in pbar:
        # 1. Emission probabilities [N, T, 12, 6]
        log_pnote = torch.log(pnote + eps)
        log_not_pnote = torch.log(1.0 - pnote + eps)

        # songs_expanded[n, t, r, p] = songs[n, t, (p+r)%12]
        songs_expanded = songs_batched[:, :, shifts]

        # log_emit[n, t, r, k] = sum_p songs_exp[n, t, r, p] * (log_p - log_not_p) + sum log_not_p
        diff = log_pnote - log_not_pnote
        psets_log = torch.einsum("ntrp,pk->ntrk", songs_expanded, diff) + log_not_pnote.sum(dim=0)
        psets = torch.exp(psets_log) * mask.view(n_songs, max_t, 1, 1)

        # 2. Forward pass
        alpha = torch.zeros(n_songs, max_t, N_TONES, N_TYPES, device=device)
        alpha[:, 0] = (pchord / N_TONES) * psets[:, 0]
        norm = alpha[:, 0].sum(dim=(1, 2), keepdim=True)
        alpha[:, 0] /= norm + eps
        total_ll = torch.log(norm + eps).sum()

        for t in range(1, max_t):
            prev = alpha[:, t - 1]  # [N, 12, K]
            prev_expanded = prev[:, r_prev_indices]  # [N, 12, 12, K] -> [N, r_n, i, t_p]
            combined_prev = torch.einsum("nrik,kio->nro", prev_expanded, pchange)

            alpha[:, t] = combined_prev * psets[:, t]
            norm = alpha[:, t].sum(dim=(1, 2), keepdim=True)
            # Only normalize where mask is 1
            alpha[:, t] /= norm + eps
            total_ll += (torch.log(norm + eps) * mask[:, t].view(-1, 1, 1)).sum()

        # 3. Backward pass
        beta = torch.zeros(n_songs, max_t, N_TONES, N_TYPES, device=device)
        beta[:, -1] = 1.0  # Will be masked anyway
        # Initialize at last actual step for each song
        for i, length in enumerate(lengths):
            beta[i, length - 1] = 1.0

        for t in range(max_t - 2, -1, -1):
            next_val = psets[:, t + 1] * beta[:, t + 1]  # [N, 12, K]
            next_expanded = next_val[:, r_next_indices_for_beta]  # [N, r_p, i, t_n]
            combined_next = torch.einsum("nrio,kio->nrk", next_expanded, pchange)
            beta[:, t] = combined_next
            norm = beta[:, t].sum(dim=(1, 2), keepdim=True)
            beta[:, t] /= norm + eps

        # 4. Expectations
        gamma = alpha * beta
        gamma /= gamma.sum(dim=(2, 3), keepdim=True) + eps
        gamma *= mask.view(n_songs, max_t, 1, 1)

        chord_hist = gamma.sum(dim=(0, 1, 2))
        note_hist = torch.einsum("ntrp,ntrk->pk", songs_expanded, gamma)

        # change_hist[t_p, i, t_n]
        term_next = psets[:, 1:] * beta[:, 1:]  # [N, T-1, 12, K]
        term_prev_expanded = alpha[:, :-1][:, :, r_prev_indices]  # [N, T-1, 12, 12, K]
        change_hist = torch.einsum("ntrik,ntro->kio", term_prev_expanded, term_next)

        # 5. M-step
        old_pnote = pnote.clone()
        pnote = note_hist / (chord_hist.view(1, N_TYPES) + eps)
        pnote = torch.clamp(pnote, 0.001, 0.999)
        pnote[0, :] = torch.clamp(pnote[0, :], 0.5, 0.999)
        pchange = change_hist / (change_hist.sum(dim=(1, 2), keepdim=True) + eps)

        delta = torch.abs(pnote - old_pnote).max().item()
        pbar.set_postfix({"Delta": f"{delta:.6f}", "LL": f"{total_ll:.1f}"})
        if delta < TARGET_DELTA:
            break

    print(f"\n  Turbo training finished in {time.time() - start_time:.1f}s")

    out_dir = Path("melodica/harmonize/weights")
    out_dir.mkdir(exist_ok=True, parents=True)
    np.savetxt(out_dir / "pnote_full.txt", pnote.cpu().numpy())
    np.save(out_dir / "pchange_full.npy", pchange.cpu().numpy())


if __name__ == "__main__":
    main()
