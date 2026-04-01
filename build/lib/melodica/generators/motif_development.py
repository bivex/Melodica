"""
generators/motif_development.py — Motif transformation and development generator.

Layer: Application / Domain
Style: Classical, film scoring, contemporary composition.

Transformations:
    "original"             — the motif as generated
    "inversion"            — intervals reversed in direction
    "retrograde"           — notes played backwards
    "retrograde_inversion" — backwards AND inverted
    "augmentation"         — durations doubled
    "diminution"           — durations halved
    "sequence_up"          — diatonic transposition up
    "sequence_down"        — diatonic transposition down
    "transposition"        — chromatic transposition by N semitones
    "pitch_class_inversion" — TnI operation

Development styles:
    "sequential"   — transformations applied one after another
    "fragmented"   — only parts of the motif used per transformation
    "continuous"   — transformations overlap and interleave
    "stretto"      — overlapping entries at compressed intervals
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12
_HALF_STEP = 6
_CHORD_TONE_PROB = 0.55
_ARCH_HALF = "arch"
_DURATION_OPTIONS = [0.25, 0.5, 0.5, 1.0, 1.0, 2.0]
_CONTOUR_SHAPES = ["arch", "ascending", "descending", "zigzag"]
_STEP_CHOICES = [-3, -2, -1, 0, 1, 2, 3]
_FRAGMENT_FRACTION = 0.5
_OVERLAP_FRACTION = 0.5
_DURATION_RATIO = 0.85
_VELOCITY_BOOST_ORIG = 1.1
_VELOCITY_BOOST_FAST = 1.15
_VELOCITY_BOOST_STRETTO = 1.2

_VALID_TRANSFORMS = frozenset(
    {
        "original",
        "inversion",
        "retrograde",
        "retrograde_inversion",
        "augmentation",
        "diminution",
        "sequence_up",
        "sequence_down",
        "transposition",
        "pitch_class_inversion",
    }
)

_VALID_STYLES = frozenset({"sequential", "fragmented", "continuous", "stretto"})


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class MotifDevelopmentGenerator(PhraseGenerator):
    """
    Motif transformation and development generator.

    transformations:
        List of transformation names to apply.
    motif_length:
        Number of notes in the generated motif.
    development_style:
        How transformations are arranged.
    transposition_semitones:
        Semitones for "transposition" transform.
    inversion_pivot:
        Pivot pitch class for "pitch_class_inversion".
    """

    name: str = "Motif Development Generator"
    transformations: list[str] = field(
        default_factory=lambda: ["original", "inversion", "retrograde"]
    )
    motif_length: int = 4
    development_style: str = "sequential"
    transposition_semitones: int = 5
    inversion_pivot: int | None = None
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        transformations: list[str] | None = None,
        motif_length: int = 4,
        development_style: str = "sequential",
        transposition_semitones: int = 5,
        inversion_pivot: int | None = None,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.transformations = (
            transformations
            if transformations is not None
            else ["original", "inversion", "retrograde"]
        )
        self.motif_length = max(2, min(12, motif_length))
        if development_style not in _VALID_STYLES:
            raise ValueError(
                f"development_style must be one of {_VALID_STYLES}; got {development_style!r}"
            )
        self.development_style = development_style
        self.transposition_semitones = max(-12, min(12, transposition_semitones))
        self.inversion_pivot = inversion_pivot
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

        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        pitches, durations = self._generate_motif(chords[0], anchor, low, high, key)
        if self.inversion_pivot is None and pitches:
            self.inversion_pivot = pitches[0] % _OCTAVE

        all_notes: list[NoteInfo] = []
        t = 0.0
        last_chord: ChordLabel | None = None

        for xi, xname in enumerate(self.transformations):
            xp, xd = self._apply_transform(xname, pitches, durations, key)
            xp, xd = self._apply_style(xp, xd, xi, all_notes, t)
            t = self._emit_notes(
                xp,
                xd,
                chords,
                low,
                high,
                xname,
                duration_beats,
                t,
                all_notes,
            )

        all_notes.sort(key=lambda n: n.start)

        if all_notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=all_notes[-1].pitch,
                last_velocity=all_notes[-1].velocity,
                last_chord=last_chord,
            )
        return all_notes

    # ------------------------------------------------------------------
    # Motif generation
    # ------------------------------------------------------------------

    def _generate_motif(
        self,
        chord: ChordLabel,
        anchor: int,
        low: int,
        high: int,
        key: Scale,
    ) -> tuple[list[int], list[float]]:
        contour = random.choice(_CONTOUR_SHAPES)
        pcs = chord.pitch_classes()
        degs = key.degrees()
        pitches: list[int] = []
        durations: list[float] = []

        for i in range(self.motif_length):
            direction = _contour_direction(contour, i, self.motif_length)
            pc = self._pick_motif_pc(i, pcs, degs, chord.root)
            base = pitches[-1] + direction * random.choice([0, 1, 2]) if pitches else anchor
            pitch = nearest_pitch(pc, base)
            pitch = max(low, min(high, pitch))
            pitches.append(pitch)
            durations.append(random.choice(_DURATION_OPTIONS))

        return pitches, durations

    def _pick_motif_pc(
        self,
        i: int,
        pcs: list[int],
        degs: list,
        root: int,
    ) -> int:
        if i == 0 and pcs:
            return int(random.choice(pcs))
        if random.random() < _CHORD_TONE_PROB and pcs:
            return int(random.choice(pcs))
        if degs:
            return int(random.choice(degs))
        return root

    # ------------------------------------------------------------------
    # Style application
    # ------------------------------------------------------------------

    def _apply_style(
        self,
        pitches: list[int],
        durations: list[float],
        xform_idx: int,
        all_notes: list[NoteInfo],
        t: float,
    ) -> tuple[list[int], list[float]]:
        style = self.development_style
        if style == "fragmented":
            return _fragment(pitches, durations)
        if style == "continuous":
            return pitches, durations  # t adjusted in _emit_notes
        if style == "stretto":
            return pitches, durations  # t adjusted in _emit_notes
        return pitches, durations

    # ------------------------------------------------------------------
    # Note emission
    # ------------------------------------------------------------------

    def _emit_notes(
        self,
        pitches: list[int],
        durations: list[float],
        chords: list[ChordLabel],
        low: int,
        high: int,
        xform_name: str,
        duration_beats: float,
        t: float,
        all_notes: list[NoteInfo],
    ) -> float:
        if self.development_style == "continuous" and all_notes:
            t = max(0.0, t - durations[0] * _OVERLAP_FRACTION)
        elif self.development_style == "stretto" and all_notes:
            overlap = sum(durations) * _OVERLAP_FRACTION
            t = max(0.0, t - overlap)

        for pitch, dur in zip(pitches, durations):
            if t >= duration_beats:
                break
            chord = chord_at(chords, t)
            if chord is None:
                t += dur
                continue
            pcs = chord.pitch_classes()
            if pcs:
                nearest_pc = min(pcs, key=lambda p: abs(int(p) - (pitch % _OCTAVE)))
                pitch = nearest_pitch(int(nearest_pc), pitch)
            pitch = max(low, min(high, pitch))

            vel = _xform_velocity(xform_name, self.params.density)
            all_notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=dur * _DURATION_RATIO,
                    velocity=max(1, min(127, vel)),
                )
            )
            t += dur
        return t

    # ------------------------------------------------------------------
    # Transforms
    # ------------------------------------------------------------------

    def _apply_transform(
        self,
        name: str,
        pitches: list[int],
        durations: list[float],
        key: Scale,
    ) -> tuple[list[int], list[float]]:
        if name == "original":
            return list(pitches), list(durations)
        if name == "inversion":
            return _invert(pitches), list(durations)
        if name == "retrograde":
            return list(reversed(pitches)), list(reversed(durations))
        if name == "retrograde_inversion":
            inv = _invert(pitches)
            return list(reversed(inv)), list(reversed(durations))
        if name == "augmentation":
            return list(pitches), [d * 2.0 for d in durations]
        if name == "diminution":
            return list(pitches), [max(0.25, d * 0.5) for d in durations]
        if name == "sequence_up":
            return _diatonic_seq(pitches, key, up=True), list(durations)
        if name == "sequence_down":
            return _diatonic_seq(pitches, key, up=False), list(durations)
        if name == "transposition":
            tr = [max(0, min(127, p + self.transposition_semitones)) for p in pitches]
            return tr, list(durations)
        if name == "pitch_class_inversion":
            pivot = self.inversion_pivot if self.inversion_pivot is not None else 0
            return _pc_invert(pitches, pivot), list(durations)
        return list(pitches), list(durations)


# ---------------------------------------------------------------------------
# Pure transform functions
# ---------------------------------------------------------------------------


def _invert(pitches: list[int]) -> list[int]:
    if len(pitches) < 2:
        return list(pitches)
    result = [pitches[0]]
    for i in range(1, len(pitches)):
        interval = pitches[i] - pitches[i - 1]
        result.append(max(0, min(127, result[-1] - interval)))
    return result


def _diatonic_seq(pitches: list[int], key: Scale, up: bool) -> list[int]:
    degs = key.degrees()
    if not degs:
        return list(pitches)
    result = []
    for p in pitches:
        pc = p % _OCTAVE
        idx = min(
            range(len(degs)),
            key=lambda i: abs(int(degs[i]) - pc),
        )
        next_deg = degs[(idx + (1 if up else -1)) % len(degs)]
        shift = (int(next_deg) - pc) % _OCTAVE
        if shift > _HALF_STEP:
            shift -= _OCTAVE
        result.append(max(0, min(127, p + shift)))
    return result


def _pc_invert(pitches: list[int], pivot: int) -> list[int]:
    result = []
    for p in pitches:
        pc = p % _OCTAVE
        new_pc = (2 * pivot - pc) % _OCTAVE
        octave = p // _OCTAVE
        result.append(max(0, min(127, octave * _OCTAVE + new_pc)))
    return result


def _fragment(pitches: list[int], durations: list[float]) -> tuple[list[int], list[float]]:
    frag_len = max(1, len(pitches) // 2)
    start = random.randint(0, max(0, len(pitches) - frag_len))
    return pitches[start : start + frag_len], durations[start : start + frag_len]


# ---------------------------------------------------------------------------
# Contour and velocity
# ---------------------------------------------------------------------------


def _contour_direction(shape: str, i: int, length: int) -> int:
    if shape == "arch":
        return 1 if i < length // 2 else -1
    if shape == "ascending":
        return 1
    if shape == "descending":
        return -1
    return 1 if i % 2 == 0 else -1  # zigzag


def _xform_velocity(xform_name: str, density: float) -> int:
    base = int(60 + density * 30)
    if xform_name == "original":
        return min(127, int(base * _VELOCITY_BOOST_ORIG))
    if xform_name in ("diminution", "retrograde_inversion"):
        return min(127, int(base * _VELOCITY_BOOST_FAST))
    return base
