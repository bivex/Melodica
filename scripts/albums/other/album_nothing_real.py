# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_nothing_real.py — НИЧЕГО НАСТОЯЩЕГО (Nothing Real)

Based on Terry Pratchett's «Mort» — Death's domain, the garden, the arch-fly.

Scale: D Byzantine / Double Harmonic [0, 1, 4, 5, 7, 8, 11]
       (same intervals as D Hungarian Minor shifted — both exotic, dark, regal)
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
import math
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.plucked_solo import PianoSoloGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# D Byzantine / Double Harmonic (D-Eb-G-A-Bb-C#) — dark, exotic, regal
KEY = types.Scale(root=2, mode=types.Mode.BYZANTINE)

# GM Programs
HARPSICHORD = 6
CONTRABASS = 43
CELLO = 42
VIOLA = 41
FLUTE = 73
BASSOON = 70
CLARINET = 71
PIANO = 1
HARP = 46
CHOIR = 52
VOICE_OOH = 53
BANJO = 105
BOWED_GLASS = 92
PAD_CHOIR = 91
PAD_WARM = 89
STRING_ENS = 48
TIMPANI = 47
XYLOPHONE = 13

random.seed(666)
OUT = Path("output/album_nothing_real")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "harpsichord": 0.75, "bass": 0.55, "lead": 0.80,
        "strings": 0.65, "flute": 0.70, "cello": 0.60,
        "viola": 0.55, "voice": 0.50, "pad": 0.35,
        "choir": 0.45, "perc": 0.70, "harp": 0.60,
        "banjo": 0.55, "glass": 0.45,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict,
            lufs: float = -16.0):
    final_notes, cc_events = _master(tracks, bpm, lufs=lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. Кабинет (The Study) — 72 BPM
# Death tying flies at his desk. Harpsichord precision, bone fingers.
# =====================================================================
def produce_study():
    print("--- 01_The_Study ---")
    bpm = 72
    dur = 180.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR, start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    # Harpsichord: precise, methodical arpeggios (mid register)
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.45, velocity_range=(55, 80)),
        pattern="up_down", note_duration=0.25
    ).render(chords, KEY, dur)

    # Contrabass: slow pedal tones (gravity of Death)
    bass = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=28, key_range_high=40),
        velocity=45
    ).render(chords, KEY, dur)

    # Xylophone: dry clicks — bone on bone, tying flies
    clicks = []
    t = 2.0
    while t < dur:
        clicks.append(types.NoteInfo(pitch=random.choice([74, 76, 79]),
                                     start=t, duration=0.08,
                                     velocity=random.randint(50, 70)))
        t += random.uniform(3.0, 8.0)

    # Sparse piano — isolated introspective notes between harpsichord phrases
    piano_sparse = PianoSoloGenerator(
        GeneratorParams(density=0.06, velocity_range=(25, 45), key_range_low=48, key_range_high=72)
    ).render(chords, KEY, dur)

    # Distant choir murmur — barely audible existential presence
    choir_distant = ChoirAahsGenerator(
        GeneratorParams(density=0.02, velocity_range=(20, 35), key_range_low=48, key_range_high=60)
    ).render(chords, KEY, dur)

    tracks = {"harpsichord": harp, "bass": bass, "perc": clicks,
              "piano": piano_sparse, "choir": choir_distant}
    inst = {"harpsichord": HARPSICHORD, "bass": CONTRABASS, "perc": XYLOPHONE,
            "piano": PIANO, "choir": CHOIR}
    _export(tracks, OUT / "01_The_Study.mid", bpm, inst, lufs=-18.0)

# =====================================================================
# II. Слава Смерти (Glory of Death) — 108 BPM
# The arch-fly. Primal, ancient, teeth and venom. Aggressive.
# =====================================================================
def produce_glory():
    print("--- 02_Glory_of_Death ---")
    bpm = 108
    dur = 200.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    # Lead: aggressive, angular (high register, high density)
    lead = MelodyGenerator(
        GeneratorParams(density=0.7, complexity=0.95, velocity_range=(90, 120)),
        phrase_length=8.0, note_range_low=62, note_range_high=91,
        steps_probability=0.3, random_movement=0.35
    ).render(chords[4:], KEY, dur - 16.0)

    # Strings: tense tremolo backdrop
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, velocity_range=(60, 85)),
        section_size=6, articulation="tremolo"
    ).render(chords, KEY, dur)

    # Active bass line
    bass = BassGenerator(
        GeneratorParams(density=0.5, velocity_range=(85, 105),
                        key_range_low=28, key_range_high=45),
        style="walking"
    ).render(chords, KEY, dur)

    # Percussion: irregular thuds (the fly hitting walls)
    perc = []
    for i in range(int(dur / 2)):
        t = i * 2.0 + random.uniform(-0.3, 0.3)
        if random.random() < 0.4:
            perc.append(types.NoteInfo(36, t, 0.15, random.randint(80, 105)))

    tracks = {
        "lead": _off(lead, 16.0),
        "strings": strings, "bass": bass, "perc": perc
    }
    inst = {
        "lead": BOWED_GLASS, "strings": STRING_ENS,
        "bass": CELLO, "perc": TIMPANI
    }
    _export(tracks, OUT / "02_Glory_of_Death.mid", bpm, inst, lufs=-14.0)

# =====================================================================
# III. Библиотека (The Library) — 48 BPM
# Books about young women. Whispers between shelves. Forbidden.
# =====================================================================
def produce_library():
    print("--- 03_The_Library ---")
    bpm = 48
    dur = 160.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    # Soft flute: whispered melody, low register
    flute = MelodyGenerator(
        GeneratorParams(density=0.08, complexity=0.5, velocity_range=(30, 50)),
        phrase_length=20.0, note_range_low=55, note_range_high=67,
        ornament_probability=0.15
    ).render(chords, KEY, dur)

    # Choir pad: distant murmurs
    choir = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=48, key_range_high=60),
        voicing="cluster"
    ).render(chords, KEY, dur)

    # Isolated piano notes: pages turning
    piano = []
    t = 8.0
    while t < dur - 8.0:
        piano.append(types.NoteInfo(
            pitch=random.choice([50, 53, 57, 62, 65]),
            start=t, duration=0.3, velocity=random.randint(25, 40)
        ))
        t += random.uniform(5.0, 15.0)

    # Sparse piano — pages turning, single notes like footsteps between shelves
    piano_pages = PianoSoloGenerator(
        GeneratorParams(density=0.04, velocity_range=(20, 35), key_range_low=48, key_range_high=72)
    ).render(chords, KEY, dur)

    # Wider choir — the forbidden whispers fill the stacks
    choir_whisper = ChoirAahsGenerator(
        GeneratorParams(density=0.025, velocity_range=(18, 30), key_range_low=48, key_range_high=64)
    ).render(chords, KEY, dur)

    tracks = {"flute": flute, "choir": choir, "perc": piano,
              "piano": piano_pages, "choir2": choir_whisper}
    inst = {"flute": FLUTE, "choir": PAD_CHOIR, "perc": PIANO,
            "piano": PIANO, "choir2": CHOIR}
    _export(tracks, OUT / "03_The_Library.mid", bpm, inst, lufs=-20.0)

# =====================================================================
# IV. Чёрный газон (The Black Lawn) — 88 BPM
# Mort and Isabel bicker. Pizzicato spar. Awkward dance.
# =====================================================================
def produce_lawn():
    print("--- 04_The_Black_Lawn ---")
    bpm = 88
    dur = 220.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 4.0), duration=4.0)
              for i in range(int(dur / 4.0))]

    # Viola pizzicato: Isabel's sharp retorts
    viola = MelodyGenerator(
        GeneratorParams(density=0.4, complexity=0.7, velocity_range=(70, 95)),
        phrase_length=4.0, note_range_low=48, note_range_high=65,
        syncopation=0.5
    ).render(chords, KEY, dur)

    # Clarinet: Mort's clumsy replies
    clarinet = MelodyGenerator(
        GeneratorParams(density=0.35, complexity=0.6, velocity_range=(65, 90)),
        phrase_length=4.0, note_range_low=50, note_range_high=67,
        syncopation=0.3
    ).render(chords[8:], KEY, dur - 32.0)

    # Light arpeggiated backdrop (the garden)
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.25, velocity_range=(40, 60)),
        pattern="up", note_duration=0.5
    ).render(chords, KEY, dur)

    tracks = {
        "viola": viola,
        "lead": _off(clarinet, 32.0),
        "harp": harp
    }
    inst = {"viola": VIOLA, "lead": CLARINET, "harp": HARP}
    _export(tracks, OUT / "04_The_Black_Lawn.mid", bpm, inst, lufs=-17.0)

# =====================================================================
# V. Каменный лев (The Stone Lion) — 52 BPM
# The pond. Icy spring. Fat white carp. Black velvet lily pads.
# =====================================================================
def produce_lion():
    print("--- 05_The_Stone_Lion ---")
    bpm = 52
    dur = 240.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    # Glass harmonica pad: icy, still water
    glass = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=72, key_range_high=96),
        voicing="open"
    ).render(chords, KEY, dur)

    # Cello: deep, slow — the carp in the depths
    cello = MelodyGenerator(
        GeneratorParams(density=0.06, complexity=0.4, velocity_range=(40, 60)),
        phrase_length=24.0, note_range_low=36, note_range_high=52,
        ornament_probability=0.1
    ).render(chords, KEY, dur)

    # Harp: lily pads, gentle ripples
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, velocity_range=(30, 50)),
        pattern="converge", note_duration=1.0
    ).render(chords, KEY, dur)

    # Timpani: the stone lion retching water (rare, low)
    lion = []
    for t in [30.0, 90.0, 150.0, 210.0]:
        lion.append(types.NoteInfo(36, t, 2.0, 55))
        lion.append(types.NoteInfo(38, t + 0.5, 1.0, 45))

    tracks = {"pad": glass, "cello": cello, "harp": harp, "perc": lion}
    inst = {"pad": BOWED_GLASS, "cello": CELLO, "harp": HARP, "perc": TIMPANI}
    _export(tracks, OUT / "05_The_Stone_Lion.mid", bpm, inst, lufs=-20.0)

# =====================================================================
# VI. Рукопожатие (The Handshake) — 60 BPM
# The moment of truce. Sitting on the stone bench. Grateful silence.
# =====================================================================
def produce_handshake():
    print("--- 06_The_Handshake ---")
    bpm = 60
    dur = 200.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=float(i * 8.0), duration=8.0)
              for i in range(int(dur / 8.0))]

    # Cello: warm, singing — the human moment
    cello = MelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.65, velocity_range=(60, 85)),
        phrase_length=8.0, note_range_low=36, note_range_high=56,
        steps_probability=0.5, ornament_probability=0.1
    ).render(chords, KEY, dur)

    # Strings: gentle sustains
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.15, velocity_range=(35, 55)),
        section_size=4, articulation="legato"
    ).render(chords, KEY, dur)

    # Voice (ooh): Isabel, barely audible
    voice = MelodyGenerator(
        GeneratorParams(density=0.05, complexity=0.3, velocity_range=(25, 40)),
        phrase_length=16.0, note_range_low=57, note_range_high=69
    ).render(chords[6:], KEY, dur - 48.0)

    # Sparse piano — the human moment, warm single notes under the cello
    piano_bench = PianoSoloGenerator(
        GeneratorParams(density=0.08, velocity_range=(30, 50), key_range_low=48, key_range_high=72)
    ).render(chords, KEY, dur)

    # Choir aahs — Isabel's presence, distant and grateful
    choir_bench = ChoirAahsGenerator(
        GeneratorParams(density=0.03, velocity_range=(22, 38), key_range_low=52, key_range_high=68)
    ).render(chords, KEY, dur)

    tracks = {
        "cello": cello, "strings": strings,
        "voice": _off(voice, 48.0),
        "piano": piano_bench, "choir": choir_bench
    }
    inst = {"cello": CELLO, "strings": STRING_ENS, "voice": VOICE_OOH,
            "piano": PIANO, "choir": CHOIR}
    _export(tracks, OUT / "06_The_Handshake.mid", bpm, inst, lufs=-18.0)

# =====================================================================
# VII. Ничего настоящего (Nothing Real) — 40 BPM
# "Here there is nothing really real." Dissolution. Banjo in the distance.
# =====================================================================
def produce_nothing_real():
    print("--- 07_Nothing_Real ---")
    bpm = 40
    dur = 320.0
    chords = [types.ChordLabel(root=2, quality=types.Quality.MINOR,
                               start=0.0, duration=dur)]

    # Choir pad: vast, empty domain
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=48, key_range_high=72),
        voicing="open"
    ).render(chords, KEY, dur)

    # Flute: distant, fading melody
    flute = MelodyGenerator(
        GeneratorParams(density=0.04, complexity=0.4, velocity_range=(25, 45)),
        phrase_length=24.0, note_range_low=60, note_range_high=79
    ).render(chords, KEY, 240.0)

    # Banjo: Death trying to be human — clumsy, faint, in the last 60 seconds
    banjo = MelodyGenerator(
        GeneratorParams(density=0.15, complexity=0.3, velocity_range=(30, 50)),
        phrase_length=4.0, note_range_low=55, note_range_high=72,
        steps_probability=0.6
    ).render(chords, KEY, 60.0)

    # Single unison note: everything dissolves
    dissolve = types.NoteInfo(pitch=50, start=280.0, duration=40.0, velocity=30)

    tracks = {
        "pad": pad + [dissolve],
        "flute": flute + [dissolve],
        "banjo": _off(banjo, 260.0) + [dissolve]
    }
    inst = {"pad": PAD_CHOIR, "flute": FLUTE, "banjo": BANJO}
    _export(tracks, OUT / "07_Nothing_Real.mid", bpm, inst, lufs=-22.0)

# =====================================================================
# EXECUTION
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
