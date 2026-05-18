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
Applies advanced mixing and mastering logic.
"""

import os
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.render_context import RenderContext
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def produce_track_1():
    """I. Ash in Pockets — Silence/Void. Minimalism and isolation."""
    print("Producing I. Ash in Pockets...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    params = GeneratorParams(density=0.2, leap_probability=0.15)
    
    gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.95,
        motif_probability=0.2,
        note_range_low=45,
        note_range_high=67,
        phrase_length=12.0,
        register_smoothness=0.95
    )
    
    duration = 128.0
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
    pad_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration*2.0, velocity=int(n.velocity*0.7)) for n in notes]
    
    raw_tracks = {"piano": notes, "pad": pad_notes}
    return raw_tracks, notes, 65.0

def produce_track_2():
    """II. The Crack — Conflict/Explosion. High energy and chaos."""
    print("Producing II. The Crack...")
    key_minor = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    key_major = types.Scale(root=2, mode=types.Mode.MAJOR)
    
    params = GeneratorParams(density=0.85, leap_probability=0.7)
    gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.7,
        motif_probability=0.6,
        ornament_probability=0.5,
        note_range_low=38,
        note_range_high=93,
        syncopation=0.65,
        rhythm_variety=0.85,
        after_leap="any"
    )
    
    duration = 160.0
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
    brass_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration, velocity=127) for n in notes if n.velocity > 100]
    
    raw_tracks = {"lead": notes, "fanfare": brass_notes}
    return raw_tracks, 115.0

def produce_track_3(theme_notes):
    """III. City Hears — Acceptance. Warmth and light."""
    print("Producing III. City Hears...")
    key = types.Scale(root=2, mode=types.Mode.MAJOR)
    params = GeneratorParams(density=0.55, leap_probability=0.25)
    
    gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.6,
        motif_probability=0.85,
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
        
    context = RenderContext(prev_pitches=[n.pitch for n in theme_notes])
    notes = gen.render(chords, key, duration, context=context)
    
    choir_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration*2, velocity=65) for n in notes if n.start % 2.0 == 0]
    ambient_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=8.0, velocity=70) for n in notes if n.start % 8.0 == 0]
    
    raw_tracks = {"voice": choir_notes, "lead": notes, "pad": ambient_notes}
    return raw_tracks, 85.0

def apply_post_production(raw_tracks, bpm, lufs=-12.0):
    """Apply mixing and mastering chain."""
    desk = MixingDesk(niche_cfg={})
    mixed_tracks = desk.apply_mixing(raw_tracks, [("Dynamics", 200, [])], int(bpm))
    
    master = MasteringDesk(target_lufs=lufs)
    mastered_tracks, pan_events = master.apply_mastering(mixed_tracks)
    
    return mastered_tracks, pan_events

def main():
    album_dir = Path("output/album_city_that_hears")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("=== STARTING ALBUM PRODUCTION: CITY THAT HEARS ===")
    
    # Track 1
    t1_raw, t1_melody, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-18.0)
    export_multitrack_midi(t1_m, str(album_dir / "01_Ash_in_Pockets.mid"), 
                           bpm=t1_bpm, cc_events=t1_pan, 
                           instruments={"piano": 1, "pad": 90})
    
    # Track 2
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-9.0)
    export_multitrack_midi(t2_m, str(album_dir / "02_The_Crack.mid"), 
                           bpm=t2_bpm, cc_events=t2_pan, 
                           instruments={"lead": 41, "fanfare": 62})
    
    # Track 3
    t3_raw, t3_bpm = produce_track_3(t1_melody)
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-12.0)
    export_multitrack_midi(t3_m, str(album_dir / "03_City_Hears.mid"), 
                           bpm=t3_bpm, cc_events=t3_pan, 
                           instruments={"lead": 43, "voice": 53, "pad": 92})
    
    print("=== PRODUCTION COMPLETE ===")
    print(f"Files saved to: {album_dir}")

if __name__ == "__main__":
    main()
