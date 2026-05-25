# Harmonizer: known issues & TODO

Last updated: 2026-05-26

## What works

- Coupled HMM (Baum-Welch) trains on 1144 synthetic songs
- 5/5 sanity checks pass (pnote finite, pchange finite, aug <15%, dom7->min P4 >8%, maj V-I)
- Viterbi produces functional progressions with V7->I resolutions
- Anti-stagnation penalty in Viterbi prevents same-type repetition
- Post-processing caps self-loops (25%), individual cells (25%), and type distribution (12%)

## Known problems

### 1. Augmented chord still overrepresented (15.6%)

Aug (0,4,8) is symmetric — EM easily assigns ambiguous pitch sets to it.
Self-loop 24%, and it rarely resolves anywhere useful.

**Fix:** Replace Aug with a more constrained type (e.g. Maj7#5) or add
hard prior against Aug transitions in Viterbi.

### 2. Dom7->Maj P4 dominates all progressions

Dom7->Maj at P4 = 25.7%, Dom7->Min at P4 = 25.4%. These two cells eat
almost all Dom7 probability, producing repetitive V7->I chains:

```
D7 -> G -> A7 -> D -> E7 -> A -> B7 -> E
```

The pattern is musically valid but monotonous — every bar pair is the
same functional relationship.

**Fix:** Introduce secondary dominant paths (V7/ii, V7/iii) and
deceptive cadences (V7->vi) with higher priors. Or diversify by adding
interval-based diversity bonus beyond the current -1.5 penalty.

### 3. Maj9/Min9/Add9 form a "gravity well"

Extended chords (indices 9-11) collectively absorb 39.2% of transitions.
Once the Viterbi path enters an extended chord, it tends to drift through
root changes while staying in the same quality:

```
D(add9) -> F#(add9) -> A(add9) -> G#(add9) -> ...
```

The type-level anti-stagnation penalty (-2.0) breaks this, but only at
the cost of always switching away from extended chords, losing their
color.

**Fix:** Add a "type family" penalty that distinguishes between
triads (0-5), seventh chords (6-8), and ninth chords (9-11). Encourage
transitions between families rather than within.

### 4. Synthetic corpus limits harmonic vocabulary

The training corpus is 1144 synthetic .ntc files generated from a single
script. This means:

- No real voice-leading data
- No modulation patterns beyond what the script encodes
- No genre diversity (jazz ii-V-I, classical deceptive cadences, etc.)

**Fix:** Import real MIDI transcriptions. Sources:
- iReal Pro jazz corpus (~1300 standards)
- Hooktheory corpus (pop/rock progressions)
- IMSLP classical transcriptions

### 5. pnote emission model ignores non-chord tones

The emission model treats every pitch class independently. It cannot
distinguish between:

- A chord tone (high probability)
- A passing tone that happens to match (should be lower)
- A suspension that should resolve (context-dependent)

**Fix:** Add a simple context window (previous chord tones) to the
emission model, or train a small neural emission model.

### 6. Early stop at iter 2-349 (no learning after initial fit)

Best LL is almost always captured at iter 2 (LL=-101999). Everything
after is stagnation. This means the post-processing caps do all the
real shaping, not the EM.

The self-loop cap, cell cap, and type balance are applied to the
iter-2 weights retroactively, which works but is brittle.

**Fix:** Use a different LL that penalizes low entropy in the
transition distribution. Or use mini-batch training with diversity
regularization.

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
