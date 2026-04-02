# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/chorale.py — Four-part chorale harmonization generator.

Layer: Application / Domain
Style: Bach-style chorale, hymn writing, SATB voice leading.

Generates four simultaneous voices (Soprano, Alto, Tenor, Bass)
with proper voice leading: no parallel fifths/octaves, smooth motion,
proper doubling, leading-tone resolution, and contrary motion preference.

Voices are produced as separate note streams interleaved by onset time.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_at


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_SEMITONES_IN_OCTAVE = 12
_VELOCITY_BASE = 60
_VELOCITY_SCALE = 25
_DURATION_RATIO = 0.9

_BASS_RANGE = (36, 60)
_TENOR_RANGE = (48, 67)
_ALTO_RANGE = (55, 74)
_SOPRANO_RANGE = (60, 84)

_RANGES: dict[str, tuple[int, int]] = {
    "S": _SOPRANO_RANGE,
    "A": _ALTO_RANGE,
    "T": _TENOR_RANGE,
    "B": _BASS_RANGE,
}

_PARALLEL_FORBIDDEN = {0, 7}  # unison/octave, perfect fifth

_DEFAULT_VOICES = {"S": 72, "A": 65, "T": 55, "B": 48}

_VOICE_ORDER = ("B", "T", "A", "S")


# ---------------------------------------------------------------------------
# Voice state helper
# ---------------------------------------------------------------------------


@dataclass
class _VoiceState:
    """Holds the SATB voice pitches and provides copy/merge operations."""

    S: int = 72
    A: int = 65
    T: int = 55
    B: int = 48

    def to_dict(self) -> dict[str, int]:
        return {"S": self.S, "A": self.A, "T": self.T, "B": self.B}

    @classmethod
    def from_dict(cls, d: dict[str, int]) -> _VoiceState:
        return cls(S=d["S"], A=d["A"], T=d["T"], B=d["B"])

    def copy(self) -> _VoiceState:
        return _VoiceState(S=self.S, A=self.A, T=self.T, B=self.B)


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class ChoraleGenerator(PhraseGenerator):
    """
    Four-part chorale harmonization generator.

    Voices: Soprano (highest), Alto, Tenor, Bass (lowest).

    voice_spacing:
        Maximum interval between adjacent voices (in semitones).
    soprano_motion:
        "stepwise" — prefer stepwise soprano line
        "free" — any motion
    rhythmic_unit:
        Duration of each chord in beats (typically 1.0 or 2.0).
    voice_crossing:
        Allow voice crossing (Tenor above Alto).
    doubling_preference:
        "root" — always double root
        "fifth" — double fifth in I and V chords
        "auto" — follow standard doubling rules
    """

    name: str = "Chorale Generator"
    voice_spacing: int = 12
    soprano_motion: str = "stepwise"
    rhythmic_unit: float = 1.0
    voice_crossing: bool = False
    doubling_preference: str = "auto"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voice_spacing: int = 12,
        soprano_motion: str = "stepwise",
        rhythmic_unit: float = 1.0,
        voice_crossing: bool = False,
        doubling_preference: str = "auto",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.voice_spacing = max(6, min(24, voice_spacing))
        self.soprano_motion = soprano_motion
        self.rhythmic_unit = max(0.5, min(4.0, rhythmic_unit))
        self.voice_crossing = voice_crossing
        self.doubling_preference = doubling_preference
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
        prev = _VoiceState()
        last_chord: ChordLabel | None = None
        leading_tone = _leading_tone_pc(key)
        tonic_pc = int(key.degrees()[0]) if key.degrees() else 0

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += self.rhythmic_unit
                continue
            last_chord = chord

            voices = self._build_voices(chord, prev, key, leading_tone, tonic_pc)
            self._emit_chord_notes(voices, t, notes)
            prev = voices
            t += self.rhythmic_unit

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Voice building pipeline
    # ------------------------------------------------------------------

    def _build_voices(
        self,
        chord: ChordLabel,
        prev: _VoiceState,
        key: Scale,
        leading_tone: int | None,
        tonic_pc: int,
    ) -> _VoiceState:
        pcs = chord.pitch_classes()
        root = chord.root

        voices = _assign_voices(pcs, root, prev, key, leading_tone, self.doubling_preference)

        if leading_tone is not None:
            voices = _resolve_leading_tone(voices, prev, leading_tone)

        voices = _apply_contrary_motion(voices, prev, pcs)

        voices = _fix_all_parallels(prev, voices, pcs)

        voices = _enforce_spacing(voices, self.voice_spacing)

        if not self.voice_crossing:
            voices = _enforce_no_crossing(voices)

        return voices

    def _emit_chord_notes(
        self,
        voices: _VoiceState,
        t: float,
        notes: list[NoteInfo],
    ) -> None:
        vel = _velocity(self.params.density)
        dur = self.rhythmic_unit * _DURATION_RATIO
        vd = voices.to_dict()
        for vname in _VOICE_ORDER:
            lo, hi = _RANGES[vname]
            pitch = max(lo, min(hi, vd[vname]))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=dur,
                    velocity=max(1, min(127, vel)),
                )
            )


# ---------------------------------------------------------------------------
# Pure helper functions
# ---------------------------------------------------------------------------


def _leading_tone_pc(key: Scale) -> int | None:
    degs = key.degrees()
    return int(degs[6]) if len(degs) >= 7 else None


def _velocity(density: float) -> int:
    return int(_VELOCITY_BASE + density * _VELOCITY_SCALE)


def _assign_voices(
    pcs: list[int],
    root: int,
    prev: _VoiceState,
    key: Scale,
    leading_tone: int | None,
    doubling_pref: str,
) -> _VoiceState:
    if not pcs:
        return prev.copy()

    bass = _assign_bass(root, prev.B)
    double_pc = _choose_doubling_pc(root, pcs, leading_tone, doubling_pref)
    upper_pcs = _build_upper_pcs(pcs, root, double_pc, leading_tone)

    tenor = _assign_tenor(upper_pcs, prev.T)
    alto = _assign_alto(upper_pcs, tenor, prev.A)
    soprano = _assign_soprano(upper_pcs, alto, prev.S, double_pc)

    return _VoiceState(S=soprano, A=alto, T=tenor, B=bass)


def _assign_bass(root: int, prev_bass: int) -> int:
    p = nearest_pitch(root, prev_bass)
    return max(_BASS_RANGE[0], min(_BASS_RANGE[1], p))


def _choose_doubling_pc(
    root: int,
    pcs: list[int],
    leading_tone: int | None,
    doubling_pref: str,
) -> int:
    if leading_tone is not None and root == leading_tone:
        return pcs[2] if len(pcs) >= 3 else (pcs[1] if len(pcs) >= 2 else root)
    if doubling_pref == "fifth" and len(pcs) >= 3:
        return pcs[2]
    return root


def _build_upper_pcs(
    pcs: list[int],
    root: int,
    double_pc: int,
    leading_tone: int | None,
) -> list[int]:
    non_root = [pc for pc in pcs if pc != root]
    if len(pcs) >= 3:
        upper = [double_pc] + non_root[:2]
    elif len(pcs) == 2:
        upper = [double_pc] + pcs
    else:
        upper = [double_pc, double_pc, double_pc]

    if leading_tone is not None:
        upper = _limit_leading_tone_doubling(upper, leading_tone, root, pcs)
    return upper


def _limit_leading_tone_doubling(
    upper: list[int],
    lt: int,
    root: int,
    pcs: list[int],
) -> list[int]:
    count = sum(1 for pc in upper if pc == lt)
    if count <= 1:
        return upper
    result = list(upper)
    for i in range(len(result)):
        if result[i] == lt and count > 1:
            result[i] = root if root != lt else (pcs[1] if len(pcs) > 1 else root)
            count -= 1
    return result


def _assign_tenor(upper_pcs: list[int], prev_t: int) -> int:
    candidates = [nearest_pitch(int(pc), prev_t) for pc in upper_pcs]
    candidates = [p for p in candidates if _TENOR_RANGE[0] <= p <= _TENOR_RANGE[1]]
    if not candidates:
        candidates = [nearest_pitch(int(upper_pcs[0]), prev_t)]
    return min(candidates, key=lambda p: abs(p - prev_t))


def _assign_alto(upper_pcs: list[int], tenor: int, prev_a: int) -> int:
    remaining = list(upper_pcs)
    used_pc = tenor % _SEMITONES_IN_OCTAVE
    if used_pc in remaining:
        remaining.remove(used_pc)
    if len(remaining) < 2:
        remaining.append(upper_pcs[0])

    candidates = [nearest_pitch(int(pc), prev_a) for pc in remaining]
    candidates = [p for p in candidates if _ALTO_RANGE[0] <= p <= _ALTO_RANGE[1] and p > tenor]
    if not candidates:
        candidates = [max(_ALTO_RANGE[0], tenor + 3)]
    return min(candidates, key=lambda p: abs(p - prev_a))


def _assign_soprano(
    upper_pcs: list[int],
    alto: int,
    prev_s: int,
    doubling_pc: int,
) -> int:
    remaining = list(upper_pcs)
    used_pc = alto % _SEMITONES_IN_OCTAVE
    if used_pc in remaining:
        remaining.remove(used_pc)
    if not remaining:
        remaining = [doubling_pc]

    candidates = [nearest_pitch(int(pc), prev_s) for pc in remaining]
    candidates = [p for p in candidates if _SOPRANO_RANGE[0] <= p <= _SOPRANO_RANGE[1] and p > alto]
    if candidates:
        return min(candidates, key=lambda p: abs(p - prev_s))
    p = nearest_pitch(int(remaining[0]), prev_s)
    return max(_SOPRANO_RANGE[0], min(_SOPRANO_RANGE[1], p))


# ---------------------------------------------------------------------------
# Voice-leading corrections
# ---------------------------------------------------------------------------


def _resolve_leading_tone(
    voices: _VoiceState,
    prev: _VoiceState,
    lt: int,
) -> _VoiceState:
    result = voices.copy()
    vd = result.to_dict()
    pv = prev.to_dict()
    for vname in _VOICE_ORDER:
        if pv[vname] % _SEMITONES_IN_OCTAVE == lt:
            target = pv[vname] + 1
            lo, hi = _RANGES[vname]
            if lo <= target <= hi:
                vd[vname] = target
    return _VoiceState.from_dict(vd)


def _apply_contrary_motion(
    voices: _VoiceState,
    prev: _VoiceState,
    pcs: list[int],
) -> _VoiceState:
    sop_dir = voices.S - prev.S
    bass_dir = voices.B - prev.B
    if sop_dir == 0 or bass_dir == 0:
        return voices
    if (sop_dir > 0) != (bass_dir > 0):
        return voices
    alt = _nudge_contrary(voices.B, prev.B, pcs, _BASS_RANGE, sop_dir)
    if alt is None:
        return voices
    result = voices.copy()
    result.B = alt
    return result


def _nudge_contrary(
    current: int,
    prev: int,
    pcs: list[int],
    pitch_range: tuple[int, int],
    soprano_dir: int,
) -> int | None:
    desired = -1 if soprano_dir > 0 else 1
    for step in (1, 2, 3):
        candidate = prev + desired * step
        if pitch_range[0] <= candidate <= pitch_range[1]:
            if (candidate % _SEMITONES_IN_OCTAVE) in pcs:
                return candidate
    return None


def _fix_all_parallels(
    prev: _VoiceState,
    curr: _VoiceState,
    pcs: list[int],
) -> _VoiceState:
    result = curr.to_dict()
    pv = prev.to_dict()

    for i in range(len(_VOICE_ORDER)):
        for j in range(i + 1, len(_VOICE_ORDER)):
            v1, v2 = _VOICE_ORDER[i], _VOICE_ORDER[j]
            if _is_parallel_motion(pv, result, v1, v2):
                _fix_parallel_pair(result, pv, pcs, v1, v2)

    return _VoiceState.from_dict(result)


def _is_parallel_motion(
    prev: dict[str, int],
    curr: dict[str, int],
    v1: str,
    v2: str,
) -> bool:
    prev_ivl = abs(prev[v2] - prev[v1]) % _SEMITONES_IN_OCTAVE
    curr_ivl = abs(curr[v2] - curr[v1]) % _SEMITONES_IN_OCTAVE
    if prev_ivl not in _PARALLEL_FORBIDDEN:
        return False
    if curr_ivl != prev_ivl:
        return False
    d1 = curr[v1] - prev[v1]
    d2 = curr[v2] - prev[v2]
    return (d1 > 0 and d2 > 0) or (d1 < 0 and d2 < 0)


def _fix_parallel_pair(
    voices: dict[str, int],
    prev: dict[str, int],
    pcs: list[int],
    v1: str,
    v2: str,
) -> None:
    lo, hi = _RANGES[v2]
    d2 = voices[v2] - prev[v2]
    nudge = 1 if d2 >= 0 else -1

    # Strategy 1: nudge upper voice toward a chord tone
    for sign in (nudge, -nudge):
        new_pitch = voices[v2] + sign
        if lo <= new_pitch <= hi:
            if (new_pitch % _SEMITONES_IN_OCTAVE) in pcs:
                voices[v2] = new_pitch
                return

    # Strategy 2: nudge lower voice
    lo1, hi1 = _RANGES[v1]
    for sign in (-nudge, nudge):
        new_low = voices[v1] + sign
        if lo1 <= new_low <= hi1:
            if (new_low % _SEMITONES_IN_OCTAVE) in pcs:
                voices[v1] = new_low
                return

    # Strategy 3: find any non-forbidden chord tone
    for pc in pcs:
        candidate = nearest_pitch(pc, voices[v2])
        if lo <= candidate <= hi:
            ivl = abs(candidate - voices[v1]) % _SEMITONES_IN_OCTAVE
            if ivl not in _PARALLEL_FORBIDDEN:
                voices[v2] = candidate
                return


def _enforce_spacing(
    voices: _VoiceState,
    max_spacing: int,
) -> _VoiceState:
    result = voices.copy()
    if result.S - result.A > max_spacing:
        result.S = result.A + max_spacing
    if result.A - result.T > max_spacing:
        result.A = result.T + max_spacing
    return result


def _enforce_no_crossing(voices: _VoiceState) -> _VoiceState:
    result = voices.copy()
    if result.T >= result.A:
        result.A = result.T + 1
    if result.A >= result.S:
        result.S = result.A + 1
    return result
