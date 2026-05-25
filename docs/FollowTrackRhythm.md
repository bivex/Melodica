# Follow Track Rhythm

Apply another track's rhythm (onsets and durations) to the current track.

## What It Does

A track with `follow_rhythm_track` set will have its note timings replaced by the rhythm of the referenced source track. The follower keeps its own pitches and velocities — only start times and durations change.

```
Source track (Drums):   x . x . x x . x .   (onsets/durations)
Follower before:        x . . . x . . . x   (own rhythm)
Follower after:         x . x . x x . x .   (source rhythm, own pitches)
```

## Setup

Add `follow_rhythm_track` to a `TrackConfig`:

```python
TrackConfig(
    name="Brass_Hits",
    generator=BrassSectionGenerator(articulation="hit"),
    instrument="brass",
    density=0.3,
    follow_rhythm_track="Lead_Synth",
)
```

That's it. The source track renders first, then the follower's notes get re-timed to match.

## Rendering Order

The pipeline has three phases:

| Phase | Tracks | Description |
|-------|--------|-------------|
| 1 | Independent | All tracks with no `depends_on` and no `follow_rhythm_track` |
| 2 | Dependent | Tracks with `depends_on` (e.g. countermelody needs melody) |
| 3 | Follow rhythm | Tracks with `follow_rhythm_track` — re-timing applied after generation |

The source track must render before the follower. A source cannot be a dependent track or another follower.

## How It Works Internally

`FollowRhythmModifier` extracts unique onset/duration pairs from the source track, then for each onset finds the active note(s) in the follower and moves them to that onset with that duration. If no follower note is active at a source onset, the closest note in time is used.

## Use Cases

### Brass hits locked to lead melody

Brass stabs hit exactly when the lead plays:

```python
tracks = [
    TrackConfig(name="Lead_Synth", generator=LeadSynthGenerator(), ...),
    TrackConfig(name="Brass_Hits", generator=BrassSectionGenerator(articulation="hit"),
                ..., follow_rhythm_track="Lead_Synth"),
]
```

### Vocal chops following drum pattern

Vocal slices trigger on every drum hit:

```python
tracks = [
    TrackConfig(name="Trap_Drums", generator=TrapDrumsGenerator(), ...),
    TrackConfig(name="Vocal_Chops", generator=VocalChopsGenerator(),
                ..., follow_rhythm_track="Trap_Drums"),
]
```

### Counter-melody synchronized with lead

Two melodic lines share the same rhythmic skeleton:

```python
tracks = [
    TrackConfig(name="Lead_Synth", generator=LeadSynthGenerator(), ...),
    TrackConfig(name="Counter_Lead", generator=CountermelodyGenerator(),
                ..., follow_rhythm_track="Lead_Synth"),
]
```

### Bass following kick drum

Bass hits land on every kick:

```python
tracks = [
    TrackConfig(name="Trap_Drums", generator=TrapDrumsGenerator(), ...),
    TrackConfig(name="Sub_808", generator=Bass808SlidingGenerator(),
                ..., follow_rhythm_track="Trap_Drums"),
]
```

## Combining with Phrase Schedules

`follow_rhythm_track` applies globally across all parts. If the source track rests in some parts (via phrase schedules), those sections will have no source onsets — the follower keeps its original notes unchanged for those sections.

```python
IdeaPart(
    name="Verse",
    track_phrase_schedules={
        "Lead_Synth": structure_to_schedule("A", 8),   # plays
        "Brass_Hits": structure_to_schedule("A", 8),    # follows Lead_Synth rhythm
    },
),
IdeaPart(
    name="Breakdown",
    track_phrase_schedules={
        "Lead_Synth": structure_to_schedule("R", 8),   # rests
        "Brass_Hits": structure_to_schedule("A", 8),    # no source → keeps own rhythm
    },
),
```

## Combining with Modifiers

`follow_rhythm_track` runs as a post-processing step after all modifiers. The order:

1. Track generates its notes
2. `cfg.modifiers` are applied (humanize, velocity curves, etc.)
3. Voice leading, non-chord tones
4. `follow_rhythm_track` re-timing (Phase 3 of `_generate_all_tracks`)

If you want humanization after re-timing, add a second pass in your post-processing:

```python
from melodica.modifiers import HumanizeModifier, ModifierPipeline, ModifierContext

# After IdeaTool.generate()
pipeline = ModifierPipeline(base_notes=notes_dict["Brass_Hits"])
pipeline.add_modifier(HumanizeModifier(timing_std=0.01, velocity_std=3.0))
notes_dict["Brass_Hits"] = pipeline.process(mod_context)
```

## Advanced: FollowRhythmModifier as a Modifier

You can also use `FollowRhythmModifier` manually via `cfg.modifiers` for more control. This requires the source track notes to be available in `ModifierContext.tracks`:

```python
from melodica.modifiers.rhythmic import FollowRhythmModifier

TrackConfig(
    name="Brass_Hits",
    generator=BrassSectionGenerator(articulation="hit"),
    instrument="brass",
    density=0.3,
    modifiers=[FollowRhythmModifier(source_track="Lead_Synth")],
)
```

When used this way, `apply_track_modifiers` must receive the full `result` dict as `all_tracks` so the modifier can find the source notes. The declarative `follow_rhythm_track` field handles this automatically.

## Limitations

- The source track must be independent (not a dependent or follower itself)
- Re-timing applies to the entire track across all parts — there is no per-part override
- The follower's note count may change (more notes if source has denser rhythm, fewer if sparser)
- Polyphonic source tracks (chords, pads) produce onset groups — all simultaneous source notes count as one onset
