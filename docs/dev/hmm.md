релевантные бумаги для улучшения FunctionalHMMHarmonizer:

  #: 1
  Paper: Melody Harmonization with Orderless NADE
  ID: 2010.13468
  Что улучшает: Phase 2 (Chord Selection) — Gibbs sampling вместо greedy
    pick. Block-by-block перебор → больше variety, лучше
  "interestingness".
     Бьет MTHarmonizer по 5/6 метрик.
  ────────────────────────────────────────
  #: 2
  Paper: SurpriseNet
  ID: 2108.00378
  Что улучшает: Phase 1 (Functional Plan) — surprise contour (entropy over

    time) как управляющий сигнал. Твоя tension curve уже есть, но surprise

    = информационная неожиданность, а не просто tension. Марковская
    энтропия переходов как proxy.
  ────────────────────────────────────────
  #: 3
  Paper: Spiral Array Tension (VAE)
  ID: 2010.06230 + 1910.02049
  Что улучшает: Phase 1 + Scoring — Spiral Array вместо твоей
  TensionCurve.
     Midi Miner библиотека считает 3 меры тонального напряжения  (cloud
    diameter, cloud momentum, tensile strain). Математически обосновано,
    лучше коррелирует с восприятием.
  ────────────────────────────────────────
  #: 4
  Paper: Tonal Tension in Piano Performance
  ID: 1807.01080
  Что улучшает: _score_progression — показывает что тональное напряжение
    предсказывает expressive dynamics/tempo. Можно добавить в скоринг
    candidate quality.
  ────────────────────────────────────────
  #: 5
  Paper: AutoHarmonizer
  ID: 2112.11122
  Что улучшает: Phase 2 — controllable harmonic density (как часто
  меняются
     аккорды). 1,462 типа аккордов. У тебя chord_change="bars"
    фиксированный — они дают гибкий harmonic rhythm.
  ────────────────────────────────────────
  #: 6
  Paper: Comparative Study of Melody Harmonization
  ID: 2001.02360
  Что улучшает: Архитектурный обзор — сравнивает template matching, HMM,
    genetic algorithm, deep learning. 9,226 melody/chord пар, 48 triads,
    объективные метрики + субъективное тестирование с 202 участниками.
    HMM-based подход — один из canonical baselines.
  ────────────────────────────────────────
  #: 7
  Paper: Explicit Tonal Tension via Dual-Level Beam Search
  ID: 2511.19342
  Что улучшает: Phase 2 (Selection) + Phase 4 (Scoring) — dual-level beam
    search: token-level re-ranking (quality+diversity) + bar-level tension

    re-ranking. Можно заменить твой n_candidates=8 + random noise на
    structured beam search.
  ────────────────────────────────────────
  #: 8
  Paper: Cadence Detection with GNN
  ID: 2208.14819
  Что улучшает: Phase 1 — graph neural network для cadence detection. Твои

    cadence_positions эвристические (i+1 % 4 == 0) — GNN может
  обнаруживать
     каденции структурно.

  Топ-3 по impact/effort для твоего кода:

  1. SurpriseNet (entropy-based surprise contour) — легко добавить в
  _score_progression, даёт объективную меру "interestingness" вместо
  random noise
  2. Spiral Array / Midi Miner — заменить/дополнить TensionCurve
  математически обоснованной моделью
  3. Dual-Level Beam Search — заменить n_candidates=8 с random noise на
  structured search с quality+tension re-ranking