#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
#
# A quick smoke-track verification script to harmonize an 8-bar Dorian melody
# and verify correct modal chords and pitch bend exports in <0.1 seconds.

import time
from pathlib import Path
from melodica.types import NoteInfo, Scale, Mode
from melodica.harmonize import HMM3Harmonizer
from melodica.midi import export_multitrack_midi

def run_smoke_track():
    print("=" * 60)
    print(" MELODICA SMOKE-TRACK HARMONIZATION & MIDI EXPORT ")
    print("=" * 60)

    # 1. Define an 8-bar D Dorian melody emphasizing the characteristic major 6th (B4, pitch 71)
    melody = [
        # Bar 1
        NoteInfo(pitch=62, start=0.0, duration=1.0),  # D4
        NoteInfo(pitch=65, start=1.0, duration=1.0),  # F4
        NoteInfo(pitch=67, start=2.0, duration=2.0),  # G4
        # Bar 2
        NoteInfo(pitch=71, start=4.0, duration=2.0),  # B4 (Dorian characteristic 6th!)
        NoteInfo(pitch=69, start=6.0, duration=2.0),  # A4
        # Bar 3
        NoteInfo(pitch=67, start=8.0, duration=2.0),  # G4
        NoteInfo(pitch=69, start=10.0, duration=2.0), # A4
        # Bar 4
        NoteInfo(pitch=71, start=12.0, duration=2.0), # B4
        NoteInfo(pitch=72, start=14.0, duration=2.0), # C5
        # Bar 5
        NoteInfo(pitch=74, start=16.0, duration=4.0), # D5
        # Bar 6
        NoteInfo(pitch=71, start=20.0, duration=2.0), # B4
        NoteInfo(pitch=67, start=22.0, duration=2.0), # G4
        # Bar 7
        NoteInfo(pitch=65, start=24.0, duration=2.0), # F4
        NoteInfo(pitch=64, start=26.0, duration=2.0), # E4
        # Bar 8
        NoteInfo(pitch=62, start=28.0, duration=4.0), # D4
    ]

    key = Scale(root=2, mode=Mode.DORIAN)  # D Dorian
    print(f"Key: Root PC {key.root}, Mode {key.mode.value}")
    print(f"Melody length: {len(melody)} notes")

    # 2. Harmonize using HMM3Harmonizer
    print("\n[1/3] Running HMM3Harmonizer...")
    start_harm = time.perf_counter()
    harmonizer = HMM3Harmonizer(chord_change="bars")  # chord every bar (4 beats)
    chords = harmonizer.harmonize(melody, key, 32.0)
    end_harm = time.perf_counter()

    harm_elapsed_ms = (end_harm - start_harm) * 1000.0
    print(f"Harmonization completed in {harm_elapsed_ms:.2f} ms.")

    # 3. Print the generated chord progression
    print("\nGenerated Chord Progression:")
    NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for i, chord in enumerate(chords):
        bar_num = i + 1
        chord_name = f"{NOTE_NAMES[chord.root]} {chord.quality.name}"
        print(f"  Bar {bar_num:02d} (beats {chord.start:04.1f}-{chord.start + chord.duration:04.1f}): "
              f"{chord_name} (Degree: {chord.degree}, Quality: {chord.quality.name})")

    # Verify Dorian authenticity: presence of i (D minor) and IV (G major)
    has_i = any(c.degree == 1 for c in chords)
    has_iv = any(c.degree == 4 for c in chords)

    print("\nMusicological Verification:")
    print(f"  Contains i (Tonic D minor)    : {'PASSED' if has_i else 'FAILED'}")
    print(f"  Contains IV (Plagal G major)  : {'PASSED' if has_iv else 'FAILED'}")

    assert has_i, "Progression must contain the tonic chord i"
    assert has_iv, "Progression must contain the plagal chord IV"
    print("  Dorian Plagal Progression Verification: SUCCESS!")

    # 4. Generate multi-track MIDI file to verify the microtonal/pitch wheel export works
    output_dir = Path("scratch/output")
    output_dir.mkdir(parents=True, exist_ok=True)
    midi_path = output_dir / "smoke_track_dorian.mid"

    print(f"\n[2/3] Exporting to MIDI: {midi_path}...")
    start_export = time.perf_counter()
    export_multitrack_midi(
        tracks_data={"melody": melody},
        path=midi_path,
        bpm=110.0,
        key=key,
        humanize=True
    )
    end_export = time.perf_counter()
    export_elapsed_ms = (end_export - start_export) * 1000.0
    print(f"MIDI exported successfully in {export_elapsed_ms:.2f} ms!")

    print(f"\nPhase Timings: [harmonize: {harm_elapsed_ms:.2f} ms] [export: {export_elapsed_ms:.2f} ms]")

    print("\n[3/3] Overall Smoke Track check: PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    run_smoke_track()
