# Copyright (c) 2026 Bivex
# Album: APOCALYPSE PROTOCOL [MASSIVE: ULTIMATE EDITION]
# Style: Cybernetic Orchestral / Extreme Industrial / Technical Metal-Synth Hybrid

import os
import random
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams, MelodicIntelligenceConfig, MelodyGenerator
from melodica.generators.staccato import StringsStaccatoGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.combat_escalation import CombatEscalationGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def get_ultimate_intel():
    """Ultimate intelligence settings for extreme musicality and aggression."""
    return MelodicIntelligenceConfig(
        enable_interval_weights=True,
        enable_leading_tone_resolution=True,
        tonal_gravity_strength=1.0,
        chord_tone_bias=1.2,
        enable_rhythmic_phrasing=True,
        enable_micro_groove=True,
        tension_subdivision_boost=1.0,  # Max speed bursts
        time_humanization=0.015,
        velocity_humanization=0.2
    )

def apply_ultimate_mastering(raw_tracks, bpm, lufs=-5.5):
    """Surgical loudness with extreme weight."""
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "war_drums": 1.4, 
        "sub_bass": 1.4, 
        "lead_main": 1.0, 
        "lead_octave": 0.75, 
        "brass_power": 1.2, 
        "brass_low": 1.0,
        "texture_fill": 0.6, 
        "stabs_high": 1.1,
        "stabs_low": 0.9,
        "cyber_arp": 0.8
    })
    master = MasteringDesk(target_lufs=lufs)
    mixed = desk.apply_mixing(raw_tracks, [("Dynamics", 1800, [])], int(bpm))
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan

def produce_ultimate_siege():
    print("Forging I. Siege Engine [Ultimate]...")
    key = types.Scale(root=2, mode=types.Mode.PHRYGIAN)
    duration = 128.0
    intel = get_ultimate_intel()
    
    # 1. War Drums (Combat Evolution)
    drums_gen = CombatEscalationGenerator(GeneratorParams(density=0.9, intel=intel))
    drums = drums_gen.render([], key, duration)
    
    # 2. Orchestral Wall (Triple Layering)
    stabs_gen = StringsStaccatoGenerator(GeneratorParams(density=0.6, complexity=0.8, intel=intel))
    chords = []
    for i in range(32):
        chord = key.parse_roman("i" if i % 8 < 6 else "bII")
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
    
    stabs_main = stabs_gen.render(chords, key, duration)
    stabs_low = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration, velocity=int(n.velocity*0.85)) for n in stabs_main]
    stabs_sub = [types.NoteInfo(pitch=n.pitch-24, start=n.start, duration=n.duration, velocity=int(n.velocity*0.7)) for n in stabs_main]
    
    # 3. Ambient Texture
    texture = [types.NoteInfo(pitch=random.choice([26, 31, 38]), start=i*8, duration=8.1, velocity=50) for i in range(16)]
    
    raw = {
        "war_drums": drums, 
        "stabs_high": stabs_main, 
        "stabs_low": stabs_low, 
        "sub_bass": stabs_sub,
        "texture_fill": texture
    }
    return raw, 145.0

def produce_ultimate_fracture():
    print("Forging II. Neural Fracture [Ultimate]...")
    key = types.Scale(root=2, mode=types.Mode.LOCRIAN)
    duration = 96.0
    intel = get_ultimate_intel()
    
    # 1. Virtuoso Lead (Double Layer + Integrated Intelligence)
    gen = MelodyGenerator(
        GeneratorParams(density=0.95, complexity=1.0, intel=intel),
        drama_shape="dramatic",
        ornament_probability=0.7
    )
    chords = []
    for i in range(24):
        chord = key.parse_roman("i" if i % 4 != 3 else "v")
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
    
    lead_main = gen.render(chords, key, duration)
    lead_oct = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration, velocity=int(n.velocity*0.75)) for n in lead_main]
    
    # 2. Cyber Arp
    arp = [types.NoteInfo(pitch=74 + (i%12), start=i*0.25, duration=0.1, velocity=85) for i in range(int(duration*4))]
    
    raw = {"lead_main": lead_main, "lead_octave": lead_oct, "cyber_arp": arp}
    return raw, 195.0

def produce_ultimate_redline():
    print("Forging III. Red Line [Ultimate]...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    duration = 160.0
    intel = get_ultimate_intel()
    
    # Extreme speed + Combat escalation
    combat_gen = CombatEscalationGenerator(GeneratorParams(density=1.0, intel=intel))
    drums = combat_gen.render([], key, duration)
    
    # Screaming Brass Wall
    brass_gen = MelodyGenerator(
        GeneratorParams(density=0.8, complexity=0.6, intel=intel),
        note_range_low=60, note_range_high=84
    )
    chords = [key.parse_roman("i")] * 40
    for i, c in enumerate(chords): c.start = i*4; c.duration = 4
    brass = brass_gen.render(chords, key, duration)
    brass_low = [types.NoteInfo(pitch=n.pitch-12, start=n.start, duration=n.duration, velocity=int(n.velocity*0.9)) for n in brass]
    
    sub = [types.NoteInfo(pitch=26, start=i*0.5, duration=0.45, velocity=115) for i in range(int(duration*2))]
    
    raw = {"war_drums": drums, "brass_power": brass, "brass_low": brass_low, "sub_bass": sub}
    return raw, 220.0 # BEYOND EXTREME

def main():
    album_dir = Path("output/apocalypse_ultimate")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "!"*60)
    print("   ALBUM PRODUCTION: APOCALYPSE PROTOCOL [ULTIMATE EDITION]")
    print("   FEATURING CENTRALIZED MUSICAL INTELLIGENCE V2")
    print("!"*60 + "\n")
    
    # 01. Siege Engine
    raw1, bpm1 = produce_ultimate_siege()
    m1, p1 = apply_ultimate_mastering(raw1, bpm1, lufs=-6.5)
    export_multitrack_midi(m1, str(album_dir / "01_Siege_Ultimate.mid"), bpm=bpm1, cc_events=p1)
    
    # 02. Neural Fracture
    raw2, bpm2 = produce_ultimate_fracture()
    m2, p2 = apply_ultimate_mastering(raw2, bpm2, lufs=-5.5)
    export_multitrack_midi(m2, str(album_dir / "02_Fracture_Ultimate.mid"), bpm=bpm2, cc_events=p2)
    
    # 03. Red Line
    raw3, bpm3 = produce_ultimate_redline()
    m3, p3 = apply_ultimate_mastering(raw3, bpm3, lufs=-5.0) # THE LIMIT
    export_multitrack_midi(m3, str(album_dir / "03_RedLine_Ultimate.mid"), bpm=bpm3, cc_events=p3)

    print(f"\n   ULTIMATE PRODUCTION COMPLETE. Location: {album_dir}\n")

if __name__ == "__main__":
    main()
