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
demo_voice_leading.py — Showcasing horizontal voice leading.
Compare jumping chords vs smoothed chord transitions.
"""

from pathlib import Path
import mido

from melodica.engines.functional import FunctionalEngine
from melodica.types import Note, HarmonizationRequest, Scale, Mode, PhraseInstance
from melodica.generators import ChordGenerator
from melodica.modifiers import VoiceLeadingModifier, ModifierContext

def run_demo():
    print("🚂 Melodica Voice Leading Demo")
    
    key = Scale(root=0, mode=Mode.MAJOR) # C Major
    # Big jumps: C -> G -> Am -> F
    chords = [
        FunctionalEngine().harmonize(HarmonizationRequest([Note(60, 0, 4)], key, chord_rhythm=4.0))[0],
        FunctionalEngine().harmonize(HarmonizationRequest([Note(79, 4, 4)], key, chord_rhythm=4.0))[0], # G high
        FunctionalEngine().harmonize(HarmonizationRequest([Note(45, 8, 4)], key, chord_rhythm=4.0))[0], # Am low
        FunctionalEngine().harmonize(HarmonizationRequest([Note(77, 12, 4)], key, chord_rhythm=4.0))[0],# F high
    ]
    for i, c in enumerate(chords):
        c.start = i * 4.0
        c.duration = 4.0

    gen = ChordGenerator(voicing="closed")
    
    # 1. Track WITHOUT Voice Leading (will jump wildly)
    phrase_jumpy = PhraseInstance(generator=gen)
    notes_jumpy = phrase_jumpy.render(chords, key)
    
    # 2. Track WITH Voice Leading (will stay in a comfortable center)
    phrase_smooth = PhraseInstance(
        generator=gen,
        modifiers=[VoiceLeadingModifier(target_octave=5)] # Anchor around C5
    )
    notes_smooth = phrase_smooth.render(chords, key)

    # Export
    out_dir = Path("output")
    out_dir.mkdir(parents=True, exist_ok=True)
    
    def save_notes(name, notes):
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)
        events = []
        for n in notes:
            events.append((round(n.start * 480), "note_on", n.pitch, n.velocity))
            events.append((round((n.start + n.duration) * 480), "note_off", n.pitch, 0))
        events.sort(key=lambda x: (x[0], 0 if x[1] == "note_off" else 1))
        p_t = 0
        for t, m, p, v in events:
            track.append(mido.Message(m, note=int(p), velocity=int(v), time=int(t-p_t)))
            p_t = t
        mid.save(out_dir / f"demo_vl_{name}.mid")

    save_notes("jumpy", notes_jumpy)
    save_notes("smooth", notes_smooth)
    print(f"✅ Saved jumpy vs smooth files to {out_dir}/")

if __name__ == "__main__":
    run_demo()
