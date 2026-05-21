# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
roblox_modern_acoustic.py — Современный акустический/оркестровый трек для детей.

Вайб: Animal Crossing, Pixar, современные казуальные игры Nintendo.
Никакого агрессивного 8-битного чиптьюна (not chiptune/8-bit), только благородный,
теплый, «дорогой» и чистый акустический звук без драмы.

Тональность: До-мажор (C Major) — светлая и солнечная.
Темп: 108 BPM — умеренный, прыгучий, очень уютный и певучий.
Гармония: Ультра-светлая и мягкая прогрессия (C - Em - F - G).
Инструменты:
  - Lead: Flute (73) — нежная поперечная флейта.
  - Pluck: Pizzicato Strings (45) — игривые щипковые струнные (фирменный вайб Pixar).
  - Harmony: Orchestral Harp (46) — благородная арфа.
  - Pad: String Ensemble 1 (48) — мягкий фоновый струнный оркестр.
  - Bass: Acoustic Bass (32) — теплый акустический контрабас.
  - Percussion: Soft Toy Percussion (Channel 10) — треугольники, шейкеры, колокольчики.
"""

import random
from pathlib import Path

from melodica import types
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.bass import BassGenerator
from melodica.midi import export_multitrack_midi
from melodica.shorts_mixing import MixingDesk
from melodica.shorts_mastering import MasteringDesk

# C Major (root=0, mode=MAJOR)
KEY = types.Scale(root=0, mode=types.Mode.MAJOR)

random.seed(999)  # Уютный seed для красивой мелодии
OUT = Path("output/roblox_bounce")
OUT.mkdir(parents=True, exist_ok=True)

def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "lead": 0.82,     # Нежная флейта
        "pizz": 0.75,     # Игривые пиццикато
        "harp": 0.68,     # Искрящаяся арфа
        "strings": 0.50,  # Очень тихий струнный подклад
        "bass": 0.65,     # Теплый контрабас
        "perc": 0.55,     # Деликатная перкуссия
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict, lufs: float = -16.0):
    final_notes, cc_events = _master(tracks, bpm, lufs=lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

def generate_roblox_modern():
    print("=" * 60)
    print("   ГЕНЕРАЦИЯ: MODERN ACOUSTIC CASUAL (ROBLOX / NINTENDO STYLE)")
    print("=" * 60)
    
    bpm = 108.0
    dur = 64.0  # 16 тактов (64 доли)
    
    # 1. Супер-светлая, нежная прогрессия аккордов: C - Em - F - G (I - iii - IV - V)
    # Звучит невероятно тепло, по-доброму и полностью лишено драматизма
    chords = []
    progression = [
        (0, types.Quality.MAJOR),  # C (До-мажор) — радость, дом
        (4, types.Quality.MINOR),  # Em (Ми-минор) — мягкость, мечтательность
        (5, types.Quality.MAJOR),  # F (Фа-мажор) — открытость, полет
        (7, types.Quality.MAJOR),  # G (Соль-мажор) — теплое ожидание
    ]
    for i in range(16):
        root, quality = progression[i % 4]
        chords.append(types.ChordLabel(
            root=root,
            quality=quality,
            start=float(i * 4.0),
            duration=4.0
        ))

    # 2. Нежная лид-мелодия (Акустическая Флейта)
    print("-> Генерация нежной певучей мелодии (Flute)...")
    lead_gen = MelodyGenerator(
        params=GeneratorParams(
            density=0.48, 
            complexity=0.55, 
            velocity_range=(75, 100),
            key_range_low=64,
            key_range_high=86
        ),
        phrase_length=8.0,              # Длинные, дышащие фразы
        phrase_contour="wave",          # Мягкое волнообразное покачивание
        motif_probability=0.75,         # Отличная запоминаемость темы
        harmony_note_probability=0.85,  # Хорошая опора на аккорды
        drama_shape="crescendo",        # Плавное крещендо без резких провалов и напряжения
        ornament_probability=0.25       # Легкие, аккуратные трели и форшлаги
    )
    lead_notes = lead_gen.render(chords, KEY, dur)

    # 3. Игривые пиццикато струнные (Pizzicato) — задают весь прыгучий казуальный ритм
    print("-> Генерация прыгучего пиццикато фона (Pizzicato Strings)...")
    pizz_gen = MelodyGenerator(
        params=GeneratorParams(
            density=0.55, 
            complexity=0.6, 
            velocity_range=(70, 95),
            key_range_low=52,
            key_range_high=72
        ),
        phrase_length=4.0,
        phrase_contour="flat",          # Ритмически стабильный рисунок
        harmony_note_probability=0.90,  # Строго по аккордам
        syncopation=0.25                # Небольшая веселая синкопа
    )
    pizz_notes = pizz_gen.render(chords, KEY, dur)

    # 4. Волшебные переливы арфы (Orchestral Harp)
    print("-> Генерация пассажей арфы (Orchestral Harp)...")
    harp_gen = ArpeggiatorGenerator(
        params=GeneratorParams(
            density=0.25, 
            key_range_low=60, 
            key_range_high=84, 
            velocity_range=(50, 70)
        ),
        pattern="converge",             # Пассажи сходятся к центру, создавая сказочный эффект
        note_duration=0.5
    )
    harp_notes = harp_gen.render(chords, KEY, dur)

    # 5. Теплый фоновый оркестровый ковер
    print("-> Генерация мягкого подклада (String Ensemble)...")
    pad_gen = AmbientPadGenerator(
        params=GeneratorParams(
            density=0.03, 
            key_range_low=48, 
            key_range_high=64, 
            velocity_range=(35, 50)
        ),
        voicing="open"
    )
    pad_notes = pad_gen.render(chords, KEY, dur)

    # 6. Глубокий акустический контрабас
    print("-> Генерация теплого акустического баса (Acoustic Bass)...")
    bass_gen = BassGenerator(
        params=GeneratorParams(
            density=0.45, 
            key_range_low=28, 
            key_range_high=48, 
            velocity_range=(70, 85)
        ),
        style="walking"
    )
    bass_notes = bass_gen.render(chords, KEY, dur)

    # 7. Деликатная акустическая перкуссия (без грубой электронной бочки и снейров)
    # Только мягкие шейкеры, колокольчики и треугольники
    print("-> Создание мягкой акустической перкуссии (Percussion)...")
    perc_notes = []
    for beat in range(int(dur)):
        # Мягкий Cabasa / Shaker (MIDI 69) на каждую четверть
        perc_notes.append(types.NoteInfo(pitch=69, start=float(beat), duration=0.08, velocity=60))
        
        # Легкий треугольник (MIDI 81) или Tinkle Bell (MIDI 112 в GM, на 10 канале это Tambourine MIDI 54)
        # Tambourine (MIDI 54) на слабых долях (and)
        perc_notes.append(types.NoteInfo(pitch=54, start=beat + 0.5, duration=0.05, velocity=50))
        
        # Редкий красивый звон треугольника Triangle (MIDI 80/81) каждые 4 доли
        if beat % 4 == 0:
            perc_notes.append(types.NoteInfo(pitch=80, start=float(beat), duration=0.20, velocity=70))

    # Сводим все дорожки
    tracks = {
        "lead": lead_notes,
        "pizz": pizz_notes,
        "harp": harp_notes,
        "strings": pad_notes,
        "bass": bass_notes,
        "perc": perc_notes
    }
    
    # Номера инструментов General MIDI (100% акустика)
    inst = {
        "lead": 73,    # Flute — нежная флейта
        "pizz": 45,    # Pizzicato Strings — щипковые струнные
        "harp": 46,    # Orchestral Harp — акустическая арфа
        "strings": 48, # String Ensemble 1 — мягкие скрипки/виолончели
        "bass": 32,    # Acoustic Bass — акустический контрабас
        "perc": 0,     # Мягкая перкуссия (канал 10)
    }

    midi_path = OUT / "roblox_uplift.mid"
    print(f"-> Сведение, мастеринг и экспорт акустического трека в MIDI...")
    _export(tracks, midi_path, bpm, inst, lufs=-16.0)

    print("\n" + "=" * 60)
    print("   ГЕНЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"   Файл сохранен: {midi_path.resolve()}")
    print("   Параметры аранжировки:")
    print("     - Темп: 108 BPM (Уютный, спокойный, казуальный)")
    print("     - Тональность: C Major (Чистый мажор)")
    print("     - Гармония: C - Em - F - G (Нежная, без грамма драмы)")
    print("     - Инструменты: 100% акустические (Flute, Pizzicato, Harp, Contrabass)")
    print("     - Перкуссия: деликатные треугольники, шейкеры и тамбурин")
    print("=" * 60)

if __name__ == "__main__":
    generate_roblox_modern()
