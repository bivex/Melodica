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
import argparse

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
    """Load .ntc/.ntc2 files and return as a list of tensors + per-song weights.

    Handles both formats:
      - **.ntc** (legacy): one bracket per line, the melody pitch classes.
        `1.0 [4, 7, 10]`
      - **.ntc2** (extended): two brackets — a leading chord bracket
        `[root type bass]` and a trailing melody bracket `[pc, pc, ...]`.
        `1.0 4/4 0 major [0 0 0] [4, 7]`

    The melody is ALWAYS in the LAST bracket of the line (rfind), so this
    loader reads both formats correctly. The chord/key/meter fields in .ntc2
    are currently ignored by the trainer but are preserved for future
    structured-field training. Legacy .ntc files have only one bracket, so
    last == first and behaviour is unchanged.
    """
    songs = []
    weights = []
    songlist_path = data_dir / songlist_file
    if not songlist_path.exists():
        names = [p.stem for p in sorted(data_dir.glob("*.ntc"))]
    else:
        names = [line.strip() for line in songlist_path.read_text().splitlines() if line.strip()]

    for i, name in enumerate(names):
        # Try .ntc2 first, fall back to .ntc for legacy corpora
        filepath = data_dir / f"{name}.ntc2"
        if not filepath.exists():
            filepath = data_dir / f"{name}.ntc"
        if not filepath.exists():
            continue
        song_steps = []
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if "[" not in line:
                    continue
                # Melody is the LAST bracket (works for both .ntc and .ntc2).
                # Legacy loader used find() which grabbed the FIRST bracket —
                # correct for .ntc (one bracket) but wrong for .ntc2 (chord
                # bracket comes first).
                last_open = line.rfind("[")
                last_close = line.rfind("]")
                notes_str = line[last_open + 1 : last_close]
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
    parser = argparse.ArgumentParser(description="Turbo HMM Training with Optimized Hyperparameters.")
    parser.add_argument(
        "--corpus",
        choices=["synth", "theorytab", "t5harmony"],
        default="synth",
        help="Predefined corpus to train on (synth, theorytab, t5harmony)"
    )
    parser.add_argument(
        "--corpus-dir",
        type=str,
        default=None,
        help="Custom path to the corpus directory (overrides --corpus)"
    )
    parser.add_argument(
        "--max-iter",
        type=int,
        default=MAX_ITER,
        help=f"Maximum training iterations (default: {MAX_ITER})"
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=PATIENCE,
        help=f"Patience for early stopping (default: {PATIENCE})"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="melodica/harmonize/weights",
        help="Output directory for weights (default: melodica/harmonize/weights)"
    )
    parser.add_argument(
        "--suffix",
        type=str,
        default="_full",
        help="Suffix for output weight files (e.g. _full -> pnote_full.txt, default: _full)"
    )
    parser.add_argument(
        "--batch-budget",
        type=int,
        default=50000,
        help="Batch budget (total steps B * max_t) to prevent OOM (default: 50000)"
    )
    args = parser.parse_args()

    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"  Device: {device}")

    # Determine corpus directory
    if args.corpus_dir:
        corpus_dir = Path(args.corpus_dir)
    elif args.corpus == "synth":
        corpus_dir = Path("tymoczko_code/Code/First step/synth_data")
        if not corpus_dir.exists():
            corpus_dir = Path("/Volumes/External/Code/Melodica/tymoczko_code/Code/First step/synth_data")
    elif args.corpus == "theorytab":
        corpus_dir = Path("melodica/harmonize/corpus_theorytab")
    elif args.corpus == "t5harmony":
        corpus_dir = Path("melodica/harmonize/corpus_t5harmony")
    else:
        raise ValueError(f"Unknown corpus: {args.corpus}")

    print(f"  Loading corpus from {corpus_dir}...")
    raw_songs, raw_weights = load_ntc_songs(corpus_dir)
    print(f"    Loaded {len(raw_songs)} songs")

    # Sort songs by length to minimize padding within batches
    raw_songs = sorted(raw_songs, key=lambda s: s.shape[0])
    max_t = max(s.shape[0] for s in raw_songs)
    n_songs = len(raw_songs)

    # Plan batches dynamically based on memory budget
    batches = []
    current_batch = []
    current_max_len = 0
    for s in raw_songs:
        s_len = s.shape[0]
        candidate_max = max(current_max_len, s_len)
        candidate_count = len(current_batch) + 1
        if candidate_count * candidate_max <= args.batch_budget:
            current_batch.append(s)
            current_max_len = candidate_max
        else:
            if current_batch:
                batches.append(current_batch)
            current_batch = [s]
            current_max_len = s_len
    if current_batch:
        batches.append(current_batch)

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

    print(f"\n  Turbo Training: {n_songs} songs, {max_t} max steps, {args.max_iter} iters, planned {len(batches)} batches (budget={args.batch_budget})")
    start_time = time.time()
    eps = 1e-8

    best_ll = -float("inf")
    best_pnote = pnote.clone()
    best_pchange = pchange.clone()
    stagnation = 0

    pbar = tqdm(range(args.max_iter), desc="Training")
    for iter_idx in pbar:
        # Accumulators for expected statistics
        chord_hist_total = torch.zeros(N_TYPES, device=device)
        note_hist_total = torch.zeros(N_TONES, N_TYPES, device=device)
        change_hist_total = torch.zeros(N_TYPES, N_TONES, N_TYPES, device=device)
        total_ll = 0.0

        # Loop over batches
        for batch_songs in batches:
            n_songs_batch = len(batch_songs)
            max_t_batch = max(s.shape[0] for s in batch_songs)

            # Build batch tensors
            songs_batched = torch.zeros(n_songs_batch, max_t_batch, N_TONES, device=device)
            mask = torch.zeros(n_songs_batch, max_t_batch, device=device)
            lengths_batch = []
            for i, s in enumerate(batch_songs):
                t = s.shape[0]
                songs_batched[i, :t, :] = s.to(device)
                mask[i, :t] = 1.0
                lengths_batch.append(t)

            # E-step
            log_pnote = torch.log(pnote + eps)
            log_not_pnote = torch.log(1.0 - pnote + eps)
            songs_expanded = songs_batched[:, :, shifts]
            diff = log_pnote - log_not_pnote
            psets_log = torch.einsum("ntrp,pk->ntrk", songs_expanded, diff) + log_not_pnote.sum(dim=0)
            psets = torch.exp(psets_log) * mask.view(n_songs_batch, max_t_batch, 1, 1)

            alpha = torch.zeros(n_songs_batch, max_t_batch, N_TONES, N_TYPES, device=device)
            alpha[:, 0] = (pchord / N_TONES) * psets[:, 0]
            norm = alpha[:, 0].sum(dim=(1, 2), keepdim=True)
            alpha[:, 0] /= norm + eps
            batch_ll = torch.log(norm + eps).sum()

            for t in range(1, max_t_batch):
                prev_expanded = alpha[:, t - 1][:, r_prev_indices]
                combined_prev = torch.einsum("nrik,kio->nro", prev_expanded, pchange)
                alpha[:, t] = combined_prev * psets[:, t]
                norm = alpha[:, t].sum(dim=(1, 2), keepdim=True)
                alpha[:, t] /= norm + eps
                batch_ll += (torch.log(norm + eps) * mask[:, t].view(-1, 1, 1)).sum()

            total_ll += batch_ll.item()

            beta = torch.zeros(n_songs_batch, max_t_batch, N_TONES, N_TYPES, device=device)
            for i, length in enumerate(lengths_batch):
                beta[i, length - 1] = 1.0
            for t in range(max_t_batch - 2, -1, -1):
                next_val = psets[:, t + 1] * beta[:, t + 1]
                next_expanded = next_val[:, r_next_indices_for_beta]
                combined_next = torch.einsum("nrio,kio->nrk", next_expanded, pchange)
                active = torch.tensor([t < l - 1 for l in lengths_batch], dtype=torch.float32, device=device).view(-1, 1, 1)
                beta[:, t] = combined_next * active + beta[:, t] * (1 - active)
                norm = beta[:, t].sum(dim=(1, 2), keepdim=True)
                beta[:, t] /= norm + eps

            gamma = alpha * beta
            gamma /= gamma.sum(dim=(2, 3), keepdim=True) + eps
            gamma *= mask.view(n_songs_batch, max_t_batch, 1, 1)

            chord_hist = gamma.sum(dim=(0, 1, 2))
            note_hist = torch.einsum("ntrp,ntrk->pk", songs_expanded, gamma)

            # Transition expected counts (xi) via the Rabiner (1989) identity.
            term_next = psets[:, 1:] * beta[:, 1:]
            term_prev_expanded = alpha[:, :-1][:, :, r_prev_indices]
            raw_xi = torch.einsum("ntrik,kio->ntro", term_prev_expanded, pchange)
            xi_norm = raw_xi / (raw_xi.sum(dim=-1, keepdim=True) + eps)
            gamma_prev_expanded = gamma[:, :-1][:, :, r_prev_indices]
            change_hist = torch.einsum("ntrik,ntro->kio", gamma_prev_expanded, xi_norm)

            # Accumulate statistics
            chord_hist_total += chord_hist
            note_hist_total += note_hist
            change_hist_total += change_hist

        # M-step
        old_pnote = pnote.clone()
        pnote = note_hist_total / (chord_hist_total.view(1, N_TYPES) + eps)
        pnote = torch.clamp(pnote, 0.001, 0.999)

        uniform_prior = torch.ones_like(change_hist_total) / (N_TONES * N_TYPES)
        pchange = (change_hist_total + PRIOR_STRENGTH * uniform_prior) / \
                  (change_hist_total + PRIOR_STRENGTH * uniform_prior).sum(dim=(1, 2), keepdim=True)

        for t in range(N_TYPES):
            if pchange[t, 0, t] > MAX_SELF_LOOP:
                excess = pchange[t, 0, t] - MAX_SELF_LOOP
                pchange[t, 0, t] = MAX_SELF_LOOP
                others = pchange[t].sum() - pchange[t, 0, t]
                if others > eps:
                    pchange[t] *= (1.0 + excess / others)
                    pchange[t, 0, t] = MAX_SELF_LOOP
        pchange /= pchange.sum(dim=(1, 2), keepdim=True)

        if total_ll > best_ll + MIN_LL_DELTA:
            best_ll = total_ll
            best_pnote = pnote.clone()
            best_pchange = pchange.clone()
            stagnation = 0
        else:
            stagnation += 1

        delta = torch.abs(pnote - old_pnote).max().item()
        pbar.set_postfix({"LL": f"{total_ll:.1f}", "Best": f"{best_ll:.1f}"})

        if delta < TARGET_DELTA and iter_idx > 50:
            break
        if stagnation >= args.patience:
            break

    # Save to Melodica format
    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True, parents=True)
    
    # Save as text files for the engine
    np.savetxt(out_dir / f"pnote{args.suffix}.txt", best_pnote.cpu().numpy())
    
    # pchange is 3D, we save it as flattened 2D for txt or just as .npy (preferred by engine)
    # But if you need .txt, we'll flatten it:
    pchange_np = best_pchange.cpu().numpy()
    np.savetxt(out_dir / f"pchange{args.suffix}.txt", pchange_np.reshape(-1, N_TYPES))
    np.save(out_dir / f"pchange{args.suffix}.npy", pchange_np)
    
    print(f"\n  Final weights saved to {out_dir.absolute()}")

if __name__ == "__main__":
    main()
