# TZ: Orchestral Arranger System

## Цель
Построить систему многослойной оркестровой аранжировки,
способную генерировать 5–15-минутные симфонические партии
с формой, динамическими дугами, оркестровым балансом
и структурной связностью между голосами.

## Контекст
Текущие генераторы рендерят каждый отдельно, вслепую.
При написании альбома "Symphonia Obscura" выяснилось:
- Solo-генераторы (Violin, Cello, Oboe) дают 5-10 нот на минуту
- Нет понятия формы (ABA, сонатная, рондо)
- Нет macro-динамики (pp → ff → pp на уровне всей пьесы)
- Генераторы не знают про друг друга — нет tutti/solo/sezione
- Нет tempo map (accel, rit, fermata)

## Архитектура

### 1. MusicalForm (новый модуль: `melodica/form.py`)

Определяет структуру пьесы как последовательность секций.

```python
@dataclass
class FormSection:
    name: str               # "intro", "exposition", "development", "recapitulation", "coda"
    start_beat: float
    duration_beats: float
    dynamics: str           # "pp", "p", "mp", "mf", "f", "ff"
    tempo_multiplier: float # 1.0 = normal, 0.75 = slower, 1.25 = faster
    active_families: list[str]  # ["strings", "brass", "woodwinds", "percussion", "choir"]
    mood: str               # "tense", "lyrical", "triumphant", "mournful", "ethereal"
    repeat_id: str | None   # для ABA: "A", "B" — повторяющиеся секции

@dataclass
class MusicalForm:
    sections: list[FormSection]
    tempo_map: list[tuple[float, float]]  # [(beat, bpm), ...] — tempo changes

    @staticmethod
    def sonata(key: Scale, duration_beats: float) -> MusicalForm: ...
    @staticmethod
    def ternary(key: Scale, duration_beats: float) -> MusicalForm: ...  # ABA
    @staticmethod
    def rondo(key: Scale, duration_beats: float) -> MusicalForm: ...    # ABACA
    @staticmethod
    def through_composed(key: Scale, duration_beats: float) -> MusicalForm: ...
```

**Что делает:**
- Разбивает duration_beats на секции с пропорциями
- Sonata: exposition(30%) → development(35%) → recapitulation(25%) → coda(10%)
- Ternary: A(40%) → B(30%) → A'(30%)
- Каждая секция знает какие семейства инструментов активны
- tempo_map генерирует плавные accel/rit между секциями

### 2. DynamicsArc (новый модуль: `melodica/dynamics_arc.py`)

Управляет macro-динамикой поверх формы.

```python
@dataclass
class DynamicsArc:
    """Динамическая кривая на уровне всей пьесы."""
    curve_type: str  # "crescendo", "diminuendo", "swell", "terraced", "custom"
    sections: list[tuple[float, float, float]]  # [(start_beat, end_beat, velocity_multiplier)]

    def velocity_at(self, beat: float) -> float:
        """Возвращает множитель velocity (0.0–1.0) для данного момента."""

    @staticmethod
    def from_form(form: MusicalForm) -> DynamicsArc: ...
```

**Логика:**
- Каждая секция формы имеет dynamics-метку (pp–ff)
- DynamicsArc интерполирует между ними
- `from_form()` создаёт плавную кривую:
  - intro: pp → p
  - exposition: p → mf
  - development: mf → f → mf (драматическая дуга)
  - recapitulation: mf → f
  - coda: f → ff → dim → p (если кода тихая)

### 3. Orchestrator (новый модуль: `melodica/orchestrator.py`)

Центральный координатор. Знает КАКИЕ инструменты играют КОГДА и КАК.

```python
@dataclass
class OrchestralLayer:
    name: str                    # "violins", "horns", "choir", ...
    generator: PhraseGenerator
    family: str                  # "strings", "brass", "woodwinds", "percussion", "choir"
    role: str                    # "melody", "harmony", "bass", "rhythm", "pad", "solo"
    density_curve: str           # "constant", "sparse_to_dense", "dense_to_sparse"
    default_params: dict         # параметры генератора для секции

@dataclass
class Orchestrator:
    layers: list[OrchestralLayer]
    form: MusicalForm
    dynamics: DynamicsArc

    def render(self, chords: list[ChordLabel], key: Scale,
               duration_beats: float) -> dict[str, list[NoteInfo]]:
        """Рендерит все слои, учитывая форму и динамику."""

    def _active_layers(self, section: FormSection) -> list[OrchestralLayer]:
        """Возвращает слои, активные в данной секции."""

    def _apply_section_dynamics(self, notes: list[NoteInfo],
                                section: FormSection) -> list[NoteInfo]:
        """Масштабирует velocity по динамике секции и macro-arc."""

    def _apply_density_curve(self, layer: OrchestralLayer,
                             section: FormSection) -> GeneratorParams:
        """Модифицирует density params в зависимости от секции и роли."""
```

**Ключевая логика render():**

```
for section in form.sections:
    active = _active_layers(section)
    section_chords = chords_in_section(chords, section)

    for layer in active:
        params = _apply_density_curve(layer, section)
        notes = layer.generator.render(section_chords, key, section.duration_beats)

        # Сдвигаем onset на start_beat секции
        offset_notes(notes, section.start_beat)

        # Применяем macro-динамику
        _apply_section_dynamics(notes, section)

        # Применяем tempo multiplier (растягивает/сжимает time)
        _apply_tempo(notes, section.tempo_multiplier)

        accumulate into tracks[layer.name]

return tracks
```

### 4. Улучшение solo-генераторов (правки в существующих файлах)

**Проблема:** Solo-генераторы (Violin, Cello, Oboe, Flute, etc.)
дают 5-10 нот на минуту. Для аранжировки нужно 40-80.

**Решение:** Добавить параметр `note_density` в `_OrchestralStringBase`,
`_OrchestralWoodwindBase`, `_OrchestralBrassBase`:

```python
# В orchestral_strings.py, orchestral_woodwinds.py, orchestral_brass.py
note_density: float = 1.0  # 0.5 = разреженно, 2.0 = вдвое плотнее
```

Логика: `note_density` умножает количество rhythm events.
Если `note_density=2.0` и rhythm даёт 4 события — рендерим 8,
размещая дополнительные между основными.

### 5. EnsembleMode (в существующие генераторы)

Для секций tutti/solo/chamber:

```python
# В StringsLegatoGenerator, BrassSectionGenerator, WoodwindsEnsembleGenerator
ensemble_mode: str = "full"  # "solo", "chamber" (3-4), "section" (8-12), "tutti" (full)
```

- `solo`: 1 голос, expressivo, rubato timing
- `chamber`: 2-3 голоса, лёгкая расстройка
- `section`: 4-8 голоса, divisi
- `tutti`: полная секция с удвоениями

## Зависимости между задачами

```
[1] MusicalForm ─────┐
                     ├──> [3] Orchestrator ──> [5] EnsembleMode
[2] DynamicsArc ─────┘           │
                                │
                     [4] Solo density fix
```

## Файлы для создания/изменения

| Файл | Действие |
|---|---|
| `melodica/form.py` | СОЗДАТЬ — MusicalForm, FormSection |
| `melodica/dynamics_arc.py` | СОЗДАТЬ — DynamicsArc |
| `melodica/orchestrator.py` | СОЗДАТЬ — Orchestrator, OrchestralLayer |
| `melodica/generators/orchestral_strings.py` | ИЗМЕНИТЬ — note_density param |
| `melodica/generators/orchestral_woodwinds.py` | ИЗМЕНИТЬ — note_density param |
| `melodica/generators/orchestral_brass.py` | ИЗМЕНИТЬ — note_density param |
| `melodica/generators/strings_legato.py` | ИЗМЕНИТЬ — ensemble_mode param |
| `melodica/generators/brass_section.py` | ИЗМЕНИТЬ — ensemble_mode param |
| `melodica/generators/woodwinds_ensemble.py` | ИЗМЕНИТЬ — ensemble_mode param |
| `tests/test_form.py` | СОЗДАТЬ |
| `tests/test_dynamics_arc.py` | СОЗДАТЬ |
| `tests/test_orchestrator.py` | СОЗДАТЬ |
| `scripts/demo_orchestrator.py` | СОЗДАТЬ — демо аранжировка |

## Критерии приёмки

1. **Form** — `MusicalForm.sonata(key, 240)` возвращает 4+ секции
   с корректными start_beat/duration_beats, темповыми множителями
2. **DynamicsArc** — `velocity_at(beat)` возвращает 0.0-1.0,
   плавно интерполирует между секциями, ≈pp=0.2, ff=1.0
3. **Orchestrator** — с 6 слоями на 240 beats генерирует
   >2000 нот на слой в "tutti" секции, >0 в "solo" секции,
   velocity следует form dynamics ±10%
4. **Solo density** — ViolinGenerator с `note_density=2.0`
   даёт ≥2x нот относительно `note_density=1.0`
5. **Ensemble mode** — `ensemble_mode="tutti"` даёт больше голосов
   чем `ensemble_mode="solo"` на том же генераторе
6. **Все существующие тесты** — не ломаются
7. **Демо** — `demo_orchestrator.py` генерирует 3-минутную
   сонатную форму с 4+ слоями, файл >20KB MIDI

## Приоритет реализации

| Приоритет | Задача | Сложность | Влияние |
|---|---|---|---|
| P0 | [4] Solo density fix | низкая | решает главную проблему разреженности |
| P0 | [1] MusicalForm | средняя | основа всей структуры |
| P1 | [2] DynamicsArc | низкая | macro-динамика |
| P1 | [3] Orchestrator | высокая | центральная координация |
| P2 | [5] EnsembleMode | средняя | tutti/solo/chamber |
