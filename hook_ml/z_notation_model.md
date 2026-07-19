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
  & Mode == \{ MAJOR, PHRYGIAN, AEOLIAN, LOCRIAN, HARMONIC\_MINOR, HUNGARIAN\_MINOR, \\
  & \quad\quad\quad\quad DORIAN, MIXOLYDIAN, PENTATONIC\_MINOR \} \\
  & ResolveTo == \{ TONIC, MEDIANT, DOMINANT \} \\
  & GenreProfile == [ sync\_target: \mathbb{R}; step\_target: \mathbb{R}; leap\_target: \mathbb{R}; resolve\_to: ResolveTo ]
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
  scale\_intervals(MAJOR) = \{0, 2, 4, 5, 7, 9, 11\} \land \\
  scale\_intervals(PHRYGIAN) = \{0, 1, 3, 5, 7, 8, 10\} \land \\
  scale\_intervals(AEOLIAN) = \{0, 2, 3, 5, 7, 8, 10\} \land \\
  scale\_intervals(LOCRIAN) = \{0, 1, 3, 5, 6, 8, 10\} \land \\
  scale\_intervals(HARMONIC\_MINOR) = \{0, 2, 3, 5, 7, 8, 11\} \land \\
  scale\_intervals(HUNGARIAN\_MINOR) = \{0, 2, 3, 6, 7, 8, 11\} \land \\
  scale\_intervals(DORIAN) = \{0, 2, 3, 5, 7, 9, 10\} \land \\
  scale\_intervals(MIXOLYDIAN) = \{0, 2, 4, 5, 7, 9, 10\} \land \\
  scale\_intervals(PENTATONIC\_MINOR) = \{0, 3, 5, 7, 10\}
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
│ mediant: MIDI
│ dominant: MIDI
├────────────────────────────────────────────────
│ tonic = root
│ mediant = \text{third degree of the scale}
│ dominant = \text{fifth degree of the scale}
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
Defines the parallel search space containing the batch variables and objectives, parametrized by the chosen Genre Profile.

┌─ OptimizationState ────────────────────────────
│ Scale
│ MelodyDecoder
│ z\_batch: 1 \dots 64 \rightarrow Latent
│ batch\_size: \mathbb{N}
│ temp: \mathbb{R}_{>0}
│ genre: GenreProfile
│ loss: Latent \times \mathbb{P} MIDI \times MIDI \times GenreProfile \times \mathbb{R} \rightarrow \mathbb{R}
├────────────────────────────────────────────────
│ batch\_size = 64
│ \text{dom } z\_batch = 1 \dots batch\_size
│ \forall z: Latent \bullet
│   \text{Let } target\_res == 
│     \text{if } genre.resolve\_to = MEDIANT \text{ then } mediant
│     \text{else if } genre.resolve\_to = DOMINANT \text{ then } dominant
│     \text{else } tonic \bullet
│   loss(z, degrees, target\_res, genre, temp) = \\
│     \quad L_{sync}(genre.sync\_target) + L_{duration} + L_{contour}(genre.step\_target, genre.leap\_target) + L_{res}(target\_res) + L_{entropy}
└────────────────────────────────────────────────

---

## 3. Operational Schemas

### Initialize Optimization
Initializes the latent batch with random Gaussian noise and copies the scale and genre parameters.

┌─ InitOptimization ─────────────────────────────
│ \Delta OptimizationState
│ scale?: Scale
│ genre?: GenreProfile
├────────────────────────────────────────────────
│ root' = scale?.root
│ mode' = scale?.mode
│ degrees' = scale?.degrees
│ tonic' = scale?.tonic
│ mediant' = scale?.mediant
│ dominant' = scale?.dominant
│ genre' = genre?
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
│ \text{Let } target\_res ==
│   \text{if } genre.resolve\_to = MEDIANT \text{ then } mediant
│   \text{else if } genre.resolve\_to = DOMINANT \text{ then } dominant
│   \text{else } tonic \bullet
│ \forall i: 1 \dots batch\_size \bullet
│   z\_batch'(i) = z\_batch(i) - \alpha \cdot \nabla_z loss(z\_batch(i), degrees, target\_res, genre, temp)
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
Selects the candidate vector from the batch that maximizes the exact discrete fitness score, outputting it to the aligned port `melody!`.

┌─ SelectBest ───────────────────────────────────
│ \Xi OptimizationState
│ fitness: \text{seq } Note \rightarrow 0 \dots 100
│ melody! : \text{seq } Note
├────────────────────────────────────────────────
│ \exists i_{best}: 1 \dots batch\_size \bullet
│   \text{Let } candidate\_melody = Decode(z\_batch(i_{best})) \bullet
│     melody! = candidate\_melody \land
│     (\forall j: 1 \dots batch\_size \bullet fitness(Decode(z\_batch(j))) \le fitness(melody!))
└────────────────────────────────────────────────

### Discrete Enforce Resolution
Forcibly shifts the last note to the nearest stable octave of the genre-specified target pitch while minimizing melodic jump distance to note 4.

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
│ \text{Let } target\_pc ==
│   \text{if } genre.resolve\_to = MEDIANT \text{ then } pc(mediant)
│   \text{else if } genre.resolve\_to = DOMINANT \text{ then } pc(dominant)
│   \text{else } pc(tonic) \bullet
│ \text{Let } OctavesStable == \{ p: MIDI \mid pc(p) = target\_pc \} \bullet
│ \text{Let } Cost == \lambda p: MIDI \bullet |p - last.pitch| + 4.0 \times \max(0, |p - prev.pitch| - 8) \bullet
│ 
│ (pc(melody!(5).pitch) = target\_pc) \land
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

We define the 300-step generation loop with interleaved diversity injection every 30 steps using sequential schema composition:

$$
\text{GenerationLoop} == \big( (\text{OptimizationStep})^{29} \Semi \text{OptimizationStep} \Semi \text{DiversityInjection} \big)^{10}
$$

The complete Generation Pipeline is defined as the relational sequential composition ($\Semi$) from left to right:

$$
GenerateMelody == InitOptimization \Semi \text{GenerationLoop} \Semi SelectBest \Semi EnforceResolution \Semi DiscreteRefinement
$$
