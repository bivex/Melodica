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
_specialized.py — Specialized harmonizers.
"""

from __future__ import annotations

import heapq
import math
import random
from dataclasses import dataclass, field

from melodica.harmonize._hmm_helpers import (
    _chord_pcs_for_degree, _voice_leading_cost, _melody_fits_chord, _build_diatonic_chords,
)
from melodica.types import ChordLabel, Quality, HarmonicFunction, Scale, Mode, NoteInfo

@dataclass
class GraphSearchHarmonizer:
    """
    Dijkstra-based harmonization over chord graph.

    Finds optimal chord path minimizing:
    - melody-chord fit (melody note should be in chord)
    - voice leading distance (minimize movement between chords)
    - harmonic function weight (prefer functional progressions)
    """

    melody_weight: float = 0.5
    voice_weight: float = 0.3
    harmonic_weight: float = 0.2
    chord_change: str = "bars"

    def harmonize(
        self,
        melody: list[NoteInfo],
        scale: Scale,
        duration_beats: float,
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        chords_def = _build_diatonic_chords(scale)
        n = len(chords_def)
        change_points = self._get_change_points(duration_beats)
        observations = self._extract_observations(melody, change_points)

        if not observations:
            return []

        T = len(observations)

        # Dijkstra: (cost, time_step, state)
        heap: list[tuple[float, int, int]] = []
        dist: dict[tuple[int, int], float] = {}
        parent: dict[tuple[int, int], int] = {}

        # Start: try all chords at t=0
        for s in range(n):
            cost = -self._melody_fit(observations[0], chords_def[s])
            heapq.heappush(heap, (cost, 0, s))
            dist[(0, s)] = cost

        # Functional harmonic weights
        func_weights = self._build_functional_weights(n)

        # Run Dijkstra
        while heap:
            cost, t, s = heapq.heappop(heap)
            if t == T - 1:
                # Found path to end
                break
            if dist.get((t, s), float("inf")) < cost:
                continue

            # Expand to next time step
            for next_s in range(n):
                melody_cost = -self._melody_fit(observations[t + 1], chords_def[next_s])
                pcs_a = _chord_pcs_for_degree(chords_def[s][0], chords_def[s][1])
                pcs_b = _chord_pcs_for_degree(chords_def[next_s][0], chords_def[next_s][1])
                voice_cost = _voice_leading_cost(pcs_a, pcs_b)
                harmonic_cost = 1.0 - func_weights[s][next_s]

                new_cost = cost + (
                    melody_cost * self.melody_weight
                    + voice_cost * self.voice_weight
                    + harmonic_cost * self.harmonic_weight
                )

                key = (t + 1, next_s)
                if new_cost < dist.get(key, float("inf")):
                    dist[key] = new_cost
                    parent[key] = s
                    heapq.heappush(heap, (new_cost, t + 1, next_s))

        # Reconstruct path
        end_state = min(range(n), key=lambda s: dist.get((T - 1, s), float("inf")))
        path = [end_state]
        for t in range(T - 1, 0, -1):
            path.append(parent.get((t, path[-1]), 0))
        path.reverse()

        # Build ChordLabels
        result = []
        for i, state in enumerate(path):
            root_pc, quality = chords_def[state]
            start = change_points[i]
            dur = (
                (change_points[i + 1] - start)
                if i + 1 < len(change_points)
                else duration_beats - start
            )
            result.append(
                ChordLabel(
                    root=root_pc,
                    quality=quality,
                    start=round(start, 6),
                    duration=round(dur, 6),
                    degree=state + 1,
                )
            )
        return result

    def _melody_fit(self, obs_pcs: list[int], chord_def: tuple[int, Quality]) -> float:
        """How well melody notes fit this chord (0-1)."""
        chord_pcs = _chord_pcs_for_degree(chord_def[0], chord_def[1])
        if not obs_pcs:
            return 0.5
        return sum(1 for pc in obs_pcs if pc in chord_pcs) / len(obs_pcs)

    def _build_functional_weights(self, n: int) -> list[list[float]]:
        """Functional harmony weights (higher = more expected transition)."""
        mat = [[0.1] * n for _ in range(n)]
        rules = {
            0: {3: 0.9, 4: 0.8, 1: 0.6, 5: 0.5},
            1: {4: 0.9, 0: 0.6, 3: 0.5},
            2: {5: 0.8, 3: 0.7, 4: 0.5},
            3: {4: 0.9, 0: 0.7, 1: 0.6},
            4: {0: 0.9, 5: 0.7, 3: 0.5},
            5: {1: 0.8, 4: 0.7, 3: 0.6, 0: 0.5},
            6: {0: 0.9, 4: 0.7},
        }
        for i, row in rules.items():
            for j, w in row.items():
                mat[i][j] = w
        return mat

    def _extract_observations(
        self,
        melody: list[NoteInfo],
        change_points: list[float],
    ) -> list[list[int]]:
        sorted_m = sorted(melody, key=lambda n: n.start)
        observations = []
        for i, cp in enumerate(change_points):
            next_cp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            pcs = [n.pitch % 12 for n in sorted_m if cp <= n.start < next_cp]
            observations.append(pcs if pcs else [0])
        return observations

    def _get_change_points(self, duration: float) -> list[float]:
        points = []
        step = (
            4.0
            if self.chord_change == "bars"
            else 2.0
            if self.chord_change == "strong_beats"
            else 1.0
        )
        t = 0.0
        while t < duration:
            points.append(t)
            t += step
        return points
@dataclass
class GeneticHarmonizer:
    """Evolves chord progressions using genetic algorithm."""

    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.15
    chord_change: str = "bars"

    def harmonize(
        self, melody: list[NoteInfo], scale: Scale, duration_beats: float
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []

        chords_def = _build_diatonic_chords(scale)
        n_states = len(chords_def)
        change_points = self._get_cp(duration_beats)
        observations = self._extract_obs(melody, change_points)
        T = len(observations)
        if T == 0:
            return []

        import random as _random

        population = [
            [_random.randint(0, n_states - 1) for _ in range(T)]
            for _ in range(self.population_size)
        ]
        good_pairs = {(0, 3), (0, 4), (3, 4), (4, 0), (4, 5), (5, 1), (1, 4)}

        for _ in range(self.generations):
            scores = []
            for ind in population:
                s = 0.0
                for t, state in enumerate(ind):
                    rpc, qual = chords_def[state]
                    cpcs = _chord_pcs_for_degree(rpc, qual)
                    if observations[t]:
                        s += (
                            sum(1 for p in observations[t] if p in cpcs)
                            / len(observations[t])
                            * 0.5
                        )
                    if t > 0 and ind[t] != ind[t - 1]:
                        s += 0.1
                    if t > 0 and (ind[t - 1], ind[t]) in good_pairs:
                        s += 0.2
                scores.append((s, ind))
            scores.sort(key=lambda x: -x[0])
            survivors = [ind for _, ind in scores[: self.population_size // 2]]
            new_pop = list(survivors)
            while len(new_pop) < self.population_size:
                p1, p2 = _random.sample(survivors, 2)
                pt = _random.randint(1, len(p1) - 1)
                child = p1[:pt] + p2[pt:]
                child = [
                    _random.randint(0, n_states - 1) if _random.random() < self.mutation_rate else g
                    for g in child
                ]
                new_pop.append(child)
            population = new_pop

        best = max(
            population,
            key=lambda ind: sum(
                0.5
                * (
                    sum(
                        1
                        for p in observations[t]
                        if p
                        in _chord_pcs_for_degree(chords_def[ind[t]][0], chords_def[ind[t]][1])
                    )
                    / max(1, len(observations[t]))
                )
                if observations[t]
                else 0.0
                + (0.1 if t > 0 and ind[t] != ind[t - 1] else 0.0)
                + (0.2 if t > 0 and (ind[t - 1], ind[t]) in good_pairs else 0.0)
                for t in range(len(ind))
            ),
        )

        result = []
        for i, state in enumerate(best):
            rpc, qual = chords_def[state]
            start = change_points[i]
            dur = (
                (change_points[i + 1] - start)
                if i + 1 < len(change_points)
                else duration_beats - start
            )
            result.append(
                ChordLabel(
                    root=rpc,
                    quality=qual,
                    start=round(start, 6),
                    duration=round(dur, 6),
                    degree=state + 1,
                )
            )
        return result

    def _extract_obs(self, melody, change_points):
        sorted_m = sorted(melody, key=lambda n: n.start)
        obs = []
        for i, cp in enumerate(change_points):
            ncp = change_points[i + 1] if i + 1 < len(change_points) else float("inf")
            obs.append([n.pitch % 12 for n in sorted_m if cp <= n.start < ncp] or [0])
        return obs

    def _get_cp(self, duration):
        pts, t, step = [], 0.0, 4.0 if self.chord_change == "bars" else 2.0
        while t < duration:
            pts.append(t)
            t += step
        return pts
@dataclass
class ChromaticMediantHarmonizer:
    """Dramatic cinematic chords: I→bVI, I→bIII, I→III, etc."""

    chromatic_prob: float = 0.4
    chord_change: str = "bars"

    def harmonize(
        self, melody: list[NoteInfo], scale: Scale, duration_beats: float
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []
        import random as _random

        mediants = [
            (-9, Quality.MAJOR),
            (-4, Quality.MAJOR),
            (3, Quality.MAJOR),
            (4, Quality.MAJOR),
            (8, Quality.MAJOR),
            (-8, Quality.MINOR),
            (-3, Quality.MINOR),
            (9, Quality.MINOR),
        ]
        chords_def = _build_diatonic_chords(scale)
        cp = self._get_cp(duration_beats)
        result, prev_root = [], chords_def[0][0]

        for i, start in enumerate(cp):
            end = cp[i + 1] if i + 1 < len(cp) else duration_beats
            obs = set(n.pitch % 12 for n in melody if start <= n.start < end)

            if _random.random() < self.chromatic_prob and i > 0:
                offset, qual = _random.choice(mediants)
                root = (prev_root + offset) % 12
            else:
                best, best_fit = 0, -1
                for j, (rpc, qual) in enumerate(chords_def):
                    fit = len(obs & set(_chord_pcs_for_degree(rpc, qual)))
                    if fit > best_fit:
                        best_fit, best = fit, j
                root, qual = chords_def[best]

            result.append(
                ChordLabel(
                    root=root, quality=qual, start=round(start, 6), duration=round(end - start, 6),
                    degree=scale.degree_of(root),
                )
            )
            prev_root = root
        return result

    def _get_cp(self, duration):
        pts, t, step = [], 0.0, 4.0 if self.chord_change == "bars" else 2.0
        while t < duration:
            pts.append(t)
            t += step
        return pts
@dataclass
class ModalInterchangeHarmonizer:
    """Borrows chords from parallel minor (iv, bVI, bVII)."""

    borrow_prob: float = 0.3
    chord_change: str = "bars"

    def harmonize(
        self, melody: list[NoteInfo], scale: Scale, duration_beats: float
    ) -> list[ChordLabel]:
        if not melody or not scale.degrees():
            return []
        import random as _random

        diatonic = _build_diatonic_chords(scale)
        minor_chords = _build_diatonic_chords(Scale(root=scale.root, mode=Mode.NATURAL_MINOR))
        borrowed = [
            (r, q) for r, q in minor_chords if all(r != dr or q != dq for dr, dq in diatonic)
        ]
        cp = self._get_cp(duration_beats)
        result = []

        for i, start in enumerate(cp):
            end = cp[i + 1] if i + 1 < len(cp) else duration_beats
            obs = set(n.pitch % 12 for n in melody if start <= n.start < end)

            if _random.random() < self.borrow_prob and borrowed:
                root, qual = _random.choice(borrowed)
                cpcs = set(_chord_pcs_for_degree(root, qual))
                if obs and not obs & cpcs:
                    root, qual = diatonic[0]  # fallback
            else:
                best, best_fit = 0, -1
                for j, (rpc, q) in enumerate(diatonic):
                    fit = len(obs & set(_chord_pcs_for_degree(rpc, q)))
                    if fit > best_fit:
                        best_fit, best = fit, j
                root, qual = diatonic[best]

            result.append(
                ChordLabel(
                    root=root, quality=qual, start=round(start, 6), duration=round(end - start, 6),
                    degree=scale.degree_of(root),
                )
            )
        return result

    def _get_cp(self, duration):
        pts, t, step = [], 0.0, 4.0 if self.chord_change == "bars" else 2.0
        while t < duration:
            pts.append(t)
            t += step
        return pts
