# Modifiers and the Non-Destructive Pipeline

Melodica uses a **Non-Destructive Modifier Pipeline** (Variation Stack) to transform musical phrases. This architecture is heavily inspired by DAWs and phrase-based arrangers (like RapidComposer).

Instead of permanently altering the generated MIDI notes, modifiers act as "inserts" in a signal chain. You can dynamically add, remove, reorder, or bypass variations on the fly, and the engine will instantly recalculate the final MIDI output without ever modifying the `base_notes`.

---

## The `ModifierPipeline`

Located in `melodica.modifiers.pipeline`, the `ModifierPipeline` is the core container for this non-destructive workflow.

### Usage Example

```python
from melodica.modifiers import ModifierPipeline, ModifierContext
from melodica.modifiers.rhythmic import SwingController, QuantizeModifier
from melodica.modifiers.dynamic import CrescendoModifier

# 1. Initialize pipeline with original generated notes
pipeline = ModifierPipeline(base_notes=my_generated_notes)

# 2. Add inserts (variations) to the stack
pipeline.add_modifier(SwingController(swing_ratio=0.6))
pipeline.add_modifier(QuantizeModifier(grid_resolution=0.125))
pipeline.add_modifier(CrescendoModifier(start_vel=40, end_vel=110))

# You can manipulate the stack dynamically:
# pipeline.set_bypass(index=1, bypass=True)  # Mute the Quantizer
# pipeline.remove_modifier(index=0)          # Remove Swing

# 3. Create context and process
mod_context = ModifierContext(
    duration_beats=32.0,
    chords=current_chords,
    timeline=current_timeline,
    scale=current_scale
)

final_notes = pipeline.process(mod_context)
```

---

## Available Modifiers

All modifiers implement the `PhraseModifier` protocol and must supply a `modify(notes, context)` method.

| Category | Modifier | Description | Key Params / Example |
| :--- | :--- | :--- | :--- |
| **Rhythmic** (`melodica.modifiers.rhythmic`) | `QuantizeModifier` | Snaps note onsets (and optionally durations) to a grid. | `grid_resolution=0.25` |
| **Rhythmic** | `SwingController` | Delays offbeat notes to create a swing feel. | `swing_ratio=0.6` |
| **Rhythmic** | `HumanizeModifier` | Adds slight Gaussian noise to timing and dynamics. | `timing_std`, `velocity_std` |
| **Rhythmic** | `AdjustNoteLengthsModifier` | Scales note durations or sets a fixed length. | `gate_factor=0.5` |
| **Rhythmic** | `FollowRhythmModifier` | Takes the rhythm (onsets and durations) from a source track and applies them to pitches. | `source_track="Melody"` |
| **Rhythmic** | `AdaptiveSwingModifier` | Applies swing that changes dynamically across the phrase. | `start_swing`, `end_swing` |
| **Rhythmic** | `PolyrhythmLayerModifier` | Overlays a second rhythmic layer (e.g., 3:4) over existing notes. | `tuple_count`, `base_count` |
| **Rhythmic** | `RhythmicDensityModifier` | Randomly thins out notes to achieve a target density. | `density=0.7` |
| **Dynamic** (`melodica.modifiers.dynamic`) | `VelocityScalingModifier` | Globally scales and shifts all note velocities in the phrase. | `scale=1.0`, `add_val=0` |
| **Dynamic** | `CrescendoModifier` | Applies a linear velocity ramp across the phrase duration. | `start_vel=40`, `end_vel=100` |
| **Dynamic** | `VelocityCurveModifier` | Applies a velocity ramp with different curve shapes (exp, log, sine, S). | `curve="s_curve"` |
| **Dynamic** | `SectionIntensityModifier` | Dynamically scales velocities based on song structure arc. | `sections` (dict) |
| **Harmonic & Voicing** (`melodica.modifiers.harmonic`, `voicings.py`) | `NoteDoublerModifier` | Duplicates notes by specific octave shifts. | `octaves=[-1, 1]` |
| **Harmonic & Voicing** | `TransposeModifier` | Transposes all notes by a fixed number of semitones. | `semitones=12` |
| **Harmonic & Voicing** | `LimitNoteRangeModifier` | Constrains pitches to a specific range, shifting octaves if needed. | `min_pitch=40`, `max_pitch=80` |
| **Harmonic & Voicing** | `ChordToneSnapModifier` | Snaps non-chord tones to the nearest pitch class of the active chord. | |
| **Harmonic & Voicing** | `ChordVoicingSpreadModifier` | Adjusts the spread of chord voices (closed, spread, open). | `spread_mode="open"` |
| **Harmonic & Voicing** | `DropVoicingModifier` | Drops the second-highest (Drop 2) or third-highest (Drop 3) note down an octave. | `drop_type=2` |
| **Harmonic & Voicing** | `InversionModifier` | Inverts chords within the phrase. | `inversion=1` |
| **Variations & Articulations** (`melodica.modifiers.variations`, `variations_articulation.py`) | `MirrorModifier` | Flips the pitch contour upside down around an axis. | |
| **Variations & Articulations** | `ArpeggiateModifier` | Turns block chords into arpeggios. | `pattern="Up"` |
| **Variations & Articulations** | `StaccatoLegatoModifier` | Intelligent articulation shaping based on phrasing. | |
| **Variations & Articulations** | `SlideLegatoModifier` | Generates pitch bend slides between legato notes. | `slide_beats=0.1` |
| **Variations & Articulations** | `MIDIEchoModifier` | Generates a MIDI delay effect with velocity decay. | `delay_beats=1.0` |
| **Aesthetic & Voice Leading** (`melodica.modifiers.aesthetic`, `voice_leading.py`) | `GrooveModifier` | Overlays a complex groove template onto the phrase. | `groove_template` |
| **Aesthetic & Voice Leading** | `VoiceLeadingModifier` | Enforces strict counterpoint and voice-leading rules between consecutive chords. | `max_leap=7` |
| **Structural** (`rc_variations_structural.py`) | `PhraseBoundaryModifier` | Ensures notes stay within phrase boundaries and adds "breath" gaps. | `breath_beats=0.1` |
| **Structural** | `MotifTransformModifier` | Applies retrograde, inversion, or both to the entire phrase. | `transform_type` |

---

## Creating Custom Modifiers

To create a new modifier, implement the `PhraseModifier` protocol. Ensure you do not mutate the notes directly if you want the modifier to be reusable, though the `ModifierPipeline` handles cloning base notes internally as a safety measure.

```python
from dataclasses import dataclass
from melodica.modifiers import PhraseModifier, ModifierContext
from melodica.types import NoteInfo

@dataclass
class RandomOctaveJumpsModifier(PhraseModifier):
    probability: float = 0.2

    def modify(self, notes: list[NoteInfo], context: ModifierContext) -> list[NoteInfo]:
        import random
        result = []
        for n in notes:
            new_pitch = n.pitch
            if random.random() < self.probability:
                new_pitch += random.choice([-12, 12])
            
            result.append(NoteInfo(
                pitch=new_pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute
            ))
        return result
```

---

## Best Practices: The Minimum Viable Stack

While you can combine modifiers in any order, some are essential for professional-sounding results. Here is the recommended prioritization:

### 🔴 Critical (Must-Haves)
Without these, the output may sound "raw" or technically broken.

*   **`QuantizeModifier`**: Ensures the rhythmic grid is stable. Crucial if generation is not perfectly aligned.
*   **`VelocityScalingModifier`**: Without dynamics control, everything sounds mechanical and flat.
*   **`LimitNoteRangeModifier`**: Protects against notes flying out of an instrument's playable range (e.g., a bass playing C6).

### 🟡 Important (Musicality)
These bring the arrangement to life.

*   **`HumanizeModifier`**: Removes the "MIDI from the 90s" feel by adding micro-imperfections.
*   **`CrescendoModifier`**: Adds dynamic arcs, allowing phrases to "breathe" over long sections.
*   **`VoiceLeadingModifier`**: Essential for chordal tracks (pads, strings) to ensure smooth transitions without jarring jumps.

### 🟢 Situational
*   **Jazz / Soul:** `SwingController`
*   **Pads / Epic Choirs:** `NoteDoublerModifier`
*   **Basslines:** `AdjustNoteLengthsModifier` (acting as a gate for staccato feel)
*   **Electronic / Synth:** `ArpeggiateModifier`

### Example: The Minimum Viable Stack (MVS)
This stack provides a rhythmically accurate, lively, and range-safe result suitable for almost any genre.

```python
pipeline.add_modifier(QuantizeModifier(grid_resolution=0.125))
pipeline.add_modifier(HumanizeModifier(timing_std=0.015, velocity_std=5.0))
pipeline.add_modifier(VelocityScalingModifier(scale=1.0))
pipeline.add_modifier(LimitNoteRangeModifier(min_pitch=36, max_pitch=84))
```