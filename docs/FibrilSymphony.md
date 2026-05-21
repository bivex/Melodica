# FIBRIL Symphony & Performance Engine

> **Melodica Intelligence Level:** 4.0 (Cascading Polyphony)  
> **Architecture:** 48-Voice Symbolic Performance Suite  
> **Inspiration:** *FIBRIL — Algorithmic Harmonizer (Max/MSP)*

## 1. Overview

**Fibril Symphony** is a monumental orchestral demonstration of Melodica's capability to generate massive, harmonically pure polyphonic clusters. Unlike traditional HMM-based harmonization, which focuses on selecting the "next best chord," the **Fibril Engine** focuses on **Voice Allocation**—the process of constructing a complex harmonic mass from the ground up, voice by voice.

## 2. Core Engine: FibrilEngine

The engine implements the "Cascading Harmonic Construction System," transforming a single melodic line into a dense 48-voice arrangement.

### 2.1 The Rank System
The harmonic space is divided into **8 Ranks**, each assigned a specific scale degree (Tonic, Dominant, etc.) and a priority order. 
- **Dynamic Activation:** Ranks are activated when the melody hits their corresponding scale degree.
- **Rank Density:** The number of voices a rank contributes is determined by the **GCI (Grey Code Integer)**, which Melodica maps from the melody's `velocity`. High intensity = higher density.

### 2.2 Rooted Note Requirement
To ensure maximum harmonic clarity (even with 48 simultaneous voices), the engine follows a strict rule: **Every active Rank must voice its Root and Perfect Fifth before any other tones.** This creates a "hollow but powerful" sound profile that anchors the orchestral mass.

### 2.3 Cascading Probability Allocation
For every single note (out of 48), the engine recalculates a **Normalized Probability Map (128-slot)**:
1.  **Hard Blocking:** Prevents notes in extreme ranges (sub-low and ultrasonic).
2.  **Gaussian Spatial Bias:** Applies a "cloud" of probability around the rank's center (Middle C focus), preventing mid-range congestion.
3.  **Perfect Interval Boost:** Strongly rewards notes that form 4ths or 5ths with already selected voices.
4.  **Repetition Penalty:** Forbids exact duplicates within the same cluster.

## 3. Orchestration of the Symphony

The "Fibril Symphony" demo distributes these 48 voices across four specialized layers:

| Layer | GM Instrument | Register | Function |
| :--- | :--- | :--- | :--- |
| **Flute Lead** | 73 (Flute) | High | **The Controller.** Its velocity dictates the polyphonic density of the entire orchestra. |
| **Strings High** | 44 (Tremolo) | > MIDI 72 | **Atmospheric Air.** Rapid cascading clusters that shimmer above the melody. |
| **Organ Cluster** | 19 (Church Organ) | MIDI 48-72 | **The Body.** Dense, majestic mid-layer that provides the "Symphonic" scale. |
| **Strings Low** | 42 (Cello/Bass) | < MIDI 48 | **The Foundation.** Heavy, episodic "Doom Notes" that anchor the harmonic flow. |

## 4. Analytical Characteristics

When analyzed by the `visualize_arrangement.py` tool, Fibril-based tracks show:
- **Peak Polyphony:** Vertical density indicators often reach the maximum (9+ voices).
- **Interval Profile:** A high dominance of **Perfect Fifths**, giving the music a "Grave" and "Majestic" character.
- **Narrative Tension:** A direct correlation between Lead expression and Orchestral volume.

## 5. Usage in Scripts

To use the Fibril logic in your own album scripts:

```python
from melodica.engines.fibril_engine import FibrilEngine

# 1. Initialize engine
engine = FibrilEngine()

# 2. Harmonize a melody
req = types.HarmonizationRequest(
    melody=my_melody, 
    key=my_key, 
    engine="fibril"
)
chords = engine.harmonize(req)

# 3. Access the generated voices via metadata
for chord in chords:
    voices = chord.fibril_metadata["voices"]
    # Distribute 'voices' (list of MIDI ints) to your tracks
```

---
*Documented by Melodica Intelligence Suite — 2026*
