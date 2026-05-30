# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_gypsy_dance.py — ЦЫГАНСКИЙ ТАНОЦ (Gypsy Dance)

10 танцевальных треков в цыганском стиле для настроения.
Только Gypsy mode (root=4, E Gypsy) с разными тональностями.

Инструменты: скрипка соло, гитара стаккато, бас, арпеджио,
струнные, арфа, ударные, мандолина-подражание.

Все треки — танцевальные, от 100 до 160 BPM.
"""

from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode, ChordLabel
from melodica.generators import GeneratorParams
from melodica.generators.orchestral_strings import ViolinGenerator, CelloGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.harp import HarpGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_pizzicato import StringsPizzicatoGenerator

from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk


# ---------------------------------------------------------------------------
# Scales — all Gypsy mode, different roots for variety
# ---------------------------------------------------------------------------
E_GY  = Scale(4,  Mode.GYPSY)
A_GY  = Scale(9,  Mode.GYPSY)
B_GY  = Scale(11, Mode.GYPSY)
D_GY  = Scale(2,  Mode.GYPSY)
G_GY  = Scale(7,  Mode.GYPSY)
C_GY  = Scale(0,  Mode.GYPSY)
F_GY  = Scale(5,  Mode.GYPSY)
FS_GY = Scale(6,  Mode.GYPSY)
BB_GY = Scale(10, Mode.GYPSY)
EF_GY = Scale(3,  Mode.GYPSY)


def _bc(prog, dur, key):
    parts = prog.split()
    b = dur / len(parts)
    ch = []
    for i, p in enumerate(parts):
        c = key.parse_roman(p)
        ch.append(ChordLabel(root=c.root, quality=c.quality, start=i * b, duration=b))
    return ch

def _cl(notes, lo=1, hi=127):
    for n in notes:
        n.velocity = max(lo, min(hi, n.velocity))
    return notes


def _mix(raw, bpm):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "Violin": 0.88, "Guitar": 0.82, "Bass": 0.80, "Arpeggio": 0.75,
        "Drums": 0.72, "Strings": 0.78, "Harp": 0.80, "Pad": 0.68,
        "Melody": 0.85, "Pizzicato": 0.75, "Cello": 0.82,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    m = MasteringDesk(target_lufs=-14.0)
    return m.apply_mastering(mixed)


# ===========================================================================
# 1. Огненный Круг (Fire Circle) — E Gypsy, 130 BPM
# ===========================================================================
def t01():
    print("  01. Огненный Круг / Fire Circle")
    dur, key, bpm = 56.0, E_GY, 130.0
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i", dur, key)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.7, key_range_low=55, key_range_high=88), articulation="sustained", vibrato=True, dynamic_curve="flat", note_density=2.5).render(ch, key, dur), 50, 100)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.6, key_range_low=40, key_range_high=76), strum_pattern="folk", palm_mute_ratio=0.3).render(ch, key, dur), 45, 85)
    bass = _cl(BassGenerator(GeneratorParams(density=0.6, key_range_low=28, key_range_high=40), style="walking").render(ch, key, dur), 50, 80)
    drums = _cl(DrumKitPatternGenerator(GeneratorParams(density=0.7), style="rock", hihat_pattern="eighth", fill_frequency=0.3).render(ch, key, dur), 40, 90)
    return {"Violin": violin, "Guitar": guitar, "Bass": bass, "Drums": drums}, bpm


# ===========================================================================
# 2. Цыганская Ночь (Gypsy Night) — A Gypsy, 120 BPM
# ===========================================================================
def t02():
    print("  02. Цыганская Ночь / Gypsy Night")
    dur, key, bpm = 60.0, A_GY, 120.0
    ch = _bc("i bII V i iv bVI bII V i iv bVI V i bII V i", dur, key)
    melody = _cl(MelodyGenerator(GeneratorParams(density=0.7, complexity=0.8, velocity_range=(70, 110)), phrase_length=4.0, note_range_low=60, note_range_high=90, motif_probability=0.8, ornament_probability=0.4, register_smoothness=0.6, syncopation=0.3).render(ch, key, dur), 55, 100)
    arp = _cl(ArpeggiatorGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=72), pattern="up", note_duration=0.2, voicing="closed", octaves=2).render(ch, key, dur), 40, 70)
    bass = _cl(BassGenerator(GeneratorParams(density=0.55, key_range_low=28, key_range_high=40), style="root_fifth").render(ch, key, dur), 50, 80)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=72), strum_pattern="folk", palm_mute_ratio=0.4).render(ch, key, dur), 40, 80)
    return {"Melody": melody, "Arpeggio": arp, "Bass": bass, "Guitar": guitar}, bpm


# ===========================================================================
# 3. Танец У Костра (Bonfire Dance) — B Gypsy, 140 BPM
# ===========================================================================
def t03():
    print("  03. Танец У Костра / Bonfire Dance")
    dur, key, bpm = 48.0, B_GY, 140.0
    ch = _bc("i bII V i iv bVI V i bII iv V i", dur, key)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.75, key_range_low=58, key_range_high=92), articulation="staccato", vibrato=True, dynamic_curve="flat", note_density=3.0).render(ch, key, dur), 55, 100)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.65, key_range_low=40, key_range_high=76), strum_pattern="folk", palm_mute_ratio=0.2).render(ch, key, dur), 50, 90)
    bass = _cl(BassGenerator(GeneratorParams(density=0.6, key_range_low=28, key_range_high=40), style="walking").render(ch, key, dur), 50, 80)
    drums = _cl(DrumKitPatternGenerator(GeneratorParams(density=0.7), style="rock", hihat_pattern="sixteenth", fill_frequency=0.4).render(ch, key, dur), 45, 95)
    return {"Violin": violin, "Guitar": guitar, "Bass": bass, "Drums": drums}, bpm


# ===========================================================================
# 4. Карта Судьбы (Cards of Fate) — D Gypsy, 108 BPM
# ===========================================================================
def t04():
    print("  04. Карта Судьбы / Cards of Fate")
    dur, key, bpm = 64.0, D_GY, 108.0
    ch = _bc("i iv V i bVI bVII i bII V i iv bVI V i", dur, key)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.5, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="up", spread_speed=0.08).render(ch, key, dur), 40, 75)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.6, key_range_low=55, key_range_high=88), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=2.0).render(ch, key, dur), 45, 90)
    bass = _cl(BassGenerator(GeneratorParams(density=0.5, key_range_low=28, key_range_high=40), style="walking").render(ch, key, dur), 45, 75)
    pizz = _cl(StringsPizzicatoGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=68), pattern="ostinato", staccato_length=0.12).render(ch, key, dur), 40, 70)
    return {"Harp": harp, "Violin": violin, "Bass": bass, "Pizzicato": pizz}, bpm


# ===========================================================================
# 5. Степь Поёт (Steppe Sings) — G Gypsy, 135 BPM
# ===========================================================================
def t05():
    print("  05. Степь Поёт / Steppe Sings")
    dur, key, bpm = 52.0, G_GY, 135.0
    ch = _bc("i bII V i iv bVI bII V i bVI V i", dur, key)
    melody = _cl(MelodyGenerator(GeneratorParams(density=0.75, complexity=0.85, velocity_range=(75, 115)), phrase_length=4.0, note_range_low=62, note_range_high=94, motif_probability=0.85, ornament_probability=0.5, register_smoothness=0.5, syncopation=0.25).render(ch, key, dur), 60, 105)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.6, key_range_low=40, key_range_high=76), strum_pattern="folk", palm_mute_ratio=0.25).render(ch, key, dur), 50, 88)
    bass = _cl(BassGenerator(GeneratorParams(density=0.55, key_range_low=28, key_range_high=40), style="root_fifth_octave").render(ch, key, dur), 50, 82)
    drums = _cl(DrumKitPatternGenerator(GeneratorParams(density=0.65), style="rock", hihat_pattern="eighth", fill_frequency=0.25).render(ch, key, dur), 45, 88)
    return {"Melody": melody, "Guitar": guitar, "Bass": bass, "Drums": drums}, bpm


# ===========================================================================
# 6. Слёзы Радости (Tears of Joy) — C Gypsy, 100 BPM
# ===========================================================================
def t06():
    print("  06. Слёзы Радости / Tears of Joy")
    dur, key, bpm = 68.0, C_GY, 100.0
    ch = _bc("i iv i V i bVI bVII i bII V i iv bVI V i", dur, key)
    cello = _cl(CelloGenerator(GeneratorParams(density=0.55, key_range_low=36, key_range_high=60), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=1.8).render(ch, key, dur), 45, 85)
    arp = _cl(ArpeggiatorGenerator(GeneratorParams(density=0.5, key_range_low=36, key_range_high=72), pattern="up_down", note_duration=0.25, voicing="closed", octaves=2).render(ch, key, dur), 40, 70)
    strings = _cl(StringsEnsembleGenerator(GeneratorParams(density=0.5, key_range_low=44, key_range_high=76), section_size="full", articulation="sustained", divisi=4, dynamic_curve="crescendo").render(ch, key, dur), 35, 70)
    bass = _cl(BassGenerator(GeneratorParams(density=0.5, key_range_low=24, key_range_high=36), style="walking").render(ch, key, dur), 40, 70)
    return {"Cello": cello, "Arpeggio": arp, "Strings": strings, "Bass": bass}, bpm


# ===========================================================================
# 7. Бубен И Монета (Tambourine & Coin) — F Gypsy, 150 BPM
# ===========================================================================
def t07():
    print("  07. Бубен И Монета / Tambourine & Coin")
    dur, key, bpm = 44.0, F_GY, 150.0
    ch = _bc("i bII V i iv bVI V i bII V i iv bVI V i", dur, key)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.8, key_range_low=58, key_range_high=92), articulation="staccato", vibrato=True, dynamic_curve="flat", note_density=3.5).render(ch, key, dur), 60, 105)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.7, key_range_low=40, key_range_high=76), strum_pattern="folk", palm_mute_ratio=0.15).render(ch, key, dur), 55, 92)
    bass = _cl(BassGenerator(GeneratorParams(density=0.65, key_range_low=28, key_range_high=40), style="walking").render(ch, key, dur), 55, 85)
    drums = _cl(DrumKitPatternGenerator(GeneratorParams(density=0.75), style="rock", hihat_pattern="sixteenth", fill_frequency=0.35).render(ch, key, dur), 50, 98)
    return {"Violin": violin, "Guitar": guitar, "Bass": bass, "Drums": drums}, bpm


# ===========================================================================
# 8. Дорога Домой (Road Home) — F# Gypsy, 112 BPM
# ===========================================================================
def t08():
    print("  08. Дорога Домой / Road Home")
    dur, key, bpm = 58.0, FS_GY, 112.0
    ch = _bc("i iv V i bVI bVII i bII V i iv bVI V i", dur, key)
    harp = _cl(HarpGenerator(GeneratorParams(density=0.45, key_range_low=36, key_range_high=80), pattern="arpeggio", direction="down", spread_speed=0.1).render(ch, key, dur), 35, 65)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.6, key_range_low=55, key_range_high=88), articulation="sustained", vibrato=True, dynamic_curve="crescendo", note_density=2.0).render(ch, key, dur), 45, 90)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=72), strum_pattern="folk", palm_mute_ratio=0.35).render(ch, key, dur), 40, 78)
    bass = _cl(BassGenerator(GeneratorParams(density=0.5, key_range_low=28, key_range_high=40), style="root_fifth").render(ch, key, dur), 45, 75)
    return {"Harp": harp, "Violin": violin, "Guitar": guitar, "Bass": bass}, bpm


# ===========================================================================
# 9. Шатёр Звёзд (Tent of Stars) — Bb Gypsy, 125 BPM
# ===========================================================================
def t09():
    print("  09. Шатёр Звёзд / Tent of Stars")
    dur, key, bpm = 54.0, BB_GY, 125.0
    ch = _bc("i bII iv V i bVI bVII i bII V i iv bVI V i", dur, key)
    melody = _cl(MelodyGenerator(GeneratorParams(density=0.7, complexity=0.8, velocity_range=(70, 110)), phrase_length=4.0, note_range_low=60, note_range_high=92, motif_probability=0.8, ornament_probability=0.35, register_smoothness=0.55, syncopation=0.3).render(ch, key, dur), 55, 100)
    arp = _cl(ArpeggiatorGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=76), pattern="up", note_duration=0.22, voicing="spread", octaves=2).render(ch, key, dur), 40, 68)
    bass = _cl(BassGenerator(GeneratorParams(density=0.55, key_range_low=28, key_range_high=40), style="walking").render(ch, key, dur), 48, 78)
    strings = _cl(StringsEnsembleGenerator(GeneratorParams(density=0.45, key_range_low=44, key_range_high=76), section_size="full", articulation="sustained", divisi=4, dynamic_curve="flat").render(ch, key, dur), 35, 65)
    return {"Melody": melody, "Arpeggio": arp, "Bass": bass, "Strings": strings}, bpm


# ===========================================================================
# 10. Последний Танец (Last Dance) — Eb Gypsy, 160 BPM
# ===========================================================================
def t10():
    print("  10. Последний Танец / Last Dance")
    dur, key, bpm = 40.0, EF_GY, 160.0
    ch = _bc("i bII V i iv bVI V i bII V i bVI V i", dur, key)
    violin = _cl(ViolinGenerator(GeneratorParams(density=0.85, key_range_low=58, key_range_high=92), articulation="staccato", vibrato=True, dynamic_curve="flat", note_density=3.5).render(ch, key, dur), 60, 108)
    guitar = _cl(GuitarStrummingGenerator(GeneratorParams(density=0.7, key_range_low=40, key_range_high=76), strum_pattern="folk", palm_mute_ratio=0.2).render(ch, key, dur), 55, 95)
    bass = _cl(BassGenerator(GeneratorParams(density=0.65, key_range_low=28, key_range_high=40), style="walking").render(ch, key, dur), 55, 85)
    drums = _cl(DrumKitPatternGenerator(GeneratorParams(density=0.75), style="rock", hihat_pattern="sixteenth", fill_frequency=0.4).render(ch, key, dur), 50, 100)
    pizz = _cl(StringsPizzicatoGenerator(GeneratorParams(density=0.5, key_range_low=40, key_range_high=68), pattern="ostinato", staccato_length=0.08).render(ch, key, dur), 40, 75)
    return {"Violin": violin, "Guitar": guitar, "Bass": bass, "Drums": drums, "Pizzicato": pizz}, bpm


# ===========================================================================
# Registry
# ===========================================================================
TRACKS = [
    (t01, "01_Ognennyy_Krug.mid",              {"Violin": 40, "Guitar": 24, "Bass": 33, "Drums": 10}),
    (t02, "02_Tsyganskaya_Noch.mid",           {"Melody": 40, "Arpeggio": 24, "Bass": 33, "Guitar": 24}),
    (t03, "03_Tanets_U_Kostra.mid",             {"Violin": 40, "Guitar": 24, "Bass": 33, "Drums": 10}),
    (t04, "04_Karta_Sudby.mid",                 {"Harp": 46, "Violin": 40, "Bass": 33, "Pizzicato": 45}),
    (t05, "05_Step_Poyot.mid",                  {"Melody": 40, "Guitar": 24, "Bass": 33, "Drums": 10}),
    (t06, "06_Slyozy_Radosti.mid",              {"Cello": 42, "Arpeggio": 24, "Strings": 48, "Bass": 33}),
    (t07, "07_Buben_I_Moneta.mid",              {"Violin": 40, "Guitar": 24, "Bass": 33, "Drums": 10}),
    (t08, "08_Doroga_Domoy.mid",                {"Harp": 46, "Violin": 40, "Guitar": 24, "Bass": 33}),
    (t09, "09_Shatyor_Zvyozd.mid",              {"Melody": 40, "Arpeggio": 24, "Bass": 33, "Strings": 48}),
    (t10, "10_Posledniy_Tanets.mid",            {"Violin": 40, "Guitar": 24, "Bass": 33, "Drums": 10, "Pizzicato": 45}),
]


def main():
    album_dir = Path("output/album_gypsy_dance")
    album_dir.mkdir(exist_ok=True, parents=True)

    print()
    print("=" * 80)
    print("      Ц Ы Г А Н С К И Й   Т А Н Е Ц")
    print("      Gypsy Dance — 10 танцев для настроения")
    print("      Все треки в Gypsy mode | 100–160 BPM")
    print("=" * 80)

    total_notes = 0
    for i, (producer, filename, instruments) in enumerate(TRACKS):
        print("-" * 80)
        raw, bpm = producer()
        mastered, pan = _mix(raw, bpm)
        export_multitrack_midi(
            mastered,
            str(album_dir / filename),
            bpm=bpm,
            cc_events=pan,
            instruments=instruments,
        )
        note_count = sum(len(n) for n in raw.values())
        total_notes += note_count
        print(f"    -> {filename}  ({note_count} notes, {bpm} BPM)")

    print()
    print("=" * 80)
    print(f"  COMPLETE: Цыганский Танец")
    print(f"  {total_notes} total notes across 10 tracks")
    print(f"  Output: {album_dir.resolve()}")
    print("=" * 80)


if __name__ == "__main__":
    main()
