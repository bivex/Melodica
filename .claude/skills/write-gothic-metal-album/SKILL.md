---
name: write-gothic-metal-album
description: Generate gothic, metal, symphonic metal, folk, and dark orchestral albums. Uses direct generators with produce_track pipeline or manual mixing/mastering. Hungarian Minor, Phrygian, and exotic scales.
---

# Write Gothic / Metal / Folk Album

Use this skill for gothic orchestral, symphonic metal, dark folk, gypsy, and albums using exotic scales (Hungarian Minor, Gypsy, Phrygian). Supports two pipelines: `produce_track()` (recommended) or manual `MixingDesk` + `MasteringDesk`.

## 1. When to Use

- Gothic / horror / vampire themed albums
- Symphonic metal / power metal
- Folk / gypsy / ethnic dance music
- Dark orchestral with heavy brass and percussion
- Albums with narrative/concept arcs

## 2. Required Imports

```python
import random
from pathlib import Path

from melodica import types
from melodica.theory import Quality
from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.solo_melody import SoloMelodyGenerator
from melodica.generators.modern_bass_2025 import ModernBass2025Generator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator, ContrabassGenerator
from melodica.generators.orchestral_brass import FrenchHornGenerator, TromboneGenerator, TrumpetGenerator
from melodica.generators.orchestral_percussion import TimpaniGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator
from melodica.generators.harp import HarpGenerator
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.composer.transformers import spiceup, serialize_canon
from melodica.harmonize.predictive import PredictiveHarmonizer
```

For manual mixing:
```python
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
```

## 3. Dark & Exotic Scales

```python
# Gothic staples
B_HUNGARIAN = Scale(root=11, mode=Mode.HUNGARIAN_MINOR)  # Classic gothic
E_PHRYGIAN  = Scale(root=4,  mode=Mode.PHRYGIAN)        # Dark tension
D_PHRYGIAN  = Scale(root=2,  mode=Mode.PHRYGIAN)        # Heavy metal
A_HARM_MIN  = Scale(root=9,  mode=Mode.HARM_MINOR)      # Neoclassical

# Metal
E_AEOLIAN   = Scale(root=4,  mode=Mode.AEOLIAN)         # Natural minor
E_DORIAN    = Scale(root=4,  mode=Mode.DORIAN)          # Power metal

# Folk / Gypsy
E_GYPSY     = Scale(root=4,  mode=Mode.GYPSY)           # Gypsy dance
A_GYPSY     = Scale(root=9,  mode=Mode.GYPSY)
D_GYPSY     = Scale(root=2,  mode=Mode.GYPSY)

# Ethereal
C_LYDIAN    = Scale(root=0,  mode=Mode.LYDIAN)          # Bright, floating
G_LOCRIAN   = Scale(root=7,  mode=Mode.LOCRIAN)         # Unstable, haunted
```

## 4. Chord Building

```python
def _build_chords(progression: str, duration: float, key: Scale) -> list[ChordLabel]:
    parts = progression.split()
    beats_per = duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per
        chord.duration = beats_per
        chords.append(chord)
    return chords

# Or manual for non-standard progressions:
chords = []
prog = [(11, Quality.MINOR), (4, Quality.MINOR), (6, Quality.MAJOR), (11, Quality.MINOR)]
for i in range(int(dur / 4.0)):
    root, qual = prog[i % 4]
    chords.append(ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))
```

## 5. Gothic Pattern

```python
def produce_gothic_track():
    bpm, dur = 76, 128.0
    chords = _build_chords("i iv V i", dur, B_HUNGARIAN)

    # Weeping violin lead with motifs
    violin = MelodyGenerator(
        GeneratorParams(density=0.55, complexity=0.75, velocity_range=(80, 110)),
        phrase_length=8.0, note_range_low=62, note_range_high=86,
        motif_probability=0.90, ornament_probability=0.40,
        register_smoothness=0.60
    ).render(chords, B_HUNGARIAN, dur)

    # Church organ drone
    organ = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=47, key_range_high=71),
        voicing="spread", overlap=0.2
    ).render(chords, B_HUNGARIAN, dur)

    # Cello counter-melody
    cello = CelloGenerator(
        GeneratorParams(density=0.40, key_range_low=36, key_range_high=60),
        articulation="legato"
    ).render(chords, B_HUNGARIAN, dur)

    return {"Violin": violin, "Organ": organ, "Cello": cello}, bpm

# Export via produce_track:
produce_track(
    tracks=track_data,
    bpm=bpm,
    instruments={"Violin": 40, "Organ": 19, "Cello": 42},
    path=str(out_path),
    mood=Mood.CINEMATIC,
    key=B_HUNGARIAN,
)
```

## 6. Metal Pattern

```python
def produce_metal_track():
    bpm, dur = 140, 96.0
    chords = _build_chords("i bII VII i", dur, D_PHRYGIAN)

    # Shred guitar solo
    solo = SoloMelodyGenerator(
        GeneratorParams(density=0.65, key_range_low=50, key_range_high=80),
        style="shred_guitar", vibrato_depth=0.8
    ).render(chords, D_PHRYGIAN, dur)

    # Refine with predictive harmonizer
    harmonizer = PredictiveHarmonizer(certainty_threshold=1.5)
    chords = harmonizer.refine(chords, solo, D_PHRYGIAN, dur)
    solo = spiceup(solo, D_PHRYGIAN, depth=1)

    # Aggressive saw bass
    bass = ModernBass2025Generator(
        GeneratorParams(density=0.7, key_range_low=26, key_range_high=46),
        style="saw"          # "saw", "euclidean", "sidechain", "fingerstyle", "spectral", "self_modifying"
    ).render(chords, D_PHRYGIAN, dur)

    # Heavy brass backing
    brass = [NoteInfo(pitch=c.root + 36, start=c.start, duration=c.duration * 0.9, velocity=88)
             for c in chords]

    return {"Solo": solo, "Bass": bass, "Brass": brass}, bpm
```

## 7. Folk / Gypsy Pattern

```python
def produce_gypsy_track():
    dur, key, bpm = 56.0, E_GYPSY, 130.0
    ch = _build_chords("i bII V i iv bVI bII V i", dur, key)

    # Gypsy violin with ornaments
    violin = ViolinGenerator(
        GeneratorParams(density=0.7, key_range_low=55, key_range_high=88),
        articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=2.5
    ).render(ch, key, dur)

    # Folk guitar strumming
    guitar = GuitarStrummingGenerator(
        GeneratorParams(density=0.6, key_range_low=40, key_range_high=76),
        strum_pattern="folk", palm_mute_ratio=0.3
    ).render(ch, key, dur)

    # Walking bass
    bass = BassGenerator(
        GeneratorParams(density=0.6, key_range_low=28, key_range_high=40),
        style="walking"
    ).render(ch, key, dur)

    # Drum kit
    drums = DrumKitPatternGenerator(
        GeneratorParams(density=0.7),
        style="rock", hihat_pattern="eighth", fill_frequency=0.3
    ).render(ch, key, dur)

    return {"Violin": violin, "Guitar": guitar, "Bass": bass, "Drums": drums}, bpm
```

## 8. Manual Mixing (Alternative)

For folk/simple albums without `produce_track`:

```python
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violin": 0.88, "Guitar": 0.82, "Bass": 0.80,
        "Drums": 0.72, "Strings": 0.78, "Pad": 0.68,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    m = MasteringDesk(target_lufs=-14.0)
    return m.apply_mastering(mixed)
```

## 9. Gothic / Metal BPM Guide

| Style | BPM |
|---|---|
| Atmospheric intro | 50-70 |
| Gothic romance | 70-90 |
| Dark orchestral march | 90-110 |
| Heavy metal / thrash | 120-145 |
| Folk dance | 120-140 |
| Gypsy virtuoso | 140-170 |
| Doom / funeral | 45-65 |

## 10. Key Instrument Choices

| Genre | Melody | Bass | Harmonic | Percussion |
|---|---|---|---|---|
| Gothic | Violin (40), Choir (52) | Contrabass (43) | Organ (19), Pad (88) | Timpani (47) |
| Metal | SoloMelody shred, Trumpet (56) | ModernBass2025 saw (38) | Brass Section (62) | DrumKitPattern (0) |
| Folk | Violin (40), MelodyGenerator | BassGenerator walking (32) | GuitarStrumming (25) | DrumKitPattern (0) |
| Gypsy | Violin (40) | BassGenerator (32) | GuitarStrumming (25), Harp (46) | DrumKitPattern (0) |

## 11. Common Pitfalls

| Issue | Fix |
|---|---|
| `Mode.HARMONIC_MINOR` doesn't exist | Use `Mode.HARM_MINOR` |
| ModernBass2025 style not found | Valid: `saw`, `euclidean`, `sidechain`, `fingerstyle`, `spectral`, `self_modifying` |
| SoloMelodyGenerator style invalid | Valid: `shred_guitar`, `neo_soul_keys`, `space_synth`, `bebop_horn`, `cinematic_strings`, `modal_ambient` |
| `spiceup` not found | Import from `melodica.composer.transformers` |
| Gypsy scale doesn't work | Use `Mode.GYPSY` (not "GYPSY_MINOR") |
| Violin sounds plain | Set `vibrato=True`, `note_density=2.5`, `ornament_probability` |

## 12. Running

```bash
python scripts/albums/gothic/album_name.py    # Gothic
python scripts/albums/metal/album_name.py     # Metal
python scripts/albums/folk_culture/album_name.py  # Folk
```
