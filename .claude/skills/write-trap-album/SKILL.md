---
name: write-trap-album
description: Generate trap / melodic trap tracks (dark minor, 808 bass, hat rolls, half-time feel). Uses CoupledHMMHarmonizer with chord-tone-contour harmony and manual MixingDesk/MasteringDesk. Bass808Sliding, TrapDrums, HiHatStutter generators. pop profile for triadic minor trap, funk profile (dom7+min7) when you want transition dominants. Static axis forms or through-composed multi-section forms.
---

# Write Trap Album

Use this skill for **melodic trap** (Lil Baby, Roddy Ricch, Drake trap-soul), **drill**, and dark minor trap. Half-time feel. Uses **CoupledHMMHarmonizer** + **chord-tone-contour harmony** + **manual MixingDesk/MasteringDesk**, with dedicated trap generators (`Bass808SlidingGenerator`, `TrapDrumsGenerator`, `HiHatStutterGenerator`).

## 1. Profile choice: `pop` (triadic) vs `funk` (transitions)

Trap harmony is minimal, so the choice is about **what color you want**, not complexity:

| Goal | Profile | Result |
|---|---|---|
| **Static dark trap**, clean minor triads (Cm–Ab–Eb–Bb) | `pop` | major triads intact, no 7th color |
| **Melodic trap with transitions** (secondary dominants G7/Bb7 + dark m7 sonority) | `funk` | m7 + dom7 retained, but **major triads get absorbed into m7** (see pitfalls) |

- `pop` = `completion_bonus=0` → clean triads only.
- `funk` = `{8:5, 7:4}` → retains dom7 (type 8) and min7 (type 7).
- **Trade-off (important):** the `funk` min7 bonus **captures spelled major triads into the m7 a fifth below**, because a major triad's tones are a subset of that m7 (Ab `[8,0,3]` ⊂ Fm7 `[5,8,0,3]`). So with `funk`, expect a lush all-minor/m7 texture with dom7 tension chords, NOT major/minor contrast. For major/minor contrast, use `pop` (but you lose dom7 transitions). You cannot cleanly have both.

## 2. Chord-tone contour — static axis vs through-composed

**Static axis** (C minor i–♭VI–♭III–♭VII, the rap/trap axis), repeated:
```python
KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)
FORM = ["i","bVI","bIII","bVII"]                         # loop these 4 bars
ARP  = {"i":[0,3,7], "bVI":[8,0,3], "bIII":[3,7,10], "bVII":[10,2,5]}  # Cm / Ab / Eb / Bb
# config=harmonizer_profile("pop")
```

**Through-composed** (interesting transitions): write a longer `FORM` with no exact repeat — mix in secondary dominants (`V7`/`V7iv`) and a Neapolitan (`bII`) across contrasting sections. Use the `funk` profile so the dom7 transitions retain:
```python
FORM = [
  # A: dark axis (0–15)
  "i","bVI","bIII","bVII", "i","bVI","bIII","bVII", "i","bVI","bIII","V7", "i","iv","V7iv","i",
  # T: chromatic transition (16–23)
  "iv","V7","i","bVI", "bII","V7","i","V7iv",
  # B: lift (24–35) / O: cadential outro (36–47) ...
]
ARP = {"i":[0,3,7,10], "bVI":[8,0,3], "bIII":[3,7,10], "bVII":[10,2,5],
       "iv":[5,8,0,3], "V7":[7,11,2,5], "V7iv":[10,2,5,8], "bII":[1,5,8]}
# config=harmonizer_profile("funk")
```
(See `scripts/albums/trap/melodic_trap_180.py` for the full 48-bar worked example.)

Only spell chord types `funk` can anchor: **min7 / dom7 / major triad**. Avoid maj7 and half-dim (ø) — `funk`'s bonus set can't pin them and they collapse ambiguously.

## 3. Required imports + pipeline

```python
import random, sys, warnings
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore"); random.seed(41)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi

def _mix(raw, bpm, gains, lufs=-14.0):
    desk = MixingDesk(niche_cfg={}); desk.track_gains.update(gains)
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=lufs).apply_mastering(mixed)  # tuple
    return mastered
```

## 4. GM programs

`SYNTH_BASS=38` (808), `DRUMS=0`, `SYNTH_PAD=88`, `EPIANO=4` (Rhodes, to make chords audible), `LEAD_SYNTH=85`, `CLEAN_GUITAR=27`.

## 5. Generators (verified kwargs)

```python
bass808 = Bass808SlidingGenerator(
    GeneratorParams(density=0.40, key_range_low=24, key_range_high=40),
    pattern="trap_basic", slide_probability=0.50, octave_range=2,
).render(chords, key, dur)                        # 808 sub-bass with pitch slides
drums = TrapDrumsGenerator(
    GeneratorParams(density=0.40),
    variant="standard", hat_roll_density=0.60, kick_pattern="standard",
    open_hat_probability=0.20, groove_swing=0.50,
).render(chords, key, dur)                        # full trap beat (kick/snare/hats w/ rolls)
hats = HiHatStutterGenerator(
    GeneratorParams(density=0.25),
    pattern="trap_eighth", roll_density=0.40, open_hat_probability=0.15,
).render(chords, key, dur)                        # extra hat rolls (optional; TrapDrums already has hats)
comp = PianoCompGenerator(
    GeneratorParams(density=0.26, key_range_low=48, key_range_high=72),
    comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.45,
).render(chords, key, dur)                        # makes chord changes audible under 808+drums
pad = AmbientPadGenerator(
    GeneratorParams(density=0.08, key_range_low=36, key_range_high=60),
    voicing="spread", overlap=0.4,
).render(chords, key, dur)
lead = SoloMelodyGenerator(
    GeneratorParams(density=0.22, key_range_low=60, key_range_high=84),
    style="blues_lick", blues_notes=True, chromaticism=0.30, vibrato_depth=0.3,
).render(chords, key, dur)                        # autotune-style melodic hook
```

## 6. Subgenres

| Subgenre | Key | BPM | Profile | Form | LUFS | Example |
|---|---|---|---|---|---|---|
| Melodic trap (static) | C minor | 140 | `pop` | i-♭VI-♭III-♭VII axis | -14 | `scripts/albums/trap/melodic_trap.py` |
| Melodic trap (through-composed) | C minor | 180 | `funk` | 48-bar 4-section, transitions | -14 | `scripts/albums/trap/melodic_trap_180.py` |
| Drill | Cm / Fm | 140–145 | `pop` | minor axis, sliding 808 | -14 | — |

> BPM is the **true** tempo; trap is felt half-time (140 ≈ 70, 180 ≈ 90). Hat rolls get denser at higher BPM — lower `hat_roll_density` if it clutters.

## 7. Pitfalls

| Issue | Fix |
|---|---|
| Major triads (Ab/Eb/Bb) turned into m7 | That's `funk`'s min7 bonus capturing them (Ab ⊂ Fm7). Use `pop` if you want major/minor contrast; accept all-minor if you want dom7 transitions. |
| Neapolitan ♭II (Db) disappeared | Same capture (Db `[1,5,8]` ⊂ Bbm7). Only spell chords `funk` can anchor (min7/dom7/maj triad); avoid maj7 & ø. |
| Hats too busy at high BPM | `TrapDrumsGenerator` already includes hats — skip `HiHatStutterGenerator`, or lower `hat_roll_density` / `roll_density`. |
| Chord changes inaudible | Add a `PianoCompGenerator` (Rhodes) comp track so harmony is heard under the 808+drums. |
| Track transposed | Contour base must be a multiple of 12. |
| `MasteringDesk` crash | Returns tuple `(mastered, cc)` — unpack. |
