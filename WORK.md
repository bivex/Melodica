# Melodica Architectural Audit — 2026-05-29

Full codebase audit: ~98K LOC, 326 files, 203 generators.

---

## CRITICAL (4)

### 1. PhraseInstance.render() passes wrong type as `key`
**File**: `melodica/types_pkg/_phrases.py:94`
`self.timeline` (MusicTimeline) is passed as `key` to `generator.render()` which expects `Scale`. Every PhraseInstance in the system is broken.

### 2. ~~49 of 68 referenced rhythm presets don't exist~~ **FIXED**
**File**: `melodica/rhythm/library.py`
`get_rhythm()` silently falls back to `straight_quarters` on KeyError (stderr only). Japanese albums (album_kage.py etc.) are most affected — all tracks get straight_quarters instead of taiko/shamisen patterns.

**Fix applied** (2026-05-29):
- 10 new JSON preset files created (half_note, ambient, drone, 7 dark_souls/, 1 japanese/)
- 20 short-name aliases added in library.py (gavotte→cls_gavotte_2_2, etc.)
- 3 dynamic presets registered: `markov:slow`, `markov:dirge`, `arpeggio:slow`
- Library now has 432 entries, 10 dynamic presets
- Verified: album_apocalyptus.py and album_fallen_empire.py run successfully

### 3. SECTION_ENERGY aliased, not copied
**File**: `melodica/types.py:95`
`SECTION_ENERGY = SECTION_ROLE_ENERGY` is a reference assignment. Mutating one dict mutates the other.

### 4. channel_active_events overwrite bug
**File**: `melodica/midi.py:747, 1128`
`export_multitrack_midi` and `export_midi` both overwrite the `channel_active_events` dict on each track iteration, losing state.

---

## HIGH (6)

### 5. ~~18 generators with silent dispatch failures~~ **FIXED**
If/elif chains without else/validation on variant/style/pattern params. Invalid values produce 0 notes with no error.

**Fix applied** (2026-05-29): Added `else: raise ValueError(...)` in 10 files, 11 locations:
- `nebula.py` (variant), `brass_section.py` (articulation), `supersaw_pad.py` (variant)
- `fx_riser.py` (riser_type), `fx_impact.py` (impact_type), `horror_dissonance.py` (variant)
- `beat_repeat.py` (repeat_type), `four_on_floor.py` (variant), `bend.py` (bend_type)
- `ethnic_world.py` (instrument, 2 locations: __init__ + render)
- 8 generators already clean: dark_bass, harp, drum_kit_pattern, tremolo_strings, reggae_skank, choir_ahhs, humanizer, electronic_drums

### 6. export_multitrack_midi / export_midi duplication
~235 lines of duplicated code between the two functions. Divergence bugs are inevitable.

### 7. GM_INSTRUMENTS vs FLUID_R3_PROGRAMS divergence
`midi.py` GM_INSTRUMENTS: organ=19. `fluid_r3_profile.py` FLUID_R3_PROGRAMS: organ=16. Albums using FLUID_R3 get different instruments than expected.

### 8. STYLE_INSTRUMENTS dead code
**File**: `melodica/midi.py:127-170`
Defined but never referenced anywhere.

### 9. MixingDesk.niche_cfg dead code
**File**: `melodica/shorts_mixing.py`
`niche_cfg` is stored in `__init__` but never read by any method.

### 10. NoteInfo has no velocity validation
**File**: `melodica/types_pkg/_notes.py`
Unlike `Note` (which validates 0-127), `NoteInfo` accepts any int. Velocities >127 are passed to MIDI unchanged, causing undefined behavior in some DAWs.

---

## MEDIUM (5)

### 11. electronic_drums.py: 112 lines unreachable dead code
**File**: `melodica/generators/electronic_drums.py`
After `return notes` at line 757, lines 758-870 are dead code. Also: `groove_template: any` (lowercase) at lines 292, 327.

### 12. MasteringDesk.quality_report() never called
**File**: `melodica/shorts_mastering.py`
Method exists but no caller in the codebase.

### 13. Mixing fade is linear, not exponential
**File**: `melodica/shorts_mixing.py`
Docstring says "exponential fade" but implementation is linear interpolation.

### 14. Velocity caps inconsistent
- MixingDesk caps at 120
- MasteringDesk caps at 125
- MIDI spec max is 127
Three different ceilings across the pipeline.

### 15. get_rhythm() fallback is silent
**File**: `melodica/rhythm/library.py`
Falls back to `straight_quarters` with only a stderr print. Should log.warning or raise.

---

## LOW (9+)

### 16-24. Minor issues
- ChordLabel quality has 30 types but no validation on construction
- RhythmEvent is frozen but RhythmEvent.onset can be negative
- Scale.__eq__ missing (can't compare two scales)
- ArpeggiatorGenerator pattern="down" doesn't reverse note order correctly in all voicings
- StringsEnsembleGenerator divisi > section_size silently clips
- BassGenerator walking style ignores chord extensions
- DroneGenerator variant="pedal" has hardcoded pitch 36 (too low for some instruments)
- ChordGenerator voicing="spread" has no max interval limit
- MelodyGenerator motif_variation="invert" inverts relative to first note, not key center

---

## Album Bug Fixes Applied (album_apocalyptus.py)

9 bugs found, 9 fixed:
1. `comp_style="ballad"` → `"waltz"` (BrassSectionGenerator)
2. `voicing_type="open"` → `"shell"` (ChordGenerator)
3. `variant="dark"/"shimmer"` → `"stasis"/"cascade"` (NebulaGenerator)
4. `articulation` fixes (BrassSectionGenerator)
5. `variant="epic"` → `"trance"` (SupersawPadGenerator, 3 locations)
6. `pattern="aggressive"` → `"breakbeat"` (ElectronicDrumsGenerator, 4 locations)
7. `style="metal"` → `"rock"` (DrumKitPatternGenerator, 2 locations)
8. `syllable="ah"` → `"aah"` (ChoirAahsGenerator, 4 locations)
9. **FIXED**: `voice_count=8/12/16` → `4` (ChoirAahsGenerator, 4 locations — lines 201, 405, 678, and one more)

---

## Recommendations

1. **Immediate**: Fix PhraseInstance.render() key type (affects all phrase-based composition)
2. ~~**Immediate**: Audit and create missing rhythm presets~~ **DONE** (aliases + 10 JSON + 3 dynamic)
3. ~~**Short-term**: Add validation in generator __init__ for variant/style/pattern params~~ **DONE** (10 files)
4. **Short-term**: Deduplicate export_multitrack_midi / export_midi
5. **Medium-term**: Unify velocity caps across pipeline
6. **Medium-term**: Add NoteInfo velocity validation
7. **Long-term**: Replace get_rhythm() silent fallback with explicit error
