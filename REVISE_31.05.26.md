# Melodica — Composer's Revision Notes

**Date:** 31.05.2026
**Context:** After writing two full albums (20-track orchestral "Sixty-Six Days" + 7-track ambient "Blood of Dawnwalker"), evaluating the framework from a composer's perspective.

**Status updated:** 31.05.2026 — all 12 items implemented.

---

## Critical — without these, the composer stumbles

### 1. Thematic Development (Motivic Transformation) — DONE
`Motif` class in `melodica/composer/motif.py`: `.invert()`, `.retrograde()`, `.augment()`, `.diminish()`, `.fragment()`, `.sequence()`, `.transpose()`, `.develop()`. Chains of transforms for full motivic development. One motif → 20 variations → cohesive album.

### 2. Tempo Mapping — DONE
`TempoMap` in `melodica/composer/tempo_map.py`: per-beat tempo changes — ritardando, accelerando, rubato, fermata. Agogic accents via `(beat, bpm)` pairs.

### 3. Dynamic Automation — DONE
`VelocityEnvelope` in `melodica/composer/velocity_envelope.py`: automation lanes with crescendo, diminuendo, subito piano, swell curves over time. Replaces manual `_clamp` and `_expr_swell`.

---

## Important — expands expressiveness

### 4. Transitions & Cadences — DONE
`OrchestralTransitionGenerator` (7 types: crescendo_build, ritardando, accelerando, fermata, pedal_point, retransition, bridge_passage). `CadenceGenerator` (8 types: PAC, IAC, plagal, deceptive, half, backdoor, phrygian, neapolitan). `TransitionCoordinator` with `apply_ducking()`, `apply_sweeps()`, `orchestrate_transition()`.

### 5. Percussion — DONE
Unpitched: `BassDrumGenerator`, `TamTamGenerator`, `GongGenerator`, `TriangleGenerator`, `CastanetsGenerator`, `WhipSlapstickGenerator` in `melodica/generators/orchestral_unpitched_percussion.py`. Pitched: `CelestaGenerator`, `GlockenspielGenerator`, `MusicBoxGenerator`, `VibraphoneGenerator`, `MarimbaGenerator`, `XylophoneGenerator`, `DulcimerGenerator` in `melodica/generators/chromatic_percussion.py`. Plus existing `TimpaniGenerator`, `SnareDrumGenerator`, `OrchestralCymbalGenerator`, `TubularBellsGenerator`.

### 6. Form / Structure — DONE
`FormSection` + `MusicalForm` in `melodica/form.py`. Per-section dynamics, tempo multiplier, active instrument families, mood, and key modulation via `FormSection.key` + `MusicalForm.key_at(beat, fallback)`. Supports sonata, rondo, through-composed, ABA templates at the album-script level.

### 7. Motivic Recurrence (Leitmotif System) — DONE
`LeitmotifRegistry` in `melodica/composer/leitmotif.py`. Named motifs with semantic tags, default instrument/velocity/register. `render()` with transforms: transpose, invert, retrograde, augment, diminish, fragment, sequence. `render_all(tag=...)` for tag-based queries. Wagner-style leitmotif across an entire album.

---

## Nice to Have — for fine work

### 8. Voice-Leading Rules — DONE (pre-existing)
`VoiceLeadingEngine` in `melodica/composer/voice_leading.py`. SATB voice leading with parallel fifth/octave avoidance, contrary motion preference, smooth voice leading between chords.

### 9. Articulation Palette — DONE (pre-existing)
`ArticulationEngine` + `ArticulationProfile` in `melodica/composer/articulations.py`. Per-instrument articulation profiles: staccatissimo, tenuto, accent, sforzando, portato, col legno. MPE expression via `MPEEnvelope` in `melodica/expression_envelope.py` with per-note CC11/CC74/CC1/pitch_bend curves.

### 10. Microtonality / Alternate Tunings — DONE
`MicrotuningEngine` in `melodica/engines/microtuning.py`: `quantize_pitch()`, `snap_to_scale()`, `render_microtonal_note()`, `wrap_notes()`. Converts fractional MIDI pitches to integer NoteInfo with pitch_bend expression. `MicrotonalMelodyGenerator` in `melodica/generators/microtonal_melody.py` produces complete microtonal melodies. Supports `Mode.QUARTER_TONE_MINOR`, `Mode.ARABIC_SIKAH`, etc.

### 11. Aleatoric / Indeterminate — DONE
`AleatoricGenerator` in `melodica/generators/aleatoric.py` with 6 modes: `tone_cluster`, `chance_operations` (Cage), `repeat_ad_lib`, `graphic_score`, `pointillist` (Webern), `textural_cloud` (Xenakis). Density-controlled, reproducible via random seeds.

### 12. Orchestration Rules Engine — DONE
`OrchestrationRules` + `InstrumentRange` in `melodica/composer/orchestration_rules.py`. 30 orchestral instruments with min/max/comfortable ranges, register names, transposition. Methods: `validate()`, `clamp_to_range()`, `suggest_octave()`, `register_at()`, `blend_with()`.

---

## Summary

All 12 revision items have been implemented. The framework now covers motivic development, tempo mapping, dynamic automation, transitions/cadences, full percussion palette, formal structure with key modulation, leitmotif system, voice-leading, articulation with MPE, microtonality, aleatoric composition, and orchestration validation.
