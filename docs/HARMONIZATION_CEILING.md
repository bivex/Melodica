# Harmonization Ceiling — 7th Chords & Extended Harmony

**Status:** Parameter ceiling PROVEN via 3-way falsification → then BROKEN by a set-completion objective term (`HMMConfig.completion_bonus`). The HMM is salvageable for extended harmony; no retrain or new architecture required.
**Date:** 2026-07-02
**Components:** `melodica/harmonize/coupled_hmm.py` (`HMMConfig.completion_bonus`, `CHORD_NOTES`), `scripts/tonality_scale_showcase.py`

## TL;DR

The supervised CoupledHMM retained 7th chords only **2/24** even when the melody literally spelled them (4-note arpeggios of maj7/min7/dom7). Three parameter hypotheses were falsified; the bottleneck is the **frame-wise emission objective** (subset-coverage, not chord identity). Adding a set-completion term `λ·𝟙(M⊆C)` restores 7th retention to **23/24**, assembles real ii–V–I and secondary dominants, with **zero showcase regression (78/78 CLEAN)**.

## The stress test

24 chord slots × 4 chord-tone notes per slot (arpeggio), target = a jazz-functional progression: `Cmaj7 Am7 Dm7 G7 | Cmaj7 Em7 Am7 D7 | Dm7 G7 Cmaj7 A7 | Dm7 G7 Em7 A7 | Dm7 G7 Cmaj7 C7 | Fmaj7 Fm6 Cmaj7 G7` (tonic prolongation, secondary dominants, modal interchange, cadences). Metric: 7th-retention, exact-pcs-match, triad-collapse. **Baseline: 7th=2/24, collapse=17/24.**

## Falsification chain (the parameter ceiling)

| # | Hypothesis | Change | Result |
|---|---|---|---|
| 1 | key-coupling overconstrains | `key_coupling_weight` 2.0→0.0 | no effect (only modal-borrow color: Bb/Cm/E) |
| 2 | type-prior suppresses 7ths | `LOG_KEY_TYPE_PRIOR[:, 6-10] += log5` | flipped ONLY slot 1 (initial, no transition); elsewhere `pchange` dominates |
| 3 | smoothing flattens 7ths | `PNOTE_PRIOR_STRENGTH` 3.0→0.5 | pnote byte-identical — `(counts+S·template)/(mel_frames+S)` makes S a rounding error vs `mel_frames[Dom7]≈137 000` |

After these, only the **likelihood geometry** remained.

## The metric — chord-tone contrast

`mean(pnote[chord-tones, type]) − mean(pnote[nct, type])` (lower = flatter = less discriminable):

| Maj | Min | Maj7 | Min7 | **Dom7** | HalfDim | FullDim |
|---|---|---|---|---|---|---|
| 0.210 | 0.223 | 0.160 | 0.187 | **0.106** | 0.157 | 0.187 |

Low contrast = high conditional entropy = tiny `KL(P(notes|7th) ‖ P(notes|triad))` → Viterbi never stably prefers the 7th. Dom7 is flattest, which is exactly why `G7 → G` always.

## Root cause — compatibility vs identity

The emission `P(note|type)` is estimated from real **linear** melodies (passing/neighbor/anticipation tones), so it faithfully learns a **broad** profile. The objective optimizes harmonic **compatibility** (which chord is plausible given a typical melody), not chord-identity **reconstruction** (which chord best explains *these* notes). Train distribution ≠ inference target. Triads win via **subset-coverage** (explain 75% of notes strongly, tolerate the remaining 25% cheaply under the broad profile); 7ths explain 100% but get **no set-completion reward**, so they lose. This is parameter-proof.

## The fix — set-completion inductive bias

`HMMConfig.completion_bonus` (default **0.0 = off**, no behavior change). In the `_viterbi_chords` emit loop it adds `λ` to the log-score of every `(root, type)` whose chord-tone set **covers all active melody pcs** (`M ⊆ chord_tones(r,k)`). This is the missing bias — it converts the per-frame objective from subset-coverage to set-completion, locally, inside the HMM. It is the minimal patch that aligns the training objective with the inference target the user actually wants.

## Results

| completion_bonus λ | 7th-retention | exact-pcs-match | triad-collapse |
|---|---|---|---|
| 0 (baseline) | 2/24 | 2/24 | 17 |
| 3 | **22/24** | 21/24 | 0 |
| 5 | **23/24** | 23/24 | 1 |
| 8 | 23/24 | 23/24 | 1 |

λ=5 progression: `CM7 CM6 Dm7 G7 | CM7 Em7 CM6 D7 | Dm7 G7 CM7 A7 | Dm7 G7 Em7 A7 | Dm7 G7 CM7 C7 | FM7 Ddim CM7 G7` — real jazz-functional harmony: **ii–V–I** cadences (Dm7→G7→CM7, twice), **secondary dominants** (A7→Dm7, D7), tonic prolongation. (`CM6`≡`Am7` — same pcs, the m7≡6 equivalence; `Ddim` at slot 22 the only mismatch vs Fm6.)

**Showcase (regression check):** 78/78 CLEAN at both λ=3 and λ=5 — no regression. The showcase uses 1 melody note per chord, so the bonus is weakly informative there and does not distort.
**Tests:** 248 passed (coupled_hmm + bridge), 2 xfailed (pre-existing).

## Usage

```python
from melodica.harmonize.coupled_hmm import HMMConfig
from melodica.engines.coupled_hmm_engine import CoupledHMMEngine

# Jazz / extended harmony:
engine = CoupledHMMEngine(config=HMMConfig(completion_bonus=5.0))
# Default 0.0 = unchanged pop-triad behavior (all existing generators unaffected)
```

λ≈3–5 recommended. Too high over-emits 7ths where the melody does not warrant them.

## What this rules in / out

- **IN:** the HMM is viable for extended (7th) harmony via a localized objective patch — no retrain, no new architecture. The earlier "ceiling" was the objective, not the model.
- **OUT (still):** a first-order Markov HMM cannot represent **phrase-scale** harmonic plans, delayed resolution, or guide-tone retention across bar boundaries — those need a sequence model (transformer over chord symbols). The completion term fixes 7th *identity*; it does not add long-range *functional hierarchy*.

## Reproduce

The 24-slot arpeggio probe lives inline in this investigation; pattern: build 4 chord-tone notes per slot, one ` HarmonizationRequest` with `chord_rhythm=4.0`, harmonize at `HMMConfig(key_coupling_weight=0.3, completion_bonus=λ)`, score with `verify_progression(chords, key=key)` and compare pcs to the target arpeggio per slot.
