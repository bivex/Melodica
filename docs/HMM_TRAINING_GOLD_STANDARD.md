# HMM Harmonization: Gold Standard Training & Integration

This document details the architecture, training process, and integration of the advanced 6-chord Hidden Markov Model (HMM) used for intelligent harmonization in Melodica.

## 1. Model Architecture
Melodica utilizes a **Coupled HMM (Hierarchical Hidden Markov Model)** architecture, inspired by the research of Dmitri Tymoczko and Mark Newman. It consists of two functionally distinct layers:

*   **Layer 1 (Chord Layer)**: Maps melody notes to chord states. It manages **72 discrete states** (12 roots × 6 chord types).
*   **Layer 2 (Key Layer)**: Tracks the global tonal center (key) to ensure harmonic consistency and manage modulations via posterior probability estimation.

### State Space Abstractions
To maintain computational efficiency and statistical density, the model employs several key abstractions:
*   **Octave Invariance**: All notes are reduced to 12 pitch classes (0-11).
*   **Voicing Abstraction**: Chord inversions and specific voice distributions are ignored during training; the model focuses strictly on root-type successions.
*   **Extension Reduction**: Complex extensions (9ths, 11ths) are treated as melodic color or passing tones, reducing to their core triad or suspended qualities.

### Design Rationale: Why 6 Chord Types?
The vocabulary (Major, Minor, Diminished, Augmented, SUS2, SUS4) was selected to provide a balance between:
1.  **Harmonic Versatility**: Inclusion of suspended and augmented chords enables cinematic, modal, and non-functional textures often missing in triad-only systems.
2.  **Statistical Density**: Limiting the types prevents the transition matrices from becoming overly sparse, ensuring that the model learns robust probability distributions even for rare modes.
3.  **Modal Compatibility**: These six qualities cover the vast majority of diatonic and chromatic triads found across the 78 supported musical modes.

---

## 2. Data Preparation: The "Gold Standard" Corpus
To achieve high harmonic intelligence, we generated a massive synthetic dataset to serve as the ground truth for training.

*   **Source**: `scripts/generate_synthetic_corpus.py`.
*   **Scope**: **7,800 synthetic songs**.
*   **Diversity**: 
    *   Covers all **78 musical modes** available in the `MODE_DATABASE` (Diatonic, Ethnic, Jazz, and Synthetic modes).
    *   Generated **100 songs per mode** across all 12 root keys.
    *   Includes functional patterns (T-S-D-T), modal loops, and randomized melodic passing tones.
*   **Format**: `.ntc` (Note-Time-Chord), facilitating symbolic sequence modeling rather than raw MIDI heuristics.

---

## 3. Turbo Training Process
Training is performed using the **Expectation-Maximization (EM)** algorithm, highly optimized for Apple Silicon via **Metal Performance Shaders (MPS)**.

*   **Script**: `scripts/train_full_modes.py`.
*   **Vectorization**: The entire 7,800-song corpus is processed as a single batched 3D tensor, eliminating Python-level loops and maximizing GPU throughput.
*   **Hyperparameters**:
    *   `MAX_ITER = 100` (Upper limit for EM cycles).
    *   `TARGET_DELTA = 1e-5` (Convergence threshold).
    *   `Device`: `mps` (Hardware acceleration).
*   **Convergence**: On a Mac Mini, the model typically achieves **parameter convergence with minimal likelihood drift** in under 60 seconds.
*   **Output**: Trained weights are saved to `melodica/harmonize/weights/` as `pnote_full.txt` (note emissions) and `pchange_full.npy` (transition probabilities).

---

## 4. Integration with Coupled HMM Harmonizer
The `CoupledHMMHarmonizer` class in `melodica/harmonize/coupled_hmm.py` implements the hierarchical decoding logic.

### Implementation Details:
1.  **Viterbi Decoding**: Finds the most likely path through the 72-state chord space based on melody note emissions and interval-based transition probabilities.
2.  **Key Layer Posterior Tracking**: Layer 2 tracks the probability distribution over 24 possible keys (12 roots × Major/Minor). It applies **modulation penalties** to favor staying in the current key unless the harmonic evidence strongly suggests a tonal shift.
3.  **Dynamic Chord Priors**: The key tracking layer influences the chord layer by re-weighting chord probabilities based on their diatonic relationship to the current estimated key.
4.  **Metric Saliency**: The harmonizer analyzes all notes active during a specific time slice (e.g., a half-bar), ensuring that the underlying harmonic structure is informed by the totality of melodic movement.

### Usage in Project Scripts:
To use this harmonizer in an album or track script, set the `progression_type` to `coupled_hmm`:

```python
parts = [IdeaPart(
    name="Ruins",
    scale=Scale(root=4, mode=Mode.ARABIC_SIKAH),
    progression_type="coupled_hmm"
)]
```

---

## 5. Future Research Directions

### Hybrid Training
While the synthetic corpus provides exceptional modal breadth, a future "Fine-Tuning" phase using real-world symbolic corpora (e.g., MIDI or MusicXML collections) could improve:
*   Cadence realism and stylistic irregularity.
*   Genre-specific transition tendencies.

### Duration-Aware Emissions
Weighting melody notes by their duration and metric position would further improve harmonic accuracy. Sustained tones and downbeat onsets generally carry more harmonic weight than rapid passing tones; incorporating this into the emission logic would sharpen the model's "focus" on the true harmonic skeleton of a melody.

### Rhythm-Coupled Constraints
Future versions may incorporate phrase-level awareness, applying stronger stabilization at the end of musical phrases and allowing for more fluid transitions during melodic development.
