# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b-top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
harmonize/predictive.py — Predictive harmonization with certainty scoring.

Ported from MusicPlusOne (ScoreSystem + StateMachine).
Adds two key capabilities to Melodica's harmonization pipeline:

1. CertaintyScorer — Evaluates how well a chord fits a melody segment.
   Computes a score based on pitch overlap, beat strength, and key context.
   When the score drops below a threshold, the chord is flagged as "uncertain".

2. PredictiveHarmonizer — Post-processes an HMM harmonization result.
   For every chord with low certainty, it consults a state transition table
   to find better alternatives, then re-scores them and picks the best one.

This allows the engine to self-correct: if the HMM produces a weak chord,
the PredictiveHarmonizer catches it and substitutes a stronger one.
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.types import NoteInfo, ChordLabel, Scale, Quality
from melodica.harmonize._hmm_helpers import _chord_pcs_for_degree


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Extended transition table from MusicPlusOne StateMachine.
# Maps chord root pitch class -> list of allowed follow-up root PCs.
# This is broader than standard functional harmony: includes IV -> bVII, V -> vi, etc.
_EXTENDED_TRANSITIONS: dict[int, list[int]] = {
    0:  [5, 7, 9, 2, 4],        # C -> F, G, A, D, E
    2:  [7, 0, 9],               # D -> G, C, A
    4:  [0, 9, 5, 2, 8],         # E -> C, A, F, D, Bb
    5:  [7, 0, 9],               # F -> G, C, A
    7:  [0, 9, 5, 2],            # G -> C, A, F, D
    9:  [5, 2, 7, 0, 3, 8, 10], # A -> F, D, G, C, Eb, Bb, Bb
    10: [7, 0, 9, 2, 5],         # Bb -> G, C, A, D, F
    11: [5, 9, 2],               # B -> F, A, D
}

# Major/minor quality preference per root PC (0=major context, 1=minor context)
_QUALITY_BY_CONTEXT: dict[int, dict[int, list[Quality]]] = {
    0: {  # major context
        0: [Quality.MAJOR], 2: [Quality.MINOR], 4: [Quality.MINOR],
        5: [Quality.MAJOR], 7: [Quality.MAJOR, Quality.DOMINANT7],
        9: [Quality.MINOR], 11: [Quality.DIMINISHED],
    },
    1: {  # minor context
        0: [Quality.MINOR], 2: [Quality.DIMINISHED], 3: [Quality.MAJOR],
        5: [Quality.MINOR], 7: [Quality.MINOR, Quality.MAJOR],
        8: [Quality.MAJOR], 10: [Quality.MAJOR],
    },
}


# ---------------------------------------------------------------------------
# CertaintyScorer
# ---------------------------------------------------------------------------

@dataclass
class CertaintyScorer:
    """
    Evaluates how confidently a chord fits a segment of melody notes.

    Scoring components:
        - Pitch overlap: how many melody pitch classes are in the chord
        - Beat strength: bonus for chord tones on strong beats
        - Duration weight: longer notes contribute more
        - Key context: minor penalty for chords foreign to the key

    threshold: score below which a chord is considered "uncertain"
    """

    threshold: float = 2.6
    beat_strength_weight: float = 1.0
    duration_weight: float = 1.0
    key_mismatch_penalty: float = 0.5

    def score(
        self,
        melody_segment: list[NoteInfo],
        chord: ChordLabel,
        scale: Scale,
    ) -> float:
        """
        Compute certainty score for a chord against a melody segment.

        Returns a float. Higher = more certain. Below threshold = uncertain.
        """
        if not melody_segment:
            return 0.0

        chord_pcs = set(chord.pitch_classes())
        if not chord_pcs:
            return 0.0

        scale_pcs = set(int(d) for d in scale.degrees())
        total = 0.0

        for note in melody_segment:
            pc = note.pitch % 12
            if pc not in chord_pcs:
                continue

            # Base point for matching a chord tone
            points = 0.5

            # Beat strength: beat 1 = strongest, beat 3 = medium
            beat_pos = note.start % 4.0
            if beat_pos < 0.01:
                points += 1.0 * self.beat_strength_weight
            elif abs(beat_pos - 2.0) < 0.01:
                points += 0.5 * self.beat_strength_weight
            elif abs(beat_pos - 1.0) < 0.01:
                points += 0.25 * self.beat_strength_weight
            elif abs(beat_pos - 3.0) < 0.01:
                points += 0.25 * self.beat_strength_weight

            # Duration weight: longer notes matter more
            dur = max(0.25, min(4.0, note.duration))
            points += dur * self.duration_weight * 0.5

            # Key context penalty: chord root foreign to scale
            if chord.root not in scale_pcs:
                points -= self.key_mismatch_penalty

            total += points

        return total

    def is_uncertain(
        self,
        melody_segment: list[NoteInfo],
        chord: ChordLabel,
        scale: Scale,
    ) -> bool:
        return self.score(melody_segment, chord, scale) < self.threshold


# ---------------------------------------------------------------------------
# PredictiveHarmonizer
# ---------------------------------------------------------------------------

@dataclass
class PredictiveHarmonizer:
    """
    Post-processor that detects and replaces uncertain harmonizations.

    Workflow:
        1. Accepts an initial chord sequence (from HMM or any harmonizer).
        2. Scores each chord-melody pair using CertaintyScorer.
        3. For uncertain chords, consults the extended transition table
           to find candidate replacements from the previous chord.
        4. Re-scores all candidates and picks the best one.

    This is the "second opinion" layer that catches cases where the HMM
    produces a mathematically valid but musically weak chord choice.

    certainty_threshold: score below which re-evaluation is triggered
    re_evaluation_bonus: extra points given to candidates from the transition table
    """

    certainty_threshold: float = 2.6
    re_evaluation_bonus: float = 1.0

    def refine(
        self,
        chords: list[ChordLabel],
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        """
        Refine a chord sequence by replacing uncertain chords.

        Returns a new list of ChordLabels with weak spots corrected.
        """
        if not chords or not melody:
            return list(chords)

        scorer = CertaintyScorer(threshold=self.certainty_threshold)
        sorted_melody = sorted(melody, key=lambda n: n.start)

        # Compute initial certainty scores
        certainties: list[float] = []
        for chord in chords:
            segment = self._melody_for_chord(chord, sorted_melody)
            certainties.append(scorer.score(segment, chord, scale))

        # Re-evaluate uncertain chords
        result = list(chords)
        for i in range(1, len(result)):
            if certainties[i] >= self.certainty_threshold:
                continue

            prev_chord = result[i - 1]
            segment = self._melody_for_chord(result[i], sorted_melody)
            replacement = self._find_better(prev_chord, segment, result[i], scale)

            if replacement is not None:
                result[i] = replacement

        return result

    def _find_better(
        self,
        prev_chord: ChordLabel,
        melody_segment: list[NoteInfo],
        current_chord: ChordLabel,
        scale: Scale,
    ) -> ChordLabel | None:
        """Search for a better chord using the transition table."""
        prev_root = prev_chord.root
        candidates_roots = _EXTENDED_TRANSITIONS.get(prev_root, [])

        # Include: previous chord (sustained), current chord, and transition candidates
        candidates: list[ChordLabel] = []

        # Previous chord as option
        candidates.append(ChordLabel(
            root=prev_root,
            quality=prev_chord.quality,
            start=current_chord.start,
            duration=current_chord.duration,
            degree=prev_chord.degree,
        ))

        # Transition candidates
        scale_pcs = set(int(d) for d in scale.degrees())
        is_minor = len(scale.intervals()) > 2 and scale.intervals()[2] == 3
        context_key = 1 if is_minor else 0

        for root_pc in candidates_roots:
            qualities = _QUALITY_BY_CONTEXT.get(context_key, {}).get(
                root_pc, [Quality.MAJOR, Quality.MINOR]
            )
            for q in qualities:
                candidates.append(ChordLabel(
                    root=root_pc,
                    quality=q,
                    start=current_chord.start,
                    duration=current_chord.duration,
                ))

        # Current chord is also a candidate
        candidates.append(current_chord)

        # Score all candidates
        scorer = CertaintyScorer()
        best_score = scorer.score(melody_segment, current_chord, scale)
        best_chord: ChordLabel | None = None

        for cand in candidates:
            s = scorer.score(melody_segment, cand, scale)

            # Bonus for candidates from transition table (they follow functional logic)
            if cand.root != current_chord.root and cand.root in candidates_roots:
                s += self.re_evaluation_bonus

            if s > best_score:
                best_score = s
                best_chord = cand

        return best_chord

    def _melody_for_chord(
        self,
        chord: ChordLabel,
        sorted_melody: list[NoteInfo],
    ) -> list[NoteInfo]:
        """Extract melody notes that fall within a chord's time span."""
        end = chord.start + chord.duration
        return [n for n in sorted_melody if chord.start <= n.start < end]
