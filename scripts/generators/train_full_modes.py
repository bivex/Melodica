# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/train_full_modes.py — Turbo HMM Training with Optimized Hyperparameters.
Full batching, no Python loops in core BW, maximized MPS utilization.
"""

import torch
import numpy as np
from pathlib import Path
import time
from tqdm import tqdm
import os

N_TONES = 12
N_TYPES = 12  # Cinematic Expanded (Maj, Min, Dim, Aug, sus2, sus4, Maj7, Min7, Dom7, Maj9, Min9, Add9)
MAX_ITER = 2000
TARGET_DELTA = 1e-5
PATIENCE = 300
MIN_LL_DELTA = 1.0

# --- BEST PARAMETERS FROM AUTORESEARCH ---
ON_PROB = 0.90
PRIOR_STRENGTH = 0.50
MAX_SELF_LOOP = 0.20
# -----------------------------------------

def load_ntc_songs(data_dir: Path, songlist_file: str = "songlist.txt"):
    """Load .ntc files and return as a list of tensors + per-song weights."""
    songs = []
    weights = []
    songlist_path = data_dir / songlist_file
    if not songlist_path.exists():
        names = [p.stem for p in sorted(data_dir.glob("*.ntc"))]
    else:
        names = [line.strip() for line in songlist_path.read_text().splitlines() if line.strip()]

    for i, name in enumerate(names):
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
            weights.append(1.0) # Equal weight for full training

    return songs, weights

def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"  Device: {device}")

    # Load corpora
    synth_dir = Path("tymoczko_code/Code/First step/synth_data")
    if not synth_dir.exists():
        synth_dir = Path("/Volumes/External/Code/Melodica/tymoczko_code/Code/First step/synth_data")
        
    print("  Loading synthetic corpus...")
    raw_songs, raw_weights = load_ntc_songs(synth_dir)
    print(f"    Loaded {len(raw_songs)} songs")

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

    # Pre-calculate indices
    shifts = (torch.arange(N_TONES, device=device).view(1, N_TONES) + torch.arange(N_TONES, device=device).view(N_TONES, 1)) % N_TONES
    r_next_indices = torch.arange(N_TONES, device=device).view(N_TONES, 1)
    interval_indices = torch.arange(N_TONES, device=device).view(1, N_TONES)
    r_prev_indices = (r_next_indices - interval_indices) % N_TONES
    r_next_indices_for_beta = (r_next_indices + interval_indices) % N_TONES

    # Initialize
    CHORD_NOTES = {
        0: {0, 4, 7}, 1: {0, 3, 7}, 2: {0, 3, 6}, 3: {0, 4, 8},
        4: {0, 2, 7}, 5: {0, 5, 7}, 6: {0, 4, 7, 11}, 7: {0, 3, 7, 10},
        8: {0, 4, 7, 10}, 9: {0, 4, 7, 11, 2}, 10: {0, 3, 7, 10, 2}, 11: {0, 4, 7, 2},
    }

    pnote = torch.full((N_TONES, N_TYPES), 0.12, device=device)
    for t_idx, notes in CHORD_NOTES.items():
        for n in notes:
            pnote[n, t_idx] = ON_PROB

    pchord = torch.ones(N_TYPES, device=device) / N_TYPES
    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)
    for t in range(N_TYPES):
        pchange[t, 0, t] = 2.0
    pchange /= pchange.sum(dim=(1, 2), keepdim=True)

    print(f"\n  Turbo Training: {n_songs} songs, {max_t} max steps, {MAX_ITER} iters")
    start_time = time.time()
    eps = 1e-8

    best_ll = -float("inf")
    best_pnote = pnote.clone()
    best_pchange = pchange.clone()
    stagnation = 0

    pbar = tqdm(range(MAX_ITER), desc="Training")
    for iter_idx in pbar:
        # E-step
        log_pnote = torch.log(pnote + eps)
        log_not_pnote = torch.log(1.0 - pnote + eps)
        songs_expanded = songs_batched[:, :, shifts]
        diff = log_pnote - log_not_pnote
        psets_log = torch.einsum("ntrp,pk->ntrk", songs_expanded, diff) + log_not_pnote.sum(dim=0)
        psets = torch.exp(psets_log) * mask.view(n_songs, max_t, 1, 1)

        alpha = torch.zeros(n_songs, max_t, N_TONES, N_TYPES, device=device)
        alpha[:, 0] = (pchord / N_TONES) * psets[:, 0]
        norm = alpha[:, 0].sum(dim=(1, 2), keepdim=True)
        alpha[:, 0] /= norm + eps
        total_ll = torch.log(norm + eps).sum()

        for t in range(1, max_t):
            prev_expanded = alpha[:, t - 1][:, r_prev_indices]
            combined_prev = torch.einsum("nrik,kio->nro", prev_expanded, pchange)
            alpha[:, t] = combined_prev * psets[:, t]
            norm = alpha[:, t].sum(dim=(1, 2), keepdim=True)
            alpha[:, t] /= norm + eps
            total_ll += (torch.log(norm + eps) * mask[:, t].view(-1, 1, 1)).sum()

        beta = torch.zeros(n_songs, max_t, N_TONES, N_TYPES, device=device)
        for i, length in enumerate(lengths):
            beta[i, length - 1] = 1.0
        for t in range(max_t - 2, -1, -1):
            next_val = psets[:, t + 1] * beta[:, t + 1]
            next_expanded = next_val[:, r_next_indices_for_beta]
            combined_next = torch.einsum("nrio,kio->nrk", next_expanded, pchange)
            active = torch.tensor([t < l - 1 for l in lengths], dtype=torch.float32, device=device).view(-1, 1, 1)
            beta[:, t] = combined_next * active + beta[:, t] * (1 - active)
            norm = beta[:, t].sum(dim=(1, 2), keepdim=True)
            beta[:, t] /= norm + eps

        gamma = alpha * beta
        gamma /= gamma.sum(dim=(2, 3), keepdim=True) + eps
        gamma *= mask.view(n_songs, max_t, 1, 1)

        chord_hist = gamma.sum(dim=(0, 1, 2))
        note_hist = torch.einsum("ntrp,ntrk->pk", songs_expanded, gamma)
        term_next = psets[:, 1:] * beta[:, 1:]
        term_prev_expanded = alpha[:, :-1][:, :, r_prev_indices]
        change_hist = torch.einsum("ntrik,kio,ntro->kio", term_prev_expanded, pchange, term_next)

        # M-step
        old_pnote = pnote.clone()
        pnote = note_hist / (chord_hist.view(1, N_TYPES) + eps)
        pnote = torch.clamp(pnote, 0.001, 0.999)

        uniform_prior = torch.ones_like(change_hist) / (N_TONES * N_TYPES)
        pchange = (change_hist + PRIOR_STRENGTH * uniform_prior) / \
                  (change_hist + PRIOR_STRENGTH * uniform_prior).sum(dim=(1, 2), keepdim=True)

        for t in range(N_TYPES):
            if pchange[t, 0, t] > MAX_SELF_LOOP:
                excess = pchange[t, 0, t] - MAX_SELF_LOOP
                pchange[t, 0, t] = MAX_SELF_LOOP
                others = pchange[t].sum() - pchange[t, 0, t]
                if others > eps:
                    pchange[t] *= (1.0 + excess / others)
                    pchange[t, 0, t] = MAX_SELF_LOOP
        pchange /= pchange.sum(dim=(1, 2), keepdim=True)

        if total_ll.item() > best_ll + MIN_LL_DELTA:
            best_ll = total_ll.item()
            best_pnote = pnote.clone()
            best_pchange = pchange.clone()
            stagnation = 0
        else:
            stagnation += 1

        delta = torch.abs(pnote - old_pnote).max().item()
        pbar.set_postfix({"LL": f"{total_ll:.1f}", "Best": f"{best_ll:.1f}"})

        if delta < TARGET_DELTA and iter_idx > 50:
            break
        if stagnation >= PATIENCE:
            break

    # Save to Melodica format
    out_dir = Path("melodica/harmonize/weights")
    out_dir.mkdir(exist_ok=True, parents=True)
    
    # Save as text files for the engine
    np.savetxt(out_dir / "pnote_full.txt", best_pnote.cpu().numpy())
    
    # pchange is 3D, we save it as flattened 2D for txt or just as .npy (preferred by engine)
    # But if you need .txt, we'll flatten it:
    pchange_np = best_pchange.cpu().numpy()
    np.savetxt(out_dir / "pchange_full.txt", pchange_np.reshape(-1, N_TYPES))
    np.save(out_dir / "pchange_full.npy", pchange_np)
    
    print(f"\n  Final weights saved to {out_dir.absolute()}")

if __name__ == "__main__":
    main()
