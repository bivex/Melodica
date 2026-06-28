# print_chords.py
import pickle
from pathlib import Path
import mido

# Let's inspect the chords of temp_0.mid or from the pipeline
# Wait, can we load the generated MIDI files and read track names, chords, etc.?
# Wait, let's write a python script that loads the midi tracks and prints the note name events,
# or prints the chords if they are written in the MIDI file as markers / text messages.
# Also, let's load IdeaTool and print the chord progression.

from melodica.types import Scale, Mode
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule

def inspect_track_chords():
    key = Scale(root=9, mode=Mode.AEOLIAN)  # A Minor
    parts = [
        IdeaPart(
            name="VelvetTheme",
            bars=32,
            scale=key,
            tempo=78,
            progression_type="coupled_hmm"
        )
    ]
    
    config = IdeaToolConfig(
        parts=parts,
        tracks=[],
        scale=key,
        tempo=78,
        use_tension_curve=True
    )
    
    tool = IdeaTool(config)
    tool.generate() # generates chords
    chords = tool.get_chords()
    print("Generated chord progression:")
    for c in chords:
        print(f"  Start: {c.start}, Duration: {c.duration}, Root: {c.root}, Quality: {c.quality}, Pitch Classes: {c.pitch_classes()}")

if __name__ == "__main__":
    inspect_track_chords()
