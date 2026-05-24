# Phrase Schedules

Phrase Schedules control **when** an instrument plays and **when** it rests within a single part — like placing clips on the FL Studio Playlist or RapidComposer's timeline.

## Problem

Without phrase schedules, every instrument plays continuously for the entire part. `track_mute` can silence a track for a whole part, but there is no way to say "play 4 bars, rest 2 bars, play 2 bars."

## Core Types

### PhraseSlot

A single segment — play, rest, or ghost copy.

```python
from melodica.idea_tool import PhraseSlot

PhraseSlot(kind="play", bars=4, label="A")   # play for 4 bars
PhraseSlot(kind="rest", bars=2)               # silence for 2 bars
PhraseSlot(kind="ghost", bars=2, label="A")   # re-render with same seed as label "A"
```

| Field  | Type   | Default   | Description                                          |
|--------|--------|-----------|------------------------------------------------------|
| `kind` | `str`  | `"play"`  | `"play"`, `"rest"`, or `"ghost"`                     |
| `bars` | `int`  | `4`       | Number of bars this slot occupies                    |
| `label`| `str`  | `"A"`     | Label for deterministic seeding (same label = same material) |

### PhraseSchedule

An ordered list of slots with optional looping.

```python
from melodica.idea_tool import PhraseSchedule

PhraseSchedule(
    slots=[...],
    loop=True   # repeat to fill the part
)
```

| Field   | Type            | Default | Description                                       |
|---------|-----------------|---------|---------------------------------------------------|
| `slots` | `list[PhraseSlot]` | `[]`  | Ordered sequence of play/rest/ghost segments      |
| `loop`  | `bool`          | `True`  | If `True`, repeat slots to fill the part's bars   |

## Usage

### On a TrackConfig

Add `phrase_schedule` to any track:

```python
from melodica.idea_tool import TrackConfig, PhraseSlot, PhraseSchedule

TrackConfig(
    name="flute",
    generator_type="melody",
    instrument="flute",
    density=0.6,
    phrase_schedule=PhraseSchedule(slots=[
        PhraseSlot(kind="play", bars=4, label="A"),
        PhraseSlot(kind="rest", bars=2),
        PhraseSlot(kind="play", bars=2, label="B"),
    ], loop=False),
)
```

### Looping Pattern

A short pattern that repeats across a longer part:

```python
# 2 bars on, 2 bars off — loops to fill 16 bars
PhraseSchedule(slots=[
    PhraseSlot(kind="play", bars=2, label="A"),
    PhraseSlot(kind="rest", bars=2),
], loop=True)
```

### Per-Part Override via IdeaPart

Different parts of a composition can have different phrase schedules for the same track:

```python
from melodica.idea_tool import IdeaPart

IdeaPart(
    name="Verse",
    bars=8,
    track_phrase_schedules={
        "strings": PhraseSchedule(slots=[
            PhraseSlot(kind="play", bars=8, label="A"),
        ]),
    },
),
IdeaPart(
    name="Chorus",
    bars=8,
    track_phrase_schedules={
        "strings": PhraseSchedule(slots=[
            PhraseSlot(kind="play", bars=4, label="A"),
            PhraseSlot(kind="rest", bars=4),
        ]),
    },
)
```

Per-part override takes priority over the track's default `phrase_schedule`.

### Ghost Phrases

Ghost re-renders with the same deterministic seed as the matching label. Same melodic contour, adapted to different underlying chords:

```python
PhraseSchedule(slots=[
    PhraseSlot(kind="play", bars=4, label="A"),
    PhraseSlot(kind="rest", bars=2),
    PhraseSlot(kind="ghost", bars=2, label="A"),  # echoes the "A" phrase
])
```

## Full Example

```python
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart,
    PhraseSlot, PhraseSchedule,
)
from melodica.types import Scale, Mode

tracks = [
    TrackConfig(name="melody", generator_type="melody", density=0.7),
    TrackConfig(
        name="strings",
        generator_type="arpeggiator",
        density=0.6,
        phrase_schedule=PhraseSchedule(slots=[
            PhraseSlot(kind="play", bars=4, label="A"),
            PhraseSlot(kind="rest", bars=4),
        ], loop=True),
    ),
    TrackConfig(
        name="brass",
        generator_type="chord",
        density=0.5,
        phrase_schedule=PhraseSchedule(slots=[
            PhraseSlot(kind="rest", bars=8),
            PhraseSlot(kind="play", bars=8, label="B"),
        ], loop=False),
    ),
]

config = IdeaToolConfig(
    parts=[
        IdeaPart(name="Intro", bars=8, scale=Scale(0, Mode.MAJOR), tempo=90),
        IdeaPart(name="Main", bars=16, scale=Scale(0, Mode.MAJOR), tempo=100),
    ],
    tracks=tracks,
)

result = IdeaTool(config).generate()
```

In this example:
- **melody** plays continuously (no schedule = old behavior)
- **strings** play 4 bars on / 4 bars off, looping across both parts
- **brass** stays silent for the Intro (8 bars rest), then plays the Main part (8 bars)

## Backward Compatibility

When `phrase_schedule` is `None` (the default), the existing arrangement-pattern logic runs unchanged. No existing scripts need modification.

`track_mute` still works and takes priority — a muted track is fully skipped regardless of phrase schedule.
