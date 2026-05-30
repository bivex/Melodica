---
name: write-symphonic-album
description: Generate a full symphonic/orchestral album using the Melodica framework. Creates multi-track compositions with proper orchestration, mixing, mastering, and MIDI export.
---

# Write Symphonic Album

You are writing a symphonic album for the Melodica music generation framework. Follow this guide precisely to produce working Python scripts that generate complete albums with proper orchestration, mixing, and export.

## 1. Required Imports

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from melodica import (
    Scale, Mode,
    GeneratorParams,
    StringsLegatoGenerator, PizzicatoGenerator, TremoloGenerator,
    HarpArpeggioGenerator, HarpGlissandoGenerator,
    FrenchHornGenerator, TrumpetGenerator, TromboneGenerator,
    BrassSectionGenerator,
    FluteGenerator, OboeGenerator, ClarinetGenerator, BassoonGenerator,
    CelloGenerator, ContrabassGenerator,
    TimpaniGenerator, SnareDrumGenerator,
    OrganDrawbarsGenerator, TensionGenerator,
    PianoGenerator,
)
from melodica.midi import export_multitrack_midi
from melodica.mixing import MixingDesk
from melodica.mastering import MasteringDesk
```

## 2. Album Boilerplate

Every album script follows this structure:

```python
ALBUM_NAME = "Album Title"
BASE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "output", "album_name")
os.makedirs(BASE_DIR, exist_ok=True)

# Helper functions
def _build_chords(progression: str, duration: float, scale) -> list:
    from melodica.progression import parse_progression
    return parse_progression(progression, scale, duration=duration)

def _clamp(notes, lo, hi):
    return [n.clone(velocity=max(lo, min(hi, n.velocity))) for n in notes]

def _expr_swell(notes, start_vel, peak_vel, end_vel, dur):
    """Apply expressive swell (crescendo then diminuendo)."""
    for n in notes:
        t = n.offset
        ratio = t / dur if dur > 0 else 0
        if ratio < 0.5:
            n.velocity = int(start_vel + (peak_vel - start_vel) * (ratio * 2))
        else:
            n.velocity = int(peak_vel + (end_vel - peak_vel) * ((ratio - 0.5) * 2))
    return notes


def apply_orchestral_mix(mix: MixingDesk):
    """Standard orchestral mixing preset."""
    mix.set_reverb(room_size=0.7, damping=0.4, wet=0.25)
    mix.set_stereo_width(0.85)


def main():
    for func, filename, programs in TRACKS:
        print(f"  Generating: {filename}...")
        track_data, bpm = func()
        all_notes = {}
        for name, notes in track_data.items():
            all_notes[name] = notes
        # Mixing
        mix = MixingDesk(bpm)
        apply_orchestral_mix(mix)
        mixed = mix.mix(all_notes)
        # Mastering
        master = MasteringDesk(bpm)
        mastered = master.master(mixed)
        # Export
        out_path = os.path.join(BASE_DIR, filename)
        export_multitrack_midi(mastered, out_path, programs=programs, bpm=bpm)
        print(f"    -> {out_path}")


if __name__ == "__main__":
    main()
```

## 3. Scale and Mode System

```python
C_MAJOR = Scale("C", Mode.MAJOR)
G_MAJOR = Scale("G", Mode.MAJOR)
D_MAJOR = Scale("D", Mode.MAJOR)
A_MINOR = Scale("A", Mode.MINOR)
E_MINOR = Scale("E", Mode.MINOR)
B_MINOR = Scale("B", Mode.MINOR)

# Bright modes
F_LYDIAN = Scale("F", Mode.LYDIAN)
D_MIXOLYDIAN = Scale("D", Mode.MIXOLYDIAN)
A_DORIAN = Scale("A", Mode.DORIAN)
E_MELODIC = Scale("E", Mode.MELODIC_MINOR)

# Exotic
E_DBL_HM = Scale("E", Mode.DOUBLE_HARM_MAJOR)
```

### Available Modes

`MAJOR`, `MINOR`, `DORIAN`, `PHRYGIAN`, `LYDIAN`, `MIXOLYDIAN`, `AEOLIAN`, `LOCRIAN`, `HARM_MINOR`, `MELODIC_MINOR`, `DOUBLE_HARM_MAJOR`

**PITFALL**: `Mode.HARMONIC_MAJOR` does NOT exist. Use `Mode.DOUBLE_HARM_MAJOR` instead.

## 4. GeneratorParams

Controls density, range, and velocity of generated notes:

```python
# Sparse (ambient, pads, slow sections)
GeneratorParams(density=0.2, key_range_low=36, key_range_high=60)

# Medium (melody, counter-melody)
GeneratorParams(density=0.5, key_range_low=48, key_range_high=72)

# Dense (tutti, climaxes, ostinati)
GeneratorParams(density=0.8, key_range_low=40, key_range_high=84)
```

## 5. Generator Reference

### Strings

| Generator | Key Params |
|---|---|
| `StringsLegatoGenerator(params, chords, scale, duration)` | Uses `dynamic_shape` NOT `articulation`. Values: `"cresc_dim"`, `"swell"`, `"sustained"` |
| `PizzicatoGenerator(params, chords, scale, duration)` | Short plucked strings |
| `TremoloGenerator(params, chords, scale, duration)` | Bow tremolo effect |
| `CelloGenerator(params, chords, scale, duration, articulation="legato")` | `articulation`: `"legato"`, `"spiccato"`, `"col_legno"` |
| `ContrabassGenerator(params, chords, scale, duration)` | Deep bass register |

### Harp

| Generator | Key Params |
|---|---|
| `HarpArpeggioGenerator(params, chords, scale, duration, pattern="rising")` | `pattern`: `"rising"`, `"falling"`, `"wave"` |
| `HarpGlissandoGenerator(params, chords, scale, duration)` | Rapid scale sweep |

### Brass

| Generator | Key Params |
|---|---|
| `FrenchHornGenerator(params, chords, scale, duration, articulation="legato")` | Warm, noble tone |
| `TrumpetGenerator(params, chords, scale, duration, articulation="legato")` | `articulation`: `"legato"`, `"staccato"`, `"marcato"` |
| `TromboneGenerator(params, chords, scale, duration)` | Powerful low brass |
| `BrassSectionGenerator(params, chords, scale, duration, articulation="legato")` | Full section unison |

### Woodwinds

| Generator | Key Params |
|---|---|
| `FluteGenerator(params, chords, scale, duration)` | Airy, bright |
| `OboeGenerator(params, chords, scale, duration)` | Expressive, reedy |
| `ClarinetGenerator(params, chords, scale, duration)` | Warm, flexible |
| `BassoonGenerator(params, chords, scale, duration)` | Deep, dark |

### Percussion

| Generator | Key Params |
|---|---|
| `TimpaniGenerator(params, chords, scale, duration)` | Kettledrum rolls/hits |
| `SnareDrumGenerator(params, chords, scale, duration)` | Military snare patterns |

### Keyboards

| Generator | Key Params |
|---|---|
| `PianoGenerator(params, chords, scale, duration)` | Acoustic grand |
| `OrganDrawbarsGenerator(params, chords, scale, duration, registration="ballad")` | `registration`: `"ballad"`, `"gospel"`, `"jazz"`, `"rock"` |

### Effects

| Generator | Key Params |
|---|---|
| `TensionGenerator(params, chords, scale, duration, mode="semitone_cluster")` | `mode`: `semitone_cluster`, `tritone_pulse`, `major7_tension`, `chromatic_rise`, `chromatic_fall`, `atonal_scatter` |

## 6. Track Function Pattern

Each track is a function returning `(dict_of_tracks, bpm)`:

```python
def track_01_dawn():
    """Track 1: Dawn (C Major, 72 BPM) - Gentle opening."""
    print("  1. Dawn")
    dur = 48.0
    chords = _build_chords("I vi IV V", dur, C_MAJOR)
    params = GeneratorParams(density=0.4, key_range_low=48, key_range_high=72)

    melody = _clamp(
        StringsLegatoGenerator(params, chords, C_MAJOR, dur,
                               dynamic_shape="cresc_dim").render(),
        50, 80
    )
    harp = _clamp(
        HarpArpeggioGenerator(params, chords, C_MAJOR, dur,
                              pattern="rising").render(),
        40, 70
    )
    bass = _clamp(
        ContrabassGenerator(
            GeneratorParams(density=0.3, key_range_low=28, key_range_high=43),
            chords, C_MAJOR, dur
        ).render(),
        45, 65
    )
    return {"Melody": melody, "Harp": harp, "Bass": bass}, 72.0
```

## 7. Track Registry

At the bottom of the file, register all tracks with MIDI program numbers:

```python
TRACKS = [
    # (function, filename, {track_name: GM_program_number})
    (track_01_dawn,   "01_Dawn.mid",    {"Melody": 49, "Harp": 46, "Bass": 43}),
    (track_02_hope,   "02_Hope.mid",    {"Melody": 40, "Counter": 42, "Bass": 43}),
    # ...
]
```

### Common GM Program Numbers

| Instrument | GM# |
|---|---|
| Acoustic Grand Piano | 0 |
| Violin | 40 |
| Viola | 41 |
| Cello | 42 |
| Contrabass | 43 |
| Tremolo Strings | 44 |
| Pizzicato Strings | 45 |
| Orchestral Harp | 46 |
| Timpani | 47 |
| String Ensemble 1 | 48 |
| String Ensemble 2 | 49 |
| French Horn | 60 |
| Trumpet | 56 |
| Trombone | 57 |
| Flute | 73 |
| Oboe | 68 |
| Clarinet | 71 |
| Bassoon | 70 |
| Choir Aahs | 52 |
| Church Organ | 19 |
| Pad (warm) | 89 |
| Percussion (ch10) | 0 |

## 8. Roman Numeral Progressions

```
I    = Tonic (major)
ii   = Supertonic (minor)
iii  = Mediant (minor)
IV   = Subdominant (major)
V    = Dominant (major)
vi   = Submediant (minor)
vii° = Leading tone (diminished)

Common progressions:
- "I IV V I"           — Classic
- "I vi IV V"          — Pop ballad
- "I V vi IV"          — Loop progression
- "i III VII VI"       — Andalusian (minor)
- "I IV I V"           — Folk
- "vi IV I V"          — Sensitive
- "I iii IV V"         — Emotional
- "i iv V i"           — Minor dramatic
- "I bVI bVII I"       — Epic (modal mixture)
```

## 9. BPM Guide by Mood

| Mood | BPM Range |
|---|---|
| Intro/ambient | 55-70 |
| Slow movement | 65-80 |
| Lyrical/cantabile | 75-90 |
| Moderate/walking | 85-100 |
| Scherzo/energetic | 100-120 |
| Allegro/dramatic | 115-135 |
| Vivace/triumphant | 130-150 |
| Presto/climax | 145-165 |

## 10. Orchestration Patterns

### Small Ensemble (2-4 tracks)
```python
StringsLegatoGenerator + HarpArpeggioGenerator + ContrabassGenerator
```

### Medium Orchestra (5-8 tracks)
```python
StringsLegatoGenerator + FrenchHornGenerator + OboeGenerator + CelloGenerator + HarpArpeggioGenerator + ContrabassGenerator
```

### Full Tutti (9+ tracks)
```python
StringsLegatoGenerator + FrenchHornGenerator + TrumpetGenerator + TromboneGenerator +
BrassSectionGenerator + FluteGenerator + OboeGenerator + CelloGenerator +
ContrabassGenerator + TimpaniGenerator + HarpArpeggioGenerator
```

### Climax Layering Strategy
1. Start with melody (strings) + bass (contrabass)
2. Add harp arpeggios
3. Introduce woodwind counter-melody
4. Add French horn sustain
5. Bring in brass section
6. Add timpani + snare for drive
7. Full tutti peak

## 11. Common Pitfalls

| Pitfall | Fix |
|---|---|
| `Mode.HARMONIC_MAJOR` does not exist | Use `Mode.DOUBLE_HARM_MAJOR` |
| `StringsLegatoGenerator` uses `articulation` | Use `dynamic_shape` instead. Values: `"cresc_dim"`, `"swell"`, `"sustained"` |
| `OrganDrawbarsGenerator` registration `"full"` or `"full_tutti"` | Valid: `"ballad"`, `"gospel"`, `"jazz"`, `"rock"` |
| `TensionGenerator` mode `"tritone_shift"` | Valid: `semitone_cluster`, `tritone_pulse`, `major7_tension`, `chromatic_rise`, `chromatic_fall`, `atonal_scatter` |
| Notes too quiet/loud | Use `_clamp(notes, min_vel, max_vel)` |
| Track has no dynamics | Use `_expr_swell()` for crescendo-diminuendo |
| All tracks same density | Vary `GeneratorParams.density`: 0.2 sparse, 0.5 medium, 0.8 dense |

## 12. Album Structure (20 Tracks)

Organize into 4-5 phases with emotional arc:

```
Phase 1 — Awakening (Tracks 1-4): Slow, gentle, building
Phase 2 — Rising (Tracks 5-8): Energetic, hopeful, forward
Phase 3 — Triumph (Tracks 9-12): Powerful, dramatic, climactic
Phase 4 — Reflection (Tracks 13-16): Introspective, lyrical, emotional
Phase 5 — Ascension (Tracks 17-20): Grand finale, epic, uplifting
```

Each phase should:
- Share related keys (circle of fifths movement)
- Gradually increase then decrease BPM
- Build orchestration from sparse to full and back

## 13. Generating the Album

After writing the script, run it:

```bash
python scripts/albums/orchestral/album_name.py
```

Output MIDI files appear in `output/album_name/`. Verify with:
```bash
ls -la output/album_name/*.mid | wc -l  # Should match track count
```

## 14. Generator Signature Reference

For detailed generator signatures, see `!`cat docs/Generators.md | head -200``.

For instrument GM numbers and orchestral profiles, see `!`cat docs/Instruments.md``.
