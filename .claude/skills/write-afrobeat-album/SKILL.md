---
name: write-afrobeat-album
description: Generate Afrobeat / Afropop tracks (Fela-style dom7 vamps, layered percussion, ostinato guitar, horn stabs). Uses CoupledHMMHarmonizer with funk profile (dom7+min7) for the dom7 vamps + chord-tone contour, and manual MixingDesk/MasteringDesk. AfrobeatsGenerator, AfroPercussionGenerator, Arpeggiator (ostinato), BrassSection, WalkingBass, PianoComp.
---

# Write Afrobeat Album

Use this skill for **Afrobeat** (Fela Kuti — extended dom7 vamps, layered percussion, horn riffs) and **Afropop** (Burna Boy / Wizkid — more produced). Uses **CoupledHMMHarmonizer** + **funk profile** + **chord-tone contour** + **manual MixingDesk/MasteringDesk**, with the dedicated `AfrobeatsGenerator` / `AfroPercussionGenerator`.

## 1. Why `funk` profile

Afrobeat is **dom7-vamp based** (F7 – Bb7 – C7, bluesy I7–IV7–V7). The `funk` profile (`completion_bonus={8:5.0, 7:4.0}`, dom7+min7) retains the dom7s spelt in the contour — exactly the same mechanism as minor blues. The dom7s are chromatic to a major key (F7's ♭7 Eb ∉ F major), but the **contour forces them** despite `key_coupling`. (chord-type codes: 7=min7, 8=dom7.)

## 2. Chord-tone contour — dom7 vamp

```python
KEY = Scale(root=5, mode=Mode.MAJOR)            # F major (afrobeat classic); dom7s are chromatic, forced by contour
FORM = ["I7","IV7","I7","V7"]                   # 4-bar vamp, repeat
ARP  = {"I7":[5,9,0,3], "IV7":[10,2,5,8], "V7":[0,4,7,10]}  # F7 / Bb7 / C7
# config=harmonizer_profile("funk")
# contour builder identical to write-blues-album §2; base must be a multiple of 12
```
Expected output: `5:7 10:7 5:7 0:7` = F7–Bb7–F7–C7, **48/48 dom7 retained**.

## 3. Required imports + pipeline

```python
import random, sys, warnings
from pathlib import Path
REPO = Path(__file__).resolve().parents[3]; sys.path.insert(0, str(REPO))
warnings.filterwarnings("ignore"); random.seed(67)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.generators import GeneratorParams
from melodica.generators.afrobeats import AfrobeatsGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
from melodica.midi import export_multitrack_midi

def _mix(raw, bpm, gains, lufs=-15.0):
    desk = MixingDesk(niche_cfg={}); desk.track_gains.update(gains)
    mixed = desk.apply_mixing(raw, [], int(bpm))
    mastered, _cc = MasteringDesk(target_lufs=lufs).apply_mastering(mixed)  # tuple
    return mastered
```

## 4. GM programs

`DRUMS=0` (percussion → channel 10), `ELEC_BASS=33`, `EPIANO=4` (Rhodes), `CLEAN_GUITAR=27`, `BRASS=62` (brass section), `NYLON_GUITAR=24`, `SAX=66`.

## 5. Generators (verified kwargs)

```python
groove = AfrobeatsGenerator(
    GeneratorParams(density=0.50),
    variant="afrobeats", log_drum_density=0.60, shaker_pattern="sixteenth",
    include_piano=False, bounce_amount=0.60, percussion_layer=True,
).render(chords, key, dur)                        # full afrobeats groove (log drums + shaker + percussion)
perc = AfroPercussionGenerator(
    GeneratorParams(density=0.50),
    ensemble="west_african", include_pitched=False, call_response=True, swing=0.55,
).render(chords, key, dur)                        # extra west-african percussion layer
bass = WalkingBassGenerator(
    GeneratorParams(density=0.60, key_range_low=28, key_range_high=43),
    approach_style="mixed", add_chromatic_passing=True, swing_eighth_ratio=0.56,
).render(chords, key, dur)                        # repetitive pocket bass
keys = PianoCompGenerator(
    GeneratorParams(density=0.30, key_range_low=48, key_range_high=72),
    comp_style="pop", voicing_type="close", accent_pattern="syncopated", chord_density=0.55,
).render(chords, key, dur)
guitar = ArpeggiatorGenerator(
    GeneratorParams(density=0.55, key_range_low=50, key_range_high=67),
    pattern="up", note_duration=0.5, octaves=1,
).render(chords, key, dur)                        # the classic 2-chord guitar ostinato
horns = BrassSectionGenerator(
    GeneratorParams(density=0.14, key_range_low=54, key_range_high=72),
    articulation="hit", voicing="closed", intensity=0.70, divisi_count=3,
).render(chords, key, dur)                        # horn stabs / riffs
```

**Layering** — afrobeat lives on layered percussion. Use `AfrobeatsGenerator` (set `include_piano=False` so it stays pure percussion on the drum channel) **plus** `AfroPercussionGenerator` for the second percussion layer, then bass/keys/guitar/horns on top. Both percussion generators → GM program 0.

## 6. Subgenres

| Subgenre | Key | BPM | Profile | Vamp | LUFS | Example |
|---|---|---|---|---|---|---|
| Afrobeat (Fela) | F major | 108 | `funk` | I7-IV7-I7-V7 (dom7) | -15 | `scripts/albums/afro/afrobeat.py` |
| Afropop (modern) | Ab / Db major | 102–112 | `funk` or `pop` | shorter vamps, brighter | -14 | — |
| Afro-house | A minor | 120 | `lofi` | diatonic 7th loop | -14 | (see `afro_house.py` generator) |

## 7. Pitfalls

| Issue | Fix |
|---|---|
| Dom7 vamp came out as triads | Use `funk` profile (not `pop`). Spell the dom7 tones in the contour (`{8:5}` only fires when present). |
| Pitched notes on the drum track | Set `AfrobeatsGenerator(include_piano=False)` and `AfroPercussionGenerator(include_pitched=False)` so percussion stays on channel 10. |
| Too much percussion clutter | Two percussion generators is intentional (layered), but lower `density` / `log_drum_density` if it overpowers the bass/horns. |
| Horns inaudible | `BrassSectionGenerator` at low `density` (~0.14) for stabs; raise `intensity`. |
| Track transposed | Contour base must be a multiple of 12. |
| `MasteringDesk` crash | Returns tuple `(mastered, cc)` — unpack. |
| Stale kwargs from other skill docs | The kwargs above are verified. Other docs' `voicing_style`/`style="walking"` raise ValueError — use `voicing_type`/`approach_style`. |
