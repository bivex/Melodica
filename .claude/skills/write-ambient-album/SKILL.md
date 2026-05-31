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
from melodica.composer.orchestration_rules import OrchestrationRules, INSTRUMENTS
from melodica.form import FormSection, MusicalForm
from melodica.engines.microtuning import MicrotuningEngine
from melodica.generators.microtonal_melody import MicrotonalMelodyGenerator
from melodica.generators.aleatoric import AleatoricGenerator
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

## 7. Motif Transforms

`Motif` provides 19 transforms — each returns a NEW Motif (immutability preserved). Chain transforms via `develop()`.

```python
from melodica.composer import Motif
from melodica.types import NoteInfo, Scale, Mode

m = Motif.from_notes([
    NoteInfo(pitch=72, start=0.0, duration=3.0, velocity=55),
    NoteInfo(pitch=70, start=3.0, duration=2.0, velocity=50),
    NoteInfo(pitch=67, start=5.0, duration=3.0, velocity=55),
])

sc = Scale(0, Mode.MAJOR)
```

### Transform Reference

| Method | Purpose |
|---|---|
| `transpose(semitones)` | Chromatic transposition |
| `invert(center)` | Mirror pitches around center (default: average) |
| `retrograde()` | Reverse note order with re-timed starts |
| `augment(factor)` | Stretch durations and gaps (2.0 = twice as long) |
| `diminish(factor)` | Compress durations and gaps |
| `sequence(intervals, spacing)` | Repeat at pitch intervals |
| `fragment(start_beat, end_beat)` | Extract notes in time window |
| `transpose_diatonic(degrees, scale)` | Modal transpose by N scale degrees |
| `invert_diatonic(scale, axis_degree)` | Scale-aware inversion (stays diatonic) |
| `displace(beats)` | Rhythmic displacement — shift all start times |
| `truncate_head(n)` | Remove first N notes |
| `truncate_tail(n)` | Remove last N notes |
| `expand(factor)` | Stretch gaps between notes, keep durations |
| `apply_dynamics(envelope)` | Apply VelocityEnvelope |
| `ornament(style, scale)` | Add grace/passing/neighbor/cambiata/spiceup |
| `canon(voices, delay, intervals)` | Generate canon entries |
| `with_pedal(pitch)` | Add sustained pedal note spanning motif |
| `humanize(timing, velocity)` | Random timing/velocity variation |

### Chaining via `develop()`

```python
# Chain multiple transforms in musical order
developed = m.develop(
    retrograde=True,
    transpose=-3,
    augment_factor=2.0,
    humanize_timing=0.01,
    pedal_pitch=36,
)

# Full develop() chain order:
# fragment → truncate → retrograde → invert → invert_diatonic →
# augment/diminish → expand → transpose → transpose_diatonic →
# displace → ornament → apply_dynamics → humanize → canon →
# with_pedal → sequence
```

### develop() kwargs

| Kwarg | Effect |
|---|---|
| `fragment_start`, `fragment_end` | Keep only notes in time window |
| `truncate_head_n`, `truncate_tail_n` | Remove first/last N notes |
| `retrograde` (bool) | Reverse note order |
| `invert` (bool), `invert_center` | Chromatic inversion |
| `invert_diatonic` (bool), `invert_diatonic_scale`, `invert_diatonic_axis` | Scale-aware inversion |
| `augment_factor`, `diminish_factor` | Time stretching |
| `expand_factor` | Stretch gaps only |
| `transpose` | Semitone transposition |
| `transpose_diatonic_degrees`, `transpose_diatonic_scale` | Modal transposition |
| `displace_beats` | Shift all starts |
| `ornament_style`, `ornament_scale` | Add ornamentation |
| `dynamics_envelope` | Apply VelocityEnvelope |
| `humanize_timing`, `humanize_velocity` | Random variation |
| `canon_voices`, `canon_delay`, `canon_intervals` | Canon generation |
| `pedal_pitch` | Add sustained bass note |
| `sequence_intervals`, `sequence_spacing` | Sequence repetition |

## 8. Leitmotif Registry

`LeitmotifRegistry` binds named motifs to characters, places, emotions via tags. Supports variants, evolution, mood-based rendering, layering, and counter-motif generation.

```python
from melodica.composer import Motif, LeitmotifRegistry, MOOD_PRESETS
from melodica.types import NoteInfo

# Create and register motifs
hero_motif = Motif.from_notes([
    NoteInfo(pitch=72, start=0.0, duration=3.0, velocity=55),
    NoteInfo(pitch=70, start=3.0, duration=2.0, velocity=50),
    NoteInfo(pitch=67, start=5.0, duration=3.0, velocity=55),
])

registry = LeitmotifRegistry()
registry.register("hero", hero_motif,
    tags=["protagonist", "brave"], instrument=73, velocity=55)
registry.register("villain", hero_motif,
    tags=["antagonist", "dark"], instrument=68, velocity=45)

# Basic rendering with transforms
notes = registry.render("hero", offset=120.0)
notes = registry.render("hero", offset=60.0, transpose=7)
notes = registry.render("villain", offset=80.0, invert=True, transpose=-7)

# Evolve — create named variants via transform chains
registry.evolve("hero", "dark_version", transpose=-6, retrograde=True)
registry.evolve("hero", "bright", transpose=12, augment_factor=1.5)

# Render a specific variant
notes = registry.render("hero", variant="dark_version", offset=40.0)

# Mood-based rendering — 8 presets
notes = registry.render_for("hero", "dark", offset=60.0)
notes = registry.render_for("hero", "ethereal", offset=80.0, intensity=1.5)

# Layer multiple motifs polyphonically
notes = registry.layer(
    ["hero", "villain"], [0.0, 20.0],
    transpose=5, augment_factor=1.5
)

# Auto-generate contrasting counter-motif
from melodica.types import Scale, Mode
sc = Scale(0, Mode.MAJOR)
counter = registry.counter_motif("hero", sc)
counter_notes = counter.render(offset=50.0)

# Query by tag
all_hero = registry.render_all(tag="protagonist")
```

### Mood Presets

| Mood | Transforms |
|---|---|
| `"dark"` | invert + diminish x2 + transpose -6 |
| `"triumphant"` | transpose +7 + augment x1.5 |
| `"tender"` | augment x1.8 + fragment |
| `"aggressive"` | diminish x2 + retrograde |
| `"mysterious"` | invert + augment x2 + transpose +3 |
| `"nostalgic"` | retrograde + augment x2 |
| `"urgent"` | diminish x2.5 |
| `"ethereal"` | augment x3 + transpose +12 |

### render() Transform Parameters

| Parameter | Effect |
|---|---|
| `offset` | Time shift in beats |
| `variant` | Use a named variant instead of default |
| `transpose` | Semitone transposition (positive = up) |
| `invert` | Mirror intervals |
| `retrograde` | Reverse note order |
| `augment_factor` | Stretch durations |
| `diminish_factor` | Compress durations |
| `fragment_start`, `fragment_end` | Keep only notes in time window |
| `sequence_intervals`, `sequence_spacing` | Repeat at pitch intervals with spacing |

## 9. Orchestral Unpitched Percussion

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

## 10. Key Modulation via MusicalForm

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

## 11. GM Program Assignments

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

## 12. Track Function Pattern

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

## 13. Album Structure

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

## 14. Ambient BPM Guide

| Mood | BPM |
|---|---|
| Deep meditation | 40-50 |
| Stillness / void | 44-52 |
| Floating / drift | 48-60 |
| Breath-paced | 56-64 |
| Warm ambient | 60-72 |
| Dark ambient march | 70-90 |
| Energetic meditation | 100-120 |

## 15. Mastering LUFS Targets

| Context | Target LUFS |
|---|---|
| Meditation / sleep | -20.0 to -18.0 |
| Ambient listening | -16.0 to -14.0 |
| Dark ambient / cinematic | -14.0 to -12.0 |

## 16. Density Guide

| Role | Density |
|---|---|
| Drone / pedal tone | 0.01–0.03 |
| Pad atmosphere | 0.05–0.12 |
| Sparse melody | 0.04–0.10 |
| Arpeggio | 0.06–0.15 |
| Percussion hint | 0.08–0.20 |

## 17. Orchestration Rules Engine

`OrchestrationRules` validates notes against 30 orchestral instrument ranges. Use before export to catch unplayable pitches.

```python
from melodica.composer.orchestration_rules import OrchestrationRules, INSTRUMENTS

rules = OrchestrationRules()

# Validate — returns list of OrchestrationWarning
warnings = rules.validate(flute_notes, "flute")
for w in warnings:
    print(f"{w.severity}: {w.message}")

# Clamp — force notes into playable range
safe_notes = rules.clamp_to_range(flute_notes, "flute")

# Identify register
reg = rules.register_at("flute", 84)  # "high"

# Suggest nearest comfortable octave
pitch = rules.suggest_octave("cello", 72)

# Analyze blend between two instruments
blend = rules.blend_with("violin", "viola")
# {"overlap_semitones": 33, "blend_quality": "strong", ...}
```

Available instruments: violin, viola, cello, contrabass, flute, piccolo, oboe, english_horn, clarinet, bass_clarinet, bassoon, contrabassoon, french_horn, trumpet, trombone, bass_trombone, tuba, harp, piano, timpani, marimba, vibraphone, xylophone, glockenspiel, celesta, choir_soprano, choir_alto, choir_tenor, choir_bass, organ.

## 18. Microtonality

`MicrotuningEngine` converts fractional MIDI pitches into integer NoteInfo with pitch_bend expression data, enabling microtonal scales (quarter-tone, Arabic, etc.) within standard MIDI.

```python
from melodica.engines.microtuning import MicrotuningEngine

tuning = MicrotuningEngine(bend_range=2)  # ±2 semitones (standard)

# Snap float pitch to nearest scale degree
snapped = tuning.snap_to_scale(61.5, key)

# Quantize — returns (midi_int, expression_dict)
midi_int, expr = tuning.quantize_pitch(61.5, key)
# midi_int=62, expr={} if on-scale, or {"pitch_bend": [(0.0, bend_val)]}

# Render a single microtonal note
note = tuning.render_microtonal_note(61.5, start=0.0, duration=4.0, velocity=55, scale=key)

# Wrap existing notes with microtonal quantization
wrapped = tuning.wrap_notes(melody_notes, key)
```

`MicrotonalMelodyGenerator` produces complete microtonal melodies:

```python
from melodica.generators.microtonal_melody import MicrotonalMelodyGenerator

micro_melody = MicrotonalMelodyGenerator(
    GeneratorParams(density=0.05, key_range_low=60, key_range_high=84),
    phrase_length=16.0,
    bend_range=2,
    note_duration=3.0,
    velocity_range=(35, 55),
).render(chords, key, dur)
```

Use with microtonal modes: `Mode.QUARTER_TONE_MINOR`, `Mode.ARABIC_SIKAH`, etc.

## 19. Aleatoric Generator

`AleatoricGenerator` produces chance-based compositions with 6 modes. Ideal for ambient textures, experimental passages, and atmospheric soundscapes.

```python
from melodica.generators.aleatoric import AleatoricGenerator

# Xenakis-inspired textural cloud
cloud = AleatoricGenerator(
    GeneratorParams(density=0.08, key_range_low=36, key_range_high=72),
    mode="textural_cloud",
    density=0.3,
).render(chords, key, dur)

# Webern-inspired pointillist
points = AleatoricGenerator(
    GeneratorParams(density=0.06, key_range_low=60, key_range_high=96),
    mode="pointillist",
    density=0.15,
).render(chords, key, dur)
```

| Mode | Description | Use Case |
|---|---|---|
| `"tone_cluster"` | Dense chromatic cluster, simultaneous onset | Dissonant stabs, tension |
| `"chance_operations"` | Random pitch/rhythm placement (Cage) | Unpredictable textures |
| `"repeat_ad_lib"` | Repeated figure with micro-variations | Minimalist ostinato |
| `"graphic_score"` | Broad pitch regions with free rhythm | Spatial, open-form |
| `"pointillist"` | Isolated, scattered short notes | Webern-esque fragility |
| `"textural_cloud"` | Gaussian density cloud (Xenakis) | Ambient masses, swarms |

## 20. Common Pitfalls

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

## 21. Running

```bash
python scripts/albums/ambient/album_name.py
```

Verify output:
```bash
ls output/album_name/*.mid
```
