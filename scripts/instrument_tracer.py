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
    8: {"name": "Celesta", "band": "High", "type": "Transient"},
    9: {"name": "Glockenspiel", "band": "High", "type": "Transient"},
    10: {"name": "Music Box", "band": "High", "type": "Transient"},
    12: {"name": "Marimba", "band": "Mid", "type": "Percussive"},
    13: {"name": "Xylophone", "band": "High", "type": "Percussive"},
    19: {"name": "Church Organ", "band": "Full", "type": "Sustained"},
    21: {"name": "Accordion", "band": "Mid", "type": "Sustained"},
    24: {"name": "Acoustic Guitar (nylon)", "band": "Mid", "type": "Plucked"},
    25: {"name": "Acoustic Guitar (steel)", "band": "Mid", "type": "Plucked"},
    32: {"name": "Acoustic Bass", "band": "Low", "type": "Plucked"},
    35: {"name": "Fretless Bass", "band": "Low", "type": "Sustained"},
    38: {"name": "Synth Bass 1", "band": "Low", "type": "Sustained"},
    40: {"name": "Violin", "band": "Mid_High", "type": "Sustained"},
    42: {"name": "Cello", "band": "Low_Mid", "type": "Sustained"},
    43: {"name": "Contrabass", "band": "Low", "type": "Sustained"},
    44: {"name": "Tremolo Strings", "band": "Mid_High", "type": "Sustained"},
    45: {"name": "Pizzicato Strings", "band": "Mid", "type": "Plucked"},
    46: {"name": "Orchestral Harp", "band": "Full", "type": "Plucked"},
    47: {"name": "Timpani", "band": "Low", "type": "Percussive"},
    48: {"name": "String Ensemble 1", "band": "Full", "type": "Sustained"},
    52: {"name": "Choir Aahs", "band": "Mid_High", "type": "Sustained"},
    58: {"name": "Tuba", "band": "Low", "type": "Sustained"},
    60: {"name": "French Horn", "band": "Mid", "type": "Sustained"},
    61: {"name": "Brass Section", "band": "Mid", "type": "Sustained"},
    68: {"name": "Oboe", "band": "Mid", "type": "Sustained"},
    70: {"name": "Bassoon", "band": "Low_Mid", "type": "Sustained"},
    71: {"name": "Clarinet", "band": "Mid", "type": "Sustained"},
    73: {"name": "Flute", "band": "High", "type": "Sustained"},
    78: {"name": "Whistle", "band": "High", "type": "Sustained"},
    88: {"name": "Pad 1 (new age)", "band": "Full", "type": "Pad"},
    89: {"name": "Pad 2 (warm)", "band": "Mid", "type": "Pad"},
    91: {"name": "Pad 4 (choir)", "band": "Mid", "type": "Pad"},
    92: {"name": "Pad 5 (bowed)", "band": "Mid_High", "type": "Pad"},
    115: {"name": "Woodblock", "band": "High", "type": "Percussive"}
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
