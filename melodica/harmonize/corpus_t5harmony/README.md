# t5-harmony Corpus

The primary training corpus for the HMM harmonizer — **49,803 real songs**
from the [wrkzk/t5-harmony](https://github.com/wrkzk/t5-harmony) dataset,
which scraped Hooktheory TheoryTab and tokenized the data into Roman-numeral
notation with separated melody and chord tracks.

This is the corpus that addresses `harmonize_todo.md` issue #4 (synthetic
corpus limits vocabulary). It provides **44× more songs and 133× more beats**
than the original synthetic corpus, with real harmonic practice across pop,
rock, electronic, videogame, jazz, and other genres.

## Source

- **Repository:** https://github.com/wrkzk/t5-harmony
- **Original source:** Hooktheory TheoryTab (manually-analyzed lead sheets)
- **Tokenization:** Roman-numeral notation (transposition-invariant) with
  genre, scale, rhythm, and per-bar melody/chord tokens

## Format (.ntc2)

Same `.ntc2` format as the TheoryTab corpus:

```
<beat> <meter> <key_root> <key_mode> [<chord_root> <chord_type> <bass>] [<pc>, ...]
```

All songs are normalized to tonic = C (root 0) because the source data is in
Roman-numeral notation, which is already transposition-invariant. This is
correct for HMM training: the model learns interval relationships, not
absolute keys.

## Conversion

`scripts/generators/convert_t5harmony.py` decodes the t5-harmony token format:

- **Roman numerals → absolute pitch classes:** I=tonic, ii=2nd degree minor,
  V7=dominant 7th, etc. Uses modal-aware degree offsets (MINOR, DORIAN,
  PHRYGIAN, LYDIAN, etc. all handled).
- **Chord quality inference:** from Roman-numeral case (uppercase=major-based,
  lowercase=minor-based) + suffix (7, dim, aug, sus, 9, maj7).
- **NOTE_ tokens → pitch classes:** scale degrees with octave and accidental
  modifiers (NOTE_5-1 = 5th degree one octave down).

### Bugs found and fixed during development

1. **SCALE_ token location:** in `dataset_chords.jsonl` the SCALE_ token is
   in the chords field, not the melody field. Fixed by searching both.
2. **Roman-numeral regex ordering:** the initial regex matched 'vi' as 'v'
   (V instead of VI) because alternatives weren't ordered longest-first.
   This silently mis-parsed ~half the chords. Fixed with explicit
   length-descending alternatives including b/# accidentals.

## Corpus statistics (full 49,803 songs)

- Songs: 49,803
- Total beats: 2,367,553
- Mean song length: 47.5 beats
- Chord type distribution (realistic pop/rock proportions):

| Type | Count | % |
|---|---|---|
| Major | 1,039,892 | 39.4% |
| Minor | 611,834 | 23.2% |
| Minor7 | 313,719 | 11.9% |
| Dominant7 | 231,791 | 8.8% |
| Diminished | 112,132 | 4.2% |
| Major9 | 73,150 | 2.8% |
| Minor9 | 66,833 | 2.5% |
| Add9 | 53,729 | 2.0% |
| sus4 | 52,596 | 2.0% |
| sus2 | 47,930 | 1.8% |
| Augmented | 35,613 | 1.3% |
| Major7 | 3,099 | 0.1% |

## Regenerating

```bash
# Requires the t5-harmony repo cloned to /tmp/t5-harmony
python3 scripts/generators/convert_t5harmony.py \
    --src /tmp/t5-harmony/datasets/dataset_chords.jsonl \
    --dst melodica/harmonize/corpus_t5harmony \
    --analyze
```
