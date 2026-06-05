---
name: write-jazz-album
description: Generate jazz albums (bebop, swing, cool jazz, Latin jazz, modal jazz, blues, stride, boogie-woogie). Uses CoupledHMMHarmonizer with manual MixingDesk/MasteringDesk pipeline. WalkingBass, PianoComp, SaxSolo, StridePiano, Montuno, BluesLick, BoogieWoogie generators.
---

# Write Jazz Album

Use this skill for bebop, swing, cool jazz, hard bop, Latin jazz, modal jazz, blues, stride piano, and boogie-woogie albums. Uses **CoupledHMMHarmonizer** for harmony and **manual mixing** with `MixingDesk` + `MasteringDesk`.

## 1. When to Use

- Traditional / swing / big band jazz
- Bebop / hard bop / cool jazz
- Modal jazz (Kind of Blue style)
- Latin jazz / Afro-Cuban jazz
- Blues / jazz-blues crossover
- Stride piano / boogie-woogie
- Jazz ballads and slow standards

## 2. Required Imports

```python
import random
import sys
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica import types
from melodica.theory import Quality
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality, KeyLabel, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.swing import SwingGenerator
from melodica.generators.stride_piano import StridePianoGenerator
from melodica.generators.montuno import MontunoGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.boogie_woogie import BoogieWoogieGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.bass import BassGenerator
from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.composer.transformers import spiceup
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
```

## 3. Jazz Scales & Modes

```python
# Bebop / Hard Bop
Bb_BEBOP_DOM = Scale(root=10, mode=Mode.BEBOP_DOMINANT)
F_BEBOP_DOM  = Scale(root=5,  mode=Mode.BEBOP_DOMINANT)
C_BEBOP_DOM  = Scale(root=0,  mode=Mode.BEBOP_DOMINANT)

# Modal Jazz
D_DORIAN   = Scale(root=2, mode=Mode.DORIAN)     # So What
C_DORIAN   = Scale(root=0, mode=Mode.DORIAN)
G_DORIAN   = Scale(root=7, mode=Mode.DORIAN)

# Standard Jazz
Bb_MAJOR   = Scale(root=10, mode=Mode.MAJOR)      # Bright swing
F_MAJOR    = Scale(root=5,  mode=Mode.MAJOR)       # Classic
Eb_MAJOR   = Scale(root=3,  mode=Mode.MAJOR)       # Bluesy
C_MAJOR    = Scale(root=0,  mode=Mode.MAJOR)

# Minor / Blues
D_MINOR    = Scale(root=2, mode=Mode.NATURAL_MINOR) # Ballad
G_MINOR    = Scale(root=7, mode=Mode.NATURAL_MINOR)
C_MINOR    = Scale(root=0, mode=Mode.NATURAL_MINOR)
F_BLUES    = Scale(root=5, mode=Mode.BLUES)
Bb_BLUES   = Scale(root=10, mode=Mode.BLUES)

# Latin Jazz
A_DORIAN   = Scale(root=9,  mode=Mode.DORIAN)      # Latin feel
G_MIXOLYD  = Scale(root=7,  mode=Mode.MIXOLYDIAN)   # Montuno
```

## 4. Harmony: CoupledHMMHarmonizer

```python
def make_chords(key: Scale, dur: float, bars_per_chord: float = 4.0) -> list[ChordLabel]:
    total_bars = int(dur / bars_per_chord)
    harmonizer = CoupledHMMHarmonizer(
        beam_width=14,
        chord_change="half",     # "half" = half-note resolution (jazz standard)
    )
    # Build a sparse melody contour for harmonization
    contour = []
    degrees = key.degrees()
    for bar in range(total_bars):
        deg = degrees[bar % len(degrees)]
        contour.append(NoteInfo(
            pitch=60 + int(deg),
            start=bar * bars_per_chord,
            duration=bars_per_chord - 0.1,
            velocity=60,
        ))
    chords = harmonizer.harmonize(contour, key, dur)
    return chords
```

## 5. GM MIDI Programs

```python
PIANO       = 0    # Acoustic Grand Piano
EPIANO      = 4    # Electric Piano 1 (Rhodes)
ORGAN       = 16   # Drawbar Organ
JAZZ_GUITAR = 26   # Jazz Guitar (archtop)
ACOUSTIC_BASS = 32 # Acoustic Bass (walking)
FRETLESS    = 35   # Fretless Bass
TRUMPET     = 56
TROMBONE    = 57
SOPRANO_SAX = 64
ALTO_SAX    = 65
TENOR_SAX   = 66
BARI_SAX    = 67
CLARINET    = 71
FLUTE       = 73
VIBRAPHONE  = 11
DRUMS       = 0    # Drums use program 0 (channel assigned sequentially)
```

## 6. Register Separation

Critical for clean jazz mixes — keep generators in their own frequency bands:

| Role | Range | Pitches |
|---|---|---|
| Bass | 24–38 | Bass guitar, acoustic bass |
| Low Comp | 36–48 | Left-hand piano, stride |
| Comp | 48–67 | Piano voicings, guitar chords |
| Melody | 54–84 | Sax, trumpet, flute lead |
| Sparkle | 72–88 | Upper piano, vibraphone, flute top |

## 7. Core Generators

### Walking Bass

```python
bass = WalkingBassGenerator(
    GeneratorParams(density=0.70, key_range_low=24, key_range_high=40),
    style="walking",              # "walking", "two_feel", "half_time"
    use_passing_tones=True,
    use_approach_notes=True,
    target_notes_weight=0.3,
).render(chords, key, dur)
```

### Piano Comping

```python
comp = PianoCompGenerator(
    GeneratorParams(density=0.45, key_range_low=48, key_range_high=67),
    voicing_style="rootless",     # "rootless", "shell", "spread", "locked_hands"
    rhythm_style="syncopated",    # "syncopated", "charleston", "stride_rhythm", "four_beat"
    fill_probability=0.15,
    fill_density=0.4,
).render(chords, key, dur)
```

### Saxophone Solo

```python
sax = SaxSoloGenerator(
    GeneratorParams(density=0.55, key_range_low=54, key_range_high=84),
    style="bebop",                # "bebop", "cool", "hard_bop", "smooth"
    use_chromatic_passages=True,
    quote_probability=0.08,
    vibrato_depth=0.5,
).render(chords, key, dur)
```

### Swing Ride / Feel

```python
swing = SwingGenerator(
    GeneratorParams(density=0.40, key_range_low=48, key_range_high=84),
    swing_ratio=0.67,             # Jazz triplet swing (0.67 ≈ 2:1)
).render(chords, key, dur)
```

### Stride Piano

```python
stride = StridePianoGenerator(
    GeneratorParams(density=0.55, key_range_low=28, key_range_high=88),
    style="harlem_stride",        # "harlem_stride", "fats_waller", "james_p_johnson"
).render(chords, key, dur)
```

### Montuno (Latin Jazz)

```python
montuno = MontunoGenerator(
    GeneratorParams(density=0.50, key_range_low=60, key_range_high=84),
    clave_type="son_23",          # "rumba_23", "rumba_32", "son_23", "son_32", "none"
    octave_doubling=False,        # Keep False to avoid register masking
    syncopation_level=0.6,
).render(chords, key, dur)
```

### Blues Licks

```python
blues = BluesLickGenerator(
    GeneratorParams(density=0.50, key_range_low=48, key_range_high=72),
    lick_complexity=0.6,          # 0.0-1.0
    bend_probability=0.15,
).render(chords, key, dur)
```

### Boogie-Woogie

```python
boogie = BoogieWoogieGenerator(
    GeneratorParams(density=0.65, key_range_low=36, key_range_high=72),
    pattern="eight_to_bar",       # "eight_to_bar", "sixteen_beat", "triple_treble"
).render(chords, key, dur)
```

### Jazz Drums

```python
drums = DrumKitPatternGenerator(
    GeneratorParams(density=0.08),
    style="jazz",                 # Ride cymbal (51) + snare (38) + kick (36)
    groove_swing=0.67,           # Match jazz swing ratio
    fill_frequency=0.15,
    auto_fills=True,
).render(chords, key, dur)
```

### Brush Ghost Notes

```python
ghosts = GhostNotesGenerator(
    GeneratorParams(density=0.03),
    pattern="jazz",               # Built-in jazz brush pattern
    target="snare",
    ghost_velocity=30,
    ghost_density=0.4,
).render(chords, key, dur)
```

## 8. Mixing & Mastering

```python
def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Bass":    0.85,
        "Comp":    0.80,
        "Melody":  0.88,
        "Guitar":  0.78,
        "Drums":   0.72,
        "Ghosts":  0.55,
        "Strings": 0.68,
        "Pad":     0.55,
        "Stride":  0.82,
        "Montuno": 0.78,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    m = MasteringDesk(target_lufs=-18.0)   # Jazz sits at -18 LUFS (louder than ambient -20)
    return m.apply_mastering(mixed)
```

## 9. Track Function Pattern

```python
def _track(title: str, key: Scale, bpm: float, dur: float, builder, instruments: dict):
    chords = make_chords(key, dur)
    raw = builder(chords, key, dur)
    mixed = _mix(raw, bpm)
    out = album_dir / f"{title}.mid"
    export_multitrack_midi(mixed, instruments, int(bpm), str(out), key_label=key.name)

def main():
    global album_dir
    album_dir = Path("output/album_name")
    album_dir.mkdir(exist_ok=True, parents=True)

    _track("01_Sunny Side", Scale(root=10, mode=Mode.BEBOP_DOMINANT), 138, 64.0,
            build_sunny_side, {"Bass": ACOUSTIC_BASS, "Comp": PIANO, ...})
```

## 10. Subgenre Guide

| Subgenre | BPM | Density | Feel |
|---|---|---|---|
| Ballad | 55–75 | 0.25–0.40 | Rubato, sparse |
| Cool Jazz | 80–110 | 0.35–0.50 | Laid-back, legato |
| Bebop | 140–200 | 0.55–0.75 | Fast, dense lines |
| Hard Bop | 120–145 | 0.45–0.65 | Gospel-blues infused |
| Swing / Big Band | 120–160 | 0.45–0.60 | Driving, ensemble |
| Modal Jazz | 90–130 | 0.30–0.50 | Open, spacious |
| Latin Jazz | 100–135 | 0.45–0.65 | Syncopated, clave |
| Stride Piano | 120–160 | 0.50–0.65 | Virtuosic, rhythmic |
| Boogie-Woogie | 130–170 | 0.55–0.70 | Driving 8ths |
| Jazz-Blues | 100–135 | 0.40–0.60 | 12-bar, swinging |

## 11. Key Instrument Combinations

| Style | Lead | Comp | Bass | Drums |
|---|---|---|---|---|
| Bebop | SaxSolo (66) | PianoComp (0) | WalkingBass (32) | DrumKit jazz (0) |
| Cool Jazz | MelodyGenerator on Flute (73) | PianoComp rootless (0) | WalkingBass two_feel (32) | DrumKit jazz (0) |
| Latin Jazz | Trumpet (56) | Montuno (0) | WalkingBass (32) | DrumKit jazz (0) + Ghosts |
| Stride | StridePiano (0) | — | WalkingBass (32) | DrumKit jazz (0) |
| Blues | BluesLick (0) + Sax (66) | PianoComp shell (0) | WalkingBass (32) | DrumKit jazz (0) |
| Ballad | SaxSolo cool (66) | PianoComp spread (0) | WalkingBass half_time (35) | Ghosts jazz only |
| Boogie-Woogie | BoogieWoogie (0) | — | BassGenerator walking (32) | DrumKit jazz (0) |
| Organ Trio | MelodyGenerator (16) | PianoComp locked_hands (16) | WalkingBass (32) | DrumKit jazz (0) |

## 12. Common Pitfalls

| Issue | Fix |
|---|---|
| `Mode.HARMONIC_MINOR` not found | Use `Mode.HARM_MINOR` |
| Montuno `clave_type` error | Valid: `rumba_23`, `rumba_32`, `son_23`, `son_32`, `none` |
| `note_range_low` on GeneratorParams | Use `key_range_low` / `key_range_high` on GeneratorParams; `note_range_low`/`note_range_high` only on MelodyGenerator |
| Bass and comp overlap | Keep bass ≤38, comp ≥48 — see register table |
| Montuno octave_doubling pushes too high | Set `octave_doubling=False` |
| Drums not audible | Add both DrumKitPattern (ride+snare+kick) AND GhostNotes (brushes) |
| Swing feel missing | Set `groove_swing=0.67` on drums, `swing_ratio=0.67` on SwingGenerator |
| `CoupledHMMHarmonizer` not found | Import from `melodica.harmonize.coupled_hmm` |
| WalkingBass too busy | Lower density to 0.55, or use `style="two_feel"` |
| Jazz too quiet after mastering | Target -18 LUFS, not -20 (ambient is quieter) |

## 13. Running

```bash
python scripts/albums/jazz/album_name.py
```
