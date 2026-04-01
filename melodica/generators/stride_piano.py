"""
generators/stride_piano.py — Stride piano left-hand pattern generator.

Layer: Application / Domain
Style: Harlem stride piano (Fats Waller, James P. Johnson, Art Tatum).

Stride piano alternates between:
  - A bass note (or octave) on beats 1 and 3
  - A chord (or chord voicing) on beats 2 and 4

Patterns:
    "standard"       — bass(1)-chord(2)-bass(3)-chord(4)
    "waltz"          — bass(1)-chord-chord (3/4 time)
    "tatum"          — faster, chromatic approaches + ornaments
    "simple"         — bass(1)-rest-chord(3)-rest
    "broken_tenths"  — bass(1)-chord(2)-tenth(3)-chord(4)
    "walking_stride" — walking bass + chord on 2/4
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import (
    nearest_pitch,
    chord_pitches_closed,
    chord_at,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12
_BASS_LOW_DEFAULT = 28
_APPROACH_THRESHOLD = 0.4
_APPROACH_DUR_FRACTION = 0.3
_NEIGHBOR_DUR_FRACTION = 0.2
_NEIGHBOR_VEL_FACTOR = 0.7
_TURN_DIVISIONS = 4
_TURN_VEL_FACTOR = 0.6
_CHORD_DUR_FRACTION = 0.3
_DOWNBEAT_VEL_BOOST = 1.1
_CHORD_VEL_FACTOR = 0.85
_CHROMATIC_RAND_THRESHOLD = 0.6

_VALID_PATTERNS = frozenset(
    {
        "standard",
        "waltz",
        "tatum",
        "simple",
        "broken_tenths",
        "walking_stride",
    }
)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class StridePianoGenerator(PhraseGenerator):
    """
    Stride piano left-hand pattern generator.

    pattern:
        "standard", "waltz", "tatum", "simple",
        "broken_tenths", "walking_stride"
    bass_octave_doubled:
        Double the bass note at the octave below.
    chord_voicing:
        "closed" or "open" voicing for the chord portion.
    chromatic_approach:
        Add chromatic approach notes before bass notes.
    ornaments:
        Add grace note ornaments (turns, mordents).
    """

    name: str = "Stride Piano Generator"
    pattern: str = "standard"
    bass_octave_doubled: bool = True
    chord_voicing: str = "closed"
    chromatic_approach: bool = True
    ornaments: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "standard",
        bass_octave_doubled: bool = True,
        chord_voicing: str = "closed",
        chromatic_approach: bool = True,
        ornaments: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if pattern not in _VALID_PATTERNS:
            raise ValueError(f"pattern must be one of {_VALID_PATTERNS}; got {pattern!r}")
        self.pattern = pattern
        self.bass_octave_doubled = bass_octave_doubled
        self.chord_voicing = chord_voicing
        self.chromatic_approach = chromatic_approach
        self.ornaments = ornaments
        self.rhythm = rhythm

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        notes: list[NoteInfo] = []
        mid = self._mid_pitch()
        low = max(_BASS_LOW_DEFAULT, self.params.key_range_low)
        state = _StrideState(prev_bass=low + _OCTAVE)
        last_chord: ChordLabel | None = None

        for event in self._build_events(duration_beats):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            slot = _classify_slot(self.pattern, event.onset)
            sc = _SlotCtx(
                chord=chord,
                chords=chords,
                key=key,
                event=event,
                mid=mid,
                low=low,
            )
            state = self._handle_slot(slot, sc, state, notes)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Slot handlers
    # ------------------------------------------------------------------

    def _handle_slot(
        self,
        slot: str,
        sc: _SlotCtx,
        state: _StrideState,
        notes: list[NoteInfo],
    ) -> _StrideState:
        if slot == "bass":
            return self._handle_bass(sc, state, notes)
        if slot == "tenth":
            return self._handle_tenth(sc, state, notes)
        if slot == "walking":
            return self._handle_walking(sc, state, notes)
        return self._handle_chord(sc, state, notes)

    def _handle_bass(
        self,
        sc: _SlotCtx,
        state: _StrideState,
        notes: list[NoteInfo],
    ) -> _StrideState:
        root_pc = sc.chord.root
        target = nearest_pitch(root_pc, state.prev_bass)
        target = max(sc.low, min(sc.mid - 5, target))

        # Chromatic approach
        if self._should_approach(state):
            approach = self._chromatic_approach_bass(target, sc.low, sc.mid)
            if approach is not None:
                dur = sc.event.duration * _APPROACH_DUR_FRACTION
                vel = _velocity_bass(self.params.density, sc.event.onset)
                notes.append(_make_note(approach, sc.event.onset, dur, vel))

        # Ornaments
        if self._should_ornament():
            notes.extend(
                _turn_ornament(target, sc.event.onset, sc.event.duration, self.params.density)
            )

        vel = _velocity_bass(self.params.density, sc.event.onset)
        notes.append(_make_note(target, sc.event.onset, sc.event.duration, vel))

        if self.bass_octave_doubled:
            oct_down = max(sc.low, target - _OCTAVE)
            notes.append(_make_note(oct_down, sc.event.onset, sc.event.duration, int(vel * 0.8)))

        return _StrideState(prev_bass=target, prev_bass_pc=target % _OCTAVE)

    def _handle_tenth(
        self,
        sc: _SlotCtx,
        state: _StrideState,
        notes: list[NoteInfo],
    ) -> _StrideState:
        root_pc = sc.chord.root
        bass = nearest_pitch(root_pc, state.prev_bass)
        bass = max(sc.low, min(sc.mid - 5, bass))

        third_pc = _find_third_pc(sc.chord)
        tenth = nearest_pitch(third_pc, bass + 15)
        tenth = max(sc.mid - 5, min(self.params.key_range_high, tenth))

        vel = _velocity_chord(self.params.density, sc.event.onset)
        notes.append(_make_note(bass, sc.event.onset, sc.event.duration, vel))
        notes.append(
            _make_note(tenth, sc.event.onset, sc.event.duration, int(vel * _CHORD_VEL_FACTOR))
        )

        return _StrideState(prev_bass=bass, prev_bass_pc=bass % _OCTAVE)

    def _handle_walking(
        self,
        sc: _SlotCtx,
        state: _StrideState,
        notes: list[NoteInfo],
    ) -> _StrideState:
        next_ch = _next_chord(sc.chords, sc.event.onset)
        if next_ch is not None:
            bass = _walking_bass_pitch(state.prev_bass, next_ch, sc.key, sc.low, sc.mid)
        else:
            bass = nearest_pitch(sc.chord.root, state.prev_bass)
            bass = max(sc.low, min(sc.mid - 5, bass))

        vel = _velocity_bass(self.params.density, sc.event.onset)
        notes.append(_make_note(bass, sc.event.onset, sc.event.duration, vel))
        return _StrideState(prev_bass=bass, prev_bass_pc=bass % _OCTAVE)

    def _handle_chord(
        self,
        sc: _SlotCtx,
        state: _StrideState,
        notes: list[NoteInfo],
    ) -> _StrideState:
        voicing = _build_chord_voicing(sc.chord, sc.mid, self.chord_voicing)
        voicing = [max(sc.mid - 5, min(self.params.key_range_high, p)) for p in voicing]
        vel = _velocity_chord(self.params.density, sc.event.onset)

        # Tatum-style chromatic neighbor
        if self.pattern == "tatum" and self.chromatic_approach:
            if voicing and random.random() < _CHORD_DUR_FRACTION:
                neighbor = voicing[-1] - 1
                if neighbor >= sc.mid - 5:
                    dur = sc.event.duration * _NEIGHBOR_DUR_FRACTION
                    nvel = int(vel * _NEIGHBOR_VEL_FACTOR)
                    notes.append(_make_note(neighbor, sc.event.onset, dur, nvel))

        for p in voicing:
            notes.append(_make_note(p, sc.event.onset, sc.event.duration, vel))
        return state

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mid_pitch(self) -> int:
        return (self.params.key_range_low + self.params.key_range_high) // 2

    def _should_approach(self, state: _StrideState) -> bool:
        return (
            self.chromatic_approach
            and state.prev_bass_pc is not None
            and random.random() < _APPROACH_THRESHOLD
        )

    def _should_ornament(self) -> bool:
        return self.ornaments and self.pattern == "tatum" and random.random() < 0.25

    def _chromatic_approach_bass(
        self,
        target: int,
        low: int,
        mid: int,
    ) -> int | None:
        approach = target - 1
        return approach if approach >= low else None

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.9))
            t += 1.0
        return events


# ---------------------------------------------------------------------------
# State and helpers
# ---------------------------------------------------------------------------


@dataclass
class _StrideState:
    prev_bass: int
    prev_bass_pc: int | None = None


@dataclass(frozen=True)
class _SlotCtx:
    """Context passed to slot handlers."""

    chord: ChordLabel
    chords: list[ChordLabel]
    key: Scale
    event: RhythmEvent
    mid: int
    low: int


def _make_note(pitch: int, onset: float, dur: float, vel: int) -> NoteInfo:
    return NoteInfo(
        pitch=max(0, min(127, pitch)),
        start=round(onset, 6),
        duration=dur,
        velocity=max(1, min(127, vel)),
    )


def _classify_slot(pattern: str, onset: float) -> str:
    beat = int(onset % 4) if pattern != "waltz" else int(onset % 3)
    if pattern == "standard":
        return "bass" if beat in (0, 2) else "chord"
    if pattern == "waltz":
        return "bass" if beat == 0 else "chord"
    if pattern == "simple":
        return "bass" if beat in (0, 2) else "chord"
    if pattern == "broken_tenths":
        if beat == 0:
            return "bass"
        if beat == 2:
            return "tenth"
        return "chord"
    if pattern == "tatum":
        return "bass" if beat in (0, 2) else "chord"
    if pattern == "walking_stride":
        return "walking" if beat in (0, 2) else "chord"
    return "bass" if beat in (0, 2) else "chord"


def _find_third_pc(chord: ChordLabel) -> int:
    root = chord.root
    for pc in chord.pitch_classes():
        ivl = (pc - root) % _OCTAVE
        if ivl in (3, 4):
            return pc
    pcs = chord.pitch_classes()
    return pcs[1] if len(pcs) > 1 else root


def _next_chord(chords: list[ChordLabel], onset: float) -> ChordLabel | None:
    for c in chords:
        if c.start > onset + 0.01:
            return c
    return None


def _walking_bass_pitch(
    prev_bass: int,
    next_chord: ChordLabel,
    key: Scale,
    low: int,
    mid: int,
) -> int:
    next_root = nearest_pitch(next_chord.root, prev_bass)
    if random.random() < _CHROMATIC_RAND_THRESHOLD:
        approach = next_root - 1 if prev_bass > next_root else next_root + 1
        bass = max(low, min(mid - 5, approach))
    else:
        degs = key.degrees()
        candidates = [nearest_pitch(int(d), next_root) for d in degs]
        candidates = [p for p in candidates if 1 <= abs(p - next_root) <= 2]
        bass = random.choice(candidates) if candidates else next_root
    return max(low, min(mid - 5, bass))


def _build_chord_voicing(chord: ChordLabel, mid: int, voicing_type: str) -> list[int]:
    if voicing_type == "open":
        from melodica.utils import chord_pitches_open

        return chord_pitches_open(chord, mid)
    return chord_pitches_closed(chord, mid)


def _turn_ornament(
    bass: int,
    onset: float,
    duration: float,
    density: float,
) -> list[NoteInfo]:
    note_dur = duration / _TURN_DIVISIONS
    vel = int(65 + density * 25)
    orn = [bass - 1, bass, bass + 1, bass]
    return [
        NoteInfo(
            pitch=max(0, min(127, p)),
            start=round(onset + i * note_dur, 6),
            duration=note_dur * 0.8,
            velocity=max(1, min(127, int(vel * _TURN_VEL_FACTOR))),
        )
        for i, p in enumerate(orn)
    ]


def _velocity_bass(density: float, onset: float) -> int:
    base = int(65 + density * 25)
    if onset % 4.0 < 0.1:
        return min(127, int(base * _DOWNBEAT_VEL_BOOST))
    return base


def _velocity_chord(density: float, onset: float) -> int:
    return int(55 + density * 20)
