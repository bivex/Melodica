# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
timbre_demonstrator.py — Интерактивный демонстратор тембральных MIDI CC изменений.

Этот скрипт наглядно показывает, как именно движок Melodica управляет тембром звука 
во времени (динамический морфинг, дыхание CC11, задержка вибрато CC1, яркость фильтра CC74) 
на примере красивой прогрессии C - Em - F - G.

В процессе выполнения скрипт строит ASCII-графики изменения тембра прямо в консоли!
"""

import math
from pathlib import Path

from melodica import types
from melodica.midi import export_multitrack_midi

# Тональность До-мажор (C Major)
KEY = types.Scale(root=0, mode=types.Mode.MAJOR)
OUT = Path("output/demo_timbre")
OUT.mkdir(parents=True, exist_ok=True)

def generate_expression_curves(notes: list[types.NoteInfo], total_beats: float) -> list[tuple[float, int, int]]:
    """
    Генерирует кривые автоматизации для демонстрации:
    - CC 11 (Expression): Дыхание (синусоидальные волны громкости внутри длинных нот)
    - CC 1  (Modulation): Запоздалое вибрато (плавное нарастание вибрато после начала ноты)
    - CC 74 (Brightness): Яркость фильтра (зависит от высоты тона ноты - чем выше нота, тем ярче срез)
    """
    cc_events = []
    
    # Шаг сканирования времени: каждые 0.1 доли (для высокой плавности тембральных переходов)
    step = 0.1
    t = 0.0
    
    while t < total_beats:
        # 1. Ищем, какая нота сейчас звучит
        current_note = None
        for n in notes:
            if n.start <= t <= (n.start + n.duration):
                current_note = n
                break
        
        if current_note is not None:
            # Позиция времени внутри звучащей ноты (от 0.0 до 1.0)
            note_progress = (t - current_note.start) / current_note.duration
            
            # --- АВТОМАТИЗАЦИЯ CC 11 (Дыхание / Выразительность) ---
            # Форма волны: плавное нарастание до максимума в середине ноты и спад в конце (колоколообразная синусоида)
            cc11_val = int(60 + 55 * math.sin(note_progress * math.pi))
            cc_events.append((t, 11, cc11_val))
            
            # --- АВТОМАТИЗАЦИЯ CC 1 (Модуляция / Запоздалое вибрато) ---
            # Первые 30% ноты скрипач/флейтист держит ровный тон (вибрато = 0).
            # Затем вибрато плавно разрастается до максимального значения
            if note_progress < 0.3:
                cc1_val = 0
            else:
                vibrato_progress = (note_progress - 0.3) / 0.7
                # Плавное сглаживание нарастания
                cc1_val = int(90 * (vibrato_progress ** 2))
            cc_events.append((t, 1, cc1_val))
            
            # --- АВТОМАТИЗАЦИЯ CC 74 (Яркость фильтра Cutoff) ---
            # Яркость зависит от Pitch ноты (чем выше берем ноту, тем сильнее раскрывается фильтр высоких частот)
            # Базовое значение 64 (нейтраль). Нота C5 (pitch=72) дает нейтраль, ноты выше раскрывают фильтр
            pitch_offset = current_note.pitch - 60
            cc74_val = int(64 + pitch_offset * 2.5 + 15 * math.sin(note_progress * math.pi))
            cc74_val = max(30, min(120, cc74_val))
            cc_events.append((t, 74, cc74_val))
            
        t += step
        
    return cc_events

def draw_ascii_graph(notes: list[types.NoteInfo], cc_events: list[tuple[float, int, int]], total_beats: float):
    """Строит красивый текстовый ASCII-график тембрального движения в консоли."""
    print("\n" + "=" * 80)
    print("   ВИЗУАЛИЗАЦИЯ ТЕМБРАЛЬНОГО МОРФИНГА ВО ВРЕМЕНИ (ASCII GRAPH)")
    print("=" * 80)
    print(" Легенда: \n"
          "   * CC 11 (Expression) - общая громкость и плотность дыхания [████░░░░]\n"
          "   * CC 1  (Vibrato)    - глубина вибрации струны/воздуха [~~~~~~~~]\n"
          "   * CC 74 (Brightness) - открытие яркости фильтра среза (High-Cut)\n")
    
    # Сгруппируем события по времени с точностью до 0.5 доли (учитывая погрешности float)
    time_steps = []
    for e in cc_events:
        t_val = round(e[0], 1)
        if abs(t_val * 2 - round(t_val * 2)) < 0.01:
            time_steps.append(t_val)
    time_steps = sorted(list(set(time_steps)))
    
    for t_step in time_steps:
        # Ищем значения CC на этом шаге времени
        c11 = 64
        c1 = 0
        c74 = 64
        for time, cc_num, val in cc_events:
            if abs(time - t_step) < 0.05:
                if cc_num == 11:
                    c11 = val
                elif cc_num == 1:
                    c1 = val
                elif cc_num == 74:
                    c74 = val
                    
        # Ищем текущую играющую ноту и ее название
        note_name = "---"
        for n in notes:
            if n.start <= t_step < (n.start + n.duration):
                # Простейший конвертер pitch -> нота
                names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "Bb", "B"]
                octave = (n.pitch // 12) - 1
                note_name = f"{names[n.pitch % 12]}{octave}"
                break
                
        # Строим графические полосы
        bar_c11_len = int((c11 / 120.0) * 15)
        bar_c11 = "█" * bar_c11_len + "░" * (15 - bar_c11_len)
        
        bar_c1_len = int((c1 / 90.0) * 12)
        bar_c1 = "~" * bar_c1_len + " " * (12 - bar_c1_len)
        
        # Вывод строки
        print(f"Beat {t_step:04.1f} | Нота: {note_name:<4} | "
              f"CC11 (Дыхание): [{bar_c11}] {c11:<3} | "
              f"CC1 (Вибрато): [{bar_c1}] {c1:<2} | "
              f"CC74 (Яркость): {c74:<3}")
    print("=" * 80 + "\n")

def run_demonstration():
    # 1. Задаем длинные, выразительные ноты соло-партии (флейта/скрипка)
    # Мелодия плавно идет по ступеням До-мажора поверх аккордов C - Em - F - G
    melody = [
        types.NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80),   # C4 (До) поверх аккорда C
        types.NoteInfo(pitch=64, start=4.0, duration=4.0, velocity=85),   # E4 (Ми) поверх аккорда Em
        types.NoteInfo(pitch=69, start=8.0, duration=4.0, velocity=90),   # A4 (Ля) поверх аккорда F (красивая надстройка)
        types.NoteInfo(pitch=67, start=12.0, duration=4.0, velocity=85),  # G4 (Соль) поверх аккорда G (разрешение)
    ]
    
    total_beats = 16.0
    
    # 2. Генерируем плавные кривые автоматизации CC
    cc_events = generate_expression_curves(melody, total_beats)
    
    # 3. Визуализируем тембральный танец в консоли!
    draw_ascii_graph(melody, cc_events, total_beats)
    
    # 4. Экспортируем в MIDI файл
    tracks = {"lead": melody}
    instruments = {"lead": 73}  # Flute
    
    # Структурируем словарь CC событий для экспортера
    # Наш экспортёр ждет формат { "TrackName": [(beat, cc_num, cc_val), ...] }
    cc_dict = {"lead": cc_events}
    
    midi_path = OUT / "timbre_modulation_demo.mid"
    export_multitrack_midi(tracks, str(midi_path), bpm=100.0, key=KEY,
                           instruments=instruments, cc_events=cc_dict)
    
    print("🚀 MIDI файл с точными кривыми тембрального морфинга успешно сгенерирован!")
    print(f"   Файл для прослушивания: {midi_path.resolve()}\n")
    print("💡 ОБРАТИТЕ ВНИМАНИЕ НА ГРАФИК:")
    print("   1. В начале каждой ноты (note_progress = 0%) вибрато (CC1) всегда равно 0 (звучит чистый тон).")
    print("   2. Ближе к середине ноты (50%) дыхание (CC11) раздувается до максимума (звук становится плотным и громким).")
    print("   3. Начиная с 30% ноты плавно нарастает вибрато (CC1), заставляя звук расцветать и петь.")
    print("   4. Яркость фильтра (CC74) раскрывается сильнее на высоких нотах (A4 на 8-й доле имеет самый яркий срез).")
    print("=" * 80)

if __name__ == "__main__":
    run_demonstration()
