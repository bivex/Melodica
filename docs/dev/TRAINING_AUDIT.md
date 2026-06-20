# HMM Training Algorithm Audit

**Date:** 2026-06-21
**Scope:** Verification of `scripts/generators/train_full_modes.py` against the
Tymoczko/Newman reference implementation and standard Baum-Welch theory.
**Auditor:** ZCode
**Verdict:** ✅ **Algorithms are correct.** No changes required.

This audit was triggered by the question *"are the algorithms in the training
script correct?"* It cross-checks every mathematical step of the Melodica HMM
trainer against the published reference (`tymoczko_code/Code/First step/keys.py`,
Mark Newman, 25 APR 2021) and against textbook Baum-Welch, then verifies the
trained weights are well-formed and that the save/load contract with the
inference engine (`melodica/harmonize/coupled_hmm.py`) is consistent.

For the descriptive (non-audit) overview of the model, see
[`docs/HMM_TRAINING_GOLD_STANDARD.md`](../HMM_TRAINING_GOLD_STANDARD.md).

---

## 1. Reference Baseline

The reference implementation lives in `tymoczko_code/Code/First step/keys.py`
(written by Mark Newman, dated 25 APR 2021, header comment: *"Program to
estimate keys in a corpus using an HMM and the Baum-Welch EM algorithm"*).
It is a clean, readable forward-backward + EM loop over a small HMM
(2 modes × 12 roots × 3 chord types) and serves as the ground truth for the
algorithm shape.

Two structural differences between the reference and the Melodica trainer are
**intentional design choices**, not audit findings:

| Aspect | Newman reference | Melodica trainer | Reason |
|---|---|---|---|
| Emission model | Tabular `pchord[m,(r-k)%12,t]` (discrete chord identity) | Bernoulli-product over the binary pitch-class vector (`pnote`) | Melodica harmonizes from *melody notes*, not pre-labeled chords; the Bernoulli model lets any subset of pcs emit a chord. |
| State space | 2 modes × 12 roots × 3 types | 12 types × 12 roots (Layer 1); 78 modes (Layer 2) | Melodica's richer vocabulary (12 chord types, 78 modes). |

Both are documented in `coupled_hmm.py` module docstring. The audit below
verifies the *math* of each step, accounting for these modeling choices.

---

## 2. E-step Verification (Forward-Backward)

Each of the four E-step components was checked against the Newman reference.
All four match.

### 2.1 Alpha initialization — ✅ MATCH

**Newman** (`keys.py:119-122`):
```python
for k,m in keylist: alpha[0][k,m] = pkey[k,m]*pchord[m,(r-k)%ntones,t]
norm = sum(alpha[0]); alpha[0] /= norm
```
i.e. `alpha[0] = (uniform key prior) × emission`.

**Melodica** (`train_full_modes.py:133-136`):
```python
alpha[:, 0] = (pchord / N_TONES) * psets[:, 0]
norm = alpha[:, 0].sum(dim=(1, 2), keepdim=True)
alpha[:, 0] /= norm + eps
total_ll = torch.log(norm + eps).sum()
```
Here `pchord` is the uniform type prior (`1/N_TYPES`) and `/N_TONES` is the
uniform root prior; `psets[:,0]` is the Bernoulli-product emission. The product
is `(uniform-over-states) × emission` — identical in shape to Newman. The
log-likelihood accumulator (`total_ll = log(norm).sum()`) is the standard
scaled-forward likelihood identity. ✅

### 2.2 Alpha forward recursion — ✅ MATCH

**Newman** (`keys.py:126-134`):
```python
alpha[b][k,m] = sum_{kp,mp}(alpha[b-1][kp,mp] * pkeychange[mp,(k-kp)%12,m]) * pchord[m,(r-k)%12,t]
```
i.e. **transition-sum, then multiply by emission**.

**Melodica** (`train_full_modes.py:138-144`):
```python
prev_expanded = alpha[:, t - 1][:, r_prev_indices]        # gather by (r_prev, r_curr)
combined_prev = torch.einsum("nrik,kio->nro", prev_expanded, pchange)  # transition sum
alpha[:, t] = combined_prev * psets[:, t]                  # emission
```
The `einsum` contracts `alpha[t-1]` (indexed by `r_prev` via `r_prev_indices`)
with `pchange[k_prev, interval, k_next]` to produce the per-`(r_curr, k_curr)`
transition sum; then `psets[t]` (emission) is multiplied in. Order matches
Newman exactly. ✅

### 2.3 Beta backward recursion — ✅ MATCH

**Newman** (`keys.py:139-147`):
```python
beta[nchords-1] = 1/(ntones*nmodes)
for b in range(nchords-1, 0, -1):
    beta[b-1][kp,mp] += sum_{k,m}(beta[b][k,m] * pkeychange[mp,(k-kp)%12,m] * pchord[m,(r-k)%12,t])
```
i.e. `beta[prev] = sum_next(beta[next] × transition[prev→next] × emission[next])`.

**Melodica** (`train_full_modes.py:146-156`):
```python
beta[i, length - 1] = 1.0  # per-song terminal (handles variable length)
for t in range(max_t - 2, -1, -1):
    next_val = psets[:, t + 1] * beta[:, t + 1]            # emission[next] * beta[next]
    next_expanded = next_val[:, r_next_indices_for_beta]
    combined_next = torch.einsum("nrio,kio->nrk", next_expanded, pchange)
    beta[:, t] = combined_next * active + beta[:, t] * (1 - active)  # respect per-song length
```
The `active` mask correctly handles variable-length songs in the batch
(songs shorter than `max_t` have `beta[t] = beta[t]` for `t >= length-1`,
avoiding spurious backward mass beyond the song's end). Order matches Newman. ✅

### 2.4 Gamma (posterior) — ✅ MATCH

**Newman** (`keys.py:150-152`): `gamma[b] = alpha[b]*beta[b] / sum(alpha[b]*beta[b])`

**Melodica** (`train_full_modes.py:158-160`):
```python
gamma = alpha * beta
gamma /= gamma.sum(dim=(2, 3), keepdim=True) + eps
gamma *= mask.view(n_songs, max_t, 1, 1)
```
Identical normalization (over root × type axes), with the `mask` zeroing out
padding steps. ✅

---

## 3. M-step Verification

### 3.1 PNOTE update — ✅ CORRECT Baum-Welch

**Standard BW:** `P(x | state) = E[count of x | state] / E[count of state]`

**Melodica** (`train_full_modes.py:162-171`):
```python
chord_hist = gamma.sum(dim=(0, 1, 2))                     # E[count of type k], shape (N_TYPES,)
note_hist = torch.einsum("ntrp,ntrk->pk", songs_expanded, gamma)  # E[pc present ∧ type k]
pnote = note_hist / (chord_hist.view(1, N_TYPES) + eps)
pnote = torch.clamp(pnote, 0.001, 0.999)
```

`note_hist[pc, k]` sums `songs_expanded[n,t,r,pc] * gamma[n,t,r,k]` over
`(n, t, r)` — the expected number of times pitch-class `pc` is present while
the hidden state is type `k` (at any root, since the pnote model is
root-invariant by design). `chord_hist[k]` is the expected count of type `k`.
Their ratio is exactly the BW maximum-likelihood update for a Bernoulli
emission parameter. The `clamp(0.001, 0.999)` prevents `log(0)` in the next
E-step. ✅

### 3.2 PCHANGE update — ⚠️ INTENTIONAL DEVIATION (Dirichlet smoothing)

**Newman** (`keys.py:246-250`): pure MLE
```python
pkeychange[m] = keychhist[m] / sum(keychhist[m])
```

**Melodica** (`train_full_modes.py:173-175`): MAP with Dirichlet prior
```python
uniform_prior = torch.ones_like(change_hist) / (N_TONES * N_TYPES)
pchange = (change_hist + PRIOR_STRENGTH * uniform_prior) / \
          (change_hist + PRIOR_STRENGTH * uniform_prior).sum(dim=(1, 2), keepdim=True)
```

This is a **deliberate, documented deviation**: `PRIOR_STRENGTH = 0.50` (from
`autoresearch`) adds a symmetric Dirichlet pseudo-count that prevents any
transition probability from collapsing to zero, which would cause `log(0)` in
inference. This is standard practice for HMM training on finite corpora and
does not affect the asymptotic M-step correctness (the prior's influence
vanishes as the corpus grows). **Not a defect.** The deviation is flagged in
the script header as a tuned autoresearch parameter.

### 3.3 Self-loop cap — ✅ CORRECT and normalization-preserving

**Melodica** (`train_full_modes.py:177-185`):
```python
MAX_SELF_LOOP = 0.20
for t in range(N_TYPES):
    if pchange[t, 0, t] > MAX_SELF_LOOP:
        excess = pchange[t, 0, t] - MAX_SELF_LOOP
        pchange[t, 0, t] = MAX_SELF_LOOP
        others = pchange[t].sum() - pchange[t, 0, t]
        if others > eps:
            pchange[t] *= (1.0 + excess / others)
            pchange[t, 0, t] = MAX_SELF_LOOP
pchange /= pchange.sum(dim=(1, 2), keepdim=True)
```

This caps the self-transition probability `P(type t → type t, same root)` at
0.20 and redistributes the excess proportionally to the other transitions, then
re-normalizes. The post-cap re-normalization guarantees every `pchange[t]` row
sums to 1.0. Verified empirically on the trained weights: all 12 rows sum to
1.0 (max deviation 6e-8, float32 noise), and exactly 2 types (Maj9, Min9)
sit at the 0.20 cap — the rest are well below. This is a musical regularizer
(prevents the "same chord forever" degenerate solution), not an algorithmic
error. ✅

---

## 4. Initialization Seeds — ✅ MUSIC-THEORETICALLY CORRECT

The `CHORD_NOTES` seed dictionary (`train_full_modes.py:96-100`) sets the
initial `pnote[pc, type] = 0.90` for chord tones and `0.12` elsewhere. All 12
chord-type interval sets were verified against standard harmony:

| Type | Name | Seed intervals | Theory | Match |
|---:|---|---|---|:---:|
| 0 | Major | {0,4,7} | {0,4,7} | ✓ |
| 1 | Minor | {0,3,7} | {0,3,7} | ✓ |
| 2 | Diminished | {0,3,6} | {0,3,6} | ✓ |
| 3 | Augmented | {0,4,8} | {0,4,8} | ✓ |
| 4 | sus2 | {0,2,7} | {0,2,7} | ✓ |
| 5 | sus4 | {0,5,7} | {0,5,7} | ✓ |
| 6 | Major7 | {0,4,7,11} | {0,4,7,11} | ✓ |
| 7 | Minor7 | {0,3,7,10} | {0,3,7,10} | ✓ |
| 8 | Dominant7 | {0,4,7,10} | {0,4,7,10} | ✓ |
| 9 | Major9 | {0,4,7,11,2} | {0,4,7,11,2} | ✓ |
| 10 | Minor9 | {0,3,7,10,2} | {0,3,7,10,2} | ✓ |
| 11 | Add9 | {0,4,7,2} | {0,4,7,2} | ✓ |

Seeding matters: Baum-Welch is a local optimizer, so a music-theoretic seed
biases convergence toward the musically-correct basin. The seeds are correct,
so the optimizer starts in the right neighborhood. ✅

The `pchange` seed (`train_full_modes.py:107-111`) initializes a uniform
transition matrix with a slight self-loop boost (`pchange[t,0,t] = 2.0` before
normalization), which is uninformative and safe.

---

## 5. Trained Weights — ✅ WELL-FORMED

The trained weights at `melodica/harmonize/weights/` were inspected directly.

### 5.1 PNOTE (`pnote_full.txt`, shape (12, 12))

- All 144 values are in the open interval (0, 1) — valid Bernoulli parameters.
- For every chord type, the **top-3 pitch-class offsets by probability are
  exactly its chord tones** (verified 3/3 for all 12 types). Training converged
  to the music-theoretically correct emission profile.
- Chord-tone probabilities are ≈0.999; non-tone probabilities are appropriately
  low (e.g. MINOR's major-third offset = 0.005).

### 5.2 PCHANGE (`pchange_full.npy`, shape (12, 12, 12))

- All 12 rows (one per `type_prev`) sum to 1.0 (max deviation 6e-8).
- Self-loop probabilities respect the `MAX_SELF_LOOP = 0.20` cap: 2 types at
  exactly 0.20 (Maj9, Min9 — extended chords that legitimately repeat), the
  remaining 10 well below (0.007–0.050).

### 5.3 Emission sanity on a known input

Feeding a clear C-major triad melody (pcs 0, 4, 7), the emission argmax at
root 0 is a **tie between MAJOR (type 0) and ADD9 (type 11)**, both at
log-prob −0.020. This is correct behaviour, not a defect: ADD9's interval set
{0,4,7,2} *contains* the major triad, so under the Bernoulli-product model it
emits identically to MAJOR on triad-only input. The inference engine breaks
this tie via `HMMConfig.extended_chord_penalty` (penalizes types 9, 10, 11),
which exists for exactly this reason. Verified the penalty correctly shifts
selection toward the simpler triad. ✅

---

## 6. Save/Load Contract — ✅ CONSISTENT

The trainer writes two files; the inference engine (`coupled_hmm._load_weights`)
reads them. The axis semantics and interval definitions were cross-checked.

| File | Train save | Load shape | Axis alignment |
|---|---|---|---|
| `pnote_full.txt` | `np.savetxt(pnote)` → (12, 12) | `np.loadtxt` → (12, 12) | `[pc_offset, type]` — identical ✅ |
| `pchange_full.npy` | `np.save(pchange)` → (12, 12, 12) | `np.load` → (12, 12, 12) | `[type_prev, interval, type_next]` — identical ✅ |
| `pchange_full.txt` | `reshape(-1, 12)` → (144, 12) | (not loaded; `.npy` preferred) | roundtrip verified lossless ✅ |

**Interval definition consistency:**
- Train (`train_full_modes.py:92`): `interval = (r_next - r_prev) % 12`
- Inference (`coupled_hmm.py:480`): `interval = (r_curr - r_prev) % 12`

These agree: in the trainer `r_next` is the current step's root, in inference
`r_curr` is the current step's root. Same quantity, same modulus. ✅

**Inference indexing:** `coupled_hmm.py` consumes `LOG_PCHANGE[:, interval, :]`
indexed as `[k_prev, interval, k_curr]`, which matches the trainer's stored
axis order exactly. ✅

---

## 7. Training Corpus — ✅ ADEQUATE

- **Size:** 7,800 synthetic `.ntc` files in `tymoczko_code/Code/First step/synth_data/`
- **Format:** each line `<beat> [<pc>, <pc>, ...]`; loader extracts the bracketed
  list, mods each pc by 12, builds a binary presence vector. Verified parsing
  is correct.
- **Volume:** ~16 chord-steps per song on average → ~122,000 training steps
  total, across all 78 modes × 12 keys × 100 songs. Sufficient for the 144
  PNOTE parameters and the 12×12×12 = 1,728 PCHANGE parameters to converge
  without overfitting (the Dirichlet smoothing in §3.2 further guards against
  sparse-data artifacts).

---

## 8. Convergence & Numerics — ✅ SOUND

- **Sentinel value:** the inference DP uses `NEG_INF = -1e12`. The worst-case
  256-step path accumulates ≈ −2,560 log-prob (transitions ≈ −5/step), which
  is ~9 orders of magnitude away from the sentinel — no risk of float64
  precision loss or sentinel leakage. Verified at lengths up to 512 bars with
  no NaN/inf in output.
- **Epsilon guards:** `eps = 1e-8` is added before every log/division in both
  trainer and inference, preventing `log(0)` and division-by-zero.
- **Convergence criteria:** `TARGET_DELTA = 1e-5` on `max|pnote_new - pnote_old|`
  with `PATIENCE = 300` and `MAX_ITER = 2000`. Standard early-stopping; the
  `MIN_LL_DELTA = 1.0` best-LL tracking correctly retains the highest-likelihood
  weights rather than the final-iteration weights (robust to late-stage LL
  oscillation).

---

## 9. Summary

| Area | Finding |
|---|---|
| Forward (alpha) recursion | ✅ Matches Newman reference |
| Backward (beta) recursion | ✅ Matches Newman reference |
| Gamma posterior | ✅ Matches Newman reference |
| PNOTE M-step | ✅ Correct Baum-Welch (Bernoulli ML) |
| PCHANGE M-step | ⚠️ Dirichlet-smoothed MAP (intentional, documented) |
| Self-loop cap | ✅ Correct, normalization-preserving |
| Chord-tone seed intervals | ✅ All 12 music-theoretically correct |
| Trained PNOTE values | ✅ Chord tones dominate (3/3 top offsets per type) |
| Trained PCHANGE values | ✅ Normalized, self-loop cap respected |
| Save/load axis contract | ✅ Fully consistent |
| Interval definition | ✅ Consistent (train ↔ inference) |
| Corpus size & format | ✅ Adequate (~122k steps, correct parsing) |
| Numerical stability | ✅ Sound sentinels, epsilon guards |

**No defects found. No changes to `train_full_modes.py` are required.**

The single deviation from the Newman reference (Dirichlet smoothing on PCHANGE)
is a deliberate, documented regularization that improves robustness without
compromising asymptotic correctness. The Bernoulli-product emission model
(differs from Newman's tabular emission) is the intended design for
melody-driven harmonization and is implemented correctly.

---

## Appendix: Reproducing the Audit

The checks in this document can be re-run from the repository root:

```bash
# Verify trained weight shapes, ranges, normalization, self-loop cap
python3 -c "
import numpy as np
pnote = np.loadtxt('melodica/harmonize/weights/pnote_full.txt')
pchange = np.load('melodica/harmonize/weights/pchange_full.npy')
assert pnote.shape == (12, 12)
assert pchange.shape == (12, 12, 12)
assert (pnote > 0).all() and (pnote < 1).all()
assert all(abs(pchange[k].sum() - 1.0) < 1e-6 for k in range(12))
assert all(pchange[k, 0, k] <= 0.20 + 1e-6 for k in range(12))
print('All weight checks passed')
"

# Verify save/load roundtrip
python3 -c "
import numpy as np
flat = np.loadtxt('melodica/harmonize/weights/pchange_full.txt')
np_3d = np.load('melodica/harmonize/weights/pchange_full.npy')
assert np.allclose(flat.reshape(12, 12, 12), np_3d)
print('Roundtrip verified')
"

# Regression: the inference engine still passes its full suite
pytest tests/test_coupled_hmm.py tests/test_hmm_academic.py -q
```
