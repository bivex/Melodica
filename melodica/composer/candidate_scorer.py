"""
composer/candidate_scorer.py — Generalized multi-candidate scoring.

Layer: Domain / Application
Style: All styles — universal evolutionary selection infrastructure.

Instead of committing to a single-note decision, generators can
produce N candidates, score them on multiple criteria, and select
the best one. This mimics evolutionary composition.

Usage:
    scorer = CandidateScorer()
    best_note = scorer.pick_best(
        candidates=[note1, note2, note3, ...],
        context=ScoringContext(prev_pitch=72, chord_root=0, ...),
    )

Or use the convenience function:
    best = pick_best_note(
        candidates, prev_pitch=72, chord_root=0,
        quality=Quality.MAJOR, scale_pcs=[0,2,4,5,7,9,11],
    )
"""

from __future__ import annotations

import random as _random
from dataclasses import dataclass, field
from typing import Callable

from melodica.types import NoteInfo, Quality
from melodica.composer.harmonic_awareness import weight_pitch


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12

# Default weights for scoring criteria
_W_SMOOTHNESS = 0.30  # Prefer stepwise motion
_W_HARMONY = 0.30  # Prefer chord tones / avoid notes
_W_CONTOUR = 0.15  # Prefer nice contour shape
_W_RANGE = 0.10  # Penalize extreme registers
_W_NOVELTY = 0.15  # Prefer notes not recently used


# ---------------------------------------------------------------------------
# Scoring context
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoringContext:
    """Context for scoring melodic note candidates."""

    prev_pitch: int | None = None
    chord_root: int = 0
    chord_quality: Quality = Quality.MAJOR
    scale_pcs: list[int] = field(default_factory=lambda: list(range(12)))
    beat_strength: float = 1.0
    recent_pitches: list[int] = field(default_factory=list)
    preferred_contour: str = ""  # "ascending", "descending", "arch", ""
    low: int = 36
    high: int = 96


# ---------------------------------------------------------------------------
# Scorer
# ---------------------------------------------------------------------------


@dataclass
class CandidateScorer:
    """
    Generalized multi-candidate scorer.

    Produces N candidates via a generator function, scores each on
    multiple weighted criteria, returns the best.

    weights:
        Dict of criterion → weight (0.0–1.0). Sum should be ≤ 1.0.
    """

    weights: dict[str, float] = field(
        default_factory=lambda: {
            "smoothness": _W_SMOOTHNESS,
            "harmony": _W_HARMONY,
            "contour": _W_CONTOUR,
            "range": _W_RANGE,
            "novelty": _W_NOVELTY,
        }
    )

    def score(
        self,
        pitch: int,
        ctx: ScoringContext,
    ) -> float:
        """Score a single pitch candidate (0.0–1.0)."""
        scores: dict[str, float] = {}

        # Smoothness: prefer small intervals
        scores["smoothness"] = _score_smoothness(pitch, ctx.prev_pitch)

        # Harmony: prefer chord tones, penalize avoid notes
        scores["harmony"] = _score_harmony(pitch, ctx)

        # Contour: prefer notes that fit the desired contour
        scores["contour"] = _score_contour(pitch, ctx)

        # Range: penalize extreme registers
        scores["range"] = _score_range(pitch, ctx.low, ctx.high)

        # Novelty: penalize recently repeated notes
        scores["novelty"] = _score_novelty(pitch, ctx.recent_pitches)

        # Weighted sum
        total = 0.0
        total_weight = 0.0
        for criterion, weight in self.weights.items():
            if criterion in scores:
                total += scores[criterion] * weight
                total_weight += weight

        return total / max(total_weight, 0.01)

    def pick_best(
        self,
        candidates: list[int],
        ctx: ScoringContext,
    ) -> int:
        """Score all candidates and return the best one."""
        if not candidates:
            return ctx.prev_pitch or 60
        if len(candidates) == 1:
            return candidates[0]

        scored = [(p, self.score(p, ctx)) for p in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        # Add small randomization to top 3 to avoid mechanical patterns
        top_n = min(3, len(scored))
        top = scored[:top_n]
        # Weighted random among top candidates
        pitches = [p for p, _ in top]
        weights = [s for _, s in top]
        return _random.choices(pitches, weights=weights, k=1)[0]

    def pick_best_note(
        self,
        candidates: list[NoteInfo],
        ctx: ScoringContext,
    ) -> NoteInfo:
        """Score NoteInfo candidates and return the best one."""
        if not candidates:
            return NoteInfo(pitch=60, start=0, duration=0.5, velocity=80)
        if len(candidates) == 1:
            return candidates[0]

        scored = [(n, self.score(n.pitch, ctx)) for n in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)

        top_n = min(3, len(scored))
        top = scored[:top_n]
        notes = [n for n, _ in top]
        weights = [s for _, s in top]
        return _random.choices(notes, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Convenience function
# ---------------------------------------------------------------------------


def pick_best_note(
    candidates: list[int],
    prev_pitch: int | None = None,
    chord_root: int = 0,
    quality: Quality = Quality.MAJOR,
    scale_pcs: list[int] | None = None,
    beat_strength: float = 1.0,
    recent_pitches: list[int] | None = None,
    low: int = 36,
    high: int = 96,
) -> int:
    """Convenience: score candidates and return the best pitch."""
    ctx = ScoringContext(
        prev_pitch=prev_pitch,
        chord_root=chord_root,
        chord_quality=quality,
        scale_pcs=scale_pcs or list(range(12)),
        beat_strength=beat_strength,
        recent_pitches=recent_pitches or [],
        low=low,
        high=high,
    )
    scorer = CandidateScorer()
    return scorer.pick_best(candidates, ctx)


# ---------------------------------------------------------------------------
# Individual scoring functions
# ---------------------------------------------------------------------------


def _score_smoothness(pitch: int, prev_pitch: int | None) -> float:
    """Prefer small intervals (stepwise motion)."""
    if prev_pitch is None:
        return 0.8
    interval = abs(pitch - prev_pitch)
    if interval == 0:
        return 0.5  # repetition is OK but not ideal
    if interval <= 2:
        return 1.0  # step
    if interval <= 4:
        return 0.8  # small leap
    if interval <= 7:
        return 0.5  # leap
    if interval <= 12:
        return 0.2  # large leap
    return 0.05  # extreme


def _score_harmony(pitch: int, ctx: ScoringContext) -> float:
    """Prefer chord tones, penalize avoid notes."""
    return weight_pitch(pitch, ctx.chord_root, ctx.chord_quality, ctx.beat_strength)


def _score_contour(pitch: int, ctx: ScoringContext) -> float:
    """Prefer notes that fit the desired melodic contour."""
    if not ctx.preferred_contour or ctx.prev_pitch is None:
        return 0.5

    diff = pitch - ctx.prev_pitch
    direction = "up" if diff > 0 else ("down" if diff < 0 else "same")

    if ctx.preferred_contour == "ascending":
        return 0.9 if direction == "up" else (0.3 if direction == "same" else 0.1)
    if ctx.preferred_contour == "descending":
        return 0.9 if direction == "down" else (0.3 if direction == "same" else 0.1)
    if ctx.preferred_contour == "arch":
        # In arch, prefer ascending in first half, descending in second
        # We don't know position here, so just prefer motion over stasis
        return 0.7 if direction != "same" else 0.3
    return 0.5


def _score_range(pitch: int, low: int, high: int) -> float:
    """Prefer middle register, penalize extremes."""
    if pitch < low or pitch > high:
        return 0.0
    mid = (low + high) / 2
    half_range = (high - low) / 2
    distance_from_center = abs(pitch - mid) / max(half_range, 1)
    return max(0.0, 1.0 - distance_from_center * 0.5)


def _score_novelty(pitch: int, recent: list[int]) -> float:
    """Prefer notes not recently used."""
    if not recent:
        return 0.8
    pc = pitch % _OCTAVE
    recent_pcs = [r % _OCTAVE for r in recent[-8:]]  # last 8 notes
    if pc not in recent_pcs:
        return 1.0
    count = recent_pcs.count(pc)
    return max(0.2, 1.0 - count * 0.3)
