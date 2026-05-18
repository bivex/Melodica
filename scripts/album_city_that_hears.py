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
    # Extreme sparse density for "void"
    params = GeneratorParams(density=0.2, leap_probability=0.15)
    
    gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.95,
        motif_probability=0.2,
        note_range_low=45,
        note_range_high=67,  # restricted range for "isolation"
        phrase_length=12.0,   # long phrases for breathing
        register_smoothness=0.95
    )
    
    duration = 128.0 # 32 bars
    progression = "i i i i VI VI iv v" * 4
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
    piano = types.Track(name="Muted Piano", program=1, notes=notes, volume=115, expression=127)
    # Atmospheric Pad (doubling low)
    pad_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration*2.0, velocity=int(n.velocity*0.7)) for n in notes]
    pad = types.Track(name="Atmospheric Pad", program=90, notes=pad_notes, volume=95, expression=110)
    
    return [piano, pad], notes, 65.0 # return tracks, melody, and BPM

def produce_track_2():
    """II. The Crack — Conflict/Explosion. High energy, chaotic, heavy."""
    print("Producing II. The Crack...")
    key_minor = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    key_major = types.Scale(root=2, mode=types.Mode.MAJOR)
    
    # High density and leaps for "conflict"
    params = GeneratorParams(density=0.85, leap_probability=0.7)
    gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.7,
        motif_probability=0.6,
        ornament_probability=0.5,
        note_range_low=38,
        note_range_high=93,  # huge range for "explosion"
        syncopation=0.65,
        rhythm_variety=0.85,
        after_leap="any"     # unpredictable
    )
    
    duration = 160.0 # ~40 bars
    # i - bII - iv - V (Harmonic/Phrygian tension)
    progression = "i bII iv V i bII iv V" * 4 + "I IV V I I IV V I" 
    chords = []
    prog_parts = progression.split()
    beats_per_chord = duration / len(prog_parts)
    for i, p in enumerate(prog_parts):
        k = key_minor if i < len(prog_parts) * 0.7 else key_major
        chord = k.parse_roman(p)
        chord.start = i * beats_per_chord
        chord.duration = beats_per_chord
        chords.append(chord)
        
    notes = gen.render(chords, key_minor, duration)
    
    # Orchestration: Aggressive Strings + Brass
    strings = types.Track(name="Aggressive Strings", program=41, notes=notes, volume=127, expression=127)
    brass_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration, velocity=127) for n in notes if n.velocity > 100]
    brass = types.Track(name="Power Brass", program=62, notes=brass_notes, volume=115)
    
    return [strings, brass], 115.0

def produce_track_3(theme_notes):
    """III. City Hears — Acceptance. Warm, major, broad."""
    print("Producing III. City Hears...")
    key = types.Scale(root=2, mode=types.Mode.MAJOR) # D Major
    # Moderate density, stable leaps
    params = GeneratorParams(density=0.55, leap_probability=0.25)
    
    gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.6,
        motif_probability=0.85, # Strong motif return
        note_range_low=50,
        note_range_high=86,
        phrase_length=8.0,
        register_smoothness=0.85
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
        
    # Inject more thematic memory
    context = RenderContext(prev_pitches=[n.pitch for n in theme_notes])
    
    notes = gen.render(chords, key, duration, context=context)
    
    # Orchestration: Warm Cello + Choir + Ambient
    cello = types.Track(name="Warm Cello", program=43, notes=notes, volume=125, expression=127)
    choir_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration*2, velocity=65) for n in notes if n.start % 2.0 == 0]
    choir = types.Track(name="Acceptance Choir", program=53, notes=choir_notes, volume=90)
    ambient_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=8.0, velocity=70) for n in notes if n.start % 8.0 == 0]
    ambient = types.Track(name="Golden Pad", program=92, notes=ambient_notes, volume=110, expression=115)
    
    return [cello, choir, ambient], 85.0

def main():
    album_dir = Path("output/album_city_that_hears")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("=== STARTING ALBUM PRODUCTION: CITY THAT HEARS ===")
    
    # Track 1
    t1_tracks, t1_melody, t1_bpm = produce_track_1()
    export_midi(t1_tracks, str(album_dir / "01_Ash_in_Pockets.mid"), bpm=t1_bpm)
    
    # Track 2
    t2_tracks, t2_bpm = produce_track_2()
    export_midi(t2_tracks, str(album_dir / "02_The_Crack.mid"), bpm=t2_bpm)
    
    # Track 3 (pass melody from T1 for continuity)
    t3_tracks, t3_bpm = produce_track_3(t1_melody)
    export_midi(t3_tracks, str(album_dir / "03_City_Hears.mid"), bpm=t3_bpm)
    
    print("=== PRODUCTION COMPLETE ===")
    print(f"Files saved to: {album_dir}")

if __name__ == "__main__":
    main()
