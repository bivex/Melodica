# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_voros_kiraly.py — VÖRÖS KIRÁLY (Красный Король)

Hungarian Minor [0, 2, 3, 6, 7, 8, 11]
Огонь, одержимость, ночная виртуозность, цыганская трагедия.

  I.   Fekete Tűz      (Чёрный огонь) — 132 BPM, 7/8.
  II.  Vérhold         (Кровавая луна) — 84 BPM, 4/4.
  III. Ördögtánc       (Танец дьявола) — 176 BPM, 11/8.
  IV.  A Halott Király (Мёртвый король) — 58 BPM, 5/4.
  V.   Csillagvihar    (Звёздная буря) — 148 -> 220 BPM.
"""

import random
import math
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# KEY: G Hungarian Minor (very common for this scale's tragic feel)
KEY = types.Scale(root=7, mode=types.Mode.HUNGARIAN_MINOR)

# GM Programs
VIOLIN = 40
CLARINET = 71
CIMBALOM = 15    # Dulcimer
CELLO = 42
CONTRABASS = 43
GUITAR_NYLON = 24
GUITAR_OVERDRIVE = 29
ACCORDION = 21
ORGAN = 19
CHOIR_MALE = 52
DRUMS = 0 # Percussion channel 10

random.seed(666) # Appropriately demonic
OUT = Path("output/album_voros_kiraly")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -12.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "violin": 1.0, "cimbalom": 0.9, "clarinet": 0.85,
        "bass": 0.7, "drums": 0.8, "guitar": 0.75,
        "cello": 0.65, "vox": 0.9, "organ": 0.8, "choir": 0.7
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. Fekete Tűz (Чёрный огонь) — 7/8 (3+2+2)
# =====================================================================
def produce_fekete_tuz():
    print("--- 01_Fekete_Tuz ---")
    bpm = 132
    bpc = 3.5 # 7/8 bar
    dur = 210.0 # ~4 minutes
    
    chords = [types.ChordLabel(root=7, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Intro: Solo Violin rubato
    violin_intro = MelodyGenerator(
        GeneratorParams(density=0.6, complexity=0.8, velocity_range=(70, 110)),
        phrase_length=14.0, note_range_low=67, note_range_high=91,
        ornament_probability=0.4
    ).render(chords[:4], KEY, 14.0)

    # Cimbalom enter
    cimbalom = ArpeggiatorGenerator(
        GeneratorParams(density=0.8, velocity_range=(60, 95)),
        pattern="up_down_full", note_duration=0.15
    ).render(chords[4:], KEY, dur - 14.0)

    # Main Theme: Violin + Clarinet in unison
    theme_gen = MelodyGenerator(
        GeneratorParams(density=0.45, complexity=0.7, velocity_range=(85, 115)),
        phrase_length=7.0, note_range_low=67, note_range_high=84
    )
    violin_theme = theme_gen.render(chords[4:], KEY, dur - 14.0)
    clarinet_theme = list(violin_theme) # unison

    # Bass & Drums
    bass = [types.NoteInfo(pitch=31, start=float(i*bpc), duration=0.2, velocity=90) for i in range(4, int(dur/bpc))]
    kick = [types.NoteInfo(pitch=36, start=float(i*bpc), duration=0.5, velocity=110) for i in range(4, int(dur/bpc))]

    # Duel at 2:10 (beat 140 approx)
    violin_duel = MelodyGenerator(
        GeneratorParams(density=0.9, velocity_range=(100, 127)),
        note_range_low=79, note_range_high=103, steps_probability=0.3
    ).render(chords[40:48], KEY, 28.0) # Ascending feel
    
    cimbalom_duel = ArpeggiatorGenerator(
        GeneratorParams(density=0.95, velocity_range=(90, 120)),
        pattern="down", note_duration=0.1
    ).render(chords[40:48], KEY, 28.0)

    tracks = {
        "violin": violin_intro + _off(violin_theme, 14.0) + _off(violin_duel, 140.0),
        "clarinet": _off(clarinet_theme, 14.0),
        "cimbalom": _off(cimbalom, 14.0) + _off(cimbalom_duel, 140.0),
        "bass": bass,
        "drums": kick
    }
    inst = {"violin": VIOLIN, "clarinet": CLARINET, "cimbalom": CIMBALOM, "bass": CONTRABASS, "drums": 36}
    _export(tracks, OUT / "01_Fekete_Tuz.mid", bpm, inst)

# =====================================================================
# II. Vérhold (Кровавая луна) — 4/4
# =====================================================================
def produce_verhold():
    print("--- 02_Verhold ---")
    bpm = 84
    dur = 160.0
    chords = [types.ChordLabel(root=7, quality=types.Quality.MINOR, start=0, duration=dur)]

    # Whisper Vox
    vox = MelodyGenerator(
        GeneratorParams(density=0.15, velocity_range=(40, 60)),
        phrase_length=16.0, note_range_low=60, note_range_high=72
    ).render(chords, KEY, dur)

    # Cello Pedal
    cello = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=43, key_range_high=44),
        velocity=45
    ).render(chords, KEY, dur)

    # Cimbalom High Arp
    cimbalom = ArpeggiatorGenerator(
        GeneratorParams(density=0.2, key_range_low=79, key_range_high=96, velocity_range=(35, 55)),
        pattern="random", note_duration=0.5
    ).render(chords, KEY, dur)

    # Guitar Swells
    guitar = DroneGenerator(
        GeneratorParams(density=0.05, key_range_low=55, key_range_high=67),
        velocity=40
    ).render(chords, KEY, dur)

    tracks = {"vox": vox, "cello": cello, "cimbalom": cimbalom, "guitar": guitar}
    inst = {"vox": 53, "cello": CELLO, "cimbalom": CIMBALOM, "guitar": GUITAR_OVERDRIVE}
    _export(tracks, OUT / "02_Verhold.mid", bpm, inst)

# =====================================================================
# III. Ördögtánc (Танец дьявола) — 11/8
# =====================================================================
def produce_ordogtanc():
    print("--- 03_Ordogtanc ---")
    bpm = 176
    bpc = 5.5 # 11/8
    dur = 220.0
    chords = [types.ChordLabel(root=7, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Fast Violin
    violin = MelodyGenerator(
        GeneratorParams(density=0.85, velocity_range=(95, 125)),
        phrase_length=5.5, note_range_low=67, note_range_high=96
    ).render(chords, KEY, dur)

    # Accordion Accents
    accordion = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(80, 110)),
        pattern="chord", note_duration=0.25
    ).render(chords, KEY, dur)

    # Sweep Guitar
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, velocity_range=(90, 120)),
        pattern="up_down_full", note_duration=0.08
    ).render(chords, KEY, dur)

    # Bass Tremolo
    bass = DroneGenerator(
        GeneratorParams(density=0.5, key_range_low=31, key_range_high=32),
        velocity=75
    ).render(chords, KEY, dur)

    # Unison Run at 3:40 (approx beat 645 at 176bpm? No, 220 beats total)
    # Let's place it near the end
    unison_run = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=43, key_range_high=91, velocity_range=(120, 127)),
        pattern="up", note_duration=0.05
    ).render(chords[-4:], KEY, bpc*4)

    tracks = {
        "violin": violin + _off(unison_run, dur - bpc*4),
        "guitar": guitar + _off(unison_run, dur - bpc*4),
        "accordion": accordion,
        "bass": bass
    }
    inst = {"violin": VIOLIN, "guitar": GUITAR_OVERDRIVE, "accordion": ACCORDION, "bass": CONTRABASS}
    _export(tracks, OUT / "03_Ordogtanc.mid", bpm, inst)

# =====================================================================
# IV. A Halott Király (Мёртвый король) — 5/4
# =====================================================================
def produce_halott_kiraly():
    print("--- 04_A_Halott_Kiraly ---")
    bpm = 58
    bpc = 5.0
    dur = 250.0
    chords = [types.ChordLabel(root=7, quality=types.Quality.MINOR, start=float(i*bpc), duration=bpc) for i in range(int(dur/bpc))]

    # Organ Low
    organ = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=24, key_range_high=36),
        velocity=60
    ).render(chords, KEY, dur)

    # Slow Strings (Parallel Seconds feel)
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.05, key_range_low=48, key_range_high=72),
    ).render(chords, KEY, dur)

    # Male Choir Open Fifths
    choir = ArpeggiatorGenerator(
        GeneratorParams(density=0.1, key_range_low=43, key_range_high=67, velocity_range=(50, 75)),
        pattern="power" # Root + 5th
    ).render(chords, KEY, dur)

    # Full Hungarian Minor Chord in Choir at 4:20 (approx beat 250?)
    # Script total dur is 250. Let's make it 300.
    final_chord = [types.NoteInfo(pitch=7+off, start=250.0, duration=10.0, velocity=100) for off in [0, 2, 3, 6, 7, 8, 11]]

    tracks = {"organ": organ, "strings": strings, "choir": choir + final_chord}
    inst = {"organ": ORGAN, "strings": 49, "choir": CHOIR_MALE}
    _export(tracks, OUT / "04_A_Halott_Kiraly.mid", bpm, inst)

# =====================================================================
# V. Csillagvihar (Звёздная буря) — Accelerando
# =====================================================================
def produce_csillagvihar():
    print("--- 05_Csillagvihar ---")
    bpm = 180 # Fixed in MIDI, but we simulate intensity
    dur = 400.0
    chords = [types.ChordLabel(root=7, quality=types.Quality.MINOR, start=float(i*4), duration=4.0) for i in range(100)]

    # Intro Drone + Harmonics
    drone = DroneGenerator(GeneratorParams(density=0.01), velocity=40).render(chords[:10], KEY, 40.0)
    violin_h = MelodyGenerator(
        GeneratorParams(density=0.2, key_range_low=91, key_range_high=108),
        phrase_length=8.0
    ).render(chords[:10], KEY, 40.0)

    # Main Idea: Variations
    # 1. Violin Original
    v_orig = MelodyGenerator(GeneratorParams(density=0.6), phrase_length=4.0).render(chords[10:], KEY, dur-40.0)
    
    # 2. Guitar Inversion (Manual inversion via pitch mapping)
    g_raw = MelodyGenerator(GeneratorParams(density=0.6), phrase_length=4.0).render(chords[10:], KEY, dur-40.0)
    g_inv = [types.NoteInfo(pitch=150 - n.pitch, start=n.start, duration=n.duration, velocity=n.velocity) for n in g_raw]
    # Re-snap to scale
    from melodica.utils import snap_to_scale
    for n in g_inv:
        n.pitch = snap_to_scale(max(40, min(80, n.pitch)), KEY)

    # 3. Slow Choir
    choir_slow = DroneGenerator(GeneratorParams(density=0.05), velocity=55).render(chords[10:], KEY, dur-40.0)

    # 4. Cimbalom Fragments
    cimbalom = ArpeggiatorGenerator(GeneratorParams(density=0.4), pattern="random", note_duration=0.1).render(chords[10:], KEY, dur-40.0)

    # Climax Ascending Run
    climax_run = ArpeggiatorGenerator(
        GeneratorParams(density=1.0, key_range_low=31, key_range_high=103, velocity_range=(110, 127)),
        pattern="up", note_duration=0.05
    ).render(chords[90:], KEY, 40.0)

    tracks = {
        "violin": violin_h + _off(v_orig, 40.0) + _off(climax_run, 360.0),
        "guitar": _off(g_inv, 40.0) + _off(climax_run, 360.0),
        "choir": _off(choir_slow, 40.0),
        "cimbalom": _off(cimbalom, 40.0)
    }
    inst = {"violin": VIOLIN, "guitar": GUITAR_OVERDRIVE, "choir": CHOIR_MALE, "cimbalom": CIMBALOM}
    _export(tracks, OUT / "05_Csillagvihar.mid", bpm, inst)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   VÖRÖS KIRÁLY — КРАСНЫЙ КОРОЛЬ")
print("   Hungarian Minor Virtuosity")
print("=" * 60)

produce_fekete_tuz()
produce_verhold()
produce_ordogtanc()
produce_halott_kiraly()
produce_csillagvihar()

print("\n" + "=" * 60)
print("   VÖRÖS KIRÁLY — COMPLETE.")
print(f"   Files generated in: {OUT}")
print("=" * 60)
