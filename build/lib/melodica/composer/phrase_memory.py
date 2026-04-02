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
composer/phrase_memory.py — Phrase memory for motif recall and reuse.

Layer: Domain / Application
Style: All styles — universal compositional memory system.

Stores generated phrases and allows retrieval with transformations.
Generators can save phrases they generate and later recall them
with variations (transpose, invert, retrograde, augment, etc.).

This makes the music "memorable" — motifs return in varied forms,
creating thematic coherence across sections.

Usage:
    memory = PhraseMemory()

    # Save a phrase
    memory.store(Phrase(
        notes=generated_notes,
        section="verse",
        bar=4,
        chord_root=0,
    ))

    # Recall with transformation
    recalled = memory.recall(
        section="chorus",
        transform="retrograde_inversion",
        transpose=5,
    )
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum

from melodica.types import NoteInfo


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OCTAVE = 12
_MAX_MEMORY = 32


# ---------------------------------------------------------------------------
# Transform types
# ---------------------------------------------------------------------------


class Transform(str, Enum):
    """Available phrase transformations."""

    ORIGINAL = "original"
    TRANSPOSE = "transpose"
    INVERSION = "inversion"
    RETROGRADE = "retrograde"
    RETROGRADE_INVERSION = "retrograde_inversion"
    AUGMENTATION = "augmentation"
    DIMINUTION = "diminution"


# ---------------------------------------------------------------------------
# Phrase
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Phrase:
    """A stored musical phrase with metadata."""

    notes: tuple[NoteInfo, ...]  # frozen — stored as tuple
    section: str = ""
    bar: int = 0
    chord_root: int = 0
    tag: str = ""  # user-defined label (e.g., "main_theme", "response")

    @property
    def pitch_contour(self) -> list[int]:
        return [n.pitch for n in self.notes]

    @property
    def rhythm_pattern(self) -> list[float]:
        return [n.duration for n in self.notes]

    @property
    def length(self) -> int:
        return len(self.notes)

    def similarity(self, other: Phrase) -> float:
        """Cosine-like similarity between pitch contours (0.0–1.0)."""
        if not self.notes or not other.notes:
            return 0.0
        a = self.pitch_contour
        b = other.pitch_contour
        # Normalise lengths to shorter
        n = min(len(a), len(b))
        a, b = a[:n], b[:n]
        # Interval-based similarity
        intervals_a = [a[i + 1] - a[i] for i in range(n - 1)]
        intervals_b = [b[i + 1] - b[i] for i in range(n - 1)]
        if not intervals_a or not intervals_b:
            return 0.0
        # Count matching interval directions
        matches = sum(1 for x, y in zip(intervals_a, intervals_b) if (x > 0) == (y > 0))
        return matches / max(len(intervals_a), 1)


# ---------------------------------------------------------------------------
# Phrase Memory
# ---------------------------------------------------------------------------


@dataclass
class PhraseMemory:
    """
    Memory bank for musical phrases.

    Stores up to `max_size` phrases. Phrases can be recalled by:
    - Section name
    - Tag
    - Similarity to a target phrase
    - Random selection
    - Recency (most recent first)

    Recalled phrases can be transformed (transpose, invert, etc.).
    """

    max_size: int = _MAX_MEMORY
    _bank: list[Phrase] = field(default_factory=list, init=False, repr=False)

    # ------------------------------------------------------------------
    # Storage
    # ------------------------------------------------------------------

    def store(self, phrase: Phrase) -> None:
        """Add a phrase to memory. Evicts oldest if full."""
        self._bank.append(phrase)
        if len(self._bank) > self.max_size:
            self._bank = self._bank[-self.max_size :]

    def store_notes(
        self,
        notes: list[NoteInfo],
        section: str = "",
        bar: int = 0,
        chord_root: int = 0,
        tag: str = "",
    ) -> None:
        """Convenience: store a list of NoteInfo directly."""
        self.store(
            Phrase(
                notes=tuple(notes),
                section=section,
                bar=bar,
                chord_root=chord_root,
                tag=tag,
            )
        )

    def clear(self) -> None:
        self._bank.clear()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @property
    def size(self) -> int:
        return len(self._bank)

    def has_phrases(self) -> bool:
        return bool(self._bank)

    def get_all(self) -> list[Phrase]:
        return list(self._bank)

    def get_by_section(self, section: str) -> list[Phrase]:
        return [p for p in self._bank if p.section == section]

    def get_by_tag(self, tag: str) -> list[Phrase]:
        return [p for p in self._bank if p.tag == tag]

    def get_most_recent(self, n: int = 1) -> list[Phrase]:
        return self._bank[-n:]

    def find_similar(self, target: Phrase, top_k: int = 3) -> list[Phrase]:
        """Find most similar phrases by pitch contour."""
        scored = [(p, p.similarity(target)) for p in self._bank]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, _ in scored[:top_k]]

    # ------------------------------------------------------------------
    # Recall with transformation
    # ------------------------------------------------------------------

    def recall(
        self,
        *,
        section: str | None = None,
        tag: str | None = None,
        transform: str = "original",
        transpose: int = 0,
        anchor_pitch: int | None = None,
        low: int = 36,
        high: int = 96,
    ) -> list[NoteInfo] | None:
        """
        Recall a phrase from memory with optional transformation.

        section:     Filter by section name
        tag:         Filter by tag
        transform:   One of Transform values
        transpose:   Semitone offset (for "transpose" or applied to all)
        anchor_pitch: If set, transpose so first note matches this pitch
        low, high:   Range clamp after transformation
        """
        candidates = self._filter(section, tag)
        if not candidates:
            return None

        phrase = random.choice(candidates)
        notes = list(phrase.notes)

        # Apply transformation
        notes = _apply_transform(notes, transform)

        # Transpose
        if anchor_pitch is not None and notes:
            transpose = anchor_pitch - notes[0].pitch
        if transpose != 0:
            notes = [
                NoteInfo(
                    pitch=n.pitch + transpose,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in notes
            ]

        # Range clamp
        notes = [
            NoteInfo(
                pitch=max(low, min(high, n.pitch)),
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                articulation=n.articulation,
                expression=n.expression,
            )
            for n in notes
        ]

        return notes

    def recall_as_new_sequence(
        self,
        *,
        section: str | None = None,
        tag: str | None = None,
        transform: str = "original",
        transpose: int = 0,
        start_at: float = 0.0,
        low: int = 36,
        high: int = 96,
    ) -> list[NoteInfo] | None:
        """
        Recall a phrase, re-time it to start at `start_at`, return as new notes.
        Useful for inserting recalled material at a specific beat.
        """
        notes = self.recall(
            section=section,
            tag=tag,
            transform=transform,
            transpose=transpose,
            low=low,
            high=high,
        )
        if not notes:
            return None

        # Re-time: shift all starts to start_at
        if notes:
            first_start = min(n.start for n in notes)
            offset = start_at - first_start
            notes = [
                NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + offset, 6),
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in notes
            ]

        return notes

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _filter(self, section: str | None, tag: str | None) -> list[Phrase]:
        candidates = self._bank
        if section is not None:
            candidates = [p for p in candidates if p.section == section]
        if tag is not None:
            candidates = [p for p in candidates if p.tag == tag]
        return candidates


# ---------------------------------------------------------------------------
# Transform functions
# ---------------------------------------------------------------------------


def _apply_transform(notes: list[NoteInfo], transform: str) -> list[NoteInfo]:
    if transform == "original" or not notes:
        return list(notes)
    if transform == "retrograde":
        return _retrograde(notes)
    if transform == "inversion":
        return _inversion(notes)
    if transform == "retrograde_inversion":
        return _retrograde(_inversion(notes))
    if transform == "augmentation":
        return _augmentation(notes)
    if transform == "diminution":
        return _diminution(notes)
    return list(notes)


def _retrograde(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Reverse note order, re-time from start."""
    if not notes:
        return []
    total_dur = max(n.start + n.duration for n in notes)
    reversed_notes = list(reversed(notes))
    # Re-time: first note starts at 0
    offset = reversed_notes[0].start
    return [
        NoteInfo(
            pitch=n.pitch,
            start=round(n.start - offset, 6),
            duration=n.duration,
            velocity=n.velocity,
            articulation=n.articulation,
            expression=n.expression,
        )
        for n in reversed_notes
    ]


def _inversion(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Invert intervals: reverse the direction of each interval."""
    if len(notes) < 2:
        return list(notes)
    result = [notes[0]]
    for i in range(1, len(notes)):
        interval = notes[i].pitch - notes[i - 1].pitch
        new_pitch = result[-1].pitch - interval
        result.append(
            NoteInfo(
                pitch=max(0, min(127, new_pitch)),
                start=notes[i].start,
                duration=notes[i].duration,
                velocity=notes[i].velocity,
                articulation=notes[i].articulation,
                expression=notes[i].expression,
            )
        )
    return result


def _augmentation(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Double all durations."""
    return [
        NoteInfo(
            pitch=n.pitch,
            start=n.start * 2,
            duration=n.duration * 2,
            velocity=n.velocity,
            articulation=n.articulation,
            expression=n.expression,
        )
        for n in notes
    ]


def _diminution(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Halve all durations."""
    return [
        NoteInfo(
            pitch=n.pitch,
            start=round(n.start * 0.5, 6),
            duration=max(0.125, n.duration * 0.5),
            velocity=n.velocity,
            articulation=n.articulation,
            expression=n.expression,
        )
        for n in notes
    ]
