# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18
# Last Updated: 2026-05-18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import os
from melodica.types import Scale, Mode, NoteInfo
from melodica.theory import Quality
from melodica.theory.voicing import voice_lead, chord_to_notes
from melodica.midi import export_multitrack_midi
from melodica.tracer import EngineTracer

def run_demo():
    print("=== Generating Expert Harmonies Showcase ===")

    # Create output directory
    os.makedirs("output", exist_ok=True)
    trace_path = "output/expert_harmonies_trace.log"

    with EngineTracer(output_path=trace_path, show_private=True, show_duration=True, use_colors=False):
        # 1. Setup scale
        key = Scale(root=0, mode=Mode.MAJOR) # C Major

        # 2. Progression showcasing various custom qualities and inversions:
        # - Imystic: Scriabin mystic chord on tonic
        # - IV7s11: Lydian dominant on IV (F7#11)
        # - V7b9: Spanish Phrygian dominant on V (G7b9)
        # - bVIIphryg: Phrygian major on flat VII
        # - Icl4: Quartal chord on tonic
        # - I/3: First inversion of I
        # - ii/3: First inversion of ii
        progression_tokens = [
            "Imystic",
            "IV7s11",
            "V7b9",
            "bVIIphryg",
            "Icl4",
            "I/3",
            "ii/3",
            "Imystic"
        ]

        # 3. Parse and analyze chords
        chords = [key.parse_roman(token) for token in progression_tokens]

        # 4. Generate smooth voice-leading track
        voice_led_notes: list[NoteInfo] = []
        block_notes: list[NoteInfo] = []

        beat_step = 4.0

        for i, chord in enumerate(chords):
            onset = i * beat_step
            chord.start = onset
            chord.duration = beat_step

            # Voicing A: Raw template conversion (block chords without voice leading)
            raw_pitches = chord_to_notes(chord, base_octave=4)
            for p in raw_pitches:
                block_notes.append(NoteInfo(pitch=p, start=onset, duration=beat_step, velocity=80))

            # Voicing B: Smooth voice leading relative to previous chord!
            if i == 0:
                led_pitches = raw_pitches
            else:
                # Let's voice lead dynamically by passing the pre-calculated pitch lists!
                led_pitches = voice_lead(led_pitches, raw_pitches)

            for p in led_pitches:
                voice_led_notes.append(NoteInfo(pitch=p, start=onset, duration=beat_step, velocity=95))

    out_path = "output/expert_harmonies_showcase.mid"

    # Export tracks to MIDI
    tracks_data = {
        "Block Chords (Raw)": block_notes,
        "Smooth Voice Leading": voice_led_notes
    }

    export_multitrack_midi(tracks_data, out_path, bpm=100.0)
    print(f"Success! Masterpiece exported to {out_path}")
    print(f"Execution trace written to {trace_path}")

if __name__ == "__main__":
    run_demo()
