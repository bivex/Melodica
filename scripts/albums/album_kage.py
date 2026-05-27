# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_kage.py — 影 (KAGE — «Тень»)
Hirajoshi [0, 2, 3, 7, 8] — японская пентатоника.
Минимализм, пустота, смерть, самурайская меланхолия.

  1. Мусаси    — Пустота, 58 BPM, 4/4
  2. Юки-Онна  — Снежная смерть, 66 BPM, 3/4
  3. Сэппуку   — Решимость, 40 BPM, 5/4
  4. Фурю-моно — Абсурд, 76 BPM (сбой темпа)
  5. Му        — Ничто, rubato solo

Тьма не в звуке. Она в молчании между нотами.
"""

from pathlib import Path
from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


KEY = types.Scale(root=2, mode=types.Mode.HIROJOSHI)  # D Hirajoshi


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


def _master(raw: dict, bpm: float, lufs: float = -12.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "shakuhachi": 1.0, "koto": 0.6, "strings": 0.5,
        "drums": 0.7, "drone": 0.3, "piano": 0.65,
        "voice": 0.8, "bell": 0.9,
    })
    mixed = desk.apply_mixing(raw, [("Dynamics", 400, [])], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)


# =====================================================================
# Track 1 — Мусаси (空 — Пустота)
# 58 BPM, 4/4, D Hirajoshi
# Рассвет перед последней битвой. Туман. Концепция ма (間)
# =====================================================================
def produce_musashi():
    """Shakuhachi breath → koto drips → single taiko → back to breath."""
    print("  I. Мусаси (空) [Hirajoshi — 58 BPM — D]")

    dur = 192.0  # ~5:30 at 58 BPM
    chords = _chords("i iv v i " * 8, dur)

    s1, s2, s3 = 48.0, 128.0, 168.0
    c_a = [c for c in chords if c.start < s1]
    c_b = [c for c in chords if s1 <= c.start < s2]
    c_c = [c for c in chords if s2 <= c.start < s3]
    c_d = [c for c in chords if c.start >= s3]

    # 1. Shakuhachi — ma (間): breath between sounds
    #    density 0.05 = almost nothing. phrase_length 24 = huge gaps.
    shakuhachi_a = MelodyGenerator(
        GeneratorParams(density=0.05, leap_probability=0.02),
        drama_shape="crescendo", drama_peak=0.15,
        harmony_note_probability=0.98,
        note_range_low=62, note_range_high=70,
        phrase_length=24.0, register_smoothness=0.99,
        steps_probability=0.98, first_note="tonic",
        motif_probability=0.5, motif_variation="fragment",
    ).render(c_a, KEY, s1)

    shakuhachi_b = MelodyGenerator(
        GeneratorParams(density=0.12, leap_probability=0.06),
        drama_shape="crescendo", drama_peak=0.3,
        harmony_note_probability=0.92,
        note_range_low=60, note_range_high=74,
        phrase_length=16.0, register_smoothness=0.96,
        steps_probability=0.95, first_note="tonic",
        motif_probability=0.7, motif_variation="transpose",
        ornament_probability=0.1,
    ).render(c_b, KEY, s2 - s1)

    shakuhachi_d = MelodyGenerator(
        GeneratorParams(density=0.04, leap_probability=0.01),
        drama_shape="crescendo", drama_peak=0.08,
        harmony_note_probability=0.99,
        note_range_low=62, note_range_high=67,
        phrase_length=32.0, register_smoothness=0.99,
        steps_probability=0.99, first_note="tonic",
    ).render(c_d, KEY, dur - s3)

    for n in shakuhachi_b: n.start += s1
    for n in shakuhachi_d: n.start += s3
    shakuhachi = shakuhachi_a + shakuhachi_b + shakuhachi_d

    # 2. Koto — drops of water on stone, enters mid-track
    koto = ArpeggiatorGenerator(
        GeneratorParams(density=0.12),
        pattern="up", note_duration=1.5,
        voicing="open", octaves=1,
    ).render(c_b, KEY, s2 - s1)
    for n in koto: n.start += s1

    # 3. Strings — barely present, lower register
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.08, key_range_low=38, key_range_high=55),
        articulation="sustained", divisi=1, dynamic_curve="crescendo",
    ).render(c_b, KEY, s2 - s1)
    for n in strings: n.start += s1

    # 4. Drone — sub-bass hum
    drone = DroneGenerator(
        GeneratorParams(density=0.04), variant="tonic",
    ).render(c_b, KEY, s2 - s1)
    for n in drone: n.start += s1

    # 5. Taiko — ONE hit every 16 beats. Just one.
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.03), kit="808", pattern="minimal",
    ).render(c_c, KEY, s3 - s2)
    for n in drums: n.start += s2

    raw = {"shakuhachi": shakuhachi, "koto": koto, "strings": strings,
           "drone": drone, "drums": drums}
    mastered, pan = _master(raw, 58.0, lufs=-22.0)
    return mastered, pan, 58.0, KEY, {
        "shakuhachi": 77,   # Shakuhachi
        "koto": 107,        # Koto
        "strings": 49,      # String Ensemble 1
        "drone": 89,        # New Age Pad
        "drums": 0,
    }


# =====================================================================
# Track 2 — Юки-Онна (雪女 — Снежная женщина)
# 66 BPM, 3/4, D Hirajoshi
# Дух-убийца в метели. Красота и смерть неразличимы.
# =====================================================================
def produce_yuki_onna():
    """Ghost voice + prepared piano + one crystal bell. No percussion."""
    print("  II. Юки-Онна (雪女) [Hirajoshi — 66 BPM — D]")

    dur = 160.0
    bpc = 3.0  # 3/4
    chords = _chords("i iv v i " * 8, dur, beats_per_chord=bpc)

    s1, s2, s3 = 40.0, 100.0, 140.0
    c_a = [c for c in chords if c.start < s1]
    c_b = [c for c in chords if s1 <= c.start < s2]
    c_c = [c for c in chords if s2 <= c.start < s3]
    c_d = [c for c in chords if c.start >= s3]

    # 1. Voice — high, vowel-only, microtonal deviations
    #    Very low density, almost speaking. ornament_prob creates the
    #    "almost wrong but intentional" feel
    voice_a = MelodyGenerator(
        GeneratorParams(density=0.12, leap_probability=0.08),
        drama_shape="crescendo", drama_peak=0.25,
        harmony_note_probability=0.9,
        ornament_probability=0.2,
        note_range_low=69, note_range_high=81,
        phrase_length=12.0, register_smoothness=0.97,
        steps_probability=0.93, first_note="tonic",
        motif_probability=0.6, motif_variation="transpose",
    ).render(c_a, KEY, s1)

    voice_b = MelodyGenerator(
        GeneratorParams(density=0.35, leap_probability=0.3),
        drama_shape="tension_release", drama_peak=0.5,
        harmony_note_probability=0.7,
        ornament_probability=0.45,
        note_range_low=67, note_range_high=84,
        phrase_length=6.0, register_smoothness=0.88,
        steps_probability=0.82, syncopation=0.2,
        motif_probability=0.7, motif_variation="any",
    ).render(c_b, KEY, s2 - s1)

    # Bridge: voice drops to sub-tone (very sparse)
    voice_c = MelodyGenerator(
        GeneratorParams(density=0.06, leap_probability=0.02),
        drama_shape="crescendo", drama_peak=0.1,
        harmony_note_probability=0.97,
        ornament_probability=0.05,
        note_range_low=64, note_range_high=72,
        phrase_length=24.0, register_smoothness=0.99,
        steps_probability=0.98, first_note="tonic",
    ).render(c_c, KEY, s3 - s2)

    for n in voice_b: n.start += s1
    for n in voice_c: n.start += s2
    voice = voice_a + voice_b + voice_c

    # 2. Prepared piano — dull thuds, staccato clusters
    #    Using piano_comp with very low density and staccato feel
    piano = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.15),
        drama_shape="crescendo", drama_peak=0.35,
        harmony_note_probability=0.75,
        note_range_low=60, note_range_high=79,
        phrase_length=9.0, register_smoothness=0.9,
        steps_probability=0.85, rhythm_variety=0.6,
        syncopation=0.3,
        motif_probability=0.6, motif_variation="any",
    ).render(chords, KEY, dur)

    # 3. Crystal bell — ONE note, around the midpoint (~80s)
    bell = [types.NoteInfo(
        pitch=84, start=80.0, duration=2.0, velocity=90
    )]

    # 4. Strings — frozen, barely moving
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.1, key_range_low=48, key_range_high=62),
        articulation="sustained", divisi=1, dynamic_curve="crescendo",
    ).render(chords, KEY, dur)

    # 5. Drone — wind howl
    drone = DroneGenerator(
        GeneratorParams(density=0.04), variant="tonic",
    ).render(chords, KEY, dur)

    raw = {"voice": voice, "piano": piano, "bell": bell,
           "strings": strings, "drone": drone}
    mastered, pan = _master(raw, 66.0, lufs=-19.0)
    return mastered, pan, 66.0, KEY, {
        "voice": 54,     # Voice Oohs
        "piano": 1,      # Acoustic Grand Piano
        "bell": 115,     # Woodblock (as metallic hit)
        "strings": 49,   # String Ensemble 1
        "drone": 89,     # New Age Pad
    }


# =====================================================================
# Track 3 — Сэппуку (切腹)
# 40 BPM, 5/4, D Hirajoshi
# Не горе — решимость. Самый тёмный трек.
# =====================================================================
def produce_seppuku():
    """Silence → o-daiko hit → strings descending → cluster fortissimo → silence → one koto note."""
    print("  III. Сэппуку (切腹) [Hirajoshi — 40 BPM — D]")

    dur = 180.0  # ~7:30 at 40 BPM
    bpc = 5.0  # 5/4

    # Very few chords — static, suffocating
    chords = _chords("i i iv i i i i i", dur, beats_per_chord=bpc)

    # Sections: silence(0-20) → strings(20-120) → climax(120-125) → silence+decay(125-180)
    s_climax = 120.0
    s_after = 125.0
    c_main = [c for c in chords if c.start < s_climax]
    c_after = [c for c in chords if c.start >= s_after]

    # 1. Strings — unison descent. Very low, very slow. Down. Down. Down.
    #    density 0.15 = barely moving. leap_probability 0.02 = no jumps.
    #    Low register = dark. steps_probability 0.98 = pure steps.
    strings = MelodyGenerator(
        GeneratorParams(density=0.15, leap_probability=0.02),
        drama_shape="crescendo", drama_peak=0.85,
        harmony_note_probability=0.95,
        note_range_low=38, note_range_high=55,
        phrase_length=20.0, register_smoothness=0.98,
        steps_probability=0.98, first_note="step_above_tonic",
        motif_probability=0.3, motif_variation="fragment",
        ornament_probability=0.0,
    ).render(c_main, KEY, s_climax)

    # 2. O-daiko — single massive hit at the start (after silence)
    drums_intro = [types.NoteInfo(
        pitch=36, start=20.0, duration=6.0, velocity=120
    )]

    # Cluster chord at climax — fortissimo hit then silence
    cluster_notes = [
        types.NoteInfo(pitch=38, start=s_climax, duration=1.5, velocity=127),
        types.NoteInfo(pitch=39, start=s_climax, duration=1.5, velocity=127),
        types.NoteInfo(pitch=42, start=s_climax, duration=1.5, velocity=127),
        types.NoteInfo(pitch=43, start=s_climax, duration=1.5, velocity=127),
        types.NoteInfo(pitch=46, start=s_climax, duration=1.5, velocity=127),
        types.NoteInfo(pitch=50, start=s_climax, duration=1.5, velocity=127),
    ]

    # After silence — single koto note, pianissimo
    koto_decay = [types.NoteInfo(
        pitch=62, start=s_after + 20.0, duration=12.0, velocity=30
    )]

    raw = {"strings": strings + cluster_notes, "drums": drums_intro,
           "koto": koto_decay}
    mastered, pan = _master(raw, 40.0, lufs=-14.0)
    return mastered, pan, 40.0, KEY, {
        "strings": 44,   # Tremolo Strings (sul ponticello feel)
        "drums": 0,      # O-daiko
        "koto": 107,     # Koto
    }


# =====================================================================
# Track 4 — Фурю-моно (不条理 — Абсурд)
# 76 BPM (сбой темпа), D Hirajoshi
# Призрак между мирами. Два слоя не слышат друг друга.
# =====================================================================
def produce_furyu_mono():
    """Koto at one pace, piano at another, voice out of sync with both."""
    print("  IV. Фурю-моно (不条理) [Hirajoshi — 76 BPM — D]")

    dur = 168.0  # ~3:40
    chords = _chords("i iv v i " * 6, dur)

    # Layer 1: Koto — stable, measured arpeggios
    koto = ArpeggiatorGenerator(
        GeneratorParams(density=0.25),
        pattern="up", note_duration=0.75,
        voicing="open", octaves=1,
    ).render(chords, KEY, dur)

    # Layer 2: Piano — slightly different density/pattern = temporal drift
    #    Using melody generator with different phrase lengths to create
    #    the illusion of two separate clocks
    piano = MelodyGenerator(
        GeneratorParams(density=0.18, leap_probability=0.12),
        drama_shape="crescendo", drama_peak=0.35,
        harmony_note_probability=0.85,
        note_range_low=60, note_range_high=79,
        phrase_length=7.0, register_smoothness=0.93,
        steps_probability=0.9, rhythm_variety=0.5,
        syncopation=0.15,
        motif_probability=0.6, motif_variation="any",
    ).render(chords, KEY, dur)

    # Layer 3: Voice — baritone, reading haiku rhythm, out of sync
    voice = MelodyGenerator(
        GeneratorParams(density=0.1, leap_probability=0.05),
        drama_shape="crescendo", drama_peak=0.25,
        harmony_note_probability=0.93,
        note_range_low=45, note_range_high=58,
        phrase_length=9.0, register_smoothness=0.97,
        steps_probability=0.96, first_note="tonic",
        motif_probability=0.5, motif_variation="transpose",
    ).render(chords, KEY, dur)

    # 4. Percussion — clockwork: quiet metallic ticks
    drums = ElectronicDrumsGenerator(
        GeneratorParams(density=0.12), kit="808", pattern="minimal",
    ).render(chords, KEY, dur)

    raw = {"koto": koto, "piano": piano, "voice": voice, "drums": drums}
    mastered, pan = _master(raw, 76.0, lufs=-18.0)
    return mastered, pan, 76.0, KEY, {
        "koto": 107,     # Koto
        "piano": 1,      # Acoustic Grand Piano
        "voice": 54,     # Voice Oohs
        "drums": 0,
    }


# =====================================================================
# Track 5 — Му (無 — Ничто)
# Rubato, solo shakuhachi, D Hirajoshi
# Дзен-буддийская пустота. Хонкёку — без структуры.
# =====================================================================
def produce_mu():
    """One shakuhachi. Nothing else. Honkyoku — formless."""
    print("  V. Му (無) [Hirajoshi — Rubato Solo]")

    dur = 240.0  # ~6:40 at effective 56 BPM
    chords = _chords("i i i i i i i i i i i i i i i i", dur)

    # Shakuhachi — honkyoku form
    # density 0.04 = almost nothing. Each note is an event.
    # phrase_length 30 = vast silences between phrases
    # ornament_probability 0.15 = occasional breath/vibrato
    shakuhachi = MelodyGenerator(
        GeneratorParams(density=0.04, leap_probability=0.02),
        drama_shape="crescendo", drama_peak=0.2,
        harmony_note_probability=0.97,
        ornament_probability=0.15,
        note_range_low=60, note_range_high=74,
        phrase_length=30.0, register_smoothness=0.99,
        steps_probability=0.98, first_note="tonic",
        motif_probability=0.3, motif_variation="fragment",
    ).render(chords, KEY, dur)

    raw = {"shakuhachi": shakuhachi}
    mastered, pan = _master(raw, 56.0, lufs=-26.0)
    return mastered, pan, 56.0, KEY, {
        "shakuhachi": 77,  # Shakuhachi
    }


# =====================================================================
# Main
# =====================================================================
def main():
    album_dir = Path("output/album_kage")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   影 KAGE — ТЕНЬ")
    print("   Hirajoshi [0,2,3,7,8] — 5 tracks")
    print("   Тьма не в звуке. Она в молчании между нотами.")
    print("=" * 60 + "\n")

    tracks = [
        ("01_Musashi_Мусаси",        produce_musashi),
        ("02_Yuki-Onna_Юки-Онна",    produce_yuki_onna),
        ("03_Seppuku_Сэппуку",       produce_seppuku),
        ("04_Furyu-mono_Фурю-моно",  produce_furyu_mono),
        ("05_Mu_Му",                 produce_mu),
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
            77: "Shakuhachi", 107: "Koto", 49: "Strings Ens 1",
            89: "New Age Pad", 54: "Voice Oohs", 1: "Piano",
            115: "Bell", 44: "Trem Strings", 0: "Drums",
        }
        print(f"    -> {name}.mid  ({bpm} BPM, {len(mastered)} tracks)")
        for track_name, program in instr.items():
            gm_name = inst_names.get(program, f"GM#{program}")
            note_count = sum(len(v) for k, v in mastered.items() if k == track_name)
            print(f"       {track_name:16s}  {gm_name:20s}  {note_count:>4d} notes")

    print("\n" + "=" * 60)
    print(f"   影 KAGE — COMPLETE.")
    print(f"   Files in: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
