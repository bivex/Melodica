# HMM Harmonization: Gold Standard Training & Integration

This document details the architecture, training process, and integration of the advanced Hidden Markov Model (HMM) used for intelligent harmonization in Melodica.

## 1. Model Architecture
Melodica utilizes a **Coupled HMM (Hierarchical Hidden Markov Model)** architecture, inspired by the research of Dmitri Tymoczko and Mark Newman. It consists of two functionally distinct layers:

*   **Layer 1 (Chord Layer)**: Maps melody notes to chord states. It manages **108 discrete states** (12 roots × 9 chord types).
*   **Layer 2 (Key Layer)**: Tracks the global tonal center (key) to ensure harmonic consistency and manage modulations across **78 musical modes**.

### State Space Abstractions
*   **Octave Invariance**: All notes are reduced to 12 pitch classes (0-11).
*   **Voicing Abstraction**: Chord inversions and specific voice distributions are abstracted to root-type successions.
*   **9 Chord Qualities**: The vocabulary includes Major, Minor, Diminished, Augmented, SUS2, SUS4, and the recently added **Major7, Minor7, and Dominant7**.

---

## 2. Data Preparation: The "Gold Standard" Corpus
To achieve high harmonic intelligence, we generated a massive synthetic dataset.

*   **Source**: `scripts/generate_synthetic_corpus.py`.
*   **Scope**: **7,800 synthetic songs**.
*   **Diversity**: 
    *   Covers all **78 musical modes** in the database.
    *   Generated **100 songs per mode** across all 12 root keys.
    *   Includes functional patterns, modal loops, and randomized melodic passing tones.
    *   **7th Chord Integration**: 50% of the corpus utilizes 4-note 7th chord structures where scale-appropriate.

---

## 3. Turbo Training Process
Training is performed using the **Expectation-Maximization (EM)** algorithm, highly optimized for Apple Silicon via **Metal Performance Shaders (MPS)**.

*   **Script**: `scripts/train_full_modes.py`.
*   **Vectorization**: The entire 7,800-song corpus is processed as a single batched 3D tensor.
*   **Hyperparameters**:
    *   `MAX_ITER = 100`
    *   `TARGET_DELTA = 1e-5` (Convergence threshold).
    *   `Device`: `mps` (Hardware acceleration).
*   **Performance**: Parameter convergence with minimal likelihood drift is achieved in under 60 seconds on a Mac Mini.

---

## 4. Advanced Harmonization Features

### Hybrid Constrained Decoding
The harmonizer supports **Hard Constraints**, allowing composers to fix specific chords as "harmonic pillars." The Viterbi algorithm then calculates the most statistically optimal path between these anchors, ensuring a seamless blend of human intent and AI logic.

### Duration & Metric Weighting
Melodica implements **Weighted Harmonic Anchors**:
*   **Duration Weighting**: Notes are weighted by the square root of their active duration (`sqrt(dur)`).
*   **Metric Weighting**: Notes on strong beats (e.g., Beat 1 and 3) receive higher harmonic salience multipliers.
*   **Normalization**: Emissions are normalized across time steps to ensure statistical stability regardless of melodic density.

### Universal Modal Priors
Layer 2 dynamically calculates priors for all **78 global modes**. This allows the system to track any tonal center (e.g., Arabic Sikah, Japanese Hirojoshi) natively, rather than approximating them as standard Major or Minor keys.

---

## 5. Usage in Project Scripts
To use the hybrid mode in an album or track script:

```python
parts = [IdeaPart(
    name="Ruins",
    scale=Scale(root=4, mode=Mode.ARABIC_SIKAH),
    progression_type="constrained_hmm",
    progression_list=["Im7:4.0", "IVaug:4.0"] # Fixed anchors
)]
```

The harmonizer will guarantee the anchors are used while intelligently filling the gaps based on the melody.
