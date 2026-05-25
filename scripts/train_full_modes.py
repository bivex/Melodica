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
N_TYPES = 12  # Cinematic Expanded (Maj, Min, Dim, Aug, sus2, sus4, Maj7, Min7, Dom7, Maj9, Min9, Add9)
MAX_ITER = 2000
TARGET_DELTA = 1e-5
PATIENCE = 100
MIN_LL_DELTA = 1.0


def load_ntc_songs(data_dir: Path, songlist_file: str = "songlist.txt"):
    """Load .ntc files and return as a list of tensors + per-song weights."""
    songs = []
    weights = []
    songlist_path = data_dir / songlist_file
    if not songlist_path.exists():
        names = [p.stem for p in sorted(data_dir.glob("*.ntc"))]
    else:
        names = [line.strip() for line in songlist_path.read_text().splitlines() if line.strip()]

    # Load per-song weights if available (genre-weighted corpus)
    weights_path = data_dir / "song_weights.txt"
    raw_weights = None
    if weights_path.exists():
        raw_weights = [float(w) for w in weights_path.read_text().splitlines() if w.strip()]

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
            w = raw_weights[i] if raw_weights and i < len(raw_weights) else 1.0
            # Invert: more songs for a mode → each song gets lower weight
            # This way Common modes still dominate but don't overwhelm
            weights.append(1.0 / max(w, 1e-3))

    return songs, weights


TYPE_NAMES = ["Maj", "Min", "Dim", "Aug", "sus2", "sus4",
              "Maj7", "Min7", "Dom7", "Maj9", "Min9", "Add9"]


def run_sanity_check(pnote, pchange, pchord):
    """Validate trained weights before use."""
    pn = pnote.cpu().numpy() if isinstance(pnote, torch.Tensor) else pnote
    pc = pchange.cpu().numpy() if isinstance(pchange, torch.Tensor) else pchange
    pch = pchord.cpu().numpy() if isinstance(pchord, torch.Tensor) else pchord

    checks = {}
    checks["pnote_finite"] = np.all(np.isfinite(pn))
    checks["pchange_finite"] = np.all(np.isfinite(pc))

    # Aug not dominant
    aug_idx = 3
    pchange_marginal = pc.sum(axis=(1, 2))
    total = pchange_marginal.sum()
    if total > 0 and np.isfinite(total):
        pchange_marginal = pchange_marginal / total
    else:
        pchange_marginal = np.ones(N_TYPES) / N_TYPES
        print("    [WARN] pchange marginal is NaN/zero, using uniform")
    checks["aug_not_dominant"] = pchange_marginal[aug_idx] <= 0.15

    # Dom7 -> Min strong at P4
    dom7_to_min_p4 = pc[8, 5, 1]
    checks["dom7_to_min_strong"] = dom7_to_min_p4 > 0.3

    # Maj -> Maj at P4/P5 (V-I / I-V) meaningful
    maj_v_i_meaningful = pc[0, 5, 0] > 0.01 or pc[0, 7, 0] > 0.01
    checks["maj_v_i_meaningful"] = maj_v_i_meaningful

    all_ok = True
    print("\n  === Sanity Check ===")
    for k, v in checks.items():
        status = "OK" if v else "FAIL"
        if not v:
            all_ok = False
        print(f"    [{status}] {k}")

    # Print chord distribution (based on transition matrix marginal)
    chord_dist = pc.sum(axis=(0, 1))
    chord_dist /= (chord_dist.sum() + 1e-8)

    print(f"\n  Chord transition distribution:")
    for i, name in enumerate(TYPE_NAMES):
        pct = chord_dist[i] * 100
        bar = "#" * int(min(max(pct, 0), 100) * 2)
        print(f"    {name:6s} {pct:5.1f}%  {bar}")

    return all_ok


def finetune_pchange_only(pchange, frozen_pnote, songs_batched, mask,
                           song_weight_tensor, lengths, shifts,
                           r_prev_indices, r_next_indices_for_beta,
                           pchord, n_songs, max_t, device, eps,
                           n_iter=200):
    """Finetune pchange with pnote frozen. Uses song weights + anti-collapse."""
    pnote = frozen_pnote
    n_types = 12
    original_pchange = pchange.clone()

    for fi in tqdm(range(n_iter), desc="Finetune pchange"):
        log_pnote = torch.log(pnote + eps)
        log_not_pnote = torch.log(1.0 - pnote + eps)
        songs_expanded = songs_batched[:, :, shifts]
        diff = log_pnote - log_not_pnote
        psets_log = torch.einsum("ntrp,pk->ntrk", songs_expanded, diff) + log_not_pnote.sum(dim=0)
        psets = torch.exp(psets_log) * mask.view(n_songs, max_t, 1, 1)

        alpha = torch.zeros(n_songs, max_t, N_TONES, n_types, device=device)
        alpha[:, 0] = (pchord / N_TONES) * psets[:, 0]
        norm = alpha[:, 0].sum(dim=(1, 2), keepdim=True)
        alpha[:, 0] /= norm + eps

        for t in range(1, max_t):
            prev_expanded = alpha[:, t - 1][:, :, r_prev_indices]
            combined_prev = torch.einsum("nrik,kio->nro", prev_expanded, pchange)
            alpha[:, t] = combined_prev * psets[:, t]
            norm = alpha[:, t].sum(dim=(1, 2), keepdim=True)
            alpha[:, t] /= norm + eps

        beta = torch.zeros(n_songs, max_t, N_TONES, n_types, device=device)
        for i, length in enumerate(lengths):
            beta[i, length - 1] = 1.0
        for t in range(max_t - 2, -1, -1):
            next_val = psets[:, t + 1] * beta[:, t + 1]
            next_expanded = next_val[:, r_next_indices_for_beta]
            combined_next = torch.einsum("nrio,kio->nrk", next_expanded, pchange)

            # Only update steps that are BEFORE the end of the song
            active = torch.tensor([t < l - 1 for l in lengths],
                                   dtype=torch.float32, device=device).view(-1, 1, 1)
            beta[:, t] = combined_next * active + beta[:, t] * (1 - active)

            norm = beta[:, t].sum(dim=(1, 2), keepdim=True)
            beta[:, t] /= norm + eps


        # Correct E-step for transitions: xi_t(i, j) ~ alpha_t(i) * a_ij * b_j(o_{t+1}) * beta_{t+1}(j)
        term_next = psets[:, 1:] * beta[:, 1:]
        term_prev_expanded = alpha[:, :-1][:, :, r_prev_indices]
        change_hist = torch.einsum("n,ntrik,kio,ntro->kio", song_weight_tensor, term_prev_expanded, pchange, term_next)

        new_pchange = change_hist / (change_hist.sum(dim=(1, 2), keepdim=True) + eps)

        # Anti-collapse: penalize any type > 15% of expected transitions
        if fi % 20 == 0:
            chord_dist = change_hist.sum(dim=(0, 1))
            chord_dist = chord_dist / (chord_dist.sum() + eps)
            for t_idx in range(n_types):
                if chord_dist[t_idx] > 0.15:
                    new_pchange[t_idx] *= 0.8
            new_pchange = new_pchange / new_pchange.sum(dim=(1, 2), keepdim=True)

        # Blend with original (80% new, 20% original) for stability
        pchange = 0.8 * new_pchange + 0.2 * original_pchange
        pchange = pchange / pchange.sum(dim=(1, 2), keepdim=True)

        # NaN guard
        if not torch.isfinite(pchange).all():
            pchange = original_pchange.clone()
            break

    return pchange.cpu().numpy()


def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"  Device: {device}")

    # Load corpora
    synth_dir = Path("tymoczko_code/Code/First step/synth_data")
    print("  Loading synthetic corpus...")
    raw_songs, raw_weights = load_ntc_songs(synth_dir)
    print(f"    Loaded {len(raw_songs)} songs")

    # Batching: Pad to max length
    max_t = max(s.shape[0] for s in raw_songs)
    n_songs = len(raw_songs)

    songs_batched = torch.zeros(n_songs, max_t, N_TONES, device=device)
    mask = torch.zeros(n_songs, max_t, device=device)
    song_weight_tensor = torch.zeros(n_songs, device=device)
    lengths = []

    for i, s in enumerate(raw_songs):
        t = s.shape[0]
        songs_batched[i, :t, :] = s.to(device)
        mask[i, :t] = 1.0
        song_weight_tensor[i] = raw_weights[i]
        lengths.append(t)

    # Normalize weights so they average to 1.0
    song_weight_tensor = song_weight_tensor / song_weight_tensor.mean()

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

    # Initialize parameters with STRONGER differentiation to avoid oscillation
    # pnote[pitch, type]
    pnote = torch.rand(N_TONES, N_TYPES, device=device) * 0.1 + 0.01
    
    # 0: Major (0, 4, 7)
    pnote[0, 0], pnote[4, 0], pnote[7, 0] = 0.9, 0.8, 0.8
    # 1: Minor (0, 3, 7)
    pnote[0, 1], pnote[3, 1], pnote[7, 1] = 0.9, 0.8, 0.8
    # 2: Dim (0, 3, 6)
    pnote[0, 2], pnote[3, 2], pnote[6, 2] = 0.8, 0.8, 0.8
    # 3: Aug (0, 4, 8)
    pnote[0, 3], pnote[4, 3], pnote[8, 3] = 0.8, 0.8, 0.8
    # 4: sus2 (0, 2, 7)
    pnote[0, 4], pnote[2, 4], pnote[7, 4] = 0.8, 0.9, 0.8
    # 5: sus4 (0, 5, 7)
    pnote[0, 5], pnote[5, 5], pnote[7, 5] = 0.8, 0.9, 0.8
    # 6: Maj7 (0, 4, 7, 11) - Focus on 11
    pnote[0, 6], pnote[4, 6], pnote[7, 6], pnote[11, 6] = 0.7, 0.6, 0.6, 0.99
    # 7: Min7 (0, 3, 7, 10) - Focus on 10
    pnote[0, 7], pnote[3, 7], pnote[7, 7], pnote[10, 7] = 0.7, 0.6, 0.6, 0.99
    # 8: Dom7 (0, 4, 7, 10) - Focus on 10
    pnote[0, 8], pnote[4, 8], pnote[7, 8], pnote[10, 8] = 0.7, 0.6, 0.6, 0.99
    # 9: Maj9 (0, 4, 7, 11, 2) - EXTREME focus on 2 and 11
    pnote[0, 9], pnote[4, 9], pnote[7, 9], pnote[11, 9], pnote[2, 9] = 0.5, 0.5, 0.5, 0.99, 0.99
    # 10: Min9 (0, 3, 7, 10, 2) - EXTREME focus on 2 and 10
    pnote[0, 10], pnote[3, 10], pnote[7, 10], pnote[10, 10], pnote[2, 10] = 0.5, 0.5, 0.5, 0.99, 0.99
    # 11: Add9 (0, 4, 7, 2) - Focus on 2, NO 11/10
    pnote[0, 11], pnote[4, 11], pnote[7, 11], pnote[2, 11] = 0.7, 0.7, 0.7, 0.99
    pnote[11, 11], pnote[10, 11] = 0.001, 0.001

    pchord = torch.tensor([2.0, 2.0, 1.0, 0.05, 0.3, 0.3, 1.0, 1.0, 1.5, 0.8, 0.8, 1.2], device=device)
    pchord /= pchord.sum()

    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)
    for t in range(N_TYPES):
        pchange[t, 0, t] = 2.0  # Chord repetition
    
    # Tonal foundations
    pchange[0, 7, 0] = 1.5  # I -> V (P5 up)
    pchange[0, 5, 0] = 2.0  # V -> I (P4 up / P5 down)
    pchange[0, 5, 1] = 1.5  # V -> i (P4 up)
    pchange[1, 7, 1] = 1.5  # i -> v
    pchange[1, 5, 1] = 2.0  # v -> i
    pchange[1, 3, 0] = 1.5  # i -> III
    
    # V7 resolutions (Dom7 -> Maj/Min at P4 up)
    pchange[8, 5, 0] = 2.5  # V7 -> I
    pchange[8, 5, 1] = 2.5  # V7 -> i
    
    pchange /= pchange.sum(dim=(1, 2), keepdim=True)

    print(f"\n  Turbo Training: {n_songs} songs, {max_t} max steps, {MAX_ITER} iters")
    start_time = time.time()
    eps = 1e-8

    # Early stopping state
    best_ll = -float("inf")
    best_pnote = pnote.clone()
    best_pchange = pchange.clone()
    stagnation = 0

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
            
            # Only update steps that are BEFORE the end of the song
            active = torch.tensor([t < l - 1 for l in lengths],
                                   dtype=torch.float32, device=device).view(-1, 1, 1)
            beta[:, t] = combined_next * active + beta[:, t] * (1 - active)
            
            norm = beta[:, t].sum(dim=(1, 2), keepdim=True)
            beta[:, t] /= norm + eps

        # 4. Expectations
        gamma = alpha * beta
        gamma /= gamma.sum(dim=(2, 3), keepdim=True) + eps

        # --- 3-PHASE EM SCHEDULE ---
        # (Phase 2 sharpening disabled because it conflicts with structural anchors)
        
        gamma *= mask.view(n_songs, max_t, 1, 1)

        # Apply per-song weights (common modes get more influence)
        gamma_weighted = gamma * song_weight_tensor.view(n_songs, 1, 1, 1)

        chord_hist = gamma_weighted.sum(dim=(0, 1, 2))
        note_hist = torch.einsum("ntrp,ntrk->pk", songs_expanded, gamma_weighted)

        # change_hist[t_p, i, t_n]
        term_next = psets[:, 1:] * beta[:, 1:]  # [N, T-1, 12, K]
        term_prev_expanded = alpha[:, :-1][:, :, r_prev_indices]  # [N, T-1, 12, 12, K]
        # Correct E-step for transitions: xi_t(i, j) ~ alpha_t(i) * a_ij * b_j(o_{t+1}) * beta_{t+1}(j)
        change_hist = torch.einsum("n,ntrik,kio,ntro->kio", song_weight_tensor, term_prev_expanded, pchange, term_next)

        # 5. M-step
        old_pnote = pnote.clone()
        pnote = note_hist / (chord_hist.view(1, N_TYPES) + eps)
        
        # --- STRUCTURAL ANCHORS: Force states to keep their musical meaning ---
        # Each column must prioritize its defining intervals
        # 0: Maj, 1: Min, 2: Dim, 3: Aug, 4: sus2, 5: sus4, 6: Maj7, 7: Min7, 8: Dom7, 9: Maj9, 10: Min9, 11: Add9
        anchors = [
            [0, 4, 7],       # 0: Major
            [0, 3, 7],       # 1: Minor
            [0, 3, 6],       # 2: Dim
            [0, 4, 8],       # 3: Aug
            [0, 2, 7],       # 4: sus2
            [0, 5, 7],       # 5: sus4
            [0, 4, 7, 11],   # 6: Maj7
            [0, 3, 7, 10],   # 7: Min7
            [0, 4, 7, 10],   # 8: Dom7
            [0, 4, 7, 11, 2],# 9: Maj9
            [0, 3, 7, 10, 2],# 10: Min9
            [0, 4, 7, 2],    # 11: Add9
        ]
        
        # Annealing: lower the floor over time to avoid oscillating with EM
        clamp_floor = max(0.05, 0.3 * (1.0 - iter_idx / MAX_ITER))
        for t_idx, notes in enumerate(anchors):
            for n in notes:
                pnote[n, t_idx] = torch.clamp(pnote[n, t_idx], clamp_floor, 0.999)
        
        pnote = torch.clamp(pnote, 0.001, 0.999)
        pchange = change_hist / (change_hist.sum(dim=(1, 2), keepdim=True) + eps)

        delta_note = torch.abs(pnote - old_pnote).max().item()
        delta_change = torch.abs(pchange - old_pchange).max().item() if 'old_pchange' in locals() else 1.0
        delta = max(delta_note, delta_change)
        old_pchange = pchange.clone()

        # Validation: check for chord type collapse every 50 iters
        if iter_idx % 50 == 0 or iter_idx == MAX_ITER - 1:
            type_names = ["Maj", "Min", "Dim", "Aug", "sus2", "sus4",
                          "Maj7", "Min7", "Dom7", "Maj9", "Min9", "Add9"]
            chord_dist = change_hist.sum(dim=(0, 1))  # [N_TYPES] — how much each type appears in expected transitions
            chord_dist = chord_dist / (chord_dist.sum() + eps)
            dominant_type = chord_dist.argmax().item()
            dominant_pct = chord_dist[dominant_type].item() * 100
            if dominant_pct > 20:
                pbar.write(f"  WARNING: {type_names[dominant_type]} dominates {dominant_pct:.1f}% of expected transitions at iter {iter_idx}")
                # Penalize dominant type in pchange to prevent collapse
                pchange[dominant_type] *= 0.8
                pchange /= pchange.sum(dim=(1, 2), keepdim=True)


        # Track best weights (always, not just after warmup)
        if total_ll.item() > best_ll + MIN_LL_DELTA:
            best_ll = total_ll.item()
            best_pnote = pnote.clone()
            best_pchange = pchange.clone()
            stagnation = 0
        elif iter_idx >= 50:
            stagnation += 1

        pbar.set_postfix({"dN": f"{delta_note:.6f}", "dC": f"{delta_change:.6f}", "LL": f"{total_ll:.1f}"})

        if delta < TARGET_DELTA and iter_idx >= 100:
            pbar.write(f"  Converged at iter {iter_idx}")
            break

        # Early stopping by LL plateau (skip warmup)
        if stagnation >= PATIENCE and iter_idx >= 50:
            pbar.write(f"  Early stop at iter {iter_idx}, LL plateau for {PATIENCE} iters (best LL={best_ll:.1f})")
            break

    # Restore best weights
    pnote = best_pnote
    pchange = best_pchange
    elapsed = time.time() - start_time

    print(f"\n  Training finished in {elapsed:.1f}s, best LL={best_ll:.1f}")

    # Save weights + checkpoint
    out_dir = Path("melodica/harmonize/weights")
    out_dir.mkdir(exist_ok=True, parents=True)
    np.savetxt(out_dir / "pnote_full.txt", pnote.cpu().numpy())
    np.save(out_dir / "pchange_full.npy", pchange.cpu().numpy())
    np.savez(
        out_dir / "hmm_checkpoint.npz",
        pnote=pnote.cpu().numpy(),
        pchange=pchange.cpu().numpy(),
        pchord=pchord.cpu().numpy(),
        log_likelihood=np.array([best_ll]),
        iteration=np.array([iter_idx]),
    )

    # Sanity check
    sanity_ok = run_sanity_check(pnote, pchange, pchord)
    original_pchange_np = pchange.cpu().numpy()
    if not sanity_ok:
        print("\n  Sanity check FAILED — running pchange-only finetune...")
        pchange_np = finetune_pchange_only(pchange, pnote, songs_batched, mask,
                                         song_weight_tensor, lengths, shifts,
                                         r_prev_indices, r_next_indices_for_beta,
                                         pchord, n_songs, max_t, device, eps)
        
        # Check if finetune actually improved things
        ft_ok = run_sanity_check(pnote, torch.from_numpy(pchange_np).to(device), pchord)
        if not ft_ok:
            # Compare: how many checks pass with each version
            def count_passes(pc_inp):
                pc = pc_inp.cpu().numpy() if isinstance(pc_inp, torch.Tensor) else pc_inp
                passes = 0
                if np.all(np.isfinite(pc)): passes += 1
                marginal = pc.sum(axis=(0, 1))
                total = marginal.sum()
                if total > 0 and np.isfinite(total):
                    marginal = marginal / total
                    if marginal[3] <= 0.15: passes += 1
                if pc[8, 5, 1] > 0.3: passes += 1
                if pc[0, 5, 0] > 0.01 or pc[0, 7, 0] > 0.01: passes += 1
                return passes
            orig_passes = count_passes(original_pchange_np)
            ft_passes = count_passes(pchange_np)
            if ft_passes <= orig_passes:
                print(f"  Finetune didn't improve ({ft_passes} vs {orig_passes} checks) — keeping original")
                pchange_np = original_pchange_np

        np.save(out_dir / "pchange_full.npy", pchange_np)
        np.savez(
            out_dir / "hmm_checkpoint.npz",
            pnote=pnote.cpu().numpy(),
            pchange=pchange_np,
            pchord=pchord.cpu().numpy(),
            log_likelihood=np.array([best_ll]),
            iteration=np.array([iter_idx]),
        )

    print(f"\n  Weights saved to {out_dir.absolute()}")


if __name__ == "__main__":
    main()
