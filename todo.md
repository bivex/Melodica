# Melodica — Feature Priorities

Приоритет по соотношению: музыкальная ценность / сложность реализации.

---

## P1 — Высокий приоритет (быстрая отдача)

### 1. Модуляция между секциями (IdeaPart → IdeaPart)
ModulationEngine уже готов и работает. Не хватает:
- Интеграция с `album_pipeline.py` — автоматический bridge на стыке частей с разными Scale
- Опция `modulation_strategy: pivot | dominant | chromatic` в TrackConfig/IdeaPart
- Pivot chord как последний аккорд предыдущей части (HMM constraint)

### 2. Динамическая огибающая по форме (tension_curve → velocity)
`tension_curve.py` и `velocity_envelope.py` уже есть, но не связаны с ARR-4 (LOW/MID/HIGH).
- Привязать tension peak к плотности регистра: crescendo = больше MID/HIGH нот
- Автоматический spill в intro/outro (ARR-7 variance уже есть)

### 3. Мотивное развитие (motif.py → развитие по форме)
`motif.py` и `leitmotif.py` есть. Не хватает:
- Трансформации: инверсия, ракоход, аугментация/диминуция ритма
- Привязка мотива к конкретному персонажу/инструменту на весь альбом

---

## P2 — Средний приоритет (значимо, но требует больше работы)

### 4. Полиритмия как структурный элемент (не только генератор)
`polyrhythm.py` существует, но изолирован.
- Интеграция с section_builder: 3-against-2 в переходных секциях
- Hemiola на стыке частей для метрической дестабилизации перед модуляцией

### 5. Schenkerian-style голосоведение (Ursatz)
На основе уже готового `voice_leading.py`:
- Детектировать структурные уровни (foreground / middleground)
- Генерировать passing tones и neighbour tones автоматически в мелодии

### 6. Серийные техники (tone row) для атональных секций
Базис — `types_pkg/_theory.py` уже знает о хроматической шкале.
- `ToneRowGenerator` — 12-tone row с трансформациями (P/I/R/RI)
- Полезно для horror/tension секций (horror_dissonance.py уже есть)

### 7. Функциональная гармония с расширенными tensions (jazz → orchestral)
`functional_hmm.py` + `reharmonization.py` уже есть.
- Добавить maj7, add9, sus2/sus4 как дополнительные состояния HMM
- Secondary dominant chains (ii-V-I в новой тональности)

---

## P3 — Низкий приоритет (интересно, но долго)

### 8. Микротональность в оркестровом контексте
`microtonal_melody.py` и `microtuning.py` есть.
- Quarter-tone inflections для струнных (expressive intonation)
- Привязать к tension_curve: высокое tension = больше микротональных отклонений

### 9. Круг квинт как навигатор модуляций
Автоматический план модуляций для альбома:
- Chain modulation по circle of fifths между треками
- Enharmonic reinterpretation для dim7/augmented chords

### 10. Ритмические пресеты → алгоритмическая генерация
`rhythm/presets/` имеет bossa nova, mazurka, reggae и др.
- Генерировать новые ритм-паттерны через Euclidean rhythm algorithm
- Адаптировать плотность под tension_curve (разреженный ритм = низкое tension)

---

## Уже реализовано (не трогать)
- ModulationEngine (find_pivot_chords, generate_modulation_bridge) — работает
- ARR-1/4/7/8 rules — чистые, album_virtuoso exit 0
- OstinatoGenerator beat-position accent — исправлено
- voice_leading.py correct_parallels — работает
- ContrabassGenerator LOW register tuning — ~48% LOW
