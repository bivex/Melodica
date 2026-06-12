"""composer/cof_navigator.py — Circle-of-Fifths modulation planner for albums.

Plans a sequence of key modulations across an album's tracks using the
circle of fifths.  Supports:

  - Chain modulation (step by step around CoF)
  - Enharmonic reinterpretation via dim7 / augmented pivot chords
  - Parallel key switches (C major → C minor)
  - Distance-ranked key suggestions

Usage
-----
    from melodica.types import Scale, Mode
    from melodica.composer.cof_navigator import CoFNavigator

    nav = CoFNavigator()

    # Plan a 5-track album starting in C major
    start = Scale(0, Mode.MAJOR)
    plan = nav.plan_album(start, n_tracks=5, strategy="cof_chain")
    for step in plan:
        print(step)

    # Or get suggestions from current key
    suggestions = nav.suggest_next(start, n=3)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from melodica.types_pkg._theory import Scale, Mode


# ---------------------------------------------------------------------------
# Circle of Fifths layout
# ---------------------------------------------------------------------------

# Pitch classes in CoF order (C G D A E B F# C# G# D# A# F)
_COF_ORDER: list[int] = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]
_COF_INDEX: dict[int, int] = {pc: i for i, pc in enumerate(_COF_ORDER)}

# Enharmonic equivalents for notation
_PC_NAMES: dict[int, str] = {
    0: "C", 1: "C#/Db", 2: "D", 3: "D#/Eb", 4: "E", 5: "F",
    6: "F#/Gb", 7: "G", 8: "G#/Ab", 9: "A", 10: "A#/Bb", 11: "B",
}

# Dim7 pivot chords: each dim7 chord connects 4 keys via enharmonic reinterpretation
# Stored as (pivot_dim7_root_pc, [target_key_pcs])
_DIM7_PIVOTS: list[tuple[int, list[int]]] = [
    (11, [0, 3, 6, 9]),   # Bdim7 → C, Eb, F#, A
    (0,  [1, 4, 7, 10]),  # Cdim7 → Db, E, G, Bb
    (1,  [2, 5, 8, 11]),  # C#dim7 → D, F, Ab, B
]

# Augmented pivot chords: connect 3 keys
_AUG_PIVOTS: list[tuple[int, list[int]]] = [
    (0,  [0, 4, 8]),   # Caug → C, E, Ab
    (1,  [1, 5, 9]),   # C#aug → Db, F, A
    (2,  [2, 6, 10]),  # Daug → D, F#, Bb
    (3,  [3, 7, 11]),  # Ebaug → Eb, G, B
]


def cof_distance(pc_a: int, pc_b: int) -> int:
    """Shortest distance between two pitch classes on the circle of fifths (0–6)."""
    ia = _COF_INDEX[pc_a % 12]
    ib = _COF_INDEX[pc_b % 12]
    diff = abs(ia - ib)
    return min(diff, 12 - diff)


def relative_minor(scale: Scale) -> Scale:
    """Return the relative minor of a major scale (or relative major of minor)."""
    if scale.mode in (Mode.MAJOR,):
        return Scale((scale.root + 9) % 12, Mode.NATURAL_MINOR)
    return Scale((scale.root + 3) % 12, Mode.MAJOR)


def parallel_key(scale: Scale) -> Scale:
    """Return the parallel key (same root, opposite mode)."""
    if scale.mode in (Mode.MAJOR,):
        return Scale(scale.root, Mode.NATURAL_MINOR)
    return Scale(scale.root, Mode.MAJOR)


# ---------------------------------------------------------------------------
# ModulationStep — one key change in a plan
# ---------------------------------------------------------------------------

@dataclass
class ModulationStep:
    """One step in a modulation plan.

    Attributes
    ----------
    from_scale : Scale
        Source key.
    to_scale : Scale
        Destination key.
    cof_distance : int
        Distance on circle of fifths (0–6).
    method : str
        How the modulation is achieved:
        'direct'      — no pivot, abrupt change
        'pivot'       — common chord pivot (see ModulationEngine)
        'dominant'    — V7 → I approach
        'dim7'        — enharmonic dim7 reinterpretation
        'augmented'   — enharmonic augmented reinterpretation
        'parallel'    — parallel key switch (same root)
        'relative'    — relative major/minor
    pivot_pc : int | None
        Pitch class of the pivot chord root, if applicable.
    """
    from_scale: Scale
    to_scale: Scale
    cof_distance: int
    method: str
    pivot_pc: int | None = None

    def __str__(self) -> str:
        from_name = f"{_PC_NAMES[self.from_scale.root % 12]} {self.from_scale.mode.name}"
        to_name   = f"{_PC_NAMES[self.to_scale.root % 12]} {self.to_scale.mode.name}"
        pivot = f" (pivot PC={_PC_NAMES[self.pivot_pc]})" if self.pivot_pc is not None else ""
        return f"{from_name} → {to_name}  [{self.method}, dist={self.cof_distance}]{pivot}"


# ---------------------------------------------------------------------------
# CoFNavigator
# ---------------------------------------------------------------------------

class CoFNavigator:
    """Circle-of-Fifths modulation navigator.

    Plans key sequences for albums, suggests next keys, and identifies
    enharmonic pivot opportunities.
    """

    def suggest_next(
        self,
        current: Scale,
        n: int = 4,
        *,
        allow_relative: bool = True,
        allow_parallel: bool = True,
        max_cof_distance: int = 3,
    ) -> list[ModulationStep]:
        """Suggest the n best next keys from the current key.

        Keys are ranked by:
          1. CoF distance (closer = more natural)
          2. Relative/parallel relationships (free jumps)
          3. Enharmonic pivot availability

        Parameters
        ----------
        current : Scale
            Current key.
        n : int
            Number of suggestions to return.
        allow_relative : bool
            Include relative major/minor as a suggestion.
        allow_parallel : bool
            Include parallel key as a suggestion.
        max_cof_distance : int
            Maximum CoF distance for direct modulation suggestions.

        Returns
        -------
        list[ModulationStep]
            Ranked suggestions (best first).
        """
        suggestions: list[ModulationStep] = []
        seen: set[tuple[int, str]] = set()

        def _add(to: Scale, method: str, pivot_pc: int | None = None):
            key = (to.root % 12, to.mode.name)
            if key == (current.root % 12, current.mode.name):
                return
            if key in seen:
                return
            seen.add(key)
            dist = cof_distance(current.root, to.root)
            suggestions.append(ModulationStep(
                from_scale=current,
                to_scale=to,
                cof_distance=dist,
                method=method,
                pivot_pc=pivot_pc,
            ))

        # 1. Adjacent keys on CoF (±1, ±2, ±3 steps)
        cur_idx = _COF_INDEX[current.root % 12]
        for step in range(1, max_cof_distance + 1):
            for direction in (+1, -1):
                next_pc = _COF_ORDER[(cur_idx + direction * step) % 12]
                next_mode = current.mode  # same mode family
                _add(Scale(next_pc, next_mode), "pivot" if step <= 2 else "dominant")

        # 2. Relative key
        if allow_relative:
            _add(relative_minor(current), "relative")

        # 3. Parallel key
        if allow_parallel:
            _add(parallel_key(current), "parallel")

        # 4. Dim7 enharmonic targets
        for dim_root, targets in _DIM7_PIVOTS:
            if current.root % 12 in targets:
                for t in targets:
                    if t != current.root % 12:
                        _add(Scale(t, current.mode), "dim7", pivot_pc=dim_root)

        # 5. Augmented enharmonic targets
        for aug_root, targets in _AUG_PIVOTS:
            if current.root % 12 in targets:
                for t in targets:
                    if t != current.root % 12:
                        _add(Scale(t, current.mode), "augmented", pivot_pc=aug_root)

        # Sort: relative/parallel first (free), then by distance
        def _rank(s: ModulationStep) -> tuple[int, int]:
            method_priority = {"relative": 0, "parallel": 1, "pivot": 2, "dominant": 3,
                               "dim7": 4, "augmented": 4, "direct": 5}
            return (method_priority.get(s.method, 9), s.cof_distance)

        suggestions.sort(key=_rank)
        return suggestions[:n]

    def plan_album(
        self,
        start: Scale,
        n_tracks: int,
        strategy: Literal["cof_chain", "cof_arch", "enharmonic", "dramatic"] = "cof_chain",
        *,
        seed: int | None = None,
    ) -> list[ModulationStep]:
        """Plan a sequence of key modulations for an entire album.

        Strategies
        ----------
        cof_chain   — step clockwise around CoF (sharpward).
                      Each track is one fifth up from the previous.
        cof_arch    — go sharpward for the first half, then flatward back
                      (tension arc: builds then releases).
        enharmonic  — use dim7 enharmonic pivots for distant key jumps.
                      Generates surprise / unexpected colour changes.
        dramatic    — alternate between relative minor and dominant key.
                      Creates strong contrast between tracks.

        Parameters
        ----------
        start : Scale
            Key of the first track.
        n_tracks : int
            Number of tracks (one Scale per track, n_tracks-1 modulation steps).
        strategy : str
            Modulation strategy.
        seed : int | None
            Random seed for 'enharmonic' strategy.

        Returns
        -------
        list[ModulationStep]
            n_tracks-1 modulation steps.
        """
        import random
        rng = random.Random(seed)

        scales: list[Scale] = [start]
        cur = start

        for i in range(n_tracks - 1):
            cur_idx = _COF_INDEX[cur.root % 12]

            if strategy == "cof_chain":
                # One step clockwise (sharpward = +7 semitones)
                next_pc = _COF_ORDER[(cur_idx + 1) % 12]
                nxt = Scale(next_pc, cur.mode)
                method = "pivot"

            elif strategy == "cof_arch":
                half = (n_tracks - 1) // 2
                direction = +1 if i < half else -1
                next_pc = _COF_ORDER[(cur_idx + direction) % 12]
                nxt = Scale(next_pc, cur.mode)
                method = "pivot"

            elif strategy == "enharmonic":
                # Use dim7 pivot for distant jumps
                available = []
                for dim_root, targets in _DIM7_PIVOTS:
                    for t in targets:
                        if t != cur.root % 12:
                            available.append((t, dim_root))
                if available:
                    t, pivot = rng.choice(available)
                    nxt = Scale(t, cur.mode)
                    method = "dim7"
                else:
                    next_pc = _COF_ORDER[(cur_idx + 1) % 12]
                    nxt = Scale(next_pc, cur.mode)
                    method = "pivot"
                    pivot = None  # type: ignore[assignment]

            elif strategy == "dramatic":
                # Alternate: relative minor → dominant → relative minor ...
                if i % 2 == 0:
                    nxt = relative_minor(cur)
                    method = "relative"
                else:
                    dom_pc = (cur.root + 7) % 12
                    nxt = Scale(dom_pc, cur.mode)
                    method = "dominant"

            else:
                raise ValueError(f"Unknown strategy: {strategy!r}")

            dist = cof_distance(cur.root, nxt.root)
            pivot_pc = None
            if strategy == "enharmonic" and method == "dim7":
                pivot_pc = pivot  # type: ignore[possibly-undefined]

            scales.append(nxt)
            cur = nxt

        # Build steps from scale sequence
        steps: list[ModulationStep] = []
        method_map = {"pivot": "pivot", "dominant": "dominant",
                      "relative": "relative", "dim7": "dim7"}
        for i in range(len(scales) - 1):
            a, b = scales[i], scales[i + 1]
            dist = cof_distance(a.root, b.root)
            # Re-derive method
            if b.root == (a.root + 9) % 12 and b.mode != a.mode:
                m = "relative"
            elif b.root == a.root and b.mode != a.mode:
                m = "parallel"
            elif dist <= 1:
                m = "pivot"
            elif dist <= 2:
                m = "dominant"
            else:
                m = "dim7" if strategy == "enharmonic" else "direct"
            steps.append(ModulationStep(
                from_scale=a, to_scale=b,
                cof_distance=dist, method=m,
            ))

        return steps

    def enharmonic_dim7_targets(self, current: Scale) -> list[ModulationStep]:
        """Return all keys reachable via dim7 enharmonic reinterpretation."""
        results = []
        for dim_root, targets in _DIM7_PIVOTS:
            if current.root % 12 in targets:
                for t in targets:
                    if t != current.root % 12:
                        dist = cof_distance(current.root, t)
                        results.append(ModulationStep(
                            from_scale=current,
                            to_scale=Scale(t, current.mode),
                            cof_distance=dist,
                            method="dim7",
                            pivot_pc=dim_root,
                        ))
        return results

    def cof_position(self, scale: Scale) -> int:
        """Return the position of scale.root on the circle of fifths (0–11)."""
        return _COF_INDEX[scale.root % 12]

    def keys_at_distance(self, scale: Scale, distance: int) -> list[Scale]:
        """Return all keys at exactly `distance` steps on the CoF."""
        cur_idx = _COF_INDEX[scale.root % 12]
        pcs = set()
        pcs.add(_COF_ORDER[(cur_idx + distance) % 12])
        pcs.add(_COF_ORDER[(cur_idx - distance) % 12])
        return [Scale(pc, scale.mode) for pc in sorted(pcs)]
