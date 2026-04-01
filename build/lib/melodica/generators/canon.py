"""
generators/canon.py — Canon/imitation generator with counterpoint rules.

Layer: Application / Domain
Style: Classical counterpoint, fugal writing.

Canon types:
    "strict"    — exact intervallic transposition
    "tonal"     — diatonic transposition preserving scale function
    "contrary"  — follower moves in opposite direction
    "free"      — follower adapts to fit harmony
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
_STRONG_CONSONANT = {0, 3, 4, 7, 8, 9}
_STEP_WEIGHT = 0.5
_INVALID_CANON_TYPES = frozenset({"strict", "tonal", "contrary", "free"})
_DEFAULT_DELAY = 2.0


# ---------------------------------------------------------------------------
# Follower config
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _FollowerCfg:
    """Configuration for a single follower voice."""

    interval: int
    delay: float
    index: int


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class CanonGenerator(PhraseGenerator):
    """
    Canon/imitation generator with counterpoint rules.

    canon_type:
        "strict", "tonal", "contrary", "free"
    delay_beats:
        How many beats the follower lags behind.
    interval:
        Semitone offset for the first follower.
    num_followers:
        Number of follower voices (1-3).
    """

    name: str = "Canon Generator"
    canon_type: str = "tonal"
    delay_beats: float = _DEFAULT_DELAY
    interval: int = 7
    num_followers: int = 1
    lead_rhythm: RhythmGenerator | None = None
    follower_rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        canon_type: str = "tonal",
        delay_beats: float = _DEFAULT_DELAY,
        interval: int = 7,
        num_followers: int = 1,
        lead_rhythm: RhythmGenerator | None = None,
        follower_rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if canon_type not in _INVALID_CANON_TYPES:
            raise ValueError(
                f"canon_type must be one of {_INVALID_CANON_TYPES}; got {canon_type!r}"
            )
        self.canon_type = canon_type
        self.delay_beats = max(0.25, delay_beats)
        self.interval = interval
        self.num_followers = max(1, min(3, num_followers))
        self.lead_rhythm = lead_rhythm
        self.follower_rhythm = follower_rhythm

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

        lead = self._generate_lead(chords, key, duration_beats, context)
        all_notes = list(lead)

        for cfg in self._follower_configs(key):
            follower = self._generate_follower(lead, chords, key, duration_beats, cfg)
            all_notes.extend(follower)

        all_notes.sort(key=lambda n: n.start)
        last_chord = chords[-1] if chords else None

        if all_notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=all_notes[-1].pitch,
                last_velocity=all_notes[-1].velocity,
                last_chord=last_chord,
            )
        return all_notes

    # ------------------------------------------------------------------
    # Follower configs
    # ------------------------------------------------------------------

    def _follower_configs(self, key: Scale) -> list[_FollowerCfg]:
        configs: list[_FollowerCfg] = []
        for i in range(self.num_followers):
            ivl = self._follower_interval(i)
            delay = self.delay_beats * (i + 1)
            configs.append(_FollowerCfg(interval=ivl, delay=delay, index=i))
        return configs

    def _follower_interval(self, idx: int) -> int:
        if idx == 0:
            return self.interval
        if idx == 1:
            offset = 7 if self.interval < 7 else 5
            return self.interval + offset
        return self.interval + _OCTAVE

    # ------------------------------------------------------------------
    # Lead melody
    # ------------------------------------------------------------------

    def _generate_lead(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        events = self._build_events(duration_beats, self.lead_rhythm)
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2
        prev = context.prev_pitch if context and context.prev_pitch is not None else anchor

        for ev in events:
            chord = chord_at(chords, ev.onset)
            if chord is None:
                continue
            pitch = _pick_lead_pitch(chord, key, prev, low, high)
            vel = int((70 + self.params.density * 30) * ev.velocity_factor)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ev.onset, 6),
                    duration=ev.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev = pitch
        return notes

    # ------------------------------------------------------------------
    # Follower generation
    # ------------------------------------------------------------------

    def _generate_follower(
        self,
        lead: list[NoteInfo],
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        cfg: _FollowerCfg,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high

        for note in lead:
            onset = note.start + cfg.delay
            if onset >= duration_beats:
                break
            pitch = self._follower_pitch(note, lead, chords, key, cfg, onset)
            pitch = max(low, min(high, pitch))

            chord = chord_at(chords, onset)
            if chord is not None:
                pitch = _ensure_consonance(pitch, note.pitch, chord, low, high)

            vel = max(1, min(127, int(note.velocity * (0.9 - cfg.index * 0.05))))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=note.duration,
                    velocity=vel,
                )
            )
        return notes

    def _follower_pitch(
        self,
        note: NoteInfo,
        lead: list[NoteInfo],
        chords: list[ChordLabel],
        key: Scale,
        cfg: _FollowerCfg,
        onset: float,
    ) -> int:
        ct = self.canon_type
        if ct == "strict":
            return note.pitch + cfg.interval
        if ct == "tonal":
            return _tonal_transpose(note.pitch, cfg.interval, key)
        if ct == "contrary":
            return _contrary_pitch(note, lead, cfg.interval)
        return _free_imitation(note, chords, key, cfg.interval, onset)

    # ------------------------------------------------------------------
    # Rhythm
    # ------------------------------------------------------------------

    def _build_events(
        self,
        duration_beats: float,
        rhythm: RhythmGenerator | None,
    ) -> list[RhythmEvent]:
        if rhythm is not None:
            return rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.45))
            t += 0.5
        return events


# ---------------------------------------------------------------------------
# Pure pitch-selection functions
# ---------------------------------------------------------------------------


def _pick_lead_pitch(
    chord: ChordLabel,
    key: Scale,
    prev: int,
    low: int,
    high: int,
) -> int:
    pcs = chord.pitch_classes()
    degs = key.degrees()

    if random.random() < 0.5 and pcs:
        pc = random.choice(pcs)
    elif degs:
        pc = random.choice(degs)
    else:
        pc = chord.root

    step = random.choice([-3, -2, -1, -1, 1, 1, 2, 3])
    target = prev + step
    pitch = nearest_pitch(int(pc), target)
    return max(low, min(high, pitch))


def _tonal_transpose(pitch: int, semitones: int, key: Scale) -> int:
    degs = key.degrees()
    if not degs:
        return pitch + semitones

    pc = pitch % _OCTAVE
    deg_idx = _find_scale_degree(pc, degs)
    if deg_idx is None:
        return pitch + semitones

    degree_shift = round(semitones / 2)
    new_idx = (deg_idx + degree_shift) % len(degs)
    new_pc = int(degs[new_idx])

    shift = (new_pc - pc) % _OCTAVE
    if shift > 6:
        shift -= _OCTAVE
    return pitch + shift


def _find_scale_degree(pc: int, degs: list) -> int | None:
    for i, d in enumerate(degs):
        if abs(int(d) - pc) < 2:
            return i
    return None


def _contrary_pitch(
    note: NoteInfo,
    lead: list[NoteInfo],
    interval: int,
) -> int:
    direction = 1
    for i, ln in enumerate(lead):
        if abs(ln.start - note.start) < 0.01 and i > 0:
            prev_lead = lead[i - 1]
            direction = 1 if note.pitch < prev_lead.pitch else -1
            break
    base = note.pitch + interval
    contrary = direction * random.choice([2, 3, 4, 5])
    return base - contrary


def _free_imitation(
    note: NoteInfo,
    chords: list[ChordLabel],
    key: Scale,
    interval: int,
    onset: float,
) -> int:
    chord = chord_at(chords, onset)
    if chord is None:
        return note.pitch + interval

    base = note.pitch + interval
    pcs = chord.pitch_classes()
    if pcs:
        nearest_pc = min(pcs, key=lambda p: abs(int(p) - (base % _OCTAVE)))
        return nearest_pitch(int(nearest_pc), base)
    return base


def _ensure_consonance(
    follower: int,
    lead: int,
    chord: ChordLabel,
    low: int,
    high: int,
) -> int:
    ivl = abs(follower - lead) % _OCTAVE
    if ivl in _STRONG_CONSONANT:
        return follower

    pcs = chord.pitch_classes()
    best = follower
    best_dist = 999
    for pc in pcs:
        cand = nearest_pitch(int(pc), follower)
        if low <= cand <= high:
            iv = abs(cand - lead) % _OCTAVE
            if iv in _CONSONANT:
                dist = abs(cand - follower)
                if dist < best_dist:
                    best_dist = dist
                    best = cand
    return best
