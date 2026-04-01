"""
generators/montuno.py — Latin piano montuno pattern generator.

Layer: Application / Domain
Style: Salsa, son cubano, Latin jazz.

A montuno is a repeating piano pattern in Afro-Cuban music, typically
consisting of a syncopated two-bar ostinato figure that outlines the
chord changes with rhythmic precision.

Patterns:
    "son"              — classic son montuno
    "salsa"            — salsa montuno with more chord tones
    "guajira"          — guajira montuno (more melodic)
    "cha_cha"          — cha-cha-chá piano pattern
    "mambo"            — mambo horn-like piano pattern
    "guajeo_modern"    — modern guajeo with syncopation
    "moña"             — moña (repeated melodic hook)

Clave types:
    "son_32"    — son clave 3-2
    "son_23"    — son clave 2-3
    "rumba_32"  — rumba clave 3-2
    "rumba_23"  — rumba clave 2-3
    "none"      — no clave alignment
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
_CYCLE_LEN = 8.0  # 2 bars of 4/4
_BASS_LOW = 28
_TUMBAO_BASS_SPAN = 19
_TUMBAO_BAR_BEATS = 4
_TUMBAO_BEAT4_OFFSET = 3.5
_TUMBAO_BEAT2_OFFSET = 1.5
_TUMBAO_DUR = 0.4
_DYNAMIC_ROOT_PROB = 0.4
_DYNAMIC_FIFTH_PROB = 0.5
_CLAVE_TOLERANCE = 0.15
_DOWNBEAT_TOLERANCE = 0.1
_DURATION_FACTOR = 0.85
_OCTAVE_VEL_FACTOR = 0.7
_TUMBAO_VEL_BOOST = 1.1


# ---------------------------------------------------------------------------
# Pattern data
# ---------------------------------------------------------------------------

NAMED_PATTERNS: dict[str, list[tuple[int, float]]] = {
    "son": [
        (1, 0.5),
        (5, 0.5),
        (8, 0.5),
        (3, 0.5),
        (5, 0.5),
        (3, 0.5),
        (1, 0.5),
        (5, 0.5),
    ],
    "salsa": [
        (1, 0.25),
        (3, 0.25),
        (5, 0.25),
        (8, 0.25),
        (5, 0.5),
        (3, 0.5),
        (1, 0.25),
        (3, 0.25),
        (5, 0.5),
    ],
    "guajira": [
        (1, 0.5),
        (3, 0.5),
        (5, 0.5),
        (6, 0.5),
        (5, 0.5),
        (3, 0.5),
    ],
    "cha_cha": [
        (1, 0.5),
        (3, 0.5),
        (5, 0.5),
        (5, 0.25),
        (3, 0.25),
        (1, 0.5),
        (3, 0.5),
    ],
    "mambo": [
        (1, 0.25),
        (3, 0.25),
        (5, 0.25),
        (8, 0.25),
        (8, 0.25),
        (5, 0.25),
        (3, 0.25),
        (1, 0.25),
        (3, 0.25),
        (5, 0.25),
        (8, 0.25),
        (5, 0.25),
        (3, 0.25),
        (1, 0.25),
        (5, 0.25),
        (1, 0.25),
    ],
    "guajeo_modern": [
        (1, 0.25),
        (5, 0.25),
        (3, 0.5),
        (8, 0.25),
        (5, 0.25),
        (1, 0.5),
        (3, 0.25),
        (5, 0.25),
        (8, 0.5),
        (5, 0.5),
        (1, 0.5),
    ],
    "moña": [
        (1, 0.25),
        (3, 0.25),
        (5, 0.25),
        (3, 0.25),
        (1, 0.5),
        (5, 0.5),
        (8, 0.25),
        (5, 0.25),
        (3, 0.25),
        (5, 0.25),
        (1, 0.5),
        (3, 0.5),
    ],
}

_CLAVE_SON_32 = [0.0, 1.5, 3.0, 4.0, 6.0]
_CLAVE_SON_23 = [0.0, 3.0, 4.0, 5.5, 7.0]
_CLAVE_RUMBA_32 = [0.0, 1.5, 3.0, 4.0, 6.5]
_CLAVE_RUMBA_23 = [0.0, 3.0, 4.0, 5.5, 7.5]

_CLAVE_PATTERNS: dict[str, list[float]] = {
    "son_32": _CLAVE_SON_32,
    "son_23": _CLAVE_SON_23,
    "rumba_32": _CLAVE_RUMBA_32,
    "rumba_23": _CLAVE_RUMBA_23,
}

_DYNAMIC_RHYTHMS = [0.25, 0.25, 0.5, 0.5, 0.5]


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class MontunoGenerator(PhraseGenerator):
    """
    Latin piano montuno pattern generator with clave awareness.

    pattern:
        Named pattern ("son", "salsa", "guajira", "cha_cha", "mambo",
        "guajeo_modern", "moña").
    clave_type:
        Clave pattern for accent alignment.
    octave_doubling:
        Double notes at the octave.
    tumbao_bass:
        Generate a tumbao bass line.
    dynamic_pattern:
        Vary pattern based on chord structure.
    """

    name: str = "Montuno Generator"
    pattern: str = "son"
    clave_type: str = "none"
    octave_doubling: bool = True
    tumbao_bass: bool = False
    dynamic_pattern: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    _VALID_PATTERNS = frozenset(NAMED_PATTERNS.keys())
    _VALID_CLAVES = frozenset(_CLAVE_PATTERNS.keys()) | {"none"}

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "son",
        clave_type: str = "none",
        octave_doubling: bool = True,
        tumbao_bass: bool = False,
        dynamic_pattern: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if pattern not in self._VALID_PATTERNS:
            raise ValueError(f"pattern must be one of {self._VALID_PATTERNS}; got {pattern!r}")
        if clave_type not in self._VALID_CLAVES:
            raise ValueError(f"clave_type must be one of {self._VALID_CLAVES}; got {clave_type!r}")
        self.pattern = pattern
        self.clave_type = clave_type
        self.octave_doubling = octave_doubling
        self.tumbao_bass = tumbao_bass
        self.dynamic_pattern = dynamic_pattern
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

        pattern_data = NAMED_PATTERNS.get(self.pattern, NAMED_PATTERNS["son"])
        cycle = self._cycle_length(pattern_data)
        events = self._build_events(duration_beats, cycle)
        notes: list[NoteInfo] = []
        mid = self._mid_pitch()
        low = max(_BASS_LOW, self.params.key_range_low)
        clave_hits = _CLAVE_PATTERNS.get(self.clave_type, [])
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pat = (
                self._generate_dynamic_pattern(chord, pattern_data)
                if self.dynamic_pattern
                else pattern_data
            )

            self._emit_pattern_notes(pat, chord, event, mid, clave_hits, notes)

            if self.tumbao_bass:
                notes.extend(
                    _tumbao_bass_line(
                        chord,
                        chords,
                        event.onset,
                        event.duration,
                        low,
                        mid,
                        self.params.density,
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Pattern emission
    # ------------------------------------------------------------------

    def _emit_pattern_notes(
        self,
        pattern: list[tuple[int, float]],
        chord: ChordLabel,
        event: RhythmEvent,
        mid: int,
        clave_hits: list[float],
        notes: list[NoteInfo],
    ) -> None:
        t = event.onset
        pat_t = 0.0
        while pat_t < event.duration:
            for degree, note_dur in pattern:
                if pat_t >= event.duration:
                    break
                actual_dur = min(note_dur, event.duration - pat_t)
                onset = t + pat_t
                pitch = _degree_to_pitch(
                    degree,
                    chord,
                    mid,
                    self.params.key_range_low,
                    self.params.key_range_high,
                )
                vel = _clave_velocity(
                    onset,
                    clave_hits,
                    event.onset,
                    self.params.density,
                )
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=actual_dur * _DURATION_FACTOR,
                        velocity=max(1, min(127, vel)),
                    )
                )
                if self.octave_doubling:
                    notes.append(
                        NoteInfo(
                            pitch=pitch + _OCTAVE,
                            start=round(onset, 6),
                            duration=actual_dur * _DURATION_FACTOR,
                            velocity=max(1, min(127, int(vel * _OCTAVE_VEL_FACTOR))),
                        )
                    )
                pat_t += note_dur
            if pat_t < event.duration:
                pass  # loop

    # ------------------------------------------------------------------
    # Dynamic pattern
    # ------------------------------------------------------------------

    def _generate_dynamic_pattern(
        self,
        chord: ChordLabel,
        fallback: list[tuple[int, float]],
    ) -> list[tuple[int, float]]:
        pcs = chord.pitch_classes()
        if not pcs:
            return fallback

        pattern: list[tuple[int, float]] = []
        t = 0.0
        pat_len = sum(d for _, d in fallback)

        while t < pat_len:
            dur = random.choice(_DYNAMIC_RHYTHMS)
            if t + dur > pat_len:
                dur = pat_len - t
            degree = self._pick_dynamic_degree(pcs)
            pattern.append((degree, dur))
            t += dur
        return pattern

    def _pick_dynamic_degree(self, pcs: list[int]) -> int:
        if random.random() < _DYNAMIC_ROOT_PROB:
            return 1
        if random.random() < _DYNAMIC_FIFTH_PROB:
            return 5 if len(pcs) >= 3 else 3
        return random.choice([3, 5, 8][: len(pcs) + 1])

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _mid_pitch(self) -> int:
        return (self.params.key_range_low + self.params.key_range_high) // 2

    def _cycle_length(self, pattern: list[tuple[int, float]]) -> float:
        if self.clave_type != "none":
            return _CYCLE_LEN
        return sum(d for _, d in pattern)

    def _build_events(self, duration_beats: float, pat_len: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(pat_len, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += pat_len
        return events


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _degree_to_pitch(
    degree: int,
    chord: ChordLabel,
    anchor: int,
    range_low: int,
    range_high: int,
) -> int:
    pcs = chord.pitch_classes()
    if not pcs:
        return anchor
    idx = (degree - 1) % len(pcs)
    octave_shift = (degree - 1) // len(pcs)
    pc = pcs[idx]
    pitch = nearest_pitch(pc, anchor) + octave_shift * _OCTAVE
    return max(range_low, min(range_high, pitch))


def _next_chord(chords: list[ChordLabel], onset: float) -> ChordLabel | None:
    for c in chords:
        if c.start > onset + 0.01:
            return c
    return None


# ---------------------------------------------------------------------------
# Tumbao bass
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _TumbaoCtx:
    """Context for tumbao bass generation."""

    chord: ChordLabel
    chords: list[ChordLabel]
    onset: float
    duration: float
    low: int
    mid: int
    density: float


def _tumbao_bass_line(
    chord: ChordLabel,
    chords: list[ChordLabel],
    onset: float,
    duration: float,
    low: int,
    mid: int,
    density: float,
) -> list[NoteInfo]:
    ctx = _TumbaoCtx(
        chord=chord,
        chords=chords,
        onset=onset,
        duration=duration,
        low=low,
        mid=mid,
        density=density,
    )
    notes: list[NoteInfo] = []
    root_pc = chord.root
    fifth_pc = (root_pc + 7) % _OCTAVE
    bass_high = low + _TUMBAO_BASS_SPAN
    bar_start = (onset // _TUMBAO_BAR_BEATS) * _TUMBAO_BAR_BEATS

    _add_tumbao_hit(
        notes,
        ctx,
        bar_start + _TUMBAO_BEAT4_OFFSET,
        _next_chord(chords, onset),
        bass_high,
    )
    _add_tumbao_syncop(
        notes,
        ctx,
        bar_start + _TUMBAO_BEAT2_OFFSET,
        root_pc,
        fifth_pc,
        bass_high,
    )
    return notes


def _add_tumbao_hit(
    notes: list[NoteInfo],
    ctx: _TumbaoCtx,
    beat: float,
    next_ch: ChordLabel | None,
    bass_high: int,
) -> None:
    if not (ctx.onset <= beat < ctx.onset + ctx.duration):
        return
    target_pc = next_ch.root if next_ch else ctx.chord.root
    pitch = nearest_pitch(target_pc, (ctx.low + ctx.mid) // 2)
    pitch = max(ctx.low, min(bass_high, pitch))
    vel = int(70 + ctx.density * 20)
    notes.append(
        NoteInfo(
            pitch=pitch,
            start=round(beat, 6),
            duration=_TUMBAO_DUR,
            velocity=max(1, min(127, vel)),
        )
    )


def _add_tumbao_syncop(
    notes: list[NoteInfo],
    ctx: _TumbaoCtx,
    beat: float,
    root_pc: int,
    fifth_pc: int,
    bass_high: int,
) -> None:
    if not (ctx.onset <= beat < ctx.onset + ctx.duration):
        return
    hit_pc = random.choice([root_pc, fifth_pc])
    pitch = nearest_pitch(hit_pc, (ctx.low + ctx.mid) // 2)
    pitch = max(ctx.low, min(bass_high, pitch))
    vel = int(65 + ctx.density * 15)
    notes.append(
        NoteInfo(
            pitch=pitch,
            start=round(beat, 6),
            duration=_TUMBAO_DUR,
            velocity=max(1, min(127, vel)),
        )
    )


# ---------------------------------------------------------------------------
# Velocity
# ---------------------------------------------------------------------------


def _clave_velocity(
    onset: float,
    clave_hits: list[float],
    cycle_start: float,
    density: float,
) -> int:
    base = int(60 + density * 30)
    beat_in_cycle = (onset - cycle_start) % _CYCLE_LEN

    for clave_beat in clave_hits:
        if abs(beat_in_cycle - clave_beat) < _CLAVE_TOLERANCE:
            base = min(127, int(base * 1.15))
            break

    if beat_in_cycle % _TUMBAO_BAR_BEATS < _DOWNBEAT_TOLERANCE:
        base = min(127, int(base * 1.05))

    return base
