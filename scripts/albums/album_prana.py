# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_prana.py — ПРАНА (Prāṇa — Дыхание жизни)

7-ступенчатый цикл дыхательной медитации.
Каждый трек — новая техника и новое состояние.

  I.   Ujjayi (Океаническое дыхание)      — C Major. Спокойствие. 60 BPM.
  II.  Anuloma (Попеременное дыхание)     — G Lydian. Баланс. 56 BPM.
  III. Kumbhaka (Задержка)                — D Dorian. Глубина. 48 BPM.
  IV.  Kapalabhati (Огненное дыхание)     — E Phrygian Dominant. Энергия. 120 BPM.
  V.   Bhramari (Пчелиное дыхание)        — B Locrian (Natural 2). Резонанс. 52 BPM.
  VI.  Sama Vritti (Квадратное дыхание)   — F Lydian. Стабильность. 64 BPM.
  VII. Shavasana (Полное расслабление)    — C Overtone. Тишина. 40 BPM.
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
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# GM Programs
PIANO = 0
HARP = 46
NYLON_GUITAR = 24
CELLO = 42
FLUTE = 73
PAD_WARM = 89
PAD_SPACE = 91
CHOIR = 52
BOWL = 14
TABLA = 116 # Taiko/Ethnic
SHAKER = 115 # Woodblock/Shaker

random.seed(432) # Standard healing frequency seed
OUT = Path("output/album_prana")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "piano": 0.8, "harp": 0.7, "flute": 0.75, "cello": 0.6,
        "pad": 0.5, "choir": 0.55, "drums": 0.4, "perc": 0.35,
        "drone": 0.4, "bowl": 0.9, "guitar": 0.7
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, key: types.Scale, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=key,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. Ujjayi — C Major, 60 BPM
# =====================================================================
def produce_ujjayi():
    print("--- 01_Ujjayi ---")
    bpm = 60
    dur = 240.0
    key = types.Scale(0, types.Mode.MAJOR)
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0.0, duration=dur)]

    # Soft Pad - "Breathe in/out" automation feel
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.1, key_range_low=48, key_range_high=72),
        overlap=1.0
    ).render(chords, key, dur)

    # Flute - slow phrases, 4 beats in, 4 beats out
    flute = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(40, 60)),
        phrase_length=8.0,
        note_range_low=72, note_range_high=84
    ).render(chords, key, dur)

    # Cello - deep support
    cello = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=36, key_range_high=48),
        velocity=45
    ).render(chords, key, dur)

    tracks = {"pad": pad, "flute": flute, "cello": cello}
    inst = {"pad": PAD_WARM, "flute": FLUTE, "cello": CELLO}
    _export(tracks, OUT / "01_Ujjayi.mid", bpm, key, inst)

# =====================================================================
# II. Anuloma — G Lydian, 56 BPM
# =====================================================================
def produce_anuloma():
    print("--- 02_Anuloma ---")
    bpm = 56
    dur = 256.0
    key = types.Scale(7, types.Mode.LYDIAN)
    chords = [types.ChordLabel(root=7, quality=types.Quality.MAJOR, start=0.0, duration=dur)]

    # Harp - back and forth (panning left/right logic via two tracks)
    harp_l = ArpeggiatorGenerator(
        GeneratorParams(density=0.2, key_range_low=60, key_range_high=84),
        pattern="up"
    ).render(chords, key, dur)
    
    # Guitar - soft response
    guitar = ArpeggiatorGenerator(
        GeneratorParams(density=0.15, key_range_low=48, key_range_high=72),
        pattern="down"
    ).render(chords, key, dur)

    # Strings
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.05, key_range_low=36, key_range_high=60),
    ).render(chords, key, dur)

    tracks = {"harp": harp_l, "guitar": guitar, "strings": strings}
    inst = {"harp": HARP, "guitar": NYLON_GUITAR, "strings": 49}
    _export(tracks, OUT / "02_Anuloma.mid", bpm, key, inst)

# =====================================================================
# III. Kumbhaka — D Dorian, 48 BPM
# =====================================================================
def produce_kumbhaka():
    print("--- 03_Kumbhaka ---")
    bpm = 48
    dur = 192.0
    key = types.Scale(2, types.Mode.DORIAN)
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # Space Pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, key_range_low=36, key_range_high=72)
    ).render(chords, key, dur)

    # Piano - very sparse, echoing
    piano = MelodyGenerator(
        GeneratorParams(density=0.04, velocity_range=(30, 50)),
        phrase_length=16.0,
        note_range_low=60, note_range_high=84
    ).render(chords, key, dur)

    # Bowl - marking the hold periods (every 16 beats)
    bowl = [types.NoteInfo(pitch=74, start=float(i*16), duration=8.0, velocity=85) for i in range(12)]

    tracks = {"pad": pad, "piano": piano, "bowl": bowl}
    inst = {"pad": PAD_SPACE, "piano": PIANO, "bowl": BOWL}
    _export(tracks, OUT / "03_Kumbhaka.mid", bpm, key, inst)

# =====================================================================
# IV. Kapalabhati — E Phrygian Dominant, 120 BPM
# =====================================================================
def produce_kapalabhati():
    print("--- 04_Kapalabhati ---")
    bpm = 120
    dur = 160.0
    key = types.Scale(4, types.Mode.PHRYGIAN_DOMINANT)
    chords = [types.ChordLabel(root=4, quality=types.Quality.MAJOR, start=0.0, duration=dur)]

    # Percussion - Sharp exhales (shaker/perc)
    perc = ElectronicDrumsGenerator(
        GeneratorParams(density=0.8, velocity_range=(60, 95)),
        pattern="light"
    ).render(chords, key, dur)

    # Bass - steady drive
    bass = DroneGenerator(
        GeneratorParams(density=0.2, key_range_low=28, key_range_high=29),
        velocity=70
    ).render(chords, key, dur)

    # Sitar-like melody
    sitar = MelodyGenerator(
        GeneratorParams(density=0.4, velocity_range=(70, 100)),
        phrase_length=4.0,
        note_range_low=64, note_range_high=88,
        ornament_probability=0.4
    ).render(chords, key, dur)

    tracks = {"perc": perc, "bass": bass, "sitar": sitar}
    inst = {"perc": SHAKER, "bass": 38, "sitar": 104}
    _export(tracks, OUT / "04_Kapalabhati.mid", bpm, key, inst)

# =====================================================================
# V. Bhramari — B Locrian (Nat 2), 52 BPM
# =====================================================================
def produce_bhramari():
    print("--- 05_Bhramari ---")
    bpm = 52
    dur = 208.0
    # Locrian Nat 2 is Aeolian b5 essentially
    key = types.Scale(11, types.Mode.LOCRIAN_NAT_2)
    chords = [types.ChordLabel(root=11, quality=types.Quality.DIMINISHED, start=0.0, duration=dur)]

    # Drone - Humming feel (Low Voice + Pad)
    voice = DroneGenerator(
        GeneratorParams(density=0.1, key_range_low=47, key_range_high=59),
        velocity=40
    ).render(chords, key, dur)

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.08, key_range_low=59, key_range_high=71)
    ).render(chords, key, dur)

    # Cello solo
    cello = MelodyGenerator(
        GeneratorParams(density=0.1, velocity_range=(35, 55)),
        phrase_length=12.0,
        note_range_low=48, note_range_high=64
    ).render(chords, key, dur)

    tracks = {"voice": voice, "pad": pad, "cello": cello}
    inst = {"voice": CHOIR, "pad": PAD_WARM, "cello": CELLO}
    _export(tracks, OUT / "05_Bhramari.mid", bpm, key, inst)

# =====================================================================
# VI. Sama Vritti — F Lydian, 64 BPM
# =====================================================================
def produce_sama_vritti():
    print("--- 06_SamaVritti ---")
    bpm = 64
    dur = 256.0
    key = types.Scale(5, types.Mode.LYDIAN)
    chords = [types.ChordLabel(root=5, quality=types.Quality.MAJOR, start=0.0, duration=dur)]

    # Piano - Square, steady 4-beat phrases
    piano = MelodyGenerator(
        GeneratorParams(density=0.25, velocity_range=(50, 70)),
        phrase_length=4.0,
        note_range_low=65, note_range_high=81
    ).render(chords, key, dur)

    # Harp - steady eighths
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(45, 65)),
        pattern="up_down", note_duration=0.5
    ).render(chords, key, dur)

    # Bass - every downbeat
    bass = [types.NoteInfo(pitch=41, start=float(i*4), duration=3.5, velocity=50) for i in range(64)]

    tracks = {"piano": piano, "harp": harp, "bass": bass}
    inst = {"piano": PIANO, "harp": HARP, "bass": 32}
    _export(tracks, OUT / "06_SamaVritti.mid", bpm, key, inst)

# =====================================================================
# VII. Shavasana — C Overtone, 40 BPM
# =====================================================================
def produce_shavasana():
    print("--- 07_Shavasana ---")
    bpm = 40
    dur = 480.0
    key = types.Scale(0, types.Mode.ACOUSTIC_MAJOR)
    chords = [types.ChordLabel(root=0, quality=types.Quality.MAJOR, start=0.0, duration=dur)]

    # Deepest Pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=36, key_range_high=72)
    ).render(chords, key, dur)

    # Choir - "Infinite"
    choir = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=60, key_range_high=72),
        velocity=30
    ).render(chords, key, dur)

    # Final Bowl at the very end
    bowl = [types.NoteInfo(pitch=60, start=dur-10.0, duration=10.0, velocity=70)]

    tracks = {"pad": pad, "choir": choir, "bowl": bowl}
    inst = {"pad": PAD_SPACE, "choir": CHOIR, "bowl": BOWL}
    _export(tracks, OUT / "07_Shavasana.mid", bpm, key, inst)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   PRĀṆA — ПРАНА — ДЫХАНИЕ ЖИЗНИ")
print("   7-Track Breath Meditation Album")
print("=" * 60)

produce_ujjayi()
produce_anuloma()
produce_kumbhaka()
produce_kapalabhati()
produce_bhramari()
produce_sama_vritti()
produce_shavasana()

print("\n" + "=" * 60)
print("   PRĀṆA — COMPLETE.")
print(f"   Files generated in: {OUT}")
print("=" * 60)
