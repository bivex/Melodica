# Formal Specification of Melodica's MLX Optimization Model in Z Notation

This document provides a formal mathematical description of the Melodica generative model and optimization pipeline using **Z Notation** (based on typed set theory and first-order predicate logic).

---

## 1. Given Sets, Types, and Constants

First, we define the basic types and domains of our system:

$$
\begin{align*}
  & [MIDI] \subseteq \mathbb{N} && \text{Domain of MIDI pitch values } (0 \dots 127) \\
  & [Time] == \mathbb{R}_{\ge 0} && \text{Time beats domain} \\
  & [Latent] == \mathbb{R}^{32} && \text{Latent space dimension} \\
  & Mode == \{ PHRYGIAN, AEOLIAN, LOCRIAN, HARMONIC\_MINOR, HUNGARIAN\_MINOR \}
\end{align*}
$$

We define a $Note$ as a tuple of pitch, start beat, and duration:

$$
Note == [ pitch: MIDI; start: Time; duration: \mathbb{R}_{> 0} ]
$$

We define the function $pc$ mapping MIDI pitches to their pitch classes:

$$
\begin{align*}
  & pc: MIDI \rightarrow 0 \dots 11 \\
  & \forall p: MIDI \bullet pc(p) = p \bmod 12
\end{align*}
$$

We define the scale intervals axiomatically:

$$
\begin{axdef}
  scale\_intervals: Mode \rightarrow \mathbb{P} (0 \dots 11)
\where
  scale\_intervals(PHRYGIAN) = \{0, 1, 3, 5, 7, 8, 10\} \land \\
  scale\_intervals(AEOLIAN) = \{0, 2, 3, 5, 7, 8, 10\} \land \\
  scale\_intervals(LOCRIAN) = \{0, 1, 3, 5, 6, 8, 10\} \land \\
  scale\_intervals(HARMONIC\_MINOR) = \{0, 2, 3, 5, 7, 8, 11\} \land \\
  scale\_intervals(HUNGARIAN\_MINOR) = \{0, 2, 3, 6, 7, 8, 11\}
\end{axdef}
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
│ dominant = root + 7
│ \forall d: degrees \bullet pc(d) \in \{ pc(root + i) \mid i \in scale\_intervals(mode) \}
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
│ z\_batch: 1 \dots 64 \rightarrow Latent
│ batch\_size: \mathbb{N}
│ temp: \mathbb{R}_{>0}
│ loss: Latent \times \mathbb{P} MIDI \times MIDI \times MIDI \times \mathbb{R} \rightarrow \mathbb{R}
├────────────────────────────────────────────────
│ batch\_size = 64
│ \text{dom } z\_batch = 1 \dots batch\_size
│ \forall z: Latent \bullet
│   loss(z, degrees, \text{tonic}, \text{dominant}, temp) = \\
│     \quad L_{sync} + L_{duration} + L_{contour} + L_{res} + L_{motif} + L_{entropy}
└────────────────────────────────────────────────

---

## 3. Operational Schemas

### Initialize Optimization
Initializes the latent batch with random Gaussian noise and copies the scale parameters.

┌─ InitOptimization ─────────────────────────────
│ \Delta OptimizationState
│ scale?: Scale
├────────────────────────────────────────────────
│ root' = scale?.root
│ mode' = scale?.mode
│ degrees' = scale?.degrees
│ tonic' = scale?.tonic
│ dominant' = scale?.dominant
│ 
│ \forall i: 1 \dots batch\_size' \bullet z\_batch'(i) \sim \mathcal{N}(0, I_{32})
│ temp' = 2.0
└────────────────────────────────────────────────

### Optimization Step (Continuous Autograd Update)
Updates the batch latent vectors using continuous gradients from the relaxed Gumbel-Softmax loss, keeping scale parameters constant.

┌─ OptimizationStep ─────────────────────────────
│ \Delta OptimizationState
│ \Xi Scale
├────────────────────────────────────────────────
│ \forall i: 1 \dots batch\_size \bullet
│   z\_batch'(i) = z\_batch(i) - \alpha \cdot \nabla_z loss(z\_batch(i), degrees, \text{tonic}, \text{dominant}, temp)
│ temp' = \text{Anneal}(temp, step)
└────────────────────────────────────────────────

### Diversity Injection (Stochastic Perturbation)
Injects normal noise into the batch variables to escape local minima.

┌─ DiversityInjection ───────────────────────────
│ \Delta OptimizationState
├────────────────────────────────────────────────
│ \forall i: 1 \dots batch\_size \bullet
│   \exists \delta: Latent \bullet \delta \sim \mathcal{N}(0, 0.05 \cdot I_{32}) \land z\_batch'(i) = z\_batch(i) + \delta
└────────────────────────────────────────────────

### Select Best Candidate
Selects the candidate vector from the batch that maximizes the exact discrete fitness score.

┌─ SelectBest ───────────────────────────────────
│ \Xi OptimizationState
│ fitness: \text{seq } Note \rightarrow 0 \dots 100
│ best\_notes! : \text{seq } Note
├────────────────────────────────────────────────
│ \exists i_{best}: 1 \dots batch\_size \bullet
│   \text{Let } candidate\_melody = Decode(z\_batch(i_{best})) \bullet
│     best\_notes! = candidate\_melody \land
│     (\forall j: 1 \dots batch\_size \bullet fitness(Decode(z\_batch(j))) \le fitness(best\_notes!))
└────────────────────────────────────────────────

### Discrete Enforce Resolution
Forcibly shifts the last note to the nearest stable octave of tonic or dominant while minimizing melodic jump distance to note 4.

┌─ EnforceResolution ────────────────────────────
│ \Xi OptimizationState
│ melody?: \text{seq } Note
│ melody! : \text{seq } Note
├────────────────────────────────────────────────
│ \# melody? = 5
│ \forall i: 1 \dots 4 \bullet melody!(i) = melody?(i)
│ 
│ \text{Let } last = melody?(5) \bullet
│ \text{Let } prev = melody?(4) \bullet
│ \text{Let } t\_pc = pc(tonic) \bullet
│ \text{Let } d\_pc = pc(dominant) \bullet
│ \text{Let } OctavesStable == \{ p: MIDI \mid pc(p) \in \{ t\_pc, d\_pc \} \} \bullet
│ \text{Let } Cost == \lambda p: MIDI \bullet |p - last.pitch| + 4.0 \times \max(0, |p - prev.pitch| - 8) \bullet
│ 
│ (pc(melody!(5).pitch) \in \{ t\_pc, d\_pc \}) \land
│ (melody!(5).pitch = \arg\min_{p \in OctavesStable} Cost(p))
└────────────────────────────────────────────────

### Discrete Refinement (Hill-Climbing)
Performs discrete local search to maximize exact fitness while maintaining resolution of the last note.

┌─ DiscreteRefinement ───────────────────────────
│ \Xi Scale
│ melody?: \text{seq } Note
│ melody! : \text{seq } Note
│ fitness: \text{seq } Note \rightarrow 0 \dots 100
├────────────────────────────────────────────────
│ \# melody? = 5
│ \# melody! = 5
│ fitness(melody?) \le fitness(melody!)
│ melody!(5).pitch = melody?(5).pitch \quad \text{[Preserves resolved last note]}
└────────────────────────────────────────────────

---

## 4. Complete Optimization Pipeline

We define the complete generation pipeline as a relational composition of the operational schemas:

$$
GenerateMelody == InitOptimization \circ (OptimizationStep)^{300} \circ SelectBest \circ EnforceResolution \circ DiscreteRefinement
$$
