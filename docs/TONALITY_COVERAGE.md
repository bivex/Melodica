# Tonality Coverage — CoupledHMM Harmonization across all Modes

**Last updated:** 2026-07-02  
**Model:** CoupledHMMHarmonizer (supervised weights)  
**Script:** `scripts/tonality_scale_showcase.py`  
**Method:** Melody built from I–III–V–VII degrees of each scale, `key_coupling_weight=2.0`

---

## Summary

| Category | Count | % |
|---|---|---|
| **CLEAN** — parse=4/4, ambiguous=0 | 60 | 76% |
| **PARTIAL** — parse=4/4 but ≥1 chord ambiguous | 18 | 23% |
| **EXOTIC** — 0 parsed / all ambiguous | 0 | 0% |
| **ERRORS** | 0 | 0% |

Total modes probed: **78**

No mode causes a crash or zero-parse result. The model degrades gracefully even on
exotic, microtonal, and symmetric scales.

---

## CLEAN — Full Tonality Coverage (60 modes)

These modes produce parse=4/4, ambiguous=0. Tonality names every chord unambiguously.

| Mode | Example progression (C root) | VL |
|---|---|---|
| major | C → Em → C → E | 4 |
| ionian | C → Em → C → E | 4 |
| harmonic_minor | Cm → Ab → Gm → Bm | 7 |
| melodic_minor | Cm → Ebm → Gm → Bm | 7 |
| dorian | Cm → Ebm → Gm → Bbm | 8 |
| phrygian | Cm → Ab → Cm → Bbm | 8 |
| lydian | C → Em → C → E | 4 |
| mixolydian | C → Em → C → Bb | 8 |
| locrian | Cm → Ab → F# → Bbm | 8 |
| diminished | Cm → Ab → F#m → D | 7 |
| bebop_major | C → Em → C → D | 8 |
| bebop_dominant | C → Em → C → Bb | 8 |
| bebop_dominant_mode_vi | C → Em → C → Bb | 8 |
| bebop_dominant_mode_vii | C → G → Bb → D | 8 |
| bebop_dominant_mode_viii | Cm → Ebm → F#m → Am | 9 |
| blues | Cm → Ebm → Fm → F#m | 12 |
| hungarian_minor | Cm → Ab → Gm → Bm | 7 |
| gypsy | C → Em → C → E | 4 |
| hirojoshi | Cm → Dm → Cm → Gm | 15 |
| kumoi | Cm → Dm → Gm → C | — |
| japanese | Cm → C# → Fm → C | 7 |
| spanish_8_tone | Cm → Dm → Fm → Cm | 12 |
| byzantine | C → Em → C → E | 4 |
| arabian | Cm → Ab → Gm → Bm | 7 |
| altered | Cm → Ab → F# → Bbm | 8 |
| lydian_dominant | C → Em → C → Bb | 8 |
| major_pentatonic | C → G → Em → C | 6 |
| minor_pentatonic | Cm → Ebm → Fm → Cm | 12 |
| neapolitan_major | Cm → Ebm → Gm → Bm | 7 |
| neapolitan_minor | Cm → Ab → Gm → Bm | 7 |
| half_whole_diminished | Cm → Ebm → B → Am | 9 |
| whole_half_diminished | Cm → Ab → F#m → D | 7 |
| aeolian_bb7 | Cm → Ab → Gm → Am | 11 |
| augmented | Cm → Ebm → Em → C | 7 |
| alt_bb3 | Cm → Ab → F# → Bbm | 8 |
| alt_bb3_bb7 | Cm → Ab → F#m → Am | 9 |
| messiaen_2 | Cm → Ebm → B → Am | 9 |
| messiaen_4 | Cm → G → F#m → Bbm | 8 |
| messiaen_5 | Cm → Dm → F#m → D | — |
| messiaen_6 | Cm → Dm → Fm → Cm | — |
| prometheus | Cm → Dm → A → F#m | 10 |
| mystic | Cm → Dm → A → F#m | 10 |
| locrian_nat_2 | Cm → Ab → F# → Bbm | 8 |
| mixolydian_b6 | C → Em → C → Bb | 8 |
| dorian_b2 | Cm → Ebm → Gm → Bbm | 8 |
| ionian_b5 | Cm → Em → F#m → Bm | 8 |
| pedal_minor | Cm → Ebm → Fm → Cm | 12 |
| suspended_penta | Cm → Dm → Gm → C | — |
| slendro_approx | C → G → Em → C | 6 |
| pelog_approx | Cm → C#m → Ebm → Gm | — |
| bhupali | C → G → Em → C | 6 |
| yaman | C → Em → C → E | 4 |
| bayati | Cm → C# → Ebm → Em | — |
| phrygian_dominant | C → Em → C → Bb | 8 |
| double_harmonic | C → Em → C → E | 4 |
| dorian_pentatonic | Cm → Dm → Cm → Gm | 15 |
| minor_hexatonic | Cm → Dm → Cm → Fm | 12 |
| super_locrian | Cm → Ab → F# → Bbm | 8 |
| double_harmonic_major | C → Em → C → E | 4 |
| acoustic_major | C → Em → C → Bb | 8 |

---

## PARTIAL — Ambiguous naming (18 modes)

Parse=4/4 in all cases — harmonization succeeds, but ≥1 chord is ambiguous in the
naming layer. Root causes:

1. **7th chord ambiguity** — Cm7, Gm7, C7 have multiple valid interpretations
2. **Augmented triad** — symmetric, no single root reading
3. **Microtonal intervals** — quarter-tone scales map to 12-TET approximations

| Mode | Progression | amb | Note |
|---|---|---|---|
| natural_minor | Cm → Ab → Gm → **Cm7** | 1 | VII = Cm7 ambiguous |
| aeolian | Cm → Ab → Gm → **Cm7** | 1 | same as natural_minor |
| whole_tone | **Caug** → Daug → Caug → F#m | 3 | symmetric scale |
| bebop_minor | Cm → Ab → Gm → **Cm7** | 1 | VII = Cm7 |
| hungarian_major | Cm → Em → Gm → **Cm7** | 1 | VII = Cm7 |
| persian | **Caug** → E → F#m → Bm | 1 | aug on I |
| augmented_mode_2 | **Caug** → C#m → Caug → Fm | 2 | aug on I+III |
| messiaen_1 | **Caug** → Daug → Caug → F#m | 3 | whole-tone = aug |
| messiaen_3 | **Caug** → C#m → Caug → Fm | 2 | aug on I+III |
| enigmatic | Cm → Ebm → Gm → **Cm7** | 1 | VII = Cm7 |
| suspense | **Caug** → C → G → CM7 | 1 | aug on I |
| horror_cluster | **Caug** → C#m → G → Cmajadd9 | 1 | aug on I |
| quarter_tone_minor | Cm → Ab → Gm → **Cm7** | 1 | microtonal → 12-TET |
| arabic_sikah | Cm → C → Gm → **Cm7** | 1 | quarter-tone [see note] |
| acoustic_minor | Cm → Ebm → Gm → **Cm7** | 1 | VII = Cm7 |
| lydian_minor | **Caug** → C → Gm → Cm7 | 2 | aug + 7th |
| lydian_aug_mode | **Caug** → A → Abm → E | 1 | aug on I |
| lyrical_major | **Caug** → C → G → CM7 | 1 | aug on I |

---

## Microtonal Modes

The following modes contain microtonal (quarter-tone) intervals. The harmonizer
preserves Layer-2 distinctness via fuzzy 24-EDO membership but **output chords
remain 12-TET** — quarter-tone pitches are not synthesized in chord voicings.

| Mode | Intervals (semitones) | Coverage |
|---|---|---|
| arabic_sikah | 0, 1.5, 3.5, 5, 7, 8.5, 10.5 | PARTIAL (amb=1) |
| quarter_tone_minor | contains ~0.5 offsets | PARTIAL (amb=1) |

For authentic maqam harmony, a dedicated microtonal naming layer and corpus
would be required.

---

## Chord Vocabulary

The model operates with **12 chord types**:

| Index | Quality | Symbol | Real music % (combined corpus) |
|---|---|---|---|
| 0 | Major | C | 43.3% |
| 1 | Minor | Cm | 23.3% |
| 2 | Diminished | Cdim | 2.6% |
| 3 | Augmented | Caug | 0.1% |
| 4 | Sus2 | Csus2 | ~0% (template prior only) |
| 5 | Sus4 | Csus4 | 0.2% |
| 6 | Major7 | CM7 | 0.9% |
| 7 | Minor7 | Cm7 | 10.9% |
| 8 | Dominant7 | C7 | 15.6% |
| 9 | HalfDim | Cm7b5 | 0.9% |
| 10 | FullDim | Cdim7 | 0.8% |
| 11 | Add9 | Cadd9 | 1.4% |

Sus2 (type 4) relies on template prior only — 0% in real music. Dom7 (15.6%)
is empirically grounded from ChoCo jazz + iReal Pro + ChoCo extra corpora.

---

## Training Pipeline

| Parameter | Value |
|---|---|
| **pnote + pchange corpus** | t5harmony + ChoCo jazz + iReal Pro + ChoCo extra |
| Songs | 49 803 + 2 935 + 2 045 + 7 578 = **62 361 total** |
| Chord frames | ~2.97M |
| **pchange-only aux** | Chordonomicon (HuggingFace ailsntua/Chordonomicon, 666k songs, 50.3M frames) |
| Method | Supervised from gold `[root type bass]` labels; aux=pchange only (no pnote) |
| Script | `train_full_modes.py --corpus-dir corpus_combined --pchange-aux-dir corpus_chordonomicon --supervised auto` |
| Runtime | ~20 seconds (numpy-only, no GPU) |
| Weights | `melodica/harmonize/weights/pnote_full.txt` + `pchange_full.npy` |

**Converters:**
- `scripts/data/convert_choco_jazz.py` — Harte/ABC/Leadsheet/Weimar→ntc2 (multi-namespace)
- `scripts/data/convert_ireal_pro.py` — iReal Pro URL→ntc2 (pyRealParser)
- `scripts/data/convert_chordonomicon.py` — HuggingFace streaming→ntc2 (pchange-only)
- `scripts/data/convert_maiakovsky.py` — Maiakovsky/song_chord_changes→ntc2 (available but not used: inflates Maj→60%, causes EXOTIC regression)

**ChoCo partitions** at `/Volumes/External/Code/choco/partitions/`:
real-book (2846), jaah (89), ireal-pro (2045), wikifonia (6114), jazz-corpus (76),
weimar (456), nottingham (1002), when-in-rome (449, skipped — Roman numeral format)

**Why supervised?** The unsupervised EM path (train_full_modes.py default) ignores
the gold `[root type bass]` bracket in .ntc2 files and rediscovers chord types via
EM — causing self-reinforcing degenerate spikes (`pnote[2,sus2]=1.0`,
`pnote[5,sus4]=1.0`) and killing 7th chords (mass ~0.01). Supervised estimation
uses the labels directly: pnote[offset,type] from melody-annotated frames,
pchange[tp,int,tn] from chord transition sequences. See
`scripts/supervised_pnote_probe.py` for the diagnostic.

---

## Limitations

- **7th chord naming ambiguity** is a naming-layer issue, not an HMM issue;
  harmonization itself is correct, Tonality has multiple valid interpretations
- **Augmented triads** are symmetric — no single root reading possible
- **Microtonal modes** (sikah, quarter_tone_minor) produce 12-TET approximations;
  authentic quarter-tone voicings not supported
- **sus2/sus4** types are template-prior-only; they appear only when melody
  strongly implies them (no real-corpus evidence)
- **when-in-rome** partition (449 classical songs) not yet converted — requires
  key-aware Roman numeral resolver

---

## Rebuild After Reboot

Corpus directories are in `.gitignore` — only scripts and weights are committed.
After a fresh clone or reboot, rebuild everything in order:

```bash
cd /Volumes/External/Code/Melodica

# 1. ChoCo jazz (real-book + jaah) — 2 935 songs
.venv_dd/bin/python scripts/data/convert_choco_jazz.py \
  --partitions real-book jaah \
  --choco-dir /Volumes/External/Code/choco/partitions \
  --out-dir melodica/harmonize/corpus_choco_jazz

# 2. ChoCo extra (wikifonia + jazz-corpus + weimar + nottingham) — 7 648 songs
.venv_dd/bin/python scripts/data/convert_choco_jazz.py \
  --partitions wikifonia jazz-corpus weimar nottingham \
  --choco-dir /Volumes/External/Code/choco/partitions \
  --out-dir melodica/harmonize/corpus_choco_extra

# 3. iReal Pro — 2 045 songs (jazz/bossa/latin)
.venv_dd/bin/python scripts/data/convert_ireal_pro.py \
  --playlist-dir /Volumes/External/Code/choco/partitions/ireal-pro/raw/playlists \
  --out-dir melodica/harmonize/corpus_ireal_pro

# 4. Merge into combined (t5harmony already lives separately)
rsync -a melodica/harmonize/corpus_choco_jazz/  melodica/harmonize/corpus_combined/
rsync -a melodica/harmonize/corpus_choco_extra/ melodica/harmonize/corpus_combined/
rsync -a melodica/harmonize/corpus_ireal_pro/   melodica/harmonize/corpus_combined/
# t5harmony — 49 803 songs, copy or re-download if not present:
#   .venv_dd/bin/python scripts/data/convert_t5harmony.py --out-dir melodica/harmonize/corpus_combined

# 5. Chordonomicon pchange-aux — full 666k songs (HuggingFace streaming, ~5min)
.venv_dd/bin/python scripts/data/convert_chordonomicon.py \
  --limit 666000 \
  --out-dir melodica/harmonize/corpus_chordonomicon

# 6. Retrain supervised weights (~20s, numpy-only, no GPU)
.venv_dd/bin/python scripts/generators/train_full_modes.py \
  --corpus-dir melodica/harmonize/corpus_combined \
  --pchange-aux-dir melodica/harmonize/corpus_chordonomicon \
  --supervised auto

# 7. Verify
.venv_dd/bin/python -m pytest tests/test_coupled_hmm.py -q          # 232 passed
.venv_dd/bin/python scripts/tonality_scale_showcase.py               # 58 CLEAN (74%)
```

**Expected output of step 6:**

```
labeled frames by type%: {0: 57.0, 1: 23.2, 2: 1.2, ..., 7: 6.3, 8: 8.7, ...}
Supervised weights saved to melodica/harmonize/weights
```

**DO NOT** add Maiakovsky/song_chord_changes as pchange-aux — it is pop-heavy
(Maj 60%), inflates tonic mass and causes EXOTIC regression in the showcase.
The converter (`convert_maiakovsky.py`) is available for experimentation only.

### Update TONALITY_COVERAGE.md after retraining

Run the showcase and paste the summary:

```bash
.venv_dd/bin/python scripts/tonality_scale_showcase.py 2>&1 \
  | grep -E "SUMMARY|CLEAN|PARTIAL|EXOTIC"
```

Then update the Summary table and the CLEAN/PARTIAL lists in this file manually,
or regenerate with:

```bash
.venv_dd/bin/python scripts/tonality_scale_showcase.py 2>&1 \
  | grep -v "Warning\|warn" > /tmp/showcase_out.txt
# then copy relevant lines into this doc
```
