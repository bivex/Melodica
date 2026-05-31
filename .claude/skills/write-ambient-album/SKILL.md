---
name: write-ambient-album
description: Generate ambient, meditation, drone, and atmospheric albums. Uses DroneGenerator, AmbientPadGenerator, MelodyGenerator with ultra-low density. Manual MixingDesk/MasteringDesk pipeline.
---

# Write Ambient / Meditation / Drone Album

Use this skill for ambient, meditation, drone, atmospheric, and space-themed albums. Characterized by ultra-low density (0.01–0.15), long durations (120–300 beats), slow BPM (40–65), and minimal harmonic motion.

## 1. When to Use

- Ambient / drone / space music
- Meditation / yoga / breathwork soundtracks
- Atmospheric soundscapes
- Tibetan bowl / singing bowl music
- Overtone / acoustic resonance music
- Dark ambient / void atmospheres

## 2. Required Imports

```python
import random
from pathlib import Path

from melodica import types
from melodica.types import Scale, Mode, Quality, ChordLabel, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.rest import RestGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators import (
    BassDrumGenerator, TamTamGenerator, GongGenerator,
    TriangleGenerator, CastanetsGenerator, WhipSlapstickGenerator,
)
from melodica.composer import Motif, TempoMap, VelocityEnvelope, LeitmotifRegistry
from melodica.form import FormSection, MusicalForm
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk
```

## 3. Ambient Scales

```python
# Meditation / overtone
C_OVERTONE  = Scale(root=0, mode=Mode.ACOUSTIC_MAJOR)  # Natural resonance
C_MAJOR     = Scale(root=0, mode=Mode.MAJOR)            # Peace, clarity
G_LYDIAN    = Scale(root=7, mode=Mode.LYDIAN)           # Floating, bright
F_LYDIAN    = Scale(root=5, mode=Mode.LYDIAN)           # Ethereal

# Dark ambient
D_PHRYGIAN  = Scale(root=2, mode=Mode.PHRYGIAN)         # Tension
C_LOCRIAN   = Scale(root=0, mode=Mode.LOCRIAN)          # Unstable, haunted
A_HARM_MIN  = Scale(root=9, mode=Mode.HARM_MINOR)       # Occult

# Warm / healing
D_DORIAN    = Scale(root=2, mode=Mode.DORIAN)           # Warm minor
E_PHRYG_DOM = Scale(root=4, mode=Mode.PHRYGIAN_DOMINANT) # Energy
```

## 4. Core Pattern

Ambient albums use **manual mixing** (not `produce_track`) because tracks are long, sparse, and need precise gain control.

```python
random.seed(108)
OUT = Path("output/album_name")
OUT.mkdir(parents=True, exist_ok=True)


def _off(notes, offset):
    """Shift notes by offset beats."""
    return [
        NoteInfo(pitch=n.pitch, start=n.start + offset,
                 duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _master(raw: dict, bpm: float, lufs: float = -18.0):
    """Mix and master with soft ambient gains."""
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "bowl": 0.8, "pad": 0.4, "flute": 0.7, "cello": 0.5,
        "sitar": 0.7, "voice": 0.6, "tanpura": 0.5, "harp": 0.65,
        "bass": 0.45, "piano": 0.7, "drone": 0.35, "bells": 0.4,
        "strings": 0.5, "choir": 0.55, "arp": 0.45,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, key: Scale, instruments: dict, lufs: float = -18.0):
    final_notes, cc_events = _master(tracks, bpm, lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)
```

## 5. Static Harmony Pattern

Most ambient tracks use a single chord for the entire duration:

```python
dur = 200.0
chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]
```

For slow-moving harmony, use 2–4 chords over a very long duration:

```python
chords = [
    ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=64),
    ChordLabel(root=5, quality=Quality.MAJOR, start=64, duration=64),
    ChordLabel(root=7, quality=Quality.MINOR, start=128, duration=64),
    ChordLabel(root=0, quality=Quality.MAJOR, start=192, duration=64),
]
```

## 6. Generator Configs for Ambient

### Drone (tanpura, bass pedal)

```python
drone = DroneGenerator(
    GeneratorParams(density=0.01, key_range_low=36, key_range_high=37),
    velocity=35
).render(chords, key, dur)
```

### Ambient Pad (atmosphere)

```python
pad = AmbientPadGenerator(
    GeneratorParams(density=0.08, key_range_low=48, key_range_high=72),
    voicing="spread", overlap=1.0
).render(chords, key, dur)
```

### Slow Melody (flute, vocal)

```python
flute = MelodyGenerator(
    GeneratorParams(density=0.05, velocity_range=(40, 60)),
    phrase_length=16.0,
    harmony_note_probability=0.8,
    steps_probability=0.9,
    note_range_low=72, note_range_high=84,
    register_smoothness=0.9
).render(chords, key, dur - 40.0)
flute = _off(flute, 36.0)  # Delayed entry
```

### Sparse Arpeggio (harp, bells)

```python
arp = ArpeggiatorGenerator(
    GeneratorParams(density=0.08),
    pattern="up", note_duration=2.0
).render(chords, key, dur)
```

### Rest (silence / space)

```python
rest = RestGenerator(
    GeneratorParams(density=0.0)
).render(chords, key, dur)
```

### Cello / Strings (support)

```python
cello = DroneGenerator(
    GeneratorParams(density=0.01, key_range_low=36, key_range_high=37),
    velocity=30
).render(chords, key, dur)
```

## 7. Leitmotif Registry

`LeitmotifRegistry` binds named motifs to characters, places, emotions via tags. Replaces manual `Motif.invert().fragment(...)` chains with a semantic, reusable API.

```python
from melodica.composer import Motif, LeitmotifRegistry
from melodica.types import NoteInfo

# Create the base motif
hero_motif = Motif.from_notes([
    NoteInfo(pitch=72, start=0.0, duration=3.0, velocity=55),
    NoteInfo(pitch=70, start=3.0, duration=2.0, velocity=50),
    NoteInfo(pitch=67, start=5.0, duration=3.0, velocity=55),
])

# Register with semantic tags and instrument preferences
registry = LeitmotifRegistry()
registry.register("hero", hero_motif,
    tags=["protagonist", "brave"], instrument=73, velocity=55)
registry.register("villain", hero_motif,
    tags=["antagonist", "dark"], instrument=68, velocity=45)

# Render with transforms — replaces manual Motif chains
notes = registry.render("hero", offset=120.0)                          # plain
notes = registry.render("hero", offset=60.0, transpose=7)              # transposed up
notes = registry.render("villain", offset=80.0, invert=True, transpose=-7)  # corrupted
notes = registry.render("hero", offset=140.0, retrograde=True, diminish_factor=2.0)
notes = registry.render("hero", offset=60.0, augment_factor=1.5)
notes = registry.render("hero", offset=130.0, fragment_start=0.0, fragment_end=5.0)
notes = registry.render("hero", offset=20.0,
    retrograde=True, augment_factor=2.0,
    sequence_intervals=[0, 5, -5, 12], sequence_spacing=20.0)

# Query by tag — render all motifs tagged "protagonist"
all_hero = registry.render_all(tag="protagonist")
```

### Transform Reference

| Parameter | Effect |
|---|---|
| `offset` | Time shift in beats |
| `transpose` | Semitone transposition (positive = up) |
| `invert` | Mirror intervals around first note |
| `retrograde` | Reverse note order |
| `augment_factor` | Stretch durations (2.0 = twice as long) |
| `diminish_factor` | Compress durations (2.0 = half as long) |
| `fragment_start`, `fragment_end` | Keep only notes in time window |
| `sequence_intervals`, `sequence_spacing` | Repeat at pitch intervals with spacing |

## 8. Orchestral Unpitched Percussion

Six generators for atmospheric/cinematic percussion. All use fixed GM drum-map pitches (scale-agnostic). Constructor: `(params=None, *, pattern_type="...")`.

```python
from melodica.generators import (
    BassDrumGenerator, TamTamGenerator, GongGenerator,
    TriangleGenerator, CastanetsGenerator, WhipSlapstickGenerator,
)
```

### Generator Reference

| Generator | GM Pitch | Pattern Types | Use Case |
|---|---|---|---|
| `BassDrumGenerator` | 36 (Gran Cassa), 35 (Acoustic) | `"single"`, `"roll"`, `"march"` | Heartbeat, tension, primal pulse |
| `TamTamGenerator` | 55 | `"strike"`, `"crescendo_strike"`, `"tremolo"` | Doom, ritual, ominous presence |
| `GongGenerator` | 55 | `"strike"`, `"roll"`, `"crescendo"` | Power, transformation, revelation |
| `TriangleGenerator` | 80 | `"single"`, `"roll"`, `"trill"` | Delicacy, temptation, shimmer |
| `CastanetsGenerator` | 85 | `"single"`, `"roll"`, `"rhythm"` | Urgency, agitation, Spanish flavor |
| `WhipSlapstickGenerator` | 91 | `"single"`, `"rapid"` | Shock, decision, violence |

### Usage Pattern

```python
# Bass drum march — a heartbeat or approaching doom
bdrum = BassDrumGenerator(pattern_type="march").render(chords, key, dur)

# Tam-tam crescendo — building tension toward a reveal
tamtam = TamTamGenerator(pattern_type="crescendo_strike").render(chords, key, dur)

# Gong crescendo — dark power manifesting
gong = GongGenerator(pattern_type="crescendo").render(chords, key, dur)

# Triangle trill — silver edge of temptation
triangle = TriangleGenerator(pattern_type="trill").render(chords, key, dur)

# Whip rapid — the crack of a final decision
whip = WhipSlapstickGenerator(pattern_type="rapid").render(chords, key, dur)
```

### Mixing Gains for Percussion

```python
desk.track_gains.update({
    "bdrum": 0.35, "tamtam": 0.4, "gong": 0.35, "triangle": 0.3,
    "castanets": 0.25, "whip": 0.3,
})
```

Percussion tracks use GM program `0` (channel 10 assignment handled upstream):
```python
_export({...},
    instruments={..., "bdrum": 0, "tamtam": 0, "gong": 0},
)
```

## 9. Key Modulation via MusicalForm

`MusicalForm` with `FormSection.key` enables per-section key changes within a single track. Use for narrative albums where the tonal center shifts with the story.

```python
from melodica.form import FormSection, MusicalForm

form = MusicalForm(sections=[
    FormSection(name="doubt", start_beat=0, duration_beats=100,
                dynamics="pp", tempo_multiplier=1.0,
                active_families=["piano"], mood="hesitation",
                key=A_DOR),           # Dorian — uncertain
    FormSection(name="resolve", start_beat=100, duration_beats=120,
                dynamics="mf", tempo_multiplier=1.15,
                active_families=["full"], mood="determination",
                key=D_DOR),           # D Dorian — warmer, resolved
    FormSection(name="judgment", start_beat=220, duration_beats=100,
                dynamics="ff", tempo_multiplier=0.85,
                active_families=["full", "percussion"], mood="transcendent",
                key=F_LYD),           # Lydian — transcendent, open
], tempo_map=[(0, bpm)])

# Query the active key at any beat position
active_key = form.key_at(50.0, fallback_key)   # Returns A_DOR
active_key = form.key_at(150.0, fallback_key)  # Returns D_DOR
active_key = form.key_at(250.0, fallback_key)  # Returns F_LYD
active_key = form.key_at(999.0, fallback_key)  # Returns fallback_key
```

### When to Use

- **Narrative albums**: key shifts match story beats (doubt → resolve → transcend)
- **Dark ambient**: modulation between Locrian, Phrygian, and Harmonic Minor
- **Multi-movement tracks**: each section in a different tonal center
- **Album finales**: progression from minor to Lydian for transcendence

## 10. GM Program Assignments

```python
TIBETAN_BOWL = 14   # Tubular Bells
SITAR        = 104
TANPURA      = 104  # Sitar (low register)
FLUTE        = 73
CELLO        = 42
HARP         = 46
CONTRABASS   = 43
CHOIR_AAH    = 52
VOICE_OOH    = 53
PAD_WARM     = 89
PAD_SPACE    = 91
PIANO        = 0
NYLON_GUITAR = 24
TABLE        = 116  # Taiko/Ethnic
```

## 11. Track Function Pattern

```python
def produce_track_01():
    print("--- 01_Track_Name ---")
    bpm = 52
    dur = 200.0
    key = Scale(root=0, mode=Mode.ACOUSTIC_MAJOR)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=dur)]

    # Tibetan bowl strikes
    bowl_hits = [
        NoteInfo(pitch=72, start=2.0, duration=16.0, velocity=80),
        NoteInfo(pitch=67, start=18.0, duration=16.0, velocity=65),
        NoteInfo(pitch=60, start=dur - 20.0, duration=18.0, velocity=70),
    ]

    # Tonic drone
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=48, key_range_high=49),
        velocity=35
    ).render(chords, key, dur)

    # Slow flute melody
    flute = MelodyGenerator(
        GeneratorParams(density=0.08, velocity_range=(40, 60)),
        phrase_length=16.0, note_range_low=72, note_range_high=84,
        register_smoothness=0.9
    ).render(chords, key, dur - 40.0)
    flute = _off(flute, 36.0)

    _export(
        {"bowl": bowl_hits, "drone": drone, "flute": flute},
        OUT / "01_Track_Name.mid", bpm, key,
        {"bowl": TIBETAN_BOWL, "drone": PAD_WARM, "flute": FLUTE},
    )
```

## 12. Album Structure

```python
def main():
    produce_track_01()
    produce_track_02()
    # ...
    print(f"\nAlbum complete. Files in {OUT}/")

if __name__ == "__main__":
    main()
```

Typical ambient album arc:

```
Track 1-2: Introduction, establishing drone/pad (40-50 BPM)
Track 3-4: Deeper, adding melodic elements (48-56 BPM)
Track 5:   Energetic peak (optional, 100-120 BPM)
Track 6:   Return to stillness (44-52 BPM)
Track 7:   Dissolution into silence (40 BPM)
```

## 13. Ambient BPM Guide

| Mood | BPM |
|---|---|
| Deep meditation | 40-50 |
| Stillness / void | 44-52 |
| Floating / drift | 48-60 |
| Breath-paced | 56-64 |
| Warm ambient | 60-72 |
| Dark ambient march | 70-90 |
| Energetic meditation | 100-120 |

## 14. Mastering LUFS Targets

| Context | Target LUFS |
|---|---|
| Meditation / sleep | -20.0 to -18.0 |
| Ambient listening | -16.0 to -14.0 |
| Dark ambient / cinematic | -14.0 to -12.0 |

## 15. Density Guide

| Role | Density |
|---|---|
| Drone / pedal tone | 0.01–0.03 |
| Pad atmosphere | 0.05–0.12 |
| Sparse melody | 0.04–0.10 |
| Arpeggio | 0.06–0.15 |
| Percussion hint | 0.08–0.20 |

## 16. Common Pitfalls

| Issue | Fix |
|---|---|
| Tracks too dense | Lower density below 0.10; ambient should feel sparse |
| No silence | Use `RestGenerator` or manually insert gaps with `_off(notes, offset)` |
| Duration too short | Ambient tracks need 120–300 beats (3–8 minutes) |
| LUFS too loud | Target -18.0 for meditation, not -14.0 |
| Pads overlap harshly | Set `overlap=1.0` in `AmbientPadGenerator` |
| Melody starts too early | Delay entry with `_off(notes, 36.0)` |
| All tracks same key | Move through related keys (C → G → D → F → C) |
| Drone disappears in mix | Set `track_gains["drone"]` to 0.35–0.40 |

## 17. Running

```bash
python scripts/albums/ambient/album_name.py
```

Verify output:
```bash
ls output/album_name/*.mid
```
