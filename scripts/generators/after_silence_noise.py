# Copyright (c) 2026 Bivex
# Album: After Silence Remains Noise (После тишины остаётся шум)
# Format: Cinematic Industrial / Dark Ambient

import os
import random
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def apply_post_production(raw_tracks, bpm, lufs=-14.0, compression=200):
    """Professional mixing and mastering."""
    # Custom desk for this album
    desk = MixingDesk(niche_cfg={})
    # Track-specific gains for our custom names
    desk.track_gains.update({
        "drone": 0.8,
        "piano": 1.0,
        "synth_distorted": 0.9,
        "ind_bass": 1.1,
        "strings": 0.85,
        "minimal_motif": 0.75,
        "resolved_theme": 0.9,
        "sub_bass": 1.0,
        "pad": 0.4
    })
    master = MasteringDesk(target_lufs=lufs)
    
    # Base mix
    mixed = desk.apply_mixing(raw_tracks, [("Dynamics", compression, [])], int(bpm))
    # Mastering
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan

def produce_t1_zero_room():
    """I. Zero Room — Isolation.
    Low drone, sparse piano, long tails.
    """
    print("Rendering I. Zero Room...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR) # D Minor
    
    # 1. Low Drone (Bass)
    drone_notes = [types.NoteInfo(pitch=26, start=i*16, duration=16.1, velocity=40) for i in range(8)]
    
    # 2. Sparse Piano
    gen = MelodyGenerator(
        GeneratorParams(density=0.08, leap_probability=0.2),
        note_range_low=48, note_range_high=72,
        phrase_length=16.0, register_smoothness=0.9
    )
    chords = []
    for i in range(8):
        chord = key.parse_roman("i")
        chord.start = i * 16
        chord.duration = 16
        chords.append(chord)
    
    piano_notes = gen.render(chords, key, 128.0)
    # Save theme for finale
    theme = [n for n in piano_notes[:10]] 
    
    return {"drone": drone_notes, "piano": piano_notes}, theme, 50.0

def produce_t2_displacement():
    """II. Displacement — Distortion.
    Broken rhythm, minor seconds, tritones.
    """
    print("Rendering II. Displacement...")
    key = types.Scale(root=2, mode=types.Mode.LOCRIAN) # D Locrian (dissonant)
    
    gen = MelodyGenerator(
        GeneratorParams(density=0.4),
        syncopation=0.8,
        harmony_note_probability=0.2, # More non-chord tones
        rhythm_variety=0.9,
        allow_7th=True
    )
    # Segments with "drops"
    chords_str = ["i", "bII", "v"] * 4
    chords = []
    for i, s in enumerate(chords_str):
        chord = key.parse_roman(s)
        chord.start = i * 8
        chord.duration = 8
        chords.append(chord)
        
    notes = gen.render(chords, key, 96.0)
    
    return {"synth_distorted": notes}, 72.0

def produce_t3_black_impulse():
    """III. Black Impulse — Culmination.
    Industrial pulse, aggressive bass, high density.
    """
    print("Rendering III. Black Impulse...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    
    # Aggressive bass (Industrial pulse)
    bass_notes = []
    for i in range(128): # 1/8 notes
        if i % 8 in [0, 3, 6]: # Polyrhythmic feel
            bass_notes.append(types.NoteInfo(pitch=26, start=i*0.5, duration=0.4, velocity=110))

    # Aggressive strings
    gen = MelodyGenerator(
        GeneratorParams(density=0.85, leap_probability=0.5),
        drama_shape="dramatic",
        ornament_probability=0.4,
        note_range_low=60, note_range_high=96
    )
    chords = []
    for i in range(16):
        chord = key.parse_roman("i")
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
        
    strings = gen.render(chords, key, 64.0)
    
    return {"ind_bass": bass_notes, "strings": strings}, 115.0

def produce_t4_ash_horizon():
    """IV. Ash Horizon — Aftermath.
    Monotony, minimalism, emptiness.
    """
    print("Rendering IV. Ash Horizon...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    
    # One repeating motif
    motif = [
        types.NoteInfo(pitch=50, start=0, duration=2, velocity=50),
        types.NoteInfo(pitch=49, start=2, duration=2, velocity=45),
        types.NoteInfo(pitch=46, start=4, duration=4, velocity=40),
    ]
    notes = []
    for i in range(10): # 10 repetitions
        for n in motif:
            notes.append(types.NoteInfo(pitch=n.pitch, start=n.start + i*8, duration=n.duration, velocity=n.velocity))
            
    return {"minimal_motif": notes}, 65.0

def produce_t5_new_density(t1_theme):
    """V. New Density — Stability.
    Return of T1 theme, stable harmony, deep bass.
    """
    print("Rendering V. New Density...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    
    # Transform T1 theme into stable harmony
    resolved_theme = []
    for n in t1_theme:
        resolved_theme.append(types.NoteInfo(pitch=n.pitch, start=n.start, duration=n.duration, velocity=70))
        
    # Soft deep bass
    sub_bass = [types.NoteInfo(pitch=26, start=i*8, duration=7.9, velocity=60) for i in range(8)]
    
    return {"resolved_theme": resolved_theme, "sub_bass": sub_bass}, 85.0

def main():
    album_dir = Path("output/after_silence_noise")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "!"*60)
    print("   ALBUM PRODUCTION: AFTER SILENCE REMAINS NOISE")
    print("!"*60 + "\n")
    
    # 1. Zero Room
    t1_raw, t1_theme, t1_bpm = produce_t1_zero_room()
    t1_m, t1_p = apply_post_production(t1_raw, t1_bpm, lufs=-20.0)
    export_multitrack_midi(t1_m, str(album_dir / "01_Zero_Room.mid"), bpm=t1_bpm, cc_events=t1_p)
    
    # 2. Displacement
    t2_raw, t2_bpm = produce_t2_displacement()
    t2_m, t2_p = apply_post_production(t2_raw, t2_bpm, lufs=-16.0, compression=400)
    export_multitrack_midi(t2_m, str(album_dir / "02_Displacement.mid"), bpm=t2_bpm, cc_events=t2_p)
    
    # 3. Black Impulse
    t3_raw, t3_bpm = produce_t3_black_impulse()
    t3_m, t3_p = apply_post_production(t3_raw, t3_bpm, lufs=-9.0, compression=600)
    export_multitrack_midi(t3_m, str(album_dir / "03_Black_Impulse.mid"), bpm=t3_bpm, cc_events=t3_p)
    
    # 4. Ash Horizon
    t4_raw, t4_bpm = produce_t4_ash_horizon()
    t4_m, t4_p = apply_post_production(t4_raw, t4_bpm, lufs=-18.0)
    export_multitrack_midi(t4_m, str(album_dir / "04_Ash_Horizon.mid"), bpm=t4_bpm, cc_events=t4_p)
    
    # 5. New Density
    t5_raw, t5_bpm = produce_t5_new_density(t1_theme)
    t5_m, t5_p = apply_post_production(t5_raw, t5_bpm, lufs=-12.0)
    export_multitrack_midi(t5_m, str(album_dir / "05_New_Density.mid"), bpm=t5_bpm, cc_events=t5_p)

    print("\n" + "="*60)
    print(f"   DONE. Results in: {album_dir}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
