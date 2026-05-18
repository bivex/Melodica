# Copyright (c) 2026 Bivex
# Album: APOCALYPSE PROTOCOL [MASSIVE EDITION]
# Style: Cybernetic Orchestral / Extreme Industrial / Technical Metal-Synth Hybrid

import os
import random
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.staccato import StringsStaccatoGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def humanize_track(notes):
    """Adds micro-offsets and velocity variations for 'live' feel."""
    for n in notes:
        n.start += random.uniform(-0.015, 0.015)
        n.velocity = int(n.velocity * random.uniform(0.85, 1.15))
        n.velocity = max(1, min(127, n.velocity))
    return notes

def create_cc_breathing(duration_beats):
    """Creates CC11 (Expression) automation for 'breathing' sound."""
    events = []
    for i in range(int(duration_beats * 2)): # Every 0.5 beats
        val = 80 + int(30 * (1 + random.uniform(-0.2, 0.2)))
        events.append((i * 0.5, 11, val))
    return events

def apply_massive_mastering(raw_tracks, bpm, lufs=-6.0):
    desk = MixingDesk(niche_cfg={})
    # Balanced gains for multiple layers
    desk.track_gains.update({
        "war_drums": 1.2, 
        "sub_bass": 1.3, 
        "lead_main": 1.0, 
        "lead_octave": 0.7, 
        "brass_main": 1.1, 
        "brass_low": 0.9,
        "texture": 0.5, 
        "stabs": 1.0,
        "stabs_low": 0.8,
        "cyber_arp": 0.7
    })
    master = MasteringDesk(target_lufs=lufs)
    mixed = desk.apply_mixing(raw_tracks, [("Dynamics", 1500, [])], int(bpm))
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan

def produce_massive_siege():
    print("Forging Massive Siege Engine...")
    key = types.Scale(root=2, mode=types.Mode.PHRYGIAN)
    duration = 128.0
    
    # 1. Drums + Humanization
    drums_gen = TrapDrumsGenerator(GeneratorParams(density=0.9))
    drums = drums_gen.render([], key, duration)
    drums = humanize_track(drums)
    
    # 2. Orchestral Wall (Main + Low Layering)
    stabs_gen = StringsStaccatoGenerator(GeneratorParams(density=0.6, complexity=0.7))
    chords = []
    for i in range(32):
        chord = key.parse_roman("i" if i % 4 != 3 else "bII")
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
    
    stabs_main = humanize_track(stabs_gen.render(chords, key, duration))
    stabs_low = [types.NoteInfo(pitch=n.pitch-12, start=n.start+0.005, duration=n.duration, velocity=int(n.velocity*0.8)) for n in stabs_main]
    
    # 3. Ambient Texture (spectral filler)
    texture = [types.NoteInfo(pitch=random.choice([38, 41, 45]), start=i*8, duration=8.1, velocity=40) for i in range(16)]
    
    raw = {"war_drums": drums, "stabs": stabs_main, "stabs_low": stabs_low, "texture": texture}
    cc = {"stabs": create_cc_breathing(duration), "stabs_low": create_cc_breathing(duration)}
    
    return raw, 140.0, cc

def produce_massive_fracture():
    print("Forging Massive Neural Fracture...")
    key = types.Scale(root=2, mode=types.Mode.LOCRIAN)
    duration = 96.0
    
    # 1. Virtuoso Shred (Double Layer + Humanization)
    gen = MelodyGenerator(GeneratorParams(density=0.98, complexity=1.0), ornament_probability=0.9)
    chords = []
    for i in range(24):
        chord = key.parse_roman("i" if i % 2 == 0 else "v")
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
    
    lead_main = humanize_track(gen.render(chords, key, duration))
    lead_oct = [types.NoteInfo(pitch=n.pitch-12, start=n.start+0.01, duration=n.duration, velocity=int(n.velocity*0.7)) for n in lead_main]
    
    # 2. Arp with expression
    arp = [types.NoteInfo(pitch=74 + (i%12), start=i*0.25, duration=0.1, velocity=80) for i in range(int(duration*4))]
    
    raw = {"lead_main": lead_main, "lead_octave": lead_oct, "cyber_arp": arp}
    cc = {"lead_main": create_cc_breathing(duration), "lead_octave": create_cc_breathing(duration)}
    
    return raw, 190.0, cc

def main():
    album_dir = Path("output/apocalypse_massive")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "W"*60)
    print("   ALBUM PRODUCTION: APOCALYPSE PROTOCOL [MASSIVE EDITION]")
    print("W"*60 + "\n")
    
    # Track 1
    raw1, bpm1, cc1 = produce_massive_siege()
    m1, p1 = apply_massive_mastering(raw1, bpm1, lufs=-7.0)
    # Merge CC with master's pan/automation
    for track_name in m1:
        if track_name in cc1:
            p1[track_name] = p1.get(track_name, []) + cc1[track_name]
    export_multitrack_midi(m1, str(album_dir / "01_Siege_Massive.mid"), bpm=bpm1, cc_events=p1)
    
    # Track 2
    raw2, bpm2, cc2 = produce_massive_fracture()
    m2, p2 = apply_massive_mastering(raw2, bpm2, lufs=-6.0)
    for track_name in m2:
        if track_name in cc2:
            p2[track_name] = p2.get(track_name, []) + cc2[track_name]
    export_multitrack_midi(m2, str(album_dir / "02_Fracture_Massive.mid"), bpm=bpm2, cc_events=p2)

    print(f"\n   MASSIVE PRODUCTION COMPLETE. Location: {album_dir}\n")

if __name__ == "__main__":
    main()
