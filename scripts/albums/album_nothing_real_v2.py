# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_nothing_real.py — НИЧЕГО НАСТОЯЩЕГО (Nothing Real)

Based on Terry Pratchett's «Mort» — Death's domain, the garden, the arch-fly.

Scale: D Byzantine / Double Harmonic [0, 1, 4, 5, 7, 8, 11]
Характер: Дом Смерти. Мастерство и пустота. Неловкая нежность. Нереальность.

  I.   Кабинет (The Study)          — 72 BPM. Клавесин, контрабас, сухие мухи.
  II.  Слава Смерти (Glory of Death)— 108 BPM. Архимуха — примитивная ярость.
  III. Библиотека (The Library)     — 48 BPM. Шёпот, запретное, стеллажи.
  IV.  Чёрный газон (The Black Lawn)— 88 BPM. Пиццикато, флейта, перепалка.
  V.   Каменный лев (The Stone Lion)— 52 BPM. Пруд, карп, кувшинки.
  VI.  Рукопожатие (The Handshake)  — 60 BPM. Виолончель, тепло.
  VII. Ничего настоящего (Nothing Real) — 40 BPM. Растворение.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.composer.album_pipeline import produce_track, Mood

KEY = types.Scale(root=2, mode=types.Mode.BYZANTINE)

random.seed(666)
OUT = Path("output/album_nothing_real_v2")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


# =====================================================================
# I. Кабинет — 72 BPM
# =====================================================================
def produce_study():
    bpm, dur = 72, 180.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.45, velocity_range=(55, 80)),
        pattern="up_down", note_duration=0.25
    ).render(chords, KEY, dur)

    bass = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=28, key_range_high=40),
        velocity=45
    ).render(chords, KEY, dur)

    clicks = []
    t = 2.0
    while t < dur:
        clicks.append(types.NoteInfo(pitch=random.choice([74, 76, 79]),
                                     start=t, duration=0.08,
                                     velocity=random.randint(50, 70)))
        t += random.uniform(3.0, 8.0)

    produce_track(
        tracks={"harpsichord": harp, "bass": bass, "perc": clicks},
        bpm=bpm,
        instruments={"harpsichord": 6, "bass": 43, "perc": 13},
        path=OUT / "01_The_Study.mid",
        mood=Mood.CHAMBER, key=KEY,
    )


# =====================================================================
# II. Слава Смерти — 108 BPM
# =====================================================================
def produce_glory():
    bpm, dur = 108, 200.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    lead = MelodyGenerator(
        GeneratorParams(density=0.7, complexity=0.95, velocity_range=(90, 120)),
        phrase_length=8.0, note_range_low=62, note_range_high=91,
        steps_probability=0.3, random_movement=0.35
    ).render(chords[4:], KEY, dur - 16.0)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, velocity_range=(60, 85)),
        section_size=6, articulation="tremolo"
    ).render(chords, KEY, dur)

    bass = BassGenerator(
        GeneratorParams(density=0.5, velocity_range=(85, 105),
                        key_range_low=28, key_range_high=45),
        style="walking"
    ).render(chords, KEY, dur)

    perc = []
    for i in range(int(dur / 2)):
        t = i * 2.0 + random.uniform(-0.3, 0.3)
        if random.random() < 0.4:
            perc.append(types.NoteInfo(36, t, 0.15, random.randint(80, 105)))

    produce_track(
        tracks={"lead": _off(lead, 16.0), "strings": strings,
                "bass": bass, "perc": perc},
        bpm=bpm,
        instruments={"lead": 92, "strings": 48, "bass": 42, "perc": 47},
        path=OUT / "02_Glory_of_Death.mid",
        mood=Mood.AGGRESSIVE, key=KEY,
    )


# =====================================================================
# III. Библиотека — 48 BPM
# =====================================================================
def produce_library():
    bpm, dur = 48, 160.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    flute = MelodyGenerator(
        GeneratorParams(density=0.08, complexity=0.5, velocity_range=(30, 50)),
        phrase_length=20.0, note_range_low=55, note_range_high=67,
        ornament_probability=0.15
    ).render(chords, KEY, dur)

    choir = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=48, key_range_high=60),
        voicing="cluster"
    ).render(chords, KEY, dur)

    piano = []
    t = 8.0
    while t < dur - 8.0:
        piano.append(types.NoteInfo(
            pitch=random.choice([50, 53, 57, 62, 65]),
            start=t, duration=0.3, velocity=random.randint(25, 40)))
        t += random.uniform(5.0, 15.0)

    produce_track(
        tracks={"flute": flute, "choir": choir, "piano": piano},
        bpm=bpm,
        instruments={"flute": 73, "choir": 91, "piano": 1},
        path=OUT / "03_The_Library.mid",
        mood=Mood.AMBIENT, key=KEY,
    )


# =====================================================================
# IV. Чёрный газон — 88 BPM
# =====================================================================
def produce_lawn():
    bpm, dur = 88, 220.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    viola = MelodyGenerator(
        GeneratorParams(density=0.4, complexity=0.7, velocity_range=(70, 95)),
        phrase_length=4.0, note_range_low=48, note_range_high=65,
        syncopation=0.5
    ).render(chords, KEY, dur)

    clarinet = MelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.6, velocity_range=(65, 90)),
        phrase_length=4.0, note_range_low=50, note_range_high=67,
        syncopation=0.3
    ).render(chords[8:], KEY, dur - 32.0)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.25, velocity_range=(40, 60)),
        pattern="up", note_duration=0.5
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"viola": viola, "clarinet": _off(clarinet, 32.0), "harp": harp},
        bpm=bpm,
        instruments={"viola": 41, "clarinet": 71, "harp": 46},
        path=OUT / "04_The_Black_Lawn.mid",
        mood=Mood.CHAMBER, key=KEY,
    )


# =====================================================================
# V. Каменный лев — 52 BPM
# =====================================================================
def produce_lion():
    bpm, dur = 52, 240.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    glass = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=72, key_range_high=96),
        voicing="open"
    ).render(chords, KEY, dur)

    cello = MelodyGenerator(
        GeneratorParams(density=0.06, complexity=0.4, velocity_range=(40, 60)),
        phrase_length=24.0, note_range_low=36, note_range_high=52,
        ornament_probability=0.1
    ).render(chords, KEY, dur)

    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, velocity_range=(30, 50)),
        pattern="converge", note_duration=1.0
    ).render(chords, KEY, dur)

    lion = []
    for t in [30.0, 90.0, 150.0, 210.0]:
        lion.append(types.NoteInfo(36, t, 2.0, 55))
        lion.append(types.NoteInfo(38, t + 0.5, 1.0, 45))

    produce_track(
        tracks={"glass_pad": glass, "cello": cello, "harp": harp, "lion": lion},
        bpm=bpm,
        instruments={"glass_pad": 92, "cello": 42, "harp": 46, "lion": 47},
        path=OUT / "05_The_Stone_Lion.mid",
        mood=Mood.AMBIENT, key=KEY,
    )


# =====================================================================
# VI. Рукопожатие — 60 BPM
# =====================================================================
def produce_handshake():
    bpm, dur = 60, 200.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 8.0), duration=8.0)
              for i in range(int(dur / 8.0))]

    cello = MelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.65, velocity_range=(60, 85)),
        phrase_length=8.0, note_range_low=36, note_range_high=56,
        steps_probability=0.5, ornament_probability=0.1
    ).render(chords, KEY, dur)

    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.15, velocity_range=(35, 55)),
        section_size=4, articulation="legato"
    ).render(chords, KEY, dur)

    voice = MelodyGenerator(
        GeneratorParams(density=0.05, complexity=0.3, velocity_range=(25, 40)),
        phrase_length=16.0, note_range_low=57, note_range_high=69
    ).render(chords[6:], KEY, dur - 48.0)

    produce_track(
        tracks={"cello": cello, "strings": strings, "voice": _off(voice, 48.0)},
        bpm=bpm,
        instruments={"cello": 42, "strings": 48, "voice": 53},
        path=OUT / "06_The_Handshake.mid",
        mood=Mood.INTIMATE, key=KEY,
    )


# =====================================================================
# VII. Ничего настоящего — 40 BPM
# =====================================================================
def produce_nothing_real():
    bpm, dur = 40, 320.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    pad = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=48, key_range_high=72),
        voicing="open"
    ).render(chords, KEY, dur)

    flute = MelodyGenerator(
        GeneratorParams(density=0.04, complexity=0.4, velocity_range=(25, 45)),
        phrase_length=24.0, note_range_low=60, note_range_high=79
    ).render(chords, KEY, 240.0)

    banjo = MelodyGenerator(
        GeneratorParams(density=0.15, complexity=0.3, velocity_range=(30, 50)),
        phrase_length=4.0, note_range_low=55, note_range_high=72,
        steps_probability=0.6
    ).render(chords, KEY, 60.0)

    dissolve = types.NoteInfo(pitch=50, start=280.0, duration=40.0, velocity=30)

    produce_track(
        tracks={"choir_pad": pad + [dissolve],
                "flute": flute + [dissolve],
                "banjo": _off(banjo, 260.0) + [dissolve]},
        bpm=bpm,
        instruments={"choir_pad": 91, "flute": 73, "banjo": 105},
        path=OUT / "07_Nothing_Real.mid",
        mood=Mood.AMBIENT, key=KEY,
    )


# =====================================================================
print("=" * 60)
print("   НИЧЕГО НАСТОЯЩЕГО — NOTHING REAL")
print("   D Byzantine / Double Harmonic")
print("   Based on Terry Pratchett's «Mort»")
print("=" * 60)

produce_study()
produce_glory()
produce_library()
produce_lawn()
produce_lion()
produce_handshake()
produce_nothing_real()

print("\n" + "=" * 60)
print("   НИЧЕГО НАСТОЯЩЕГО — COMPLETE.")
print(f"   Files in: {OUT}")
print("=" * 60)
