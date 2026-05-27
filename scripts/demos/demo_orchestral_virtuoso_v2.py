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
demo_orchestral_virtuoso_v2.py — Long-form (2 min) virtuous orchestral demonstration.
Showcases:
1. 'Epic' drama shape with a slow, powerful 2-minute buildup.
2. High-density virtuous runs and ornaments.
3. Complex motivic evolution across sections.
4. Dramatic pauses and tension-aware pitching in a symphonic context.
"""

import os
import random
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.render_context import RenderContext
from melodica.midi import export_midi

def main():
    # 120 BPM, 2 minutes = 240 beats
    total_beats = 240.0
    key = types.Scale(root=7, mode=types.Mode.NATURAL_MINOR)  # G Minor
    
    # Virtuous High-Energy Params
    params = GeneratorParams(
        density=0.75,          # High base density
        leap_probability=0.45,  # Expressive leaps
    )
    
    # Generator configured for virtuosity
    gen = MelodyGenerator(
        params,
        drama_shape="epic",      # Long slow build to a late peak
        drama_peak=0.85,         # Peak at ~102 seconds
        motif_probability=0.7,
        ornament_probability=0.4, # Lots of grace notes
        harmony_note_probability=0.75,
        note_range_low=55,       # G3
        note_range_high=96,      # C7 (Wide range for virtuosity)
        phrase_length=8.0,
        syncopation=0.25,
        rhythm_variety=0.6
    )
    
    # Structural Plan (32 bars of 4/4 = 128 beats, so we need ~60 bars total)
    # We define sections in 16-beat chunks (4 bars)
    sections = [
        ("Opening", 32.0, "i i VI VII i i VI V"),
        ("Development A", 32.0, "i VI III VII i VI III VII"),
        ("Development B", 32.0, "iv i V i iv i V V"),
        ("The Build", 32.0, "VI VII i iv VI VII V V"),
        ("Climax Prep", 32.0, "i VI III VII i VI III VII"),
        ("GRAND PEAK", 48.0, "i VI VII V i VI VII V VI VII V V"),
        ("Resolution", 16.0, "i i VI V"),
        ("Finale", 16.0, "i")
    ]
    
    all_notes = []
    current_time = 0.0
    context = RenderContext(phrase_position=0.0)
    
    print(f"--- Generating Orchestral Virtuoso V2 (G Minor, 2 min) ---")
    
    for name, dur, prog in sections:
        # Parse progression
        prog_parts = prog.split()
        beats_per_chord = dur / len(prog_parts)
        section_chords = []
        for i, p in enumerate(prog_parts):
            chord = key.parse_roman(p)
            chord.start = i * beats_per_chord
            chord.duration = beats_per_chord
            section_chords.append(chord)
            
        print(f"Rendering {name:15} | Progress: {context.phrase_position:.2f} | Beats: {dur}")
        
        # Render section
        # We simulate the duration of the WHOLE piece in the render call
        # but only render this specific section.
        # Actually, MelodyGenerator.render uses duration_beats for internal drama scaling,
        # so we need to pass the TOTAL duration to the DramaticArc inside render?
        # NO, our recent fix uses context.phrase_position which is global.
        
        section_notes = gen.render(section_chords, key, dur, context=context)
        
        # Add to absolute timeline
        for n in section_notes:
            all_notes.append(types.NoteInfo(
                pitch=n.pitch,
                start=n.start + current_time,
                duration=n.duration,
                velocity=n.velocity
            ))
            
        current_time += dur
        context = gen._last_context
        if context:
            # Manually update global progress for next call
            context.phrase_position = current_time / total_beats

    # Orchestration: Duplicate melody to different octaves for "Large Orchestral" sound
    violins_i = types.Track(name="Violins I", program=41, notes=all_notes, volume=127, expression=127)
    
    # Violins II - an octave lower
    v2_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration, velocity=int(n.velocity*0.8)) for n in all_notes]
    violins_ii = types.Track(name="Violins II", program=41, notes=v2_notes, volume=110, expression=110)
    
    # Flute - following same melody in high register
    flute_notes = [types.NoteInfo(pitch=n.pitch+12, start=n.start, duration=n.duration, velocity=int(n.velocity*0.9)) for n in all_notes]
    flute = types.Track(name="Flute", program=74, notes=flute_notes, volume=100, expression=110)

    output_dir = Path("output/melody_demos")
    output_dir.mkdir(exist_ok=True, parents=True)
    out_file = output_dir / "orchestral_virtuoso_v2.mid"
    
    export_midi([violins_i, violins_ii, flute], str(out_file))
    
    print(f"--- Done ---")
    print(f"MIDI saved to: {out_file}")

if __name__ == "__main__":
    main()
