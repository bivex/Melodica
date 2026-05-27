# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_hell_opera.py — HELL OPERA (Devil May Cry Style)

Style: Industrial Metal + Gothic Choir + Neoclassical Shred + Dark Electronic + Opera Rock
Scales: Hungarian Minor, Phrygian Dominant, Harmonic Minor.
Energy: "Smiling right in the middle of hell."

Tracks:
  I.   RED TRIGGER (168 BPM) - Phrygian Dominant
  II.  MARIONETTE MASSACRE (132 BPM, 7/8) - Harmonic Minor
  III. EBONY & IVORY (190 BPM) - Hungarian Minor
  IV.  THE CATHEDRAL BLEEDS (72 BPM) - Phrygian Dominant (Doom)
  V.   STYLE RANK: SSS (Tempo/Meter shifts) - Hungarian Minor
  VI.  DEVIL'S WALTZ (96 BPM, 3/4) - Harmonic Minor
  VII. INFERNO REQUIEM (14 mins) - Hungarian Minor
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
KEY_PHD = types.Scale(root=4, mode=types.Mode.PHRYGIAN_DOMINANT)   # E Phrygian Dominant
KEY_HM = types.Scale(root=9, mode=types.Mode.HUNGARIAN_MINOR)      # A Hungarian Minor
KEY_HARM = types.Scale(root=2, mode=types.Mode.HARMONIC_MINOR)     # D Harmonic Minor

# GM Programs
DIST_GUITAR = 30
OVR_GUITAR = 29
CHOIR = 52
PIPE_ORGAN = 19
MUSIC_BOX = 10
HARPSICHORD = 6
SLAP_BASS = 36
PICK_BASS = 34
SYNTH_BRASS = 62
TAIKO = 116
SHRED_LEAD = 81 # Saw/Square synth mimicking shred guitar
SAW_LEAD = 80
CELLO = 42
PIANO = 0
FX_NOISE = 122

DRUMS_KICK = 36
DRUMS_SNARE = 38
DRUMS_HAT = 42

random.seed(666999) # Hellish seed
OUT = Path("output/album_hell_opera")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -9.0): # Loud, aggressive LUFS
    desk = MixingDesk(niche_cfg={})
    # Metal / Industrial mix
    desk.track_gains.update({
        "guitar": 1.0, "guitar_2": 0.95, "lead": 0.9, "bass": 0.95, 
        "drums": 1.1, "organ": 0.85, "choir": 0.8, "strings": 0.7, 
        "taiko": 1.0, "piano": 0.8, "music_box": 0.85
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, key: types.Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. RED TRIGGER — 168 BPM
# E Phrygian Dominant
# =====================================================================
def produce_red_trigger():
    print("--- 01_Red_Trigger ---")
    bpm = 168
    dur = 504.0 # ~3 mins
    
    chords = [types.ChordLabel(root=4, quality=types.Quality.MAJOR, start=float(i*4), duration=4.0) for i in range(int(dur/4))]

    # Organ & Choir Intro (first 16 bars = 64 beats)
    organ = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(80, 110)), pattern="chord", note_duration=1.0
    ).render(chords[:16], KEY_PHD, 64.0)
    
    choir = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, velocity_range=(90, 115)), pattern="power", note_duration=0.5
    ).render(chords, KEY_PHD, dur) # Stays throughout

    # Main Riff - 8 string gallop (starts beat 64)
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=28, key_range_high=52, velocity_range=(110, 127)),
        pattern="power", note_duration=0.25 # 16th notes
    ).render(chords[16:], KEY_PHD, dur-64.0)

    # Synth doubling guitar octave higher
    synth = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=52, key_range_high=76, velocity_range=(100, 115)),
        pattern="power", note_duration=0.25
    ).render(chords[16:], KEY_PHD, dur-64.0)

    # Solo - Shred sweeps at beat 256 (for 64 beats)
    shred = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=64, key_range_high=100, velocity_range=(115, 127)),
        pattern="up_down_full", note_duration=0.125 # 32nd notes sweeps
    ).render(chords[64:80], KEY_PHD, 64.0)

    # Double kick drums non-stop after intro
    drums = []
    for beat in range(64, int(dur)):
        # Gallop double kick
        drums.append(types.NoteInfo(DRUMS_KICK, float(beat), 0.2, 120))
        drums.append(types.NoteInfo(DRUMS_KICK, float(beat)+0.5, 0.2, 110))
        drums.append(types.NoteInfo(DRUMS_KICK, float(beat)+0.75, 0.2, 110))
        # Snare on 2 and 4
        if beat % 2 == 1:
            drums.append(types.NoteInfo(DRUMS_SNARE, float(beat), 0.2, 127))

    tracks = {
        "organ": organ, "choir": choir, 
        "guitar": _off(guitar, 64.0), "synth": _off(synth, 64.0),
        "lead": _off(shred, 256.0), "drums": drums
    }
    inst = {"organ": PIPE_ORGAN, "choir": CHOIR, "guitar": DIST_GUITAR, "synth": SHRED_LEAD, "lead": OVR_GUITAR, "drums": DRUMS_KICK}
    _export(tracks, OUT / "01_Red_Trigger.mid", bpm, KEY_PHD, inst)

# =====================================================================
# II. MARIONETTE MASSACRE — 132 BPM, 7/8
# D Harmonic Minor
# =====================================================================
def produce_marionette():
    print("--- 02_Marionette_Massacre ---")
    bpm = 132
    bpc = 3.5 # 7/8
    dur = 420.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Distorted Music Box
    mbox = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, key_range_low=72, key_range_high=96, velocity_range=(80, 100)),
        pattern="random", note_duration=0.25
    ).render(chords, KEY_HARM, dur)

    # Staccato Strings
    strings = ArpeggiatorGenerator(
        GeneratorParams(density=0.7, velocity_range=(90, 115)),
        pattern="chord", note_duration=0.25
    ).render(chords, KEY_HARM, dur)

    # Bass (syncopated 7/8)
    bass = BassGenerator(
        GeneratorParams(density=0.8, velocity_range=(100, 120), key_range_low=28, key_range_high=40),
        style="walking" # We'll just use it for movement
    ).render(chords, KEY_HARM, dur)

    # Waltz from hell bridge (beat 210 to 294) - using Harpsichord
    harpsi = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, velocity_range=(85, 110)),
        pattern="waltz", note_duration=0.5
    ).render(chords[int(210/bpc):int(294/bpc)], KEY_HARM, 84.0)

    tracks = {"music_box": mbox, "strings": strings, "bass": bass, "harpsichord": _off(harpsi, 210.0)}
    inst = {"music_box": MUSIC_BOX, "strings": 45, "bass": PICK_BASS, "harpsichord": HARPSICHORD}
    _export(tracks, OUT / "02_Marionette.mid", bpm, KEY_HARM, inst)

# =====================================================================
# III. EBONY & IVORY — 190 BPM
# A Hungarian Minor
# =====================================================================
def produce_ebony_ivory():
    print("--- 03_Ebony_and_Ivory ---")
    bpm = 190
    dur = 760.0 # ~4 mins
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(int(dur/4))]

    # Twin Lead Guitars
    g1 = MelodyGenerator(
        GeneratorParams(density=0.9, complexity=0.9, velocity_range=(110, 127)),
        phrase_length=8.0, note_range_low=64, note_range_high=88
    ).render(chords, KEY_HM, dur)
    
    g2 = [types.NoteInfo(n.pitch - 4, n.start, n.duration, n.velocity) for n in g1] # 3rd below
    from melodica.utils import snap_to_scale
    for n in g2:
        n.pitch = snap_to_scale(n.pitch, KEY_HM)

    # Synth Brass Stabs
    brass = ArpeggiatorGenerator(
        GeneratorParams(density=0.3, velocity_range=(100, 127)),
        pattern="chord", note_duration=0.5
    ).render(chords, KEY_HM, dur)

    # Jazz Fusion Bridge (Beat 300 to 460)
    slap_bass = MelodyGenerator(
        GeneratorParams(density=0.8, complexity=0.8, velocity_range=(110, 127)),
        phrase_length=4.0, note_range_low=28, note_range_high=52, syncopation=0.6
    ).render(chords[75:115], KEY_HM, 160.0)

    # Hyper-fast drum fills
    drums = []
    for beat in range(int(dur)):
        drums.append(types.NoteInfo(DRUMS_KICK, float(beat), 0.2, 110))
        drums.append(types.NoteInfo(DRUMS_HAT, float(beat)+0.5, 0.2, 90))
        if beat % 2 == 1:
            drums.append(types.NoteInfo(DRUMS_SNARE, float(beat), 0.2, 127))
        # Fills every 8 bars
        if beat > 0 and beat % 32 == 30:
            for offset in [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75]:
                drums.append(types.NoteInfo(DRUMS_SNARE, float(beat)+offset, 0.1, 127))

    tracks = {
        "guitar": g1, "guitar_2": g2, "brass": brass, 
        "slap_bass": _off(slap_bass, 300.0), "drums": drums
    }
    inst = {"guitar": DIST_GUITAR, "guitar_2": OVR_GUITAR, "brass": SYNTH_BRASS, "slap_bass": SLAP_BASS, "drums": DRUMS_KICK}
    _export(tracks, OUT / "03_Ebony_Ivory.mid", bpm, KEY_HM, inst)

# =====================================================================
# IV. THE CATHEDRAL BLEEDS — 72 BPM
# C Phrygian Dominant (Doom)
# =====================================================================
def produce_cathedral():
    print("--- 04_Cathedral_Bleeds ---")
    bpm = 72
    dur = 288.0
    KEY_DOOM = types.Scale(root=0, mode=types.Mode.PHRYGIAN_DOMINANT)
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=float(i*4), duration=4.0) for i in range(int(dur/4))]

    # Slow Doom Guitars
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, key_range_low=24, key_range_high=48, velocity_range=(110, 127)),
        pattern="power", note_duration=1.0 # Very slow, heavy chords
    ).render(chords, KEY_DOOM, dur)

    # Massive Pipe Organ
    organ = DroneGenerator(
        GeneratorParams(density=0.1, key_range_low=36, key_range_high=72), velocity=80
    ).render(chords, KEY_DOOM, dur)

    # Choir
    choir = ArpeggiatorGenerator(
        GeneratorParams(density=0.6, velocity_range=(85, 115)), pattern="chord", note_duration=2.0
    ).render(chords, KEY_DOOM, dur)

    # Blast Beats Climax (Beat 200 to 288)
    drums = []
    for beat in range(200, 288):
        # 16th note blast beats
        for offset in [0.0, 0.25, 0.5, 0.75]:
            drums.append(types.NoteInfo(DRUMS_KICK, float(beat)+offset, 0.1, 127))
            drums.append(types.NoteInfo(DRUMS_SNARE, float(beat)+offset, 0.1, 120))
            drums.append(types.NoteInfo(DRUMS_HAT, float(beat)+offset, 0.1, 100))

    # Taiko Hits (Big spacey hits)
    taiko = []
    for beat in range(0, 200, 4):
        taiko.append(types.NoteInfo(pitch=35, start=float(beat), duration=2.0, velocity=127))

    tracks = {"guitar": guitar, "organ": organ, "choir": choir, "drums": drums, "taiko": taiko}
    inst = {"guitar": DIST_GUITAR, "organ": PIPE_ORGAN, "choir": CHOIR, "drums": DRUMS_KICK, "taiko": TAIKO}
    _export(tracks, OUT / "04_Cathedral.mid", bpm, KEY_DOOM, inst)

# =====================================================================
# V. STYLE RANK: SSS — Constantly changing
# E Hungarian Minor
# =====================================================================
def produce_sss():
    print("--- 05_Style_Rank_SSS ---")
    bpm = 150 # Base
    dur = 600.0
    chords = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(int(dur/4))]

    # Section 1: 5/4 Sweep Tapping
    c_sec1 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*5), duration=5.0) for i in range(20)]
    sec1 = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, velocity_range=(100, 127)), pattern="up_down_full", note_duration=0.125
    ).render(c_sec1, KEY_HM, 100.0)

    # Section 2: 11/8 Bass Solo (100 to 200)
    c_sec2 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*5.5), duration=5.5) for i in range(20)]
    sec2_bass = MelodyGenerator(
        GeneratorParams(density=0.9, complexity=0.9, velocity_range=(100, 127)),
        phrase_length=5.5, note_range_low=33, note_range_high=57, syncopation=0.5
    ).render(c_sec2, KEY_HM, 110.0)

    # Section 3: Drum'n'bass burst + Synth Duel (210 to 400)
    c_sec3 = [types.ChordLabel(root=4, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(50)]
    synth_duel_1 = MelodyGenerator(GeneratorParams(density=0.8, velocity_range=(100, 127))).render(c_sec3, KEY_HM, 190.0)
    synth_duel_2 = MelodyGenerator(GeneratorParams(density=0.8, velocity_range=(100, 127))).render(c_sec3, KEY_HM, 190.0)
    # Pan/pitch separate
    synth_duel_2 = [types.NoteInfo(n.pitch + 12, n.start, n.duration, n.velocity) for n in synth_duel_2]
    
    # Pause at 4:40 (around beat 420)
    # Sudden silence from 420 to 430
    
    # Section 4: Orchestral Hit Return (430 to 600)
    orch_hits = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=36, key_range_high=96, velocity_range=(120, 127)),
        pattern="chord", note_duration=0.5
    ).render(chords[-40:], KEY_HM, 170.0)
    
    tracks = {
        "guitar": sec1, 
        "bass": _off(sec2_bass, 100.0),
        "lead": _off(synth_duel_1, 210.0),
        "synth": _off(synth_duel_2, 210.0),
        "choir": _off(orch_hits, 430.0)
    }
    inst = {"guitar": DIST_GUITAR, "bass": SLAP_BASS, "lead": SHRED_LEAD, "synth": SAW_LEAD, "choir": 55} # 55 Orch Hit
    _export(tracks, OUT / "05_Style_Rank_SSS.mid", bpm, KEY_HM, inst)

# =====================================================================
# VI. DEVIL'S WALTZ — 96 BPM, 3/4
# G Harmonic Minor
# =====================================================================
def produce_devils_waltz():
    print("--- 06_Devils_Waltz ---")
    bpm = 96
    bpc = 3.0
    dur = 300.0
    KEY_WALTZ = types.Scale(root=7, mode=types.Mode.HARMONIC_MINOR)
    chords = [types.ChordLabel(root=7, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Piano Waltz
    piano = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(60, 90)), pattern="waltz", note_duration=1.0
    ).render(chords, KEY_WALTZ, dur)

    # Distorted Cello
    cello = MelodyGenerator(
        GeneratorParams(density=0.4, velocity_range=(80, 110)),
        phrase_length=6.0, note_range_low=43, note_range_high=67
    ).render(chords, KEY_WALTZ, dur)

    # Strings
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.2, velocity_range=(60, 80))
    ).render(chords, KEY_WALTZ, dur)
    
    # Noise Wall at the end (270 to 300)
    noise = DroneGenerator(
        GeneratorParams(density=0.1, key_range_low=24, key_range_high=96), velocity=127
    ).render(chords[-10:], KEY_WALTZ, 30.0)

    tracks = {"piano": piano, "cello": cello, "strings": strings, "fx": _off(noise, 270.0)}
    inst = {"piano": PIANO, "cello": OVR_GUITAR, "strings": 49, "fx": FX_NOISE} # Overdrive guitar for distorted cello feel
    _export(tracks, OUT / "06_Devils_Waltz.mid", bpm, KEY_WALTZ, inst)

# =====================================================================
# VII. INFERNO REQUIEM — 14 Mins
# B Hungarian Minor
# =====================================================================
def produce_inferno_requiem():
    print("--- 07_Inferno_Requiem ---")
    bpm = 120
    dur = 1680.0 # 14 mins
    KEY_REQ = types.Scale(root=11, mode=types.Mode.HUNGARIAN_MINOR)
    
    # Part I: Descent (0 - 400)
    c_p1 = [types.ChordLabel(root=11, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(100)]
    choir_p1 = ArpeggiatorGenerator(GeneratorParams(density=0.8, velocity_range=(90, 110)), pattern="chord", note_duration=1.0).render(c_p1, KEY_REQ, 400.0)
    riff_p1 = ArpeggiatorGenerator(GeneratorParams(density=0.8, key_range_low=23, key_range_high=47, velocity_range=(100, 127)), pattern="power", note_duration=0.5).render(c_p1, KEY_REQ, 400.0)

    # Part II: Blood Circuit (400 - 800)
    c_p2 = [types.ChordLabel(root=11, quality=types.Quality.MINOR, start=0.0, duration=400.0)]
    shred_p2 = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=64, key_range_high=100, velocity_range=(110, 127)),
        pattern="up_down_full", note_duration=0.083 # Fast!
    ).render(c_p2, KEY_REQ, 400.0)

    # Part III: Fallen Angel (800 - 1200)
    c_p3 = [types.ChordLabel(root=11, quality=types.Quality.MINOR, start=0.0, duration=400.0)]
    piano_p3 = MelodyGenerator(GeneratorParams(density=0.05, velocity_range=(40, 60)), phrase_length=16.0).render(c_p3, KEY_REQ, 400.0)
    vox_p3 = MelodyGenerator(GeneratorParams(density=0.08, velocity_range=(50, 75)), phrase_length=16.0).render(c_p3, KEY_REQ, 400.0)

    # Part IV: Last Trigger (1200 - 1600)
    c_p4 = [types.ChordLabel(root=11, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(100)]
    all_together_g = ArpeggiatorGenerator(GeneratorParams(density=1.0), pattern="power", note_duration=0.25).render(c_p4, KEY_REQ, 400.0)
    all_together_c = ArpeggiatorGenerator(GeneratorParams(density=0.9), pattern="chord", note_duration=1.0).render(c_p4, KEY_REQ, 400.0)

    # Finale: Heartbeat + Harmonic (1600 - 1680)
    heartbeat = [types.NoteInfo(pitch=36, start=float(t), duration=0.2, velocity=100) for t in range(1600, 1680, 2)]
    harmonic = [types.NoteInfo(pitch=95, start=1670.0, duration=10.0, velocity=90)]

    tracks = {
        "choir": choir_p1 + _off(all_together_c, 1200.0),
        "guitar": riff_p1 + _off(all_together_g, 1200.0),
        "lead": _off(shred_p2, 400.0),
        "piano": _off(piano_p3, 800.0),
        "vox": _off(vox_p3, 800.0),
        "drums": heartbeat,
        "fx": harmonic
    }
    inst = {"choir": CHOIR, "guitar": DIST_GUITAR, "lead": SHRED_LEAD, "piano": PIANO, "vox": 53, "drums": DRUMS_KICK, "fx": 31} # 31 = Guitar harmonics
    _export(tracks, OUT / "07_Inferno_Requiem.mid", bpm, KEY_REQ, inst)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   HELL OPERA")
print("   Devil May Cry Style / Operatic Metal")
print("=" * 60)

produce_red_trigger()
produce_marionette()
produce_ebony_ivory()
produce_cathedral()
produce_sss()
produce_devils_waltz()
produce_inferno_requiem()

print("\n" + "=" * 60)
print("   ALBUM COMPLETE.")
print(f"   Files in: {OUT}")
print("=" * 60)
