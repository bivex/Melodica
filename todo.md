# Melodica — Feature Priorities

Приоритет по соотношению: музыкальная ценность / сложность реализации.
Последнее обновление: 2026-06-12

---

## P4 — Новые задачи (из анализа музыкальных форм)

### 11. FormTemplate — enum + генератор IdeaPart последовательностей ✓
### 12. SonataFormPlan — конкретный план с P/T/S/C зонами ✓
### 13. variation_of поле в IdeaPart + VariationPlan ✓

---

## P5 — Новые задачи (из анализа контрапункта и оркестровки)

### 14. CanonGenerator — имитативный контрапункт
Источник: Wikipedia/Counterpoint — canon at the fifth/octave, N beats delay.
- Взять мелодию, сдвинуть на N beats, транспонировать на квинту/октаву вверх
- Поддержка 2-4 голосов (canon 2-in-1, 3-in-1)
- Интеграция с `voice_leading.py` — проверка параллельных квинт/октав

### 15. melodic_transforms() — диатонические трансформации мелодии
Источник: Wikipedia/Counterpoint — inversion, retrograde, augmentation, diminution.
- `melodic_inversion(notes, scale)` — зеркало интервалов в диатонике
- `melodic_retrograde(notes)` — обратный порядок нот
- `melodic_augmentation(notes, factor)` — умножить длительности
- `melodic_diminution(notes, factor)` — разделить длительности
- ToneRow (P/I/R/RI) уже есть для 12-tone — это диатоническая версия

### 16. AntiphonySectionBuilder — call-and-response координация
Источник: Wikipedia/Orchestration — antiphony between orchestral groups.
- Разделить IdeaToolConfig треки на группы (strings, winds, brass, perc)
- Генерировать чередующиеся фразы: group A играет bars 1-2, group B отвечает bars 3-4
- Поддержка перекрытия (overlap) и эха (echo delay)

### 17. ChordVoicingLayout — авто-раскладка аккорда по оркестровым группам
Источник: Wikipedia/Orchestration — cellos=root, violas=fifth, violins=third.
- `voice_chord(chord, instruments)` → dict[instrument → MIDI pitch]
- Правила: bass=root, inner voices=fifths/thirds, top=melody note
- Doubling hints: violins+glockenspiel=sparkling, piccolo+celesta=bright
- Интеграция с `functional_hmm.py` chord output

---

## P1 — ВЫПОЛНЕНО ✓

### 1. Модуляция между секциями ✓
- `IdeaPart.modulation_strategy` добавлен (pivot | dominant | chromatic)
- `modulation_bridge_notes()` и `apply_modulation_bridges()` в `theory/modulation.py`

### 2. Динамическая огибающая по форме ✓
- `tension_curve_to_envelope()` в `composer/velocity_envelope.py`
- Role-based компрессия: lead/pad/bass/perc профили

### 3. Мотивное развитие ✓
- `MotifDevelopmentPlan` в `composer/motif_plan.py`
- Привязка leitmotif к инструментам по форме, `.render()` → dict

---

## P2 — ВЫПОЛНЕНО ✓

### 4. Полиритмия как структурный элемент ✓
- `hemiola_layer()` и `polyrhythm_section()` в `generators/polyrhythm.py`

### 5. Schenkerian-style голосоведение ✓
- `passing_tones()`, `neighbour_tones()`, `elaborate()` в `composer/schenkerian.py`

### 6. Серийные техники ✓
- `ToneRow` + `ToneRowGenerator` в `generators/tone_row.py`
- P/I/R/RI трансформации, hexachord split, matrix

### 7. Расширенные tensions ✓
- `FunctionalHMMHarmonizer._quality_for_context` расширен
- I→MAJOR/MAJ7/ADD9, IV→MAJOR/ADD9/SUS2, V→DOM7/SUS4, vi→MINOR/MINOR7

---

## P3 — ВЫПОЛНЕНО ✓

### 8. Микротональность для струнных ✓
- `tension_scaled_inflections()` в `composer/microtonal_inflections.py`
- Leading-tone sharpening, colour-tone colouring, sustained drift по TensionCurve

### 9. Круг квинт навигатор ✓
- `CoFNavigator` в `composer/cof_navigator.py`
- `plan_album()`: cof_chain, cof_arch, enharmonic, dramatic
- Dim7/augmented enharmonic pivots

### 10. Euclidean rhythm generator ✓
- `EuclideanGenerator`, `TensionEuclidean` в `rhythm/euclidean.py`
- 16 named patterns (tresillo, bembé, aksak, etc.)
- TensionEuclidean: sparse↔dense по threshold

---

## Постоянно готово (не трогать)
- ModulationEngine (find_pivot_chords, generate_modulation_bridge)
- ARR-1/4/7/8 rules — чистые, album_virtuoso exit 0
- OstinatoGenerator beat-position accent
- voice_leading.py correct_parallels
- ContrabassGenerator LOW register tuning ~48% LOW
