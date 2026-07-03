---
name: write-blues-album
description: Generate blues tracks — major 12-bar dom7 blues (I7-IV7-V7) and minor blues (Im7-IVm7-V7), plus jazz-blues and blues ballads. Uses CoupledHMMHarmonizer with chord-tone-contour harmony and manual MixingDesk/MasteringDesk. CRITICAL profile rule: blues profile (dom7-only) for major blues, funk profile (dom7+min7) for minor blues. WalkingBass, PianoComp, BluesLick, SaxSolo, brushed drums.
---

# Write Blues Album

Use this skill for 12-bar blues — **major dom7 blues** (I7–IV7–V7) and **minor blues** (Im7–IVm7–V7) — plus jazz-blues and slow blues ballads. Uses **CoupledHMMHarmonizer** with **chord-tone-contour harmony** + **manual MixingDesk/MasteringDesk**.

## 1. The decisive choice: `blues` vs `funk` profile

This is the single most important decision, and it is **structural, not a tuning knob**. The profile's `completion_bonus` determines which 7th qualities the harmonizer can retain:

| Blues type | Form | Profile | `completion_bonus` |
|---|---|---|---|
| **Major blues** | I7 – IV7 – V7 (all dom7) | `blues` | `{8: 5.0}` — **dom7-only** |
| **Minor blues** | Im7 – IVm7 – V7 (m7 + dom7) | `funk` | `{8: 5.0, 7: 4.0}` — **dom7+min7** |
| Jazz-blues | ii-V-I / secondary doms | `jazz` | `5.0` — uniform 7th |

- The **`blues` profile is dom7-only**. It structurally **cannot retain m7** — on a minor blues, Im7/IVm7 collapse to min triads or get substituted by bIII/bVI diatonics (Ebmaj/Abmaj) whose tones are subsets of the m7 contour. **Never use `blues` for minor blues.**
- The **`funk` profile** rewards dom7 AND min7. It is the correct profile for minor blues.
- **Chord-type codes: type 7 = min7, type 8 = dom7.**

## 2. Chord-tone contour technique (how to force the harmony)

The harmonizer won't reliably emit 7ths from a plain scale-degree melody. Instead **spell each bar's target chord as its actual chord-tone arpeggio** in the contour. The completion_bonus then retains it, and the **pitch-class set disambiguates quality** — Cm7 `[0,3,7,10]` can only complete to m7, never dom7 `[0,4,7,10]`.

```python
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.types import NoteInfo, Scale, Mode

# MAJOR blues: dom7 arpeggios, in C.   (pc = pitch class)
FORM = ["I","I","I","I","IV","IV","I","I","V","IV","I","V"]
DOM7 = {"I":[0,4,7,10], "IV":[5,9,0,3], "V":[7,11,2,5]}   # C7 / F7 / G7

def make_chords(key, dur, bars_per_chord=4.0):
    total = int(dur / bars_per_chord)
    h = CoupledHMMHarmonizer(beam_width=14, chord_change="bars",
                             config=harmonizer_profile("blues"))   # <- "funk" for MINOR blues
    contour = []
    for bar in range(total):
        for j, pc in enumerate(DOM7[FORM[bar % 12]]):
            contour.append(NoteInfo(pitch=48 + pc,                # base MUST be a multiple of 12
                                    start=bar*bars_per_chord + j, duration=1.0, velocity=60))
    return h.harmonize(contour, key, dur)
```

**Minor blues** — swap profile to `"funk"` and the arpeggios to m7/dom7:
```python
KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)            # C minor
FORM = ["Im7","Im7","Im7","Im7","IVm7","IVm7","Im7","Im7","V7","IVm7","Im7","V7"]
ARP = {"Im7":[0,3,7,10], "IVm7":[5,8,0,3], "V7":[7,11,2,5]}  # Cm7 / Fm7 / G7
# config=harmonizer_profile("funk")
```

## 3. Required imports + pipeline

```python
import random, sys, warnings
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore"); random.seed(13)

from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi

def _mix(raw, bpm, gains):
    desk = MixingDesk(niche_cfg={}); desk.track_gains.update(gains)
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=-18.0).apply_mastering(mixed)  # returns a TUPLE
    return mastered

# export_multitrack_midi(mixed, out_path, bpm=BPM, key=KEY, instruments={"Bass":32, ...})
```

## 4. GM programs

`ACOUSTIC_BASS=32`, `PIANO=0`, `EPIANO=4` (Rhodes), `TENOR_SAX=66`, `JAZZ_GUITAR=26`, `DRUMS=0` (drums auto-assigned to channel 10).

## 5. Generators (verified kwargs)

```python
bass = WalkingBassGenerator(
    GeneratorParams(density=0.65, key_range_low=28, key_range_high=40),
    approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.67,
).render(chords, key, dur)
comp = PianoCompGenerator(
    GeneratorParams(density=0.45, key_range_low=48, key_range_high=72),
    comp_style="jazz", voicing_type="shell", accent_pattern="2_4", chord_density=0.6,
).render(chords, key, dur)                       # voicing_type ∈ {shell, rootless, close}
lead = BluesLickGenerator(
    GeneratorParams(density=0.40, key_range_low=48, key_range_high=72),
    lick_style="standard", rest_probability=0.45, bend_probability=0.15,
).render(chords, key, dur)
sax  = SaxSoloGenerator(
    GeneratorParams(density=0.40, key_range_low=54, key_range_high=84),
    style="cool", vibrato_depth=0.5, chromaticism=0.4, blues_notes=True,
).render(chords, key, dur)
ghosts = GhostNotesGenerator(
    GeneratorParams(density=0.04),
    target="snare", pattern="jazz", ghost_velocity=30, ghost_density=0.4,
).render(chords, key, dur)                       # brushed snare ghost notes
drums = DrumKitPatternGenerator(
    GeneratorParams(density=0.10),
    style="jazz", groove_swing=0.67, fill_frequency=0.12, auto_fills=True,
).render(chords, key, dur)                       # style ∈ {rock, jazz, latin, funk, hiphop}
```

## 6. Subgenres

| Subgenre | Key | BPM | Profile | Form | Example script |
|---|---|---|---|---|---|
| Major shuffle | C major | 120 | `blues` | I7-IV7-V7 dom7 | `scripts/albums/jazz/blues.py` |
| Minor blues ballad | C minor | 62 | `funk` | Im7-IVm7-V7 | `scripts/albums/jazz/evening_blues.py` |
| Jazz-blues | F/Bb major | 130 | `jazz` | ii-V-I + blues form | — |

## 7. Pitfalls

| Issue | Fix |
|---|---|
| Minor blues Im7/IVm7 collapse to triads | Use `funk` profile, not `blues`. `blues` is dom7-only and cannot retain m7. |
| Whole track transposed by a few semitones | Contour base `pitch=` must be a **multiple of 12** (48, 60). `50 + pc` shifts every pc by +2 (50 mod 12 = 2). |
| V7 (G7) missing in major blues | The dom7 must be **spelled in the contour** (`{8:5}` fires only when the dom7 tones are present). A bare scale-degree melody won't trigger it. |
| `MasteringDesk().apply_mastering()` crashes | It returns a **tuple** `(mastered, cc)` — unpack it. |
| Drums silent | Use `DrumKitPatternGenerator` (ride/snare/kick) **AND** `GhostNotesGenerator` (brushes). |
| Wrong generator kwargs | The kwargs above are verified against the current API. Older skill docs (`voicing_style`, `style="walking"`, `use_passing_tones`) are **stale and will raise ValueError** — use `voicing_type`, `approach_style`, `add_chromatic_passing`. |
