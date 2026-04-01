"""
demo_song_generator.py — A showcase of the Melodica Phrase Generation Engine.
Generates a multi-track MIDI file (demo_song.mid) using all features:
- Core: Functional AI harmonization.
- Rhythm Engine: Euclidean, Probabilistic, Subdivision.
- Phrase Generators: Bass, Fingerpicking, Melody, Chords.
- Modifiers: Swing, Quantize, Humanize.
"""

from pathlib import Path
import mido

from melodica.engines.functional import FunctionalEngine
from melodica.types import Note, HarmonizationRequest, Scale, Mode, PhraseInstance
from melodica.generators import (
    GeneratorParams, BassGenerator, FingerpickingGenerator, 
    MelodyGenerator, ChordGenerator
)
from melodica.modifiers import (
    HumanizeModifier, SwingController, LimitNoteRangeModifier, QuantizeModifier
)
from melodica.rhythm import (
    EuclideanRhythmGenerator, ProbabilisticRhythmGenerator, SubdivisionGenerator
)

def create_demo_song():
    print("🥁 Starting Melodica Demo Engine...")

    # 1. Define a basic melody seed (just to kick off harmonization)
    # 4 bars in A minor
    melody = [
        Note(pitch=69, start=0.0, duration=4.0), # A4
        Note(pitch=65, start=4.0, duration=4.0), # F4
        Note(pitch=62, start=8.0, duration=4.0), # D4
        Note(pitch=64, start=12.0, duration=4.0),# E4
    ]
    key = Scale(root=9, mode=Mode.NATURAL_MINOR) # A minor

    # 2. Harmonize!
    print("🎶 Harmonizing melody using FunctionalEngine...")
    engine = FunctionalEngine()
    req = HarmonizationRequest(melody, key, chord_rhythm=4.0)
    chords = engine.harmonize(req)
    
    print(f"✅ Generated {len(chords)} chords:")
    for c in chords:
        print(f"  - {c.quality.name} on root PC {c.root} (start={c.start})")

    print("ギター, 🎹, 🎷 Generating Tracks...")
    
    # ----------------------------------------------------
    # Track 1: Pad / Core Chords (Simple Subdivision)
    # ----------------------------------------------------
    chord_gen = ChordGenerator(
        params=GeneratorParams(density=1.0, key_range_low=48, key_range_high=72),
        voicing="closed",
        rhythm=SubdivisionGenerator(divisions_per_beat=2, tie_chance=0.8) # Syncopated block chords
    )
    pad_phrase = PhraseInstance(generator=chord_gen)
    pad_notes = pad_phrase.render(chords, key)

    # ----------------------------------------------------
    # Track 2: Bass (Root-Fifth with Euclidean Rhythm)
    # ----------------------------------------------------
    bass_gen = BassGenerator(
        params=GeneratorParams(density=1.0, key_range_low=36, key_range_high=48),
        style="root_fifth",
        # E(5, 8) over 2 beats (Tresillo feel repeating)
        rhythm=EuclideanRhythmGenerator(slots_per_beat=4, hits_per_bar=6)
    )
    bass_phrase = PhraseInstance(
        generator=bass_gen,
        modifiers=[QuantizeModifier(grid_resolution=0.25)]
    )
    bass_notes = bass_phrase.render(chords, key)

    # ----------------------------------------------------
    # Track 3: Lead Melody (Probabilistic + Swing + Humanize)
    # ----------------------------------------------------
    melody_gen = MelodyGenerator(
        params=GeneratorParams(density=0.6, key_range_low=72, key_range_high=85),
        prefer_chord_tones=0.8,
        rhythm=ProbabilisticRhythmGenerator(
            grid_resolution=0.25, density=0.5, syncopation=0.3
        )
    )
    lead_phrase = PhraseInstance(
        generator=melody_gen,
        # Applied effects chain!
        modifiers=[
            SwingController(swing_ratio=0.65, grid=1.0), # 16th note swing
            HumanizeModifier(timing_std=0.015, velocity_std=10.0),
            LimitNoteRangeModifier(low=65, high=88)
        ]
    )
    lead_notes = lead_phrase.render(chords, key)

    # ----------------------------------------------------
    # Track 4: Fingerpicking Acoustic Guitar
    # ----------------------------------------------------
    guitar_gen = FingerpickingGenerator(
        params=GeneratorParams(key_range_low=45),
        pattern=[0, 2, 1, 3, 2, 3], # Complex picking pattern over the arpeggio
        rhythm=SubdivisionGenerator(divisions_per_beat=4) # 16th notes
    )
    guitar_phrase = PhraseInstance(generator=guitar_gen)
    guitar_notes = guitar_phrase.render(chords, key)

    # ----------------------------------------------------
    # Export to multi-track MIDI
    # ----------------------------------------------------
    print("💾 Exporting to demo_song.mid...")
    
    mid = mido.MidiFile(ticks_per_beat=480)
    
    def add_track(name: str, notes, channel: int, program: int):
        track = mido.MidiTrack()
        track.name = name
        mid.tracks.append(track)
        track.append(mido.Message('program_change', program=program, time=0, channel=channel))
        
        events = []
        for n in notes:
            on_tick = round(n.start * 480)
            off_tick = round((n.start + n.duration) * 480)
            events.append((on_tick, "note_on", n.pitch, n.velocity))
            events.append((off_tick, "note_off", n.pitch, 0))
            
        events.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))
        
        prev_tick = 0
        for tick, msg_type, pitch, vel in events:
            delta = tick - prev_tick
            track.append(mido.Message(msg_type, note=pitch, velocity=vel, time=delta, channel=channel))
            prev_tick = tick

    add_track("Pad", pad_notes, channel=0, program=89)         # Pad 1 (new age)
    add_track("Bass", bass_notes, channel=1, program=33)       # Electric Bass (finger)
    add_track("Guitar", guitar_notes, channel=2, program=25)   # Acoustic Guitar (steel)
    add_track("Lead", lead_notes, channel=3, program=73)       # Flute

    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "demo_song.mid"
    mid.save(str(out_path))
    print(f"✨ BAM! {out_path.absolute()} created successfully. Drop it into your DAW!")

if __name__ == "__main__":
    create_demo_song()
