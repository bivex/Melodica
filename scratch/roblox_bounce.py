# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
roblox_bounce.py — Детский весёлый трек в стиле Roblox / Chiptune / Casual Game.

Тональность: До-мажор (C Major) — максимально светлая и чистая.
Темп: 130 BPM — бодрый, прыгучий и энергичный.
Гармония: Золотая поп-прогрессия (C - G - Am - F).
Инструменты:
  - Lead: Glockenspiel (9) — детские колокольчики.
  - Arpeggio: Lead Square (80) — ретро-игровой чиптьюн звук.
  - Bass: Synth Bass 1 (38) — упругий игровой бас.
  - Pad: Warm Pad (89) — мягкий фоновый подклад.
  - Percussion: Bouncy Game Drums (Channel 10) — прыгучий игровой ритм.
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

random.seed(777)  # счастливый seed для детского трека
OUT = Path("output/roblox_bounce")
OUT.mkdir(parents=True, exist_ok=True)

def _master(raw: dict, bpm: float, lufs: float = -15.0):
    desk = MixingDesk(niche_cfg={})
    desk.track_gains.update({
        "lead": 0.90,  # Громкие колокольчики на переднем плане
        "arp": 0.70,   # Игривый чиптьюн
        "pad": 0.40,   # Мягкий фон
        "bass": 0.70,  # Упругий бас
        "perc": 0.75,  # Прыгучие барабаны
    })
    mixed = desk.apply_mixing(raw, [], int(bpm))
    master = MasteringDesk(target_lufs=lufs)
    return master.apply_mastering(mixed)

def _export(tracks: dict, path: Path, bpm: float, instruments: dict, lufs: float = -15.0):
    final_notes, cc_events = _master(tracks, bpm, lufs=lufs)
    export_multitrack_midi(final_notes, str(path), bpm=bpm, key=KEY,
                           instruments=instruments, cc_events=cc_events)

def generate_roblox():
    print("=" * 60)
    print("   ГЕНЕРАЦИЯ: ROBLOX / KIDS GAME BOUNCE")
    print("=" * 60)
    
    bpm = 130.0
    dur = 64.0  # 16 тактов (64 доли)
    
    # 1. Счастливая аккордовая прогрессия: C - G - Am - F (каждый аккорд по 4 доли)
    chords = []
    progression = [
        (0, types.Quality.MAJOR),  # C (Яркий мажор)
        (7, types.Quality.MAJOR),  # G (Мажор)
        (9, types.Quality.MINOR),  # Am (Мягкий минор)
        (5, types.Quality.MAJOR),  # F (Мажор)
    ]
    for i in range(16):
        root, quality = progression[i % 4]
        chords.append(types.ChordLabel(
            root=root,
            quality=quality,
            start=float(i * 4.0),
            duration=4.0
        ))

    # 2. Игрушечное соло (Glockenspiel)
    print("-> Создание прыгучей детской мелодии (Glockenspiel)...")
    lead_gen = MelodyGenerator(
        params=GeneratorParams(
            density=0.6, 
            complexity=0.6, 
            velocity_range=(90, 115),
            key_range_low=64,
            key_range_high=88
        ),
        phrase_length=4.0,              # Короткие фразы для детского восприятия
        phrase_contour="wave",          # Прыгучий волновой контур
        motif_probability=0.85,         # Высокая повторяемость (дети обожают запоминающиеся мотивы!)
        harmony_note_probability=0.90,  # Максимальная опора на аккордовые тона (чистое созвучие)
        drama_shape="crescendo",        # Плавное радостное крещендо
        ornament_probability=0.40       # Обилие игривых форшлагов (чирикающий/игрушечный эффект)
    )
    lead_notes = lead_gen.render(chords, KEY, dur)

    # 3. Чиптьюн-арпеджио (Lead Square 8-bit)
    print("-> Генерация пузырящегося 8-битного арпеджио (Chiptune Square)...")
    arp_gen = ArpeggiatorGenerator(
        params=GeneratorParams(
            density=0.4, 
            key_range_low=60, 
            key_range_high=79, 
            velocity_range=(55, 75)
        ),
        pattern="up",
        note_duration=0.125             # Быстрые 16-е ноты для геймерского вайба
    )
    arp_notes = arp_gen.render(chords, KEY, dur)

    # 4. Мягкий поддерживающий пэд
    print("-> Генерация подклада (AmbientPadGenerator)...")
    pad_gen = AmbientPadGenerator(
        params=GeneratorParams(
            density=0.03, 
            key_range_low=48, 
            key_range_high=64, 
            velocity_range=(45, 60)
        ),
        voicing="open"
    )
    pad_notes = pad_gen.render(chords, KEY, dur)

    # 5. Упругий синтезаторный бас
    print("-> Генерация прыгающего игрового баса (Synth Bass)...")
    bass_gen = BassGenerator(
        params=GeneratorParams(
            density=0.6, 
            key_range_low=36, 
            key_range_high=52, 
            velocity_range=(80, 100)
        ),
        style="walking"                 # Бас идет активными шагами
    )
    bass_notes = bass_gen.render(chords, KEY, dur)

    # 6. Прыгучие геймерские барабаны (Канал 10)
    # Нарисуем веселый 4-on-the-floor ритм с хлопками (clap/snare) на 2 и 4
    # И бегущими hi-hats на слабых долях
    print("-> Создание прыгучего игрового ритма (Percussion)...")
    perc_notes = []
    for beat in range(int(dur)):
        # Kick (MIDI 36) на каждую долю (четыре на пол)
        perc_notes.append(types.NoteInfo(pitch=36, start=float(beat), duration=0.15, velocity=105))
        
        # Snare/Clap (MIDI 38 или 39) на 2-ю и 4-ю долю каждого такта
        if beat % 4 in [1, 3]:
            perc_notes.append(types.NoteInfo(pitch=39, start=float(beat), duration=0.10, velocity=95))
            
        # Bouncy Closed Hi-Hat (MIDI 42) на слабых долях (and)
        perc_notes.append(types.NoteInfo(pitch=42, start=beat + 0.5, duration=0.08, velocity=80))

    # Сводим все дорожки вместе
    tracks = {
        "lead": lead_notes,
        "arp": arp_notes,
        "pad": pad_notes,
        "bass": bass_notes,
        "perc": perc_notes
    }
    
    # Номера инструментов General MIDI
    inst = {
        "lead": 9,     # Glockenspiel — металлические колокольчики
        "arp": 80,     # Lead 1 (square) — квадратный чиптьюн лид
        "pad": 89,     # Pad 2 (warm) — мягкий синтезатор
        "bass": 38,    # Synth Bass 1 — упругий синт-бас
        "perc": 0,     # Барабаны (канал 10)
    }

    midi_path = OUT / "roblox_bounce.mid"
    print(f"-> Сведение, мастеринг и экспорт детского трека в MIDI...")
    _export(tracks, midi_path, bpm, inst, lufs=-14.0)

    print("\n" + "=" * 60)
    print("   ГЕНЕРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
    print(f"   Файл сохранен: {midi_path.resolve()}")
    print("   Параметры аранжировки:")
    print("     - Темп: 130 BPM (Быстрый, веселый)")
    print("     - Тональность: C Major (Чистый мажор)")
    print("     - Glockenspiel мелодия: порхающие фразы с украшениями")
    print("     - Chiptune Arp: бегущие 8-битные пассажи")
    print("     - Synth Bass: прыгающий ритмический рисунок")
    print("     - Drums: веселый танцевальный бит 4-на-4")
    print("=" * 60)

if __name__ == "__main__":
    generate_roblox()
