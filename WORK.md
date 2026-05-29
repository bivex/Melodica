# Melodica Architectural Audit — 2026-05-29

Full codebase audit: ~98K LOC, 326 files, 203 generators.

## Fix Summary (2026-05-29)

| # | Issue | Status | Files |
|---|-------|--------|-------|
| 1 | PhraseInstance.render() wrong key type | FIXED | _phrases.py |
| 2 | 49 missing rhythm presets | FIXED | library.py + 10 JSON |
| 3 | SECTION_ENERGY aliased | FIXED | types.py |
| 4 | channel_active_events overwrite | FALSE POSITIVE | — |
| 5 | 18 generators no validation | FIXED | 10 files, 11 locations |
| 8 | STYLE_INSTRUMENTS dead code | FIXED | midi.py |
| 9 | niche_cfg dead code | FIXED | shorts_mixing.py |
| 10 | NoteInfo no velocity validation | FIXED | _notes.py |
| 11 | electronic_drums 112 lines dead code | FIXED | electronic_drums.py |
| 13 | Fade linear not exponential | FIXED | shorts_mixing.py |
| 14 | Velocity caps inconsistent | FIXED | shorts_mixing.py |

---

## CRITICAL (4)

### 1. ~~PhraseInstance.render() passes wrong type as `key`~~ **FIXED**
**File**: `melodica/types_pkg/_phrases.py:94`
`self.timeline` (MusicTimeline) is passed as `key` to `generator.render()` which expects `Scale`. Every PhraseInstance in the system is broken.

**Fix applied** (2026-05-29): Extract Scale via `timeline.get_key_at(0.0)` before passing to generator.

### 2. ~~49 of 68 referenced rhythm presets don't exist~~ **FIXED**
**File**: `melodica/rhythm/library.py`
`get_rhythm()` silently falls back to `straight_quarters` on KeyError (stderr only). Japanese albums (album_kage.py etc.) are most affected — all tracks get straight_quarters instead of taiko/shamisen patterns.

**Fix applied** (2026-05-29):
- 10 new JSON preset files created (half_note, ambient, drone, 7 dark_souls/, 1 japanese/)
- 20 short-name aliases added in library.py (gavotte→cls_gavotte_2_2, etc.)
- 3 dynamic presets registered: `markov:slow`, `markov:dirge`, `arpeggio:slow`
- Library now has 432 entries, 10 dynamic presets
- Verified: album_apocalyptus.py and album_fallen_empire.py run successfully

### 3. ~~SECTION_ENERGY aliased, not copied~~ **FIXED**
**File**: `melodica/types.py:95`
`SECTION_ENERGY = SECTION_ROLE_ENERGY` is a reference assignment. Mutating one dict mutates the other.

**Fix applied** (2026-05-29): Changed to `SECTION_ENERGY = dict(SECTION_ROLE_ENERGY)` (copy).

### 4. ~~channel_active_events overwrite bug~~ **FALSE POSITIVE**
**File**: `melodica/midi.py:747, 1128`
`export_multitrack_midi` and `export_midi` both overwrite the `channel_active_events` dict on each track iteration, losing state.

**Analysis** (2026-05-29): The overwrite is intentional. `channel_active_events` tracks the *current* active note per channel for voice stealing. Stolen note's events are already in `events` list with in-place modifications preserved. `channel_active_events` is initialized per-function, not shared across tracks.

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

### 8. ~~STYLE_INSTRUMENTS dead code~~ **FIXED**
**File**: `melodica/midi.py:127-170`
Defined but never referenced anywhere.

**Fix applied** (2026-05-29): Removed 44-line dead dict.

### 9. ~~MixingDesk.niche_cfg dead code~~ **FIXED**
**File**: `melodica/shorts_mixing.py`
`niche_cfg` is stored in `__init__` but never read by any method.

**Fix applied** (2026-05-29): Marked as deprecated, kept for backward compatibility (many callers pass it).

### 10. ~~NoteInfo has no velocity validation~~ **FIXED**
**File**: `melodica/types_pkg/_notes.py`
Unlike `Note` (which validates 0-127), `NoteInfo` accepts any int. Velocities >127 are passed to MIDI unchanged, causing undefined behavior in some DAWs.

**Fix applied** (2026-05-29): Added `if not (0 <= self.velocity <= 127): raise ValueError(...)` in `__post_init__`.

---

## MEDIUM (5)

### 11. ~~electronic_drums.py: 112 lines unreachable dead code~~ **FIXED**
**File**: `melodica/generators/electronic_drums.py`
After `return notes` at line 757, lines 758-870 are dead code. Also: `groove_template: any` (lowercase) at lines 292, 327.

**Fix applied** (2026-05-29): Removed 112 lines of dead code. Fixed `any` → `"GrooveTemplate | None"` with TYPE_CHECKING import.

### 12. MasteringDesk.quality_report() never called
**File**: `melodica/shorts_mastering.py`
Method exists but no caller in the codebase.

### 13. ~~Mixing fade is linear, not exponential~~ **FIXED**
**File**: `melodica/shorts_mixing.py`
Docstring says "exponential fade" but implementation is linear interpolation.

**Fix applied** (2026-05-29): Changed to `math.exp(-3.0 * pos_in_loop / fade_beats)` — true exponential decay.

### 14. ~~Velocity caps inconsistent~~ **FIXED**
- MixingDesk caps at 120
- MasteringDesk caps at 125
- MIDI spec max is 127
Three different ceilings across the pipeline.

**Fix applied** (2026-05-29): MixingDesk cap changed from 120 → 127 (MIDI spec max). MasteringDesk limiter at 125 is intentional headroom, left as-is.

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

1. ~~**Immediate**: Fix PhraseInstance.render() key type~~ **DONE** (extract Scale via get_key_at)
2. ~~**Immediate**: Audit and create missing rhythm presets~~ **DONE** (aliases + 10 JSON + 3 dynamic)
3. ~~**Short-term**: Add validation in generator __init__ for variant/style/pattern params~~ **DONE** (10 files)
4. **Short-term**: Deduplicate export_multitrack_midi / export_midi
5. ~~**Medium-term**: Unify velocity caps across pipeline~~ **DONE** (MixingDesk 120→127)
6. ~~**Medium-term**: Add NoteInfo velocity validation~~ **DONE** (0-127 check in __post_init__)
7. **Long-term**: Replace get_rhythm() silent fallback with explicit error

---

## MIDI Deep Audit (2026-05-29)

| # | Issue | Status | Files |
|---|-------|--------|-------|
| M1 | export_midi expression validation | FIXED | midi.py |
| M2 | NoteInfo.expression wrong type annotation | FIXED | _notes.py |
| M3 | FLUID_R3_PROGRAMS dead code | FALSE POSITIVE | 11 scripts import it |
| M4 | import random inside loop | FIXED | midi.py |
| M5 | STYLE_INSTRUMENTS ImportError | FIXED | midi.py |
| M6 | virtual_midi drops pitch_bend + crashes on list CC | FIXED | virtual_midi.py |
| M7 | Voice stealing consecutive-steal bug | LATENT | midi.py (deferred) |
| M8 | Double humanization | DESIGN | callers (deferred) |

### M1. ~~export_midi expression validation~~ **FIXED**
**File**: `melodica/midi.py:1040-1058`
`export_midi` had no `isinstance(cc_num, int)` guard — if expression had a string key other than "pitch_bend", it would pass garbage to mido.

**Fix**: Reordered to match `export_multitrack_midi` pattern: int CC check first, then pitch_bend elif.

### M2. ~~NoteInfo.expression type annotation wrong~~ **FIXED**
**File**: `melodica/types_pkg/_notes.py`
Type was `dict[int, int]` but expression holds `{"pitch_bend": [(t, val)]}` (string key, list value).

**Fix**: Changed to `dict[int | str, int | list[tuple[float, int]]]`.

### M3. ~~FLUID_R3_PROGRAMS dead code~~ **FALSE POSITIVE**
11 album scripts import it. Not dead code.

### M4. ~~import random inside loop~~ **FIXED**
**File**: `melodica/midi.py` (3 locations inside humanization loops)
`import random` was inside loops, re-imported every iteration.

**Fix**: Added `import random` at module level, removed 3 inner imports.

### M5. ~~STYLE_INSTRUMENTS ImportError~~ **FIXED**
**File**: `melodica/midi.py`
`STYLE_INSTRUMENTS` was removed as "dead code" but `dark_fantasy_v3.py:85` and `df_downtempo.py:71` import it.

**Fix**: Re-added STYLE_INSTRUMENTS dict with "downtempo" and "dark_fantasy" keys.

### M6. ~~virtual_midi expression handling broken~~ **FIXED**
**File**: `melodica/virtual_midi.py:294-304`
- Silently dropped `"pitch_bend"` entries (not in int check)
- Crashed on list-valued CC data (`cc_val` passed directly to mido which expects int)

**Fix**: Added pitch_bend handling with `mido.Message("pitchwheel", ...)` and list value iteration.

### M7. Voice stealing consecutive-steal bug (LATENT)
**File**: `melodica/midi.py:582-612` and `989-1020`
When two notes steal the same channel in quick succession, the first stolen note's note_off event uses the truncated duration, but the second steal may overwrite `channel_active_events` before the first note_off is emitted. Only manifests with very small channel pools and overlapping notes.

**Deferred**: Requires careful redesign of the voice stealing state machine.

### M8. Double humanization (DESIGN)
Some callers apply `humanize()` on NoteInfo objects, then pass them through `export_midi(apply_humanize=True)` which applies a second pass. Timing/velocity noise compounds.

**Deferred**: Caller-level issue, not a code bug.
