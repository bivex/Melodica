# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
batch_test_midi.py — Generates test MIDI files for all current generators.
Outputs to: output/test_<generator_name>.mid
"""

from pathlib import Path
import mido

from melodica.engines.functional import FunctionalEngine
from melodica.types import Note, HarmonizationRequest, Scale, Mode, PhraseInstance
from melodica.generators import (
    GeneratorParams, BassGenerator, FingerpickingGenerator, 
    MelodyGenerator, ChordGenerator, ArpeggiatorGenerator,
    OstinatoGenerator, StrumPatternGenerator, PianoRunGenerator,
    MarkovMelodyGenerator, DyadGenerator
)
from melodica.rhythm import SchillingerGenerator

def generate_all():
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    key = Scale(root=0, mode=Mode.MAJOR) # C Major
    # Fixed chord progression for all: C - G - Am - F
    chords = [
        FunctionalEngine().harmonize(HarmonizationRequest([Note(60, 0, 4)], key, chord_rhythm=4.0))[0],
        FunctionalEngine().harmonize(HarmonizationRequest([Note(55, 4, 4)], key, chord_rhythm=4.0))[0],
        FunctionalEngine().harmonize(HarmonizationRequest([Note(57, 8, 4)], key, chord_rhythm=4.0))[0],
        FunctionalEngine().harmonize(HarmonizationRequest([Note(53, 12, 4)], key, chord_rhythm=4.0))[0],
    ]
    # Manually fix durations for safety
    for i, c in enumerate(chords):
        c.start = i * 4.0
        c.duration = 4.0

    generators = [
        ("bass", BassGenerator(style="root_fifth")),
        ("fingerpicking", FingerpickingGenerator(pattern=[0, 2, 1, 3])),
        ("melody", MelodyGenerator(params=GeneratorParams(density=0.8))),
        ("chords", ChordGenerator()),
        ("arpeggio", ArpeggiatorGenerator(pattern="up_down", octaves=2)),
        ("ostinato", OstinatoGenerator(shape=[0, 1, 2, 1])),
        ("strum", StrumPatternGenerator(strum_delay=0.03, direction_pattern=[1, -1])),
        ("piano_run", PianoRunGenerator(notes_per_run=16)),
        ("markov", MarkovMelodyGenerator()),
        ("dyads", DyadGenerator(interval_pref=[3, 4, 7])),
        ("schillinger_rhythm", ChordGenerator(rhythm=SchillingerGenerator(3, 4)))
    ]

    for name, gen in generators:
        print(f"Generating {name}...")
        notes = gen.render(chords, key, 16.0)
        
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        events = []
        for n in notes:
            on_tick = round(n.start * 480)
            off_tick = round((n.start + n.duration) * 480)
            events.append((on_tick, "note_on", n.pitch, n.velocity))
            events.append((off_tick, "note_off", n.pitch, 0))
            
        events.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))
        
        prev_tick = 0
        for tick, msg_type, pitch, vel in events:
            track.append(mido.Message(msg_type, note=pitch, velocity=vel, time=tick - prev_tick))
            prev_tick = tick
            
        mid.save(out_dir / f"test_{name}.mid")

    print(f"✨ DONE! Check {out_dir.absolute()} for all results.")

if __name__ == "__main__":
    generate_all()
