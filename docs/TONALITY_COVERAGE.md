# Tonality Coverage — CoupledHMM Harmonization across all Modes

**Last updated:** 2026-07-03
**Model:** CoupledHMMHarmonizer (supervised weights)  
**Script:** `scripts/tonality_scale_showcase.py`  
**Method:** Melody built from I–III–V–VII degrees of each scale, `key_coupling_weight=2.0`

---

## Summary

| Category | Count | % |
|---|---|---|
| **CLEAN** — parse=4/4, ambiguous=0 | 78 | 100% |
| **PARTIAL** — parse=4/4 but ≥1 chord ambiguous | 0 | 0% |
| **EXOTIC** — 0 parsed / all ambiguous | 0 | 0% |
| **ERRORS** | 0 | 0% |

Total modes probed: **78**

All 78 modes parse 4/4 with ambiguous=0. The 100% reflects a **key- and
bass-aware verification oracle** (see Methodology), not a model or corpus
change — the supervised weights are unchanged from the prior 60-CLEAN run. The
18 modes formerly PARTIAL (m7≡maj6, augmented symmetry) now resolve because the
oracle uses the key + chord bass it already held.

---

## Methodology — key- and bass-aware chord naming (2026-07-02)

The showcase's ambiguous-chord count is decided by `mts.name_chord`, invoked via
`melodica.theory.tonality_bridge.verify_progression`. Previously the call passed
the chord's pitch-class set with **no key and no bass** (`context=None`), so any
pc set with more than one valid naming was flagged ambiguous unconditionally.
Two intrinsic pc-set equivalences drove all 18 former PARTIAL results:

- **m7 ≡ maj6** — `{0,3,7,10}` names as both Cm7 and Eb6
- **augmented symmetry** — `{0,4,8}` names at three roots

The harmonizer already knows the active key and each chord's root/bass. The fix
threads both into `name_chord` — an `AnalyticalContext(key=…)` plus a
`Realization` whose lowest pitch is the chord's **actual bass** (slash > inversion
> root). With key + bass the two interpretations separate (Cm7 has bass C, Eb6
has bass Eb), so `is_ambiguous` flips to False.

This change is **monotone**: context scores interpretations rather than adding
them, so ambiguity can only decrease, never increase. It uses the chord's true
lowest tone (not an assumed root), so it stays correct for inverted voicings.

**This is a verification-oracle change, not a model or data change.** The
underlying pc-set equivalences still exist; we resolve them with information the
system already held. Supervised weights and corpora are unchanged.

---

## CLEAN — Full Tonality Coverage (78 modes)

All 78 modes produce parse=4/4, ambiguous=0. Tonality names every chord
unambiguously once the active key and chord bass are supplied to the oracle
(see Methodology). The table below lists the modes that were already CLEAN under
the intrinsic-only oracle; the 18 formerly PARTIAL (m7/aug equivalences) are
listed in the "Resolved" section.

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

## Resolved — formerly PARTIAL, now CLEAN (18 modes)

These 18 modes were PARTIAL under the intrinsic-only oracle: their progressions
contain a m7 or augmented chord whose pc set has multiple intrinsic namings.
Under the key+bass-aware oracle (see Methodology) all of them are now CLEAN.
No model or data change — the oracle now uses the key + chord bass it already had.

| Mode | Progression (C root) | Was ambiguous because |
|---|---|---|
| natural_minor | Cm → Ab → Gm → Cm7 | Cm7 ≡ Eb6 |
| aeolian | Cm → Ab → Gm → Cm7 | Cm7 ≡ Eb6 |
| whole_tone | Caug → Daug → Caug → F#m | aug symmetry |
| bebop_minor | Cm → Ab → Gm → Cm7 | Cm7 ≡ Eb6 |
| hungarian_major | Cm → Em → Gm → Cm7 | Cm7 ≡ Eb6 |
| persian | Caug → E → F#m → Bm | aug on I |
| augmented_mode_2 | Caug → C#m → Caug → Fm | aug on I+III |
| messiaen_1 | Caug → Daug → Caug → F#m | whole-tone = aug |
| messiaen_3 | Caug → C#m → Caug → Fm | aug on I+III |
| enigmatic | Cm → Ebm → Gm → Cm7 | Cm7 ≡ Eb6 |
| suspense | Caug → C → G → CM7 | aug on I |
| horror_cluster | Caug → C#m → G → Cmajadd9 | aug on I |
| quarter_tone_minor | Cm → Ab → Gm → Cm7 | microtonal → 12-TET, Cm7 ≡ Eb6 |
| arabic_sikah | Cm → C → Gm → Cm7 | quarter-tone, Cm7 ≡ Eb6 |
| acoustic_minor | Cm → Ebm → Gm → Cm7 | Cm7 ≡ Eb6 |
| lydian_minor | Caug → C → Gm → Cm7 | aug + 7th |
| lydian_aug_mode | Caug → A → Abm → E | aug on I |
| lyrical_major | Caug → C → G → CM7 | aug on I |

---

## Microtonal Modes

The following modes contain microtonal (quarter-tone) intervals. The harmonizer
preserves Layer-2 distinctness via fuzzy 24-EDO membership but **output chords
remain 12-TET** — quarter-tone pitches are not synthesized in chord voicings.

| Mode | Intervals (semitones) | Coverage |
|---|---|---|
| arabic_sikah | 0, 1.5, 3.5, 5, 7, 8.5, 10.5 | CLEAN (resolved by key+bass oracle) |
| quarter_tone_minor | contains ~0.5 offsets | CLEAN (resolved by key+bass oracle) |

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

- **7th-chord / augmented pc-set equivalences** (Cm7≡Eb6, aug symmetry) are
  intrinsic to bare pitch-class sets. The showcase oracle now resolves them via
  the active key + chord bass (see Methodology), so they no longer show as
  PARTIAL — but the equivalences remain real for any context-free naming task
- **Microtonal modes** (sikah, quarter_tone_minor) produce 12-TET approximations;
  authentic quarter-tone voicings not supported
- **sus2/sus4** types are template-prior-only; they appear only when melody
  strongly implies them (no real-corpus evidence)
- **Rare types aren't retainable via `completion_bonus`** — half-dim (m7b5,
  type 9), full-dim (dim7, type 10), and sus4 (type 5) are in the 12-type
  vocabulary, but their real-music priors are too small (0.9% / 0.8% / 0.2%)
  for the Viterbi path to prefer them: the emission `P(notes|type)` plus
  transitions for a tone-sharing dom7/maj7 dominate even when the per-type
  `completion_bonus` is raised to ×15. Measured empirically on a 150-bar
  stress test (`scripts/harmonize_big_progression.py`): maj/min/maj7/m7/dom7
  retain at 91% under the `jazz` profile; aug retains (its pc set is
  geometrically unique, nothing else shares it); m7b5/dim7/sus4 collapse to a
  tone-sharing dom7 or maj7. The m7b5→V7-a-fifth-below case reproduces the
  ii-V relation, so the "failure" is usually musically correct. Literal
  retention for these types needs retraining on more gold frames of those
  types (a corpus/data change), not a bigger bonus.
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
.venv_dd/bin/python scripts/tonality_scale_showcase.py               # 78 CLEAN (100%)
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
