# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
album_dracula.py — ДРАКУЛА (Dracula: A Gothic Album in Hungarian Minor)

Музыкальная адаптация знаменитого готического романа Брэма Стокера в переводе 
Л. Ю. Бриловой и Т. Н. Красавченко, с иллюстрациями Альфреда Эберлинга.

Стиль: Мрачный, величественный готический оркестровый романс.
Основная гамма: Венгерский минор (Hungarian Minor) — идеальный выбор, сочетающий
трагизм восточно-европейского фольклора Трансильвании и зловещее благородство.

Альбом состоит из 5 цепляющих треков, каждый из которых передает ключевую главу романа:

  I.   Замок в Карпатах (The Carpathian Castle) — 76 BPM. 
       Скрипка и орган. Одинокий экипаж Джонатана Харкера приближается к ущелью Борго.
  
  II.  Архив графа (The Count's Archives) — 92 BPM. 
       Виолончель, клавесин и шагающий контрабас. Интеллектуальный ужас посреди библиотеки.
  
  III. Кровь — это жизнь (Blood is the Life) — 112 BPM. 
       Агрессивный хор, орган, звенящие цимбалы и тяжелые литавры. Безумие Ренфилда.
  
  IV.  Хайгейтский склеп (Highgate Vault) — 56 BPM. 
       Пиццикато струнных, флейта и мягкая гитара. Блуждание Люси Вестенра при свете луны.
  
  V.   Охота на Вампира (The Vampire Hunt) — 120 BPM. 
       Эпический оркестровый финал. Погоня Ван Хелсинга и его команды по ущельям Трансильвании.
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
OUT = Path("output/album_dracula")
OUT.mkdir(parents=True, exist_ok=True)

def _off(notes, offset):
    """Сдвиг нот по сетке времени для стыковки разделов."""
    return [
        types.NoteInfo(pitch=n.pitch, start=n.start + offset,
                       duration=n.duration, velocity=n.velocity)
        for n in notes
    ]


# =====================================================================
# I. Замок в Карпатах (The Carpathian Castle) — 76 BPM
# =====================================================================
def produce_carpathian_castle():
    """
    Лирический и зловещий трек.
    Скрипка соло выводит плачущую, цепляющую тему на фоне тяжелого органного дрона.
    """
    bpm, dur = 76, 128.0
    
    # Гармонический круг: Bm - Em - F# - Bm (B Hungarian Minor)
    # В тонах: Bm (11), Em (4), F# (6)
    chords = []
    prog = [
        (11, Quality.MINOR),
        (4, Quality.MINOR),
        (6, Quality.MAJOR),
        (11, Quality.MINOR)
    ]
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % 4]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Скрипка - лид с цепляющим мотивом (motif_prob=0.9, ornament_prob=0.4 для цыганского колорита)
    violin = MelodyGenerator(
        GeneratorParams(density=0.55, complexity=0.75, velocity_range=(80, 110)),
        phrase_length=8.0, note_range_low=62, note_range_high=86,
        motif_probability=0.90, ornament_probability=0.40,
        register_smoothness=0.60
    ).render(chords, KEY, dur)

    # Церковный орган на фоне (Church Organ - Program 19)
    organ = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=47, key_range_high=71),
        voicing="spread", overlap=0.2
    ).render(chords, KEY, dur)

    # Низкий, зловещий гул (Drone) для нагнетания
    drone = DroneGenerator(
        GeneratorParams(density=0.02, key_range_low=23, key_range_high=35),
        velocity=50
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"violin": violin, "organ": organ, "drone": drone},
        bpm=bpm,
        instruments={"violin": 40, "organ": 19, "drone": 43}, # Violin, Church Organ, Contrabass
        path=OUT / "01_The_Carpathian_Castle.mid",
        mood=Mood.CHAMBER, key=KEY
    )


# =====================================================================
# II. Архив графа (The Count's Archives) — 92 BPM
# =====================================================================
def produce_counts_archives():
    """
    Интеллектуальный саспенс.
    Клавесин очерчивает быстрые сухие пассажи, а виолончель ведет задумчивую, 
    цепляющую мелодию.
    """
    bpm, dur = 92, 144.0
    
    # Движение баса и гармонии: Bm - G - C#dim - F#
    prog = [
        (11, Quality.MINOR),       # Bm
        (7, Quality.MAJOR),        # G
        (1, Quality.DIMINISHED),   # C#dim
        (6, Quality.MAJOR)         # F# (доминанта)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % 4]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Виолончель - глубокое, цепляющее соло (Cello - Program 42)
    cello = MelodyGenerator(
        params=GeneratorParams(
            density=0.48, complexity=0.68,
            velocity_range=(75, 100),
            key_range_low=47, key_range_high=71
        ),
        phrase_length=8.0,
        motif_probability=0.85,
        ornament_probability=0.25
    ).render(chords, KEY, dur)

    # Клавесин (Harpsichord - Program 6) — сухой, очерчивающий звук библиотеки
    harpsichord = ArpeggiatorGenerator(
        GeneratorParams(density=0.65, velocity_range=(45, 75)),
        pattern="up_down", note_duration=0.25
    ).render(chords, KEY, dur)

    # Контрабас (Acoustic Bass - Program 32)
    bass = BassGenerator(
        GeneratorParams(density=0.5, velocity_range=(65, 85), key_range_low=23, key_range_high=45),
        style="walking"
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"cello": cello, "harpsichord": harpsichord, "bass": bass},
        bpm=bpm,
        instruments={"cello": 42, "harpsichord": 6, "bass": 32},
        path=OUT / "02_The_Counts_Archives.mid",
        mood=Mood.CHAMBER, key=KEY
    )


# =====================================================================
# III. Кровь — это жизнь (Blood is the Life) — 112 BPM
# =====================================================================
def produce_blood_is_life():
    """
    Агрессивный, пугающий трек. Символизирует безумие вампиризма и Ренфилда.
    Использует яростные переливы цимбал, агрессивный хор и тяжелые литавры.
    """
    bpm, dur = 112, 160.0
    
    # Драматический подъем: Bm - Em - C#dim - F# - G - F#
    prog = [
        (11, Quality.MINOR),
        (4, Quality.MINOR),
        (1, Quality.DIMINISHED),
        (6, Quality.MAJOR),
        (7, Quality.MAJOR),
        (6, Quality.MAJOR)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Лид-синтезатор/Готическая Скрипка (Program 40 в высоком регистре)
    lead_violin = MelodyGenerator(
        GeneratorParams(density=0.72, complexity=0.90, velocity_range=(90, 120)),
        phrase_length=4.0, note_range_low=67, note_range_high=93,
        motif_probability=0.80, drama_shape="epic"
    ).render(chords, KEY, dur)

    # Агрессивный мужской хор (Choir Aahs - Program 52)
    choir = AmbientPadGenerator(
        GeneratorParams(density=0.04, key_range_low=47, key_range_high=71),
        voicing="cluster"
    ).render(chords, KEY, dur)

    # Быстрые, звенящие цимбалы (Dulcimer - Program 15) для восточно-европейской ярости
    dulcimer = ArpeggiatorGenerator(
        GeneratorParams(density=0.80, velocity_range=(60, 95)),
        pattern="up_down_full", note_duration=0.25
    ).render(chords, KEY, dur)

    # Тяжелые литавры (Timpani - Program 47) на сильные доли
    timpani = []
    for i in range(int(dur / 4.0)):
        t = i * 4.0
        timpani.append(types.NoteInfo(pitch=35, start=t, duration=1.0, velocity=105))
        if i % 2 == 1:
            timpani.append(types.NoteInfo(pitch=38, start=t + 2.0, duration=0.5, velocity=95))

    produce_track(
        tracks={"lead": lead_violin, "choir": choir, "dulcimer": dulcimer, "timpani": timpani},
        bpm=bpm,
        instruments={"lead": 40, "choir": 52, "dulcimer": 15, "timpani": 47},
        path=OUT / "03_Blood_is_the_Life.mid",
        mood=Mood.AGGRESSIVE, key=KEY
    )


# =====================================================================
# IV. Хайгейтский склеп (Highgate Vault) — 56 BPM
# =====================================================================
def produce_highgate_vault():
    """
    Нежный и пугающий ноктюрн блуждающей Люси.
    Пиццикато струнных, тихая флейта и перетекающие аккорды классической гитары.
    """
    bpm, dur = 56, 128.0
    
    # Лирический минор: Bm - G - Bm - F#
    prog = [
        (11, Quality.MINOR),
        (7, Quality.MAJOR),
        (11, Quality.MINOR),
        (6, Quality.MAJOR)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % 4]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Одинокая флейта в тумане (Flute - Program 73)
    flute = MelodyGenerator(
        GeneratorParams(density=0.15, complexity=0.45, velocity_range=(45, 70)),
        phrase_length=12.0, note_range_low=59, note_range_high=78,
        ornament_probability=0.30
    ).render(chords, KEY, dur)

    # Струнное пиццикато (Pizzicato Strings - Program 45), создающее эффект крадущихся шагов
    pizz = ArpeggiatorGenerator(
        GeneratorParams(density=0.35, velocity_range=(40, 65)),
        pattern="pinky_up_down", note_duration=0.5
    ).render(chords, KEY, dur)

    # Мягкая нейлоновая гитара (Nylon Guitar - Program 24)
    guitar = AmbientPadGenerator(
        GeneratorParams(density=0.03, key_range_low=47, key_range_high=71),
        voicing="spread", overlap=0.1
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"flute": flute, "pizz": pizz, "guitar": guitar},
        bpm=bpm,
        instruments={"flute": 73, "pizz": 45, "guitar": 24},
        path=OUT / "04_Highgate_Vault.mid",
        mood=Mood.INTIMATE, key=KEY
    )


# =====================================================================
# V. Охота на Вампира (The Vampire Hunt) — 120 BPM
# =====================================================================
def produce_vampire_hunt():
    """
    Эпический, стремительный финал альбома.
    Оркестровое легато струнных, духовая медь и галопирующий арпеджиатор.
    """
    bpm, dur = 120, 192.0
    
    # Стремительное движение: Bm - G - Em - F# -> C#dim - F# - Bm
    prog = [
        (11, Quality.MINOR),
        (7, Quality.MAJOR),
        (4, Quality.MINOR),
        (6, Quality.MAJOR),
        (1, Quality.DIMINISHED),
        (6, Quality.MAJOR),
        (11, Quality.MINOR),
        (11, Quality.MINOR)
    ]
    chords = []
    for i in range(int(dur / 4.0)):
        root, qual = prog[i % len(prog)]
        chords.append(types.ChordLabel(root=root, quality=qual, start=float(i * 4.0), duration=4.0))

    # Струнные легато (Strings Ensemble - Program 48) ведут стремительный хук
    strings = StringsEnsembleGenerator(
        GeneratorParams(density=0.60, velocity_range=(80, 115)),
        section_size=8, articulation="legato"
    ).render(chords, KEY, dur)

    # Трубы и медь (Brass Section - Program 61) выдувают зловещие акценты
    brass = MelodyGenerator(
        GeneratorParams(density=0.25, complexity=0.55, velocity_range=(75, 105)),
        phrase_length=8.0, note_range_low=59, note_range_high=74,
        motif_probability=0.75
    ).render(chords, KEY, dur)

    # Быстрый галоп цимбал (Dulcimer - Program 15) для безумного движения скачущих коней
    gallop = ArpeggiatorGenerator(
        GeneratorParams(density=0.75, velocity_range=(55, 80)),
        pattern="up_down", note_duration=0.25
    ).render(chords, KEY, dur)

    # Быстрый бас
    bass = BassGenerator(
        GeneratorParams(density=0.60, velocity_range=(85, 110), key_range_low=23, key_range_high=45),
        style="walking"
    ).render(chords, KEY, dur)

    produce_track(
        tracks={"strings": strings, "brass": brass, "gallop": gallop, "bass": bass},
        bpm=bpm,
        instruments={"strings": 48, "brass": 61, "gallop": 15, "bass": 32},
        path=OUT / "05_The_Vampire_Hunt.mid",
        mood=Mood.CINEMATIC, key=KEY
    )


# =====================================================================
# Запуск компиляции альбома
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("   БРЭМ СТОКЕР — ДРАКУЛА (Gothic Album in Hungarian Minor)")
    print("   Иллюстрации Альфреда Эберлинга")
    print("   Перевод: Л. Ю. Брилова, Т. Н. Красавченко")
    print("=" * 70)
    
    print("-> Компиляция трека 1: Замок в Карпатах...")
    produce_carpathian_castle()
    
    print("-> Компиляция трека 2: Архив графа...")
    produce_counts_archives()
    
    print("-> Компиляция трека 3: Кровь — это жизнь...")
    produce_blood_is_life()
    
    print("-> Компиляция трека 4: Хайгейтский склеп...")
    produce_highgate_vault()
    
    print("-> Компиляция трека 5: Охота на Вампира...")
    produce_vampire_hunt()
    
    print("\n" + "=" * 70)
    print("   АЛЬБОМ 'ДРАКУЛА' УСПЕШНО СКОМПИЛИРОВАН!")
    print(f"   Файлы сохранены в папку: {OUT.resolve()}")
    print("=" * 70)
