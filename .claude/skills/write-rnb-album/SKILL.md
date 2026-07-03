---
name: write-rnb-album
description: Generate R&B tracks — slow-jam / quiet-storm (lush 7th/9th harmony, neo_soul profile) and Pop R&B (triadic I-V-vi-IV, pop profile). Uses CoupledHMMHarmonizer with chord-tone-contour harmony and manual MixingDesk/MasteringDesk. Rhodes (PianoComp), walking/electric bass, funk/hiphop kit, clean guitar, sub pad, solo-melody lead.
---

# Write R&B Album

Use this skill for **slow-jam / quiet-storm R&B** (D'Angelo, Sade, early Erykah) and **Pop R&B** (modern radio R&B). Uses **CoupledHMMHarmonizer** + **chord-tone-contour harmony** + **manual MixingDesk/MasteringDesk**.

## 1. Two flavors, two profiles

| Flavor | Harmony | Profile | `completion_bonus` | Key |
|---|---|---|---|---|
| **Slow jam** | lush m7 / dom7 / 9ths | `neo_soul` | `5.0` uniform + low coupling + `extended_chord_penalty=0.0` (lush 9ths) | Dorian (e.g. Eb) |
| **Pop R&B** | clean triads, catchy | `pop` | `0.0` (no 7th retention — pure triads) | Major (e.g. Ab) |

- `neo_soul` rewards **all** 7th types uniformly and lets extensions (9ths) color the voicings — the warm, jazzy R&B sound.
- `pop` gives **clean triads only**; spelled 7ths collapse to triads. Correct for bright pop-R&B, wrong if you want 7th color.
- Don't confuse this with the older `write-rnb-soul-album` skill, which uses a different pipeline (`HMM3Harmonizer` + `produce_track`); this skill uses the proven `CoupledHMMHarmonizer` + manual mix.

## 2. Chord-tone contour technique

Spell each bar's target chord as its chord-tone arpeggio so the profile retains the exact quality. **Slow jam** (Eb Dorian i–iv–i–V7 loop, m7+dom7):
```python
KEY = Scale(root=3, mode=Mode.DORIAN)          # Eb Dorian
FORM = ["Im7","IVm7","Im7","V7"]
ARP  = {"Im7":[3,6,10,1], "IVm7":[8,11,3,6], "V7":[10,2,5,8]}  # Ebm7 / Abm7 / Bb7
# config=harmonizer_profile("neo_soul")
```
**Pop R&B** (Ab major I–V–vi–IV axis, triads):
```python
KEY = Scale(root=8, mode=Mode.MAJOR)           # Ab major
FORM = ["I","V","vi","IV"]
ARP  = {"I":[8,0,3], "V":[3,7,10], "vi":[5,8,0], "IV":[1,5,8]}  # Ab / Eb / Fm / Db
# config=harmonizer_profile("pop")
```
See §2 of `write-blues-album` for the full `make_chords()` contour builder (identical pattern; contour base must be a multiple of 12).

## 3. Required imports + pipeline

```python
import random, sys, warnings
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore"); random.seed(91)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi

def _mix(raw, bpm, gains, lufs=-16.0):
    desk = MixingDesk(niche_cfg={}); desk.track_gains.update(gains)
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=lufs).apply_mastering(mixed)  # tuple
    return mastered
```

## 4. GM programs

`EPIANO=4` (Rhodes), `ELEC_BASS=33`, `FRETBASS=35`, `CLEAN_GUITAR=27`, `SYNTH_PAD=88`, `LEAD_SYNTH=85`, `TRUMPET=56`, `DRUMS=0`.

## 5. Generators (verified kwargs)

```python
rhodes = PianoCompGenerator(
    GeneratorParams(density=0.28, key_range_low=48, key_range_high=72),
    comp_style="jazz", voicing_type="rootless", accent_pattern="syncopated", chord_density=0.50,
).render(chords, key, dur)                       # comp_style ∈ {jazz, pop, bossa, waltz}
bass = WalkingBassGenerator(
    GeneratorParams(density=0.50, key_range_low=28, key_range_high=40),
    approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.56,
).render(chords, key, dur)
drums = DrumKitPatternGenerator(
    GeneratorParams(density=0.07),
    style="funk", groove_swing=0.56, fill_frequency=0.06, auto_fills=True,
).render(chords, key, dur)                       # "hiphop" for modern pop-R&B backbeat
ghosts = GhostNotesGenerator(
    GeneratorParams(density=0.03),
    target="snare", pattern="jazz", ghost_velocity=26, ghost_density=0.35,
).render(chords, key, dur)
guitar = BluesLickGenerator(
    GeneratorParams(density=0.18, key_range_low=50, key_range_high=70),
    lick_style="standard", rest_probability=0.60, bend_probability=0.12,
).render(chords, key, dur)                       # sparse guitar fills
pad = AmbientPadGenerator(
    GeneratorParams(density=0.10, key_range_low=36, key_range_high=60),
    voicing="spread", overlap=0.3,
).render(chords, key, dur)                       # voicing ∈ {open, spread}
lead = SoloMelodyGenerator(
    GeneratorParams(density=0.20, key_range_low=58, key_range_high=79),
    style="blues_lick", blues_notes=True, chromaticism=0.30, vibrato_depth=0.5,
).render(chords, key, dur)                       # style default "blues_lick"; smooth R&B lead
```

**Gradual build** — gate a lead to enter after N bars:
```python
def _gate(notes, start_at):
    kept = [n for n in notes if getattr(n, "start", 0.0) >= start_at]
    return kept if kept else notes
lead = _gate(SoloMelodyGenerator(...).render(chords, key, dur), start_at=8 * bars_per_chord)
```

## 6. Subgenres

| Subgenre | Key | BPM | Profile | Loop | LUFS | Example |
|---|---|---|---|---|---|---|
| Slow jam / quiet storm | Eb Dorian | 74 | `neo_soul` | i-iv-i-V (m7+dom7) | -16 | `scripts/albums/rnb/slow_jam.py` |
| Pop R&B | Ab major | 98 | `pop` | I-V-vi-IV (triads) | -14 | `scripts/albums/rnb/pop_rnb.py` |
| Bedroom R&B | F minor | 70 | `lofi` | diatonic 7th loop | -18 | — |

## 7. Pitfalls

| Issue | Fix |
|---|---|
| 7ths/9ths collapse to triads in slow jam | Use `neo_soul` (not `pop`). Pop has `completion_bonus=0`. |
| Pop R&B sounds too jazzy/busy | Use `pop` profile + triad contour (3 notes/bar), not 7ths. |
| Track transposed unexpectedly | Contour base must be a multiple of 12. |
| Lead plays continuously, no space | Use `BluesLickGenerator` (has `rest_probability`) for the lead, or gate it; `SoloMelodyGenerator` runs continuous. |
| `MasteringDesk` crash | Returns tuple `(mastered, cc)` — unpack. |
| Stale kwargs | Use `voicing_type`/`comp_style`/`approach_style` (verified), not the `voicing_style`/`style="walking"` seen in older docs. |
