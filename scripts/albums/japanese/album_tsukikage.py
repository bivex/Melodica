# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_tsukikage.py — 月影 (Tsukikage — Лунная тень)

Scale: Kumoi [0, 2, 3, 7, 9]
Характер: Тишина, холодный воздух, недосказанность, красота пустоты.

  I.   霞 (Kasumi — Туман)         — 42 BPM. Сякухати и Кото.
  II.  水鏡 (Mizukagami — Зеркало) — 58 BPM, 3/4. Арфа и Голос.
  III. 孤独 (Kodoku — Одиночество) — 64 BPM, 5/4. Препарированное пианино.
  IV.  白い鳥 (Shiroi Tori — Птица) — 72 BPM, 4/4. Кото-виртуозность.
  V.   影法師 (Kagebōshi — Тень)   — 50 BPM. Виолончель и голос.
  VI.  雪庭 (Yukiniwa — Сад)       — Free. Резонанс и текстура.
  VII. 月影 (Tsukikage — Лунная тень) — 48 BPM. Финальное растворение.
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
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# KEY: A Kumoi (A-B-C-E-F#) - standard evocative key
KEY = types.Scale(root=9, mode=types.Mode.KUMOI)

# GM Programs
SHAKUHACHI = 77
KOTO = 107
HARP = 46
VIOLA = 41
CELLO = 42
CONTRABASS = 43
PIANO = 1 # Acoustic Grand (used as prepared)
VOICE_OOH = 53
CHOIR = 52
BOWL = 14
BELLS = 14
PAD_SPACE = 91
PAD_WARM = 89

random.seed(444)
OUT = Path("output/album_tsukikage")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]

def _master(raw: dict, bpm: float, lufs: float = -18.0):
    desk = MixingDesk(niche_cfg={})
    # Minimal gains for transparency
    desk.track_gains.update({
        "shakuhachi": 0.8, "koto": 0.7, "harp": 0.65, "viola": 0.5,
        "voice": 0.55, "piano": 0.6, "bass": 0.45, "cello": 0.5,
        "pad": 0.35, "bowl": 0.75, "bells": 0.4
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict):
    final_notes, cc_events = _master(tracks, bpm)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

# =====================================================================
# I. 霞 (Kasumi — Туман) — 42 BPM
# =====================================================================
def produce_kasumi():
    print("--- 01_Kasumi ---")
    bpm = 42
    dur = 160.0
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # Shakuhachi - long notes with air
    flute = MelodyGenerator(
        GeneratorParams(density=0.04, velocity_range=(35, 55)),
        phrase_length=16.0, # 4-5s silence logic handled by low density
        note_range_low=69, note_range_high=81
    ).render(chords, KEY, dur)

    # Koto - short high responses
    koto = MelodyGenerator(
        GeneratorParams(density=0.03, velocity_range=(40, 60)),
        phrase_length=32.0, note_range_low=81, note_range_high=93
    ).render(chords, KEY, dur)

    # Soft Wind Pad
    wind = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=57, key_range_high=58),
        velocity=25
    ).render(chords, KEY, dur)

    tracks = {"shakuhachi": flute, "koto": koto, "pad": wind}
    inst = {"shakuhachi": SHAKUHACHI, "koto": KOTO, "pad": PAD_WARM}
    _export(tracks, OUT / "01_Kasumi.mid", bpm, inst)

# =====================================================================
# II. 水鏡 (Mizukagami — Водяное зеркало) — 58 BPM, 3/4
# =====================================================================
def produce_mizukagami():
    print("--- 02_Mizukagami ---")
    bpm = 58
    dur = 150.0
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # Harp - 3 note pattern
    harp = ArpeggiatorGenerator(
        GeneratorParams(density=0.3, velocity_range=(40, 55)),
        pattern="up", note_duration=1.0 # One note per bar approx
    ).render(chords, KEY, dur)

    # Viola Harmonics
    viola = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=69, key_range_high=81),
        velocity=30
    ).render(chords, KEY, dur)

    # Voice - whisper a cappella bridge at beat 60
    voice = MelodyGenerator(
        GeneratorParams(density=0.1, velocity_range=(30, 45)),
        phrase_length=12.0, note_range_low=60, note_range_high=72
    ).render(chords, KEY, dur)
    
    # Silence all around voice bridge
    harp = [n for n in harp if n.start < 60 or n.start > 84]
    viola = [n for n in viola if n.start < 60 or n.start > 84]

    tracks = {"harp": harp, "viola": viola, "voice": voice}
    inst = {"harp": HARP, "viola": VIOLA, "voice": VOICE_OOH}
    _export(tracks, OUT / "02_Mizukagami.mid", bpm, inst)

# =====================================================================
# III. 孤独 (Kodoku — Одиночество) — 64 BPM, 5/4
# =====================================================================
def produce_kodoku():
    print("--- 03_Kodoku ---")
    bpm = 64
    dur = 160.0
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # Prepared Piano - Short, dry notes
    # Space between phrases decreases
    piano_notes = []
    t = 5.0
    step = 10.0
    while t < dur:
        piano_notes.append(types.NoteInfo(pitch=random.choice([57, 60, 69]), start=t, duration=0.1, velocity=50))
        t += step
        step = max(2.0, step * 0.9) # space shrinks

    # Double Bass arco
    bass = DroneGenerator(
        GeneratorParams(density=0.01, key_range_low=33, key_range_high=45),
        velocity=35
    ).render(chords, KEY, dur)

    # Shakuhachi fragments
    flute = MelodyGenerator(
        GeneratorParams(density=0.05, velocity_range=(35, 50)),
        phrase_length=5.0, note_range_low=69, note_range_high=76
    ).render(chords, KEY, dur)

    tracks = {"piano": piano_notes, "bass": bass, "shakuhachi": flute}
    inst = {"piano": PIANO, "bass": CONTRABASS, "shakuhachi": SHAKUHACHI}
    _export(tracks, OUT / "03_Kodoku.mid", bpm, inst)

# =====================================================================
# IV. 白い鳥 (Shiroi Tori — Белая птица) — 72 BPM
# =====================================================================
def produce_bird():
    print("--- 04_Shiroi_Tori ---")
    bpm = 72
    dur = 240.0
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # Koto - fast ascending runs
    koto = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, velocity_range=(60, 90)),
        pattern="up_down_full", note_duration=0.25
    ).render(chords, KEY, dur)

    # Virtuoso run at 2:50 (beat 204 at 72bpm)
    run = ArpeggiatorGenerator(
        GeneratorParams(density=0.9, key_range_low=57, key_range_high=105, velocity_range=(100, 115)),
        pattern="up", note_duration=0.125
    ).render(chords[-4:], KEY, 16.0)

    # String Quartet accents
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.15, velocity_range=(45, 70)),
    ).render(chords, KEY, dur)

    # Woodblocks
    blocks = [types.NoteInfo(pitch=76, start=float(i*2), duration=0.1, velocity=60) for i in range(120)]

    tracks = {"koto": koto + _off(run, 204.0), "strings": strings, "perc": blocks}
    inst = {"koto": KOTO, "strings": 49, "perc": 115}
    _export(tracks, OUT / "04_Shiroi_Tori.mid", bpm, inst)

# =====================================================================
# V. 影法師 (Kagebōshi — Тень) — 50 BPM
# =====================================================================
def produce_kageboshi():
    print("--- 05_Kageboshi ---")
    bpm = 50
    dur = 280.0
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # Interleaved Cello and Voice
    cello_notes = []
    voice_notes = []
    t = 0.0
    while t < 240:
        # Cello phrase
        cello_phrase = MelodyGenerator(GeneratorParams(density=0.2), note_range_low=45, note_range_high=57).render(chords, KEY, 10.0)
        cello_notes.extend(_off(cello_phrase, t))
        t += 15.0 # silence gap
        # Voice phrase
        voice_phrase = MelodyGenerator(GeneratorParams(density=0.15), note_range_low=57, note_range_high=69).render(chords, KEY, 10.0)
        voice_notes.extend(_off(voice_phrase, t))
        t += 15.0

    # Unison note at 4:00 (beat 200)
    unison = types.NoteInfo(pitch=57, start=200.0, duration=8.0, velocity=50)
    cello_notes.append(unison)
    voice_notes.append(unison)

    tracks = {"cello": cello_notes, "voice": voice_notes}
    inst = {"cello": CELLO, "voice": CHOIR}
    _export(tracks, OUT / "05_Kageboshi.mid", bpm, inst)

# =====================================================================
# VI. 雪庭 (Yukiniwa — Снежный сад) — 10 Minutes
# =====================================================================
def produce_yukiniwa():
    print("--- 06_Yukiniwa ---")
    bpm = 40
    dur = 400.0 # ~10 mins
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # High Synth Space Pad
    pad = AmbientPadGenerator(
        GeneratorParams(density=0.05, key_range_low=81, key_range_high=105),
        voicing="open"
    ).render(chords, KEY, dur)

    # Sparse Singing Bowls
    bowls = []
    for i in range(20):
        bowls.append(types.NoteInfo(pitch=random.choice([69, 72, 81]), 
                                    start=random.uniform(0, dur), 
                                    duration=15.0, velocity=40))

    tracks = {"pad": pad, "bowl": bowls}
    inst = {"pad": PAD_SPACE, "bowl": BOWL}
    _export(tracks, OUT / "06_Yukiniwa.mid", bpm, inst)

# =====================================================================
# VII. 月影 (Tsukikage — Лунная тень) — 48 BPM
# =====================================================================
def produce_tsukikage():
    print("--- 07_Tsukikage ---")
    bpm = 48
    dur = 360.0
    chords = [types.ChordLabel(root=9, quality=types.Quality.MINOR, start=0.0, duration=dur)]

    # 20s Unison at 5:30 (beat 264 at 48bpm)
    u_note = types.NoteInfo(pitch=69, start=264.0, duration=20.0, velocity=60)
    
    # Combined fade out
    flute = MelodyGenerator(GeneratorParams(density=0.05)).render(chords, KEY, 300.0)
    koto = ArpeggiatorGenerator(GeneratorParams(density=0.1), pattern="random").render(chords, KEY, 260.0)
    voice = MelodyGenerator(GeneratorParams(density=0.08)).render(chords, KEY, 280.0)
    harp = ArpeggiatorGenerator(GeneratorParams(density=0.1)).render(chords, KEY, 240.0)

    tracks = {
        "shakuhachi": flute + [u_note],
        "koto": koto + [u_note],
        "voice": voice + [u_note],
        "harp": harp + [u_note],
        "cello": [u_note]
    }
    inst = {"shakuhachi": SHAKUHACHI, "koto": KOTO, "voice": VOICE_OOH, "harp": HARP, "cello": CELLO}
    _export(tracks, OUT / "07_Tsukikage.mid", bpm, inst)

# =====================================================================
# EXECUTION
# =====================================================================
print("=" * 60)
print("   月影 — TSUKIKAGE — MOON SHADOW")
print("   Kumoi Scale Meditation")
print("=" * 60)

produce_kasumi()
produce_mizukagami()
produce_kodoku()
produce_bird()
produce_kageboshi()
produce_yukiniwa()
produce_tsukikage()

print("\n" + "=" * 60)
print("   月影 — COMPLETE.")
print(f"   Files in: {OUT}")
print("=" * 60)
