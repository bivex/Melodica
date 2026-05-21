# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
demo_catchy_melody.py — Демонстрация генератора цепляющей мелодии (MelodyGenerator).

Стиль: Catchy Pop-Epic Progression (Am - F - C - G)
Инструменты: Lead Synth (80), Warm Pad (89), Vibraphone Arp (11), Finger Bass (33).
Параметры мелодии: Contour="arch", Motif Probability=0.7, Harmony Probability=0.8, Drama="epic".
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

# A Minor (root=9, mode=NATURAL_MINOR)
KEY = types.Scale(root=9, mode=types.Mode.NATURAL_MINOR)

# Глобальный seed для стабильной, но красивой генерации
random.seed(42)

OUT = Path("output/demo_catchy")
OUT.mkdir(parents=True, exist_ok=True)

def _master(raw: dict, bpm: float, lufs: float = -16.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "lead": 0.85,
        "pad": 0.45,
        "arp": 0.60,
        "bass": 0.65,
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict, lufs: float = -16.0):
    final_notes, cc_events = _master(tracks, bpm, lufs=lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

def generate_demo():
    print("=" * 60)
    print("   ГЕНЕРАЦИЯ ДЕМО: CATCHY POP-EPIC MELODY")
    print("=" * 60)
    
    bpm = 100.0
    dur = 64.0  # 16 тактов в размере 4/4 (всего 64 доли)
    
    # 1. Построение эмоциональной аккордовой прогрессии: Am - F - C - G
    chords = []
    progression = [
        (9, types.Quality.MINOR),  # Am
        (5, types.Quality.MAJOR),  # F
        (0, types.Quality.MAJOR),  # C
        (7, types.Quality.MAJOR),  # G
    ]
    for i in range(16):  # 16 тактов
        root, quality = progression[i % 4]
        chords.append(types.ChordLabel(
            root=root,
            quality=quality,
            start=float(i * 4.0),
            duration=4.0
        ))

    # 2. Основная мелодия: MelodyGenerator с «catchy»-настройками
    print("-> Генерация цепляющей лид-мелодии (MelodyGenerator)...")
    lead_gen = MelodyGenerator(
        params=GeneratorParams(
            density=0.55, 
            complexity=0.7, 
            velocity_range=(85, 115),
            key_range_low=60,
            key_range_high=84
        ),
        phrase_length=8.0,              # Фразы по 8 долей
        phrase_contour="arch",          # Форма дуги (нарастание и спад)
        motif_probability=0.7,          # Высокий шанс мотивного развития (хук!)
        harmony_note_probability=0.8,   # Мелодия тяготеет к устойчивым ступеням аккордов
        drama_shape="epic",             # Кульминация энергии (поздний пик на ~80% длины)
        ornament_probability=0.2        # Тонкие украшения (мелизмы/форшлаги)
    )
    lead_notes = lead_gen.render(chords, KEY, dur)

    # 3. Аккомпанирующий теплый пэд для гармонии
    print("-> Генерация подклада (AmbientPadGenerator)...")
    pad_gen = AmbientPadGenerator(
        params=GeneratorParams(
            density=0.03, 
            key_range_low=48, 
            key_range_high=72, 
            velocity_range=(45, 65)
        ),
        voicing="open"
    )
    pad_notes = pad_gen.render(chords, KEY, dur)

    # 4. Чистые и звонкие арпеджио вибрафона на заднем плане
    print("-> Генерация фонового арпеджио (ArpeggiatorGenerator)...")
    arp_gen = ArpeggiatorGenerator(
        params=GeneratorParams(
            density=0.35, 
            key_range_low=57, 
            key_range_high=76, 
            velocity_range=(50, 70)
        ),
        pattern="up_down",
        note_duration=0.25
    )
    arp_notes = arp_gen.render(chords, KEY, dur)

    # 5. Движущийся пальцевый бас
    print("-> Генерация басовой линии (BassGenerator)...")
    bass_gen = BassGenerator(
        params=GeneratorParams(
            density=0.5, 
            key_range_low=33, 
            key_range_high=52, 
            velocity_range=(75, 95)
        ),
        style="walking"
    )
    bass_notes = bass_gen.render(chords, KEY, dur)

    # Собираем треки
    tracks = {
        "lead": lead_notes,
        "pad": pad_notes,
        "arp": arp_notes,
        "bass": bass_notes
    }
    
    # Присваиваем номера General MIDI
    inst = {
        "lead": 80,   # Lead 1 (square) — синтезаторное соло
        "pad": 89,    # Pad 2 (warm) — мягкий подклад
        "arp": 11,    # Vibraphone — вибрафон (чистый и колокольный)
        "bass": 33,   # Electric Bass (finger) — плотный бас
    }

    midi_path = OUT / "demo_catchy_melody.mid"
    print(f"-> Сведение, мастеринг и экспорт в MIDI с экспрессивной автоматизацией...")
    _export(tracks, midi_path, bpm, inst, lufs=-16.0)

    print("\n" + "=" * 60)
    print("   ГЕНЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"   Файл сохранен: {midi_path.resolve()}")
    print("   Параметры экспрессии в MIDI применены автоматически:")
    print("     - CC 64 (sustain педаль) для арпеджио")
    print("     - CC 11 (выразительное дыхание) для длинных нот мелодии")
    print("     - CC 1  (вибрато / модуляция) с задержкой для струнных/лида")
    print("     - CC 7  (балансировка громкости каналов микса)")
    print("=" * 60)

if __name__ == "__main__":
    generate_demo()
