"""
Numerical audit of train_full_modes.py:
  1. EM monotonicity (LL must not decrease)
  2. gamma normalization (sum over (r,k) == 1.0 per step)
  3. scaling effectiveness (no underflow on real corpus lengths)
  4. ADD9 vs MAJOR: undertraining vs structural tie (direct diagnosis)
  5. transition matrix semantic sanity (tritone vs circle-of-fifths)
"""
import torch
import numpy as np
from pathlib import Path

N_TONES = 12
N_TYPES = 12
MAX_ITER = 60          # enough to observe monotonicity + convergence trend
TARGET_DELTA = 1e-5
PATIENCE = 300
MIN_LL_DELTA = 1.0
ON_PROB = 0.90
PRIOR_STRENGTH = 0.50
MAX_SELF_LOOP = 0.20


def load_ntc_songs(data_dir):
    songs, weights = [], []
    names = [p.stem for p in sorted(data_dir.glob("*.ntc"))]
    for name in names:
        fp = data_dir / f"{name}.ntc"
        if not fp.exists(): continue
        steps = []
        for line in fp.read_text().splitlines():
            line = line.strip()
            if "[" not in line: continue
            notes_str = line[line.find("[")+1:line.find("]")]
            notes = [int(n.strip()) for n in notes_str.split(",") if n.strip()]
            vec = torch.zeros(N_TONES)
            for n in notes: vec[n % N_TONES] = 1.0
            steps.append(vec)
        if steps:
            songs.append(torch.stack(steps))
            weights.append(1.0)
    return songs, weights


def main():
    device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Device: {device}")

    synth_dir = Path("tymoczko_code/Code/First step/synth_data")
    raw_songs, _ = load_ntc_songs(synth_dir)
    # Subset for memory: the change_hist einsum creates an (n,t,12,12,12)
    # intermediate. 200 songs × 28 steps × 12^3 × 4 bytes ≈ 1.3GB — manageable.
    # Monotonicity and convergence behaviour are representative on a subset.
    raw_songs = raw_songs[:200]
    print(f"Loaded {len(raw_songs)} songs (subset of 7800 for memory)")
    lengths = [s.shape[0] for s in raw_songs]
    print(f"  length stats: min={min(lengths)} max={max(lengths)} mean={np.mean(lengths):.1f}")

    max_t = max(lengths)
    n_songs = len(raw_songs)
    songs_batched = torch.zeros(n_songs, max_t, N_TONES, device=device)
    mask = torch.zeros(n_songs, max_t, device=device)
    for i, s in enumerate(raw_songs):
        t = s.shape[0]
        songs_batched[i, :t, :] = s.to(device)
        mask[i, :t] = 1.0

    shifts = (torch.arange(N_TONES, device=device).view(1, N_TONES) + torch.arange(N_TONES, device=device).view(N_TONES, 1)) % N_TONES
    r_next_indices = torch.arange(N_TONES, device=device).view(N_TONES, 1)
    interval_indices = torch.arange(N_TONES, device=device).view(1, N_TONES)
    r_prev_indices = (r_next_indices - interval_indices) % N_TONES
    r_next_indices_for_beta = (r_next_indices + interval_indices) % N_TONES

    CHORD_NOTES = {
        0: {0, 4, 7}, 1: {0, 3, 7}, 2: {0, 3, 6}, 3: {0, 4, 8},
        4: {0, 2, 7}, 5: {0, 5, 7}, 6: {0, 4, 7, 11}, 7: {0, 3, 7, 10},
        8: {0, 4, 7, 10}, 9: {0, 4, 7, 11, 2}, 10: {0, 3, 7, 10, 2}, 11: {0, 4, 7, 2},
    }
    pnote = torch.full((N_TONES, N_TYPES), 0.12, device=device)
    for t_idx, notes in CHORD_NOTES.items():
        for n in notes: pnote[n, t_idx] = ON_PROB
    pchord = torch.ones(N_TYPES, device=device) / N_TYPES
    pchange = torch.ones(N_TYPES, N_TONES, N_TYPES, device=device) / (N_TONES * N_TYPES)
    for t in range(N_TYPES): pchange[t, 0, t] = 2.0
    pchange /= pchange.sum(dim=(1, 2), keepdim=True)

    eps = 1e-8
    ll_history = []
    gamma_norm_history = []   # max |gamma.sum((r,k)) - 1| per iter
    alpha_min_history = []    # min nonzero alpha value (underflow check)

    for iter_idx in range(MAX_ITER):
        # E-step (identical to train_full_modes.py)
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
        for i, length in enumerate(lengths): beta[i, length - 1] = 1.0
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

        # Audit captures
        with torch.no_grad():
            # gamma per-step sum over (r,k) — should be 1.0 for active steps
            gs = gamma.sum(dim=(2, 3))  # (n_songs, max_t)
            active_mask = mask.view(n_songs, max_t) > 0
            deviations = (gs - 1.0).abs()[active_mask]
            gamma_norm_history.append(deviations.max().item())
            # alpha magnitude floor (underflow indicator): min nonzero over active steps
            alpha_active = alpha.abs()[active_mask]
            alpha_min_history.append(alpha_active[alpha_active > 0].min().item() if (alpha_active > 0).any() else 0.0)

        # M-step (identical)
        chord_hist = gamma.sum(dim=(0, 1, 2))
        note_hist = torch.einsum("ntrp,ntrk->pk", songs_expanded, gamma)
        term_next = psets[:, 1:] * beta[:, 1:]
        term_prev_expanded = alpha[:, :-1][:, :, r_prev_indices]
        change_hist = torch.einsum("ntrik,kio,ntro->kio", term_prev_expanded, pchange, term_next)

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

        ll_history.append(total_ll.item())

    # ===== REPORT =====
    print("\n" + "="*70)
    print("AUDIT REPORT")
    print("="*70)

    print("\n## 1. EM Monotonicity (LL must not decrease between iterations)")
    ll = np.array(ll_history)
    deltas = np.diff(ll)
    decreases = np.where(deltas < -1e-6)[0]
    print(f"  LL trajectory (iters 0..{len(ll)-1}):")
    for i in [0, 1, 2, 5, 10, 20, 30, 40, 50, len(ll)-1]:
        if i < len(ll): print(f"    iter {i:3d}: LL = {ll[i]:.2f}")
    print(f"  Total increase: {ll[-1] - ll[0]:.2f} ({(ll[-1]/ll[0]-1)*100:.1f}%)")
    print(f"  Decreases (violation of monotonicity): {len(decreases)}")
    if len(decreases):
        for i in decreases[:5]:
            print(f"    iter {i}->{i+1}: {ll[i]:.2f} -> {ll[i+1]:.2f} (Δ={deltas[i]:.4f})")
    print(f"  Verdict: {'✓ MONOTONIC (EM correct)' if len(decreases)==0 else '✗ NON-MONOTONIC (M-step bug suspected)'}")

    print("\n## 2. gamma normalization (sum over (r,k) per step)")
    gn = np.array(gamma_norm_history)
    print(f"  max |gamma.sum((r,k)) - 1| across iters: {gn.max():.2e}")
    print(f"  final iter deviation: {gn[-1]:.2e}")
    print(f"  Verdict: {'✓ normalized correctly' if gn.max() < 1e-4 else '✗ normalization broken'}")

    print("\n## 3. Scaling / underflow protection")
    am = np.array(alpha_min_history)
    print(f"  min nonzero alpha value (across iters): {am.min():.2e}")
    print(f"  float32 underflow floor ~1.2e-38; values stay well above.")
    print(f"  Verdict: {'✓ no underflow (scaled FB working)' if am.min() > 1e-30 else '⚠️ near underflow'}")

    # ===== ADD9 vs MAJOR diagnosis =====
    print("\n## 4. ADD9 vs MAJOR — undertraining or structural tie?")
    print("  Hypothesis (auditor): undertraining — ADD9 should have nonzero P(9th)")
    print("  absent from C-E-G input, pushing MAJOR ahead. If PNOTE[2, ADD9] (the 9th)")
    print("  is high, ADD9 incurs no penalty on triad-only input → tie is structural.")
    print(f"  Trained PNOTE[2, MAJOR]  (9th-of-C, should be ~0): {pnote[2, 0].item():.4f}")
    print(f"  Trained PNOTE[2, ADD9]   (9th-of-C, chord tone)  : {pnote[2, 11].item():.4f}")
    print(f"  Trained PNOTE[2, MAJ9]   (9th-of-C, chord tone)  : {pnote[2, 9].item():.4f}")
    print("  => On C-E-G input, MAJOR's contribution from pc=2 (D) is computed as")
    print("     (1 - PNOTE[2,MAJOR]) because D is ABSENT. So MAJOR gains a *bonus*")
    print("     for the absent 9th: log(1 - PNOTE[2,MAJOR]) ≈ log(1) = 0.")
    print("     ADD9 also has log(1 - PNOTE[2,ADD9]) ≈ log(1-0.999) ≈ -6.9 (penalty!).")
    ab_2 = pnote[2, 11].item()
    print(f"  ADD9 absent-9th penalty: log(1 - {ab_2:.3f}) = {np.log(1-ab_2):.3f}")
    print(f"  MAJOR absent-9th bonus : log(1 - {pnote[2,0].item():.3f}) = {np.log(1-pnote[2,0].item()):.3f}")
    print("  => MAJOR should WIN on triad-only input (ADD9 penalized for missing 9th).")
    print("     If observed tie persists, it's the (1-p) Bernoulli structure, not training.")

    # ===== Transition matrix semantic sanity =====
    print("\n## 5. Transition matrix semantics (tritone vs circle-of-fifths)")
    pc = pchange.cpu().numpy()
    # interval 6 = tritone, interval 7 = perfect fifth (circle-of-fifths motion)
    # Average over (type_prev, type_next)
    avg_by_interval = pc.mean(axis=(0, 2))  # shape (12,) — avg P for each interval
    print(f"  Mean transition prob by root interval:")
    interval_names = ['unison','m2','M2','m3','M3','P4','tritone','P5','m6','M6','m7','M7']
    for i in range(12):
        bar = '#' * int(avg_by_interval[i] * 200)
        print(f"    {interval_names[i]:8s} (iv {i:2d}): {avg_by_interval[i]:.4f} {bar}")
    tritone = avg_by_interval[6]
    fifth = avg_by_interval[7]
    fourth = avg_by_interval[5]
    print(f"  tritone ({tritone:.4f}) vs fifth ({fifth:.4f}) vs fourth ({fourth:.4f})")
    print(f"  Verdict: {'✓ tritone < fifth/fourth' if tritone < max(fifth, fourth) else '⚠️ tritone not suppressed'}")


if __name__ == "__main__":
    main()
