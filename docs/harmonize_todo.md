# Harmonizer: known issues & TODO

Last updated: 2026-06-21

> **Cross-reference:** the training-side analysis of these issues lives in
> [`docs/dev/TRAINING_AUDIT.md`](dev/TRAINING_AUDIT.md). In particular, issue #6
> below (early stop at iter 2) is now **resolved** — its root cause was an
> E-step `xi` corruption bug, fixed in commit `3889abe` and verified
> numerically. See TRAINING_AUDIT.md §8.1.

## What works

- Coupled HMM (Baum-Welch) trains on 1144 synthetic songs
- 5/5 sanity checks pass (pnote finite, pchange finite, aug <15%, dom7->min P4 >8%, maj V-I)
- Viterbi produces functional progressions with V7->I resolutions
- Anti-stagnation penalty in Viterbi prevents same-type repetition
- Post-processing caps self-loops (25%), individual cells (25%), and type distribution (12%)

## Known problems

### 1. Augmented chord still overrepresented (15.6%)

**Status: open (partially mitigated).**

Aug (0,4,8) is symmetric — EM easily assigns ambiguous pitch sets to it.
Self-loop 24%, and it rarely resolves anywhere useful.

`extended_chord_penalty` (in `HMMConfig`) and the anti-stagnation penalty
partially mitigate this by penalising extended/symmetric types and repeated
roots, but neither targets Aug specifically.

**Fix:** Replace Aug with a more constrained type (e.g. Maj7#5) or add
hard prior against Aug transitions in Viterbi.

### 2. Dom7->Maj P4 dominates all progressions

**Status: open. Not addressable by the xi fix alone.**

Dom7->Maj at P4 = 25.7%, Dom7->Min at P4 = 25.4%. These two cells eat
almost all Dom7 probability, producing repetitive V7->I chains:

```
D7 -> G -> A7 -> D -> E7 -> A -> B7 -> E
```

The pattern is musically valid but monotonous — every bar pair is
the same functional relationship.

Note: the E-step `xi` fix (commit `3889abe`) makes the transition counts
*more correct* but does *not* make them *more diverse* — it corrects scale,
not distribution shape. Diversification is a separate concern.

**Fix:** Introduce secondary dominant paths (V7/ii, V7/iii) and
deceptive cadences (V7->vi) with higher priors. Or diversify by adding
interval-based diversity bonus beyond the current `interval_diversity_penalty`.

### 3. Maj9/Min9/Add9 form a "gravity well"

**Status: partially closed via `extended_chord_penalty`.**

Extended chords (indices 9-11) collectively absorb 39.2% of transitions.
Once the Viterbi path enters an extended chord, it tends to drift through
root changes while staying in the same quality:

```
D(add9) -> F#(add9) -> A(add9) -> G#(add9) -> ...
```

The type-level anti-stagnation penalty (-2.0) breaks this, but only at
the cost of always switching away from extended chords, losing their
color.

`extended_chord_penalty` (which penalises types 9, 10, 11 in the emission)
handles the most visible symptom — on triad-only input it breaks the
ADD9/MAJOR tie in favour of the simpler triad (verified in TRAINING_AUDIT.md
§5.3). But the full "type family" penalty (triads 0-5 / sevenths 6-8 /
ninths 9-11) proposed below is not implemented.

**Fix (remaining):** Add a "type family" penalty that distinguishes between
triads (0-5), seventh chords (6-8), and ninth chords (9-11). Encourage
transitions between families rather than within.

### 4. Synthetic corpus limits harmonic vocabulary

**Status: open. This is the single biggest lever for `pchange` quality.**

The training corpus is 1144 synthetic .ntc files generated from a single
script. This means:

- No real voice-leading data
- No modulation patterns beyond what the script encodes
- No genre diversity (jazz ii-V-I, classical deceptive cadences, etc.)

The E-step `xi` fix is a *correctness* improvement on the existing corpus;
it does not add information. Real harmonic diversity requires a richer
corpus. **This is the prerequisite for any meaningful retrain.**

**Fix:** Import real MIDI transcriptions. Sources:
- iReal Pro jazz corpus (~1300 standards)
- Hooktheory corpus (pop/rock progressions)
- IMSLP classical transcriptions

### 5. pnote emission model ignores non-chord tones

**Status: open (conscious design choice).**

The emission model treats every pitch class independently. It cannot
distinguish between:

- A chord tone (high probability)
- A passing tone that happens to match (should be lower)
- A suspension that should resolve (context-dependent)

This is an intentional simplification of the Bernoulli-product model,
documented as a known limitation rather than a defect.

**Fix:** Add a simple context window (previous chord tones) to the
emission model, or train a small neural emission model.

### 6. Early stop at iter 2-349 (no learning after initial fit)

**Status: RESOLVED (2026-06-21).**

Best LL is almost always captured at iter 2 (LL=-101999). Everything
after is stagnation. This means the post-processing caps do all the
real shaping, not the EM.

> **Update 2026-06-21:** this was a *symptom* of the `xi` corruption bug
> documented in [TRAINING_AUDIT.md §8.1](dev/TRAINING_AUDIT.md). The buggy
> `xi` made EM maximise a Q-function that no longer lower-bounded the
> observed LL, so EM appeared to "converge" at iter 2 while actually
> diverging from the true optimum. After the Rabiner-identity fix
> (commit `3889abe`):
> - **Monophonic corpus:** EM is now effectively monotone (0 real LL
>   decreases, drift = -0.04 — float32 noise), peak at iter 17.
> - **Polyphonic corpus:** peak shifted from iter 2 to **iter 12**,
>   post-peak drift reduced 6x (from -93 to -15).
>
> The remaining polyphonic oscillation (0.29% of peak LL) is an open
> question — see TRAINING_AUDIT.md §8.2 (strong data-ambiguity hypothesis,
> monophonic control test, not yet a closed diagnosis).

~~The self-loop cap, cell cap, and type balance are applied to the
iter-2 weights retroactively, which works but is brittle.~~

~~**Fix:** Use a different LL that penalizes low entropy in the
transition distribution. Or use mini-batch training with diversity
regularization.~~

## Future directions

> These are candidate directions drawn from a literature scan, with
> epistemic caveats noted. The list is intentionally *not* a roadmap —
> each item needs evaluation (see "Evaluation" below) before it earns a
> place in the system.

### Spiral Array / Midi Miner as a TensionCurve replacement

The current `TensionCurve` is heuristic. The Spiral Array (Chew & Chen),
exposed via the Midi Miner package, provides three perceptually-validated
tension measures — **cloud diameter**, **cloud momentum**, **tensile
strain** — computed at the chord level. This is the most solid of the
candidates: the package exists, works, and the measures have published
perceptual validation.

**Caveat (chord-level vs melodic-step tension):** Spiral Array tension is
computed over the chord's pitch aggregate, not over melodic step motion.
If the scoring pipeline already uses tension as one signal, verify the
two do not double-count — melodic-step tension and chord-aggregate
tension are related but not identical quantities.

### Entropy-based diversity (do NOT call this "SurpriseNet")

A *simplified* local-transition-entropy bonus — penalising low-entropy
regions of the transition distribution to encourage harmonic variety — is
cheap to implement and plausibly helps issue #2 (Dom7→Maj monotony) and
issue #3 (extended-chord gravity well).

**Epistemic caveat:** this is **not** what the SurpriseNet paper does.
SurpriseNet uses conditional entropy over the *entire harmonic structure*
(a global/structural quantity), not local per-transition Markov entropy.
Calling the local version "SurpriseNet" would be an overclaim on a
structurally similar but mathematically different quantity — the same
mistake as labelling a benign saddle-point "diagnosed". Name it honestly:
**"entropy-based diversity"**.

If the structural/conditional-entropy formulation is wanted, that is a
separate, larger implementation — do not silently substitute the local
version and call it the same thing.

### Dual-Level Beam Search

Replacing the current `n_candidates=8 + random noise` Phase-2 selection
with a structured beam search has high potential impact, but is **not
low effort** — it is effectively a rewrite of Phase 2.

**Structural prerequisite:** beam search needs *space to manoeuvre*. With
`chord_change="bars"` (fixed harmonic rhythm), the beam operates at bar
granularity but tension re-ranking needs to see neighbouring bars, so the
two interact awkwardly. The sane order is:

1. Flexible harmonic rhythm first (see AutoHarmonizer-style approaches),
2. *then* beam search on top.

Doing beam search before harmonic-rhythm flexibility exists will create a
consistency problem, not solve one.

### Comparative Study as a ready-made benchmark

The comparative harmonisation study (202 systems, objective metrics) is
undervalued as "an architecture overview". It is in fact a **ready-made
benchmark protocol** for objective positioning of this system against the
HMM baseline — usable *now*, without implementing anything new. If you
want to know where the current weights stand relative to a published
HMM harmoniser, this is the cheapest path to an answer.

### Evaluation (currently ABSENT — the strongest gap)

None of the above directions is measurable without an evaluation harness.
Every "improvement" without metrics is, in the v1-audit sense, "the formula
looks similar" — not a verified improvement. The standard HMM-harmoniser
metrics are:

- **Chord-tone ratio** — fraction of melody notes that are chord tones of
  the assigned chord.
- **Harmonic rhythm consistency** — does the chord-change grid match the
  phrase structure?
- **Subjective listening test** — does it sound better?

**Recommendation:** build the evaluation harness *before* implementing
Spiral Array / entropy diversity / beam search. Otherwise there is no way
to tell whether a change helps or regresses — exactly the failure mode
that the v1 audit exhibited ("algorithms correct" without numerical
verification).

## Suggested order of work

1. **Evaluation harness** (chord-tone ratio + harmonic rhythm consistency).
   Without this, nothing below is measurable.
2. **Spiral Array** as a TensionCurve replacement — solid, packaged,
   perceptually validated.
3. **Entropy-based diversity** (honestly named) — cheap, targets issues
   #2 and #3.
4. **Comparative Study benchmark** — position the current system
   objectively against the HMM baseline.
5. *Then*, with metrics in hand, consider the larger items: flexible
   harmonic rhythm → beam search.

Do **not** invert this order — beam search before evaluation or
harmonic-rhythm flexibility is work that cannot be validated and may fight
the existing structure.

## Architecture notes

```
pnote_full.txt    [12 x 12]   emission: pitch-class probability per chord type
pchange_full.npy  [12 x 12 x 12]  transition: [prev_type, interval, next_type]
hmm_checkpoint.npz    saved state for resuming training

Viterbi state space: 12 roots x 12 types = 144 states
```

## Quick benchmark (3 random 16-bar progressions in D harmonic minor)

Typical output:
```
Dm7 -> G#dim -> Am7 -> A#Maj7 -> C7 -> F -> C7 -> F -> G7 -> C -> D7 -> G -> A7 -> Dm -> F -> G7
```

Metrics:
- Unique intervals: 4-6 out of 15 steps
- Unique types: 4-6 out of 16 chords
- Average consecutive same-type: 0-2 per progression
