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
album_city_that_hears.py — "Director's Cut" Production.
Leverages all new engine features:
- Global/Micro Buildup via DramaticArc
- Motivic Narrative (Full -> Fragment -> Return)
- Tension-aware Pitching & Density
- Professional Mixing & Mastering
"""

import os
import random
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.render_context import RenderContext
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def produce_track_1():
    """I. Ash in Pockets — Silence/Void. 
    Focus: Isolation, frozen movement, 'breath' phrases.
    """
    print("Producing I. Ash in Pockets...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)  # D Minor
    params = GeneratorParams(density=0.18, leap_probability=0.1)
    
    gen = MelodyGenerator(
        params,
        drama_shape="crescendo",
        drama_peak=0.9,
        motif_probability=0.2,
        harmony_note_probability=0.9, # Stay safe on chords
        note_range_low=45,
        note_range_high=65,
        phrase_length=12.0,
        register_smoothness=0.95,      # Very stable register
        steps_probability=0.9,         # Almost all steps
        first_note="tonic",
        last_note="last_chord_root"
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
    # Low-pass pad doubling
    pad_notes = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration*2.5, velocity=int(n.velocity*0.75)) for n in notes]
    
    raw_tracks = {"piano": notes, "pad": pad_notes}
    return raw_tracks, notes, 60.0

def produce_track_2():
    """II. The Crack — Conflict.
    Focus: Chaos, aggressive leaps, climbing tension, syncopation.
    """
    print("Producing II. The Crack...")
    key_minor = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    key_major = types.Scale(root=2, mode=types.Mode.MAJOR)

    params = GeneratorParams(density=0.88, leap_probability=0.65)
    gen = MelodyGenerator(
        params,
        drama_shape="dramatic",
        drama_peak=0.7,
        motif_probability=0.5,
        ornament_probability=0.6,    # High virtuosity/panic
        harmony_note_probability=0.4, # Tension-heavy (non-chord tones)
        note_range_low=36,           # Deep bass
        note_range_high=96,          # Screaming highs
        syncopation=0.75,            # Very off-beat
        rhythm_variety=0.9,
        after_leap="any",            # Jagged movement
        random_movement=0.5,
        direction_bias=0.3,          # Upward climb
        allow_7th=True,
        allow_2nd=True
    )

    duration = 160.0
    progression = "i bII iv V i bII iv V" * 4 + "I IV V I I IV V I"
    chords = []
    prog_parts = progression.split()
    beats_per_chord = duration / len(prog_parts)
    major_start = int(len(prog_parts) * 0.7)
    for i, p in enumerate(prog_parts):
        k = key_major if i >= major_start else key_minor
        chord = k.parse_roman(p)
        chord.start = i * beats_per_chord
        chord.duration = beats_per_chord
        chords.append(chord)

    # Render minor section and major section separately, then combine
    minor_chords = [c for c in chords if c.start < major_start * beats_per_chord]
    major_chords = [c for c in chords if c.start >= major_start * beats_per_chord]

    minor_notes = gen.render(minor_chords, key_minor, major_start * beats_per_chord)
    major_notes = gen.render(major_chords, key_major, (len(prog_parts) - major_start) * beats_per_chord)

    # Offset major section
    offset = major_start * beats_per_chord
    for n in major_notes:
        n.start += offset

    notes = minor_notes + major_notes

    # Aggressive brass hits on accents
    fanfare_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=0.2, velocity=127) for n in notes if n.velocity > 115]

    raw_tracks = {"lead": notes, "fanfare": fanfare_notes}
    return raw_tracks, 118.0

def produce_track_3(theme_notes):
    """III. City Hears — Acceptance. 
    Focus: Thematic return, warmth, wide stable intervals, chorale feel.
    """
    print("Producing III. City Hears...")
    key = types.Scale(root=2, mode=types.Mode.MAJOR) # D Major
    params = GeneratorParams(density=0.5, leap_probability=0.3)
    
    gen = MelodyGenerator(
        params,
        drama_shape="epic",
        drama_peak=0.65,
        motif_probability=0.95,      # Strongest motif recall
        harmony_note_probability=0.8,
        note_range_low=52,
        note_range_high=84,
        phrase_length=8.0,
        register_smoothness=0.9,
        penultimate_step_above=True,
        first_note="tonic"
    )
    
    duration = 128.0
    progression = "I IV vi V I IV vi V" * 4
    chords = []
    prog_parts = progression.split()
    beats_per_chord = duration / len(prog_parts)
    for i, p in enumerate(prog_parts):
        chord = key.parse_roman(p)
        chord.start = i * beats_per_chord
        chord.duration = beats_per_chord
        chords.append(chord)
        
    # Inject full thematic memory from Track 1
    context = RenderContext(
        phrase_position=0.0, # start of this section
        prev_pitches=[n.pitch for n in theme_notes[-12:]] # last motifs of isolation
    )
    
    notes = gen.render(chords, key, duration, context=context)
    
    # Choir following the melody in octaves/harmonies
    voice_notes = [types.NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration, velocity=85) for n in notes if n.start % 1.0 < 0.1]
    ambient_notes = [types.NoteInfo(pitch=random.choice([50, 54, 57]), start=i*8.0, duration=8.0, velocity=70) for i in range(16)]
    
    raw_tracks = {"lead": notes, "voice": voice_notes, "pad": ambient_notes}
    return raw_tracks, 82.0

def apply_post_production(raw_tracks, bpm, lufs=-12.0):
    """Refined mixing/mastering chain."""
    # Custom desk for this album
    desk = MixingDesk(niche_cfg={})
    # Track-specific gains to ensure balance
    desk.track_gains.update({
        "piano": 1.05,
        "pad": 0.45,
        "lead": 0.95,
        "fanfare": 1.1,
        "voice": 0.7
    })
    
    # Mix
    mixed_tracks = desk.apply_mixing(raw_tracks, [("Dynamics", 300, [])], int(bpm))
    
    # Master
    master = MasteringDesk(target_lufs=lufs)
    # Dangerous compression for Track 2 (handled by LUFS usually)
    mastered_tracks, pan_events = master.apply_mastering(mixed_tracks)
    
    return mastered_tracks, pan_events

def main():
    album_dir = Path("output/album_city_that_hears")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "="*50)
    print("   ALBUM PRODUCTION: CITY THAT HEARS (V2)")
    print("="*50 + "\n")
    
    # Track 1
    t1_raw, t1_melody, t1_bpm = produce_track_1()
    t1_m, t1_pan = apply_post_production(t1_raw, t1_bpm, lufs=-19.0) # Airy & Distant
    export_multitrack_midi(t1_m, str(album_dir / "01_Ash_in_Pockets.mid"), 
                           bpm=t1_bpm, cc_events=t1_pan, 
                           instruments={"piano": 1, "pad": 89})
    
    # Track 2
    t2_raw, t2_bpm = produce_track_2()
    t2_m, t2_pan = apply_post_production(t2_raw, t2_bpm, lufs=-8.5) # CRUSHINGLY LOUD
    export_multitrack_midi(t2_m, str(album_dir / "02_The_Crack.mid"), 
                           bpm=t2_bpm, cc_events=t2_pan, 
                           instruments={"lead": 48, "fanfare": 61}) # Orchestral Strings & Brass
    
    # Track 3
    t3_raw, t3_bpm = produce_track_3(t1_melody)
    t3_m, t3_pan = apply_post_production(t3_raw, t3_bpm, lufs=-13.0) # WARM & BROAD
    export_multitrack_midi(t3_m, str(album_dir / "03_City_Hears.mid"), 
                           bpm=t3_bpm, cc_events=t3_pan, 
                           instruments={"lead": 42, "voice": 52, "pad": 91}) # Cello, Choir, Space Pad
    
    print("\n" + "="*50)
    print("   PRODUCTION COMPLETE. ALL TRACKS RENDERED.")
    print(f"   Location: {album_dir}")
    print("="*50 + "\n")

if __name__ == "__main__":
    main()
