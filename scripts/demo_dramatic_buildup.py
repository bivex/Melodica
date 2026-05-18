# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
demo_dramatic_buildup.py — Demonstrates the new dramatic arc and section-based buildup.
This script showcases:
1. Global buildup across sections (Intro -> Verse -> Chorus -> Outro).
2. Local micro-buildup within the Chorus using drama_shape='dramatic'.
3. Motivic development (Full -> Fragment -> Return).
4. Tension-aware pitching and density.
"""

import os
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.render_context import RenderContext
from melodica.midi import export_midi
from melodica.utils import snap_to_scale

def main():
    # Setup
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)  # D Minor
    params = GeneratorParams(density=0.5, leap_probability=0.3)
    
    # We'll use one generator for all sections to demonstrate state persistence
    gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.75,
        motif_probability=0.6,
        ornament_probability=0.2,
        harmony_note_probability=0.8,
        note_range_low=60,   # C4
        note_range_high=84,  # C6
        phrase_length=4.0
    )
    
    # Sections to render
    sections = [
        ("Intro", 16.0, "i i VII VII"),
        ("Verse", 16.0, "i VI VII v"),
        ("Chorus", 16.0, "i VI III VII"),
        ("Bridge/Peak", 8.0, "VI VII i v"),
        ("Outro", 8.0, "i")
    ]
    
    all_notes = []
    current_time = 0.0
    context = RenderContext(phrase_position=0.0)
    total_song_duration = sum(s[1] for s in sections)
    
    print(f"--- Generating Dramatic Buildup (D Minor) ---")
    
    for name, dur, prog in sections:
        # Convert progression string to ChordLabels
        section_chords = []
        prog_parts = prog.split()
        beats_per_chord = dur / len(prog_parts)
        
        for i, p in enumerate(prog_parts):
            chord = key.parse_roman(p)
            chord.start = i * beats_per_chord
            chord.duration = beats_per_chord
            section_chords.append(chord)
            
        print(f"Rendering {name:12} | Progress: {context.phrase_position:.2f} | Duration: {dur} beats")
        
        # Render section
        section_notes = gen.render(section_chords, key, dur, context=context)
        
        # Shift notes to absolute time
        for n in section_notes:
            all_notes.append(types.NoteInfo(
                pitch=n.pitch,
                start=n.start + current_time,
                duration=n.duration,
                velocity=n.velocity
            ))
            
        # Update state for next section
        current_time += dur
        # Update context based on global progress
        context = gen._last_context
        # We need to manually set total_duration in context for the next phrase_position calculation
        # normally the Director handles this, but here we do it manually.
        if context:
            context.phrase_position = current_time / total_song_duration

    # Export to MIDI
    output_dir = Path("output/melody_demos")
    output_dir.mkdir(exist_ok=True, parents=True)
    out_file = output_dir / "dramatic_buildup.mid"
    
    # Create a single track
    track = types.Track(
        name="Dramatic Melody", 
        program=1, 
        notes=all_notes,
        volume=127,
        expression=127
    )
    export_midi([track], str(out_file))
    
    print(f"--- Done ---")
    print(f"MIDI saved to: {out_file}")

if __name__ == "__main__":
    main()
