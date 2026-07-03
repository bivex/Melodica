# Harmonizer — Type Vocabulary, Retention & Corpus Notes

**Created:** 2026-07-03
**Scope:** objective findings on `CoupledHMMHarmonizer`'s type system, chord
retention behavior, and corpus/data experiments. Sources cited inline so the
claims are re-verifiable. Companion to `TONALITY_COVERAGE.md` and
`harmonize_todo.md`.

---

## 1. The 12-type vocabulary (authoritative)

`CoupledHMMHarmonizer` operates on exactly **12 chord types**. Confirmed by
three independent sources that agree:

| Idx | Type | pc-template | Source |
|---|---|---|---|
| 0 | Maj | `{0,4,7}` | `train_full_modes.py:29`, weights, `convert_choco_jazz.py` |
| 1 | Min | `{0,3,7}` | " |
| 2 | Dim | `{0,3,6}` | " |
| 3 | Aug | `{0,4,8}` | " |
| 4 | sus2 | `{0,2,7}` | " |
| 5 | sus4 | `{0,5,7}` | " |
| 6 | Maj7 | `{0,4,7,11}` | " |
| 7 | Min7 | `{0,3,7,10}` | " |
| 8 | Dom7 | `{0,4,7,10}` | " |
| 9 | **Maj9** | `{0,4,7,11,2}` | weights profile `{0,2,4,7}` |
| 10 | **Min9** | `{0,3,7,10,2}` | weights profile `{0,2,7,10}` |
| 11 | Add9 | `{0,4,7,2}` | " |

- `scripts/generators/train_full_modes.py:29` — `N_TYPES = 12 # Cinematic Expanded (Maj, Min, Dim, Aug, sus2, sus4, Maj7, Min7, Dom7, Maj9, Min9, Add9)`
- `melodica/harmonize/weights/pnote_full.txt` is `12 × 12` (semitone × type); each column's peak-pc profile identifies the type (9/10/11 peak like Maj9/Min9/Add9, **not** halfdim/fulldim).
- `scripts/data/convert_choco_jazz.py` maps accordingly (halfdim → 7, dim7 → 2).

**There is NO halfdim (m7b5) or fulldim7 (dim7) type.** They collapse to
Min7(7) / Dim(2) at the data level.

### ⚠ Three different numbering namespaces (do not confuse)

1. **Harmonizer type index** (0–11 above) — used by `.ntc2` `[root type bass]`,
   `pnote`/`pchange` arrays, and `completion_bonus` dict keys (e.g. `{8:5}`).
2. **`Quality` IntEnum** (`melodica/theory/chords.py`) — for `ChordLabel`
   construction: MAJOR=0…HALF_DIM7=7, FULL_DIM7=8, SUS2=9, SUS4=10… **Different
   values** (e.g. its 7=HALF_DIM7 ≠ harmonizer's 7=Min7).
3. **`TONALITY_COVERAGE.md` Chord Vocabulary table** — labels 9=HalfDim,
   10=FullDim. **This is stale/wrong** (should be 9=Maj9, 10=Min9 per the two
   authoritative sources above).

---

## 2. Retention mechanism — template-uniqueness, not prior magnitude

A chord type is **retained** at inference when its pc-template is *spelled in
the contour* and the profile's `completion_bonus` fires exclusively for it
(the bonus fires when `melody_pcs ⊆ chord_tones(root,type)`).

- **Prior magnitude is NOT the lever — template-uniqueness is.** `Aug` (type 3,
  ~0.1% prior, ghost-tier) **retains** reliably (isolated and in progressions)
  because `{0,4,8}` is shared by no other type — the bonus can only fire for
  Aug. Likewise `dim` triad and `sus4` retain when spelled in isolation.
- **`completion_bonus` magnitudes** (in `harmonizer_profile`, see `profiles.py`):
  `pop`=0 (triads only), `jazz`/`neo_soul`=5.0 uniform, `blues`=`{8:5}`
  (dom7-only), `funk`=`{8:5, 7:4}` (dom7+min7). Profile = quality filter; the
  contour forces the root (~90% root-match across profiles).
- Boosting a rare type's bonus does **not** help if its template isn't uniquely
  matched (a confounded `boost_exotic` experiment boosted 9/10 = Maj9/Min9, not
  halfdim/fulldim — produced a 9th flood, didn't test the intended types).

---

## 3. The diminished family — what retains, what collapses

Measured by spelling single chords and reading the output (`scripts/harmonize_big_progression.py` style):

| Spelled | pcs | Output | overlap | Why |
|---|---|---|---|---|
| C dim | `{0,3,6}` | **C:dim ✓** | 1.00 | type 2 template `{0,3,6}` matches |
| C sus4 | `{0,5,7}` | **C:sus4 ✓** | 1.00 | type 5 template `{0,5,7}` matches |
| C aug | `{0,4,8}` | **C:aug ✓** | 1.00 | type 3, unique pc-set |
| C dim7 | `{0,3,6,9}` | C:dim | 0.75 | **no type template contains all 4** → drops 9 → nearest = dim triad |
| C m7b5 | `{0,3,6,10}` | C:dim | 0.75 | **no type template contains all 4** → drops 10 → nearest = dim triad |

**Only dim7 and halfdim collapse** — and they collapse to the **dim triad**
(function preserved, 7th color lost), not to dom7/maj7. In long progressions
HMM transitions can additionally pull rare-type bars toward common chords (a
context effect, distinct from the template-match limit above).

---

## 4. Profile → genre decision rule (chord-tone contour technique)

To force a specific chord quality, **spell its chord-tone arpeggio in the
contour** (base pitch must be a multiple of 12 to preserve pcs); the profile's
`completion_bonus` retains it. Profile choice per genre:

| Genre family | Profile | Notes |
|---|---|---|
| Pop R&B, trap (triadic) | `pop` | clean triads, `completion_bonus=0` |
| R&B/neo-soul (lush 7th/9th) | `neo_soul` | uniform 5.0 + `extended_chord_penalty=0` → 9ths |
| Major blues (I7-IV7-V7) | `blues` | `{8:5}` dom7-only |
| Minor blues, afrobeat (m7+dom7) | `funk` | `{8:5,7:4}` — `blues` cannot retain m7 |
| Jazz (all 7ths) | `jazz` | uniform 5.0 |

`blues` (dom7-only) **structurally cannot retain m7** → use `funk` for minor
blues. See `write-blues-album` skill + memory `minor-blues-needs-funk-profile`.

---

## 5. when-in-rome corpus — stats, dilution, retrain result

`choco/partitions/when-in-rome/` (classical Roman-numeral analysis):

- `choco/jams/`: **449 .jams** (matches the count in `TONALITY_COVERAGE.md`;
  the 898 figure was a broader glob). `raw/`: 1544 `.mxl` + 1153 `.mscz` scores
  (notes only, no chord labels).
- Each chord is `<local key>:<roman>` (`chord_roman` namespace) + `key_mode`
  for modulations — **key-aware per-chord**.
- Frame distribution (201,878 chord_roman obs): Maj 57.4%, Min 26.2%, other-7th
  13.0%, **dim7 (°7) 2.08%, halfdim (ø) 1.15%**.
- Classical is ~3× richer in Dim than the existing corpus.

**Retrain experiment (2026-07-03, reverted):** converter `convert_when_in_rome.py`
mapped 449 jams → 93,407 frames at 92% (halfdim→Min7, dim7→Dim, per the 12-type
collapse). Ingested into `corpus_combined`, retrained supervised. Result:
- Dim corpus prior **0.2%** (WIR's 7303 Dim frames swamped in ~3M; ≈3% of corpus).
- **Stress test unchanged** (jazz 91% exact, no Dim retention gained) — **no-op**.
- Showcase **78/78 CLEAN** — no regression.
- **Conclusion:** at ~3% corpus fraction, WIR alone does not move Dim retention.
  Dilution confirms `harmonize_todo.md` issue #4's stance that data fraction matters.

---

## 6. Auto chord-recognition on raw scores — does not work (off-the-shelf)

`raw/` scores (MusicXML/MuseScore) carry **notes, not chord labels**. Attempting
automatic chord extraction via `music21` failed on every windowing strategy:

| Strategy | Result |
|---|---|
| `chordify` | 511 slices, mostly 1–2 notes (melodic fragments) → nonsense Roman |
| beat-window (absolute offsets) | 0 chords with ≥3 pcs (texture too arpeggiated) |
| measure-window union | 3–10 pc unions → absurd Roman (`bviiøb7765#5b332`) |

**Root cause:** classical scores are written as **figuration** (arpeggios, broken
chords, counterpoint, non-chord tones), not block chords. Extraction requires
real **harmonic reduction** (collapse arpeggios → verticalities, strip
passing/neighbor tones, weight metrically strong notes + bass) — the problem
human When-in-Rome annotators solve. Off-the-shelf `romanNumeralFromChord` over
slices/measures is not sufficient. `raw/` is not cheaply convertible.

---

## 7. Path B — vocabulary extension for halfdim / dim7 (viable)

To make dim7 `{0,3,6,9}` and halfdim `{0,3,6,10}` **retain as themselves**
(rather than collapse to dim triad), add them as distinct types:

1. `train_full_modes.py`: `N_TYPES` 12 → 14; add templates 12 = HalfDim
   `{0,3,6,10}`, 13 = FullDim7 `{0,3,6,9}`.
2. Converters: repoint ø7 → 12, °7 → 13 (WIR `viiø7`/`vii°7` + choco halfdim).
3. Retrain; add `{12:5, 13:5}` to `completion_bonus` for jazz/funk.
4. Verify isolated retention: `C dim7 → C dim7`, `C m7b5 → C m7b5`.

**Viable regardless of prior** — the mechanism is template-uniqueness (Aug
retains at ~0.1% by the same logic). WIR alone supplies ~0.08% (halfdim) /
~0.14% (dim7) of the combined corpus; jazz repointing adds more. Prior is not
the constraint; a unique template is.

---

## 8. Synthetic corpus — already tried, replaced (harmonize_todo issue #4)

`train_full_modes.py --corpus synth` (legacy default) trains on
`tymoczko_code/Code/First step/synth_data` (Tymoczko "Geometry of Music",
**1144 songs, single script**). Resulting weights: `*_synth_gold.*`.

`docs/harmonize_todo.md` issue #4 ("Synthetic corpus limits harmonic
vocabulary", status **OPEN**) documents the verdict:

> "The single biggest lever for `pchange` quality. The training corpus is 1144
> synthetic .ntc files generated from a single script. This means: **no real
> voice-leading data, no modulation patterns beyond what the script encodes,
> no genre diversity** (jazz ii-V-I, classical deceptive cadences). Real
> harmonic diversity requires a richer corpus. **This is the prerequisite for
> any meaningful retrain.**"

The project moved to real corpora (t5harmony, choco, ireal, chordonomicon) for
this reason. **Synthetic helps `pnote` if balanced (sharp chord-tone profiles,
matching the contour technique) but `pchange` (transitions) needs real
voice-leading diversity that a single script cannot encode.** A new synthetic
would only beat the old one if rebuilt as a rich multi-genre generator — i.e.
hand-coding what real corpora provide for free.

---

## 9. Open decisions

- **halfdim/dim7 retention:** Path B (§7) is the only mechanism that gives them
  distinct identity. Data-only (WIR / synthetic) does not — types must exist
  with unique templates.
- **`TONALITY_COVERAGE.md` corrections needed:** the Chord Vocabulary table
  mislabels type 9/10 as HalfDim/FullDim (they are Maj9/Min9, §1); and the
  "rare types not retainable via completion_bonus" Limitations bullet added
  2026-07-03 is inaccurate (dim/sus4/aug DO retain; only dim7/halfdim collapse,
  §3).
- **Revert state (2026-07-03):** the WIR retrain experiment was reverted
  (weights restored to HEAD, WIR removed from `corpus_combined`,
  `corpus_when_in_rome/` deleted). `music21` was installed in `.venv_dd` for
  the §6 probe.
