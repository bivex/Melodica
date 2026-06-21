# TheoryTab Corpus

Real pop/rock/jazz lead-sheet data converted from the
[wayne391/lead-sheet-dataset](https://github.com/wayne391/lead-sheet-dataset)
(Hooktheory TheoryTab export) into the `.ntc2` format consumable by the HMM
trainer (`scripts/generators/train_full_modes.py`).

This corpus replaces the synthetic-only training data with **real harmonic
practice** — actual melodies with actual chord progressions from 11,000+
popular songs. It is the single biggest lever for `pchange` quality (see
`docs/harmonize_todo.md` issue #4).

## Status

This directory currently contains a **sample** (15 songs, 816 beats) converted
from the lead-sheet-dataset repo's bundled sample. The **full corpus**
(~11,000 songs, ~4.9 GB) requires a manual browser download — see below.

## Format (.ntc2)

One line per beat:

```
<beat> <meter> <key_root> <key_mode> [<chord_root> <chord_type> <bass>] [<pc>, ...]
```

Example:

```
0.0 4/4 6 minor [6 0 6] [6]
1.0 4/4 6 minor [6 0 6] [4, 6]
```

- `beat` — beat index (0.0, 1.0, 2.0, ...)
- `meter` — time signature, e.g. `4/4`
- `key_root` — tonic pitch class (0-11)
- `key_mode` — `major` or `minor`
- `[chord_root chord_type bass]` — the chord active on this beat:
  - `chord_root` — chord root pc (0-11)
  - `chord_type` — Melodica type index (0=Maj, 1=Min, 2=Dim, 3=Aug, 4=sus2,
    5=sus4, 6=Maj7, 7=Min7, 8=Dom7, 9=Maj9, 10=Min9, 11=Add9), inferred from
    the chord's pitch-class composition
  - `bass` — bass note pc (for inversions)
- `[pc, ...]` — melody pitch classes present on this beat (the legacy binary
  pc field; this is what the trainer reads)

The trainer (`load_ntc_songs`) reads the melody from the **last** bracket,
ignoring the chord/key/meter fields (which are preserved for future
structured-field training). Legacy `.ntc` files have only one bracket, so
they still load correctly.

## Getting the full corpus

The full dataset lives on Google Drive:
- **MIDI (11 MB):** https://drive.google.com/file/d/1K1t8L9IRTHnQ1ozRIMRGEyxk_yhN6kLr/
- **Full event data (4.9 GB):** https://drive.google.com/file/d/13iB5Brk1hypKsw9TSf8_d4Ka3xU0XmFZ/

Google Drive blocks programmatic download of large files behind a virus-scan
confirmation page, so `gdown`/`curl` fail. Download via browser, then:

```bash
# Clone the repo (for the converter + sample)
git clone https://github.com/wayne391/lead-sheet-dataset.git /tmp/lead-sheet-dataset

# Replace the sample event/ dir with the full one from the downloaded archive
unzip theorytab_event.zip -d /tmp/lead-sheet-dataset/datasets/

# Convert the full corpus
python3 scripts/generators/convert_theorytab.py \
    --src /tmp/lead-sheet-dataset/datasets/event \
    --dst melodica/harmonize/corpus_theorytab \
    --analyze
```

## Converter

`scripts/generators/convert_theorytab.py` — converts `*_symbol_key.json`
files (the original-key, chord-symbol notation) into `.ntc2`. Key design
decisions:

- **Chord type inferred from `composition` (pitch classes), NOT from
  TheoryTab's `chord_type` field.** Empirical inspection showed TheoryTab's
  `chord_type` is a coarse category, not a specific quality
  (`chord_type=5` covers Maj, Min, AND sus2). The chord's actual intervals
  relative to its root are the ground truth.
- **Section names preserved in filenames** (verse/chorus/bridge) to avoid
  collisions when one song has multiple sections.
- **Backward-compatible loader** — `load_ntc_songs` now reads `.ntc2`
  (melody = last bracket) while still reading legacy `.ntc`.

## Validation

Run `--analyze` to see the chord-type and key distribution. The sample
corpus shows realistic pop/rock proportions:

- Maj 49%, Min7 19%, Min 11%, Dom7 5.4%, sus2 5.3%
- (vs. the synthetic corpus's over-representation of extended/sus chords)

This is exactly the diversity improvement called for in `harmonize_todo.md`
#4 (synthetic corpus limits vocabulary).
