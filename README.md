# Melodica

> A composition generator for modern music.

Melodica implements a three-engine harmonization architecture with an extensive phrase-generation library for automated music composition, providing a clear, testable Python API.

---

## Quick Start

```python
from melodica import harmonize, Note, Scale, Mode

melody = [
    Note(pitch=60, start=0.0, duration=1.0),  # C4
    Note(pitch=62, start=1.0, duration=1.0),  # D4
    Note(pitch=64, start=2.0, duration=1.0),  # E4
    Note(pitch=65, start=3.0, duration=1.0),  # F4
]

# Uses default 'hmm' engine
chords = harmonize(melody, chord_rhythm=2.0)
for c in chords:
    print(c)
```

## Script Examples

### I. DF Downtempo
The `scripts/df_downtempo.py` script demonstrates a practical Melodica workflow:
- Read melody / chord settings
- Generate harmonization and phrase arrangements
- Export MIDI output

Run:

```bash
python scripts/df_downtempo.py
```

### II. Production Battle Example: Catchy Pop-Epic Melody
The `scratch/demo_catchy_melody.py` script demonstrates a production-grade Melodica workflow using the advanced `MelodyGenerator` and our automated MIDI CC expressiveness engine:
- Build a classic, highly recognizable emotional pop progression (`Am - F - C - G`).
- Generate a memorable melody using motivic development (`motif_probability=0.7`), phrase contour shaping (`phrase_contour="arch"`), and a dramatic energy curve with late peak intensity (`drama_shape="epic"`).
- Automatically arrange multi-part arrangements including a warm synth pad, a vibraphone arpeggio backing track, and a moving finger bassline.
- Automatically mix/master and inject high-fidelity MIDI CC automation: sustain pedal (**CC64**) for the arpeggios, breathing expression sweeps (**CC11**) on sustained notes, delayed vibrato LFO (**CC1**), and channel mixing levels (**CC7**).

Run:

```bash
python3 scratch/demo_catchy_melody.py
```

The output MIDI is exported directly to `output/demo_catchy/demo_catchy_melody.mid`.

## MIDI Analyzer

`scripts/midi_analyzer.py` — unified diagnostic tool that reads a MIDI file (or full album directory) and prints a compositional report.

```bash
# Analyze a single track
python3 scripts/midi_analyzer.py output/album_ainulindale/I_The_Theme_of_Eru.mid

# Analyze an entire album directory
python3 scripts/midi_analyzer.py output/album_ainulindale/

# Skip music21 (no key detection / consonance profiling)
python3 scripts/midi_analyzer.py output/album_ainulindale/ --no-music21
```

### What it reports

| Section | Description |
|---------|-------------|
| **Track Stats & Roles** | Note count, pitch range, velocity, density (notes/s). Auto-assigns role: BASS / LEAD / PAD / PERC / STRINGS / CHOIR / FX |
| **Register Distribution** | 9-band breakdown (sub → top) with note counts and bar chart |
| **Psychoacoustic** | 6 checks — frequency masking, temporal masking, harmonic fusion, rhythmic blur, register masking, brightness overload |
| **Harmonic Analysis** | Cross-track clashes by interval (m2, TT, M7, etc.) and top clashing pairs |
| **Timeline** | Which tracks are active in each quarter of the piece |
| **music21 Advanced** | Key detection + confidence, ambitus per track, consonance/dissonance profile, low-interval mud (LIM) warnings, melodic motion (step vs leap ratio, large-leap resolution rate) |
| **Suggestions** | Actionable fixes — velocity too low, register overlap, blurry notes, dense tracks |

### Requirements

- `mido` (required)
- `music21` (optional — for key detection and consonance analysis; skip with `--no-music21`)

### Register Balancing Workflow

The analyzer exposes register overlap and density problems. Fix them in the album script, then re-analyze to verify.

**1. Run the analyzer** and look at **Register Distribution** (9 bands from sub to top) and **Suggestions** (lines like `Chaos_Tremolo ↔ Defiant_Brass: 77% register overlap`).

**2. Diagnose.** In **Track Stats**, the `Band` column shows where each track sits. Two tracks in the same band will mask each other. Rule of thumb: one track per register band (sub / low / mid / mid-high / high).

**3. Fix register overlap** with `octave_shift` on `TrackConfig`:

```python
# Both in mid — overlap:
TrackConfig(name="Defiant_Brass", ..., octave_shift=1)    # → mid-high
TrackConfig(name="Tension_Cluster", ..., octave_shift=0)   # → mid (stays)

# Push bass deeper:
TrackConfig(name="Darkness_Pad", ..., octave_shift=-2)     # → sub
```

**4. Fix note density.** `TrackConfig.density` controls phrase-level density, not internal generator output. For generators like `TremoloStringsGenerator` that produce notes internally, adjust their own parameters:

```python
# bow_speed directly controls stroke count (lower = more notes):
TremoloStringsGenerator(bow_speed=0.0625)  # ~64 strokes per 4 beats
TremoloStringsGenerator(bow_speed=0.20)    # ~20 strokes (3× fewer notes)
```

**5. Regenerate and re-analyze:**

```bash
python3 scripts/album_xxx.py
python3 scripts/midi_analyzer.py output/album_xxx/
```

Verify: register distribution is spread, register masking dropped, no overlap pairs above 50%.

Cycle: **analyze → diagnose → `octave_shift` + generator params → regenerate → analyze**.

---

### Case Study: Sikhs in the Ruins of Tandumi

[`scripts/album_tandumi_ruins.py`](scripts/album_tandumi_ruins.py) — 5-track epic album in Arabic Sikah scale (E½♭),
Punjabi warrior energy over orchestral ruins atmosphere.
Below is the full, unedited balancing cycle we ran during production.

#### Iteration 1 — First run, first analysis

```bash
python3 scripts/album_tandumi_ruins.py
python3 scripts/midi_analyzer.py output/album_tandumi_ruins/ --no-music21
```

**Album-wide FREQUENCY BALANCE VERDICT:**

```
LOW  (bass foundation)   13.3%   target 15–35%  🟡 1.7% short
MID  (body / harmony)    77.4%   target 35–60%  🟡 17.4% over target
HIGH (air / presence)     9.2%   target 15–35%  🟡 5.8% short
Overall balance: ★★☆☆☆  NEEDS WORK
```

**Key findings from Suggestions:**

```
Bass_Foundation: max velocity 44 — raise velocity scaling
Tremolo_Rise: 4 362 notes — reduce density to avoid clutter
Tremolo_Rise: 2 734 blurry notes (<30ms) — increase durations
Glory_Horns  ↔ Light_Drone:        100% register overlap — separate ranges
Bass_Foundation ↔ Glory_Horns:      93% register overlap — separate ranges
Bass_Foundation ↔ Light_Drone:      86% register overlap — separate ranges
```

**What we fixed — round 1:**

| Problem | Fix | Parameter changed |
|---------|-----|-------------------|
| LOW deficit | `Battle_Bass` and `Chaos_Taiko` moved to sub-bass | `octave_shift=-2` (was -1) |
| HIGH deficit | `Warrior_Melody`, `Sitar_Counter`, `Final_Sitar`, `Victory_Bells` pushed up | `octave_shift=2` (was 1) |
| Bass/Horns 93% overlap | `Glory_Horns` lifted one octave | `octave_shift=0` (was -1) |
| Horns/Drone 100% overlap | `Light_Drone` dropped to sub-bass | `octave_shift=-2` (was -1) |
| Bass too quiet | `Deep_Rumble` velocity raised | `velocity_level=0.85` (was 0.6) |
| Blurry tremolo | `Tremolo_Rise` bow speed slowed | `bow_speed=0.08` (was 0.18) |

#### Iteration 2 — Tremolo_Rise is still the bottleneck

After round 1 fixes, tracks 01 and 02 immediately scored **EXCELLENT**,
but track 05 (Undying Light) got *worse* — jumped to **CRITICAL**:

```
LOW   6.2%   🔴 critically low
MID  91.8%   🔴 critically overloaded
HIGH  2.0%   🔴 critically low
Tremolo_Rise: 9 921 notes — reduce density to avoid clutter
Overall: ☆☆☆☆☆  CRITICAL
```

**Root cause discovered:** `TremoloStringsGenerator` ignores `TrackConfig.density`.
Its note count is determined entirely by `bow_speed` inside the generator:

```python
# From melodica/generators/tremolo_strings.py:
total_strokes = max(1, int(total_dur / self.bow_speed))
```

At `bow_speed=0.08` over a 180-second track:
`180 / 0.08 = 2 250 strokes × 4–5 chord notes = ~9 900 notes`.

Cutting `TrackConfig.density` from `0.65` to `0.12` had **zero effect**
because the generator doesn't read that field for stroke count.

**Fix — round 2:**

```python
# Before (9 921 notes):
TremoloStringsGenerator(variant="chord", bow_speed=0.08), density=0.40

# After (1 368 notes):
TremoloStringsGenerator(variant="single", bow_speed=0.2), density=0.12, octave_shift=-1
```

Two changes at once:
- `variant="single"` — plays one note per stroke instead of a full chord voicing
- `bow_speed=0.2` — maximum allowed value, cuts strokes from 2 250 → 900
- `octave_shift=-1` — moves the tremolo mass from mid-high into mid-low,
  freeing space for choir and horns above

#### Final results after 3 iterations

| Track | LOW | MID | HIGH | Rating |
|-------|-----|-----|------|--------|
| 01 The Ruins Breathe | 20% | 49% | 31% | ★★★★★ **EXCELLENT** |
| 02 Warriors of the Khalsa | 30% | 50% | 20% | ★★★★★ **EXCELLENT** |
| 03 The Temple Falls | 21% | 66% | 14% | ★★★☆☆ **ACCEPTABLE** |
| 04 Requiem of the Fallen | 10% | 50% | 40% | ★★★☆☆ **ACCEPTABLE** |
| 05 Undying Light | 29% | 63% | 8% | ★★★☆☆ **ACCEPTABLE** |

Tracks 03–05 remain slightly outside the ideal window — this is expected
and intentional: an action track (03) naturally concentrates energy in the mid register,
an elegy (04) leans high, a climax (05) pushes bass. These are compositional
decisions, not technical errors. The **CRITICAL → ACCEPTABLE** jump on track 05
was achieved by fixing a single generator parameter (`bow_speed`).

#### Key lessons

1. **`TrackConfig.density` ≠ generator note count.**
   Always check generator-specific parameters (`bow_speed`, `note_density`,
   `voice_count`) when the Suggestions section reports a track with thousands of notes.
   Setting `density=0.0` on TrackConfig will not silence a generator that
   calculates its output from duration alone.

2. **`octave_shift` is your primary register tool.**
   Moving a track ±1 octave shifts its entire note population into a new band
   without changing its musical content or harmonic role.

3. **Analyze per-file, not just album-wide.**
   The album-wide verdict can look reasonable while one track is completely broken.
   The `midi_analyzer.py` prints a verdict for every file in the directory — read each one.

4. **One iteration is rarely enough.**
   Plan for at least 2–3 analyze → fix → regenerate cycles.
   Each round reveals second-order effects (e.g., fixing overlap in one track
   exposes a different imbalance in another).

5. **The balance targets are genre-adjustable.**
   The defaults in `midi_analyzer.py` (`_BALANCE_TARGETS`) assume cinematic/orchestral.
   For electronic music, bass-heavy genres, or solo piano you may want to tighten
   or widen the LOW/MID/HIGH windows.

## Engines

| ID | Name | Algorithm |
|----|------|-----------|
| 0  | `functional` | 18th-century functional harmony, cadential T→S→D→T |
| 1  | `rules` | Viterbi search over a weighted chord-progression rule graph |
| 2  | `adaptive` | Heuristic candidate search: simplicity + melody fit + look-ahead |
| 3  | `hmm` | Advanced HMM-based search with cadential and functional layers |
| 4  | `coupled_hmm` | **Default.** Hierarchical "First Principles" HMM (Key + Chord layers) |

### Coupled HMM (First Principles Harmony)
Inspired by recent research (arXiv:2407.21130), this engine implements a dual-layer Hidden Markov Model:
- **Chord Layer**: Learns interval-based (modulo 12) transition probabilities and probabilistic note emissions.
- **Key Layer**: Tracks the tonality and manages natural modulations by analyzing the "weight" of chord sequences within a key center.

## Chord Detection

```python
from melodica import detect_chord, detect_scale, Note

notes = [Note(60, 0, 1), Note(64, 0, 1), Note(67, 0, 1)]  # C major
chord = detect_chord(notes)
# ChordLabel(root=0, quality=Quality.MAJOR, …)

scale = detect_scale(notes)
# Scale(root=0, mode=Mode.MAJOR)
```

## MIDI I/O

```python
from melodica import from_midi, chords_to_midi, notes_to_midi

melody = from_midi("song.mid", track=0)
chords = harmonize(melody)
chords_to_midi(chords, "chords.mid", voicing="open")
```

### Channel Pool Isolation (MIDI Track Isolation)

To prevent pitch bend cross-talk in multitrack MIDI files (since standard MIDI pitch bend affects the entire channel rather than individual notes), Melodica isolates channel pools:
- **Disjoint Pools**: Every track gets a disjoint pool of 3 MIDI channels (e.g., Track 1 gets `[0, 1, 2]`, Track 2 gets `[3, 4, 5]`, etc.).
- **Drums Protection**: Channel 9 (the 10th channel) is reserved exclusively for drums and is bypassed by tonal instruments.
- **Cross-Talk Elimination**: Microtonal pitch bends applied to notes on one track are kept strictly within that track's isolated channels and will never affect other tracks.



## Generators & Idea Tool

```python
from melodica import (
    harmonize, Note, Scale, Mode, IdeaTrack, PhraseInstance, StaticPhrase,
    NoteInfo, generate_idea, slots_to_notes, notes_to_midi,
)
from melodica.generators.melody import MelodyGenerator

key = Scale(root=0, mode=Mode.MAJOR)
melody = [Note(60, 0, 1), Note(62, 1, 1), Note(64, 2, 1), Note(65, 3, 1)]
chords = harmonize(melody, key=key)

gen = MelodyGenerator()
seed = PhraseInstance(static=StaticPhrase(notes=[NoteInfo(60, 0, 1)]))

track = IdeaTrack(seed_phrases=[seed], generator=gen, phrase_order="AABA")
slots = generate_idea(track, chords, key, beats_per_slot=4.0)
notes = slots_to_notes(slots)
notes_to_midi(notes, "idea.mid", bpm=120)
```

## Project Layout

```
melodica/
├── __init__.py          # public API
├── types.py             # domain model (enums, dataclasses, invariants)
├── utils.py             # pure pitch-class arithmetic
├── detection.py         # chord detection, scale detection
├── midi.py              # MIDI adapter (only module using mido)
├── idea.py              # Idea Tool six-stage pipeline
├── engines/
│   ├── __init__.py      # HarmonizerPort + build_engine() factory
│   ├── functional.py    # Engine 0 — 18th-century functional
│   ├── rule_based.py    # Engine 1 — Viterbi + rule graph
│   └── adaptive.py      # Engine 2 — heuristic candidate search
├── generators/
│   ├── __init__.py              # PhraseGenerator ABC, GeneratorParams, freeze()
│   ├── melody.py                # MelodyGenerator
│   ├── markov.py                # MarkovMelodyGenerator
│   ├── arpeggiator.py           # ArpeggiatorGenerator
│   ├── bass.py                  # BassGenerator & walking bass patterns
│   ├── chord_gen.py             # ChordGenerator
│   ├── ostinato.py              # OstinatoGenerator
│   ├── piano_comp.py            # PianoCompGenerator
│   ├── strum.py                 # StrumGenerator
│   ├── staccato.py              # StaccatoGenerator
│   ├── ambient.py               # AmbientGenerator
│   ├── vocal_melisma.py         # VocalMelismaGenerator
│   ├── neural_melody.py         # NeuralMelodyGenerator (torch-based)
│   ├── rhythm_lab.py            # RhythmLab for grid-based rhythms
│   └── (100+ more specialized generators)
└── rule_db/
    ├── __init__.py      # ChordProgressionRuleDB
    └── default.json     # built-in classical/jazz/pop rules
tests/
├── test_types.py
├── test_detection.py
├── test_engines.py
├── test_generators.py
└── test_idea.py
```

## Architecture

Melodica follows hexagonal (ports-and-adapters) architecture with strict layer separation:

```
Presentation / CLI
      ↓
Application  (harmonize, generate_idea)
      ↓
Domain       (types, engines, generators — pure logic)
      ↑
Infrastructure adapters (midi.py — the only I/O boundary)
```

- **Domain → no I/O**: `types.py`, `utils.py`, `detection.py`, `engines/`, `generators/` contain zero I/O.
- **Infrastructure isolation**: only `midi.py` imports `mido`.
- **DIP**: engines depend on `HarmonizerPort` protocol; callers use `build_engine()` factory.
- **ISP**: `HarmonizerPort` has one method (`harmonize`); `PhraseGeneratorProtocol` has one (`render`).

## Dependencies

| Package | Purpose |
|---------|---------|
| `mido`  | MIDI file read/write |
| `numpy` | Krumhansl-Schmuckler key profiles |

Python ≥ 3.11.

## Development

```bash
pip install -e ".[dev]"
pytest
```
