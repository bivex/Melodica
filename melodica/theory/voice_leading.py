# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.theory.voice_leading — Unified voice leading rules, SATB engine, and parallel correction.

Layer: Core / Theory
Unifies voice leading logic across the framework:
- Detection of parallel fifths, octaves, and voice motion classification
- SATB 4-voice leading engine with beam search and strict classical constraints
- Post-generation multi-track grid parallel motion corrector (Aldwell & Schachter §11)
- Voice leading distance and smoothness cost calculation
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from melodica.types import ChordLabel, NoteInfo, Scale

# ---------------------------------------------------------------------------
# SATB Voice ranges (MIDI pitches)
# ---------------------------------------------------------------------------
VOICE_RANGES: dict[str, tuple[int, int]] = {
    "soprano": (60, 81),  # C4 - A5
    "alto": (53, 74),     # F3 - D5
    "tenor": (45, 69),    # A2 - C4 (written)
    "bass": (36, 60),     # C2 - C4
}

VOICE_ORDER: list[str] = ["soprano", "alto", "tenor", "bass"]


# ---------------------------------------------------------------------------
# GM comfortable pitch ranges per program number
# ---------------------------------------------------------------------------
GM_RANGES: dict[int, tuple[int, int]] = {
    # Strings
    40: (55, 103),   # Violin
    41: (48, 91),    # Viola
    42: (36, 79),    # Cello
    43: (28, 60),    # Contrabass
    44: (40, 84),    # Tremolo Strings
    45: (36, 79),    # Pizzicato Strings
    48: (48, 84),    # String Ensemble 1
    49: (48, 84),    # String Ensemble 2
    # Choir
    52: (48, 81),    # Choir Aahs
    53: (48, 81),    # Voice Oohs
    # Brass
    56: (52, 82),    # Trumpet
    57: (36, 72),    # Trombone
    58: (28, 58),    # Tuba
    60: (36, 77),    # French Horn
    61: (36, 77),    # Brass Section
    # Woodwinds
    68: (58, 91),    # Oboe
    71: (50, 91),    # Clarinet
    73: (60, 96),    # Flute
    # Keyboards / Pitched Percussion
    9: (72, 108),    # Glockenspiel
    11: (60, 96),    # Vibraphone
    12: (36, 96),    # Marimba
    13: (60, 84),    # Xylophone
    # Harp / Piano
    0: (21, 108),    # Piano
    46: (24, 103),   # Orchestral Harp
    47: (36, 60),    # Timpani
    # Synth / Pads
    38: (24, 60),    # Synth Bass 1
    39: (24, 60),    # Synth Bass 2
    80: (55, 108),   # Synth Lead 1
    81: (55, 108),   # Synth Lead 2
    88: (48, 96),    # Pad 1 (New Age)
    89: (48, 96),    # Pad 2 (Warm)
    92: (48, 96),    # Pad 5 (Bowed)
}

DEFAULT_RANGE: tuple[int, int] = (24, 108)

# Backward-compatibility alias
_GM_RANGE = GM_RANGES
_DEFAULT_RANGE = DEFAULT_RANGE


def get_instrument_range(program: int | None) -> tuple[int, int]:
    """Retrieve playable MIDI register bounds for GM program number."""
    if program is None:
        return DEFAULT_RANGE
    return GM_RANGES.get(program, DEFAULT_RANGE)


_get_range = get_instrument_range


# ---------------------------------------------------------------------------
# Pure Theory Functions
# ---------------------------------------------------------------------------
def pitch_class(pitch: int) -> int:
    """Return pitch class 0..11."""
    return pitch % 12


_pitch_class = pitch_class


def interval(a: int, b: int) -> int:
    """Semitone interval from a to b (positive = upward motion)."""
    return b - a


_interval = interval


def is_parallel_fifth(prev_a: int, prev_b: int, curr_a: int, curr_b: int) -> bool:
    """Check if motion between two voices forms parallel fifths."""
    prev_int = abs(prev_a - prev_b) % 12
    curr_int = abs(curr_a - curr_b) % 12
    if prev_int == 7 and curr_int == 7:
        dir_a = 1 if curr_a > prev_a else (-1 if curr_a < prev_a else 0)
        dir_b = 1 if curr_b > prev_b else (-1 if curr_b < prev_b else 0)
        if dir_a == dir_b and dir_a != 0:
            return True
    return False


_is_parallel_fifth = is_parallel_fifth


def is_parallel_octave(prev_a: int, prev_b: int, curr_a: int, curr_b: int) -> bool:
    """Check if motion between two voices forms parallel octaves or unisons."""
    prev_int = abs(prev_a - prev_b) % 12
    curr_int = abs(curr_a - curr_b) % 12
    if prev_int == 0 and curr_int == 0:
        dir_a = 1 if curr_a > prev_a else (-1 if curr_a < prev_a else 0)
        dir_b = 1 if curr_b > prev_b else (-1 if curr_b < prev_b else 0)
        if dir_a == dir_b and dir_a != 0:
            return True
    return False


_is_parallel_octave = is_parallel_octave


def classify_motion(prev_a: int, prev_b: int, curr_a: int, curr_b: int) -> str:
    """Classify 2-voice motion: parallel, contrary, oblique, or similar."""
    dir_a = 1 if curr_a > prev_a else (-1 if curr_a < prev_a else 0)
    dir_b = 1 if curr_b > prev_b else (-1 if curr_b < prev_b else 0)
    if dir_a == 0 or dir_b == 0:
        return "oblique"
    if (dir_a > 0 and dir_b < 0) or (dir_a < 0 and dir_b > 0):
        return "contrary"
    if curr_a - prev_a == curr_b - prev_b:
        return "parallel"
    return "similar"


def _motion_type(a: int, b: int) -> str:
    """Legacy alias used in composer voice leading."""
    return "oblique" if a == b else "parallel"


def has_parallel_motion(prev_voicing: Sequence[int], curr_voicing: Sequence[int]) -> bool:
    """Check all voice pairs between two voicings for parallel fifths or octaves."""
    n = min(len(prev_voicing), len(curr_voicing))
    for i in range(n):
        for j in range(i + 1, n):
            if is_parallel_fifth(prev_voicing[i], prev_voicing[j], curr_voicing[i], curr_voicing[j]):
                return True
            if is_parallel_octave(prev_voicing[i], prev_voicing[j], curr_voicing[i], curr_voicing[j]):
                return True
    return False


def voice_leading_distance(
    voicing1: Sequence[int],
    voicing2: Sequence[int],
    p: float = 2.0,
) -> float:
    """
    Compute voice leading distance (L_p norm) between two pitch voicings.
    Tymoczko / Callender-Quinn-Tymoczko metric.
    """
    if not voicing1 or not voicing2:
        return 0.0
    n = min(len(voicing1), len(voicing2))
    diffs = [abs(voicing1[i] - voicing2[i]) for i in range(n)]
    if p == 1.0:
        return float(sum(diffs))
    if p == 2.0:
        return math.sqrt(sum(d * d for d in diffs))
    return sum(d**p for d in diffs) ** (1.0 / p)


# ---------------------------------------------------------------------------
# SATB Voice Leading Engine
# ---------------------------------------------------------------------------
@dataclass
class _VoiceSearchContext:
    chord: ChordLabel
    pcs: list[int]
    prev_voicing: list[int]
    candidates: list[tuple[float, list[int]]]


@dataclass
class VoiceLeadingEngine:
    """
    SATB voice leading engine.

    Takes chord progressions and produces 4-voice voicings with proper
    voice leading: no parallel fifths/octaves, minimal motion, proper ranges.

    beam_width: number of beam candidates to keep per step.
        beam_width=1 reproduces the legacy pairwise greedy behaviour.
        beam_width>1 enables proper beam search for globally better voice leading.
    """

    strict_mode: bool = True
    max_voice_gap: int = 12
    beam_width: int = 3

    def voicize_progression(
        self,
        chords: list[ChordLabel],
        scale: Scale,
    ) -> dict[str, list[NoteInfo]]:
        """
        Convert chord progression to 4-voice SATB voicing.
        Returns dict with keys: 'soprano', 'alto', 'tenor', 'bass'.
        """
        if not chords:
            return {v: [] for v in VOICE_ORDER}

        if self.beam_width <= 1:
            return self._voicize_greedy(chords, scale, VOICE_ORDER)

        best_voicings = self._beam_search(chords, scale)
        if not best_voicings:
            return self._voicize_greedy(chords, scale, VOICE_ORDER)

        return self._build_satb_notes(chords, best_voicings)

    def _beam_search(self, chords: list[ChordLabel], scale: Scale) -> list[list[int]]:
        first_voicing = self._best_initial_voicing(chords[0], scale)
        beams: list[tuple[float, list[list[int]]]] = [(0.0, [first_voicing])]

        for i in range(1, len(chords)):
            new_beams = self._expand_beams(beams, chords[i], scale)
            if not new_beams:
                new_beams = self._expand_beams_relaxed(beams, chords[i], scale)
            new_beams.sort(key=lambda x: -x[0])
            beams = new_beams[: self.beam_width]

        return beams[0][1] if beams else []

    def _expand_beams(
        self,
        beams: list[tuple[float, list[list[int]]]],
        chord: ChordLabel,
        scale: Scale,
    ) -> list[tuple[float, list[list[int]]]]:
        new_beams: list[tuple[float, list[list[int]]]] = []
        for score, path in beams:
            prev_v = path[-1]
            candidates = self._generate_candidates(chord, scale, prev_v)
            for cand in candidates:
                if self.strict_mode and self._has_parallels(prev_v, cand):
                    continue
                step_score = self._score_voicing(prev_v, cand)
                new_beams.append((score + step_score, path + [cand]))
        return new_beams

    def _expand_beams_relaxed(
        self,
        beams: list[tuple[float, list[list[int]]]],
        chord: ChordLabel,
        scale: Scale,
    ) -> list[tuple[float, list[list[int]]]]:
        new_beams: list[tuple[float, list[list[int]]]] = []
        for score, path in beams:
            prev_v = path[-1]
            candidates = self._generate_candidates(chord, scale, prev_v)
            for cand in candidates:
                step_score = self._score_voicing(prev_v, cand)
                new_beams.append((score + step_score, path + [cand]))
        return new_beams

    def _build_satb_notes(
        self,
        chords: list[ChordLabel],
        best_voicings: list[list[int]],
    ) -> dict[str, list[NoteInfo]]:
        from melodica.types import NoteInfo
        result: dict[str, list[NoteInfo]] = {}
        for vi, voice in enumerate(VOICE_ORDER):
            notes = [
                NoteInfo(
                    pitch=best_voicings[ci][vi],
                    start=round(chord.start, 6),
                    duration=chord.duration,
                    velocity=80,
                )
                for ci, chord in enumerate(chords)
            ]
            result[voice] = notes
        return result

    def _has_parallels(self, prev: list[int], curr: list[int]) -> bool:
        return has_parallel_motion(prev, curr)

    def _voicize_greedy(
        self,
        chords: list[ChordLabel],
        scale: Scale,
        voice_names: list[str],
    ) -> dict[str, list[NoteInfo]]:
        voices: dict[str, list[int]] = {}
        first_voicing = self._best_initial_voicing(chords[0], scale)
        for i, vn in enumerate(voice_names):
            voices[vn] = [first_voicing[i]]

        for i in range(1, len(chords)):
            prev_voicing = [voices[vn][-1] for vn in voice_names]
            candidates = self._generate_candidates(chords[i], scale, prev_voicing)
            best = self._select_best(prev_voicing, candidates)
            for j, vn in enumerate(voice_names):
                voices[vn].append(best[j])

        from melodica.types import NoteInfo
        result: dict[str, list[NoteInfo]] = {}
        for voice in voice_names:
            notes = []
            for i, chord in enumerate(chords):
                pitch = voices[voice][i]
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(chord.start, 6),
                        duration=chord.duration,
                        velocity=80,
                    )
                )
            result[voice] = notes
        return result

    def _best_initial_voicing(self, chord: ChordLabel, scale: Scale) -> list[int]:
        root = chord.root
        pcs = chord.pitch_classes()
        if not pcs:
            return [72, 64, 55, 36]

        sop = self._nearest_in_range(pcs[0], VOICE_RANGES["soprano"])
        alt = self._nearest_in_range(pcs[min(1, len(pcs) - 1)], VOICE_RANGES["alto"])
        ten = self._nearest_in_range(pcs[min(2, len(pcs) - 1)], VOICE_RANGES["tenor"])
        bass = self._nearest_in_range(root, VOICE_RANGES["bass"])

        if ten >= alt:
            ten -= 12
        if alt >= sop:
            alt -= 12

        sop = max(VOICE_RANGES["soprano"][0], min(VOICE_RANGES["soprano"][1], sop))
        alt = max(VOICE_RANGES["alto"][0], min(VOICE_RANGES["alto"][1], alt))
        ten = max(VOICE_RANGES["tenor"][0], min(VOICE_RANGES["tenor"][1], ten))
        bass = max(VOICE_RANGES["bass"][0], min(VOICE_RANGES["bass"][1], bass))

        return [sop, alt, ten, bass]

    def _is_valid_candidate(self, cand: list[int]) -> bool:
        sop, alt, ten, bass = cand
        if not (sop >= alt >= ten >= bass):
            return False
        return not (
            abs(sop - alt) > self.max_voice_gap
            or abs(alt - ten) > self.max_voice_gap
            or abs(ten - bass) > self.max_voice_gap
        )

    def _generate_candidates(
        self,
        chord: ChordLabel,
        scale: Scale,
        prev_voicing: list[int],
    ) -> list[list[int]]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [prev_voicing]

        candidates: list[tuple[float, list[int]]] = []
        ctx = _VoiceSearchContext(chord, pcs, prev_voicing, candidates)
        bass_range = VOICE_RANGES["bass"]
        bass_pitches = self._all_in_range(chord.root, bass_range) or [self._nearest_in_range(chord.root, bass_range)]

        for bass in bass_pitches:
            self._collect_candidates_for_bass(bass, ctx)

        if not candidates:
            return [self._best_initial_voicing(chord, scale)]

        candidates.sort(key=lambda x: -x[0])
        return self._deduplicate_candidates(candidates)

    def _collect_candidates_for_bass(
        self,
        bass: int,
        ctx: _VoiceSearchContext,
    ) -> None:
        sop_range = VOICE_RANGES["soprano"]
        for sop_pc in ctx.pcs:
            sop_pitches = self._all_in_range(sop_pc, sop_range) or [self._nearest_in_range(sop_pc, sop_range)]
            for sop in sop_pitches:
                if sop >= bass:
                    self._collect_inner_voices(bass, sop, ctx)

    def _collect_inner_voices(
        self,
        bass: int,
        sop: int,
        ctx: _VoiceSearchContext,
    ) -> None:
        alt_range = VOICE_RANGES["alto"]
        ten_range = VOICE_RANGES["tenor"]
        for alt_pc in ctx.pcs:
            alt_pitches = self._all_in_range(alt_pc, alt_range) or [self._nearest_in_range(alt_pc, alt_range)]
            for alt in alt_pitches:
                if not (sop >= alt >= bass):
                    continue
                for ten_pc in ctx.pcs:
                    ten_pitches = self._all_in_range(ten_pc, ten_range) or [self._nearest_in_range(ten_pc, ten_range)]
                    for ten in ten_pitches:
                        cand = [sop, alt, ten, bass]
                        if self._is_valid_candidate(cand):
                            ctx.candidates.append((self._score_voicing(ctx.prev_voicing, cand), cand))

    def _deduplicate_candidates(self, candidates: list[tuple[float, list[int]]], limit: int = 12) -> list[list[int]]:
        unique_cands: list[list[int]] = []
        seen = set()
        for _, c in candidates:
            key = tuple(c)
            if key not in seen:
                seen.add(key)
                unique_cands.append(c)
                if len(unique_cands) >= limit:
                    break
        return unique_cands

    def _select_best(
        self,
        prev: list[int],
        candidates: list[list[int]],
    ) -> list[int]:
        for candidate in candidates:
            if self.strict_mode and self._has_parallels(prev, candidate):
                continue
            return candidate
        return candidates[0] if candidates else prev

    def _score_voicing(self, prev: list[int], curr: list[int]) -> float:
        score = 0.0
        for i in range(4):
            motion = abs(curr[i] - prev[i])
            if motion == 0:
                score += 2.0
            elif motion <= 2:
                score += 1.0
            elif motion <= 4:
                score += 0.4
            elif motion <= 7:
                score -= 0.5
            else:
                score -= 1.5

        if (curr[0] > prev[0] and curr[3] < prev[3]) or (curr[0] < prev[0] and curr[3] > prev[3]):
            score += 1.2
        elif (curr[0] == prev[0]) or (curr[3] == prev[3]):
            score += 0.5

        inner_motion = abs(curr[1] - prev[1]) + abs(curr[2] - prev[2])
        score -= inner_motion * 0.1
        return score

    def _all_in_range(self, pc: int, voice_range: tuple[int, int]) -> list[int]:
        lo, hi = voice_range
        return [p for p in range(lo, hi + 1) if p % 12 == pc % 12]

    def _nearest_in_range(self, pc: int, voice_range: tuple[int, int]) -> int:
        lo, hi = voice_range
        candidates = self._all_in_range(pc, voice_range)
        if candidates:
            mid = (lo + hi) // 2
            return min(candidates, key=lambda p: abs(p - mid))
        pitch = lo + (pc - lo % 12) % 12
        while pitch > hi:
            pitch -= 12
        return max(lo, pitch)


# ---------------------------------------------------------------------------
# Grid-based post-generation parallel correction
# ---------------------------------------------------------------------------
_SAMPLE = 0.25
_MIN_INSTANCES = 1


def _note_with_pitch(note: NoteInfo, new_pitch: int) -> NoteInfo:
    """Return a copy of note with pitch replaced."""
    from melodica.types import NoteInfo as _NI
    return _NI(
        pitch=new_pitch,
        start=note.start,
        duration=note.duration,
        velocity=note.velocity,
        absolute=note.absolute,
        articulation=note.articulation,
        expression=dict(note.expression) if note.expression else {},
    )


def _build_track_index(notes: list[NoteInfo]) -> dict[int, int]:
    idx: dict[int, int] = {}
    for i, n in enumerate(notes):
        t_start = float(n.start)
        t_end = t_start + float(n.duration)
        slot_s = int(t_start / _SAMPLE)
        slot_e = max(slot_s + 1, int(t_end / _SAMPLE))
        for slot in range(slot_s, slot_e):
            if slot not in idx or int(notes[idx[slot]].pitch) > int(n.pitch):
                idx[slot] = i
    return idx


def _find_parallel_slots(
    idx_a: dict[int, int],
    idx_b: dict[int, int],
    notes_a: list[NoteInfo],
    notes_b: list[NoteInfo],
) -> list[tuple[int, int, bool]]:
    common = sorted(set(idx_a) & set(idx_b))
    slots: list[tuple[int, int, bool]] = []
    for k in range(len(common) - 1):
        s0, s1 = common[k], common[k + 1]
        if s1 - s0 > 4:
            continue
        pa0, pa1 = int(notes_a[idx_a[s0]].pitch), int(notes_a[idx_a[s1]].pitch)
        pb0, pb1 = int(notes_b[idx_b[s0]].pitch), int(notes_b[idx_b[s1]].pitch)
        raw0, raw1 = abs(pa0 - pb0), abs(pa1 - pb1)
        is_fifth = (raw0 % 12 == 7 and raw1 % 12 == 7)
        is_octave = (raw0 in {0, 12, 24} and raw1 in {0, 12, 24})
        if not (is_fifth or is_octave):
            continue
        move_a, move_b = pa1 - pa0, pb1 - pb0
        if move_a == 0 and move_b == 0:
            continue
        if (move_a >= 0) == (move_b >= 0):
            slots.append((s0, s1, is_octave))
    return slots


def _resolve_parallel_shift(
    result: dict[str, list[NoteInfo]],
    indexes: dict[str, dict[int, int]],
    slot_info: tuple[int, int, bool],
    names: tuple[str, str],
    ranges: tuple[tuple[int, int], tuple[int, int]],
) -> None:
    _, s1, _ = slot_info
    name_a, name_b = names
    (lo_a, hi_a), (lo_b, hi_b) = ranges

    idx_a, idx_b = indexes[name_a], indexes[name_b]
    pa1 = int(result[name_a][idx_a[s1]].pitch)
    pb1 = int(result[name_b][idx_b[s1]].pitch)

    if pa1 >= pb1:
        u_name, u_idx, lo_u, hi_u, lower_pitch = name_a, idx_a[s1], lo_a, hi_a, pb1
    else:
        u_name, u_idx, lo_u, hi_u, lower_pitch = name_b, idx_b[s1], lo_b, hi_b, pa1

    upper_note = result[u_name][u_idx]
    up = int(upper_note.pitch)

    for shift in (12, -12):
        candidate = up + shift
        if lo_u <= candidate <= hi_u:
            new_raw = abs(candidate - lower_pitch)
            if new_raw % 12 != 7 and new_raw not in {0, 12, 24}:
                result[u_name][u_idx] = _note_with_pitch(upper_note, candidate)
                indexes[u_name] = _build_track_index(result[u_name])
                break


def _correct_pair_parallels(
    name_a: str,
    name_b: str,
    indexes: dict[str, dict[int, int]],
    result: dict[str, list[NoteInfo]],
    instr: dict[str, int],
) -> None:
    slots = _find_parallel_slots(indexes[name_a], indexes[name_b], result[name_a], result[name_b])
    if len(slots) < _MIN_INSTANCES:
        return
    rng_a = get_instrument_range(instr.get(name_a))
    rng_b = get_instrument_range(instr.get(name_b))
    for slot_info in slots:
        _resolve_parallel_shift(result, indexes, slot_info, (name_a, name_b), (rng_a, rng_b))


def correct_parallels(
    tracks_data: dict[str, list[NoteInfo]],
    instruments: dict[str, int] | None = None,
) -> dict[str, list[NoteInfo]]:
    """Return a corrected copy of tracks_data with parallel 5ths/8ths resolved."""
    from melodica.form_validator import _is_percussion

    result: dict[str, list[NoteInfo]] = {
        name: list(notes) for name, notes in tracks_data.items()
    }
    pitched_names = [n for n in result if not n.startswith("_") and not _is_percussion(n) and result[n]]
    if len(pitched_names) < 2:
        return result

    instr = instruments or {}
    indexes = {name: _build_track_index(result[name]) for name in pitched_names}

    for i, name_a in enumerate(pitched_names):
        for name_b in pitched_names[i + 1:]:
            _correct_pair_parallels(name_a, name_b, indexes, result, instr)

    return result
