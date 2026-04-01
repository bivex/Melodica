"""
rhythm/markov_rhythm.py — Markov-chain rhythm generator.

Layer: Application / Domain
Style: All styles — rhythmic variety through probabilistic transitions.

Uses a first-order Markov chain on duration categories to generate
rhythmically coherent but varied patterns. States are duration values
(eighth, quarter, half, etc.); transitions determine what duration
follows what.

Features:
  - Pre-built transition matrices for common styles
  - Metric hierarchy (downbeat/weak beat awareness)
  - Syncopation probability
  - Phrase boundary lengthening (last note of phrase is longer)
  - Trainable from existing rhythm patterns
"""

from __future__ import annotations

import random as _random
from dataclasses import dataclass, field

from melodica.rhythm import RhythmEvent, RhythmGenerator


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Standard duration categories (beats)
DUR_SIXTEENTH = 0.25
DUR_EIGHTH = 0.5
DUR_DOTTED_EIGHTH = 0.75
DUR_QUARTER = 1.0
DUR_DOTTED_QUARTER = 1.5
DUR_HALF = 2.0
DUR_WHOLE = 4.0

_ALL_DURATIONS = [
    DUR_SIXTEENTH,
    DUR_EIGHTH,
    DUR_DOTTED_EIGHTH,
    DUR_QUARTER,
    DUR_DOTTED_QUARTER,
    DUR_HALF,
    DUR_WHOLE,
]

_DURATION_LABELS = {
    0.25: "16th",
    0.5: "8th",
    0.75: "d8th",
    1.0: "quarter",
    1.5: "dquarter",
    2.0: "half",
    4.0: "whole",
}

# Pre-built transition matrices: duration → {next_duration: probability}
# These favour stepwise rhythm changes (e.g., 8th→8th or 8th→quarter)

TRANSITION_STRAIGHT: dict[float, dict[float, float]] = {
    0.25: {0.25: 0.5, 0.5: 0.3, 1.0: 0.15, 2.0: 0.05},
    0.5: {0.5: 0.4, 0.25: 0.2, 1.0: 0.3, 2.0: 0.1},
    0.75: {1.0: 0.4, 0.5: 0.3, 1.5: 0.2, 2.0: 0.1},
    1.0: {1.0: 0.3, 0.5: 0.3, 0.25: 0.1, 2.0: 0.2, 0.75: 0.1},
    1.5: {1.0: 0.3, 0.5: 0.3, 1.5: 0.2, 2.0: 0.2},
    2.0: {2.0: 0.3, 1.0: 0.3, 0.5: 0.2, 4.0: 0.2},
    4.0: {1.0: 0.4, 0.5: 0.3, 2.0: 0.2, 4.0: 0.1},
}

TRANSITION_SWING: dict[float, dict[float, float]] = {
    0.25: {0.25: 0.3, 0.5: 0.4, 0.75: 0.2, 1.0: 0.1},
    0.5: {0.5: 0.3, 0.25: 0.2, 0.75: 0.2, 1.0: 0.2, 1.5: 0.1},
    0.75: {0.5: 0.3, 0.25: 0.3, 1.0: 0.2, 1.5: 0.2},
    1.0: {1.0: 0.2, 0.5: 0.3, 0.75: 0.2, 1.5: 0.2, 2.0: 0.1},
    1.5: {0.5: 0.3, 1.0: 0.3, 0.75: 0.2, 2.0: 0.2},
    2.0: {1.0: 0.3, 0.5: 0.2, 1.5: 0.2, 2.0: 0.2, 4.0: 0.1},
    4.0: {1.0: 0.3, 0.5: 0.3, 1.5: 0.2, 2.0: 0.2},
}

TRANSITION_BALLAD: dict[float, dict[float, float]] = {
    0.25: {0.25: 0.3, 0.5: 0.4, 1.0: 0.2, 2.0: 0.1},
    0.5: {0.5: 0.2, 1.0: 0.4, 0.25: 0.1, 2.0: 0.2, 1.5: 0.1},
    0.75: {1.0: 0.4, 1.5: 0.3, 0.5: 0.2, 2.0: 0.1},
    1.0: {1.0: 0.3, 2.0: 0.3, 1.5: 0.2, 0.5: 0.1, 4.0: 0.1},
    1.5: {2.0: 0.3, 1.0: 0.3, 1.5: 0.2, 4.0: 0.2},
    2.0: {2.0: 0.3, 4.0: 0.3, 1.0: 0.2, 1.5: 0.2},
    4.0: {2.0: 0.4, 1.0: 0.3, 4.0: 0.2, 1.5: 0.1},
}

TRANSITION_DRIVING: dict[float, dict[float, float]] = {
    0.25: {0.25: 0.6, 0.5: 0.3, 1.0: 0.1},
    0.5: {0.5: 0.5, 0.25: 0.3, 1.0: 0.15, 0.75: 0.05},
    0.75: {0.5: 0.4, 0.25: 0.3, 1.0: 0.2, 0.75: 0.1},
    1.0: {1.0: 0.3, 0.5: 0.4, 0.25: 0.2, 2.0: 0.1},
    1.5: {1.0: 0.3, 0.5: 0.4, 0.25: 0.2, 1.5: 0.1},
    2.0: {1.0: 0.4, 0.5: 0.3, 2.0: 0.2, 0.25: 0.1},
    4.0: {1.0: 0.4, 0.5: 0.3, 2.0: 0.2, 0.25: 0.1},
}

STYLE_MATRICES: dict[str, dict[float, dict[float, float]]] = {
    "straight": TRANSITION_STRAIGHT,
    "swing": TRANSITION_SWING,
    "ballad": TRANSITION_BALLAD,
    "driving": TRANSITION_DRIVING,
}


# ---------------------------------------------------------------------------
# Generator
# ---------------------------------------------------------------------------


@dataclass
class MarkovRhythmGenerator(RhythmGenerator):
    """
    Markov-chain rhythm generator with metric hierarchy.

    States are duration values (0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 4.0).
    Transitions determine what duration follows what.

    style:
        "straight", "swing", "ballad", "driving", or "custom"
    transitions:
        Custom transition matrix (overrides style if set)
    syncopation:
        Probability of placing notes on weak offbeats (0.0–1.0)
    phrase_length:
        Number of notes per phrase. Last note gets lengthening.
    downbeat_preference:
        Extra probability weight for notes starting on downbeats
    seed:
        RNG seed for reproducibility
    """

    style: str = "straight"
    transitions: dict[float, dict[float, float]] | None = None
    syncopation: float = 0.15
    phrase_length: int = 8
    downbeat_preference: float = 0.3
    seed: int | None = None

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if duration_beats <= 0:
            return []

        rng = _random.Random(self.seed)
        trans = self._get_transitions()
        events: list[RhythmEvent] = []

        t = 0.0
        current_dur = DUR_QUARTER  # start with quarter note
        note_idx = 0

        while t < duration_beats - 0.001:
            # Get duration from Markov chain
            if note_idx > 0:
                current_dur = _sample_next(current_dur, trans, rng)

            # Phrase boundary: lengthen last note of phrase
            is_phrase_end = self.phrase_length > 0 and (note_idx + 1) % self.phrase_length == 0
            if is_phrase_end:
                current_dur = min(current_dur * 1.5, DUR_HALF)

            # Clamp to remaining duration
            actual_dur = min(current_dur, duration_beats - t)

            # Metric position
            beat_pos = t % 4.0
            is_downbeat = beat_pos < 0.1 or abs(beat_pos - 4.0) < 0.1
            is_upbeat = (beat_pos % 1.0) > 0.4 and (beat_pos % 1.0) < 0.6

            # Velocity based on metric hierarchy
            vel = _metric_velocity(is_downbeat, is_upbeat)

            # Syncopation: occasional weak-beat hits with accent
            if not is_downbeat and not is_upbeat and rng.random() < self.syncopation:
                vel = max(vel, 0.75)

            events.append(
                RhythmEvent(
                    onset=round(t, 6),
                    duration=round(actual_dur, 6),
                    velocity_factor=vel,
                )
            )

            t += actual_dur
            note_idx += 1

        return events

    def _get_transitions(self) -> dict[float, dict[float, float]]:
        if self.transitions is not None:
            return self.transitions
        return STYLE_MATRICES.get(self.style, TRANSITION_STRAIGHT)

    @classmethod
    def train_from_durations(
        cls,
        durations: list[float],
        style_name: str = "custom",
    ) -> dict[float, dict[float, float]]:
        """
        Learn a transition matrix from observed duration sequences.

        durations: list of note durations (e.g., from a MIDI file)
        Returns a transition matrix usable as `transitions` parameter.
        """
        if len(durations) < 2:
            return dict(TRANSITION_STRAIGHT)

        # Quantize durations to nearest standard
        quantized = [_quantize_dur(d) for d in durations]

        # Count transitions
        counts: dict[float, dict[float, int]] = {}
        for i in range(len(quantized) - 1):
            prev = quantized[i]
            curr = quantized[i + 1]
            if prev not in counts:
                counts[prev] = {}
            counts[prev][curr] = counts[prev].get(curr, 0) + 1

        # Normalize to probabilities
        result: dict[float, dict[float, float]] = {}
        for prev, nexts in counts.items():
            total = sum(nexts.values())
            result[prev] = {curr: count / total for curr, count in nexts.items()}

        # Fill missing transitions with defaults
        default = TRANSITION_STRAIGHT
        for dur in _ALL_DURATIONS:
            if dur not in result:
                result[dur] = dict(default.get(dur, {DUR_QUARTER: 1.0}))

        return result


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------


def _sample_next(
    current: float,
    transitions: dict[float, dict[float, float]],
    rng: _random.Random,
) -> float:
    """Sample next duration from transition probabilities."""
    probs = transitions.get(current)
    if not probs:
        return DUR_QUARTER

    durations = list(probs.keys())
    weights = list(probs.values())
    return rng.choices(durations, weights=weights, k=1)[0]


def _metric_velocity(is_downbeat: bool, is_upbeat: bool) -> float:
    if is_downbeat:
        return 1.0
    if is_upbeat:
        return 0.85
    return 0.7


def _quantize_dur(dur: float) -> float:
    """Quantize a duration to nearest standard value."""
    best = DUR_QUARTER
    best_dist = abs(dur - DUR_QUARTER)
    for d in _ALL_DURATIONS:
        dist = abs(dur - d)
        if dist < best_dist:
            best_dist = dist
            best = d
    return best
