# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
hungarian_scratch.py — Интерактивный генератор и визуализатор цепляющей венгерской мелодии.

Стиль: Трагический и выразительный Венгерский Цыганский Романс (Hungarian Minor).
Инструменты: 
  - Lead Violin (40) — плачущая, певучая скрипка со сложным фразированием и орнаментами.
  - Cimbalom/Dulcimer (15) — традиционный цимбалы, рассыпающие быстрые этнические арпеджио.
  - Nylon Guitar (24) — акустическая гитара, создающая мягкую ритмическую гармонию.
  - Acoustic Bass (32) — глубокий акустический контрабас, ведущий линию.

Тональность: Соль венгерский минор (G Hungarian Minor: G, A, Bb, C#, D, Eb, F#).
Особый акцент сделан на характерные интервалы: увеличенную секунду (Bb - C# и Eb - F#),
которые придают восточно-европейский колорит, а также на выразительное фразирование.
"""

import random
import math
from pathlib import Path

from melodica import types
from melodica.theory import Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.bass import BassGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
# Импортируем MasteringDesk для единого безопасного сведения без клиппинга
from melodica.shorts_mastering import MasteringDesk

# G Hungarian Minor (root=7, mode=HUNGARIAN_MINOR)
KEY = types.Scale(root=7, mode=types.Mode.HUNGARIAN_MINOR)

# Демонически-цыганский сид для идеального художественного баланса
random.seed(777)

OUT = Path("output/hungarian_minor")
OUT.mkdir(parents=True, exist_ok=True)

def build_chord_progression(dur: float) -> list[types.ChordLabel]:
    """
    Строит классическую цыганскую романсовую структуру:
    Раздел A (Тема): Gm - Eb - D - Gm (с глубоким драматическим развитием)
    Раздел B (Кульминация): Eb - D - Eb - D -> Cm - D - Gm
    """
    chords = []
    
    # 32 такта по 4 доли = 128 долей (около 1 минуты 10 секунд при 110 BPM)
    # 1 такт = 4.0 доли
    
    # --- РАЗДЕЛ А (0.0 - 64.0 доли) ---
    # Повторяющийся лирический мотив
    prog_a = [
        (7, Quality.MINOR),      # Gm
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        (7, Quality.MINOR),      # Gm
        
        (7, Quality.MINOR),      # Gm
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        (2, Quality.MAJOR),      # D (зависание перед переходом)
        
        (7, Quality.MINOR),      # Gm
        (0, Quality.MINOR),      # Cm (субдоминанта)
        (3, Quality.MAJOR),      # Eb (яркий свет)
        (2, Quality.MAJOR),      # D (напряжение)
        
        (7, Quality.MINOR),      # Gm
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        (7, Quality.MINOR),      # Gm
    ]
    
    # --- РАЗДЕЛ B (64.0 - 128.0 доли) ---
    # Трагический подъем и кульминация
    prog_b = [
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        (7, Quality.MINOR),      # Gm
        (7, Quality.MINOR),      # Gm
        
        (0, Quality.MINOR),      # Cm
        (2, Quality.MAJOR),      # D
        (7, Quality.MINOR),      # Gm
        (7, Quality.MINOR),      # Gm
        
        (3, Quality.MAJOR),      # Eb
        (2, Quality.MAJOR),      # D
        (7, Quality.MINOR),      # Gm
        (7, Quality.MINOR),      # Gm (финал)
    ]
    
    full_prog = prog_a + prog_b
    
    for i, (root, quality) in enumerate(full_prog):
        chords.append(types.ChordLabel(
            root=root,
            quality=quality,
            start=float(i * 4.0),
            duration=4.0
        ))
        
    return chords

def visualize_melody_phrases(melody_notes: list[types.NoteInfo], total_beats: float):
    """
    Строит наглядный ASCII-график движения скрипичной мелодии,
    подсвечивая характерные интервалы венгерского минора (увеличенная секунда).
    """
    print("\n" + "=" * 90)
    print("   ВИЗУАЛИЗАЦИЯ СКРИПИЧНОЙ МЕЛОДИИ И СТРУКТУРЫ ФРАЗ (G HUNGARIAN MINOR)")
    print("=" * 90)
    print(" Легенда:")
    print("   * Каждая строка отображает шаг в 2.0 доли.")
    print("   * Буквами указаны играющие ноты (в Соль венгерском миноре: G, A, Bb, C#, D, Eb, F#).")
    print("   * Символы [!] обозначают характерные пряные интервалы (увеличенные секунды Bb-C# или Eb-F#)!")
    print("=" * 90)
    
    # Шаг в 2.0 доли для хорошего масштаба
    step = 2.0
    t = 0.0
    
    # Тональность G Hungarian Minor:
    # 7=G, 9=A, 10=Bb, 1=C#, 2=D, 3=Eb, 6=F#
    note_names = {
        0: "C", 1: "C#", 2: "D", 3: "Eb", 4: "E", 5: "F", 
        6: "F#", 7: "G", 8: "Ab", 9: "A", 10: "Bb", 11: "B"
    }
    
    # Особые "венгерские" интервальные переходы
    spicy_notes = {1, 3, 6, 10} # C#, Eb, F#, Bb
    
    while t < total_beats:
        # Находим ноты, звучащие в этот интервал времени
        current_notes = []
        for n in melody_notes:
            if n.start <= t < (n.start + n.duration):
                current_notes.append(n)
                
        # Если ноты есть, берем самую высокую (лид-линия)
        if current_notes:
            lead = max(current_notes, key=lambda x: x.pitch)
            pitch_val = lead.pitch
            pc = pitch_val % 12
            octave = (pitch_val // 12) - 1
            name = f"{note_names[pc]}{octave}"
            
            # Строим графическую шкалу высоты (pitch от 60 до 84)
            norm_pitch = max(0, min(24, pitch_val - 60))
            bar = " " * norm_pitch + "●" + " " * (24 - norm_pitch)
            
            # Подсвечиваем пряные интервалы
            is_spicy = pc in spicy_notes
            spicy_tag = "[!] SPICY!" if is_spicy else "         "
            
            # Группируем по тактам
            bar_num = int(t // 4.0) + 1
            beat_in_bar = t % 4.0 + 1
            
            print(f"Такт {bar_num:02d}.{int(beat_in_bar)} | Нота: {name:<5} |{bar}| {spicy_tag} (Vel: {lead.velocity})")
        else:
            bar_num = int(t // 4.0) + 1
            beat_in_bar = t % 4.0 + 1
            print(f"Такт {bar_num:02d}.{int(beat_in_bar)} | Нота: ---   |{" " * 12 + "·" + " " * 12}|           (Пауза)")
            
        t += step
        # Выведем разделитель между Разделами A и B
        if t == 64.0:
            print("-" * 90)
            print(" >>> ПЕРЕХОД К РАЗДЕЛУ B (КУЛЬМИНАЦИЯ, БОЛЕЕ ВЫСОКИЙ РЕГИСТР, ДРАМАТИЧЕСКИЙ НАДРЫВ) <<<")
            print("-" * 90)
            
    print("=" * 90 + "\n")

def run_generation():
    print("🚀 НАЧАЛО ГЕНЕРАЦИИ: HUNGARIAN ROMANCE IN G MINOR")
    print("   Масштаб: 32 такта, темп 110 BPM, глубокое фразирование скрипки.")
    
    bpm = 110.0
    dur = 128.0  # 32 такта
    
    # 1. Генерируем гармоническую сетку аккордов
    chords = build_chord_progression(dur)
    
    # 2. Выразительная скрипка (Lead Violin - Program 40)
    # Мелодия должна фразами цеплять! 
    # phrase_length=8.0 (длинные связные фразы на 2 такта),
    # motif_probability=0.85 (высокий уровень мотивных повторений — основа хуковости и узнаваемости),
    # ornament_probability=0.35 (красивые украшения/форшлаги в венгерском стиле),
    # drama_shape="epic" (нарастание напряжения к финалу).
    print("-> Создание плачущей лид-скрипки (MelodyGenerator)...")
    violin_gen = MelodyGenerator(
        params=GeneratorParams(
            density=0.60,
            complexity=0.75,
            velocity_range=(75, 115),
            key_range_low=62, # D4
            key_range_high=86 # D6
        ),
        phrase_length=8.0,
        phrase_contour="arch",
        motif_probability=0.85,
        harmony_note_probability=0.70,
        drama_shape="epic",
        ornament_probability=0.35,
        register_smoothness=0.65
    )
    violin_notes = violin_gen.render(chords, KEY, dur)
    
    # 3. Цимбалы (Cimbalom/Dulcimer - Program 15)
    # Этнические переливы и арпеджио на заднем плане
    print("-> Создание рассыпчатых цимбал (ArpeggiatorGenerator)...")
    cimbalom_gen = ArpeggiatorGenerator(
        params=GeneratorParams(
            density=0.70,
            key_range_low=55, # G3
            key_range_high=79, # G5
            velocity_range=(50, 75)
        ),
        pattern="up_down_full",
        note_duration=0.25 # 16-е длительности (быстрая россыпь)
    )
    cimbalom_notes = cimbalom_gen.render(chords, KEY, dur)
    
    # 4. Акустическая гитара (Nylon Guitar - Program 24)
    # Мягкая гармоническая подложка
    print("-> Создание теплой акустической гитары (AmbientPadGenerator)...")
    guitar_gen = AmbientPadGenerator(
        params=GeneratorParams(
            density=0.04, # Длинные, плавно перетекающие аккорды
            key_range_low=43, # G2
            key_range_high=67, # G4
            velocity_range=(45, 60)
        ),
        voicing="spread",
        overlap=0.15
    )
    guitar_notes = guitar_gen.render(chords, KEY, dur)
    
    # 5. Акустический глубокий контрабас (Acoustic Bass - Program 32)
    # Медленный и уверенный walking-бас, очерчивающий корни аккордов
    print("-> Создание глубокого контрабаса (BassGenerator)...")
    bass_gen = BassGenerator(
        params=GeneratorParams(
            density=0.45,
            key_range_low=29, # F1
            key_range_high=50, # D3
            velocity_range=(65, 85)
        ),
        style="walking"
    )
    bass_notes = bass_gen.render(chords, KEY, dur)
    
    # Собираем все дорожки в сырой микс
    raw_tracks = {
        "violin": violin_notes,
        "cimbalom": cimbalom_notes,
        "guitar": guitar_notes,
        "bass": bass_notes
    }
    
    # General MIDI настройки
    instruments = {
        "violin": 40,    # Violin
        "cimbalom": 15,  # Dulcimer / Cimbalom
        "guitar": 24,    # Acoustic Guitar (nylon)
        "bass": 32       # Acoustic Bass
    }
    
    # Настройка баланса громкости на микшерном пульте (MixingDesk)
    print("-> Сведение и балансировка громкости...")
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "violin": 0.90,    # Лид должен парить сверху
        "cimbalom": 0.58,  # Цимбалы рассыпаются фоном
        "guitar": 0.65,    # Мягкий гармонический фундамент
        "bass": 0.72       # Уверенная басовая опора
    })
    mixed_tracks = desk.apply_mixing(raw_tracks, [], int(bpm))
    
    # Применение единого Global Mastering Desk для теплого аналогового сжатия и защиты от клиппинга
    print("-> Мастеринг трека с защитой от щелчков и перегруза (MasteringDesk)...")
    master = MasteringDesk(target_lufs=-14.0)
    mastered_notes, cc_events = master.apply_mastering(mixed_tracks)
    
    # Экспортируем в MIDI файл с автоматическим добавлением экспрессии
    midi_path = OUT / "hungarian_romance.mid"
    print(f"-> Экспорт в MIDI файл...")
    export_multitrack_midi(
        mastered_notes, 
        str(midi_path), 
        bpm=bpm, 
        key=KEY,
        instruments=instruments, 
        cc_events=cc_events
    )
    
    # Визуализируем мелодическое движение скрипки в консоли
    visualize_melody_phrases(violin_notes, dur)
    
    print("🎉 ГЕНЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"   Файл сохранен: {midi_path.resolve()}")
    print("   Примененные технологии выразительности:")
    print("     - Полноценная защита от перекрытий нот одной высоты (без кликов)")
    print("     - Синусоидальное 'дыхание' скрипки (CC11) для живого ведения смычка")
    print("     - Запоздалое вибрато скрипки (CC1) для раскрытия длинных нот")
    print("     - Прореженная плотность CC (0.25 beat) для стабильности DAW")
    print("=" * 90)

if __name__ == "__main__":
    run_generation()
