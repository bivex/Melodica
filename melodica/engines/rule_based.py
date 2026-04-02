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
engines/rule_based.py — Engine 1: RuleBasedEngine.

Layer: Domain / Application

Algorithm (§5.3):
  1. Segment melody into harmonic-rhythm windows.
  2. Collect candidate diatonic chords per window.
  3. Score = melody_fit × rule_weight(prev→candidate).
  4. Viterbi search over the full sequence.
  5. Return optimal chord sequence.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from melodica.rule_db import ChordProgressionRuleDB
from melodica import types
from melodica.utils import chord_pitches_closed, voice_leading_distance


# ---------------------------------------------------------------------------
# Internal Viterbi state
# ---------------------------------------------------------------------------


@dataclass
class _State:
    chord: types.ChordLabel
    log_prob: float
    prev: "_State | None"


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------


class RuleBasedEngine:
    """
    Engine 1 — Viterbi search over a chord-progression rule graph.

    rule_db: ChordProgressionRuleDB instance or None (uses built-in default).
    """

    def __init__(self, rule_db: ChordProgressionRuleDB | None = None) -> None:
        self._rule_db = rule_db or ChordProgressionRuleDB.default()

    def harmonize(self, req: types.HarmonizationRequest) -> list[types.ChordLabel]:
        melody = req.melody
        key = req.key
        rhythm = req.chord_rhythm
        context = "classical"

        windows = _segment_by_rhythm(melody, rhythm)
        if not windows:
            return []

        # DP table: for each window, list of _State nodes
        dp: list[list[_State]] = []

        # --- Initialise first column ---
        first_notes, first_start, first_dur = windows[0]
        first_candidates = _get_candidates(first_notes, key)
        initial_states = [
            _State(
                chord=c,
                log_prob=math.log(max(_melody_fit(c, first_notes), 1e-9)),
                prev=None,
            )
            for c in first_candidates
        ]
        dp.append(initial_states)

        # --- Fill subsequent columns ---
        for win_notes, win_start, win_dur in windows[1:]:
            candidates = _get_candidates(win_notes, key)
            column: list[_State] = []

            for c in candidates:
                best_prev: _State | None = None
                best_score = -math.inf

                melody_fit = _melody_fit(c, win_notes)
                if melody_fit <= 0:
                    continue

                for prev_state in dp[-1]:
                    rule_w = _rule_weight(
                        prev_state.chord, c, self._rule_db, context
                    )
                    combined = prev_state.log_prob + math.log(
                        max(melody_fit * rule_w, 1e-9)
                    )
                    if combined > best_score:
                        best_score = combined
                        best_prev = prev_state

                column.append(_State(chord=c, log_prob=best_score, prev=best_prev))

            if not column:
                # Fallback: take tonic if no candidates fit
                fallback = key.diatonic_chord(1)
                column = [_State(chord=fallback, log_prob=-math.inf, prev=dp[-1][0])]
            dp.append(column)

        # Traceback
        best_final = max(dp[-1], key=lambda s: s.log_prob)
        path: list[types.ChordLabel] = []
        state: _State | None = best_final
        while state is not None:
            path.append(state.chord)
            state = state.prev
        path.reverse()

        # Assign timing
        for i, chord in enumerate(path):
            chord.start = windows[i][1]
            chord.duration = windows[i][2]

        return path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _segment_by_rhythm(
    melody: list[types.Note],
    rhythm: float,
) -> list[tuple[list[types.Note], float, float]]:
    if not melody:
        return []
    end_time = max(n.start + n.duration for n in melody)
    windows = []
    t = 0.0
    while t < end_time:
        window_notes = [n for n in melody if t <= n.start < t + rhythm]
        windows.append((window_notes, t, rhythm))
        t += rhythm
    return windows


def _get_candidates(notes: list[types.Note], key: types.Scale) -> list[types.ChordLabel]:
    """Return all diatonic chords (triads + sevenths) for this window."""
    candidates: list[types.ChordLabel] = []
    for degree in range(1, 8):
        candidates.append(key.diatonic_chord(degree, seventh=False))
        candidates.append(key.diatonic_chord(degree, seventh=True))
    return candidates


def _melody_fit(chord: types.ChordLabel, notes: list[types.Note]) -> float:
    """
    Fraction of melody note durations that are chord tones.
    Returns 0.0–1.0.
    """
    if not notes:
        return 1.0
    chord_pcs = set(chord.pitch_classes())
    total = sum(n.duration for n in notes)
    fitting = sum(n.duration for n in notes if (n.pitch % types.OCTAVE) in chord_pcs)
    return fitting / total if total > 0 else 0.0


def _rule_weight(
    prev: types.ChordLabel,
    next_chord: types.ChordLabel,
    rule_db: ChordProgressionRuleDB,
    context: str,
) -> float:
    """
    Look up the transition weight from prev → next_chord in the rule DB.
    Falls back to a small default if not found.
    """
    if prev.degree is None or next_chord.degree is None:
        return 0.3  # no degree info → neutral weight

    succs = rule_db.successors(prev.degree, prev.quality, context, top_n=20)
    for to_deg, to_qual, weight in succs:
        if to_deg == next_chord.degree and to_qual == next_chord.quality:
            return weight
    return 0.1  # allowed but not explicitly listed
