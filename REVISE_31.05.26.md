# Melodica — Composer's Revision Notes

**Date:** 31.05.2026
**Context:** After writing two full albums (20-track orchestral "Sixty-Six Days" + 7-track ambient "Blood of Dawnwalker"), evaluating the framework from a composer's perspective.

---

## Critical — without these, the composer stumbles

### 1. Thematic Development (Motivic Transformation)
No way to define a motif and develop it: inversion, retrograde, augmentation, diminution, sequence, fragmentation. Every generator is one-shot right now. A composer thinks in motifs. One motif → 20 variations → cohesive album.

### 2. Tempo Mapping
Fixed BPM per track. No ritardando, accelerando, rubato, fermata. Music lives in agogic accents — slowing before a cadence, accelerating at climax. Without this, everything sounds mechanical.

### 3. Dynamic Automation
`_clamp` and `_expr_swell` are manual workarounds. No envelope system: "crescendo from bar 8 to bar 16, subito piano, then gradual diminuendo." Need automation lanes — velocity curves over time, not per-note manual editing.

---

## Important — expands expressiveness

### 4. Transitions & Cadences
No generator for transitions between sections. Bridge, fill, turnaround, perfect/imperfect cadence, deceptive cadence — all manual. Transitions are where music breathes.

### 5. Percussion — Poor
Only timpani and snare. Missing: cymbals (crash, ride, suspended), bass drum, tam-tam, gong, triangle, glockenspiel, marimba, vibraphone, xylophone, castanets, whip. Percussion palette is the composer's color palette.

### 6. Form / Structure
No ABA, rondo, sonata, through-composed, strophic form. Every track is manual assembly. A formal template system: "sonata form in D minor, exposition 32 beats, development 24, recapitulation 32" — generators fill the sections.

### 7. Motivic Recurrence (Leitmotif System)
Define a theme → it can appear in any track, any voice, any transformation. Wagner-style. For concept albums this is a must-have.

---

## Nice to Have — for fine work

### 8. Voice-Leading Rules
No rules for "outer voices contrary motion preferred", "avoid parallel fifths", "smooth voice leading between chords". There is a counterpoint generator, but no rules engine.

### 9. Articulation Palette
No staccatissimo, tenuto, accent, sforzando, portato (col legno exists for Cello, but not systematically). Currently mostly legato vs staccato binary.

### 10. Microtonality / Alternate Tunings
No quarter tones, just intonation, meantone. For non-European music (Arabic, Indian, Turkish material) this is a wall.

### 11. Aleatoric / Indeterminate
No chance operations, cluster notation, "repeat ad lib", graphic score interpretation. Contemporary orchestral music without this is not contemporary.

### 12. Orchestration Rules Engine
No "contrabassoon shouldn't go above F3", "French horn in closed position shouldn't play above C5", "flute in low register is breathy and quiet". Instrumentation knowledge as rules.

---

## Summary

**Tempo mapping**, **motivic development**, and **dynamic automation** are what would transform Melodica from a "note generator over progressions" into a "composer's instrument". Right now it's like a piano roll without expression — the notes are there, but the music barely breathes.
