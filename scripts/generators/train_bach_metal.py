# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/train_bach_metal.py — Ultra-fast Metal-accelerated HMM training.
Fully vectorized version to eliminate Python overhead.
Includes tqdm progress bars.
"""

import torch
import numpy as np
from pathlib import Path
import time
from tqdm import tqdm

def load_bach_dataset(data_dir: Path):
    songs_notes = []
    songlist = (data_dir / "songlist.txt").read_text().splitlines()
    for name in songlist:
        file_path = data_dir / f"{name.strip()}.ntc"
        if not file_path.exists(): continue
        
        song_steps = []
        with open(file_path, "r") as f:
            for line in f:
                if "[" not in line: continue
                notes_str = line[line.find("[")+1 : line.find("]")]
                notes = [int(n.strip()) for n in notes_str.split(",") if n.strip()]
                # Convert to multi-hot vector [12]
                vec = torch.zeros(12)
                for n in notes: vec[n % 12] = 1.0
                song_steps.append(vec)
        if song_steps:
            songs_notes.append(torch.stack(song_steps))
    return songs_notes

def main():
    device = torch.device("mps")
    data_dir = Path("tymoczko_code/Code/First step/ntc_data")
    
    print(f"  -> Loading Bach dataset from {data_dir}...")
    # songs is a list of tensors [T, 12]
    songs = [s.to(device) for s in load_bach_dataset(data_dir)]
    print(f"  -> Loaded {len(songs)} songs to Metal device.")

    N_TONES = 12
    N_TYPES = 3 
    MAX_ITER = 50
    TARGET_DELTA = 1e-5

    # pnote[12, 3]: Probability of pitch class s given chord type t
    pnote = torch.rand(N_TONES, N_TYPES, device=device)
    pnote[0, :] = 0.9 # Root strong bias
    pnote[4, 0] = 0.8 # Major 3rd
    pnote[3, 1] = 0.8 # Minor 3rd
    pnote[7, :2] = 0.8 # Fifth
    
    # pchord[3]: Initial prob
    pchord = torch.ones(N_TYPES, device=device) / N_TYPES

    # pchange[type_from, interval, type_to]
    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)

    # Baum-Welch Loop
    start_time = time.time()
    pbar_outer = tqdm(range(MAX_ITER), desc="Training Progress")
    
    for iter_idx in pbar_outer:
        note_hist = torch.zeros_like(pnote)
        chord_hist = torch.zeros(N_TYPES, device=device)
        change_hist = torch.zeros_like(pchange)
        total_ll = 0.0

        # Optimization: Pre-calculate log-probs
        eps = 1e-8
        log_pnote = torch.log(pnote + eps)
        log_not_pnote = torch.log(1.0 - pnote + eps)

        for song_vec in tqdm(songs, desc=f"  Iter {iter_idx+1}", leave=False):
            T = song_vec.shape[0]
            
            # 1. Vectorized psets [T, 12, 3]
            psets_log = torch.zeros(T, N_TONES, N_TYPES, device=device)
            for r in range(N_TONES):
                heard = torch.roll(song_vec, shifts=-r, dims=1)
                not_heard = 1.0 - heard
                p_emit = heard @ log_pnote + not_heard @ log_not_pnote
                psets_log[:, r, :] = p_emit
            
            psets = torch.exp(psets_log)

            # 2. Forward Pass
            alpha = torch.zeros(T, N_TONES, N_TYPES, device=device)
            alpha[0] = (pchord / N_TONES) * psets[0]
            norm = alpha[0].sum()
            alpha[0] /= (norm + eps)
            total_ll += torch.log(norm + eps)

            for t_step in range(1, T):
                prev = alpha[t_step-1]
                combined_prev = torch.zeros(N_TONES, N_TYPES, device=device)
                for i in range(N_TONES):
                    prev_shifted = torch.roll(prev, shifts=i, dims=0)
                    combined_prev += prev_shifted @ pchange[:, i, :]
                
                alpha[t_step] = combined_prev * psets[t_step]
                norm = alpha[t_step].sum()
                alpha[t_step] /= (norm + eps)
                total_ll += torch.log(norm + eps)

            # 3. Backward Pass
            beta = torch.zeros(T, N_TONES, N_TYPES, device=device)
            beta[T-1] = 1.0
            for t_step in range(T-2, -1, -1):
                next_val = psets[t_step+1] * beta[t_step+1]
                combined_next = torch.zeros(N_TONES, N_TYPES, device=device)
                for i in range(N_TONES):
                    next_shifted = torch.roll(next_val, shifts=-i, dims=0)
                    combined_next += next_shifted @ pchange[:, i, :].T
                beta[t_step] = combined_next
                beta[t_step] /= (beta[t_step].sum() + eps)

            # 4. Expectations
            gamma = alpha * beta
            gamma /= (gamma.sum(dim=(1,2), keepdim=True) + eps)
            chord_hist += gamma.sum(dim=(0, 1))
            
            for r in range(N_TONES):
                heard = torch.roll(song_vec, shifts=-r, dims=1)
                note_hist += heard.T @ gamma[:, r, :]

            for t_step in range(T-1):
                term_next = psets[t_step+1] * beta[t_step+1]
                for i in range(N_TONES):
                    term_prev = alpha[t_step]
                    next_shifted = torch.roll(term_next, shifts=-i, dims=0)
                    change_hist[:, i, :] += term_prev.T @ next_shifted

        # 5. M-Step
        old_pnote = pnote.clone()
        pnote = note_hist / (chord_hist.view(1, 3) + eps)
        pnote = torch.clamp(pnote, 0.001, 0.999)
        pchange = change_hist / (change_hist.sum(dim=(1,2), keepdim=True) + eps)
        
        delta = torch.abs(pnote - old_pnote).max().item()
        pbar_outer.set_postfix({"Delta": f"{delta:.6f}", "LL": f"{total_ll:.2f}"})
        
        if delta < TARGET_DELTA: break

    end_time = time.time()
    print(f"\n  Training Finished in {end_time - start_time:.2f}s on Metal.")
    
    np.savetxt("pnote_metal.txt", pnote.cpu().numpy())
    np.save("pchange_metal.npy", pchange.cpu().numpy())
    print("  Saved weights: pnote_metal.txt and pchange_metal.npy")

if __name__ == "__main__":
    main()
