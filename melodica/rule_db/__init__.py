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
rule_db/__init__.py — ChordProgressionRuleDB: weighted digraph of chord transitions.

Layer: Domain

Rules:
  - Pure domain logic; no I/O except for loading the JSON data file.
  - JSON file path is injected (not hardcoded) for testability.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from melodica.types import Quality


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------


@dataclass
class ProgressionRule:
    """One directed edge in the chord-progression graph."""

    from_degree: int         # 1–7 (Roman numeral)
    to_degree: int
    from_quality: Quality
    to_quality: Quality
    weight: float            # desirability 0–1
    context: list[str]       # tags: "classical", "jazz", "pop", …

    def __post_init__(self) -> None:
        if not (1 <= self.from_degree <= 7):
            raise ValueError(f"from_degree must be 1–7, got {self.from_degree}")
        if not (1 <= self.to_degree <= 7):
            raise ValueError(f"to_degree must be 1–7, got {self.to_degree}")
        if not (0.0 <= self.weight <= 1.0):
            raise ValueError(f"weight must be 0–1, got {self.weight}")


class ChordProgressionRuleDB:
    """
    Weighted digraph of allowed chord transitions.

    Port (interface) consumed by RuleBasedEngine.
    Concrete data comes from a JSON file or from the built-in default.
    """

    def __init__(self, rules: list[ProgressionRule]) -> None:
        self._rules = rules
        # Pre-index by (from_degree, from_quality) for O(1) lookup
        self._index: dict[tuple[int, Quality], list[ProgressionRule]] = {}
        for rule in rules:
            key = (rule.from_degree, rule.from_quality)
            self._index.setdefault(key, []).append(rule)

    # ------------------------------------------------------------------
    # Query interface
    # ------------------------------------------------------------------

    def successors(
        self,
        degree: int,
        quality: Quality,
        context: str = "classical",
        top_n: int = 5,
    ) -> list[tuple[int, Quality, float]]:
        """
        Return up to top_n (to_degree, to_quality, weight) tuples,
        filtered by context and sorted by weight descending.
        """
        candidates = self._index.get((degree, quality), [])
        filtered = [
            r for r in candidates
            if context in r.context
        ]
        filtered.sort(key=lambda r: r.weight, reverse=True)
        return [
            (r.to_degree, r.to_quality, r.weight)
            for r in filtered[:top_n]
        ]

    def all_rules(self) -> list[ProgressionRule]:
        return list(self._rules)

    # ------------------------------------------------------------------
    # Factory methods (DIP: callers depend on this abstraction, not I/O)
    # ------------------------------------------------------------------

    @classmethod
    def load(cls, path: str | Path) -> "ChordProgressionRuleDB":
        """Load a rule database from a JSON file at `path`."""
        data = Path(path).read_text(encoding="utf-8")
        return cls._from_json(data)

    @classmethod
    def default(cls) -> "ChordProgressionRuleDB":
        """
        Built-in rule set: classical, jazz, pop progressions.
        Loaded from the package-bundled default.json.
        """
        pkg_dir = Path(__file__).parent
        data = (pkg_dir / "default.json").read_text(encoding="utf-8")
        return cls._from_json(data)

    # ------------------------------------------------------------------
    # Internal deserialization
    # ------------------------------------------------------------------

    @classmethod
    def _from_json(cls, json_text: str) -> "ChordProgressionRuleDB":
        raw = json.loads(json_text)
        rules = [
            ProgressionRule(
                from_degree=r["from_degree"],
                to_degree=r["to_degree"],
                from_quality=Quality(r["from_quality"]),
                to_quality=Quality(r["to_quality"]),
                weight=float(r["weight"]),
                context=list(r.get("context", ["classical"])),
            )
            for r in raw["rules"]
        ]
        return cls(rules)
