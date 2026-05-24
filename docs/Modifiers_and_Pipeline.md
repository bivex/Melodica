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

### 1. Rhythmic Modifiers (`melodica.modifiers.rhythmic`)
*   **`QuantizeModifier`**: Snaps note onsets (and optionally durations) to a grid (e.g., `grid_resolution=0.25` for 16th notes).
*   **`SwingController`**: Delays offbeat notes to create a swing feel (`swing_ratio=0.6` for triplet swing).
*   **`HumanizeModifier`**: Adds slight Gaussian noise to timing (`timing_std`) and dynamics (`velocity_std`) for realism.
*   **`AdjustNoteLengthsModifier`**: Scales note durations (e.g., `gate_factor=0.5` for staccato) or sets a fixed length.
*   **`FollowRhythmModifier`**: Takes the rhythm (onsets and durations) from a source track and applies them to the current track's pitches.

### 2. Dynamic Modifiers (`melodica.modifiers.dynamic`)
*   **`VelocityScalingModifier`**: Globally scales and shifts all note velocities in the phrase.
*   **`CrescendoModifier`**: Applies a linear velocity ramp across the phrase duration (`start_vel` to `end_vel`).
*   **`SectionIntensityModifier`**: Dynamically scales velocities based on song structure (e.g., quieter in the Intro, louder in the Climax).

### 3. Harmonic & Voicing Modifiers (`melodica.modifiers.harmonic`, `voicings.py`)
*   **`NoteDoublerModifier`**: Duplicates notes by specific octave shifts (e.g., `octaves=[-1, 1]`).
*   **`TransposeModifier`**: Transposes all notes by a fixed number of semitones.
*   **`LimitNoteRangeModifier`**: Constrains pitches to a specific range (e.g., `min_pitch=40`, `max_pitch=80`), shifting octaves if needed.
*   **`DropVoicingModifier`**: Drops the second-highest note (Drop 2) or third-highest note (Drop 3) down an octave.
*   **`InversionModifier`**: Inverts chords within the phrase.

### 4. Variations & Articulations (`melodica.modifiers.variations`, `variations_articulation.py`)
*   **`MirrorModifier`**: Flips the pitch contour upside down around an axis.
*   **`ArpeggiateModifier`**: Turns block chords into arpeggios (Up, Down, UpDown, Random).
*   **`StaccatoLegatoModifier`**: Intelligent articulation shaping based on phrasing.
*   **`MIDIEchoModifier`**: Generates a MIDI delay effect with velocity decay.

### 5. Aesthetic & Voice Leading (`melodica.modifiers.aesthetic`, `voice_leading.py`)
*   **`GrooveModifier`**: Overlays a complex groove template onto the phrase.
*   **`VoiceLeadingModifier`**: Enforces strict counterpoint and voice-leading rules (minimizing leaps, avoiding parallel fifths) between consecutive chords.

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