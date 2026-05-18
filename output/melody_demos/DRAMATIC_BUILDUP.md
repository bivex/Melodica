# Dramatic Buildup Demo

## What it does

This demo showcases the **Dramatic Arc** and **Global Buildup** capabilities of the `MelodyGenerator`. It demonstrates how a melody can evolve from a simple opening to an intense, complex climax and then resolve.

**Key Features Demonstrated:**
- **Global Buildup**: Increasing density, syncopation, and register across multiple sections (Intro -> Verse -> Chorus).
- **Micro-Buildup**: Local tension shaping within a section (Chorus peak).
- **Motivic Narrative**: Evolution of a theme (Full Motif -> Fragments -> Sequence -> Return).
- **Tension-Aware Pitching**: Selection of more expressive/tense notes during dramatic peaks.
- **Dramatic Pauses**: Natural breathing spaces after large melodic leaps.

---

## How to run

```bash
# Generate the dramatic buildup demo MIDI
python3 scripts/demo_dramatic_buildup.py
```

**Output:**
- `output/melody_demos/dramatic_buildup.mid`

---

## Dramatic Components

| Feature | Low Tension (Intro) | High Tension (Chorus Peak) |
|---------|---------------------|----------------------------|
| **Density** | Sparse (half/quarter notes) | Dense (eighth/sixteenth notes) |
| **Register** | Mid-Low (around C4) | High (up to C6 or higher) |
| **Pitching** | Chord Tones (1-3-5) | Expressive Tones (9ths, passing tones) |
| **Motif** | Full, stable statement | Fragments, inversions, sequences |
| **Rhythm** | Straight, on-beat | Syncopated, urgent |

---

## How it works (SDK Internals)

The `MelodyGenerator` orchestrates several sub-modules controlled by the `DramaticArc`:

1. **DramaticArc (`_melody_drama.py`)**: Computes a tension value (0.0-1.0) based on global progress and a chosen shape (`dramatic`, `epic`, `crescendo`).
2. **MotifManager (`_melody_motif.py`)**: Receives "orders" from the drama arc to fragment or invert motifs to build energy.
3. **RhythmBuilder (`_melody_rhythm.py`)**: Dynamically adjusts note density and syncopation probabilities in real-time as the tension curve rises.
4. **MelodyPitchSelector (`_melody_pitch.py`)**: Nudges pitch choices toward higher registers and less stable scale degrees at high tension points.
5. **RenderContext (`render_context.py`)**: Carries state between sections, allowing the generator to "know" it's at 50% or 90% of the song's duration.

---

## Listening Guide

1. **0:00 - Intro**: Simple, low-energy melody. Stable intervals.
2. **0:15 - Verse**: Slight increase in movement, but still grounded.
3. **0:30 - Chorus**: The buildup begins. Notes become more frequent, syncopation increases, and the melody starts to climb higher.
4. **0:45 - Bridge/Peak**: Maximum intensity. Fragments of the original motif are thrown around in a high register with expressive leaps.
5. **0:55 - Outro**: The melody returns to its original "full" motif form, moves back to the middle register, and simplifies for a satisfying resolution.

---

## Listening

Open `output/melody_demos/dramatic_buildup.mid` in your favorite DAW.
The melody uses General MIDI Program 1 (Grand Piano) for clarity of the melodic line.
