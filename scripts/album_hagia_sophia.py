# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_hagia_sophia.py — Византийский лад, пять граней империи.

Byzantine / Hijaz Major: [0, 1, 4, 5, 7, 8, 11]
Аугментированные секунды, восточная торжественность, сакральный драматизм.

  1. Порфира       — Имперская процессия, 72 BPM, 4/4
  2. Феофания      — Явление света, 60 BPM, 6/8
  3. Никефор       — Военный марш, 108 BPM, 5/4
  4. Хрисовул      — Ночная мистерия, 52 BPM, 7/8
  5. Апокатастасис — Вечность, 44→88 BPM, 4/4
"""

from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


def _chords(progression: str, key: types.Scale, duration: float,
            beats_per_chord: float | None = None):
    parts = progression.split()
    bpc = beats_per_chord if beats_per_chord else duration / len(parts)
    chords = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        c.start = i * bpc
        c.duration = bpc
        chords.append(c)
    return chords


def _master(raw: dict, bpm: float, lufs: float = -12.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "duduk": 1.0, "choir": 0.9, "strings": 0.7,
        "drums": 0.85, "drone": 0.4, "arp": 0.55,
        "bass": 0.95, "oud": 0.9, "organ": 0.6,
        "violin": 0.85, "trumpet": 0.8, "voice": 0.9,
        "ostinato": 0.5, "buzuk": 0.65, "baritone": 0.75,
    })
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# =====================================================================
# Track 1 — Порфира (Porphyra)
# 72 BPM, 4/4, D Byzantine
# Имперская процессия, рассвет над Константинополем
# =====================================================================
def produce_porphyra():
    """Dawn → Imperial march → Royal chorus → Ud solo → Fade."""
    print("  I. Порфира (Porphyra) [Byzantine — 72 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.BYZANTINE)
    dur = 160.0
    bpc = 4.0  # beats per chord (4/4)

    prog = ("i iv v i " * 8).strip()
    chords = _chords(prog, key, dur, beats_per_chord=bpc)

    # Sections: intro(0-32) → verse(32-96) → chorus(96-128) → outro(128-160)
    s1, s2, s3 = 32.0, 96.0, 128.0
    c_a = [c for c in chords if c.start < s1]
    c_b = [c for c in chords if s1 <= c.start < s2]
    c_c = [c for c in chords if s2 <= c.start < s3]
    c_d = [c for c in chords if c.start >= s3]

    # 1. Duduk — the imperial voice, eastern ornamented
    duduk_a = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.08),
        drama_shape="crescendo", drama_peak=0.3,
        harmony_note_probability=0.95, motif_probability=0.85,
        note_range_low=69, note_range_high=81,
        phrase_length=16.0, register_smoothness=0.97,
        steps_probability=0.93, first_note="tonic",
        ornament_probability=0.3,
    ).render(c_a, key, s1)

    duduk_b = MelodyGenerator(
        GeneratorParams(density=0.45, leap_probability=0.3),
        drama_shape="crescendo", drama_peak=0.55,
        harmony_note_probability=0.7, motif_probability=0.8,
        motif_variation="any",
        ornament_probability=0.4,
        note_range_low=62, note_range_high=79,
        phrase_length=8.0, register_smoothness=0.9,
        steps_probability=0.85, first_note="tonic",
    ).render(c_b, key, s2 - s1)

    duduk_c = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.12),
        drama_shape="crescendo", drama_peak=0.35,
        harmony_note_probability=0.9, motif_probability=0.9,
        motif_variation="transpose",
        note_range_low=66, note_range_high=79,
        phrase_length=12.0, register_smoothness=0.95,
        steps_probability=0.9, first_note="tonic",
    ).render(c_c, key, s3 - s2)

    duduk_d = MelodyGenerator(
        GeneratorParams(density=0.1, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.15,
        harmony_note_probability=0.97,
        note_range_low=66, note_range_high=76,
        phrase_length=24.0, register_smoothness=0.98,
        steps_probability=0.96, first_note="tonic",
        motif_probability=0.9, motif_variation="fragment",
    ).render(c_d, key, dur - s3)

    for n in duduk_b: n.start += s1
    for n in duduk_c: n.start += s2
    for n in duduk_d: n.start += s3
    duduk = duduk_a + duduk_b + duduk_c + duduk_d

    # 2. Choir — male unison Orthodox singing, enters at chorus
    choir_c = MelodyGenerator(
        GeneratorParams(density=0.5, leap_probability=0.25),
        drama_shape="epic", drama_peak=0.7,
        harmony_note_probability=0.8,
        note_range_low=55, note_range_high=72,
        phrase_length=8.0, register_smoothness=0.92,
        steps_probability=0.85, first_note="tonic",
        motif_probability=0.85, motif_variation="any",
    ).render(c_c, key, s3 - s2)

    choir_d = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.15,
        harmony_note_probability=0.95,
        note_range_low=55, note_range_high=67,
        phrase_length=16.0, register_smoothness=0.97,
        steps_probability=0.95, first_note="tonic",
    ).render(c_d, key, dur - s3)

    for n in choir_c: n.start += s2
    for n in choir_d: n.start += s3
    choir = choir_c + choir_d

    # 3. Strings — drone + counterpoint
    strings_a = StringsEnsembleGenerator(
        GeneratorParams(density=0.1, key_range_low=38, key_range_high=55),
        articulation="sustained", divisi=1, dynamic_curve="crescendo",
    ).render(c_a, key, s1)

    strings_full = StringsEnsembleGenerator(
        GeneratorParams(density=0.4, key_range_low=38, key_range_high=72),
        articulation="sustained", divisi=4, dynamic_curve="crescendo",
    ).render([c for c in chords if c.start >= s1], key, dur - s1)
    for n in strings_full: n.start += s1

    strings = strings_a + strings_full

    # 4. Ud — solo bridge section
    oud_b = MelodyGenerator(
        GeneratorParams(density=0.65, leap_probability=0.5),
        drama_shape="dramatic", drama_peak=0.75,
        harmony_note_probability=0.4,
        ornament_probability=0.55,
        note_range_low=55, note_range_high=79,
        syncopation=0.55, rhythm_variety=0.8,
        after_leap="step_any", random_movement=0.4,
        phrase_length=4.0, motif_probability=0.8, motif_variation="any",
    ).render(c_b, key, s2 - s1)
    for n in oud_b: n.start += s1

    # 5. Tambourine — enters after intro
    drums_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.35), kit="cr78", pattern="minimal",
    ).render(c_b, key, s2 - s1)

    drums_c = ElectronicDrumsGenerator(
        GeneratorParams(density=0.5), kit="909", pattern="four_on_floor",
    ).render(c_c, key, s3 - s2)

    drums_d = ElectronicDrumsGenerator(
        GeneratorParams(density=0.2), kit="808", pattern="minimal",
    ).render(c_d, key, dur - s3)

    for n in drums_b: n.start += s1
    for n in drums_c: n.start += s2
    for n in drums_d: n.start += s3
    drums = drums_b + drums_c + drums_d

    raw = {"duduk": duduk, "choir": choir, "strings": strings,
           "oud": oud_b, "drums": drums}
    mastered, pan = _master(raw, 72.0, lufs=-13.0)
    return mastered, pan, 72.0, key, {
        "duduk": 73,    # Flute (as Duduk)
        "choir": 52,    # Choir Aahs
        "strings": 49,  # String Ensemble 1
        "oud": 24,      # Nylon Guitar (as Oud)
        "drums": 0,
    }


# =====================================================================
# Track 2 — Феофания (Theophania)
# 60 BPM, 6/8 (phrase_length=3), D Byzantine
# Явление света, транс, откровение
# =====================================================================
def produce_theophania():
    """Bell → monodic voice → ison drone → canon → full chorus → silence."""
    print("  II. Феофания (Theophania) [Byzantine — 60 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.BYZANTINE)
    dur = 180.0
    bpc = 3.0  # 6/8 = 3 beats per chord slot

    prog = ("i iv v i " * 10).strip()
    chords = _chords(prog, key, dur, beats_per_chord=bpc)

    # Sections: intro(0-30) → voice(30-90) → canon(90-135) → climax(135-165) → fade(165-180)
    s1, s2, s3, s4 = 30.0, 90.0, 135.0, 165.0
    c_a = [c for c in chords if c.start < s1]
    c_b = [c for c in chords if s1 <= c.start < s2]
    c_c = [c for c in chords if s2 <= c.start < s3]
    c_d = [c for c in chords if s3 <= c.start < s4]
    c_e = [c for c in chords if c.start >= s4]

    # 1. Voice — female, melismatic, high register (monodic Byzantine chant)
    voice_b = MelodyGenerator(
        GeneratorParams(density=0.25, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.4,
        harmony_note_probability=0.85,
        ornament_probability=0.5,
        note_range_low=67, note_range_high=84,
        phrase_length=6.0, register_smoothness=0.93,
        steps_probability=0.88, first_note="tonic",
        motif_probability=0.85, motif_variation="any",
    ).render(c_b, key, s2 - s1)

    voice_c = MelodyGenerator(
        GeneratorParams(density=0.45, leap_probability=0.3),
        drama_shape="crescendo", drama_peak=0.6,
        harmony_note_probability=0.65,
        ornament_probability=0.55,
        note_range_low=64, note_range_high=86,
        phrase_length=4.5, register_smoothness=0.88,
        steps_probability=0.82, syncopation=0.2,
        motif_probability=0.8, motif_variation="any",
    ).render(c_c, key, s3 - s2)

    voice_d = MelodyGenerator(
        GeneratorParams(density=0.6, leap_probability=0.35),
        drama_shape="epic", drama_peak=0.85,
        harmony_note_probability=0.55,
        ornament_probability=0.6,
        note_range_low=62, note_range_high=88,
        phrase_length=3.0, register_smoothness=0.85,
        syncopation=0.25, rhythm_variety=0.6,
        motif_probability=0.75, motif_variation="any",
    ).render(c_d, key, s4 - s3)

    for n in voice_b: n.start += s1
    for n in voice_c: n.start += s2
    for n in voice_d: n.start += s3
    voice = voice_b + voice_c + voice_d

    # 2. Choir — ison (drone) then full chorus at climax
    choir_c = StringsEnsembleGenerator(
        GeneratorParams(density=0.25, key_range_low=50, key_range_high=60),
        articulation="sustained", divisi=2, dynamic_curve="flat",
    ).render(c_c, key, s3 - s2)

    choir_d = MelodyGenerator(
        GeneratorParams(density=0.55, leap_probability=0.25),
        drama_shape="epic", drama_peak=0.8,
        harmony_note_probability=0.75,
        note_range_low=55, note_range_high=74,
        phrase_length=3.0, register_smoothness=0.9,
        steps_probability=0.85, first_note="tonic",
        motif_probability=0.8, motif_variation="any",
    ).render(c_d, key, s4 - s3)

    choir_e = MelodyGenerator(
        GeneratorParams(density=0.1, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.12,
        harmony_note_probability=0.95,
        note_range_low=55, note_range_high=67,
        phrase_length=12.0, register_smoothness=0.97,
        steps_probability=0.95, first_note="tonic",
        motif_probability=0.9, motif_variation="fragment",
    ).render(c_e, key, dur - s4)

    for n in choir_c: n.start += s2
    for n in choir_d: n.start += s3
    for n in choir_e: n.start += s4
    choir = choir_c + choir_d + choir_e

    # 3. Strings — sustained swells
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, key_range_low=41, key_range_high=72),
        articulation="sustained", divisi=3, dynamic_curve="swell",
    ).render(chords, key, dur)

    # 4. Drone — pedal tone throughout
    drone = DroneGenerator(
        GeneratorParams(density=0.06), variant="tonic",
    ).render(chords, key, dur)

    # 5. Percussion — riq and buben, enters at canon
    drums_c = ElectronicDrumsGenerator(
        GeneratorParams(density=0.25), kit="cr78", pattern="minimal",
    ).render(c_c, key, s3 - s2)

    drums_d = ElectronicDrumsGenerator(
        GeneratorParams(density=0.5), kit="909", pattern="four_on_floor",
    ).render(c_d, key, s4 - s3)

    for n in drums_c: n.start += s2
    for n in drums_d: n.start += s3
    drums = drums_c + drums_d

    raw = {"voice": voice, "choir": choir, "strings": strings,
           "drone": drone, "drums": drums}
    mastered, pan = _master(raw, 60.0, lufs=-15.0)
    return mastered, pan, 60.0, key, {
        "voice": 54,    # Voice Oohs
        "choir": 52,    # Choir Aahs
        "strings": 48,  # String Ensemble 2
        "drone": 19,    # Church Organ
        "drums": 0,
    }


# =====================================================================
# Track 3 — Никефор (Nikephoros)
# 108 BPM, 5/4 (phrase_length=5), D Byzantine
# Военный марш, имперская экспансия, трагическая нота
# =====================================================================
def produce_nikephoros():
    """March → trumpets → violin lament → march returns → final blow."""
    print("  III. Никефор (Nikephoros) [Byzantine — 108 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.BYZANTINE)
    dur = 140.0
    bpc = 5.0  # 5/4 = 5 beats per chord

    prog = ("i iv v i " * 6).strip()
    chords = _chords(prog, key, dur, beats_per_chord=bpc)

    # Sections: groove(0-35) → march(35-70) → violin bridge(70-105) → return(105-140)
    s1, s2, s3 = 35.0, 70.0, 105.0
    c_a = [c for c in chords if c.start < s1]
    c_b = [c for c in chords if s1 <= c.start < s2]
    c_c = [c for c in chords if s2 <= c.start < s3]
    c_d = [c for c in chords if c.start >= s3]

    # 1. Trumpet — military signals in unison
    trumpet_a = MelodyGenerator(
        GeneratorParams(density=0.55, leap_probability=0.45),
        drama_shape="crescendo", drama_peak=0.6,
        harmony_note_probability=0.6,
        note_range_low=58, note_range_high=79,
        phrase_length=5.0, register_smoothness=0.85,
        syncopation=0.4, rhythm_variety=0.7,
        motif_probability=0.8, motif_variation="any",
    ).render(c_a, key, s1)

    trumpet_b = MelodyGenerator(
        GeneratorParams(density=0.7, leap_probability=0.5),
        drama_shape="dramatic", drama_peak=0.75,
        harmony_note_probability=0.45,
        ornament_probability=0.3,
        note_range_low=55, note_range_high=84,
        phrase_length=2.5, register_smoothness=0.8,
        syncopation=0.5, rhythm_variety=0.8,
        after_leap="step_any", random_movement=0.4,
        motif_probability=0.75, motif_variation="any",
    ).render(c_b, key, s2 - s1)

    trumpet_d = MelodyGenerator(
        GeneratorParams(density=0.8, leap_probability=0.55),
        drama_shape="epic", drama_peak=0.9,
        harmony_note_probability=0.4,
        ornament_probability=0.35,
        note_range_low=53, note_range_high=88,
        phrase_length=2.5, register_smoothness=0.75,
        syncopation=0.55, rhythm_variety=0.85,
        after_leap="step_any", random_movement=0.5,
        motif_probability=0.7, motif_variation="any",
    ).render(c_d, key, dur - s3)

    for n in trumpet_b: n.start += s1
    for n in trumpet_d: n.start += s3
    trumpet = trumpet_a + trumpet_b + trumpet_d

    # 2. Violin — the soldier's lament in bridge section
    violin_c = MelodyGenerator(
        GeneratorParams(density=0.3, leap_probability=0.2),
        drama_shape="tension_release", drama_peak=0.55,
        harmony_note_probability=0.8,
        ornament_probability=0.45,
        note_range_low=55, note_range_high=74,
        phrase_length=10.0, register_smoothness=0.92,
        steps_probability=0.88, first_note="tonic",
        motif_probability=0.9, motif_variation="any",
    ).render(c_c, key, s3 - s2)
    for n in violin_c: n.start += s2

    # 3. Strings — military ensemble
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.45, key_range_low=38, key_range_high=72),
        articulation="sustained", divisi=4, dynamic_curve="crescendo",
    ).render(chords, key, dur)

    # 4. Bass — davul-like low pulse
    bass = BassGenerator(
        GeneratorParams(density=0.5, key_range_low=26, key_range_high=40),
        style="root_fifth_octave",
    ).render(chords, key, dur)

    # 5. Drums — davul + zurna groove (5/4 pattern)
    drums_a = ElectronicDrumsGenerator(
        GeneratorParams(density=0.5), kit="909", pattern="four_on_floor",
    ).render(c_a, key, s1)

    drums_b = ElectronicDrumsGenerator(
        GeneratorParams(density=0.65), kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(c_b, key, s2 - s1)

    drums_d = ElectronicDrumsGenerator(
        GeneratorParams(density=0.8), kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(c_d, key, dur - s3)

    for n in drums_a: pass  # already at 0
    for n in drums_b: n.start += s1
    for n in drums_d: n.start += s3
    drums = drums_a + drums_b + drums_d

    raw = {"trumpet": trumpet, "violin": violin_c, "strings": strings,
           "bass": bass, "drums": drums}
    mastered, pan = _master(raw, 108.0, lufs=-9.0)
    return mastered, pan, 108.0, key, {
        "trumpet": 56,   # Trumpet
        "violin": 41,    # Viola (as mournful violin)
        "strings": 48,   # String Ensemble 2
        "bass": 36,      # Fretless Bass (as davul low end)
        "drums": 0,
    }


# =====================================================================
# Track 4 — Хрисовул (Chrysobull)
# 52 BPM, 7/8 (phrase_length=3.5), D Byzantine
# Ночная литургия, тайный ритуал, мистерия
# =====================================================================
def produce_chrysobull():
    """Static texture → baritone psalmody → cluster harmonies → silence."""
    print("  IV. Хрисовул (Chrysobull) [Byzantine — 52 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.BYZANTINE)
    dur = 176.0  # ~6:45 at 52 BPM
    bpc = 3.5  # 7/8 = 3.5 beats per chord slot

    prog = ("i i iv i " * 8).strip()
    chords = _chords(prog, key, dur, beats_per_chord=bpc)

    # 1. Buzuk — shimmering arpeggio pattern, static texture
    buzuk = ArpeggiatorGenerator(
        GeneratorParams(density=0.3),
        pattern="up", note_duration=0.75,
        voicing="open", octaves=2,
    ).render(chords, key, dur)

    # 2. Baritone — psalmody, minimal melodic line
    baritone = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.08),
        drama_shape="crescendo", drama_peak=0.35,
        harmony_note_probability=0.92,
        note_range_low=45, note_range_high=60,
        phrase_length=7.0, register_smoothness=0.97,
        steps_probability=0.95, first_note="tonic",
        motif_probability=0.85, motif_variation="transpose",
        ornament_probability=0.1,
    ).render(chords, key, dur)

    # 3. Strings — second clusters, "correct dissonance"
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.25, key_range_low=41, key_range_high=62),
        articulation="sustained", divisi=2, dynamic_curve="crescendo",
    ).render(chords, key, dur)

    # 4. Drone — deep nocturnal hum
    drone = DroneGenerator(
        GeneratorParams(density=0.05), variant="tonic",
    ).render(chords, key, dur)

    # 5. Frame drum — heartbeat, almost inaudible
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.12), kit="808", pattern="minimal",
    ).render(chords, key, dur)

    raw = {"buzuk": buzuk, "baritone": baritone, "strings": strings,
           "drone": drone, "drums": drums}
    mastered, pan = _master(raw, 52.0, lufs=-20.0)
    return mastered, pan, 52.0, key, {
        "buzuk": 25,    # Steel Guitar (as buzuk)
        "baritone": 54, # Voice Oohs
        "strings": 49,  # String Ensemble 1
        "drone": 89,    # New Age Pad
        "drums": 0,
    }


# =====================================================================
# Track 5 — Апокатастасис (Apokatastasis)
# 44→88 BPM, 4/4, D Byzantine
# Вечность — конец империи и её бессмертие
# =====================================================================
def produce_apokatastasis():
    """Organ solo → instruments join one by one → all themes → tempo shift → fade."""
    print("  V. Апокатастасис (Apokatastasis) [Byzantine — 44→88 BPM — D]")

    key = types.Scale(root=2, mode=types.Mode.BYZANTINE)
    # Render at 88 BPM but first half is sparse (perceived as 44 BPM)
    dur = 200.0
    bpc = 4.0

    prog = ("i iv v i " * 10).strip()
    chords = _chords(prog, key, dur, beats_per_chord=bpc)

    # Five additive layers, each ~40 beats
    s1, s2, s3, s4 = 40.0, 80.0, 120.0, 160.0
    c_a = [c for c in chords if c.start < s1]
    c_b = [c for c in chords if s1 <= c.start < s2]
    c_c = [c for c in chords if s2 <= c.start < s3]
    c_d = [c for c in chords if s3 <= c.start < s4]
    c_e = [c for c in chords if c.start >= s4]

    # 1. Organ — the eternal voice, solo intro then throughout
    organ_a = MelodyGenerator(
        GeneratorParams(density=0.12, leap_probability=0.08),
        drama_shape="crescendo", drama_peak=0.3,
        harmony_note_probability=0.95,
        note_range_low=57, note_range_high=74,
        phrase_length=16.0, register_smoothness=0.97,
        steps_probability=0.95, first_note="tonic",
        motif_probability=0.9, motif_variation="any",
    ).render(c_a, key, s1)

    organ_full = MelodyGenerator(
        GeneratorParams(density=0.4, leap_probability=0.3),
        drama_shape="epic", drama_peak=0.85,
        harmony_note_probability=0.6,
        ornament_probability=0.3,
        note_range_low=50, note_range_high=79,
        phrase_length=8.0, register_smoothness=0.88,
        syncopation=0.3, rhythm_variety=0.6,
        motif_probability=0.8, motif_variation="any",
    ).render([c for c in chords if c.start >= s1], key, dur - s1)
    for n in organ_full: n.start += s1

    organ = organ_a + organ_full

    # 2. Duduk — enters at layer 2 (40), recalls Track 1 theme
    duduk_b = MelodyGenerator(
        GeneratorParams(density=0.2, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.5,
        harmony_note_probability=0.8,
        ornament_probability=0.4,
        note_range_low=62, note_range_high=79,
        phrase_length=8.0, register_smoothness=0.92,
        steps_probability=0.88, first_note="tonic",
        motif_probability=0.9, motif_variation="any",
    ).render([c for c in chords if c.start >= s1], key, dur - s1)
    for n in duduk_b: n.start += s1

    # 3. Choir — enters at layer 3 (80), full Orthodox chorus
    choir_c = MelodyGenerator(
        GeneratorParams(density=0.4, leap_probability=0.2),
        drama_shape="epic", drama_peak=0.7,
        harmony_note_probability=0.75,
        note_range_low=52, note_range_high=72,
        phrase_length=8.0, register_smoothness=0.9,
        steps_probability=0.85, first_note="tonic",
        motif_probability=0.8, motif_variation="any",
    ).render([c for c in chords if c.start >= s2], key, dur - s2)
    for n in choir_c: n.start += s2

    # 4. Strings — enters at layer 2, full ensemble
    strings_b = StringsEnsembleGenerator(
        GeneratorParams(density=0.35, key_range_low=36, key_range_high=74),
        articulation="sustained", divisi=4, dynamic_curve="crescendo",
    ).render([c for c in chords if c.start >= s1], key, dur - s1)
    for n in strings_b: n.start += s1

    # 5. Drums — enters at layer 4 (120), builds to finale
    drums_d = ElectronicDrumsGenerator(
        GeneratorParams(density=0.5), kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(c_d, key, s4 - s3)

    drums_e = ElectronicDrumsGenerator(
        GeneratorParams(density=0.7), kit="909", pattern="four_on_floor",
        sidechain=True,
    ).render(c_e, key, dur - s4)

    for n in drums_d: n.start += s3
    drums = drums_d + drums_e

    raw = {"organ": organ, "duduk": duduk_b, "choir": choir_c,
           "strings": strings_b, "drums": drums}
    mastered, pan = _master(raw, 88.0, lufs=-11.0)
    return mastered, pan, 88.0, key, {
        "organ": 19,    # Church Organ
        "duduk": 73,    # Flute
        "choir": 52,    # Choir Aahs
        "strings": 49,  # String Ensemble 1
        "drums": 0,
    }


# =====================================================================
# Main
# =====================================================================
def main():
    album_dir = Path("output/album_hagia_sophia")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   HAGIA SOPHIA — Византийский лад")
    print("   Byzantine [0,1,4,5,7,8,11] — 5 tracks")
    print("=" * 60 + "\n")

    tracks = [
        ("01_Porphyra_Порфира",          produce_porphyra),
        ("02_Theophania_Феофания",       produce_theophania),
        ("03_Nikephoros_Никефор",        produce_nikephoros),
        ("04_Chrysobull_Хрисовул",       produce_chrysobull),
        ("05_Apokatastasis_Апокатастасис", produce_apokatastasis),
    ]

    for name, producer in tracks:
        print(f"\n--- {name} ---")
        mastered, pan, bpm, key, instr = producer()
        export_multitrack_midi(
            mastered,
            str(album_dir / f"{name}.mid"),
            bpm=bpm, key=key, cc_events=pan, instruments=instr,
        )
        inst_names = {
            73: "Duduk/Flute", 52: "Choir Aahs", 49: "Strings Ens 1",
            24: "Oud/Nylon", 19: "Church Organ", 54: "Voice Oohs",
            48: "Strings Ens 2", 56: "Trumpet", 41: "Viola",
            36: "Fretless Bass", 25: "Buzuk", 89: "New Age Pad", 0: "Drums",
        }
        print(f"    -> {name}.mid  ({bpm} BPM, {len(mastered)} tracks)")
        for track_name, program in instr.items():
            gm_name = inst_names.get(program, f"GM#{program}")
            note_count = sum(len(v) for k, v in mastered.items() if k == track_name)
            print(f"       {track_name:16s}  {gm_name:20s}  {note_count:>4d} notes")

    print("\n" + "=" * 60)
    print(f"   HAGIA SOPHIA — COMPLETE.")
    print(f"   Files in: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
