# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
demo_fibril_symphony.py — Demonstration of the FIBRIL-integrated 48-voice engine.

This symphony showcases Melodica's new capability to generate dense, cascading 
polyphonic clusters of up to 48 voices using the FIBRIL allocation logic.
The arrangement features a lead flute controlling the orchestral density.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from melodica import types
from melodica.generators import GeneratorParams, MelodyGenerator
from melodica.engines.fibril_engine import FibrilEngine
from melodica.composer.album_pipeline import produce_track, Mood

def generate_symphony():
    print("=" * 70)
    print("   GENERATING: FIBRIL SYMPHONY (48-VOICE ORCHESTRAL CLUSTERS)")
    print("=" * 70)
    
    # D Dorian - Grave and Majestic
    key = types.Scale(root=2, mode=types.Mode.DORIAN) 
    bpm, dur = 60, 64.0
    
    # 1. Lead Controller (Flute)
    # The velocity of this track will drive the FIBRIL rank density
    chords_base = types.parse_progression("i:16.0 - IV:16.0 - v:16.0 - i:16.0", key)
    lead_notes = MelodyGenerator(
        GeneratorParams(density=0.45, complexity=0.6, key_range_low=72, key_range_high=93),
        phrase_length=8.0
    ).render(chords_base, key, dur)

    # 2. FIBRIL Cascade Engine
    # This generates the underlying polyphonic mass
    engine = FibrilEngine()
    req = types.HarmonizationRequest(
        melody=lead_notes,
        key=key,
        chord_rhythm=4.0, # Evaluate rank activity every bar
        engine="fibril"
    )
    
    print("   [Fibril] Constructing harmonic cascades...")
    fibril_labels = engine.harmonize(req)
    
    # 3. Orchestration Mapping
    # We take the 48 generated voices from FIBRIL metadata and split them
    orchestra = {
        "strings_high": [],
        "strings_low": [],
        "organ_cluster": []
    }
    
    for label in fibril_labels:
        if hasattr(label, "fibril_metadata"):
            voices = label.fibril_metadata["voices"]
            for v in voices:
                # Add slight start jitter for 'cascading' feel
                start_jit = label.start + (random.random() * 0.1)
                note = types.NoteInfo(
                    pitch=v, 
                    start=start_jit, 
                    duration=label.duration * 0.9, 
                    velocity=random.randint(45, 65)
                )
                
                if v > 72: orchestra["strings_high"].append(note)
                elif v < 48: orchestra["strings_low"].append(note)
                else: orchestra["organ_cluster"].append(note)

    # Add the controller lead
    orchestra["flute_lead"] = lead_notes

    print(f"   [Fibril] Arrangement complete. Peak polyphony: {max(label.fibril_metadata['total_density'] for label in fibril_labels if hasattr(label, 'fibril_metadata'))} voices.")
    
    # 4. Final Production
    produce_track(
        tracks=orchestra,
        bpm=bpm,
        instruments={
            "flute_lead": 73,   # Flute
            "strings_high": 44, # Tremolo Strings
            "strings_low": 42,  # Cello/Bass
            "organ_cluster": 19 # Church Organ
        },
        path="output/fibril_symphony.mid",
        mood=Mood.CINEMATIC,
        key=key,
        verbose=True
    )
    
    print("\n[Success] 'Fibril Symphony' generated: output/fibril_symphony.mid")

if __name__ == "__main__":
    import random # needed for jitter
    generate_symphony()
