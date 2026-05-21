# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
instrument_tracer.py — Психоакустический трейсер и анализатор MIDI-инструментов.

Этот скрипт анализирует сгенерированные MIDI-файлы и оценивает аранжировку
с точки зрения психоакустической совместимости:
1. Частотные конфликты (Low-end mud, Mid-range clutter).
2. Тембральный контраст (Plucked vs Sustained).
3. Правильное наслоение (Layering) и комплементарность.
"""

import sys
from pathlib import Path
import mido

# База знаний по инструментам General MIDI (GM)
# band: Low, Mid, High, Full
# type: Percussive, Plucked, Sustained, Pad, Transient
GM_PROFILES = {
    0: {"name": "Acoustic Grand Piano", "band": "Full", "type": "Percussive"},
    1: {"name": "Bright Acoustic Piano", "band": "Full", "type": "Percussive"},
    2: {"name": "Electric Grand Piano", "band": "Full", "type": "Percussive"},
    3: {"name": "Honky-tonk Piano", "band": "Full", "type": "Percussive"},
    4: {"name": "Electric Piano 1", "band": "Full", "type": "Percussive"},
    5: {"name": "Electric Piano 2", "band": "Full", "type": "Percussive"},
    6: {"name": "Harpsichord", "band": "Full", "type": "Percussive"},
    7: {"name": "Clavinet", "band": "Full", "type": "Percussive"},
    8: {"name": "Celesta", "band": "High", "type": "Transient"},
    9: {"name": "Glockenspiel", "band": "High", "type": "Transient"},
    10: {"name": "Music Box", "band": "High", "type": "Transient"},
    11: {"name": "Vibraphone", "band": "High", "type": "Transient"},
    12: {"name": "Marimba", "band": "High", "type": "Transient"},
    13: {"name": "Xylophone", "band": "High", "type": "Transient"},
    14: {"name": "Tubular Bells", "band": "High", "type": "Transient"},
    15: {"name": "Dulcimer", "band": "High", "type": "Transient"},
    16: {"name": "Drawbar Organ", "band": "Full", "type": "Sustained"},
    17: {"name": "Percussive Organ", "band": "Full", "type": "Sustained"},
    18: {"name": "Rock Organ", "band": "Full", "type": "Sustained"},
    19: {"name": "Church Organ", "band": "Full", "type": "Sustained"},
    20: {"name": "Reed Organ", "band": "Full", "type": "Sustained"},
    21: {"name": "Accordion", "band": "Full", "type": "Sustained"},
    22: {"name": "Harmonica", "band": "Full", "type": "Sustained"},
    23: {"name": "Tango Accordion", "band": "Full", "type": "Sustained"},
    24: {"name": "Acoustic Guitar (nylon)", "band": "Mid", "type": "Plucked"},
    25: {"name": "Acoustic Guitar (steel)", "band": "Mid", "type": "Plucked"},
    26: {"name": "Electric Guitar (jazz)", "band": "Mid", "type": "Plucked"},
    27: {"name": "Electric Guitar (clean)", "band": "Mid", "type": "Plucked"},
    28: {"name": "Electric Guitar (muted)", "band": "Mid", "type": "Plucked"},
    29: {"name": "Overdriven Guitar", "band": "Mid", "type": "Plucked"},
    30: {"name": "Distortion Guitar", "band": "Mid", "type": "Plucked"},
    31: {"name": "Guitar Harmonics", "band": "Mid", "type": "Plucked"},
    32: {"name": "Acoustic Bass", "band": "Low", "type": "Plucked"},
    33: {"name": "Electric Bass (finger)", "band": "Low", "type": "Plucked"},
    34: {"name": "Electric Bass (pick)", "band": "Low", "type": "Plucked"},
    35: {"name": "Fretless Bass", "band": "Low", "type": "Sustained"},
    36: {"name": "Slap Bass 1", "band": "Low", "type": "Plucked"},
    37: {"name": "Slap Bass 2", "band": "Low", "type": "Plucked"},
    38: {"name": "Synth Bass 1", "band": "Low", "type": "Sustained"},
    39: {"name": "Synth Bass 2", "band": "Low", "type": "Sustained"},
    40: {"name": "Violin", "band": "High", "type": "Sustained"},
    41: {"name": "Viola", "band": "Mid_High", "type": "Sustained"},
    42: {"name": "Cello", "band": "Low_Mid", "type": "Sustained"},
    43: {"name": "Contrabass", "band": "Low", "type": "Sustained"},
    44: {"name": "Tremolo Strings", "band": "Mid_High", "type": "Sustained"},
    45: {"name": "Pizzicato Strings", "band": "Mid_High", "type": "Plucked"},
    46: {"name": "Orchestral Harp", "band": "Mid_High", "type": "Plucked"},
    47: {"name": "Timpani", "band": "Low", "type": "Percussive"},
    48: {"name": "String Ensemble 1", "band": "Full", "type": "Sustained"},
    49: {"name": "String Ensemble 2", "band": "Full", "type": "Sustained"},
    50: {"name": "Synth Strings 1", "band": "Full", "type": "Sustained"},
    51: {"name": "Synth Strings 2", "band": "Full", "type": "Sustained"},
    52: {"name": "Choir Aahs", "band": "Full", "type": "Sustained"},
    53: {"name": "Voice Oohs", "band": "Full", "type": "Sustained"},
    54: {"name": "Synth Choir", "band": "Full", "type": "Sustained"},
    55: {"name": "Orchestra Hit", "band": "Full", "type": "Sustained"},
    56: {"name": "Trumpet", "band": "Mid", "type": "Sustained"},
    57: {"name": "Trombone", "band": "Low_Mid", "type": "Sustained"},
    58: {"name": "Tuba", "band": "Low", "type": "Sustained"},
    59: {"name": "Muted Trumpet", "band": "Mid", "type": "Sustained"},
    60: {"name": "French Horn", "band": "Mid", "type": "Sustained"},
    61: {"name": "Brass Section", "band": "Mid", "type": "Sustained"},
    62: {"name": "Synth Brass 1", "band": "Mid", "type": "Sustained"},
    63: {"name": "Synth Brass 2", "band": "Mid", "type": "Sustained"},
    64: {"name": "Soprano Sax", "band": "Mid", "type": "Sustained"},
    65: {"name": "Alto Sax", "band": "Mid", "type": "Sustained"},
    66: {"name": "Tenor Sax", "band": "Mid", "type": "Sustained"},
    67: {"name": "Baritone Sax", "band": "Low_Mid", "type": "Sustained"},
    68: {"name": "Oboe", "band": "Mid", "type": "Sustained"},
    69: {"name": "English Horn", "band": "Mid", "type": "Sustained"},
    70: {"name": "Bassoon", "band": "Low_Mid", "type": "Sustained"},
    71: {"name": "Clarinet", "band": "Mid", "type": "Sustained"},
    72: {"name": "Piccolo", "band": "High", "type": "Sustained"},
    73: {"name": "Flute", "band": "High", "type": "Sustained"},
    74: {"name": "Recorder", "band": "High", "type": "Sustained"},
    75: {"name": "Pan Flute", "band": "High", "type": "Sustained"},
    76: {"name": "Blown Bottle", "band": "High", "type": "Sustained"},
    77: {"name": "Shakuhachi", "band": "High", "type": "Sustained"},
    78: {"name": "Whistle", "band": "High", "type": "Sustained"},
    79: {"name": "Ocarina", "band": "High", "type": "Sustained"},
    80: {"name": "Lead 1 (square)", "band": "Mid_High", "type": "Sustained"},
    81: {"name": "Lead 2 (sawtooth)", "band": "Mid_High", "type": "Sustained"},
    82: {"name": "Lead 3 (calliope)", "band": "Mid_High", "type": "Sustained"},
    83: {"name": "Lead 4 (chiff)", "band": "Mid_High", "type": "Sustained"},
    84: {"name": "Lead 5 (charang)", "band": "Mid_High", "type": "Sustained"},
    85: {"name": "Lead 6 (voice)", "band": "Mid_High", "type": "Sustained"},
    86: {"name": "Lead 7 (fifths)", "band": "Mid_High", "type": "Sustained"},
    87: {"name": "Lead 8 (bass + lead)", "band": "Mid_High", "type": "Sustained"},
    88: {"name": "Pad 1 (new age)", "band": "Full", "type": "Pad"},
    89: {"name": "Pad 2 (warm)", "band": "Full", "type": "Pad"},
    90: {"name": "Pad 3 (polysynth)", "band": "Full", "type": "Pad"},
    91: {"name": "Pad 4 (choir)", "band": "Full", "type": "Pad"},
    92: {"name": "Pad 5 (bowed)", "band": "Full", "type": "Pad"},
    93: {"name": "Pad 6 (metallic)", "band": "Full", "type": "Pad"},
    94: {"name": "Pad 7 (halo)", "band": "Full", "type": "Pad"},
    95: {"name": "Pad 8 (sweep)", "band": "Full", "type": "Pad"},
    96: {"name": "FX 1 (rain)", "band": "Full", "type": "Pad"},
    97: {"name": "FX 2 (soundtrack)", "band": "Full", "type": "Pad"},
    98: {"name": "FX 3 (crystal)", "band": "Full", "type": "Pad"},
    99: {"name": "FX 4 (atmosphere)", "band": "Full", "type": "Pad"},
    100: {"name": "FX 5 (brightness)", "band": "Full", "type": "Pad"},
    101: {"name": "FX 6 (goblins)", "band": "Full", "type": "Pad"},
    102: {"name": "FX 7 (echoes)", "band": "Full", "type": "Pad"},
    103: {"name": "FX 8 (sci-fi)", "band": "Full", "type": "Pad"},
    104: {"name": "Sitar", "band": "Mid", "type": "Plucked"},
    105: {"name": "Banjo", "band": "Mid", "type": "Plucked"},
    106: {"name": "Shamisen", "band": "Mid", "type": "Plucked"},
    107: {"name": "Koto", "band": "Mid", "type": "Plucked"},
    108: {"name": "Kalimba", "band": "Mid", "type": "Plucked"},
    109: {"name": "Bagpipe", "band": "Mid", "type": "Plucked"},
    110: {"name": "Fiddle", "band": "Mid", "type": "Plucked"},
    111: {"name": "Shanai", "band": "Mid", "type": "Plucked"},
    112: {"name": "Tinkle Bell", "band": "Mid", "type": "Percussive"},
    113: {"name": "Agogo", "band": "Mid", "type": "Percussive"},
    114: {"name": "Steel Drums", "band": "Mid", "type": "Percussive"},
    115: {"name": "Woodblock", "band": "Mid", "type": "Percussive"},
    116: {"name": "Taiko Drum", "band": "Mid", "type": "Percussive"},
    117: {"name": "Melodic Tom", "band": "Mid", "type": "Percussive"},
    118: {"name": "Synth Drum", "band": "Mid", "type": "Percussive"},
    119: {"name": "Reverse Cymbal", "band": "Mid", "type": "Percussive"},
    120: {"name": "Guitar Fret Noise", "band": "Full", "type": "Transient"},
    121: {"name": "Breath Noise", "band": "Full", "type": "Transient"},
    122: {"name": "Seashore", "band": "Full", "type": "Transient"},
    123: {"name": "Bird Tweet", "band": "Full", "type": "Transient"},
    124: {"name": "Telephone Ring", "band": "Full", "type": "Transient"},
    125: {"name": "Helicopter", "band": "Full", "type": "Transient"},
    126: {"name": "Applause", "band": "Full", "type": "Transient"},
    127: {"name": "Gunshot", "band": "Full", "type": "Transient"},
}

def analyze_orchestration(instruments_used):
    """
    Анализирует список инструментов и выдает психоакустическое заключение.
    """
    low_count = sum(1 for p in instruments_used if p["band"] in ("Low", "Low_Mid"))
    mid_count = sum(1 for p in instruments_used if p["band"] in ("Mid", "Mid_High", "Low_Mid"))
    high_count = sum(1 for p in instruments_used if p["band"] in ("High", "Mid_High"))
    full_count = sum(1 for p in instruments_used if p["band"] == "Full")

    sustained_count = sum(1 for p in instruments_used if p["type"] in ("Sustained", "Pad"))
    transient_count = sum(1 for p in instruments_used if p["type"] in ("Transient", "Percussive", "Plucked"))
    
    print("\n  [Психоакустический анализ]")
    
    # 1. Анализ баса (Low-end)
    if low_count + full_count > 2:
        print("  ⚠️ ВНИМАНИЕ (Low-end Clash): Слишком много басовых/полночастотных инструментов.")
        print("     Риск эффекта 'грязи' (mud). Убедитесь, что бас-гитара, виолончель и левая рука пианино разведены по октавам или играют в разное время.")
    elif low_count == 0 and full_count == 0:
        print("  ⚠️ ВНИМАНИЕ (Thin Mix): Отсутствуют инструменты басового регистра. Микс может звучать пусто и легковесно.")
    else:
        print("  ✅ Басовый фундамент: Сбалансирован. Конфликты в нижнем регистре минимальны.")

    # 2. Анализ средних частот (Mid-range)
    if mid_count + full_count > 3:
        print("  ⚠️ ВНИМАНИЕ (Mid-range Clutter): Сильная перегрузка средних частот (самая чувствительная зона для слуха).")
        print("     Инструменты будут 'бороться' за место. Используйте эквализацию, панорамирование (L/R) или сделайте часть партий тише.")
    else:
        print("  ✅ Средние частоты: Инструментам хватает пространства. Хорошая читаемость.")

    # 3. Тембральный баланс (Transient vs Sustained)
    if sustained_count > 0 and transient_count > 0:
        print("  ✅ Тембральный контраст: Отличный! Сочетание тягучих (Sustained/Pad) и отрывистых (Transient/Plucked) звуков создает глубокую 3D-сцену.")
    elif sustained_count == 0:
        print("  ℹ️ Инфо: Нет педальных/тянущихся звуков. Аранжировка очень ритмичная, сухая и 'острая' (хорошо для маршей или экшена).")
    elif transient_count == 0:
        print("  ℹ️ Инфо: Нет перкуссионных/щипковых звуков. Аранжировка очень 'плавающая' и эмбиентная. Не хватает ритмического якоря.")

    # 4. Проверка крутых комбинаций (Layering)
    names = [p["name"] for p in instruments_used]
    
    # Layering 1: Shimmer
    if "Music Box" in names or "Celesta" in names or "Glockenspiel" in names:
        if sum(1 for n in names if n in ("Music Box", "Celesta", "Glockenspiel")) > 1:
            print("  🌟 ПРО-ПРИЕМ (Shimmer Layer): Вы наслоили несколько звенящих 'волшебных' инструментов. Это даст очень богатый сказочный тембр!")

    # Layering 2: Epic Brass/Strings
    if any("Strings" in n for n in names) and any("Horn" in n or "Brass" in n or "Tuba" in n for n in names):
        print("  🌟 ПРО-ПРИЕМ (Hollywood Orchestration): Струнные + Медные духовые. Очень мощная, эпическая и плотная связка.")

    # Layering 3: Classic Complement
    if "Acoustic Grand Piano" in names and "Cello" in names:
        print("  🌟 ПРО-ПРИЕМ (Classic Duo): Пианино + Виолончель. Пианино дает атаку (атакующий транзиент), а виолончель — теплое тело ноты. Идеальное слияние.")

    print("\n  Используемые инструменты:")
    for p in instruments_used:
        print(f"  - {p['name']} [Частоты: {p['band']} | Тип: {p['type']}]")


def trace_midi_file(filepath):
    print(f"\n{'='*70}")
    print(f"Трейсинг файла: {filepath.name}")
    print(f"{'='*70}")
    
    try:
        mid = mido.MidiFile(filepath)
    except Exception as e:
        print(f"Ошибка чтения: {e}")
        return

    used_programs = set()
    track_info = []

    for i, track in enumerate(mid.tracks):
        prog = None
        notes = 0
        for msg in track:
            if msg.type == 'program_change':
                prog = msg.program
            elif msg.type == 'note_on' and msg.velocity > 0:
                notes += 1
        
        if prog is not None and notes > 0:
            used_programs.add(prog)
            name = GM_PROFILES.get(prog, {}).get("name", f"Unknown({prog})")
            track_info.append(f"Трек {i}: {name} ({notes} нот)")

    print("Структура треков:")
    for info in track_info:
        print(f"  {info}")

    instruments_used = [GM_PROFILES[p] for p in used_programs if p in GM_PROFILES]
    
    if instruments_used:
        analyze_orchestration(instruments_used)
    else:
        print("  Инструменты из GM-профиля не найдены.")


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "output/album_tin_soldier"
    path = Path(target_dir)
    
    if not path.exists():
        print(f"Директория {path} не найдена.")
        sys.exit(1)

    midi_files = sorted(list(path.glob("*.mid")))
    if not midi_files:
        print(f"В директории {path} нет MIDI-файлов.")
        sys.exit(0)

    for midi_file in midi_files:
        trace_midi_file(midi_file)
