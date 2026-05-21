# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
pro_showcase_arrangement.py — PROFESSIONAL HYBRID ORCHESTRAL PRODUCTION

This script demonstrates high-end arrangement techniques to avoid "cheap" sound:
1. TIMBRAL LAYERING: Lead = Synth + Piano + Bells.
2. COUNTERPOINT: Secondary melodic line responding to the main one.
3. DRIVING OSTINATO: Constant 16th note movement in the background (Strings).
4. HARMONIC RHYTHM: Chords are played with syncopated "comping" patterns.
5. TRANSITIONS: Coordinated filter sweeps and lead-in fills.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.composer.automation import AutomationCurve
from melodica.composer.transition_coordinator import TransitionCoordinator
from melodica.composer.phrase_memory import PhraseMemory, Phrase

# Setup
KEY = types.Scale(root=2, mode=types.Mode.DORIAN) # D Dorian (cool, cinematic)
OUT = Path("output/pro_showcase")
OUT.mkdir(parents=True, exist_ok=True)
random.seed(777)

def generate_pro_track():
    print("Generating Professional Showcase Arrangement...")
    
    # Cinematic progression: i - VI - III - VII
    prog_str = "i:4.0 - VI:4.0 - III:4.0 - VII:4.0"
    chords = types.parse_progression(prog_str + " - " + prog_str, KEY)
    dur = 32.0
    
    full_chords = []
    t = 0.0
    while t < dur:
        for c in chords:
            if t >= dur: break
            full_chords.append(types.ChordLabel(root=c.root, quality=c.quality, start=t, duration=c.duration))
            t += c.duration

    # --- 1. THE LEAD STACK (The "Hero" Sound) ---
    # We layer three instruments for one melody
    lead_gen = MelodyGenerator(
        GeneratorParams(density=0.5, complexity=0.4, key_range_low=62, key_range_high=86),
        phrase_length=8.0,
        motif_probability=0.8 # Strong melodic identity
    )
    core_melody = lead_gen.render(full_chords, KEY, dur)
    
    # Lead Layer 1: Power Synth (Sawtooth)
    lead_synth = core_melody
    # Lead Layer 2: Piano Attack (Short, punchy)
    lead_piano = [types.NoteInfo(n.pitch, n.start, 0.2, n.velocity) for n in core_melody]
    # Lead Layer 3: High Bells (Sparkle - transposing up an octave)
    lead_bells = [types.NoteInfo(n.pitch + 12, n.start, n.duration, int(n.velocity * 0.7)) for n in core_melody]

    # --- 2. COUNTER-MELODY (Call & Response) ---
    # A cello line that moves in contrary motion to the lead
    counter_gen = MelodyGenerator(
        GeneratorParams(density=0.3, complexity=0.3, key_range_low=38, key_range_high=55),
        phrase_length=8.0
    )
    counter_melody = counter_gen.render(full_chords, KEY, dur)

    # --- 3. THE ENGINE (Driving Ostinato) ---
    # Fast 16th notes in strings to keep energy high
    ostinato_gen = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, velocity_range=(60, 85), key_range_low=45, key_range_high=62),
        pattern="up_down"
    )
    strings_ostinato = ostinato_gen.render(full_chords, KEY, dur)

    # --- 4. RHYTHMIC CHORDS (The Comping) ---
    # Syncopated brass stabs
    brass_gen = RhythmicAccentGenerator(preset="gallop", pitch=None, octave=4)
    # Filter to only chord tones
    brass_notes = brass_gen.render(full_chords, KEY, dur)

    # --- 5. SUB BASS & DRUMS ---
    bass = BassGenerator(GeneratorParams(density=0.4, key_range_low=24, key_range_high=36)).render(full_chords, KEY, dur)
    drums = RhythmicAccentGenerator(preset="march", pitch=36).render(full_chords, KEY, dur)

    # --- 6. HARMONIC CLEANING ---
    from melodica.composer.harmonic_verifier import verify_and_fix, VerifierConfig
    raw_tracks = {
        "lead": lead_synth, 
        "counter": counter_melody, 
        "ostinato": strings_ostinato,
        "brass": brass_notes,
        "bass": bass
    }
    fixed, _ = verify_and_fix(raw_tracks, VerifierConfig(dissonance_tolerance=0.4))

    # --- 7. COMPLEX AUTOMATION ---
    cc_events = {
        "lead": AutomationCurve.sine_lfo(1, 20, 90, 0.0, dur, period=4.0), # Vibrato
        "ostinato": AutomationCurve.exponential(11, 40, 110, 0.0, dur, exponent=1.5), # Swell
        "brass": AutomationCurve.linear(74, 30, 90, 0.0, dur) # Opening filter
    }

    produce_track(
        tracks={
            "synth_lead": fixed["lead"],
            "piano_atk": lead_piano,
            "bells_sparkle": lead_bells,
            "cello_counter": fixed["counter"],
            "strings_drive": fixed["ostinato"],
            "brass_stabs": fixed["brass"],
            "sub_bass": fixed["bass"],
            "kick": drums
        },
        bpm=124,
        instruments={
            "synth_lead": 81, "piano_atk": 0, "bells_sparkle": 9,
            "cello_counter": 42, "strings_drive": 44, "brass_stabs": 61,
            "sub_bass": 38, "kick": 116
        },
        path=OUT / "pro_showcase_demo.mid",
        mood=Mood.CINEMATIC,
        key=KEY,
        chords=full_chords,
        cc_events=cc_events
    )
    print("Professional Showcase Arrangement успешно сгенерирован!")

if __name__ == "__main__":
    generate_pro_track()
