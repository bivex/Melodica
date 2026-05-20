# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_jan.py — ДЖАН (جان — Душа)

Maqam Sikah [0, 1.5, 3.5, 5, 7, 8.5, 10.5]
Четвертьтоновые интервалы — ноты которых нет на фортепиано.
Страсть, томление, нежность, боль любви — всё одновременно.

  I.   Лейла      — Первый взгляд. Золотой.
  II.  Ваджд      — Экстаз тоски. Тёмно-синий.
  III. Гыйра      — Ревность. Алый.
  IV.  Шавк       — Томление. Серый.
  V.   Хасрет     — Вечное «между». Пурпурный.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


KEY = types.Scale(root=2, mode=types.Mode.ARABIC_SIKAH)  # D Sikah [0,1.5,3.5,5,7,8.5,10.5]

# GM Programs
OUD = 24       # Acoustic Guitar (nylon)
KANUN = 15     # Dulcimer
NEY = 73       # Flute
CELLO = 43     # Cello
VOX_F = 53     # Voice Oohs
VOX_M = 52     # Choir Aahs
DARBUKA = 118  # Synth Drum
RIQ = 107      # Tambourine
CHOIR = 52     # Choir Aahs
PAD = 88       # New Age Pad

random.seed(42)
OUT = Path("output/album_jan")
OUT.mkdir(parents=True, exist_ok=True)


def _chords(progression: str, duration: float, beats_per_chord: float | None = None):
    parts = progression.split()
    bpc = beats_per_chord if beats_per_chord else duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        c = KEY.parse_roman(p)
        c.start = i * bpc
        c.duration = bpc
        chords.append(c)
    return chords


def _off(notes, offset):
    if offset <= 0:
        return list(notes)
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


def _cut_after(notes, beat):
    return [n for n in notes if n.start < beat]


def _master(raw: dict, bpm: float, lufs: float = -14.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "oud": 0.9, "voice_f": 1.0, "voice_m": 0.85,
        "kanun": 0.6, "ney": 0.8, "cello": 0.55,
        "darbuka": 0.75, "riq": 0.5, "drone": 0.3,
        "choir": 0.65, "strings": 0.5, "arp": 0.55,
    })
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


def _export(tracks: dict, path: Path, bpm: float, instruments: dict, lufs: float = -14.0):
    final_notes, cc_events = _master(tracks, bpm, lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)
    return final_notes


def _print(subtitle, bpm, tracks, path):
    print(f"  {subtitle} [Sikah — {bpm} BPM — D]")
    print(f"    -> {path.name}  ({bpm} BPM, {len(tracks)} tracks)")
    for name, notes in tracks.items():
        print(f"       {name:18s}             {len(notes)} notes")


# ═══════════════════════════════════════════════════════════════════
print("=" * 60)
print("   جان ДЖАН — ДУША")
print("   Maqam Sikah — 5 tracks")
print("   Страсть, томление, нежность, боль любви")
print("=" * 60)
print()


# =====================================================================
# Track I — Лейла (ليلى)
# 84 BPM, 4/4 — Первый взгляд. Момент, когда всё изменилось.
# Intro: ud taksim → Verse: voice + kanun → Bridge: voice high → Outro: ud
# =====================================================================
def produce_leyla():
    """Первый взгляд. Золотой."""
    print("--- 01_Leyla_Лейла ---")
    bpm = 84

    # Section boundaries (beats)
    S1, S2, S3, S4 = 32.0, 96.0, 160.0, 192.0
    DUR = 224.0

    chords = _chords("i iv v iii " * 8 + "i iv vii v " * 8
                      + "vii vi v i " * 4 + "i iv i iv " * 4, DUR)

    c_a = [c for c in chords if c.start < S1]
    c_b = [c for c in chords if S1 <= c.start < S2]
    c_c = [c for c in chords if S2 <= c.start < S3]
    c_d = [c for c in chords if S3 <= c.start < S4]
    c_e = [c for c in chords if c.start >= S4]

    # Intro: ud taksim — медленная импровизация, исследует лад
    oud_a = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.25),
        drama_shape="crescendo", drama_peak=0.4,
        motif_probability=0.3, motif_variation="any",
        ornament_probability=0.15, harmony_note_probability=0.5,
        note_range_low=57, note_range_high=74,
        phrase_length=16.0, register_smoothness=0.7,
        steps_probability=0.7, first_note="chord_root",
        after_leap="step_opposite",
    ).render(c_a, KEY, S1)

    # Verse 1: voice enters — без предупреждения
    voice_b = MelodyGenerator(
        GeneratorParams(density=0.22, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.65,
        motif_probability=0.45, motif_variation="any",
        ornament_probability=0.2, harmony_note_probability=0.6,
        note_range_low=62, note_range_high=82,
        phrase_length=8.0, register_smoothness=0.6,
        steps_probability=0.7, first_note="any_chord",
        after_leap="step_opposite", note_repetition_probability=0.03,
    ).render(c_b, KEY, S2 - S1)

    # Kanun: тихие арпеджио, высокий регистр
    kanun_b = ArpeggiatorGenerator(
        GeneratorParams(density=0.3, leap_probability=0.3,
                        key_range_low=66, key_range_high=86),
        pattern="up", note_duration=0.4,
    ).render(c_b, KEY, S2 - S1)

    # Verse 2: + riq enters
    voice_c = MelodyGenerator(
        GeneratorParams(density=0.25, leap_probability=0.18),
        drama_shape="crescendo", drama_peak=0.7,
        motif_probability=0.5, motif_variation="any",
        ornament_probability=0.25, harmony_note_probability=0.6,
        accent_pattern="syncopated",
        note_range_low=62, note_range_high=84,
        phrase_length=8.0, register_smoothness=0.5,
        steps_probability=0.65, first_note="any_chord",
        after_leap="step_opposite", note_repetition_probability=0.03,
    ).render(c_c, KEY, S3 - S2)

    kanun_c = ArpeggiatorGenerator(
        GeneratorParams(density=0.3, leap_probability=0.3,
                        key_range_low=66, key_range_high=86),
        pattern="up", note_duration=0.4,
    ).render(c_c, KEY, S3 - S2)

    riq_c = ElectronicDrumsGenerator(
        GeneratorParams(density=0.2, leap_probability=0.0,
                        key_range_low=60, key_range_high=61),
        pattern="light",
    ).render(c_c, KEY, S3 - S2)

    # Bridge: voice upper register — нота держится без вибрато
    voice_d = MelodyGenerator(
        GeneratorParams(density=0.12, leap_probability=0.1),
        drama_shape="crescendo", drama_peak=0.85,
        motif_probability=0.3, motif_variation="invert",
        ornament_probability=0.3, harmony_note_probability=0.5,
        note_range_low=70, note_range_high=86,
        phrase_length=16.0, register_smoothness=0.8,
        steps_probability=0.75, first_note="any_chord",
        after_leap="step_opposite",
    ).render(c_d, KEY, S4 - S3)

    # Outro: ud returns — та же таксим, но звучит иначе
    oud_e = MelodyGenerator(
        GeneratorParams(density=0.12, leap_probability=0.2),
        drama_shape="none", drama_peak=0.3,
        motif_probability=0.3, motif_variation="fragment",
        ornament_probability=0.1, harmony_note_probability=0.5,
        note_range_low=57, note_range_high=72,
        phrase_length=16.0, register_smoothness=0.7,
        steps_probability=0.75, first_note="chord_root",
        after_leap="step_opposite",
    ).render(c_e, KEY, DUR - S4)

    # Assemble with offsets
    oud_all = oud_a + _off(oud_e, S4)
    voice_all = _off(voice_b, S1) + _off(voice_c, S2) + _off(voice_d, S3)
    kanun_all = _off(kanun_b, S1) + _off(kanun_c, S2)
    riq_all = _off(riq_c, S2)

    # Drone — subtle, throughout
    drone = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=50, key_range_high=51),
    ).render(c_a[:1], KEY, DUR)

    tracks = {
        "oud":     oud_all,
        "voice_f": voice_all,
        "kanun":   kanun_all,
        "riq":     riq_all,
        "drone":   drone,
    }
    instruments = {
        "oud": OUD, "voice_f": VOX_F, "kanun": KANUN, "riq": RIQ, "drone": PAD
    }

    final = _export(tracks, OUT / "01_Leyla_Лейла.mid", bpm, instruments, lufs=-16.0)
    _print("I. Лейла (ليلى)", bpm, final, OUT / "01_Leyla_Лейла.mid")


# =====================================================================
# Track II — Ваджд (وجد — Экстаз тоски)
# 56 BPM, 6/8 — Два голоса, одна мелодия, разница в полтакта
# Только струнные: уд, канун, виолончель. pp → mp.
# =====================================================================
def produce_wajd():
    """Экстаз тоски. Тёмно-синий."""
    print("--- 02_Wajd_Ваджд ---")
    bpm = 56
    bpc = 3.0  # 6/8 compound duple
    dur = 150.0

    chords = _chords("i iii v iv " * 10 + "vii vi iv v " * 10, dur, beats_per_chord=bpc)

    # Female voice — главная мелодия, мелизматика
    voice_f = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.12),
        drama_shape="crescendo", drama_peak=0.55,
        motif_probability=0.5, motif_variation="any",
        ornament_probability=0.2, harmony_note_probability=0.6,
        note_range_low=62, note_range_high=80,
        phrase_length=12.0, register_smoothness=0.7,
        steps_probability=0.75, first_note="any_chord",
        after_leap="step_opposite", accent_pattern="natural",
        note_repetition_probability=0.03,
    ).render(chords, KEY, dur)

    # Male voice — та же мелодия, но на полтакта позже
    # Они никогда не встречаются в унисон
    voice_m = _off(voice_f, 0.5)

    # Мужской голос замолкает за 24 такта до конца (~24*3=72 beats → let's use 40 beats)
    male_cutoff = dur - 40.0
    voice_m = _cut_after(voice_m, male_cutoff)

    # Oud — редкий, pizzicato, pp
    oud = MelodyGenerator(
        GeneratorParams(density=0.08, leap_probability=0.12),
        drama_shape="none",
        motif_probability=0.2, motif_variation="fragment",
        ornament_probability=0.05, harmony_note_probability=0.5,
        note_range_low=55, note_range_high=70,
        phrase_length=24.0, register_smoothness=0.8,
        steps_probability=0.8, first_note="chord_root",
        after_leap="step_opposite", note_repetition_probability=0.02,
    ).render(chords, KEY, dur)

    # Cello — длинные педальные тоны, дрон меняется каждые ~16 тактов
    cello = StringsEnsembleGenerator(
        GeneratorParams(density=0.06, leap_probability=0.02,
                        key_range_low=38, key_range_high=55),
    ).render(chords, KEY, dur)

    # Kanun — очень тихие арпеджио
    kanun = ArpeggiatorGenerator(
        GeneratorParams(density=0.12, leap_probability=0.2,
                        key_range_low=62, key_range_high=78),
        pattern="up", note_duration=0.5,
    ).render(chords, KEY, dur)

    tracks = {
        "voice_f": voice_f,
        "voice_m": voice_m,
        "oud":     oud,
        "cello":   cello,
        "kanun":   kanun,
    }
    instruments = {
        "voice_f": VOX_F, "voice_m": VOX_M, "oud": OUD, "cello": CELLO, "kanun": KANUN
    }

    final = _export(tracks, OUT / "02_Wajd_Ваджд.mid", bpm, instruments, lufs=-18.0)
    _print("II. Ваджд (وجد)", bpm, final, OUT / "02_Wajd_Ваджд.mid")


# =====================================================================
# Track III — Гыйра (غيرة — Ревность)
# 138 BPM, 7/8 (3+2+2) — Виртуозный взрыв. Единственный быстрый трек.
# Darbuka intro → Oud + voice → Silence bridge → Full → Oud solo
# =====================================================================
def produce_ghyra():
    """Ревность. Алый."""
    print("--- 03_Ghyra_Гыйра ---")
    bpm = 138
    bpc = 3.5  # 7/8

    # Sections in beats
    S1, S2, S3, S4 = 28.0, 126.0, 140.0, 224.0
    DUR = 280.0

    chords = _chords(
        "i ii iv v " * 32, DUR, beats_per_chord=bpc
    )

    c_a = [c for c in chords if c.start < S1]
    c_b = [c for c in chords if S1 <= c.start < S2]
    c_c = [c for c in chords if S2 <= c.start < S3]
    c_d = [c for c in chords if c.start >= S3]

    # Darbuka intro — сольный ритмический брейк 8 тактов
    darbuka_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.7, leap_probability=0.0,
                        key_range_low=36, key_range_high=42),
        pattern="heavy",
    ).render(c_a, KEY, S1)

    # Main: oud — быстрые шестнадцатые, египетская школа
    oud_b = MelodyGenerator(
        GeneratorParams(density=0.75, leap_probability=0.5),
        drama_shape="dramatic", drama_peak=0.8,
        motif_probability=0.7, motif_variation="any",
        ornament_probability=0.5, harmony_note_probability=0.35,
        note_range_low=57, note_range_high=79,
        syncopation=0.5, rhythm_variety=0.8,
        phrase_length=3.5, register_smoothness=0.4,
        after_leap="step_any", random_movement=0.4,
        first_note="chord_root",
    ).render(c_b, KEY, S2 - S1)

    # Voice: страстный, почти крик
    voice_b = MelodyGenerator(
        GeneratorParams(density=0.55, leap_probability=0.45),
        drama_shape="dramatic", drama_peak=0.85,
        motif_probability=0.6, motif_variation="any",
        ornament_probability=0.45, harmony_note_probability=0.3,
        note_range_low=55, note_range_high=82,
        syncopation=0.4, rhythm_variety=0.7,
        phrase_length=7.0, register_smoothness=0.3,
        after_leap="step_any", random_movement=0.5,
        first_note="any_chord",
    ).render(c_b, KEY, S2 - S1)

    # Darbuka continues with main theme
    darbuka_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.6, leap_probability=0.0,
                        key_range_low=36, key_range_high=42),
        pattern="heavy",
    ).render(c_b, KEY, S2 - S1)

    # Bridge: 4 такта тишины, потом женский голос тихо
    voice_c = MelodyGenerator(
        GeneratorParams(density=0.06, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.2,
        motif_probability=0.3, motif_variation="fragment",
        ornament_probability=0.05, harmony_note_probability=0.7,
        note_range_low=62, note_range_high=76,
        phrase_length=14.0, register_smoothness=0.9,
        steps_probability=0.9, first_note="scale",
        after_leap="step_opposite",
    ).render(c_c, KEY, S3 - S2)

    # Full ensemble explosion
    oud_d = MelodyGenerator(
        GeneratorParams(density=0.8, leap_probability=0.55),
        drama_shape="dramatic", drama_peak=0.9,
        motif_probability=0.65, motif_variation="any",
        ornament_probability=0.55, harmony_note_probability=0.3,
        note_range_low=55, note_range_high=82,
        syncopation=0.6, rhythm_variety=0.85,
        phrase_length=3.5, register_smoothness=0.35,
        after_leap="step_any", random_movement=0.45,
        first_note="chord_root",
    ).render(c_d, KEY, DUR - S3)

    voice_d = MelodyGenerator(
        GeneratorParams(density=0.7, leap_probability=0.5),
        drama_shape="dramatic", drama_peak=0.95,
        motif_probability=0.55, motif_variation="any",
        ornament_probability=0.5, harmony_note_probability=0.3,
        note_range_low=55, note_range_high=86,
        syncopation=0.5, rhythm_variety=0.75,
        phrase_length=7.0, register_smoothness=0.3,
        after_leap="step_any", random_movement=0.5,
        first_note="any_chord",
    ).render(c_d, KEY, DUR - S3)

    darbuka_d = ElectronicDrumsGenerator(
        GeneratorParams(density=0.7, leap_probability=0.0,
                        key_range_low=36, key_range_high=42),
        pattern="heavy",
    ).render(c_d, KEY, DUR - S3)

    kanun_d = ArpeggiatorGenerator(
        GeneratorParams(density=0.5, leap_probability=0.4,
                        key_range_low=60, key_range_high=84),
        pattern="up_down", note_duration=0.2,
    ).render(c_d, KEY, DUR - S3)

    # Assemble with offsets
    oud_all = _off(oud_b, S1) + _off(oud_d, S3)
    voice_m_all = _off(voice_b, S1) + _off(voice_d, S3)
    voice_f_all = _off(voice_c, S2)
    darbuka_all = darbuka_a + _off(darbuka_b, S1) + _off(darbuka_d, S3)
    kanun_all = _off(kanun_d, S3)

    # Abrupt ending: cut all notes at final beat
    oud_all = _cut_after(oud_all, DUR)
    voice_m_all = _cut_after(voice_m_all, DUR)
    voice_f_all = _cut_after(voice_f_all, DUR)
    darbuka_all = _cut_after(darbuka_all, DUR)
    kanun_all = _cut_after(kanun_all, DUR)

    tracks = {
        "oud":      oud_all,
        "voice_m":  voice_m_all,
        "voice_f":  voice_f_all,
        "darbuka":  darbuka_all,
        "kanun":    kanun_all,
    }
    instruments = {
        "oud": OUD, "voice_m": VOX_M, "voice_f": VOX_F, "darbuka": DARBUKA, "kanun": KANUN
    }

    final = _export(tracks, OUT / "03_Ghyra_Гыйра.mid", bpm, instruments, lufs=-12.0)
    _print("III. Гыйра (غيرة)", bpm, final, OUT / "03_Ghyra_Гыйра.mid")


# =====================================================================
# Track IV — Шавк (شوق — Томление / Longing)
# 63 BPM, 4/4 — Ночь. Пустая комната. Запах, который ещё остался.
# Нэй + уд pizz + голос. Нэй и голос в унисон, нэй чуть впереди.
# =====================================================================
def produce_shawk():
    """Томление. Серый."""
    print("--- 04_Shawk_Шавк ---")
    bpm = 63
    dur = 160.0

    chords = _chords("i v iv iii " * 10, dur)

    S_END_VOICE = dur - 32.0  # last 32 beats: voice a cappella

    c_full = chords
    c_accomp = [c for c in chords if c.start < S_END_VOICE]

    # Ney — хриплый, тёплый, много воздуха
    ney = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.1),
        drama_shape="crescendo", drama_peak=0.5,
        motif_probability=0.5, motif_variation="any",
        ornament_probability=0.15, harmony_note_probability=0.55,
        note_range_low=62, note_range_high=79,
        phrase_length=16.0, register_smoothness=0.7,
        steps_probability=0.8, first_note="scale",
        after_leap="step_opposite", note_repetition_probability=0.03,
    ).render(c_accomp, KEY, S_END_VOICE)

    # Oud — только pizz, редко. Очень редко.
    oud = MelodyGenerator(
        GeneratorParams(density=0.05, leap_probability=0.08),
        drama_shape="none",
        motif_probability=0.2, motif_variation="fragment",
        ornament_probability=0.02, harmony_note_probability=0.5,
        note_range_low=50, note_range_high=67,
        phrase_length=32.0, register_smoothness=0.9,
        steps_probability=0.9, first_note="chord_root",
        after_leap="step_opposite", note_repetition_probability=0.01,
    ).render(c_accomp, KEY, S_END_VOICE)

    # Female voice — в унисон с нэй, но чуть позади (offset 0.3 beats)
    voice_base = MelodyGenerator(
        GeneratorParams(density=0.14, leap_probability=0.1),
        drama_shape="crescendo", drama_peak=0.5,
        motif_probability=0.5, motif_variation="any",
        ornament_probability=0.15, harmony_note_probability=0.55,
        note_range_low=62, note_range_high=79,
        phrase_length=16.0, register_smoothness=0.7,
        steps_probability=0.8, first_note="scale",
        after_leap="step_opposite", note_repetition_probability=0.03,
    ).render(chords, KEY, dur)

    # Voice is 0.3 beats behind ney — тень догоняет
    voice_all = _off(
        [n for n in voice_base if n.start < S_END_VOICE], 0.3
    ) + [n for n in voice_base if n.start >= S_END_VOICE]

    # Drone — barely audible
    drone = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=50, key_range_high=51),
    ).render(chords[:1], KEY, dur)

    tracks = {
        "ney":     ney,
        "oud":     oud,
        "voice_f": voice_all,
        "drone":   drone,
    }
    instruments = {
        "ney": NEY, "oud": OUD, "voice_f": VOX_F, "drone": PAD
    }

    final = _export(tracks, OUT / "04_Shawk_Шавк.mid", bpm, instruments, lufs=-17.0)
    _print("IV. Шавк (شوق)", bpm, final, OUT / "04_Shawk_Шавк.mid")


# =====================================================================
# Track V — Хасрет (حسرة — Неутолимая тоска)
# 72 BPM, 4/4 → 12/8 — Финал. Вечное состояние «между».
# Полный ансамбль. Куплет 4/4 — припев 12/8.
# Инструменты уходят один за другим. Остаются два голоса.
# Женский голос — последняя нота, вибрато нарастает.
# =====================================================================
def produce_hasrat():
    """Вечное «между». Пурпурный."""
    print("--- 05_Hasrat_Хасрет ---")
    bpm = 72

    # Sections: intro(4/4) → verseA(4/4) → chorusB(12/8) →
    #           verseA(4/4) → chorusB(12/8) → instruments leave
    S1, S2, S3, S4, S5 = 32.0, 64.0, 112.0, 144.0, 192.0
    DUR = 256.0

    # 4/4 sections: bpc=4.0
    c_a = _chords("i iv v iii " * 4, S1)                       # intro
    c_b = _chords("i iv v iii " * 4, S2 - S1)                  # verse A
    c_d = _chords("i iv vii v " * 4, S4 - S3)                  # verse A repeat

    # 12/8 sections: bpc=6.0
    c_c = _chords("vii vi v i " * 4, S3 - S2, beats_per_chord=6.0)   # chorus B
    c_e = _chords("vii vi v i " * 4, S5 - S4, beats_per_chord=6.0)   # chorus B repeat

    # Outro: full chord coverage, 4/4
    c_out = _chords("i iv v i " * 8, DUR - S5)

    # ── Intro: full ensemble from beat 1 ──
    oud_a = MelodyGenerator(
        GeneratorParams(density=0.3, leap_probability=0.2),
        drama_shape="crescendo", drama_peak=0.5,
        motif_probability=0.5, motif_variation="any",
        ornament_probability=0.1, harmony_note_probability=0.6,
        note_range_low=55, note_range_high=74,
        phrase_length=8.0, register_smoothness=0.6,
        steps_probability=0.7, first_note="chord_root",
        after_leap="step_opposite",
    ).render(c_a, KEY, S1)

    voice_f_a = MelodyGenerator(
        GeneratorParams(density=0.25, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.55,
        motif_probability=0.5, motif_variation="any",
        ornament_probability=0.2, harmony_note_probability=0.6,
        note_range_low=62, note_range_high=82,
        phrase_length=8.0, register_smoothness=0.6,
        steps_probability=0.7, first_note="any_chord",
        after_leap="step_opposite",
    ).render(c_a, KEY, S1)

    voice_m_a = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.5,
        motif_probability=0.45, motif_variation="any",
        ornament_probability=0.15, harmony_note_probability=0.6,
        note_range_low=50, note_range_high=70,
        phrase_length=8.0, register_smoothness=0.6,
        steps_probability=0.7, first_note="chord_root",
        after_leap="step_opposite",
    ).render(c_a, KEY, S1)

    kanun_a = ArpeggiatorGenerator(
        GeneratorParams(density=0.3, leap_probability=0.25,
                        key_range_low=62, key_range_high=82),
        pattern="up", note_duration=0.35,
    ).render(c_a, KEY, S1)

    cello_a = StringsEnsembleGenerator(
        GeneratorParams(density=0.08, leap_probability=0.02,
                        key_range_low=38, key_range_high=55),
    ).render(c_a, KEY, S1)

    darbuka_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.4, leap_probability=0.0,
                        key_range_low=36, key_range_high=42),
        pattern="light",
    ).render(c_a, KEY, S1)

    # ── Verse A (4/4): melody for each instrument ──
    def _verse(gen_p, **kw):
        return MelodyGenerator(gen_p, **kw).render(c_b, KEY, S2 - S1)

    oud_b = _verse(
        GeneratorParams(density=0.35, leap_probability=0.25),
        drama_shape="crescendo", drama_peak=0.6,
        motif_probability=0.55, harmony_note_probability=0.55,
        note_range_low=55, note_range_high=76,
        phrase_length=8.0, register_smoothness=0.55,
        after_leap="step_opposite", first_note="chord_root",
    )

    voice_f_b = _verse(
        GeneratorParams(density=0.28, leap_probability=0.18),
        drama_shape="crescendo", drama_peak=0.65,
        motif_probability=0.5, ornament_probability=0.2,
        harmony_note_probability=0.55,
        note_range_low=62, note_range_high=84,
        phrase_length=8.0, register_smoothness=0.55,
        after_leap="step_opposite", first_note="any_chord",
    )

    voice_m_b = _verse(
        GeneratorParams(density=0.22, leap_probability=0.18),
        drama_shape="crescendo", drama_peak=0.55,
        motif_probability=0.45, ornament_probability=0.15,
        harmony_note_probability=0.6,
        note_range_low=50, note_range_high=72,
        phrase_length=8.0, register_smoothness=0.55,
        after_leap="step_opposite", first_note="chord_root",
    )

    # ── Chorus B (12/8): meter shifts — земля уходит из-под ног ──
    def _chorus(gen_p, **kw):
        return MelodyGenerator(gen_p, **kw).render(c_c, KEY, S3 - S2)

    oud_c = _chorus(
        GeneratorParams(density=0.4, leap_probability=0.3),
        drama_shape="crescendo", drama_peak=0.7,
        motif_probability=0.6, ornament_probability=0.25,
        harmony_note_probability=0.45,
        note_range_low=55, note_range_high=79,
        syncopation=0.4, phrase_length=6.0,
        register_smoothness=0.5, after_leap="step_any",
    )

    voice_f_c = _chorus(
        GeneratorParams(density=0.35, leap_probability=0.22),
        drama_shape="crescendo", drama_peak=0.75,
        motif_probability=0.55, ornament_probability=0.25,
        harmony_note_probability=0.45,
        note_range_low=62, note_range_high=86,
        syncopation=0.35, phrase_length=6.0,
        register_smoothness=0.45, after_leap="step_opposite",
    )

    voice_m_c = _chorus(
        GeneratorParams(density=0.3, leap_probability=0.22),
        drama_shape="crescendo", drama_peak=0.65,
        motif_probability=0.5, ornament_probability=0.2,
        harmony_note_probability=0.5,
        note_range_low=50, note_range_high=74,
        syncopation=0.35, phrase_length=6.0,
        register_smoothness=0.45, after_leap="step_opposite",
    )

    kanun_c = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, leap_probability=0.3,
                        key_range_low=60, key_range_high=84),
        pattern="up_down", note_duration=0.3,
    ).render(c_c, KEY, S3 - S2)

    # Second chorus: female choir ison (pedal tone)
    choir_ison = DroneGenerator(
        GeneratorParams(density=0.03, key_range_low=62, key_range_high=63),
    ).render(c_e, KEY, S5 - S4)

    # ── Outro: instruments leave one by one ──
    # Cello → Darbuka → Kanun → Ney → Oud → voices
    # Each instrument plays only part of the outro
    fade_start = S5

    oud_out = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.15),
        drama_shape="none", drama_peak=0.3,
        motif_probability=0.3, harmony_note_probability=0.6,
        note_range_low=55, note_range_high=72,
        phrase_length=16.0, register_smoothness=0.7,
        after_leap="step_opposite", first_note="chord_root",
    ).render(c_out, KEY, DUR - S5)
    oud_out = _cut_after(oud_out, 40.0)  # oud leaves at fade_start + 40

    cello_out = StringsEnsembleGenerator(
        GeneratorParams(density=0.06, key_range_low=38, key_range_high=55),
    ).render(c_out, KEY, 20.0)  # cello leaves at fade_start + 20

    darbuka_out = ElectronicDrumsGenerator(
        GeneratorParams(density=0.35, leap_probability=0.0,
                        key_range_low=36, key_range_high=42),
        pattern="light",
    ).render(c_out, KEY, 30.0)  # darbuka leaves at fade_start + 30

    kanun_out = ArpeggiatorGenerator(
        GeneratorParams(density=0.25, leap_probability=0.2,
                        key_range_low=62, key_range_high=78),
        pattern="up", note_duration=0.4,
    ).render(c_out, KEY, 35.0)  # kanun leaves at fade_start + 35

    # Voices continue to the end
    voice_f_out = MelodyGenerator(
        GeneratorParams(density=0.18, leap_probability=0.1),
        drama_shape="none", drama_peak=0.2,
        motif_probability=0.4, ornament_probability=0.15,
        harmony_note_probability=0.6,
        note_range_low=62, note_range_high=82,
        phrase_length=32.0, register_smoothness=0.8,
        steps_probability=0.8, after_leap="step_opposite",
        first_note="any_chord",
    ).render(c_out, KEY, DUR - S5)

    voice_m_out = MelodyGenerator(
        GeneratorParams(density=0.14, leap_probability=0.1),
        drama_shape="none", drama_peak=0.15,
        motif_probability=0.35, ornament_probability=0.1,
        harmony_note_probability=0.6,
        note_range_low=50, note_range_high=70,
        phrase_length=32.0, register_smoothness=0.8,
        steps_probability=0.8, after_leap="step_opposite",
        first_note="chord_root",
    ).render(c_out, KEY, DUR - S5)
    voice_m_out = _cut_after(voice_m_out, (DUR - S5) - 12.0)  # male drops 12 beats before end

    # ── Assemble all sections with offsets ──
    oud_all = oud_a + _off(oud_b, S1) + _off(oud_c, S2) + _off(oud_out, S5)
    voice_f_all = voice_f_a + _off(voice_f_b, S1) + _off(voice_f_c, S2) + _off(voice_f_out, S5)
    voice_m_all = voice_m_a + _off(voice_m_b, S1) + _off(voice_m_c, S2) + _off(voice_m_out, S5)
    kanun_all = kanun_a + _off(kanun_c, S2) + _off(kanun_out, S5)
    cello_all = cello_a + _off(cello_out, S5)
    darbuka_all = darbuka_a + _off(darbuka_out, S5)

    # Second verse + chorus (repeat pattern)
    oud_d = MelodyGenerator(
        GeneratorParams(density=0.35, leap_probability=0.25),
        drama_shape="crescendo", drama_peak=0.7,
        motif_probability=0.55, harmony_note_probability=0.5,
        note_range_low=55, note_range_high=76,
        phrase_length=8.0, register_smoothness=0.5,
        after_leap="step_opposite", first_note="chord_root",
    ).render(c_d, KEY, S4 - S3)

    voice_f_d = MelodyGenerator(
        GeneratorParams(density=0.3, leap_probability=0.2),
        drama_shape="crescendo", drama_peak=0.75,
        motif_probability=0.5, ornament_probability=0.25,
        harmony_note_probability=0.5,
        note_range_low=62, note_range_high=86,
        phrase_length=8.0, register_smoothness=0.5,
        after_leap="step_opposite", first_note="any_chord",
    ).render(c_d, KEY, S4 - S3)

    voice_m_d = MelodyGenerator(
        GeneratorParams(density=0.24, leap_probability=0.2),
        drama_shape="crescendo", drama_peak=0.6,
        motif_probability=0.45, ornament_probability=0.2,
        harmony_note_probability=0.55,
        note_range_low=50, note_range_high=74,
        phrase_length=8.0, register_smoothness=0.5,
        after_leap="step_opposite", first_note="chord_root",
    ).render(c_d, KEY, S4 - S3)

    # Second chorus: oud + voices + choir ison + kanun
    oud_e = MelodyGenerator(
        GeneratorParams(density=0.4, leap_probability=0.3),
        drama_shape="crescendo", drama_peak=0.8,
        motif_probability=0.6, ornament_probability=0.3,
        harmony_note_probability=0.4,
        note_range_low=55, note_range_high=82,
        syncopation=0.45, phrase_length=6.0,
        register_smoothness=0.4, after_leap="step_any",
    ).render(c_e, KEY, S5 - S4)

    voice_f_e = MelodyGenerator(
        GeneratorParams(density=0.35, leap_probability=0.22),
        drama_shape="crescendo", drama_peak=0.85,
        motif_probability=0.55, ornament_probability=0.3,
        harmony_note_probability=0.4,
        note_range_low=62, note_range_high=88,
        syncopation=0.4, phrase_length=6.0,
        register_smoothness=0.4, after_leap="step_opposite",
    ).render(c_e, KEY, S5 - S4)

    voice_m_e = MelodyGenerator(
        GeneratorParams(density=0.3, leap_probability=0.22),
        drama_shape="crescendo", drama_peak=0.7,
        motif_probability=0.5, ornament_probability=0.25,
        harmony_note_probability=0.45,
        note_range_low=50, note_range_high=76,
        syncopation=0.4, phrase_length=6.0,
        register_smoothness=0.4, after_leap="step_opposite",
    ).render(c_e, KEY, S5 - S4)

    kanun_e = ArpeggiatorGenerator(
        GeneratorParams(density=0.4, leap_probability=0.3,
                        key_range_low=60, key_range_high=84),
        pattern="up_down", note_duration=0.3,
    ).render(c_e, KEY, S5 - S4)

    # Add second verse + chorus sections
    oud_all += _off(oud_d, S3) + _off(oud_e, S4)
    voice_f_all += _off(voice_f_d, S3) + _off(voice_f_e, S4)
    voice_m_all += _off(voice_m_d, S3) + _off(voice_m_e, S4)
    kanun_all += _off(kanun_e, S4)

    # Choir ison in second chorus
    choir_all = _off(choir_ison, S4)

    # Drone throughout
    drone = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=50, key_range_high=51),
    ).render(c_a[:1], KEY, DUR)

    tracks = {
        "oud":      oud_all,
        "voice_f":  voice_f_all,
        "voice_m":  voice_m_all,
        "kanun":    kanun_all,
        "cello":    cello_all,
        "darbuka":  darbuka_all,
        "choir":    choir_all,
        "drone":    drone,
    }
    instruments = {
        "oud": OUD, "voice_f": VOX_F, "voice_m": VOX_M, "kanun": KANUN,
        "cello": CELLO, "darbuka": DARBUKA, "choir": CHOIR, "drone": PAD
    }

    final = _export(tracks, OUT / "05_Hasrat_Хасрет.mid", bpm, instruments, lufs=-14.0)
    _print("V. Хасрет (حسرة)", bpm, final, OUT / "05_Hasrat_Хасрет.mid")


# ═══════════════════════════════════════════════════════════════════
produce_leyla()
print()
produce_wajd()
print()
produce_ghyra()
print()
produce_shawk()
print()
produce_hasrat()
print()
print("=" * 60)
print("   جان ДЖАН — COMPLETE.")
print("   Files in:", OUT)
print("=" * 60)
