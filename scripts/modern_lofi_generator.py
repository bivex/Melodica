# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
modern_lofi_generator.py — LOFI CHILL PRODUCER PIPELINE

Demonstrates phrase-based production in a Chill/Lofi aesthetic:
1. Jazz Phrasing: Muted Trumpet with lazy, sparse phrases.
2. Drunk Rhythm: Heavy swing and offset timing for the "head-nod" feel.
3. Frequency Gaps: Wide separation between sub-bass and high-mid leads.
4. Found Sounds: Background rain and vinyl crackle using GM FX.
5. Dynamic Filters: Constant automation of cutoff on the electric piano.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.composer.automation import AutomationCurve
from melodica.composer.phrase_memory import PhraseMemory, Phrase

# Setup
KEY = types.Scale(root=0, mode=types.Mode.MAJOR)
OUT = Path("output/modern_lofi")
OUT.mkdir(parents=True, exist_ok=True)
random.seed(420) # Lofi seed

def generate_lofi():
    print("Generating a Lofi Chill Track...")
    
    # 8 bars of progression: ii - V7 - Imaj7 - IV
    # Dm7 - G7 - Cmaj7 - F
    prog_str = "ii:4.0 - V:4.0 - I:4.0 - IV:4.0"
    chords = types.parse_progression(prog_str + " - " + prog_str, KEY)
    dur = 32.0
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- 1. THE CHILL LEAD (Muted Trumpet) ---
    lead_gen = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.4, key_range_low=67, key_range_high=79),
        phrase_length=4.0,
        syncopation=0.4 # More off-beat notes
    )
    lead_notes = lead_gen.render(full_chords, KEY, dur)
    
    # Add humanization manually for extra "laziness"
    for n in lead_notes:
        n.start += random.uniform(0.02, 0.05) # Slightly late

    # --- 2. THE RHODES CHORDS (Electric Piano 1) ---
    # Using PhraseMemory to repeat a nice rhythmic comping pattern
    chord_gen = MelodyGenerator(
        GeneratorParams(density=0.4, complexity=0.2, key_range_low=48, key_range_high=64),
        phrase_length=4.0
    )
    rhodes_notes = chord_gen.render(full_chords, KEY, dur)

    # --- 3. THE LOW-END (Finger Bass) ---
    # Very simple, mostly root notes
    bass = BassGenerator(
        GeneratorParams(density=0.3, velocity_range=(60, 80), key_range_low=24, key_range_high=43)
    ).render(full_chords, KEY, dur)

    # --- 4. ATMOSPHERE & PERC ---
    # Rain/Vinyl (FX 1: Rain)
    rain = [types.NoteInfo(pitch=96, start=0.0, duration=dur, velocity=40)]
    
    # Simple Kick/Snare pattern (Drums)
    drums = RhythmicAccentGenerator(preset="backbeat", pitch=36).render(full_chords, KEY, dur)

    # --- 5. HARMONIC VERIFIER (Ensuring Jazz consonance) ---
    from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
    raw_tracks = {"lead": lead_notes, "rhodes": rhodes_notes, "bass": bass}
    # Higher tolerance for jazz, but still clean
    fixed_tracks, _ = verify_and_fix(raw_tracks, VerifierConfig(dissonance_tolerance=0.6))

    # --- 6. AUTOMATION (The "Breathing" Mix) ---
    cc_events = {
        "rhodes": AutomationCurve.sine_lfo(74, 30, 70, 0.0, dur, period=8.0), # Lofi low-pass filter
        "rain": AutomationCurve.sine_lfo(11, 20, 50, 0.0, dur, period=16.0),  # Drifting atmosphere
        "lead": AutomationCurve.exponential(1, 0, 60, 0.0, dur, exponent=1.2) # Delayed vibrato
    }

    produce_track(
        tracks={
            "lead": fixed_tracks["lead"], 
            "rhodes": fixed_tracks["rhodes"], 
            "bass": fixed_tracks["bass"], 
            "drums": drums,
            "rain": rain
        },
        bpm=84, # Classic lofi tempo
        instruments={"lead": 59, "rhodes": 4, "bass": 33, "drums": 115, "rain": 96},
        path=OUT / "modern_lofi_demo.mid",
        mood=Mood.INTIMATE,
        key=KEY,
        chords=full_chords,
        cc_events=cc_events
    )
    print("Lofi Chill Track сгенерирован!")

if __name__ == "__main__":
    generate_lofi()
