# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
modern_hit_generator.py — THE MODERN PRODUCER PIPELINE (FIXED)

Demonstrates 10 modern production principles with MIDI DOCTOR fixes:
1. Register Separation: Leads raised, Bass clamped to low frequencies.
2. Harmonic Cleaning: Using verify_and_fix to remove m2/M7 clashes.
3. Call & Response: Interplay between Lead and Synth.
4. Micro-variations: Repeating phrases with slight tweaks.
5. Loop-thinking: Stackable layers.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.composer.automation import AutomationCurve
from melodica.composer.transition_coordinator import TransitionCoordinator
from melodica.composer.phrase_memory import PhraseMemory, Phrase

# Setup
KEY = types.Scale(root=0, mode=types.Mode.MAJOR)
OUT = Path("output/modern_hit")
OUT.mkdir(parents=True, exist_ok=True)
random.seed(2026)

def generate_hit():
    print("Generating a Fixed Modern Hit...")
    
    # 8 bars of progression: I - IV - vi - V
    prog_str = "I:4.0 - IV:4.0 - vi:4.0 - V:4.0"
    chords = types.parse_progression(prog_str + " - " + prog_str, KEY)
    dur = 32.0
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- 1. THE HOOK (Raised to avoid bass clash) ---
    hook_gen = MelodyGenerator(
        GeneratorParams(density=0.6, complexity=0.2, key_range_low=72, key_range_high=84),
        phrase_length=4.0,
        mode="downbeat_chord"
    )
    hook_notes = hook_gen.render(full_chords[:2], KEY, 8.0)
    
    # --- 2. MICRO-VARIATIONS ---
    memory = PhraseMemory()
    memory.store(Phrase(notes=tuple(hook_notes), section="hook", tag="main"))
    hook_variation = memory.recall(transform="original", transpose=2)
    for n in hook_variation: n.shift_time(8.0) 
    
    main_hook = hook_notes + hook_variation
    full_lead = main_hook + [types.NoteInfo(n.pitch, n.start+16.0, n.duration, n.velocity) for n in main_hook]

    # --- 3. CALL & RESPONSE (In Mid register) ---
    response_gen = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.3, key_range_low=60, key_range_high=72),
        phrase_length=4.0
    )
    response_notes = response_gen.render(full_chords, KEY, dur)
    lead_starts = {round(n.start, 2) for n in full_lead}
    final_response = [n for n in response_notes if round(n.start, 2) not in lead_starts]

    # --- 4. BASS (Clamped to Low end) ---
    bass = BassGenerator(GeneratorParams(density=0.5, velocity_range=(80, 100), key_range_low=24, key_range_high=48)).render(full_chords, KEY, dur)
    
    # --- 5. PERC & PAUSES ---
    drums = RhythmicAccentGenerator(preset="march", pitch=36).render(full_chords, KEY, dur)
    # Drops
    drums = [n for n in drums if not (12.0 <= n.start < 16.0)]
    full_lead = [n for n in full_lead if not (12.0 <= n.start < 16.0)]

    # --- 6. HARMONIC FIXING (The Doctor's Cure) ---
    from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
    raw_tracks = {"lead": full_lead, "response": final_response, "bass": bass}
    fixed_tracks, _ = verify_and_fix(raw_tracks, VerifierConfig(dissonance_tolerance=0.3))
    
    full_lead = fixed_tracks["lead"]
    final_response = fixed_tracks["response"]
    bass = fixed_tracks["bass"]

    # --- 7. ENERGY AUTOMATION ---
    cc_events = {
        "lead": AutomationCurve.sine_lfo(74, 60, 120, 0.0, dur, period=8.0),
        "response": AutomationCurve.exponential(11, 40, 110, 0.0, dur, exponent=1.5)
    }

    produce_track(
        tracks={"lead": full_lead, "response": final_response, "bass": bass, "drums": drums},
        bpm=128,
        instruments={"lead": 81, "response": 80, "bass": 39, "drums": 116},
        path=OUT / "modern_hit_demo.mid",
        mood=Mood.AGGRESSIVE,
        key=KEY,
        chords=full_chords,
        cc_events=cc_events
    )
    print("Modern Hit сгенерирован и исправлен!")

if __name__ == "__main__":
    generate_hit()
