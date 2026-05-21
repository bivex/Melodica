# Continuous Album Mode — Режим непрерывного альбома

> Документ описывает **три экспертных системы** движка Melodica для создания
> бесшовных альбомов с автоматической дятонической модуляцией и
> многотрековой оркестровой синхронизацией переходов.

---

## Содержание

1. [Обзор архитектуры](#обзор-архитектуры)
2. [TransitionCoordinator](#transitioncoordinator)
   - [apply_ducking](#apply_ducking)
   - [apply_sweeps](#apply_sweeps)
   - [apply_lead_in_fill](#apply_lead_in_fill)
   - [orchestrate_transition](#orchestrate_transition) ← единый вызов
3. [ModulationEngine](#modulationengine)
   - [generate_modulation_bridge](#generate_modulation_bridge)
   - [Стратегии: pivot / dominant / chromatic](#стратегии)
4. [compile_continuous_album](#compile_continuous_album)
   - [Параметры](#параметры)
   - [Автоматический transition_pad](#автоматический-transition_pad)
   - [Схема обработки](#схема-обработки)
5. [Готовый пример: Дракула Глава IV](#готовый-пример-дракула-глава-iv)
6. [Шаблон нового альбома](#шаблон-нового-альбома)

---

## Обзор архитектуры

```
 Album Script
 ┌────────────────────────────────────────────┐
 │  build_track_N() → metadata dict           │
 │    {tracks, bpm, instruments,              │
 │     cc_events, key, tempo_events}          │
 └──────────────────┬─────────────────────────┘
                    │ list of dicts
                    ▼
 compile_continuous_album(...)
 ┌────────────────────────────────────────────┐
 │ 1. Для каждого трека:                      │
 │    • копирует ноты с временным сдвигом     │
 │    • сдвигает CC-события                   │
 │                                            │
 │ 2. В зоне нахлеста (overlap_beats):        │
 │    • CC 7 fade-out предыдущего             │
 │    • CC 7 fade-in нового                   │
 │    • [если ключи разные] → ModulationEngine│
 │      строит мост → transition_pad трек     │
 │                                            │
 │ 3. produce_track(combined) → .mid          │
 └────────────────────────────────────────────┘
```

---

## TransitionCoordinator

**Файл**: `melodica/composer/transition_coordinator.py`

```python
from melodica.composer.transition_coordinator import TransitionCoordinator
```

Статический класс — все методы вызываются без инстанса.
Работает **мутируя** переданные словари `tracks` и `cc_events` на месте.

---

### apply_ducking

```python
TransitionCoordinator.apply_ducking(
    tracks,           # dict[str, Track | list[NoteInfo]]
    target_tracks,    # list[str]  — имена треков
    start_beat,       # float      — начало окна дакинга
    end_beat,         # float      — конец окна дакинга
    duck_factor=0.0,  # 0.0 = полное удаление, 0.5 = половина velocity
)
```

Ноты, у которых есть пересечение с `[start_beat, end_beat]`:
- `duck_factor=0.0` → нота **удаляется** из трека
- `duck_factor=0.5` → velocity умножается на `0.5`

**Когда использовать**: предроповое молчание баса и ударных, «вакуум» перед секцией.

---

### apply_sweeps

```python
TransitionCoordinator.apply_sweeps(
    tracks,           # dict — нужен для проверки наличия трека
    cc_events,        # dict — сюда добавляются новые события
    target_tracks,    # list[str]
    cc_num,           # int — номер CC (74 = фильтр, 7 = громкость)
    start_val,        # int — значение CC в начале sweep
    end_val,          # int — значение CC в конце sweep
    start_beat,       # float
    end_beat,         # float
    curve_type="exponential",  # "linear" | "exponential" | "sine"
    exponent=2.0,
    steps=20,
)
```

Генерирует кривую автоматизации через `AutomationCurve` и добавляет её в `cc_events[track_name]`.

**Когда использовать**: нарастание/спад фильтра перед хорусом, volume swell, vibrato LFO.

---

### apply_lead_in_fill

```python
TransitionCoordinator.apply_lead_in_fill(
    tracks,        # dict
    target_track,  # str — имя трека
    fill_notes,    # list[NoteInfo] — ноты fill (с start=0.0)
    start_beat,    # float — граница секции
)
```

- Все ноты трека `target_track` с `start >= start_beat` **заменяются** на `fill_notes`.
- Ноты fill автоматически сдвигаются к `start_beat`.

**Когда использовать**: барабанный ролл перед хорусом, мелодическая сбивка в скрипке.

---

### orchestrate_transition

```python
TransitionCoordinator.orchestrate_transition(
    tracks,
    cc_events,
    boundary_beat=32.0,       # где начинается новая секция
    pre_duration=4.0,         # сколько бит до границы — зона дакинга/свипа
    post_duration=2.0,        # зарезервировано (для будущих пост-эффектов)

    # Дакинг
    duck_tracks=["bass", "kick"],
    duck_factor=0.0,

    # CC свип
    sweep_tracks=["pad", "strings"],
    sweep_cc=74,
    sweep_start_val=40,
    sweep_end_val=110,
    sweep_curve="exponential",

    # Лид-ин филл
    fill_track="violin",
    fill_notes=[...],
)
```

**Единственный вызов** вместо трёх отдельных.
Временное окно дакинга и свипа: `[boundary_beat - pre_duration, boundary_beat]`.

#### Пример — переход из Verse в Chorus:

```python
cc_events = {}
fill = [NoteInfo(pitch=72, start=0.0, duration=0.5, velocity=100),
        NoteInfo(pitch=74, start=0.5, duration=0.5, velocity=100)]

TransitionCoordinator.orchestrate_transition(
    tracks=tracks, cc_events=cc_events,
    boundary_beat=64.0, pre_duration=4.0,
    duck_tracks=["bass"],         duck_factor=0.0,
    sweep_tracks=["pad"],         sweep_cc=74, sweep_start_val=30, sweep_end_val=100,
    fill_track="violin",          fill_notes=fill,
)
```

---

## ModulationEngine

**Файл**: `melodica/theory/modulation.py`

```python
from melodica.types import ModulationEngine, Scale, Mode
```

---

### generate_modulation_bridge

```python
chords = ModulationEngine.generate_modulation_bridge(
    from_scale=Scale(root=0,  mode=Mode.MAJOR),       # C Major
    to_scale=Scale(root=11, mode=Mode.PHRYGIAN),      # B Phrygian
    length_beats=8.0,                                  # суммарная длина моста
    strategy="dominant",                               # "pivot" | "dominant" | "chromatic"
    start_beat=96.0,                                   # смещение в timeline
)
# → list[ChordLabel], всегда 4 аккорда с равными длительностями
```

Возвращает **4 ChordLabel** с корректными `start` и `duration`, готовые к вставке в прогрессию.

---

### Стратегии

| Стратегия | Принцип | Характер |
|---|---|---|
| `"pivot"` | Ищет общий аккорд в обоих ладах; строит разрешение через него | Плавный, академический |
| `"dominant"` | V7/V нового ключа → V7 нового ключа → I | Напряжённый, кинематографический |
| `"chromatic"` | ♭II7 (тритоновая замена) → V7 → I | Тёмный, chromatic jazz |

#### dominant — как считается:

```
to_scale = B Phrygian  (root=11)
V степень = F# (= degrees()[4] = 6)
V/V       = C# (+7 semitones) → root=1
bridge: I(C Major) → C#7 → F#7 → Bm
```

---

## compile_continuous_album

**Файл**: `melodica/composer/album_pipeline.py`

```python
from melodica.composer.album_pipeline import compile_continuous_album, Mood
```

---

### Параметры

```python
report = compile_continuous_album(
    tracks_metadata=[meta_i, meta_ii, meta_iii, ...],
    output_path="output/album/Album_Continuous.mid",

    overlap_beats=8.0,              # зона нахлёста/кроссфейда между треками
    mood=Mood.CHAMBER,              # пресет микса/мастеринга

    modulation_strategy="dominant", # None | "pivot" | "dominant" | "chromatic"
    transition_instrument=89,       # GM программа для bridge pad (89 = Warm Pad)
)
```

### Формат элемента `tracks_metadata`

```python
meta = {
    "tracks":       {"violin": [...], "pad": [...], "bass": [...]},  # dict[str, list[NoteInfo]]
    "bpm":          72.0,
    "instruments":  {"violin": 40, "pad": 89, "bass": 32},           # GM программы
    "cc_events":    {"violin": [(0.0, 11, 80), ...]},                 # опционально
    "tempo_events": [(0.0, 72.0), (32.0, 85.0)],                     # опционально
    "key":          Scale(root=11, mode=Mode.HUNGARIAN_MINOR),        # обязательно для модуляции
}
```

> [!IMPORTANT]
> `"key"` должен быть заполнен во всех мета-словарях, если нужна автоматическая модуляция.
> Без `"key"` bridge не генерируется даже при заданной стратегии.

---

### Автоматический transition_pad

При смене тональности между треками `N` и `N+1`:

```
overlap_start = текущий сдвиг timeline (начало зоны нахлёста)
overlap_end   = overlap_start + overlap_beats

1. ModulationEngine.generate_modulation_bridge(...)
   → 4 ChordLabel в [overlap_start, overlap_end]

2. Каждый аккорд → ноты (root + 3rd + 5th) на C3 регистре
   velocity = 55 (мягко, фоново)

3. Трек "transition_pad" добавляется в combined_tracks
   instrument = transition_instrument (GM 89 по умолчанию)

4. CC автоматизация:
   • CC 7:  0 → 80 → 0  (hat-shape: появляется и уходит)
   • CC 74: 35 → 95     (фильтр открывается — тепло входит)
```

---

### Схема обработки

```
tracks_metadata[0]  tracks_metadata[1]  tracks_metadata[2]
     |                    |                    |
     v                    v                    v
 shift+copy           shift+copy           shift+copy
     |                    |                    |
     |    overlap_0        |    overlap_1        |
     |<====8 beats====>|   |<====8 beats====>|   |
     |  fade-out CC7   |   |  fade-out CC7   |   |
     |                 |   |  fade-in  CC7   |   |
     |                 |   |  bridge pad     |   |
     |                 |   |   (если разные  |   |
     |                 |   |    ключи)       |   |
     v                 v   v                 v   v
              produce_track(combined) → .mid
```

---

## Готовый пример: Дракула Глава IV

**Скрипт**: [`scripts/album_dracula_ch4_continuous.py`](../scripts/album_dracula_ch4_continuous.py)

```
python3 scripts/album_dracula_ch4_continuous.py
```

Компилирует 5 частей (~20 мин) в один файл:
```
output/album_dracula_ch4/Dracula_Chapter_IV_Continuous.mid
```

Переходы:
```
I  → II  : B Hungarian Minor → B Hungarian Minor  (кроссфейд без моста)
II → III : B Hungarian Minor → B Phrygian         ← dominant bridge
III→ IV  : B Phrygian → B Hungarian Minor         ← dominant bridge
IV → V   : B Hungarian Minor → B Phrygian         ← dominant bridge
```

---

## Шаблон нового альбома

```python
# my_album_continuous.py

from pathlib import Path
from melodica import types
from melodica.generators.melody import MelodyGenerator
from melodica.generators import GeneratorParams
from melodica.composer.album_pipeline import compile_continuous_album, Mood
from melodica.composer.transition_coordinator import TransitionCoordinator
from melodica.composer.automation import AutomationCurve

KEY_A = types.Scale(root=0,  mode=types.Mode.MAJOR)
KEY_B = types.Scale(root=9,  mode=types.Mode.NATURAL_MINOR)

def build_track_1() -> dict:
    bpm, dur = 90, 64.0
    chords = [...]  # parse_progression(...)
    notes = MelodyGenerator(GeneratorParams(...)).render(chords, KEY_A, dur)
    return {
        "tracks": {"lead": notes},
        "bpm": bpm,
        "instruments": {"lead": 73},
        "cc_events": {},
        "key": KEY_A,
    }

def build_track_2() -> dict:
    ...
    return {"tracks": ..., "bpm": ..., "instruments": ..., "key": KEY_B}

if __name__ == "__main__":
    report = compile_continuous_album(
        tracks_metadata=[build_track_1(), build_track_2()],
        output_path=Path("output/my_album/Continuous.mid"),
        overlap_beats=8.0,
        mood=Mood.CINEMATIC,
        modulation_strategy="dominant",   # или "pivot" / "chromatic" / None
        transition_instrument=89,
    )
    print(report["profiles"])
```

### Рекомендации по стратегии

| Жанр | Рекомендуемая стратегия |
|---|---|
| Готика / оркестр / dark ambient | `"dominant"` |
| Классика / академическая музыка | `"pivot"` |
| Jazz / noir / neo-soul | `"chromatic"` |
| Без смены тональности | `None` |

### Рекомендации по `overlap_beats`

| Tempo / характер | `overlap_beats` |
|---|---|
| Быстрый (>120 BPM) | `4.0` |
| Средний (80–120 BPM) | `8.0` |
| Медленный (<80 BPM) | `12.0–16.0` |
| Cinematic / ambient | `16.0–32.0` |
