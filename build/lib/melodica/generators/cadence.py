"""
generators/cadence.py — Cadential formula generator.

Layer: Application / Domain
Style: All tonal music.

Cadences are the punctuation marks of music. This generator produces
cadential formulas that can end or punctuate phrases.

Cadence types:
    "PAC"           — Perfect Authentic Cadence (V->I, soprano on root)
    "IAC"           — Imperfect Authentic Cadence (V->I, other voicing)
    "plagal"        — Plagal Cadence (IV->I)
    "deceptive"     — Deceptive Cadence (V->vi)
    "half"          — Half Cadence (->V)
    "backdoor"      — Backdoor ii-V (bVII->I)
    "phrygian"      — Phrygian half cadence (iv6->V)
    "neapolitan"    — Neapolitan sixth -> V -> I
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

_SEMITONES = 12
_BASS_RANGE = (36, 60)
_TENOR_RANGE = (48, 69)
_ALTO_RANGE = (55, 76)
_SOPRANO_RANGE = (60, 84)

_VOICE_RANGES = [_BASS_RANGE, _TENOR_RANGE, _ALTO_RANGE, _SOPRANO_RANGE]

_PARALLEL_FORBIDDEN = {0, 7}

_STEP_PREFERENCE_BONUS = 0.5
_DOUBLING_PENALTY = 0.3


# ---------------------------------------------------------------------------
# Internal context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _VoiceLeadCtx:
    """Immutable context passed through voice-leading steps."""

    prev: list[int]
    new_pcs: list[int]
    lt_pc: int | None
    tonic_pc: int
    chord: ChordLabel
    is_dominant: bool
    is_last: bool


@dataclass(frozen=True)
class _VoicingCtx:
    """Context for SATB voicing generation."""

    chord: ChordLabel
    onset: float
    dur: float
    prev: list[int] | None
    is_last: bool
    is_dominant: bool
    lt_pc: int | None
    tonic_pc: int
    cadence_type: str
    melodic_approach: str
    voice_count: int


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class CadenceGenerator(PhraseGenerator):
    """
    Cadential formula generator with proper voice leading.

    cadence_type:
        One of the cadence types listed above.
    voice_count:
        Number of voices (2-4).
    cadence_length:
        Duration of the cadence in beats.
    melodic_approach:
        "stepwise" — soprano approaches by step
        "leap" — soprano approaches by leap
        "free" — any approach
    cadential_64:
        For PAC/IAC: include cadential 6/4 before dominant.
    """

    name: str = "Cadence Generator"
    cadence_type: str = "PAC"
    voice_count: int = 4
    cadence_length: float = 2.0
    melodic_approach: str = "stepwise"
    cadential_64: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        cadence_type: str = "PAC",
        voice_count: int = 4,
        cadence_length: float = 2.0,
        melodic_approach: str = "stepwise",
        cadential_64: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.cadence_type = cadence_type
        self.voice_count = max(2, min(4, voice_count))
        self.cadence_length = max(1.0, min(8.0, cadence_length))
        self.melodic_approach = melodic_approach
        self.cadential_64 = cadential_64
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
        last_chord: ChordLabel | None = None
        prev_voicing: list[int] | None = None

        for event in self._build_events(duration_beats):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            cadence_chords = self._cadence_pair(chord, key)
            prev_voicing = self._render_cadence_chords(
                cadence_chords,
                key,
                event.onset,
                duration_beats,
                prev_voicing,
                notes,
            )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_cadence_chords(
        self,
        cadence_chords: list[ChordLabel],
        key: Scale,
        start: float,
        total_dur: float,
        prev_voicing: list[int] | None,
        notes: list[NoteInfo],
    ) -> list[int] | None:
        dur_each = self.cadence_length / len(cadence_chords)
        t = start
        degs = key.degrees()
        lt_pc = int(degs[6]) if len(degs) >= 7 else None
        tonic_pc = int(degs[0]) if degs else 0

        for ci, cc in enumerate(cadence_chords):
            if t >= total_dur:
                break
            dur = min(dur_each, total_dur - t)
            is_last = ci == len(cadence_chords) - 1
            is_dom = _is_dominant(cc, key)

            vc = _VoicingCtx(
                chord=cc,
                onset=t,
                dur=dur,
                prev=prev_voicing,
                is_last=is_last,
                is_dominant=is_dom,
                lt_pc=lt_pc,
                tonic_pc=tonic_pc,
                cadence_type=self.cadence_type,
                melodic_approach=self.melodic_approach,
                voice_count=self.voice_count,
            )
            chord_notes, voicing = self._voicings_satb(vc)
            notes.extend(chord_notes)
            prev_voicing = voicing
            t += dur_each
        return prev_voicing

    # ------------------------------------------------------------------
    # Cadence chord progressions
    # ------------------------------------------------------------------

    def _cadence_pair(self, current: ChordLabel, key: Scale) -> list[ChordLabel]:
        degs = key.degrees()
        root = current.root
        dom_pc = degs[4] if len(degs) > 4 else (root + 7) % _SEMITONES
        tonic_pc = int(degs[0]) if degs else root

        dom7 = ChordLabel(root=int(dom_pc), quality=Quality.DOMINANT7)
        dom_triad = ChordLabel(root=int(dom_pc), quality=Quality.MAJOR)
        tonic = ChordLabel(root=tonic_pc, quality=current.quality)

        ct = self.cadence_type
        if ct == "PAC":
            return self._maybe_cad64(dom7, tonic, dom7, tonic_pc)
        if ct == "IAC":
            return self._maybe_cad64(dom7, tonic, dom7, tonic_pc)
        if ct == "plagal":
            sd_pc = degs[3] if len(degs) > 3 else (root + 5) % _SEMITONES
            sd = ChordLabel(root=int(sd_pc), quality=Quality.MAJOR)
            return [sd, tonic]
        if ct == "deceptive":
            vi_pc = degs[5] if len(degs) > 5 else (root + 9) % _SEMITONES
            vi = ChordLabel(root=int(vi_pc), quality=Quality.MINOR)
            return [dom7, vi]
        if ct == "half":
            return [dom_triad]
        if ct == "backdoor":
            bvii = ChordLabel(root=(root + 10) % _SEMITONES, quality=Quality.MAJOR)
            return [bvii, tonic]
        if ct == "phrygian":
            sd_pc = degs[3] if len(degs) > 3 else (root + 5) % _SEMITONES
            iv = ChordLabel(root=int(sd_pc), quality=Quality.MINOR)
            return [iv, dom_triad]
        if ct == "neapolitan":
            bii = ChordLabel(root=(tonic_pc + 1) % _SEMITONES, quality=Quality.MAJOR)
            return [bii, dom7, tonic]
        return [dom7, tonic]

    def _maybe_cad64(
        self,
        dom: ChordLabel,
        tonic: ChordLabel,
        fallback_dom: ChordLabel,
        tonic_pc: int,
    ) -> list[ChordLabel]:
        if self.cadential_64:
            cad64 = ChordLabel(
                root=tonic_pc,
                quality=Quality.MAJOR,
                bass=fallback_dom.root,
            )
            return [cad64, dom, tonic]
        return [dom, tonic]

    # ------------------------------------------------------------------
    # SATB voicing
    # ------------------------------------------------------------------

    def _voicings_satb(
        self,
        vc: _VoicingCtx,
    ) -> tuple[list[NoteInfo], list[int]]:
        pcs = vc.chord.pitch_classes()
        if not pcs:
            return [], []

        voicing = _build_voicing(pcs, vc)
        voicing = _apply_soprano_constraints(voicing, pcs, vc)
        voicing = voicing[: vc.voice_count]

        notes = [
            NoteInfo(
                pitch=max(0, min(127, p)),
                start=round(vc.onset, 6),
                duration=vc.dur * 0.9,
                velocity=max(1, min(127, _velocity(self.params.density))),
            )
            for p in voicing
        ]
        return notes, voicing

    # ------------------------------------------------------------------
    # Rhythm
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=self.cadence_length))
            t += self.cadence_length + random.uniform(2.0, 4.0)
        return events


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _is_dominant(chord: ChordLabel, key: Scale) -> bool:
    degs = key.degrees()
    if len(degs) > 4:
        return chord.root == int(degs[4])
    return (chord.root - key.root) % _SEMITONES == 7


def _velocity(density: float) -> int:
    return int(60 + density * 30)


def _seventh_pc(chord: ChordLabel) -> int | None:
    """Return the pitch class of the dominant seventh, or None."""
    for pc in chord.pitch_classes():
        ivl = (pc - chord.root) % _SEMITONES
        if ivl in (10, 11):
            return pc
    return None


def _initial_voicing(pcs: list[int], root: int) -> list[int]:
    bass = nearest_pitch(root, 48)
    bass = max(_BASS_RANGE[0], min(_BASS_RANGE[1], bass))

    tenor_pc = pcs[2 % len(pcs)] if len(pcs) > 2 else pcs[0]
    tenor = nearest_pitch(int(tenor_pc), 55)
    tenor = max(_TENOR_RANGE[0], min(_TENOR_RANGE[1], tenor))

    alto_pc = pcs[1 % len(pcs)] if len(pcs) > 1 else pcs[0]
    alto = nearest_pitch(int(alto_pc), 64)
    alto = max(_ALTO_RANGE[0], min(_ALTO_RANGE[1], alto))
    if alto <= tenor:
        alto = tenor + 3

    sop_pc = pcs[0]
    soprano = nearest_pitch(int(sop_pc), 72)
    soprano = max(_SOPRANO_RANGE[0], min(_SOPRANO_RANGE[1], soprano))
    if soprano <= alto:
        soprano = alto + 3

    return [bass, tenor, alto, soprano]


def _build_voicing(pcs: list[int], vc: _VoicingCtx) -> list[int]:
    if vc.prev and len(vc.prev) >= vc.voice_count:
        ctx = _VoiceLeadCtx(
            prev=vc.prev,
            new_pcs=pcs,
            lt_pc=vc.lt_pc,
            tonic_pc=vc.tonic_pc,
            chord=vc.chord,
            is_dominant=vc.is_dominant,
            is_last=vc.is_last,
        )
        return _voice_lead(ctx)
    return _initial_voicing(pcs, vc.chord.root)


# ---------------------------------------------------------------------------
# Voice-leading pipeline
# ---------------------------------------------------------------------------


def _voice_lead(ctx: _VoiceLeadCtx) -> list[int]:
    n = min(len(ctx.prev), 4)
    seventh = _seventh_pc(ctx.chord)
    assigned_pcs: set[int] = set()
    result: list[int] = []

    for i in range(n):
        pitch = _lead_voice_single(ctx, i, result, assigned_pcs, seventh)
        result.append(pitch)
        assigned_pcs.add(pitch % _SEMITONES)

    _enforce_ascending(result)
    return result


def _lead_voice_single(
    ctx: _VoiceLeadCtx,
    i: int,
    result: list[int],
    assigned_pcs: set[int],
    seventh: int | None,
) -> int:
    prev_pitch = ctx.prev[i]
    lo, hi = _VOICE_RANGES[i] if i < len(_VOICE_RANGES) else (36, 84)

    # Rule 1: leading tone resolves up
    if ctx.lt_pc is not None and (prev_pitch % _SEMITONES) == ctx.lt_pc:
        resolved = prev_pitch + 1
        if lo <= resolved <= hi:
            return resolved

    # Rule 2: seventh resolves down
    if seventh is not None and (prev_pitch % _SEMITONES) == seventh:
        if not ctx.is_last:
            resolved = prev_pitch - 1
            if lo <= resolved <= hi and (resolved % _SEMITONES) in ctx.new_pcs:
                return resolved

    # Rule 3: nearest chord tone (prefer stepwise)
    pitch = _nearest_chord_tone(prev_pitch, ctx.new_pcs, lo, hi, assigned_pcs)

    # Rule 4: avoid parallels
    pitch = _avoid_parallels(pitch, i, ctx, result)

    return pitch


def _nearest_chord_tone(
    prev_pitch: int,
    new_pcs: list[int],
    lo: int,
    hi: int,
    assigned_pcs: set[int],
) -> int:
    best = prev_pitch
    best_dist = 999.0
    for pc in new_pcs:
        cand = nearest_pitch(int(pc), prev_pitch)
        cand = max(lo, min(hi, cand))
        dist = float(abs(cand - prev_pitch))
        if dist <= 2:
            dist -= _STEP_PREFERENCE_BONUS
        if (cand % _SEMITONES) in assigned_pcs:
            dist += _DOUBLING_PENALTY
        if dist < best_dist:
            best_dist = dist
            best = cand
    return best


def _avoid_parallels(
    pitch: int,
    i: int,
    ctx: _VoiceLeadCtx,
    result: list[int],
) -> int:
    for j in range(len(result)):
        prev_ivl = abs(ctx.prev[j] - ctx.prev[i]) % _SEMITONES
        curr_ivl = abs(result[j] - pitch) % _SEMITONES
        d_i = pitch - ctx.prev[i]
        d_j = result[j] - ctx.prev[j]
        same_dir = (d_i > 0 and d_j > 0) or (d_i < 0 and d_j < 0)
        if not same_dir:
            continue
        if curr_ivl not in _PARALLEL_FORBIDDEN:
            continue
        if prev_ivl != curr_ivl:
            continue
        lo, hi = _VOICE_RANGES[i] if i < len(_VOICE_RANGES) else (36, 84)
        nudge = 1 if d_i >= 0 else -1
        for pc in ctx.new_pcs:
            alt = nearest_pitch(int(pc), pitch + nudge)
            alt = max(lo, min(hi, alt))
            if abs(alt - result[j]) % _SEMITONES not in _PARALLEL_FORBIDDEN:
                return alt
    return pitch


def _enforce_ascending(result: list[int]) -> None:
    for i in range(1, len(result)):
        if result[i] <= result[i - 1]:
            result[i] = result[i - 1] + 1
            if i < len(_VOICE_RANGES):
                result[i] = min(result[i], _VOICE_RANGES[i][1])


# ---------------------------------------------------------------------------
# Soprano constraints
# ---------------------------------------------------------------------------


def _apply_soprano_constraints(
    voicing: list[int],
    pcs: list[int],
    vc: _VoicingCtx,
) -> list[int]:
    if not voicing or len(voicing) < 4:
        return voicing

    result = list(voicing)
    is_last = vc.is_last
    tonic_pc = vc.tonic_pc
    ct = vc.cadence_type
    ma = vc.melodic_approach
    prev = vc.prev

    if is_last and ct == "PAC":
        target = nearest_pitch(tonic_pc, result[-1])
        target = max(_SOPRANO_RANGE[0], min(_SOPRANO_RANGE[1], target))
        result[-1] = target

    if is_last and ct == "IAC":
        sop_pc = result[-1] % _SEMITONES
        if sop_pc == tonic_pc and len(pcs) > 1:
            alt_pc = pcs[1]
            result[-1] = nearest_pitch(alt_pc, result[-1])
            result[-1] = max(
                _SOPRANO_RANGE[0],
                min(_SOPRANO_RANGE[1], result[-1]),
            )

    if is_last and ma == "stepwise" and prev:
        prev_sop = prev[-1]
        curr_sop = result[-1]
        if abs(curr_sop - prev_sop) > 2:
            for pc in pcs:
                cand = nearest_pitch(pc, prev_sop)
                if abs(cand - prev_sop) <= 2:
                    in_range = _SOPRANO_RANGE[0] <= cand <= _SOPRANO_RANGE[1]
                    if in_range:
                        result[-1] = cand
                        break

    return result
