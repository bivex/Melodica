"""
generators/_melody_pitch.py — MelodyPitchSelector helper.

Extracted from MelodyGenerator to isolate pitch-selection logic.
Uses a melodic weighting system for intelligent, musical pitch choices.
"""

from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

from melodica.utils import nearest_pitch, nearest_pitch_above, pitch_class

if TYPE_CHECKING:
    from melodica.generators.melody import MelodyGenerator

from melodica import types
from melodica.render_context import RenderContext


# ---------------------------------------------------------------------------
# Interval constants
# ---------------------------------------------------------------------------

STEP_SEMITONES: frozenset[int] = frozenset({1, 2})
SMALL_LEAP_SEMITONES: frozenset[int] = frozenset({3, 4, 5})
LARGE_LEAP_SEMITONES: frozenset[int] = frozenset({6, 7, 8, 9, 10, 11, 12})
LEAP_SEMITONES: frozenset[int] = SMALL_LEAP_SEMITONES | LARGE_LEAP_SEMITONES
ALL_INTERVALS: frozenset[int] = STEP_SEMITONES | LEAP_SEMITONES

DEFAULT_UP_INTERVALS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 7, 9, 12})
DEFAULT_DOWN_INTERVALS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 7, 9, 12})


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _all_pitches_in_range(pc: int, low: int, high: int) -> list[int]:
    """All MIDI pitches with the given pitch class in [low, high]."""
    pc = pc % 12
    result = []
    start = pc + ((low - pc + 11) // 12) * 12
    p = start
    while p <= high:
        result.append(p)
        p += 12
    return result


def _all_pitches_in_range_pc_list(pcs: list[int], low: int, high: int) -> list[int]:
    result = []
    for pc in pcs:
        result.extend(_all_pitches_in_range(pc, low, high))
    return result


# ---------------------------------------------------------------------------
# MelodyPitchSelector
# ---------------------------------------------------------------------------


class MelodyPitchSelector:
    """Encapsulates pitch selection with melodic weighting."""

    __slots__ = ("_gen",)

    def __init__(self, gen: MelodyGenerator) -> None:
        self._gen = gen

    # ------------------------------------------------------------------
    # Pitch selection
    # ------------------------------------------------------------------

    def pick_pitch(
        self,
        chord: types.ChordLabel | None,
        key: types.Scale,
        prev_pitch: int,
        low: int,
        high: int,
        last_interval: int,
        steps_prob: float,
        is_downbeat: bool = False,
        is_on_beat: bool = False,
        is_penultimate: bool = False,
        progress: float = 0.0,
        climax_pitch: int | None = None,
        next_chord: types.ChordLabel | None = None,
        register_center: int | None = None,
        range_span: int = 20,
        beat_strength: float = 1.0,
        cadence_target: int | None = None,
        cadence_strength: float = 0.7,
        harmony_prob: float | None = None,
    ) -> int:
        gen = self._gen

        # Penultimate: snap to scale degree above tonic
        if is_penultimate and chord:
            root_pc = chord.root
            scale_pcs = key.degrees()
            above = [pc for pc in scale_pcs if pc > root_pc]
            if above:
                target_pc = above[0]
            else:
                target_pc = scale_pcs[0] if scale_pcs else (root_pc + 2) % 12
            return nearest_pitch(target_pc, prev_pitch)

        pool = self.get_pitch_pool(
            chord, key, is_downbeat, is_on_beat, beat_strength, harmony_prob=harmony_prob
        )
        if not pool:
            return prev_pitch

        last_was_leap = abs(last_interval) > 2 and last_interval != 0
        is_large_leap = abs(last_interval) >= 6

        # Decide step vs. leap (after_leap may override)
        use_step = random.random() < steps_prob
        if last_was_leap and gen.after_leap in (
            "step_opposite",
            "step_any",
            "step_or_smaller_opposite",
        ):
            use_step = True

        interval_set = STEP_SEMITONES if use_step else LEAP_SEMITONES

        # Compute required direction from after_leap
        force_opposite = (
            last_was_leap
            and last_interval != 0
            and gen.after_leap in ("step_opposite", "step_or_smaller_opposite", "leap_opposite")
        )
        required_direction = (
            -1
            if (force_opposite and last_interval > 0)
            else (1 if (force_opposite and last_interval < 0) else 0)
        )

        # Climax bias: before 65% of phrase, nudge upward toward climax
        if climax_pitch is not None and progress < 0.65 and required_direction == 0:
            ascent_strength = 0.35 * (1.0 - progress / 0.65)
            if prev_pitch < climax_pitch and random.random() < ascent_strength:
                required_direction = 1

        # Post-climax: after 65%, allow descent
        if climax_pitch is not None and progress >= 0.65 and required_direction == 0:
            if prev_pitch >= climax_pitch - 2 and random.random() < 0.3:
                required_direction = -1

        # Build candidates with cascading fallbacks
        candidates = self.build_candidates(
            pool, prev_pitch, low, high, interval_set, required_direction
        )

        # Fallback 1: relax interval type
        if not candidates:
            candidates = self.build_candidates(
                pool, prev_pitch, low, high, ALL_INTERVALS, required_direction
            )

        # Fallback 2: relax direction (step_any after failed opposite)
        if not candidates and force_opposite:
            candidates = self.build_candidates(
                pool, prev_pitch, low, high, STEP_SEMITONES, 0
            )

        # Fallback 3: fully relax
        if not candidates:
            candidates = self.build_candidates(pool, prev_pitch, low, high, ALL_INTERVALS, 0)

        # Ultimate fallback
        if not candidates:
            return prev_pitch

        if len(candidates) == 1:
            return candidates[0]

        # ---- Weighted selection ----

        # Voice-leading: near chord boundary, prefer common tones with next chord
        if next_chord is not None and chord is not None:
            next_pcs = set(next_chord.pitch_classes())
            common = [c for c in candidates if c % 12 in next_pcs]
            if common and random.random() < 0.45:
                return min(common, key=lambda p: abs(p - prev_pitch))

        # Cadence target: strong attractor in last 10% of phrase
        if cadence_target is not None and progress > 0.85:
            by_cadence = sorted(candidates, key=lambda p: abs(p - cadence_target))
            if random.random() < cadence_strength:
                return by_cadence[0]

        # Climax: occasionally snap toward climax pitch
        if climax_pitch is not None and progress < 0.70 and random.random() < 0.25:
            by_climax = sorted(candidates, key=lambda p: abs(p - climax_pitch))
            return by_climax[0]

        # Direction bias: weighted probability
        bias = gen.direction_bias
        if abs(bias) > 0.01:
            return self._biased_choice(candidates, prev_pitch, bias, register_center)

        # Register awareness
        if register_center is not None and range_span > 0:
            smoothness = getattr(gen, "register_smoothness", 0.5)
            if smoothness > 0.1 and random.random() < smoothness:
                return min(candidates, key=lambda p: abs(p - register_center))

        # Melodic weighting system: blend weighted choice with random
        rm = gen.random_movement
        if rm < 0.01:
            # Fully weighted: pick best candidate
            return self._weighted_choice(candidates, prev_pitch, chord, key, register_center, climax_pitch, range_span)
        elif random.random() > rm:
            # Weighted choice
            return self._weighted_choice(candidates, prev_pitch, chord, key, register_center, climax_pitch, range_span)
        else:
            # Random choice from candidates
            return random.choice(candidates)

    def _weighted_choice(
        self,
        candidates: list[int],
        prev_pitch: int,
        chord: types.ChordLabel | None,
        key: types.Scale,
        register_center: int | None,
        climax_pitch: int | None,
        range_span: int,
    ) -> int:
        """Select candidate using melodic weighting (smoothness + register + tonal gravity)."""
        if len(candidates) == 1:
            return candidates[0]

        chord_pcs = set(chord.pitch_classes()) if chord else set()
        scale_pcs = set(key.degrees())
        root_pc = key.root

        weights: list[float] = []
        for c in candidates:
            w = 1.0

            # 1. Intervallic smoothness: prefer closer pitches
            dist = abs(c - prev_pitch)
            w *= math.exp(-dist * 0.15)

            # 2. Chord tone bonus
            if c % 12 in chord_pcs:
                w *= 1.5

            # 3. Tonal gravity: boost tonic and fifth
            pc = c % 12
            if pc == root_pc:
                w *= 1.3
            elif pc == (root_pc + 7) % 12:  # fifth
                w *= 1.15

            # 4. Register proximity
            if register_center is not None and range_span > 0:
                reg_dist = abs(c - register_center)
                w *= max(0.3, 1.0 - reg_dist / range_span)

            # 5. Climax attraction (subtle)
            if climax_pitch is not None:
                if c <= climax_pitch:
                    w *= 1.0 + 0.1 * (1.0 - abs(c - climax_pitch) / max(1, range_span))

            weights.append(max(0.01, w))

        total = sum(weights)
        r = random.random() * total
        cumul = 0.0
        for c, w in zip(candidates, weights):
            cumul += w
            if r <= cumul:
                return c
        return candidates[-1]

    def _biased_choice(
        self,
        candidates: list[int],
        prev_pitch: int,
        bias: float,
        register_center: int | None = None,
    ) -> int:
        """Weight candidates by direction bias and optionally register proximity."""
        if not candidates:
            return prev_pitch
        if len(candidates) == 1:
            return candidates[0]
        weights: list[float] = []
        for c in candidates:
            diff = c - prev_pitch
            if diff > 0:
                w = 1.0 + bias * 2.0
            elif diff < 0:
                w = 1.0 - bias * 2.0
            else:
                w = 1.0
            if register_center is not None:
                dist = abs(c - register_center)
                w *= max(0.2, 1.0 - dist / 24.0)
            weights.append(max(0.05, w))
        total = sum(weights)
        r = random.random() * total
        cumul = 0.0
        for c, w in zip(candidates, weights):
            cumul += w
            if r <= cumul:
                return c
        return candidates[-1]

    def build_candidates(
        self,
        pool: list[int],
        prev_pitch: int,
        low: int,
        high: int,
        interval_set: frozenset[int],
        required_direction: int,
    ) -> list[int]:
        gen = self._gen
        up_ivls = (
            gen.allowed_up_intervals
            if gen.allowed_up_intervals is not None
            else DEFAULT_UP_INTERVALS
        )
        dn_ivls = (
            gen.allowed_down_intervals
            if gen.allowed_down_intervals is not None
            else DEFAULT_DOWN_INTERVALS
        )

        seen: set[int] = set()
        result: list[int] = []
        for pc in pool:
            for p in _all_pitches_in_range(pc, low, high):
                if p in seen:
                    continue
                seen.add(p)
                diff = p - prev_pitch
                if diff == 0:
                    continue
                abs_diff = abs(diff)

                if required_direction == 1 and diff < 0:
                    continue
                if required_direction == -1 and diff > 0:
                    continue

                if diff > 0 and abs_diff not in up_ivls:
                    continue
                if diff < 0 and abs_diff not in dn_ivls:
                    continue

                if abs_diff not in interval_set:
                    continue

                result.append(p)
        return result

    def get_pitch_pool(
        self,
        chord: types.ChordLabel | None,
        key: types.Scale,
        is_downbeat: bool = False,
        is_on_beat: bool = False,
        beat_strength: float = 1.0,
        harmony_prob: float | None = None,
    ) -> list[int]:
        gen = self._gen
        chord_pcs = chord.pitch_classes() if chord else []
        scale_pcs = key.degrees()

        if not chord_pcs:
            return scale_pcs

        pool = list(chord_pcs)
        if chord:
            root = chord.root
            if gen.allow_2nd:
                ninth = (root + 2) % 12
                if ninth not in pool:
                    pool.append(ninth)
            if gen.allow_7th:
                seventh = (root + 10) % 12
                if hasattr(chord, 'quality'):
                    from melodica.types import Quality
                    if chord.quality == Quality.MAJOR:
                        seventh = (root + 11) % 12
                if seventh not in pool:
                    pool.append(seventh)

        effective_prob = harmony_prob if harmony_prob is not None else gen.harmony_note_probability

        if gen.mode == "scale_only":
            return scale_pcs
        elif gen.mode == "chord_only":
            return pool
        elif gen.mode == "downbeat_chord":
            if beat_strength > 0.85:  # strong beat
                return chord_pcs
            if random.random() < effective_prob:
                return pool
            return scale_pcs
        elif gen.mode == "on_beat_chord":
            if beat_strength > 0.5:
                return chord_pcs
            if random.random() < effective_prob:
                return pool
            return scale_pcs
        else:  # "scale_and_chord"
            if random.random() < effective_prob:
                return pool
            return scale_pcs

    # ------------------------------------------------------------------
    # First / last note strategies
    # ------------------------------------------------------------------

    def first_pitch(
        self,
        first_chord: types.ChordLabel,
        key: types.Scale,
        low: int,
        high: int,
        context: RenderContext | None,
    ) -> int:
        gen = self._gen
        if context and context.prev_pitch is not None:
            return context.prev_pitch

        mid = (low + high) // 2
        match gen.first_note:
            case "chord_root":
                return nearest_pitch(first_chord.root, mid)
            case "any_chord":
                pcs = first_chord.pitch_classes()
                return nearest_pitch(random.choice(pcs) if pcs else first_chord.root, mid)
            case "tonic":
                return nearest_pitch(key.root, mid)
            case "step_above_tonic":
                tonic = nearest_pitch(key.root, mid)
                scale_pcs = key.degrees()
                above = [
                    p for p in _all_pitches_in_range_pc_list(scale_pcs, low, high) if p > tonic
                ]
                return min(above, key=lambda p: p - tonic) if above else tonic
            case "step_below_tonic":
                tonic = nearest_pitch(key.root, mid)
                scale_pcs = key.degrees()
                below = [
                    p for p in _all_pitches_in_range_pc_list(scale_pcs, low, high) if p < tonic
                ]
                return max(below, key=lambda p: tonic - p) if below else tonic
            case _:  # "scale" or unknown
                pcs = key.degrees()
                return nearest_pitch(random.choice(pcs) if pcs else key.root, mid)

    def last_pitch(
        self,
        last_chord: types.ChordLabel | None,
        key: types.Scale,
        prev_pitch: int,
        low: int,
        high: int,
    ) -> int:
        gen = self._gen
        if last_chord is None:
            return prev_pitch
        match gen.last_note:
            case "last_chord_root":
                return nearest_pitch(last_chord.root, prev_pitch)
            case "any_chord":
                pcs = last_chord.pitch_classes()
                if not pcs:
                    return prev_pitch
                return min(
                    (nearest_pitch(pc, prev_pitch) for pc in pcs),
                    key=lambda p: abs(p - prev_pitch),
                )
            case "scale":
                pcs = key.degrees()
                if not pcs:
                    return prev_pitch
                return min(
                    (nearest_pitch(pc, prev_pitch) for pc in pcs),
                    key=lambda p: abs(p - prev_pitch),
                )
            case _:  # "any"
                pcs = last_chord.pitch_classes() if last_chord else key.degrees()
                if pcs:
                    return nearest_pitch(random.choice(list(pcs)), prev_pitch)
                return prev_pitch
