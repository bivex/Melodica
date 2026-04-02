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
engines/adaptive.py — Engine 2: AdaptiveEngine.

Layer: Domain / Application

Four-stage pipeline (§6.2):
  1. Segmentation
  2. Candidate search  (chord DB mask + note inclusion)
  3. Simplicity scoring (chord simplicity index)
  4. Look-ahead tonal stability
  + Inversion selection (distance-minimizing voicing)
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica import types
from melodica.utils import (
    chord_pitches_closed,
    compute_simplicity,
    voice_leading_distance,
)


# ---------------------------------------------------------------------------
# §6.2 Internal segment model
# ---------------------------------------------------------------------------


@dataclass
class NoteSectionHarm:

    segment_start: float
    segment_end: float
    melody_pitches: list[int]          # pitch classes active in window
    candidates: list[types.ChordLabel] = field(default_factory=list)
    chosen: types.ChordLabel | None = None
    tonal_stability: float = 0.0


# ---------------------------------------------------------------------------
# Public engine
# ---------------------------------------------------------------------------


class AdaptiveEngine:
    """
    Engine 2 — Melody-driven candidate search with heuristic scoring.
    Orthogonal criteria: simplicity + voice leading + look-ahead stability.
    """

    def __init__(
        self,
        *,
        simplicity_weight: float = 0.4,
        melody_fit_weight: float = 0.6,
        stability_weight: float = 0.3,
        allow_modal_mixture: bool = True,
    ) -> None:
        self.simplicity_weight = simplicity_weight
        self.melody_fit_weight = melody_fit_weight
        self.stability_weight = stability_weight
        self.allow_modal_mixture = allow_modal_mixture

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def harmonize(self, req: types.HarmonizationRequest) -> list[types.ChordLabel]:
        melody = req.melody
        key = req.key
        rhythm = req.chord_rhythm

        segments = self._build_segments(melody, key, rhythm)
        for seg in segments:
            seg.candidates = self.search_candidates(seg, key)

        # Stage 3 + 4: score with look-ahead
        chosen: list[ChordLabel] = []
        prev_chord: ChordLabel | None = None
        prev_pitches: list[int] = []

        for i, seg in enumerate(segments):
            next_candidates = (
                segments[i + 1].candidates if i + 1 < len(segments) else []
            )
            scored = self.score_candidates(
                seg.candidates, seg, prev_chord, next_candidates, key
            )

            if not scored:
                fallback = key.diatonic_chord(1)
                fallback.start = seg.segment_start
                fallback.duration = seg.segment_end - seg.segment_start
                chosen.append(fallback)
                prev_pitches = chord_pitches_closed(fallback)
                prev_chord = fallback
                continue

            best_chord, _ = max(scored, key=lambda x: x[1])

            # Stage: inversion selection (voice leading)
            if prev_pitches:
                best_chord = _select_inversion(best_chord, prev_pitches)

            best_chord.start = seg.segment_start
            best_chord.duration = seg.segment_end - seg.segment_start
            seg.chosen = best_chord
            prev_pitches = chord_pitches_closed(best_chord)
            prev_chord = best_chord
            chosen.append(best_chord)

        return chosen

    # ------------------------------------------------------------------
    # Stage 1 — Segmentation
    # ------------------------------------------------------------------

    def _build_segments(
        self,
        melody: list[types.Note],
        key: types.Scale,
        rhythm: float,
    ) -> list[NoteSectionHarm]:
        if not melody:
            return []
        end_time = max(n.start + n.duration for n in melody)
        segments: list[NoteSectionHarm] = []
        t = 0.0
        while t < end_time:
            window_notes = [
                n for n in melody
                if n.start < t + rhythm and (n.start + n.duration) > t
            ]
            pcs = list({n.pitch % types.OCTAVE for n in window_notes})
            segments.append(NoteSectionHarm(
                segment_start=t,
                segment_end=t + rhythm,
                melody_pitches=pcs,
            ))
            t += rhythm
        return segments

    # ------------------------------------------------------------------
    # Stage 2 — Candidate search (exposed for testing / tuning)
    # ------------------------------------------------------------------

    def search_candidates(
        self,
        segment: NoteSectionHarm,
        key: types.Scale,
    ) -> list[types.ChordLabel]:
        """
        Find all chords containing all melody pitch classes as chord tones.
        Falls back to chords containing at least the most prominent pitch class.
        Filters to diatonic chords (+ one chromatic for modal mixture).
        """
        pcs = set(segment.melody_pitches)
        scale_pcs = set(key.degrees())

        candidates: list[types.ChordLabel] = []

        # Diatonic candidates
        for root in range(types.OCTAVE):
            for quality, template in types.CHORD_TEMPLATES.items():
                chord_pcs = {(root + ivl) % types.OCTAVE for ivl in template}
                if pcs and not pcs.issubset(chord_pcs):
                    continue
                
                # Diatonic check
                if chord_pcs.issubset(scale_pcs):
                    chord = types.ChordLabel(root=root, quality=quality)
                    chord.degree = key.degree_of(root)
                    candidates.append(chord)
        
        # Modal Mixture candidates
        if self.allow_modal_mixture:
            # Common parallel modes to borrow from
            # Major -> Dorian, Mixolydian, Aeolian
            # Minor -> Harmonic Minor, Dorian, Major (Picardy)
            parallel_modes = [types.Mode.DORIAN, types.Mode.MIXOLYDIAN, types.Mode.NATURAL_MINOR]
            if key.mode == types.Mode.NATURAL_MINOR:
                parallel_modes = [types.Mode.MAJOR, types.Mode.DORIAN, types.Mode.HARMONIC_MINOR]
            
            for p_mode in parallel_modes:
                p_scale = key.get_parallel_scale(p_mode)
                p_scale_pcs = set(p_scale.degrees())
                
                for root in range(types.OCTAVE):
                    if root not in p_scale_pcs: continue
                    for quality, template in types.CHORD_TEMPLATES.items():
                        chord_pcs = {(root + ivl) % types.OCTAVE for ivl in template}
                        if not chord_pcs.issubset(p_scale_pcs): continue
                        if pcs and not pcs.issubset(chord_pcs): continue
                        
                        # Only add if it's NOT already in candidates (chromatic for current key)
                        if not chord_pcs.issubset(scale_pcs):
                            chord = types.ChordLabel(root=root, quality=quality)
                            chord.degree = key.degree_of(root) # might be None, which is fine
                            candidates.append(chord)

        # Fallback: relax to "metrically strongest note must be chord tone"
        if not candidates and pcs:
            primary_pc = next(iter(pcs))  # simplified: first pc
            for root in range(types.OCTAVE):
                for quality, template in types.CHORD_TEMPLATES.items():
                    chord_pcs = {(root + ivl) % types.OCTAVE for ivl in template}
                    if primary_pc not in chord_pcs:
                        continue
                    chord = types.ChordLabel(root=root, quality=quality)
                    chord.degree = key.degree_of(root)
                    candidates.append(chord)

        return candidates

    # ------------------------------------------------------------------
    # Stage 3 — Scoring (exposed for testing / tuning)
    # ------------------------------------------------------------------

    def score_candidates(
        self,
        candidates: list[types.ChordLabel],
        segment: NoteSectionHarm,
        prev_chord: types.ChordLabel | None = None,
        next_candidates: list[types.ChordLabel] | None = None,
        key: types.Scale | None = None,
    ) -> list[tuple[types.ChordLabel, float]]:
        """
        Return (chord, final_score) for each candidate.
        final_score = simplicity + melody_fit + look-ahead stability.
        """
        result: list[tuple[ChordLabel, float]] = []
        pcs = set(segment.melody_pitches)

        for c in candidates:
            simplicity = compute_simplicity(c)
            melody_fit = _melody_fit_score(c, pcs)

            score = (
                self.simplicity_weight * simplicity
                + self.melody_fit_weight * melody_fit
            )

            # Stage 4 — look-ahead tonal stability
            if key is not None:
                stability = _tonal_stability(
                    c, prev_chord, next_candidates or [], key
                )
                score += self.stability_weight * stability

            result.append((c, score))

        return result


# ---------------------------------------------------------------------------
# Inversion selection helpers (§6.3)
# ---------------------------------------------------------------------------


def _select_inversion(chord: types.ChordLabel, prev_pitches: list[int]) -> types.ChordLabel:
    """
    Try all inversions; pick the one minimising total voice-leading distance.
    Tiebreak: minimize highest-note movement, then bass movement.
    """
    n_tones = len(chord.pitch_classes())
    best = chord
    best_dist = float("inf")
    best_high = float("inf")
    best_bass = float("inf")
    prev_high = max(prev_pitches) if prev_pitches else 0
    prev_bass = min(prev_pitches) if prev_pitches else 0

    for inv in range(n_tones):
        candidate = types.ChordLabel(
            root=chord.root,
            quality=chord.quality,
            extensions=list(chord.extensions),
            bass=chord.bass,
            inversion=inv,
            start=chord.start,
            duration=chord.duration,
            degree=chord.degree,
            function=chord.function,
        )
        pitches = chord_pitches_closed(candidate)
        dist = voice_leading_distance(prev_pitches, pitches)
        high_move = abs(max(pitches) - prev_high) if pitches else float("inf")
        bass_move = abs(min(pitches) - prev_bass) if pitches else float("inf")

        if (
            dist < best_dist
            or (dist == best_dist and high_move < best_high)
            or (dist == best_dist and high_move == best_high and bass_move < best_bass)
        ):
            best_dist = dist
            best_high = high_move
            best_bass = bass_move
            best = candidate

    return best


# ---------------------------------------------------------------------------
# Scoring sub-functions (pure)
# ---------------------------------------------------------------------------


def _melody_fit_score(chord: types.ChordLabel, melody_pcs: set[int]) -> float:
    """Fraction of melody pitch classes that are chord tones."""
    if not melody_pcs:
        return 1.0
    chord_pcs = set(chord.pitch_classes())
    return len(melody_pcs & chord_pcs) / len(melody_pcs)


def _tonal_stability(
    chord: types.ChordLabel,
    prev: types.ChordLabel | None,
    next_candidates: list[types.ChordLabel],
    key: types.Scale,
) -> float:
    """
    §6.2 Stage 4 — Look-ahead tonal stability ∈ [0, 1].
    Penalises sequences leaving no good resolution in the next segment.
    Rewards diatonic degree variety (avoids repeating same degree).
    """
    score = 1.0

    # Penalise if no next candidate shares a common tone
    if next_candidates:
        cur_pcs = set(chord.pitch_classes())
        common_tone_score = max(
            len(cur_pcs & set(nc.pitch_classes())) / max(len(cur_pcs), 1)
            for nc in next_candidates
        )
        score *= common_tone_score

    # Penalise repeating same degree as prev
    if prev is not None and chord.degree == prev.degree:
        score *= 0.6

    # Reward diatonic chords
    if chord.degree is not None:
        score *= 1.0
    else:
        score *= 0.5  # chromatic chord penalty

    return min(1.0, max(0.0, score))
