# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula_ch2.py — ДРАКУЛА: Глава II (Dracula: Chapter II - Gothic Album in Hungarian Minor)

Музыкальная адаптация второй главы готического романа Брэма Стокера «Дракула»
(Дневник Джонатана Харкера — продолжение).

Стиль: Мрачный, величественный готический оркестровый романс.
Основная гамма: Венгерский минор (Hungarian Minor) — идеальный выбор, сочетающий
трагизм восточно-европейского фольклора Трансильвании и зловещее благородство.

Альбом состоит из 5 цепляющих треков:

  I.   Засовы и цепи (Chains and Bolts) — 68 BPM.
       Виолончель, клавесин, контрабас. Гремящие цепи, массивные засовы и скрежет ключа.
       
  II.  Дети ночи (Children of the Night) — 80 BPM.
       Скрипка соло, гобой, оркестровые струнные, дрон. Вой волков в долинах Карпат.
       
  III. Комната без зеркал (The Mirrorless Room) — 54 BPM.
       Флейта, струнное пиццикато, нейлоновая гитара. Бритье у окна, исчезновение отражения
       графа и внезапный хват за горло.
       
  IV.  Карфакс и Лечебница (Carfax and the Asylum) — 72 BPM.
       Цимбалы (Dulcimer), нейлоновая гитара, акустический бас. Старинная усадьба Дракулы
       в Англии под Лондоном, чертежи и любовь к полумраку.
       
  V.   Узник пропасти (Prisoner of the Abyss) — 96 BPM.
       Орган, струнный ансамбль, тяжелые литавры, бас. Глубокое ущелье под окном замка,
       осознание безвыходности Джонатана: «Я — узник!»
"""

import random
from pathlib import Path

from melodica import types
from melodica.theory import Quality
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.drone import DroneGenerator
from melodica.composer.album_pipeline import produce_track, Mood

# B Hungarian Minor (root=11, mode=HUNGARIAN_MINOR): B, C#, D, E#, F#, G, A#
# Ультра-зловещая тональность, традиционная для тяжелых готических произведений
KEY = types.Scale(root=11, mode=types.Mode.HUNGARIAN_MINOR)

random.seed(1897)  # Год первой публикации романа Брэма Стокера
OUT = Path("output/album_dracula_ch2")
OUT.mkdir(parents=True, exist_ok=True)


# =====================================================================
# I. Засовы и цепи (Chains and Bolts) — 68 BPM
# =====================================================================
def produce_chains_and_bolts():
    """
    Тяжелый, медленный и напряженный трек.
    Виолончель соло выводит зловещую, опускающуюся тему. Клавесин имитирует металлический
    скрежет, а шагающий контрабас задает ритмические шаги Джонатана у входа.
    """
    bpm, dur = 68, 128.0
    
    # Гармонический круг с фокусом на субдоминантовое напряжение: Bm - C#dim - F# - Bm
    chords = []
    prog = [
        (11, Quality.MINOR),        # Bm
        (1, Quality.DIMINISHED),    # C#dim
        (6, Quality.MAJOR),         # F# (доминанта)
        (11, Quality.MINOR)         # Bm
    ]
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Виолончель - выразительное, медленное соло (Cello - Program 42)
    # Задаем высокий motif_probability для четко очерченной запоминающейся структуры
    cello = MelodyGenerator(
        GeneratorParams(
            density=0.42, complexity=0.70,
            velocity_range=(75, 105),
            key_range_low=45, key_range_high=69
        ),
        phrase_length=8.0,
        motif_probability=0.88,
        ornament_probability=0.30
    ).render(chords, KEY, dur)

    # Клавесин (Harpsichord - Program 6) — редкие, сухие металлические щипки (как скрежет цепей)
    harpsichord = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.35,
            velocity_range=(50, 75),
            key_range_low=59, key_range_high=83
        ),
        pattern="up_down", note_duration=0.5
    ).render(chords, KEY, dur)

    # Контрабас (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.45,
            velocity_range=(65, 85),
            key_range_low=23, key_range_high=45
        ),
        style="walking"
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"cello": cello, "harpsichord": harpsichord, "bass": bass},
        bpm=bpm,
        instruments={"cello": 42, "harpsichord": 6, "bass": 32},
        path=OUT / "01_Chains_and_Bolts.mid",
        mood=Mood.CHAMBER, key=KEY
    )


# =====================================================================
# II. Дети ночи (Children of the Night) — 80 BPM
# =====================================================================
def produce_children_of_the_night():
    """
    Певучий, воющий скрипичный романс.
    Скрипка выводит трагические, широкие фразы в стиле карпатских песен.
    Гобой отвечает ей на расстоянии, а глубокие струнные пэды создают туманную атмосферу.
    """
    bpm, dur = 80, 144.0
    
    # Трагическая цыганская гармония: Bm - G - Em - F# - G - F# - Bm - Bm
    prog = [
        (11, Quality.MINOR),   # Bm
        (7, Quality.MAJOR),    # G
        (4, Quality.MINOR),    # Em
        (6, Quality.MAJOR),    # F#
        (7, Quality.MAJOR),    # G
        (6, Quality.MAJOR),    # F#
        (11, Quality.MINOR),   # Bm
        (11, Quality.MINOR)    # Bm
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Скрипка - лид с цыганским пением (Violin - Program 40, высокая экспрессия)
    violin = MelodyGenerator(
        GeneratorParams(
            density=0.55, complexity=0.82,
            velocity_range=(80, 115),
            key_range_low=62, key_range_high=86
        ),
        phrase_length=8.0,
        motif_probability=0.92,
        ornament_probability=0.45,  # Украшения для выразительности воя волков
        register_smoothness=0.65
    ).render(chords, KEY, dur)

    # Гобой - таинственный сольный ответ издали (Oboe - Program 68)
    oboe = MelodyGenerator(
        GeneratorParams(
            density=0.25, complexity=0.60,
            velocity_range=(65, 90),
            key_range_low=59, key_range_high=76
        ),
        phrase_length=12.0,
        motif_probability=0.80,
        ornament_probability=0.15
    ).render(chords, KEY, dur)

    # Ансамбль струнных (Strings Ensemble - Program 48) - плывущие, обволакивающие гармонии
    strings = StringsEnsembleGenerator(
        GeneratorParams(
            density=0.40,
            velocity_range=(55, 80),
            key_range_low=47, key_range_high=71
        ),
        section_size=6, articulation="legato"
    ).render(chords, KEY, dur)

    # Низкий, зловещий гул (Drone) для ночной глубины
    drone = DroneGenerator(
        GeneratorParams(density=0.03, key_range_low=23, key_range_high=35),
        velocity=45
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"violin": violin, "oboe": oboe, "strings": strings, "drone": drone},
        bpm=bpm,
        instruments={"violin": 40, "oboe": 68, "strings": 48, "drone": 43},
        path=OUT / "02_Children_of_the_Night.mid",
        mood=Mood.CINEMATIC, key=KEY
    )


# =====================================================================
# III. Комната без зеркал (The Mirrorless Room) — 54 BPM
# =====================================================================
def produce_mirrorless_room():
    """
    Камерный саспенс.
    Мелкие, пугливые шаги струнного пиццикато на фоне задумчивой, холодной флейты.
    Нейлоновая гитара добавляет мягкую, но неуверенную тональную опору.
    """
    bpm, dur = 54, 128.0
    
    # Минималистичные качели напряжения: Bm - F# - G - F#
    prog = [
        (11, Quality.MINOR),
        (6, Quality.MAJOR),
        (7, Quality.MAJOR),
        (6, Quality.MAJOR)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Одинокая флейта в холодном тумане (Flute - Program 73)
    flute = MelodyGenerator(
        GeneratorParams(
            density=0.18, complexity=0.50,
            velocity_range=(45, 75),
            key_range_low=60, key_range_high=80
        ),
        phrase_length=12.0,
        motif_probability=0.85,
        ornament_probability=0.25
    ).render(chords, KEY, dur)

    # Струнное пиццикато (Pizzicato Strings - Program 45) — крадущееся, нервное
    pizz = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.32,
            velocity_range=(45, 68),
            key_range_low=47, key_range_high=71
        ),
        pattern="pinky_up_down", note_duration=0.5
    ).render(chords, KEY, dur)

    # Мягкая классическая гитара (Nylon Guitar - Program 24)
    guitar = AmbientPadGenerator(
        GeneratorParams(
            density=0.03,
            velocity_range=(40, 60),
            key_range_low=47, key_range_high=67
        ),
        voicing="spread", overlap=0.1
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"flute": flute, "pizz": pizz, "guitar": guitar},
        bpm=bpm,
        instruments={"flute": 73, "pizz": 45, "guitar": 24},
        path=OUT / "03_The_Mirrorless_Room.mid",
        mood=Mood.INTIMATE, key=KEY
    )


# =====================================================================
# IV. Карфакс и Лечебница (Carfax and the Asylum) — 72 BPM
# =====================================================================
def produce_carfax_and_asylum():
    """
    Этнический карпатский колорит встречается с лондонскими туманами.
    Быстрые, кружащиеся арпеджио цимбал сплетаются с размеренным перебором гитары
    и глубоким, уверенным шагом баса.
    """
    bpm, dur = 72, 144.0
    
    # Таинственное блуждание по чертежам: Bm - G - Em - Bm - G - C#dim - F# - F#
    prog = [
        (11, Quality.MINOR),
        (7, Quality.MAJOR),
        (4, Quality.MINOR),
        (11, Quality.MINOR),
        (7, Quality.MAJOR),
        (1, Quality.DIMINISHED),
        (6, Quality.MAJOR),
        (6, Quality.MAJOR)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Цимбалы (Dulcimer - Program 15) — звенящие, вибрирующие узоры средневековья
    dulcimer = ArpeggiatorGenerator(
        GeneratorParams(
            density=0.68,
            velocity_range=(55, 85),
            key_range_low=59, key_range_high=83
        ),
        pattern="up_down_full", note_duration=0.25
    ).render(chords, KEY, dur)

    # Мягкая нейлоновая гитара (Nylon Guitar - Program 24) на бэкграунде
    guitar = AmbientPadGenerator(
        GeneratorParams(
            density=0.04,
            velocity_range=(45, 65),
            key_range_low=47, key_range_high=71
        ),
        voicing="spread", overlap=0.15
    ).render(chords, KEY, dur)

    # Акустический контрабас (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.50,
            velocity_range=(60, 80),
            key_range_low=23, key_range_high=45
        ),
        style="walking"
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"dulcimer": dulcimer, "guitar": guitar, "bass": bass},
        bpm=bpm,
        instruments={"dulcimer": 15, "guitar": 24, "bass": 32},
        path=OUT / "04_Carfax_and_the_Asylum.mid",
        mood=Mood.CHAMBER, key=KEY
    )


# =====================================================================
# V. Узник пропасти (Prisoner of the Abyss) — 96 BPM
# =====================================================================
def produce_prisoner_of_abyss():
    """
    Трагический, мощный оркестровый финал.
    Величественный готический церковный орган вступает в яростный диалог с
    драматическим легато струнных и мощными, грохочущими ударами литавр на пропасти.
    """
    bpm, dur = 96, 160.0
    
    # Мощная нисходящая и восходящая трагедия: Bm - Em - C#dim - F# - G - Em - F# - Bm
    prog = [
        (11, Quality.MINOR),
        (4, Quality.MINOR),
        (1, Quality.DIMINISHED),
        (6, Quality.MAJOR),
        (7, Quality.MAJOR),
        (4, Quality.MINOR),
        (6, Quality.MAJOR),
        (11, Quality.MINOR)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Струнные легато (Strings Ensemble - Program 48) — широкое отчаянное пение
    strings = StringsEnsembleGenerator(
        GeneratorParams(
            density=0.65,
            velocity_range=(85, 115),
            key_range_low=52, key_range_high=79
        ),
        section_size=8, articulation="legato"
    ).render(chords, KEY, dur)

    # Церковный орган (Church Organ - Program 19) — монументальный готический плач
    organ = AmbientPadGenerator(
        GeneratorParams(
            density=0.04,
            velocity_range=(75, 110),
            key_range_low=47, key_range_high=71
        ),
        voicing="cluster", overlap=0.25
    ).render(chords, KEY, dur)

    # Глубокий, тяжелый контрабас (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(
            density=0.55,
            velocity_range=(80, 105),
            key_range_low=23, key_range_high=45
        ),
        style="walking"
    ).render(chords, KEY, dur)

    # Тяжелые литавры (Timpani - Program 47) — гремят, как камни, падающие в бездну
    timpani = []
    for i in range(int(dur / 4.0)):
        t = i * 4.0
        timpani.append(types.NoteInfo(pitch=35, start=t, duration=1.0, velocity=108))
        if i % 2 == 1:
            timpani.append(types.NoteInfo(pitch=38, start=t + 2.0, duration=0.5, velocity=98))

    produce_track(
        tracks={"strings": strings, "organ": organ, "bass": bass, "timpani": timpani},
        bpm=bpm,
        instruments={"strings": 48, "organ": 19, "bass": 32, "timpani": 47},
        path=OUT / "05_Prisoner_of_the_Abyss.mid",
        mood=Mood.AGGRESSIVE, key=KEY
    )


# =====================================================================
# Запуск компиляции альбома
# =====================================================================
if __name__ == "__main__":
    print("=" * 75)
    print("   БРЭМ СТОКЕР — ДРАКУЛА: ГЛАВА II (Gothic Album in Hungarian Minor)")
    print("   Дневник Джонатана Харкера (продолжение)")
    print("=" * 75)
    
    print("-> Компиляция трека 1: Засовы и цепи...")
    produce_chains_and_bolts()
    
    print("-> Компиляция трека 2: Дети ночи...")
    produce_children_of_the_night()
    
    print("-> Компиляция трека 3: Комната без зеркал...")
    produce_mirrorless_room()
    
    print("-> Компиляция трека 4: Карфакс и Лечебница...")
    produce_carfax_and_asylum()
    
    print("-> Компиляция трека 5: Узник пропасти...")
    produce_prisoner_of_abyss()
    
    print("\n" + "=" * 75)
    print("   ГЛАВА II УСПЕШНО СКОМПИЛИРОВАНА!")
    print(f"   Файлы сохранены в папку: {OUT.resolve()}")
    print("=" * 75)
