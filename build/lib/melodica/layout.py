"""
layout.py — Modern UI/UX Layout Engine for Phrase Ordering.

Layer: Application / Interface
Supports: Custom Phrase Order string parsing (e.g., "A4 R2 B2 C2 R2 D2 E4 R2 F2 G2 R2 A2 B2 R2").
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from melodica.types import Scale, ChordLabel, Quality
from melodica.theory.modulation import ModulationEngine


@dataclass
class PhraseOrderUnit:
    """A single unit in the phrase order (e.g. 'A4' or 'R2')."""
    label: str  # 'A', 'B', 'R', etc.
    length: float  # Length in quarter notes
    variation: int = 0  # Number of variations (A' = 1, A'' = 2)


@dataclass
class KeySection:
    """A section of the composition with its own key and optional progression."""
    label: str
    key: Scale
    length: float
    progression: str | None = None  # Roman numeral progression within this section


class PhraseOrderParser:
    """
    Parses a custom phrase order string into a sequence of instructions.
    Logic:
    - Letters (A, B...) are phrases.
    - 'R' is a rest.
    - Number after letter (A4) is length.
    - Length is persistent until the next length is specified.
    - ' is a variation.
    """

    def parse(self, pattern: str) -> list[PhraseOrderUnit]:
        pattern = pattern.strip()
        # Regex to find tokens like A4, B, R2, A', A''4, etc.
        # Group 1: Label (A-Z or R)
        # Group 2: Variations (')
        # Group 3: Optional Length (digits)
        tokens = re.findall(r"([A-Z])('+)?(\d*)", pattern)

        result: list[PhraseOrderUnit] = []
        current_length = 4.0  # Default length if none specified initially

        for label, vars_str, len_str in tokens:
            if len_str:
                current_length = float(len_str)

            variation_count = len(vars_str) if vars_str else 0

            result.append(PhraseOrderUnit(
                label=label,
                length=current_length,
                variation=variation_count
            ))

        return result


def build_section_chords(
    sections: list[KeySection],
    transition_beats: float = 4.0,
) -> list[ChordLabel]:
    """
    Build chords for a multi-section composition with automatic
    modulation transitions between sections.

    For each section, if a progression is given, it is parsed in that section's key.
    Between sections, ModulationEngine inserts a pivot-chord transition.
    """
    from melodica.types import parse_progression

    chords: list[ChordLabel] = []
    t = 0.0

    for i, section in enumerate(sections):
        # --- Transition from previous key ---
        if i > 0:
            prev_key = sections[i - 1].key
            trans_chords = _transition_chords(prev_key, section.key, t, transition_beats)
            chords.extend(trans_chords)
            t += transition_beats

        # --- Section chords ---
        if section.progression:
            section_chords = parse_progression(section.progression, section.key)
            # Offset to correct position
            for c in section_chords:
                c.start += t
            chords.extend(section_chords)
        else:
            # Default: tonic chord held for the section length
            chords.append(ChordLabel(
                root=section.key.root,
                quality=Quality.MAJOR if section.key.mode.value == "major" else Quality.MINOR,
                start=t,
                duration=section.length,
            ))

        t += section.length

    return chords


def _transition_chords(
    from_key: Scale,
    to_key: Scale,
    start_time: float,
    duration: float,
) -> list[ChordLabel]:
    """Generate pivot-chord transition between two keys."""
    pivots = ModulationEngine.find_pivot_chords(from_key, to_key)

    if pivots:
        pivot_chord, _, _ = pivots[0]
    else:
        # No common chord — use V of target key as secondary dominant
        pivot_chord = ChordLabel(
            root=(to_key.root + 7) % 12,  # dominant
            quality=Quality.MAJOR,
            start=0,
            duration=duration,
        )

    half = duration / 2.0
    return [
        ChordLabel(
            root=pivot_chord.root,
            quality=pivot_chord.quality,
            start=start_time,
            duration=half,
        ),
        ChordLabel(
            root=to_key.root,
            quality=Quality.MAJOR if to_key.mode.value == "major" else Quality.MINOR,
            start=start_time + half,
            duration=half,
        ),
    ]


@dataclass
class CompositionTimeline:
    """
    Orchestrates the global timeline based on a phrase order.
    Maps labels to specific generator/preset configs.
    """
    phrase_order: str
    tracks_presets: dict[str, str]  # "Bass": "madonna_groove", etc.

    def get_full_duration(self) -> float:
        parser = PhraseOrderParser()
        units = parser.parse(self.phrase_order)
        return sum(u.length for u in units)

    def build_arrangement_plan(self) -> list[dict[str, Any]]:
        """
        Returns a plan for each track with precise timing.
        """
        parser = PhraseOrderParser()
        units = parser.parse(self.phrase_order)

        plan = []
        current_time = 0.0

        for unit in units:
            unit_data = {
                "start": current_time,
                "duration": unit.length,
                "label": unit.label,
                "is_rest": unit.label == "R",
                "variation": unit.variation
            }
            plan.append(unit_data)
            current_time += unit.length

        return plan
