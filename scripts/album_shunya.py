# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_shunya.py — ШУНЬЯ (Śūnyatā — Пустотность)

Overtone / Acoustic Scale [0, 2, 4, 6, 7, 9, 10]
Лад, продиктованный физикой звука. Природный резонанс.

  I.   Пратхама    — Первый / Начало. 52 BPM.
  II.  Антаракаша  — Внутреннее небо. 48 BPM.
  III. Нади        — Поток / Река. 60 BPM (размытый метр).
  IV.  Вишрам      — Глубокий отдых. 40 BPM.
  V.   Акаша       — Эфир / Пространство. Свободная форма.
  VI.  Самапти     — Завершение / Возвращение. 44 -> 66 BPM.
"""

import random
import math
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.rest import RestGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# KEY: C Overtone (Acoustic Major)
KEY = types.Scale(root=0, mode=types.Mode.ACOUSTIC_MAJOR)

# GM Programs (Best approximations for ethnic/meditation instruments)
TIBETAN_BOWL = 14  # Tubular Bells (closest resonance)
SITAR = 104        # Sitar
TANPURA = 104      # Sitar (layered or low register)
FLUTE_SOPRANO = 73 # Flute
FLUTE_ALTO = 73    # Flute (low register)
CELLO = 42         # Cello
HARP = 46          # Orchestral Harp
CONTRABASS = 43    # Contrabass (pizz)
VOICE_AAH = 52     # Choir Aahs
VOICE_HUM = 53     # Voice Oohs
PAD_WARM = 89      # Warm Pad
PAD_SPACE = 91     # Polysynth / Space
PIANO_SOFT = 0     # Acoustic Grand (soft)

random.seed(108) # Sacred number
OUT = Path("output/album_shunya")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -18.0):
    desk = MixingDesk(niche_cfg={})
    # Soft gains for meditation
    desk.track_gains.update({
        "bowl": 0.8, "pad": 0.4, "flute": 0.7, "cello": 0.5,
        "sitar": 0.7, "voice": 0.6, "tanpura": 0.5, "harp": 0.65,
        "bass": 0.45, "piano": 0.7, "drone": 0.35, "bells": 0.4
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict, lufs: float = -18.0):
    final_notes, cc_events = _master(tracks, bpm, lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# Track I — Пратхама (Prathama — Начало)
# =====================================================================
def produce_prathama():
    print("--- 01_Prathama ---")
    bpm = 52
    dur = 200.0 # ~4 minutes at 52bpm
    
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0, duration=dur)]

    # Intro & Outro Bowls (Tibetan)
    bowl_hits = [
        types.NoteInfo(pitch=72, start=2.0, duration=16.0, velocity=80),
        types.NoteInfo(pitch=67, start=18.0, duration=16.0, velocity=65),
        types.NoteInfo(pitch=60, start=dur-20.0, duration=18.0, velocity=70)
    ]

    # Sinth Pad - constant tonic drone
    pad = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=48, key_range_high=49),
        velocity=35
    ).render(chords, KEY, dur)

    # Cello pedal tone
    cello = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=37),
        velocity=30
    ).render(chords, KEY, dur)

    # Flute melody - extremely slow
    flute = MelodyGenerator(
        GeneratorParams(density=0.08, velocity_range=(40, 60)),
        phrase_length=16.0,
        harmony_note_probability=0.8,
        steps_probability=0.9,
        note_range_low=72, note_range_high=84,
        register_smoothness=0.9
    ).render(chords, KEY, dur - 40.0)
    flute = _off(flute, 36.0) # starts after intro bowls

    # Specific Overtone moment at 3:00 (approx beat 156 at 52bpm)
    # 6th degree (tritone F#)
    overtone_hit = types.NoteInfo(pitch=78, start=156.0, duration=12.0, velocity=50)
    flute.append(overtone_hit)

    tracks = {"bowl": bowl_hits, "pad": pad, "flute": flute, "cello": cello}
    instruments = {"bowl": TIBETAN_BOWL, "pad": PAD_WARM, "flute": FLUTE_SOPRANO, "cello": CELLO}
    _export(tracks, OUT / "01_Prathama.mid", bpm, instruments)

# =====================================================================
# Track II — Антаракаша (Antarākāśa — Внутреннее небо)
# =====================================================================
def produce_antarakasha():
    print("--- 02_Antarakasha ---")
    bpm = 48
    dur = 240.0
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0, duration=dur)]

    # Tanpura drone
    tanpura = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, velocity_range=(30, 45)),
        pattern="up_down", note_duration=0.5
    ).render(chords, KEY, dur)

    # Sitar - slow, expressive
    sitar = MelodyGenerator(
        GeneratorParams(density=0.12, velocity_range=(40, 65)),
        ornament_probability=0.3, # for meend/glissando feel
        phrase_length=12.0,
        note_range_low=60, note_range_high=76
    ).render(chords, KEY, dur - 30.0)

    # Vocalise
    voice = MelodyGenerator(
        GeneratorParams(density=0.1, velocity_range=(35, 55)),
        phrase_length=16.0,
        note_range_low=64, note_range_high=79,
        note_repetition_probability=0.05
    ).render(chords, KEY, dur)

    # Bells
    bells = ArpeggiatorGenerator(
        GeneratorParams(density=0.15, velocity_range=(20, 40), 
                        key_range_low=84, key_range_high=96),
        pattern="random", note_duration=1.0
    ).render(chords, KEY, dur)

    tracks = {"tanpura": tanpura, "sitar": sitar, "voice": voice, "bells": bells}
    instruments = {"tanpura": TANPURA, "sitar": SITAR, "voice": VOICE_HUM, "bells": TIBETAN_BOWL}
    _export(tracks, OUT / "02_Antarakasha.mid", bpm, instruments)

# =====================================================================
# Track III — Нади (Nādī — Поток)
# =====================================================================
def produce_nadi():
    print("--- 03_Nadi ---")
    bpm = 60
    dur = 300.0
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0, duration=dur)]

    # Harp - constantly evolving patterns
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.35, velocity_range=(40, 65)),
        pattern="converge", note_duration=0.5
    ).render(chords, KEY, dur)

    # Alto Flute
    flute = MelodyGenerator(
        GeneratorParams(density=0.08, velocity_range=(35, 55)),
        phrase_length=32.0,
        note_range_low=55, note_range_high=67
    ).render(chords, KEY, dur)

    # Contrabass Pizz
    bass = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(40, 60)),
        phrase_length=16.0,
        note_range_low=28, note_range_high=40
    ).render(chords, KEY, dur)

    tracks = {"harp": harp, "flute": flute, "bass": bass}
    instruments = {"harp": HARP, "flute": FLUTE_ALTO, "bass": CONTRABASS}
    _export(tracks, OUT / "03_Nadi.mid", bpm, instruments)

# =====================================================================
# Track IV — Вишрам (Viśrām — Глубокий отдых)
# =====================================================================
def produce_vishram():
    print("--- 04_Vishram ---")
    bpm = 40
    dur = 360.0
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0, duration=dur)]

    # Low Synth Drone (174 Hz approx F2-G2)
    drone = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=41, key_range_high=43),
        velocity=30
    ).render(chords, KEY, dur)

    # Singing Bowls - alternating
    bowl_large = [types.NoteInfo(pitch=48, start=i*60.0, duration=30.0, velocity=50) for i in range(0, 6)]
    bowl_mid = [types.NoteInfo(pitch=60, start=i*60.0 + 20.0, duration=20.0, velocity=45) for i in range(0, 6)]
    bowl_small = [types.NoteInfo(pitch=72, start=i*60.0 + 40.0, duration=15.0, velocity=40) for i in range(0, 6)]
    bowls = bowl_large + bowl_mid + bowl_small

    # Monochord melody
    monochord = MelodyGenerator(
        GeneratorParams(density=0.06, velocity_range=(30, 45)),
        phrase_length=24.0,
        note_range_low=60, note_range_high=72
    ).render(chords, KEY, dur)

    # Male Throat Hum
    voice = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=36, key_range_high=48),
        velocity=35
    ).render(chords, KEY, dur)

    tracks = {"drone": drone, "bowl": bowls, "monochord": monochord, "voice": voice}
    instruments = {"drone": PAD_WARM, "bowl": TIBETAN_BOWL, "monochord": SITAR, "voice": VOICE_AAH}
    _export(tracks, OUT / "04_Vishram.mid", bpm, instruments)

# =====================================================================
# Track V — Акаша (Ākāśa — Эфир)
# =====================================================================
def produce_akasha():
    print("--- 05_Akasha ---")
    bpm = 40 # Nominal
    dur = 600.0 # 10 minutes
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0, duration=dur)]

    # Long Synth Pads
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, velocity_range=(25, 45))
    ).render(chords, KEY, dur)

    # White noise / Wind (using high register soft pad)
    wind = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=96, key_range_high=108),
        velocity=15
    ).render(chords, KEY, dur)

    # Silence gap at 4:00 (beat 160 at 40bpm)
    # Actually at 4:00 it's 240 seconds. 240s / (60/40) = 160 beats.
    pad = [n for n in pad if n.start < 160 or n.start > 180]

    tracks = {"pad": pad, "drone": wind}
    instruments = {"pad": PAD_SPACE, "drone": PAD_WARM}
    _export(tracks, OUT / "05_Akasha.mid", bpm, instruments)

# =====================================================================
# Track VI — Самапти (Samāpti — Завершение)
# =====================================================================
def produce_samapti():
    print("--- 06_Samapti ---")
    bpm_start = 44
    bpm_end = 66
    dur = 240.0
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0, duration=dur)]

    # Soft Piano - enters gradually
    piano = MelodyGenerator(
        GeneratorParams(density=0.2, velocity_range=(40, 75)),
        phrase_length=8.0,
        note_range_low=60, note_range_high=79
    ).render(chords, KEY, dur - 32.0)
    piano = _off(piano, 32.0)

    # Warm Voice
    voice = MelodyGenerator(
        GeneratorParams(density=0.15, velocity_range=(50, 75)),
        phrase_length=12.0,
        note_range_low=62, note_range_high=74
    ).render(chords, KEY, dur)

    # Strings buildup
    cello = DroneGenerator(GeneratorParams(density=0.02, key_range_low=36, key_range_high=48), velocity=40).render(chords, KEY, dur)
    viola = DroneGenerator(GeneratorParams(density=0.02, key_range_low=48, key_range_high=60), velocity=45).render(chords, KEY, dur)
    violin = DroneGenerator(GeneratorParams(density=0.02, key_range_low=60, key_range_high=72), velocity=50).render(chords, KEY, dur)
    
    # Assembly
    tracks = {
        "piano": piano, "voice": voice, 
        "cello": cello, "viola": viola, "violin": violin,
        "bowl": [types.NoteInfo(pitch=60, start=0, duration=10, velocity=60)]
    }
    instruments = {
        "piano": PIANO_SOFT, "voice": VOICE_HUM, 
        "cello": CELLO, "viola": 41, "violin": 40, "bowl": TIBETAN_BOWL
    }
    
    # We use mid-point BPM for export as constant
    _export(tracks, OUT / "06_Samapti.mid", 55, instruments)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   ŚŪNYATĀ — ШУНЬЯ — ПУСТОТНОСТЬ")
print("   Album in Overtone Scale")
print("=" * 60)

produce_prathama()
produce_antarakasha()
produce_nadi()
produce_vishram()
produce_akasha()
produce_samapti()

print("\n" + "=" * 60)
print("   ŚŪNYATĀ — COMPLETE.")
print(f"   Files generated in: {OUT}")
print("=" * 60)
