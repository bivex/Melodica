# Melodica — Feature Priorities

Приоритет по соотношению: музыкальная ценность / сложность реализации.
Последнее обновление: 2026-06-12

---

## P4 — Новые задачи (из анализа музыкальных форм)

### 11. FormTemplate — enum + генератор IdeaPart последовательностей
Wikipedia: sonata, rondo, ternary, through-composed — стандартные формы.
- `FormTemplate` enum: SONATA, RONDO, TERNARY, THROUGH_COMPOSED, VARIATIONS, BINARY
- `form_plan(template, scale, n_bars)` → list[IdeaPart] с правильными SectionRole и Scale
- Sonata: P(tonic)→T→S(dominant)→Development(unstable)→Recapitulation(tonic)
- Rondo: ABACABA с тональной схемой I-V-I-VI-I-I-I
- Through-composed: каждый IdeaPart с уникальным material, нет повторов

### 12. SonataFormPlan — конкретный план с P/T/S/C зонами
Wikipedia: exposition зоны P, T, S, C с конкретными гармоническими функциями.
- `SonataFormPlan(scale, n_bars)` → IdeaPart список
- P-zone: tonic, main theme density high
- T-zone: modulating, bridge к dominant
- S-zone: dominant (major) / relative major (minor), lyrical
- C-zone: cadential, reinforces new key
- Development: нестабильная тональность, фрагментация тем через ModulationEngine
- Recapitulation: всё в tonic, S-zone транспонируется назад

### 13. variation_of поле в IdeaPart + VariationPlan
Wikipedia: variation form — melodic/rhythmic/harmonic/minor-mode.
- `variation_of: str | None` в IdeaPart (ссылка на исходный IdeaPart по имени)
- `VariationPlan` — генерирует серию вариаций из одного IdeaPart
- Типы: melodic (SchenkerianElaborator), rhythmic (другой ритм-пресет), harmonic (реharmonization), modal (параллельный минор/мажор), reductive (_thin)

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
