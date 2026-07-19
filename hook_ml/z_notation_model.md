# Formal Specification of Melodica's MLX Optimization Model in Z Notation

This document provides a formal mathematical description of the Melodica generative model and optimization pipeline using **Z Notation** (based on typed set theory and first-order predicate logic).

---

## 1. Given Sets, Types, and Constants

First, we define the basic types and domains of our system:

$$
\begin{align*}
  & [MIDI] \subseteq \mathbb{N} && \text{Domain of MIDI pitch values } (0 \dots 127) \\
  & [Time] == \mathbb{R}_{\ge 0} && \text{Time beats domain} \\
  & [Latent] == \mathbb{R}^{32} && \text{Laten space dimension} \\
  & Mode == \{ PHRYGIAN, AEOLIAN, LOCRIAN, HARMONIC\_MINOR, HUNGARIAN\_MINOR \}
\end{align*}
$$

We define a $Note$ as a tuple of pitch, start beat, and duration:

$$
Note == [ pitch: MIDI; start: Time; duration: \mathbb{R}_{> 0} ]
$$

---

## 2. State Schemas

### Scale Schema
Defines the target key and scale constraints for the optimization.

┌─ Scale ────────────────────────────────────────
│ root: MIDI
│ mode: Mode
│ degrees: \mathbb{P} MIDI
│ tonic: MIDI
│ dominant: MIDI
├────────────────────────────────────────────────
│ tonic = root
│ dominant = (root + 7) \bmod 12
│ \forall d: degrees \bullet d \in \{ root + i \mid i \in scale\_intervals(mode) \}
└────────────────────────────────────────────────

### Decoder Schema
Defines the parametric neural projection from the latent code $z$ to continuous melody properties.

┌─ MelodyDecoder ────────────────────────────────
│ f_{pitches}: Latent \rightarrow \mathbb{R}^{5 \times 7}
│ f_{gaps}: Latent \rightarrow \mathbb{R}^5
│ f_{durations}: Latent \rightarrow \mathbb{R}^5
├────────────────────────────────────────────────
│ \forall z: Latent \bullet
│   \text{Let } gaps = 0.5 + \sigma(f_{gaps}(z)) \times 0.75 \bullet
│   \text{Let } durations = 0.3 + \sigma(f_{durations}(z)) \times 0.9 \bullet
│   \text{onsets}(z) = \langle \sum_{i=1}^{k} gaps_i - gaps_1 \mid k \in 1 \dots 5 \rangle
└────────────────────────────────────────────────

### Optimization State
Defines the parallel search space containing the batch variables and objectives.

┌─ OptimizationState ────────────────────────────
│ Scale
│ MelodyDecoder
│ z\_batch: \mathbb{P} Latent
│ batch\_size: \mathbb{N}
│ temp: \mathbb{R}_{>0}
│ loss: Latent \times \mathbb{P} MIDI \times \mathbb{R} \rightarrow \mathbb{R}
├────────────────────────────────────────────────
│ batch\_size = 64
│ \# z\_batch = batch\_size
│ \forall z: z\_batch \bullet
│   loss(z, degrees, temp) = L_{sync} + L_{duration} + L_{contour} + L_{res} + L_{entropy}
└────────────────────────────────────────────────

---

## 3. Operational Schemas

### Initialize Optimization
Initializes the latent batch with random Gaussian noise.

┌─ InitOptimization ─────────────────────────────
│ OptimizationState'
│ scale?: Scale
├────────────────────────────────────────────────
│ root' = scale?.root
│ mode' = scale?.mode
│ \forall z: z\_batch' \bullet z \sim \mathcal{N}(0, I_{32})
│ temp' = 2.0
└────────────────────────────────────────────────

### Optimization Step (Continuous Autograd Update)
Updates the batch latent vectors using continuous gradients from the relaxed Gumbel-Softmax loss.

┌─ OptimizationStep ─────────────────────────────
│ \Delta OptimizationState
├────────────────────────────────────────────────
│ \forall z: z\_batch \bullet
│   z' = z - \alpha \cdot \nabla_z loss(z, degrees', temp)
│ temp' = \text{Anneal}(temp, step)
└────────────────────────────────────────────────

### Discrete Enforcement (Post-Processing Override)
Applies the discrete tonic/dominant constraint to the final note to guarantee 5/5 resolution.

┌─ EnforceResolution ────────────────────────────
│ \Xi OptimizationState
│ melody?: \text{seq } Note
│ melody! : \text{seq } Note
├────────────────────────────────────────────────
│ \# melody? = 5
│ \forall i: 1 \dots 4 \bullet melody!(i) = melody?(i)
│ 
│ \text{Let } last = melody?(5) \bullet
│ \text{Let } t\_pc = tonic \bmod 12 \bullet
│ \text{Let } d\_pc = dominant \bmod 12 \bullet
│ 
│ (melody!(5).pitch \bmod 12 \in \{ t\_pc, d\_pc \}) \land
│ (melody!(5).pitch = \arg\min_{p \in Octaves(t\_pc) \cup Octaves(d\_pc)} |p - last.pitch|)
└────────────────────────────────────────────────
