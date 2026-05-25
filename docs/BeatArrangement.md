# Beat Arrangement

How to build, render, and analyze multi-track beats in Melodica.

## Overview

A beat is a multi-track arrangement built with `IdeaTool`. The pipeline:

```
IdeaToolConfig (tracks + parts)
    → IdeaTool.generate()
        → chord progression per part
        → render each track per phrase schedule
        → post-processing (texture, voice leading, modifiers)
    → notes dict
    → export MIDI
```

The reference implementation is `scripts/demo_beat_arrangement.py`.

---

## 1. Define Tracks

Each track = one instrument with its generator. Put track definitions in a `_build_tracks()` function.

```python
from melodica.idea_tool import TrackConfig, structure_to_schedule
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator

lead_rhythm = MarkovRhythmGenerator(style="syncopated", syncopation=0.3)

tracks = [
    TrackConfig(
        name="Ambient_Pad",
        generator=NebulaGenerator(variant="swell", density_notes=6),
        instrument="dark_pad",
        density=0.4,
        octave_shift=-1,
    ),
    TrackConfig(
        name="Sub_808",
        generator=Bass808SlidingGenerator(pattern="trap_basic", slide_probability=0.4),
        instrument="synth_bass",
        density=0.6,
        octave_shift=-2,
    ),
    TrackConfig(
        name="Lead_Synth",
        generator=LeadSynthGenerator(style="trance", rhythm=lead_rhythm),
        instrument="synth_lead",
        density=0.6,
        octave_shift=1,
    ),
]
```

Key fields:

| Field | Type | Purpose |
|-------|------|---------|
| `name` | `str` | Track identifier, used in phrase schedules |
| `generator` | `PhraseGenerator` | Note generator instance |
| `instrument` | `str` | GM program name for MIDI mapping |
| `density` | `float` | 0.0–1.0, overall note density |
| `octave_shift` | `int` | Transpose rendered notes by N octaves |
| `modifiers` | `list` | Optional per-track modifier stack |
| `follow_rhythm_track` | `str \| None` | Name of another track whose onsets/durations to apply to this track's notes |

### Available Generators for Beats

| Generator | Module | Use case |
|-----------|--------|----------|
| `NebulaGenerator` | `generators.nebula` | Evolving pad textures |
| `AmbientPadGenerator` | `generators.ambient` | Sustained chord pads |
| `Bass808SlidingGenerator` | `generators.bass_808_sliding` | 808 bass with pitch slides |
| `TrapDrumsGenerator` | `generators.trap_drums` | Kicks, snares, hi-hats |
| `LeadSynthGenerator` | `generators.lead_synth` | Melodic lead lines |
| `VocalChopsGenerator` | `generators.vocal_chops` | Chopped vocal phrases |
| `BrassSectionGenerator` | `generators.brass_section` | Stab hits |
| `FXRiserGenerator` | `generators.fx_riser` | Transition risers |
| `FXImpactGenerator` | `generators.fx_impact` | Impact booms |
| `CountermelodyGenerator` | `generators` | Counter-melody to lead |
| `HiHatStutterGenerator` | `generators.hihat_stutter` | Rapid hat rolls |

---

## 2. Define Parts (Song Structure)

Each part = a section of the song (Intro, Verse, Hook, etc.). Parts specify which tracks play when, via phrase schedules.

```python
from melodica.types import Scale, Mode
from melodica.idea_tool import IdeaPart, structure_to_schedule

scale = Scale(2, Mode.NATURAL_MINOR)  # D minor

parts = [
    IdeaPart(
        name="Intro",
        bars=8,
        scale=scale,
        tempo=78,
        progression_type="coupled_hmm",
        track_phrase_schedules={
            "Ambient_Pad":   structure_to_schedule("A", 8),       # play A theme 8 bars
            "Sub_808":       structure_to_schedule("A", 8),
            "Trap_Drums":    structure_to_schedule("R", 8),       # rest
            "Lead_Synth":    structure_to_schedule("R", 8),
        },
    ),
    IdeaPart(
        name="Hook",
        bars=8,
        scale=scale,
        tempo=92,
        progression_type="coupled_hmm",
        track_phrase_schedules={
            "Ambient_Pad":   structure_to_schedule("A", 8),
            "Sub_808":       structure_to_schedule("C", 8),       # C theme = hook energy
            "Trap_Drums":    structure_to_schedule("C", 8),
            "Lead_Synth":    structure_to_schedule("C", 8),
        },
    ),
]
```

### Phrase Schedule Notation

`structure_to_schedule(template, slot_bars, loop=True)` creates phrase slots:

| Template | Meaning |
|----------|---------|
| `"A"` | Play A theme |
| `"R"` | Rest (silence) |
| `"A R"` | Play A, then rest (2 slots, each `slot_bars` long) |
| `"B R B:var"` | B, rest, B with variation |
| `"C:retro"` | C theme played retrograde |
| `"A B"` | A then B |

Same letter = same deterministic seed = identical phrase content across parts. Variants (`:var`, `:retro`, `:inv`) transform the recalled phrase.

### Typical Song Structure

```
Intro(8) → Build(4) → Verse(16) → PreHook(4) → Hook(8)
→ Breakdown(8) → Verse2(12) → Bridge(8) → Hook2(8) → Outro(8)
```

Energy curve: sparse → build → peak → drop → rebuild → peak → fade.

---

## 3. Generate

Wire tracks + parts into `IdeaToolConfig` and generate:

```python
from melodica.idea_tool import IdeaTool, IdeaToolConfig

config = IdeaToolConfig(
    style="hip_hop_trap",
    parts=parts,
    tracks=tracks,
    use_voice_leading=True,
    use_harmonic_verifier=True,
)

notes_dict = IdeaTool(config).generate()
```

Returns a dict: `{track_name: [NoteInfo, ...], "_chords": [...], "_timeline": MusicTimeline}`.

### Follow Track Rhythm

One track can adopt the rhythm (onsets and durations) of another track. Set `follow_rhythm_track` on the receiving track:

```python
TrackConfig(
    name="Brass_Hits",
    generator=BrassSectionGenerator(articulation="hit"),
    instrument="brass",
    density=0.3,
    follow_rhythm_track="Lead_Synth",  # brass plays when lead plays
)
```

How it works:
1. The source track renders normally (Phase 1/2 of `_generate_all_tracks`)
2. After the receiving track generates its own notes, `FollowRhythmModifier` replacess their onsets/durations with the source track's rhythm
3. The receiving track keeps its own pitches and velocities — only timing changes

This is a post-processing step, so the source track must be independent (not depend on the follower).

### Pipeline Flags

| Flag | Effect |
|------|--------|
| `use_voice_leading` | Smooth octave leaps in melodic tracks |
| `use_harmonic_verifier` | Reject notes that clash with chord progression |
| `use_texture_control` | Drop chord/pad notes based on tension curve density |

---

## 4. Post-Processing (Expression Pipeline)

Apply humanization, velocity curves, and metric accents per track:

```python
from melodica.modifiers import (
    ModifierPipeline, ModifierContext,
    HumanizeModifier, VelocityCurveModifier, MetricAccentModifier,
)

# Per-track modifier chains
pipelines = {
    "Lead_Synth": [
        HumanizeModifier(timing_std=0.02, velocity_std=8.0),
        VelocityCurveModifier(start_vel=50, end_vel=100, curve="crescendo"),
        MetricAccentModifier(strength=0.25),
    ],
    "Sub_808": [
        HumanizeModifier(timing_std=0.03, velocity_std=10.0),
        MetricAccentModifier(strength=0.3),
    ],
    "Trap_Drums": [
        HumanizeModifier(timing_std=0.01, velocity_std=5.0),
        MetricAccentModifier(strength=0.35),
    ],
}

for name, modifiers in pipelines.items():
    if name in notes_dict:
        pipeline = ModifierPipeline(base_notes=notes_dict[name])
        for mod in modifiers:
            pipeline.add_modifier(mod)
        notes_dict[name] = pipeline.process(mod_context)
```

### Recommended Modifiers per Track Type

| Track type | Modifiers |
|------------|-----------|
| Lead/Melody | Humanize + VelocityCurve (crescendo) + MetricAccent |
| Bass | Humanize + MetricAccent |
| Drums | Humanize (tight) + MetricAccent (strong) |
| Pad | Humanize (subtle) + VelocityCurve (fade) |
| Vocals | Humanize + VelocityCurve (swell) |

---

## 5. Export MIDI

```python
from melodica.midi import export_multitrack_midi
from melodica.idea_tool import _GM_PROGRAMS

tracks_data = {k: v for k, v in notes_dict.items()
               if not k.startswith("_") and isinstance(v, list)}

instruments_map = {t.name: _GM_PROGRAMS.get(t.instrument, 0) for t in tracks}

export_multitrack_midi(
    tracks_data,
    "output/my_beat.mid",
    bpm=85,
    instruments=instruments_map,
)
```

---

## 6. Analyze for Monotony

`scripts/analyze_beat.py` scores each track for musical variety. Lower scores indicate monotony problems.

```bash
python3 scripts/analyze_beat.py                    # analyze beat arrangement
python3 scripts/analyze_beat.py --script pro       # analyze cinematic structure
```

### What It Measures

| Metric | Weight | What it checks |
|--------|--------|----------------|
| Pitch entropy | 25% | Are many different pitches used, or just a few? |
| Rhythm entropy | 20% | Variety of note durations |
| Velocity entropy | 20% | Dynamic range (loud/soft contrast) |
| Interval entropy | 15% | Variety of pitch intervals between consecutive notes |
| Repetition | 20% | 4-note sequence repetition ratio (lower = better) |

**Overall score** = weighted average. 0.0 = complete monotony, 1.0 = maximum variety.

### Score Thresholds

| Range | Status |
|-------|--------|
| 0.5+ | Good |
| 0.3–0.5 | Needs attention |
| <0.3 | Problem |

### Common Issues Detected

| Issue | Cause | Fix |
|-------|-------|-----|
| `EMPTY TRACK` | Generator produces 0 notes | Check phrase schedule is not all `R`, check generator pitch range |
| `MONORHYTHM` | All notes same duration | Add a rhythm generator (Markov/Probabilistic) |
| `LOW PITCH ENTROPY` | Same few notes repeating | Use motif_probability, interval_limit, or wider voicing |
| `FLAT VELOCITY` | No dynamic variation | Add VelocityCurveModifier + MetricAccentModifier |
| `FLAT DENSITY` | Same notes/bar throughout | Vary density per part in track_phrase_schedules |
| `HIGH REPETITION` | 4-note patterns repeat verbatim | Enable phrase memory transforms (`:var`, `:retro`) |

### Reading the Report

```
┌─ Lead_Synth (134 notes, 320 beats) ─────────────────
│ Pitch variety:    ████████████████████░░ 0.93
│ Rhythm variety:   █████████████████░░░░ 0.87
│ Velocity variety: ██████████████████░░░ 0.92
│ Interval variety: █████████████████░░░░ 0.89
│ Repetition:       ████████████████████░ 1.00
│ OVERALL:          ██████████████████░░░ 0.93
│
│ Pitches: 35 unique, range 45.0 semitones
│ Duration types: 15 unique
│ Velocity range: 45
│ Density: 1.7 notes/bar, variance 2.2
└────────────────────────────────────────────────────
```

- Green bars = good (0.5+)
- Yellow bars = borderline (0.3–0.5)
- Red bars = problem (<0.3)

---

## Quick Start Template

Minimal working beat:

```python
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.types import Scale, Mode
from melodica.midi import export_multitrack_midi

scale = Scale(2, Mode.NATURAL_MINOR)

tracks = [
    TrackConfig(name="Drums", generator=TrapDrumsGenerator(), instrument="drums", density=0.8),
    TrackConfig(name="Bass", generator=Bass808SlidingGenerator(), instrument="synth_bass", density=0.6, octave_shift=-2),
    TrackConfig(name="Lead", generator=LeadSynthGenerator(), instrument="synth_lead", density=0.6, octave_shift=1),
]

parts = [
    IdeaPart(name="Verse", bars=8, scale=scale, tempo=85, progression_type="coupled_hmm",
             track_phrase_schedules={
                 "Drums": structure_to_schedule("A", 8),
                 "Bass":  structure_to_schedule("A", 8),
                 "Lead":  structure_to_schedule("R A", 4),
             }),
    IdeaPart(name="Hook", bars=8, scale=scale, tempo=92, progression_type="coupled_hmm",
             track_phrase_schedules={
                 "Drums": structure_to_schedule("C", 8),
                 "Bass":  structure_to_schedule("C", 8),
                 "Lead":  structure_to_schedule("C", 8),
             }),
]

notes = IdeaTool(IdeaToolConfig(style="hip_hop_trap", parts=parts, tracks=tracks)).generate()

export_multitrack_midi(
    {k: v for k, v in notes.items() if not k.startswith("_")},
    "output/quick_beat.mid", bpm=85,
)
```
