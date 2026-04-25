## Архитектура

Проект построен по **гексагональной (ports-and-adapters) архитектуре** со строгим разделением слоёв:

```
┌─────────────────────────────────────────────────┐
│ Presentation / CLI  (scripts/)                  │
├─────────────────────────────────────────────────┤
│ Application  (harmonize(), generate_idea(),     │
│              idea_tool.py, composition/)         │
├─────────────────────────────────────────────────┤
│ Domain  (types, engines, generators, theory,    │
│         rhythm, composer, modifiers — чистая    │
│         логика, без I/O)                        │
├─────────────────────────────────────────────────┤
│ Infrastructure  (midi.py, virtual_midi.py,      │
│                 vst_player.py, presets.py)       │
└─────────────────────────────────────────────────┘
```

**Главное правило:** доменные модули никогда не делают I/O. Только `midi.py`, `virtual_midi.py`, `vst_player.py` взаимодействуют с внешним миром.

---

## Назначение

**Melodica** — Python-библиотека для автоматической композиции и гармонизации музыки. Основные возможности:

- **Гармонизация:** 4 движка преобразуют мелодии в аккордовые последовательности
- **Генерация фраз:** 166+ специализированных генераторов создают партии инструментов (бас, арпеджио, пэды, ударные) в десятках жанров
- **Idea Tool:** шестиэтапный пайплайн композиции, собирающий фразы в многодорожечные треки
- **Live-режим:** real-time MIDI вывод через виртуальные порты (`python-rtmidi`)
- **Экспорт MIDI:** готовые файлы для DAW (Logic, Ableton, Reaper) и VST инструментов

---

## Модульная структура

### Domain Types
| Модуль | Назначение |
|--------|-----------|
| `types.py` | Ядро: `Note`, `NoteInfo`, `ChordLabel`, `Scale`, `HarmonizationRequest`, `PhraseInstance`, `MusicTimeline`, `Track`, `Arrangement` |
| `types_pkg/_notes.py` | Ноты, pitch-классы |
| `types_pkg/_theory.py` | Муз. теория: `Mode`, `Quality`, `Scale` |
| `types_pkg/_phrases.py` | Фразы, `PhraseInstance` |
| `types_pkg/_timeline.py` | Таймлайн, `Track`, `Arrangement` |

### Theory
| Модуль | Содержание |
|--------|-----------|
| `theory/modes.py` | 70+ ладов (`Mode` enum) |
| `theory/chords.py` | 18 типов аккордов (`Quality` enum), шаблоны `CHORD_TEMPLATES` |
| `theory/modulation.py` | Модуляции между тональностями |

### Engines (движки гармонизации)
Все имплементируют протокол `HarmonizerPort`. Factory: `build_engine(engine_id)`.

| Модуль | Тип | Описание |
|--------|-----|----------|
| `engines/functional.py` | Engine 0 | Функциональная гармония (T-S-D-T каденции) |
| `engines/rule_based.py` | Engine 1 | Взвешенный граф аккордовых переходов + Viterbi |
| `engines/adaptive.py` | Engine 2 | Адаптивный движок, учитывающий простоту |
| `engines/hmm_engine.py` | Engine 3 | Скрытая марковская модель с beam search (по умолчанию) |

### Generators (166+ файлов)
Все наследуют `PhraseGenerator(ABC)` с методом `render()`. Factory: `create_generator()`.

| Категория | Примеры |
|-----------|---------|
| **Мелодические** | `melody.py`, `markov.py`, `neural_melody.py` |
| **Басовые** | `bass.py`, `eight_o_eight.py`, `sub_bass.py` |
| **Арпеджио** | `arpeggiator.py`, `arpeggio_variants*.py` |
| **Оркестровые** | `strings.py`, `brass.py`, `woodwinds.py`, `choir.py` |
| **Электронные** | `trap.py`, `drill.py`, `house.py`, `dnb.py`, `future_bass.py`, `afro_beats.py`, `latin_trap.py` |
| **Ударные** | `drums.py`, `percussion.py`, `hi_hats.py`, `conga.py` |
| **Игровая музыка** | `game_bgm.py`, `game_battle.py`, `game_overworld.py` |

### Composer
Продвинутая композиция:

| Модуль | Функция |
|--------|---------|
| `voice_leading.py` | SATB голосоведение |
| `tension_curve.py` | Кривые напряжения/драматургии |
| `style_profiles.py` | Стилевые профили |
| `non_chord_tones.py` | Неаккордовые тона (проходящие, вспомогательные, задержания) |
| `texture_controller.py` | Управление плотностью фактуры |
| `articulations.py` | Артикуляции через CC automation |
| `psychoacoustic.py` | Психоакустический анализ |
| `harmonic_verifier.py` | Детектор гармонических коллизий |
| `phrase_memory.py` | Память фраз для непрерывности |
| `harmonic_awareness.py` | Гармоническая осведомлённость при генерации |
| `candidate_scorer.py` | Скоринг кандидатов |
| `unified_style.py` | Унифицированная стилевая система |
| `diagnostics.py` | Диагностика композиции |

### Modifiers
Пост-обработка фраз:

| Модуль | Трансформации |
|--------|--------------|
| `rhythmic.py` | Квантизация, свинг, хуманизация |
| `harmonic.py` | Транспозиция, mirror, inversion |
| `dynamic.py` | Crescendo, diminuendo, velocity shaping |
| `voice_leading.py` | Голосоведение |
| `aesthetic.py` | Эстетические модификации |
| `variations.py` | Вариации |
| `voicings.py` | Аккордовые расположения |
| `rc_variations*.py` | Вариации RenderContext |

### Rhythm
Генерация ритмических сеток независимо от высоты:

| Модуль | Алгоритм |
|--------|----------|
| `euclidean.py` | Евклидовы ритмы |
| `probabilistic.py` | Вероятностная генерация |
| `subdivision.py` | Субдивизии |
| `schillinger.py` | Система Шиллингера |
| `motif.py` | Мотивная разработка |
| `library.py` | Библиотека паттернов |
| `polyrhythm.py` | Полиритмия |
| `bass_rhythm.py` | Басовые ритмы |
| `markov_rhythm.py` | Марковские ритмы |
| `rhythm_lab.py` | Экспериментальные ритмы |

`RhythmCoordinator` синхронизирует ритмические сетки между треками.

### Infrastructure
| Модуль | Библиотека | Функция |
|--------|-----------|---------|
| `midi.py` | `mido` | Чтение/запись MIDI файлов |
| `virtual_midi.py` | `python-rtmidi` (опц.) | Виртуальные MIDI порты |
| `vst_player.py` | `pedalboard` (опц.) | VST3 плагины, рендер в WAV |
| `live_loopback.py` | `python-rtmidi` (опц.) | Live playback с синхронизацией DAW |
| `presets.py` | — | JSON пресеты конфигураций |

### Application
| Модуль | Назначение |
|--------|-----------|
| `idea.py` | Базовая генерация идей |
| `idea_tool.py` | Шестиэтапный пайплайн композиции |
| `composition/__init__.py` | `Composition`, `Section`, `Style`, `MusicDirector` DSL |
| `application/orchestration.py` | Оркестровка треков |
| `application/automation.py` | CC automation |

---

## Стек технологий

| Библиотека | Версия | Назначение |
|-----------|--------|-----------|
| `mido` | >=1.3 | MIDI I/O |
| `numpy` | >=1.24 | Krumhansl-Schmuckler, аудио |
| `torch` | >=2.0 | Опционально (`[neural]`): нейросетевая мелодия |
| `python-rtmidi` | >=1.5 | Опционально (`[live]`): виртуальные MIDI порты |
| `pedalboard` | >=0.9 | Опционально (`[vst]`): VST3 хостинг |
| **Python** | **>=3.11** | Runtime |
| `pytest` | >=7.4 | Тестирование |
| `pytest-cov` | >=4.1 | Покрытие |
| `ruff` | — | Линтинг (line-length 100) |
| `mutmut` | — | Мутационное тестирование |

---

## Шаблоны проектирования

1. **Ports-and-Adapters (Hexagonal):** доменная логика изолирована от I/O
2. **Protocol-based DIP:** `HarmonizerPort`, `PhraseGeneratorProtocol`, `PhraseModifier`, `RhythmGenerator` — протоколы вместо абстрактных классов
3. **Factory:** `build_engine()`, `create_generator()` — централизованное создание объектов
4. **Abstract Base Class:** `PhraseGenerator(ABC)` с `render()` — единый интерфейс для 166+ генераторов
5. **Dataclass-heavy:** замороженные/мутабельные датаклассы с валидацией в `__post_init__`
6. **Strategy:** каждый движок гармонизации — отдельная стратегия
7. **Pipeline:** Idea Tool — конвейер из 6 этапов
8. **Composition over Inheritance:** генераторы компонуют ритм-генераторы, RenderContext, цепочки модификаторов
9. **Lazy Imports:** опциональные зависимости подгружаются try/except, при ошибке — `None`

---

## Входные точки

### Library API
```python
from melodica import (
    harmonize,           # гармонизация мелодии
    Note, Scale, Mode,   # доменные типы
    detect_chord,        # определение аккорда
    detect_scale,        # определение тональности (Krumhansl-Schmuckler)
    from_midi,           # загрузка MIDI
    notes_to_midi,       # экспорт нот в MIDI
    chords_to_midi,      # экспорт аккордов в MIDI
    generate_idea,       # генерация идеи
    slots_to_notes,      # конвертация слотов в ноты
)
```

### CLI
```bash
python scripts/melodica_cli.py arrange \
    --progression "I-V-vi-IV" \
    --key "C major" \
    --preset presets/ambient.json \
    --output output.mid
```

---

## Пайплайн Idea Tool

```
1. Source Collection  → сбор источников (мелодия, аккорды, стиль)
2. Selection          → выбор подходящих генераторов
3. Parameter Injection → инъекция параметров в генераторы
4. Rendering          → вызов render() у каждого генератора
5. Arrangement        → размещение фраз на таймлайне
6. Post-processing    → текстурный контроль, velocity shaping
```

`RenderContext` передаёт состояние между последовательными фразами для мелодической непрерывности.

---

## MIDI экспорт

`export_midi()` и `export_multitrack_midi()` поддерживают:

- Key signature и time signature события
- Маркеры
- CC события: expression (11), sustain (64), pitch bend, volume (7), pan (10), modulation (1), attack (73), release (72), reverb (91), chorus (93)
- RPN pitch bend range
- Keyswitch события
- Program change
- Диагностическую информацию по трекам

---

## Тестирование

- **56+ тестовых файлов** покрывают все основные группы модулей
- **pytest fixtures** в `conftest.py`
- **pytest-cov** для измерения покрытия
- **mutmut** для мутационного тестирования (`melodica/harmonize/`)
- Целевые файлы для непокрытых веток: `test_extra_coverage.py`, `test_generators_uncovered.py`, `test_rhythm_uncovered.py`, `test_harmonize_edge.py`, `test_harmonize_mutations.py`, `test_harmonize_metamorphic.py`

---

## Ключевые архитектурные решения

1. **Иммутабельное доменное ядро:** `Note` и `Scale` — frozen dataclasses; мутации разрешены только на границах инфраструктуры
2. **Система ступеней (Roman numerals):** весь гармонический анализ — в римских цифрах (I-VII) с поддержкой borrowed chords (`bII`, `bVI`), secondary dominants, modal interchange
3. **Krumhansl-Schmuckler:** стандартный алгоритм музыкальной психологии для автоопределения тональности
4. **Viterbi / HMM:** rule-based engine использует Viterbi по взвешенному графу; HMM engine расширяет до полной скрытой марковской модели
5. **Разделение ритма и высоты:** `rhythm/` генерирует `RhythmEvent` независимо; `RhythmCoordinator` синхронизирует сетки между треками
6. **Composition DSL:** `Composition` + `Section` + `Style` + `MusicDirector` — мини-DSL для структуры песен
7. **JSON-пресеты:** в `presets/` лежат конфигурации генераторов и модификаторов для не-кодовой настройки

---

## Потенциальные проблемы

| Проблема | Описание |
|----------|----------|
| **Раздувание `factory.py`** | ~1400 строк, гигантский `_GENERATOR_MAP` — OCP нарушается на практике |
| **Дублирование генераторов** | 166+ генераторов, многие с пересекающейся логикой |
| **Устаревшая валидация** | `HarmonizationRequest.__post_init__` проверяет engine_id 0-2, а engine 3 уже добавлен |
| **Два модуля гармонизации** | `engines/` и `harmonize/` — частичное дублирование |
| **Крупные файлы** | `factory.py` (~1400), `melody.py` (865), `idea_tool.py` (902), `midi.py` (677), `bass.py` (451) — кандидаты на декомпозицию |
| **Неполное покрытие генераторов** | Из 166+ генераторов явно протестированы ~50-70 |
| **Нет CI/CD** | Отсутствуют `.github/workflows/` или аналоги |
| **Скудная документация** | Только `docs/Generators.md` (билингвальный EN/RU), нет API reference |
| **Неоднородный стиль импортов** | `from melodica.types import X` и `import melodica.types` используются бессистемно |

---

## Связность модулей (граф зависимостей)

```
__init__.py (публичное API)
 ├── types.py ──────────► types_pkg/{_notes, _theory, _phrases, _timeline}
 │                          └── theory/{modes, chords}
 ├── detection.py ───────► types, utils, numpy
 ├── midi.py ────────────► types, utils, theory, mido
 ├── idea.py ────────────► types, generators, render_context
 └── vst_player.py ──────► mido, numpy, pedalboard (опц.)

engines/ → {functional, rule_based, adaptive, hmm_engine}
  ├── functional.py ─────► types, utils
  ├── rule_based.py ─────► types, utils, rule_db
  └── hmm_engine.py ─────► types, utils

generators/ → 166+ модулей
  ├── melody.py ─────────► generators (base), types, rhythm
  ├── bass.py ───────────► generators, types, utils, rhythm
  └── markov.py ─────────► generators, types

harmonize/ → {auto_harmonize, advanced, _specialized, _hmm_*}

composer/ → {voice_leading, tension_curve, style_profiles,
            non_chord_tones, texture_controller, articulations, ...}

modifiers/ → {rhythmic, harmonic, dynamic, voice_leading, aesthetic, ...}

rhythm/ → {euclidean, probabilistic, subdivision, schillinger, ...}

composition/ → types, presets, render_context, application/{automation, orchestration}
```

**Правила зависимостей:**
- `types.py` — только `theory/` и `types_pkg/`
- `utils.py` — только `types.py`
- `detection.py` — types + utils + numpy (чистые алгоритмы)
- `engines/` — types + utils + rule_db (без I/O)
- `generators/` — types + rhythm + render_context (без I/O)
- `midi.py` — **единственный модуль**, импортирующий `mido`
