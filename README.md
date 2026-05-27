# Melodica
**Software Specification and Documentation**

> A composition generator for modern music.

Melodica implements a three-engine harmonization architecture with an extensive phrase-generation library for automated music composition, providing a clear, testable Python API.

---

## Table of Contents

1. [Scope](#1-scope)
2. [Normative References](#2-normative-references)
3. [Installation](#3-installation)
4. [System Architecture](#4-system-architecture)
   4.1. [Hexagonal Architecture](#41-hexagonal-architecture)
   4.2. [Engines](#42-engines)
   4.3. [MIDI I/O & Channel Isolation](#43-midi-io--channel-isolation)
5. [Operational Procedures](#5-operational-procedures)
   5.1. [Quick Start](#51-quick-start)
   5.2. [Script Examples](#52-script-examples)
   5.3. [Chord Detection](#53-chord-detection)
   5.4. [Generators & Idea Tool](#54-generators--idea-tool)
   5.5. [Advanced Arrangement & Expression Pipeline](#55-advanced-arrangement--expression-pipeline)
6. [Diagnostic Tools (MIDI Analyzer)](#6-diagnostic-tools-midi-analyzer)
   6.1. [Reporting Metrics](#61-reporting-metrics)
   6.2. [Register Balancing Workflow](#62-register-balancing-workflow)
7. [Development](#7-development)

**Annexes**
* [Annex A (Informative): Case Study — Register Balancing](#annex-a-informative-case-study--register-balancing)
* [Annex B (Informative): Project Directory Structure](#annex-b-informative-project-directory-structure)

---

## 1. Scope

This document specifies the architecture, components, and operational procedures for the **Melodica** software system. Melodica is designed for automated music composition, providing capabilities for phrase-generation, chord detection, and MIDI input/output isolation to ensure high-fidelity multitrack rendering.

## 2. Normative References

The following dependencies and environments are required for the execution and development of the system.

* **Python Environment**: Version ≥ 3.11
* **`mido`** (Required): Facilitates MIDI file read/write operations.
* **`numpy`** (Required): Core mathematical dependency for Krumhansl-Schmuckler key profiles.
* **`music21`** (Optional): Used for key detection and advanced consonance analysis.

## 3. Installation

To install the application in development mode with test dependencies, execute the following command:

```bash
pip install -e ".[dev]"
```

## 4. System Architecture

### 4.1. Hexagonal Architecture

Melodica adheres to a strict hexagonal (ports-and-adapters) architecture to ensure layer separation:

```text
Presentation / CLI
      ↓
Application  (harmonize, generate_idea)
      ↓
Domain       (types, engines, generators — pure logic)
      ↑
Infrastructure adapters (midi.py — the only I/O boundary)
```

* **Domain (No I/O)**: `types.py`, `utils.py`, `detection.py`, `engines/`, `generators/` contain zero I/O operations.
* **Infrastructure Isolation**: Only `midi.py` imports `mido`.
* **Dependency Inversion Principle (DIP)**: Engines depend on the `HarmonizerPort` protocol; callers utilize the `build_engine()` factory.
* **Interface Segregation Principle (ISP)**: `HarmonizerPort` has one method (`harmonize`); `PhraseGeneratorProtocol` has one method (`render`).

### 4.2. Engines

The system implements multiple harmonization engines:

| ID | Name | Algorithm Specification |
|:---|:---|:---|
| 0 | `functional` | 18th-century functional harmony, cadential T→S→D→T |
| 1 | `rules` | Viterbi search over a weighted chord-progression rule graph |
| 2 | `adaptive` | Heuristic candidate search: simplicity + melody fit + look-ahead |
| 3 | `hmm` | Advanced HMM-based search with cadential and functional layers |
| 4 | `coupled_hmm` | **Default.** Hierarchical "First Principles" HMM (Key + Chord layers) |

**Coupled HMM (First Principles Harmony)**
Inspired by external research (arXiv:2407.21130), this default engine implements a dual-layer Hidden Markov Model:
* **Chord Layer**: Learns interval-based (modulo 12) transition probabilities and probabilistic note emissions.
* **Key Layer**: Tracks tonality and manages natural modulations by analyzing the relative weights of chord sequences within a key center.

### 4.3. MIDI I/O & Channel Isolation

To prevent pitch bend cross-talk in multitrack MIDI files, Melodica structurally isolates channel pools:
* **Disjoint Pools**: Every track is assigned a disjoint pool of 3 MIDI channels (e.g., Track 1 utilizes channels `[0, 1, 2]`).
* **Drums Protection**: Channel 9 (the 10th channel) is reserved exclusively for percussive instruments and bypassed by tonal processors.
* **Cross-Talk Elimination**: Microtonal pitch bends are confined to isolated channels to guarantee zero interference between tracks.

## 5. Operational Procedures

### 5.1. Quick Start

```python
from melodica import harmonize, Note, Scale, Mode

melody = [
    Note(pitch=60, start=0.0, duration=1.0),  # C4
    Note(pitch=62, start=1.0, duration=1.0),  # D4
    Note(pitch=64, start=2.0, duration=1.0),  # E4
    Note(pitch=65, start=3.0, duration=1.0),  # F4
]

# Uses default 'coupled_hmm' engine
chords = harmonize(melody, chord_rhythm=2.0)
for c in chords:
    print(c)
```

### 5.2. Script Examples

**I. Standard Workflow: DF Downtempo**
The `scripts/df_downtempo.py` script validates the standard workflow: reading settings, generating harmonization, and exporting MIDI.
```bash
python scripts/df_downtempo.py
```

**II. Advanced Workflow: Catchy Pop-Epic Melody**
The `scratch/demo_catchy_melody.py` script validates production-grade workflows utilizing the `MelodyGenerator` and automated MIDI CC expressiveness:
* Implements motivic development (`motif_probability=0.7`), contour shaping (`phrase_contour="arch"`), and dynamic energy curves (`drama_shape="epic"`).
* Automates MIDI CC mapping: sustain pedal (**CC64**), expression sweeps (**CC11**), delayed vibrato LFO (**CC1**), and channel mixing (**CC7**).

```bash
python3 scratch/demo_catchy_melody.py
# Exports to output/demo_catchy/demo_catchy_melody.mid
```

### 5.3. Chord Detection

```python
from melodica import detect_chord, detect_scale, Note

notes = [Note(60, 0, 1), Note(64, 0, 1), Note(67, 0, 1)]  # C major
chord = detect_chord(notes) # Returns: ChordLabel(root=0, quality=Quality.MAJOR, …)
scale = detect_scale(notes) # Returns: Scale(root=0, mode=Mode.MAJOR)
```

### 5.4. Generators & Idea Tool

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

### 5.5. Advanced Arrangement & Expression Pipeline

To compose structured tracks (Intro → Verse → Climax), use the 3-stage `IdeaTool` pipeline:

1. **Track Config & Generator Assignment**: Map instruments to generators and assign frequency bands (`octave_shift`).
2. **Structure & Schedule**: Slice the track into `IdeaPart` objects. Use `structure_to_schedule` to define repeating themes (`A`, `B`, `C`), variations (`A:var`), or silence (`R`).
3. **Modifier Pipeline**: Post-process generated notes using `ModifierPipeline` to inject "humanization" and dynamics (`HumanizeModifier`, `VelocityCurveModifier`, `MetricAccentModifier`).

```python
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
from melodica.modifiers import ModifierPipeline, HumanizeModifier, MetricAccentModifier

# 1. Parts & Scheduling
part = IdeaPart(
    name="Intro", bars=8, scale=Scale(2, Mode.MINOR),
    progression_type="coupled_hmm",
    track_phrase_schedules={
        "Sub_Bass":    structure_to_schedule("A", 8),
        "Epic_Strings": structure_to_schedule("R", 8), # Strings rest during Intro
    }
)

# 2. Generation
config = IdeaToolConfig(style="cinematic", parts=[part], tracks=tracks)
notes_dict = IdeaTool(config).generate()

# 3. Humanization & Modifiers
pipeline = ModifierPipeline(base_notes=notes_dict["Sub_Bass"])
pipeline.add_modifier(HumanizeModifier(timing_std=0.02, velocity_std=5.0))
pipeline.add_modifier(MetricAccentModifier(strength=0.2))
notes_dict["Sub_Bass"] = pipeline.process(mod_context)
```

## 6. Diagnostic Tools (MIDI Analyzer)

The `scripts/midi_analyzer.py` module serves as the unified diagnostic tool for auditing MIDI outputs.

```bash
# Analyze a single track
python3 scripts/midi_analyzer.py output/album_ainulindale/I_The_Theme_of_Eru.mid

# Analyze an entire album directory (skip consonance profiling with --no-music21)
python3 scripts/midi_analyzer.py output/album_ainulindale/ [--no-music21]
```

### 6.1. Reporting Metrics

| Inspection Category | Monitored Parameters |
|:---|:---|
| **Track Stats & Roles** | Note count, pitch range, velocity, density (notes/s), automated role assignment. |
| **Register Distribution** | 9-band breakdown mapping frequency distributions. |
| **Psychoacoustic Constraints**| Audits for frequency masking, temporal masking, harmonic fusion, register masking, and brightness overload. |
| **Harmonic Analysis** | Cross-track clashing detection grouped by interval (m2, TT, M7, etc.). |
| **Timeline** | Component active-state tracking across quarter-divisions. |
| **music21 Advanced** | Key detection confidence, ambitus, low-interval mud (LIM) warnings, step/leap ratios. |
| **Suggestions** | Actionable rectifications (e.g., density reductions, velocity adjustments). |

### 6.2. Register Balancing Workflow

To resolve frequency masking and overlap warnings:
1. **Analyze**: Execute the analyzer and inspect **Register Distribution** and **Suggestions**.
2. **Diagnose**: Review the `Band` column in **Track Stats**. Establish a strict one-track-per-band rule.
3. **Rectify Position**: Utilize `octave_shift` on `TrackConfig` to decouple intersecting elements.
   ```python
   TrackConfig(name="Defiant_Brass", ..., octave_shift=1) # Shifts to mid-high
   ```
4. **Rectify Density**: Adjust internal generator parameters. Note that `TrackConfig.density` governs external phrase-level density. Internal density is generator-specific.
   ```python
   TremoloStringsGenerator(bow_speed=0.20) # Modifies internal stroke count
   ```
5. **Re-Verify**: Regenerate and re-execute the analyzer.

## 7. Development

Unit and integration tests are executed via `pytest`:

```bash
pytest
```

---

## Annex A (Informative): Case Study — Register Balancing

### A.1. Context
**Target:** `scripts/album_tandumi_ruins.py` (5-track album, Arabic Sikah scale).

### A.2. Iteration 1
**Execution:**
```bash
python3 scripts/album_tandumi_ruins.py
python3 scripts/midi_analyzer.py output/album_tandumi_ruins/ --no-music21
```

**Diagnostic Output:**
```text
LOW  (bass foundation)   13.3%   target 15–35%  🟡 1.7% short
MID  (body / harmony)    77.4%   target 35–60%  🟡 17.4% over target
HIGH (air / presence)     9.2%   target 15–35%  🟡 5.8% short
Overall balance: ★★☆☆☆  NEEDS WORK
```

**Applied Corrections (Round 1):**
* `LOW` deficit offset by shifting `Battle_Bass` and `Chaos_Taiko` to `octave_shift=-2`.
* `HIGH` deficit offset by shifting `Warrior_Melody` to `octave_shift=2`.
* Masking conflicts resolved by separating `Glory_Horns` (`octave_shift=0`) and `Light_Drone` (`octave_shift=-2`).
* Over-dense tremolo reduced via `bow_speed=0.08`.

### A.3. Iteration 2
**Diagnostic Output:** Track 05 downgraded to **CRITICAL** (MID load: 91.8%). `Tremolo_Rise` recorded 9,921 notes.

**Root Cause:** `TremoloStringsGenerator` dynamically calculates notes based on `bow_speed`, effectively ignoring `TrackConfig.density`.
**Applied Corrections (Round 2):**
```python
# Before
TremoloStringsGenerator(variant="chord", bow_speed=0.08), density=0.40

# After (reduced output to 1,368 notes)
TremoloStringsGenerator(variant="single", bow_speed=0.2), density=0.12, octave_shift=-1
```

### A.4. Conclusions
After 3 iterations, track distributions normalized to standard limits (**EXCELLENT** to **ACCEPTABLE** ratings).
* **Key Finding 1:** `TrackConfig.density` does not universally silence generators executing time-based internal loops.
* **Key Finding 2:** Multiple recursive `analyze → fix → regenerate` cycles are mandatory for proper balancing.

---

## Annex B (Informative): Project Directory Structure

```text
melodica/
├── __init__.py          # Public API
├── types.py             # Domain model (enums, dataclasses, invariants)
├── utils.py             # Pure pitch-class arithmetic
├── detection.py         # Chord detection, scale detection
├── midi.py              # MIDI adapter (I/O boundary)
├── idea.py              # Idea Tool six-stage pipeline
├── engines/
│   ├── __init__.py      # HarmonizerPort + build_engine() factory
│   ├── functional.py    # Engine 0
│   ├── rule_based.py    # Engine 1
│   └── adaptive.py      # Engine 2
├── generators/
│   ├── __init__.py      # PhraseGenerator ABC, GeneratorParams, freeze()
│   ├── melody.py        # MelodyGenerator
│   ├── markov.py        # MarkovMelodyGenerator
│   └── (100+ specialized phrase generators)
└── rule_db/
    └── default.json     # Built-in classical/jazz/pop rules
tests/
├── test_types.py
└── test_detection.py
```
