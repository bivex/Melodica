# Copyright (c) 2026 Bivex
# Album: OVERLOAD (Перегруз)
# Style: Industrial Techno / Dark Synthwave / Technical Neoclassical

import os
import random
from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

def apply_overload_mastering(raw_tracks, bpm, lufs=-7.0):
    """Extreme loudness with transient preservation."""
    desk = MixingDesk(niche_cfg={})
    # Surgical precision gains
    desk.track_gains.update({
        "kick": 1.2, 
        "bass": 1.1, 
        "lead": 0.9, 
        "strings": 0.8, 
        "perc": 0.7,
        "arp": 0.85,
        "hits": 1.1,
        "glitch_perc": 0.75,
        "sub": 1.2,
        "top": 0.6,
        "poly3": 0.9,
        "poly4": 1.0,
        "sharp_lead": 0.95
    })
    master = MasteringDesk(target_lufs=lufs)
    mixed = desk.apply_mixing(raw_tracks, [("Dynamics", 800, [])], int(bpm))
    mastered, pan = master.apply_mastering(mixed)
    return mastered, pan

def produce_t1_protocol_ramp():
    """I. Разгон протокола. BPM 138 -> 150.
    Mechanical arpeggio, driving force.
    """
    print("Executing I. Protocol Ramp...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR) # D Minor
    
    # Mechanical Arp (16th notes)
    arp = []
    pitches = [50, 53, 57, 62] # D, F, A, D
    for i in range(256): # 64 beats
        arp.append(types.NoteInfo(pitch=pitches[i % 4], start=i*0.25, duration=0.2, velocity=min(127, 90 + (i//10))))
        
    # Syncopated Kick
    kick = [types.NoteInfo(pitch=36, start=i*1.0 + (0.375 if i%2 else 0), duration=0.1, velocity=110) for i in range(64)]
    
    return {"arp": arp, "kick": kick}, 144.0 # Avg BPM for export

def produce_t2_blind_speed():
    """II. Слепая скорость. BPM 160.
    7/8 polyrhythms, virtuoso lead.
    """
    print("Executing II. Blind Speed...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    
    # Virtuoso Lead (Fast Legato)
    gen = LeadSynthGenerator(GeneratorParams(density=0.9, complexity=0.9))
    chords = []
    for i, s in enumerate(["i", "VI", "iv", "V"] * 4):
        chord = key.parse_roman(s)
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
    
    lead_notes = gen.render(chords, key, 64.0)
    
    # 7/8 Bass Pulse
    bass = []
    for i in range(64):
        start = (i // 7) * 3.5 + (i % 7) * 0.5
        bass.append(types.NoteInfo(pitch=38, start=start, duration=0.4, velocity=105))
        
    return {"lead": lead_notes, "bass": bass}, 160.0

def produce_t3_contact():
    """III. Контакт. BPM 175.
    Industrial hits, maximum density.
    """
    print("Executing III. Contact...")
    key = types.Scale(root=2, mode=types.Mode.PHRYGIAN) # Darker
    
    # Industrial Hits (Unison strings/synts)
    hits = []
    for i in range(128):
        if i % 4 == 0 or i % 16 in [6, 10]:
            hits.append(types.NoteInfo(pitch=38, start=i*0.25, duration=0.1, velocity=120))
            hits.append(types.NoteInfo(pitch=50, start=i*0.25, duration=0.1, velocity=110))
            
    # Glitchy percussion
    drums = TrapDrumsGenerator(GeneratorParams(density=0.8))
    perc = drums.render([], key, 32.0)
    
    return {"hits": hits, "glitch_perc": perc}, 175.0

def produce_t4_tactical_darkness():
    """IV. Тактическая тьма. BPM 140.
    Sub-weight, silence contrast.
    """
    print("Executing IV. Tactical Darkness...")
    # Massive groove
    sub = [types.NoteInfo(pitch=26, start=i*2.0, duration=1.8, velocity=80) for i in range(32)]
    high_perc = [types.NoteInfo(pitch=82, start=i*0.5 + 0.25, duration=0.05, velocity=60) for i in range(128)]
    
    return {"sub": sub, "top": high_perc}, 140.0

def produce_t5_last_impulse():
    """V. Последний импульс. BPM 180.
    3 vs 4 polyrhythm, surgical lead.
    """
    print("Executing V. Last Impulse...")
    key = types.Scale(root=2, mode=types.Mode.NATURAL_MINOR)
    
    # 3 vs 4 Polyrhythm
    poly_3 = [types.NoteInfo(pitch=62, start=i*0.75, duration=0.2, velocity=100) for i in range(64)] # 3-feel
    poly_4 = [types.NoteInfo(pitch=38, start=i*0.5, duration=0.2, velocity=110) for i in range(96)]  # 4-feel
    
    # Sharp Lead
    gen = MelodyGenerator(GeneratorParams(density=0.95), drama_shape="dramatic")
    chords = []
    for i in range(8):
        chord = key.parse_roman("i")
        chord.start = i * 4
        chord.duration = 4
        chords.append(chord)
        
    lead = gen.render(chords, key, 32.0)
    
    return {"poly3": poly_3, "poly4": poly_4, "sharp_lead": lead}, 180.0

def main():
    album_dir = Path("output/overload")
    album_dir.mkdir(exist_ok=True, parents=True)
    
    print("\n" + "X"*60)
    print("   ALBUM PRODUCTION: OVERLOAD [SYSTEM ACTIVE]")
    print("X"*60 + "\n")
    
    tracks_cfg = [
        ("01_Protocol_Ramp", produce_t1_protocol_ramp, -10.0),
        ("02_Blind_Speed", produce_t2_blind_speed, -8.0),
        ("03_Contact", produce_t3_contact, -6.5), # Extreme
        ("04_Tactical_Darkness", produce_t4_tactical_darkness, -12.0),
        ("05_Last_Impulse", produce_t5_last_impulse, -7.0)
    ]
    
    for name, producer, lufs in tracks_cfg:
        raw, bpm = producer()
        mastered, pan = apply_overload_mastering(raw, bpm, lufs=lufs)
        export_multitrack_midi(mastered, str(album_dir / f"{name}.mid"), bpm=bpm, cc_events=pan)
        
    print("\n" + "="*60)
    print(f"   SYSTEM OVERLOAD COMPLETE. Location: {album_dir}")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
