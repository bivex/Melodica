# Algorithmic Music Composition & Arrangement

When tasked with generating music, writing arrangements, or building composition scripts in Python (e.g., using frameworks like Melodica or music21), follow these core principles to ensure professional, expressive output.

## 1. Arrangement Structure
Do not let all instruments play simultaneously from start to finish. A professional arrangement requires a dynamic energy curve.
- **Sectioning**: Divide the track into logical parts (e.g., Intro, Build, Climax, Breakdown, Outro).
- **Scheduling**: Explicitly schedule which tracks rest (silence) and which tracks play specific themes or variations in each section.
- **Register Balancing**: Explicitly map instruments to frequency bands (Sub-bass, low, mid, high) using octave shifts. Avoid having multiple lead or bass elements competing in the exact same register to prevent frequency masking.

## 2. Expression and Humanization (Post-Processing)
Raw generated notes often sound robotic and flat. Always apply an expression pipeline before exporting to MIDI or audio:
- **Timing & Velocity Humanization**: Add slight micro-timing variations (e.g., standard deviation off the grid) and velocity randomization.
- **Dynamic Curves**: Apply crescendo/decrescendo or swell velocity curves to long notes, pads, and risers.
- **Metric Accents**: Emphasize downbeats or strong metric pulses to establish the groove.

## 3. Harmonic Progression Formatting
When providing chord progressions as string literals (e.g., Roman numerals), adhere strictly to standard parsing conventions.
- **Pitfall**: Watch out for invalid minor chord extensions depending on the parser. For instance, in many strict harmonic parsers, you must use `Vm9` (minor 9th) instead of `Vmin9`.
- **Duration**: Ensure chord timings/durations explicitly match the section's overall bar length.

## 4. Safety Checks in Structural Evaluation
- **Pitfall**: When aggregating durations or bar counts from abstract structural objects (like sections or parts), ensure you filter out `None` types (e.g., `sum(p.bars for p in parts if p.bars is not None)`) to prevent unexpected runtime `TypeError` exceptions during structural calculations.
