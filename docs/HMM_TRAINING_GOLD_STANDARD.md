# HMM Harmonization: Gold Standard Training & Integration

This document details the architecture, training process, and integration of the advanced 6-chord Hidden Markov Model (HMM) used for intelligent harmonization in Melodica.

## 1. Model Architecture
Melodica utilizes a **Coupled HMM (Hierarchical Hidden Markov Model)** architecture, inspired by the research of Dmitri Tymoczko. It consists of two distinct layers:

*   **Layer 1 (Chord Layer)**: Maps melody notes to chord states. It manages 72 states (12 roots × 6 chord types).
*   **Layer 2 (Key Layer)**: Tracks the global tonal center (key) to ensure harmonic consistency and manage modulations.

### Supported Chord Types (6 Qualities):
The model has been expanded beyond standard Major/Minor to support:
0. **Major**
1. **Minor**
2. **Diminished**
3. **Augmented**
4. **SUS2** (Suspended 2nd)
5. **SUS4** (Suspended 4th)

---

## 2. Data Preparation: The "Gold Standard" Corpus
To achieve high harmonic intelligence, we generated a massive synthetic dataset.

*   **Source**: `scripts/generate_synthetic_corpus.py`.
*   **Scope**: **7,800 synthetic songs**.
*   **Diversity**: 
    *   Covers all **78 musical modes** available in the `MODE_DATABASE` (Diatonic, Ethnic, Jazz, and Synthetic modes).
    *   Generated **100 songs per mode** across all 12 root keys.
    *   Includes functional progressions (T-S-D-T), modal movements, and melodic passing tones.
*   **Format**: `.ntc` (Note-Time-Chord), ensuring mathematical compatibility with classical HMM training methods.

---

## 3. Turbo Training Process
Training is performed using the **Expectation-Maximization (EM)** algorithm, highly optimized for Apple Silicon via **Metal Performance Shaders (MPS)**.

*   **Script**: `scripts/train_full_modes.py`.
*   **Vectorization**: The entire 7,800-song corpus is processed in parallel as a single 3D tensor, maximizing GPU utilization.
*   **Hyperparameters**:
    *   `MAX_ITER = 100` (Maximum EM iterations).
    *   `TARGET_DELTA = 1e-5` (Convergence threshold for 0.001% parameter stability).
    *   `Device`: `mps` (Hardware acceleration on Mac Mini).
*   **Convergence**: On a Mac Mini, the model typically converges in ~50-60 seconds, achieving a high degree of statistical stability.
*   **Output**: Trained weights are saved to `melodica/harmonize/weights/` as `pnote_full.txt` (emissions) and `pchange_full.npy` (transitions).

---

## 4. Integration with Coupled HMM Harmonizer
The `CoupledHMMHarmonizer` class in `melodica/harmonize/coupled_hmm.py` is designed to utilize these weights dynamically.

### Implementation Details:
1.  **Weight Loading**: The harmonizer automatically loads the "Gold Standard" weights upon initialization.
2.  **Viterbi Decoding**: It uses the Viterbi algorithm to find the "most likely" sequence of chords. It evaluates:
    *   **Note Emissions**: How well the melody notes fit into a specific chord type.
    *   **Interval Transitions**: The statistical likelihood of moving from one chord to another (e.g., Minor to Major via a Perfect 4th).
3.  **Active Note Extraction**: The harmonizer analyzes all notes active during a specific time slice (e.g., a half-bar), ensuring that even long melodic tones influence the harmonic choice.

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

## 5. Benefits for the Composer
*   **Modal Awareness**: Since the model was trained on 78 modes, it understands the unique harmonic requirements of non-Western scales (e.g., Sikah, Bayati).
*   **Modern Color**: Support for `sus2`, `sus4`, and `augmented` chords allows for more atmospheric, cinematic, and non-traditional textures.
*   **Stability**: The "Gold Standard" corpus ensures that the harmonizer makes musically logical choices even when faced with complex or chromatic melodies.
