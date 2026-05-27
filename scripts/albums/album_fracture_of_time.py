# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_fracture_of_time.py — THE FRACTURE OF TIME

Concept: Progressive Rock / Jazz Fusion / Symphonic Prog.
A journey of a mind losing the sensation of linear time.
Scales: Hungarian Minor, Lydian Dominant, Polymodal shifts.

Tracks:
  I.   CLOCKWORK VEINS (132 BPM) - 7/8 -> 11/8 -> 4/4
  II.  GLASS CONSTELLATIONS (76 BPM) - Freless Bass, Sax, Fusion
  III. THE CITY BREATHES STATIC (148 BPM) - Djent, 13/8
  IV.  MIRRORS OF THE DEAD SUN (58 BPM) - Organ, Choir, Crescendo
  V.   PARALLEL HEARTS (92 BPM) - 9/8 -> 4/4, Melodic Prog
  VI.  THE FRACTURE OF TIME (120 BPM avg) - 18-minute Epic
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# Keys
KEY_HM = types.Scale(root=4, mode=types.Mode.HUNGARIAN_MINOR)   # E Hungarian Minor
KEY_LD = types.Scale(root=2, mode=types.Mode.LYDIAN_DOMINANT)   # D Lydian Dominant

# Instruments
PIANO = 0
RHODES = 4
MELLOTRON = 49       # String Ensemble 1
PIPE_ORGAN = 19
CLEAN_GUITAR = 27
DIST_GUITAR = 30
FRETLESS_BASS = 35
PICK_BASS = 34
MOOG_LEAD = 81
SAW_LEAD = 80
ALTO_SAX = 65
CHOIR = 52
VOICE_FEMALE = 53
DRUMS_KICK = 36
DRUMS_SNARE = 38
DRUMS_HAT = 42

random.seed(2112) # Prog seed
OUT = Path("output/album_fracture")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -11.0):
    desk = MixingDesk(niche_cfg={})
    # Prog rock mastering - dense, punchy
    desk.track_gains.update({
        "guitar": 0.85, "lead": 0.9, "bass": 0.9, "drums": 1.0,
        "organ": 0.75, "choir": 0.65, "sax": 0.85, "rhodes": 0.7,
        "piano": 0.8, "strings": 0.65, "clean_gtr": 0.75
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, key: types.Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. CLOCKWORK VEINS — 132 BPM
# 7/8 -> 11/8 -> 4/4
# =====================================================================
def produce_clockwork_veins():
    print("--- 01_Clockwork_Veins ---")
    bpm = 132
    
    # Timeline
    S_INTRO = 0.0      # 7/8 (bpc 3.5), 16 bars = 56 beats
    S_MAIN = 56.0      # 11/8 (bpc 5.5), 16 bars = 88 beats
    S_VERSE = 144.0    # 11/8, 16 bars = 88 beats
    S_CHORUS = 232.0   # 4/4 (bpc 4.0), 16 bars = 64 beats
    S_POLY = 296.0     # The 3:20 mark. Polymeter section. 32 bars of 4/4 = 128 beats
    S_OUTRO = 424.0    # 4/4, 32 beats
    DUR = 456.0

    c_intro = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*3.5), duration=3.5) for i in range(16)]
    c_main = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*5.5), duration=5.5) for i in range(16)]
    c_verse = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*5.5), duration=5.5) for i in range(16)]
    c_chorus = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=float(i*4.0), duration=4.0) for i in range(16)]

    # Intro (7/8)
    synth_seq = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(80, 100)),
        pattern="random", note_duration=0.25
    ).render(c_intro, KEY_HM, 56.0)
    
    clean_tap = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, key_range_low=64, key_range_high=88, velocity_range=(90, 115)),
        pattern="up_down", note_duration=0.125
    ).render(c_intro[8:], KEY_HM, 28.0) # Enters at bar 8 (beat 28)

    # Main Riff (11/8) - Unison Moog + Guitar
    main_riff = MelodyGenerator(
        GeneratorParams(density=0.6, complexity=0.8, velocity_range=(100, 127)),
        phrase_length=5.5, note_range_low=40, note_range_high=64, syncopation=0.5
    ).render(c_main, KEY_HM, 88.0)

    # Verse (11/8)
    vox_verse = MelodyGenerator(
        GeneratorParams(density=0.2, complexity=0.2, velocity_range=(50, 70)),
        phrase_length=11.0, note_range_low=52, note_range_high=64
    ).render(c_verse, KEY_HM, 88.0)
    
    # Ghost notes drums in verse
    drums_verse = []
    for i in range(16):
        t = i * 5.5
        drums_verse.append(types.NoteInfo(DRUMS_KICK, t, 0.5, 90))
        drums_verse.append(types.NoteInfo(DRUMS_SNARE, t+2.5, 0.2, 40)) # Ghost
        drums_verse.append(types.NoteInfo(DRUMS_SNARE, t+3.5, 0.2, 100))

    # Chorus (4/4)
    chorus_choir = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(80, 110)), pattern="chord", note_duration=1.0
    ).render(c_chorus, KEY_HM, 64.0)
    chorus_mellotron = StringsEnsembleGenerator(GeneratorParams(density=0.3)).render(c_chorus, KEY_HM, 64.0)
    
    # Polymeter Section at 3:20 (S_POLY)
    # Drums in 5 (1.25 beats), Bass in 7 (1.75 beats), Guitar in 4 (1.0 beats)
    poly_drums = []
    poly_bass = []
    poly_guitar = []
    
    for beat in range(128): # 128 beats total
        # Guitar every beat (4/4 feel)
        poly_guitar.append(types.NoteInfo(pitch=40, start=float(beat), duration=0.5, velocity=110))
        poly_guitar.append(types.NoteInfo(pitch=47, start=float(beat), duration=0.5, velocity=110))
    
    t_d = 0.0
    while t_d < 128.0:
        poly_drums.append(types.NoteInfo(DRUMS_KICK, t_d, 0.5, 115))
        poly_drums.append(types.NoteInfo(DRUMS_HAT, t_d+0.5, 0.2, 90))
        t_d += 1.25 # 5/16 feel
        
    t_b = 0.0
    bass_notes = [40, 42, 43, 46, 47, 43, 42]
    b_idx = 0
    while t_b < 128.0:
        poly_bass.append(types.NoteInfo(pitch=bass_notes[b_idx%7], start=t_b, duration=0.8, velocity=110))
        t_b += 1.75 # 7/16 feel
        b_idx += 1

    tracks = {
        "lead": synth_seq + _off(main_riff, S_MAIN),
        "guitar": _off(clean_tap, 28.0) + _off(main_riff, S_MAIN) + _off(poly_guitar, S_POLY),
        "vox": _off(vox_verse, S_VERSE),
        "drums": _off(drums_verse, S_VERSE) + _off(poly_drums, S_POLY),
        "choir": _off(chorus_choir, S_CHORUS),
        "strings": _off(chorus_mellotron, S_CHORUS),
        "bass": _off(poly_bass, S_POLY)
    }
    inst = {
        "lead": MOOG_LEAD, "guitar": DIST_GUITAR, "vox": VOICE_FEMALE,
        "drums": DRUMS_KICK, "choir": CHOIR, "strings": MELLOTRON, "bass": PICK_BASS
    }
    _export(tracks, OUT / "01_Clockwork_Veins.mid", bpm, KEY_HM, inst)

# =====================================================================
# II. GLASS CONSTELLATIONS — 76 BPM
# Lydian Dominant Fusion
# =====================================================================
def produce_glass_constellations():
    print("--- 02_Glass_Constellations ---")
    bpm = 76
    dur = 760.0 # ~10 mins
    
    # We'll generate it as one massive block, but varying the density
    chords = [types.ChordLabel(root=2, quality=types.Quality.DOMINANT7, start=float(i*4), duration=4.0) for i in range(int(dur/4))]

    # Rhodes Piano - Jazzy chords
    rhodes = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, key_range_low=48, key_range_high=72, velocity_range=(50, 75)),
        pattern="random", note_duration=1.0
    ).render(chords, KEY_LD, dur)

    # Fretless Bass Lead (very expressive, lots of ornaments for slides)
    bass = MelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.6, velocity_range=(60, 90)),
        phrase_length=16.0, note_range_low=36, note_range_high=60,
        ornament_probability=0.5, harmony_note_probability=0.4
    ).render(chords, KEY_LD, dur)

    # Volume Swells Guitar
    guitar = DroneGenerator(
        GeneratorParams(density=0.05, key_range_low=60, key_range_high=84),
        velocity=45
    ).render(chords, KEY_LD, dur)

    # Saxophone Solo (Middle 7 mins: beat 152 to 684)
    sax_dur = 684.0 - 152.0
    sax = MelodyGenerator(
        GeneratorParams(density=0.6, complexity=0.9, velocity_range=(70, 115)),
        phrase_length=8.0, note_range_low=62, note_range_high=86,
        ornament_probability=0.7, steps_probability=0.4
    ).render(chords[38:171], KEY_LD, sax_dur)

    tracks = {
        "rhodes": rhodes, "bass": bass, "clean_gtr": guitar, "sax": _off(sax, 152.0)
    }
    inst = {"rhodes": RHODES, "bass": FRETLESS_BASS, "clean_gtr": CLEAN_GUITAR, "sax": ALTO_SAX}
    _export(tracks, OUT / "02_Glass_Constellations.mid", bpm, KEY_LD, inst)

# =====================================================================
# III. THE CITY BREATHES STATIC — 148 BPM
# 13/8 (4+4+5) -> Ambient Bridge -> Double Tempo
# =====================================================================
def produce_city_static():
    print("--- 03_City_Breathes_Static ---")
    bpm = 148
    bpc = 6.5 # 13/8
    dur = 888.0 # ~6 mins
    
    # 0 to 400: Djent
    # 400 to 600: Ambient Bridge
    # 600 to 888: Double Tempo Return
    
    chords_djent = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(400/bpc))]

    # Djent Guitar - low, rhythmic, repetitive
    guitar_djent = []
    for i in range(int(400/bpc)):
        t = i * bpc
        # 4 + 4 + 5 pattern
        for offset in [0, 0.5, 2.0, 2.5, 4.0, 4.5, 5.5, 6.0]:
            guitar_djent.append(types.NoteInfo(pitch=28, start=t+offset, duration=0.2, velocity=120))

    # Aggressive Synth Arp
    synth_arp = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, key_range_low=64, key_range_high=88, velocity_range=(90, 110)),
        pattern="up_down_full", note_duration=0.25
    ).render(chords_djent, KEY_HM, 400.0)

    # Ambient Bridge (400 to 600)
    chords_amb = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0.0, duration=200.0)]
    piano = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(30, 50)),
        phrase_length=16.0, note_range_low=60, note_range_high=84
    ).render(chords_amb, KEY_HM, 200.0)
    
    noise = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=90, key_range_high=91), velocity=20
    ).render(chords_amb, KEY_HM, 200.0)

    # Double Tempo Return (600 to 888) - 13/8 but played twice as fast
    chords_fast = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*3.25), duration=3.25) for i in range(int(288/3.25))]
    synth_fast = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=52, key_range_high=88, velocity_range=(100, 127)),
        pattern="up_down", note_duration=0.125
    ).render(chords_fast, KEY_HM, 288.0)

    guitar_fast = []
    for i in range(int(288/3.25)):
        t = i * 3.25
        # Fast 4+4+5 squeezed into 3.25 beats (13/16)
        for offset in [0, 0.25, 1.0, 1.25, 2.0, 2.25, 2.75, 3.0]:
            guitar_fast.append(types.NoteInfo(pitch=28, start=t+offset, duration=0.1, velocity=127))

    tracks = {
        "guitar": guitar_djent + _off(guitar_fast, 600.0),
        "lead": synth_arp + _off(synth_fast, 600.0),
        "piano": _off(piano, 400.0),
        "fx": _off(noise, 400.0)
    }
    inst = {"guitar": DIST_GUITAR, "lead": SAW_LEAD, "piano": PIANO, "fx": 89}
    _export(tracks, OUT / "03_City_Static.mid", bpm, KEY_HM, inst)

# =====================================================================
# IV. MIRRORS OF THE DEAD SUN — 58 BPM
# =====================================================================
def produce_mirrors():
    print("--- 04_Mirrors_of_Dead_Sun ---")
    bpm = 58
    dur = 350.0 # ~6 mins
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(int(dur/4))]

    # Pipe Organ
    organ = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, key_range_low=24, key_range_high=60, velocity_range=(60, 90)),
        pattern="chord", note_duration=2.0
    ).render(chords, KEY_HM, dur)

    # Huge Choir (Singing in Byzantine/Double Harmonic - simulating polymodality by shifting the key object)
    KEY_BYZ = types.Scale(root=4, mode=types.Mode.DOUBLE_HARMONIC)
    choir = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, key_range_low=48, key_range_high=84, velocity_range=(70, 100)),
        pattern="power", note_duration=1.0
    ).render(chords, KEY_BYZ, dur)

    # Massive Crescendo at 5:40 (beat 328)
    orchestra_cresc = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=36, key_range_high=96, velocity_range=(100, 127)),
        pattern="converge", note_duration=0.25
    ).render(chords[-6:], KEY_HM, 24.0)

    # Female Voice alone at the end
    vox = [types.NoteInfo(pitch=64, start=330.0, duration=20.0, velocity=70)]

    tracks = {"organ": organ, "choir": choir + _off(orchestra_cresc, 328.0), "vox": vox}
    inst = {"organ": PIPE_ORGAN, "choir": CHOIR, "vox": VOICE_FEMALE}
    _export(tracks, OUT / "04_Mirrors.mid", bpm, KEY_HM, inst)

# =====================================================================
# V. PARALLEL HEARTS — 92 BPM
# =====================================================================
def produce_parallel_hearts():
    print("--- 05_Parallel_Hearts ---")
    bpm = 92
    dur = 460.0 # ~5 mins
    
    # 9/8 verses (bpc=4.5), 4/4 choruses (bpc=4.0)
    # Let's just alternate chunks
    t = 0.0
    chords = []
    while t < dur:
        if (t // 36) % 2 == 0:
            chords.append(types.ChordLabel(root=4, quality=types.Quality.MINOR, start=t, duration=4.5))
            t += 4.5
        else:
            chords.append(types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=t, duration=4.0))
            t += 4.0

    # Clean Guitar Delay (Arp)
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(60, 85)),
        pattern="up_down", note_duration=0.5
    ).render(chords, KEY_HM, dur)

    # Live Strings
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.15, velocity_range=(50, 70))
    ).render(chords, KEY_HM, dur)

    # Solo Modulating across 5 modes (Middle section beat 200 to 300)
    solo_notes = []
    solo_dur = 20.0
    modes = [types.Mode.HUNGARIAN_MINOR, types.Mode.LYDIAN, types.Mode.DORIAN, types.Mode.PHRYGIAN_DOMINANT, types.Mode.HUNGARIAN_MINOR]
    for i, mode in enumerate(modes):
        k = types.Scale(root=4, mode=mode)
        c = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=solo_dur)]
        s = MelodyGenerator(
            GeneratorParams(density=0.7, complexity=0.8, velocity_range=(85, 110)),
            phrase_length=4.0, note_range_low=64, note_range_high=88
        ).render(c, k, solo_dur)
        solo_notes.extend(_off(s, 200.0 + i*solo_dur))

    tracks = {"clean_gtr": guitar, "strings": strings, "lead": solo_notes}
    inst = {"clean_gtr": CLEAN_GUITAR, "strings": MELLOTRON, "lead": DIST_GUITAR}
    _export(tracks, OUT / "05_Parallel_Hearts.mid", bpm, KEY_HM, inst)

# =====================================================================
# VI. THE FRACTURE OF TIME — 120 BPM
# 18 Minutes = 2160 Beats
# =====================================================================
def produce_fracture_of_time():
    print("--- 06_Fracture_of_Time ---")
    bpm = 120
    dur = 2160.0
    
    # Part I - Collapse (0 to 500)
    c_p1 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(125)]
    p1_heavy = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, velocity_range=(100, 127)), pattern="power", note_duration=0.25
    ).render(c_p1, KEY_HM, 500.0)
    p1_choir = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(90, 115)), pattern="chord", note_duration=1.0
    ).render(c_p1, KEY_HM, 500.0)

    # Part II - Silence Between Seconds (500 to 1000)
    c_p2 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=0, duration=500.0)]
    p2_piano = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(30, 50)), phrase_length=16.0
    ).render(c_p2, KEY_HM, 500.0)
    p2_drone = DroneGenerator(GeneratorParams(density=0.01), velocity=35).render(c_p2, KEY_HM, 500.0)

    # Part III - Recursion (1000 to 1500)
    # Overlapping fast arps in different times
    c_p3 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(125)]
    p3_arp1 = ArpeggiatorGenerator(GeneratorParams(density=0.8), pattern="up", note_duration=0.333).render(c_p3, KEY_HM, 500.0) # Triplet
    p3_arp2 = ArpeggiatorGenerator(GeneratorParams(density=0.8), pattern="down", note_duration=0.25).render(c_p3, KEY_LD, 500.0) # 16th
    p3_arp3 = ArpeggiatorGenerator(GeneratorParams(density=0.8), pattern="converge", note_duration=0.2).render(c_p3, KEY_HM, 500.0) # Quintuplet

    # Part IV - Ascension (1500 to 2000)
    c_p4 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(125)]
    p4_unison = MelodyGenerator(
        GeneratorParams(density=0.6, complexity=0.7, velocity_range=(100, 127)),
        phrase_length=8.0, note_range_low=52, note_range_high=76
    ).render(c_p4, KEY_HM, 500.0)
    
    # Final 1-minute decay (2000 to 2160)
    final_chord = [
        types.NoteInfo(pitch=40, start=2000.0, duration=100.0, velocity=100),
        types.NoteInfo(pitch=47, start=2000.0, duration=100.0, velocity=100),
        types.NoteInfo(pitch=52, start=2000.0, duration=100.0, velocity=100),
    ]
    heartbeat = [types.NoteInfo(pitch=36, start=float(t), duration=0.5, velocity=80) for t in range(2000, 2160, 2)]

    tracks = {
        "guitar": p1_heavy + _off(p3_arp1, 1000.0) + _off(p4_unison, 1500.0) + final_chord,
        "choir": p1_choir + _off(p4_unison, 1500.0),
        "piano": _off(p2_piano, 500.0),
        "organ": _off(p2_drone, 500.0) + _off(p4_unison, 1500.0),
        "lead": _off(p3_arp2, 1000.0),
        "rhodes": _off(p3_arp3, 1000.0),
        "drums": heartbeat
    }
    inst = {
        "guitar": DIST_GUITAR, "choir": CHOIR, "piano": PIANO,
        "organ": PIPE_ORGAN, "lead": MOOG_LEAD, "rhodes": RHODES, "drums": DRUMS_KICK
    }
    _export(tracks, OUT / "06_Fracture_of_Time.mid", bpm, KEY_HM, inst)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   THE FRACTURE OF TIME")
print("   Prog Rock / Jazz Fusion Concept")
print("=" * 60)

produce_clockwork_veins()
produce_glass_constellations()
produce_city_static()
produce_mirrors()
produce_parallel_hearts()
produce_fracture_of_time()

print("\n" + "=" * 60)
print("   ALBUM COMPLETE.")
print(f"   Files in: {OUT}")
print("=" * 60)
