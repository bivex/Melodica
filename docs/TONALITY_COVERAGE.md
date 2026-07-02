# Tonality Coverage — CoupledHMM Harmonization across all Modes

**Last updated:** 2026-07-02  
**Model:** CoupledHMMHarmonizer (supervised weights, t5harmony 49 803 songs)  
**Script:** `scripts/tonality_scale_showcase.py`  
**Method:** Melody built from I–III–V–VII degrees of each scale, `key_coupling_weight=2.0`

---

## Summary

| Category | Count | % |
|---|---|---|
| **CLEAN** — parse=4/4, ambiguous=0 | 52 | 66% |
| **PARTIAL** — some ambiguous or 7th-chord naming edge cases | 26 | 33% |
| **EXOTIC** — 0 parsed / all ambiguous | 0 | 0% |
| **ERRORS** | 0 | 0% |

Total modes probed: **78**

No mode causes a crash or zero-parse result. The model degrades gracefully even on
exotic, microtonal, and symmetric scales.

---

## CLEAN — Full Tonality Coverage (52 modes)

These modes produce parse=4/4, ambiguous=0. Tonality names every chord unambiguously.

| Mode | Example progression (C root) |
|---|---|
| major | C → Em → C → G |
| ionian | C → Em → C → G |
| harmonic_minor | Cm → Ab → G → Bm |
| lydian | C → Em → C → G |
| mixolydian | C → Em → C → Bb |
| locrian | Cm → Ab → F# → Bbm |
| diminished | Cm → Ab → F#m → D |
| bebop_major | C → Em → C → D |
| bebop_dominant | C → Em → C → Bb |
| bebop_dominant_mode_vi | C → Em → C → Bb |
| bebop_dominant_mode_vii | C → Dm → Bb → F |
| bebop_dominant_mode_viii | Cm → Ab → F#m → D |
| hungarian_minor | Cm → Ab → C → Bm |
| gypsy | C → Em → C → G |
| hirojoshi | Cm → Dm → Cm → Gm |
| japanese | Cm → C# → Fm → C |
| spanish_8_tone | Cm → Gm → Fm → Cm |
| byzantine | C → Em → C → G |
| arabian | Cm → Ab → G → Bm |
| altered | Cm → Ab → F# → Bbm |
| lydian_dominant | C → Em → C → Bb |
| major_pentatonic | C → G → Em → C |
| minor_pentatonic | Cm → Eb → Fm → Cm |
| neapolitan_minor | Cm → Ab → C → Bm |
| half_whole_diminished | Cm → Ab → F#m → A |
| whole_half_diminished | Cm → Ab → F#m → D |
| aeolian_bb7 | Cm → Ab → Gm → Am |
| augmented | Cm → Ab → G → C |
| augmented_mode_2 | Cm → C# → C → Fm |
| alt_bb3 | Cm → Ab → F# → Bbm |
| messiaen_2 | Cm → Ab → F#m → A |
| messiaen_3 | Cm → C# → C → Fm |
| messiaen_4 | Cm → G → F# → Bbm |
| messiaen_5 | Cm → D → F#m → D |
| prometheus | Cm → Dm → A7 → F#m |
| mystic | Cm → Dm → A → F#m |
| locrian_nat_2 | Cm → Ab → F# → Bbm |
| mixolydian_b6 | C → Em → C → Bb |
| suspense | C → Em → C → G |
| slendro_approx | C → G → Em → C |
| pelog_approx | Cm → C# → Cm → Gm |
| bhupali | C → G → Em → C |
| yaman | C → Em → C → G |
| bayati | Cm → C# → Ebm → E |
| phrygian_dominant | C → Em → C → Bb |
| double_harmonic | C → Em → C → G |
| dorian_pentatonic | Cm → Dm → Cm → Gm |
| minor_hexatonic | Cm → Dm → Cm → Fm |
| super_locrian | Cm → Ab → F# → Bbm |
| double_harmonic_major | C → Em → C → G |
| acoustic_major | C → Em → C → Bb |
| lyrical_major | C → Em → C → G |

---

## PARTIAL — Ambiguous naming (26 modes)

Parse=4/4 in all cases — harmonization succeeds, but ≥1 chord is ambiguous in the
naming layer. Root cause is almost always one of:

1. **7th chord ambiguity** — Cm7, Gm7, C7 have multiple valid interpretations
2. **Augmented triad** — symmetric, no single root reading
3. **Microtonal intervals** — quarter-tone scales map to 12-TET approximations

| Mode | Progression | amb | Note |
|---|---|---|---|
| natural_minor | Cm → Ab → Gm → **Cm7** | 1 | VII = Cm7 ambiguous |
| aeolian | Cm → Ab → Gm → **Cm7** | 1 | same as natural_minor |
| melodic_minor | Cm → **Ebaug** → G → Bm | 1 | aug triad |
| dorian | Cm → **Cm7** → Gm → **Cm7** | 2 | two 7th chords |
| phrygian | Cm → Ab → Gm → **Cm7** | 1 | VII = Cm7 |
| whole_tone | **Caug** → Dm → Em → F#m | 1 | aug on I |
| bebop_minor | Cm → Ab → Gm → **Cm7** | 1 | VII = Cm7 |
| blues | Cm → **Cm7** → Fm → Ebm | 1 | dom7 ambiguous |
| hungarian_major | C → Am → Gm → **Cm7** | 1 | VII = Cm7 |
| kumoi | Cm → Dm → **Gm7** → C7 | 1 | Gm7 ambiguous |
| persian | **Caug** → E → F#m → Bm | 1 | aug on I |
| neapolitan_major | Cm → **Ebaug** → G → Bm | 1 | aug triad |
| alt_bb3_bb7 | Cm → Ab → F#m → **C#aug** | 1 | aug on VII |
| messiaen_1 | **Caug** → Dm → Em → F#m | 1 | whole-tone = aug I |
| messiaen_6 | Cm → Dm → **Gm7** → Cm | 1 | Gm7 ambiguous |
| enigmatic | Cm → **Cm7** → Gm → **Cm7** | 2 | two 7th chords |
| dorian_b2 | Cm → **Cm7** → Gm → **Cm7** | 2 | same as dorian |
| ionian_b5 | **Caug** → E → F#m → Bm | 1 | aug on I |
| horror_cluster | **Csus2** → F#m → G → Cmajadd9 | 1 | sus2 / add9 edge |
| pedal_minor | Cm → **Cm7** → Fm → Cm | 1 | Cm7 ambiguous |
| quarter_tone_minor | Cm → Ab → Gm → **Cm7** | 1 | microtonal → 12-TET |
| arabic_sikah | **Caug** → Am → Gm → **Cm7** | 2 | microtonal [see note] |
| suspended_penta | Cm → Dm → **Gm7** → C7 | 1 | Gm7 ambiguous |
| acoustic_minor | Cm → **Cm7** → Gm → **Cm7** | 2 | two 7th chords |
| lydian_minor | **Caug** → C → Gm → **Cm7** | 2 | aug + 7th |
| lydian_aug_mode | **Caug** → E → Abm → E | 1 | aug on I |

---

## Microtonal Modes

The following modes contain microtonal (quarter-tone) intervals. The harmonizer
preserves Layer-2 distinctness via fuzzy 24-EDO membership but **output chords
remain 12-TET** — quarter-tone pitches are not synthesized in chord voicings.

| Mode | Intervals (semitones) | Coverage |
|---|---|---|
| arabic_sikah | 0, 1.5, 3.5, 5, 7, 8.5, 10.5 | PARTIAL (amb=2) |
| quarter_tone_minor | contains ~0.5 offsets | PARTIAL (amb=1) |

For authentic maqam harmony, a dedicated microtonal naming layer and corpus
would be required.

---

## Chord Vocabulary

The model operates with **12 chord types** (9 originally + 3 added):

| Index | Quality | Symbol | Status in real music (t5harmony) |
|---|---|---|---|
| 0 | Major | C | 46.7% |
| 1 | Minor | Cm | 27.7% |
| 2 | Diminished | Cdim | 2.7% |
| 3 | Augmented | Caug | 0.1% |
| 4 | Sus2 | Csus2 | ~0% (template prior only) |
| 5 | Sus4 | Csus4 | ~0% (template prior only) |
| 6 | Major7 | CM7 | ~0% (template prior only) |
| 7 | Minor7 | Cm7 | 10.3% |
| 8 | Dominant7 | C7 | 9.5% |
| 9 | Major9 | CM9 | 1.1% |
| 10 | Minor9 | Cm9 | 0.9% |
| 11 | Add9 | Cadd9 | 1.0% |

Types 4–6 (sus2, sus4, Maj7) appear ~0% in real music (t5harmony corpus) and rely
on template priors. The model will rarely output them unless the melody strongly
implies them. This is by design — see `docs/HMM_TRAINING_GOLD_STANDARD.md`.

---

## Training

| Parameter | Value |
|---|---|
| Corpus | t5harmony (Hooktheory TheoryTab) |
| Songs | 49 803 |
| Method | Supervised from gold `[root type bass]` labels |
| Script | `scripts/generators/train_full_modes.py --corpus t5harmony` |
| Runtime | ~17 seconds (numpy-only, no GPU required) |
| Weights | `melodica/harmonize/weights/pnote_full.txt` + `pchange_full.npy` |
| Backup (EM) | `pnote_full_unsup.txt` + `pchange_full_unsup.npy` |

Prior to supervised training, the unsupervised EM path produced degenerate spikes
(`pnote[2,sus2]=1.0`, `pnote[5,sus4]=1.0`) causing sus-chord spam on sparse melodies.
The supervised estimator fixes this at the source — see `scripts/supervised_pnote_probe.py`
for the diagnostic that confirmed the issue.

---

## Limitations

- **No zero-coverage modes** — all 78 modes produce valid chord output
- **7th chord naming ambiguity** is a naming-layer issue, not an HMM issue; the
  harmonization itself is correct, Tonality just has multiple valid interpretations
- **Microtonal modes** (sikah, quarter_tone_minor) produce 12-TET approximations;
  authentic quarter-tone voicings are not supported
- **sus2/sus4/Maj7** types are template-prior-only; they will appear only when the
  melody unambiguously implies them (rare in practice)
- The model was trained on western pop/rock harmony; non-western modes (bayati,
  pelog, slendro, hirojoshi) get functional results but not culturally authentic ones
