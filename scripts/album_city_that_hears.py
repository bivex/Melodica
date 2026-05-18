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
album_city_that_hears.py — Full production of the 3-track concept album.
1. "Ash in Pockets" (Silence/Void)
2. "The Crack" (Conflict/Explosion)
3. "The City Hears" (Acceptance/Light)
"""

import os
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.render_context import RenderContext
from melodica.midi import export_midi

def produce_track_1():
    """I. Ash in Pockets — Silence/Void. Build from minimalism to atmosphere."""
    print("Producing I. Ash in Pockets...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)  # D Minor
    params = GeneratorParams(density=0.3, leap_probability=0.2)
    
    gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.9,
        motif_probability=0.3,
        note_range_low=45,
        note_range_high=72,
        phrase_length=8.0,
        register_smoothness=0.8
    )
    
    duration = 128.0 # 32 bars
    progression = "i i VI VI iv iv v v" * 4
    chords = []
    prog_parts = progression.split()
    beats_per_chord = duration / len(prog_parts)
    for i, p in enumerate(prog_parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per_chord
        chord.duration = beats_per_chord
        chords.append(chord)
        
    notes = gen.render(chords, key, duration)
    
    # Orchestration: Echoey Piano
    piano = types.Track(name="Muted Piano", program=1, notes=notes, volume=120, expression=127)
    # Atmospheric Pad (doubling low)
    pad_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration*1.5, velocity=int(n.velocity*0.85)) for n in notes]
    pad = types.Track(name="Atmospheric Pad", program=90, notes=pad_notes, volume=100, expression=110)
    
    return [piano, pad], notes # return melody for theme reuse

def produce_track_2():
    """II. The Crack — Conflict/Explosion. High energy, chaotic, heavy."""
    print("Producing II. The Crack...")
    key_minor = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    key_major = types.Scale(root=2, mode=types.Mode.MAJOR)
    
    params = GeneratorParams(density=0.7, leap_probability=0.5)
    gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.75,
        motif_probability=0.6,
        ornament_probability=0.3,
        note_range_low=40,
        note_range_high=88,
        syncopation=0.4,
        rhythm_variety=0.7
    )
    
    duration = 160.0 # ~40 bars
    # i - bII - iv - V (Harmonic/Phrygian tension)
    progression = "i bII iv V i bII iv V" * 4 + "I IV V I I IV V I" # transition to major at end
    chords = []
    prog_parts = progression.split()
    beats_per_chord = duration / len(prog_parts)
    for i, p in enumerate(prog_parts):
        k = key_minor if i < len(prog_parts) * 0.75 else key_major
        chord = k.parse_roman(p)
        chord.start = i * beats_per_chord
        chord.duration = beats_per_chord
        chords.append(chord)
        
    notes = gen.render(chords, key_minor, duration)
    
    # Orchestration: Aggressive Strings + Bass Synth
    strings = types.Track(name="Aggressive Strings", program=41, notes=notes, volume=127, expression=127)
    bass_notes = [types.NoteInfo(pitch=n.pitch-24, start=n.start, duration=0.5, velocity=120) for n in notes if n.start % 1.0 < 0.1]
    bass = types.Track(name="Power Bass", program=39, notes=bass_notes, volume=110)
    
    return [strings, bass]

def produce_track_3(theme_notes):
    """III. City Hears — Acceptance. Warm, major, broad."""
    print("Producing III. City Hears...")
    key = types.Scale(root=2, mode=types.Mode.MAJOR) # D Major
    params = GeneratorParams(density=0.5, leap_probability=0.3)
    
    gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.7,
        motif_probability=0.8,
        note_range_low=55,
        note_range_high=84,
        phrase_length=8.0
    )
    
    duration = 120.0
    progression = "I IV vi V I IV vi V" * 4
    chords = []
    prog_parts = progression.split()
    beats_per_chord = duration / len(prog_parts)
    for i, p in enumerate(prog_parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per_chord
        chord.duration = beats_per_chord
        chords.append(chord)
        
    # Re-use theme from Track 1 (thematic continuity)
    context = RenderContext(prev_pitches=[n.pitch for n in theme_notes[:8]])
    
    notes = gen.render(chords, key, duration, context=context)
    
    # Orchestration: Warm Cello + Ambient Pads
    cello = types.Track(name="Warm Cello", program=43, notes=notes, volume=120, expression=127)
    pad_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=4.0, velocity=80) for n in notes if n.start % 4.0 == 0]
    ambient = types.Track(name="Golden Pad", program=92, notes=pad_notes, volume=110, expression=115)
    
    return [cello, ambient]

def main():
    album_dir = Path("output/album_city_that_hears")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("=== STARTING ALBUM PRODUCTION: CITY THAT HEARS ===")
    
    # Track 1
    t1_tracks, t1_melody = produce_track_1()
    export_midi(t1_tracks, str(album_dir / "01_Ash_in_Pockets.mid"))
    
    # Track 2
    t2_tracks = produce_track_2()
    export_midi(t2_tracks, str(album_dir / "02_The_Crack.mid"))
    
    # Track 3 (pass melody from T1 for continuity)
    t3_tracks = produce_track_3(t1_melody)
    export_midi(t3_tracks, str(album_dir / "03_City_Hears.mid"))
    
    print("=== PRODUCTION COMPLETE ===")
    print(f"Files saved to: {album_dir}")

if __name__ == "__main__":
    main()
