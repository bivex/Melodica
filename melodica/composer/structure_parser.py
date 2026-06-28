# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
composer/structure_parser.py — RC-style Structure Notation Parser.

Layer: Domain / Application

Parses structure strings like "AABB", "AA'BB", "A1 A1 B1 B1", "A_var A_inv B B_fast"
into PhraseSlot lists, handling:

1. The Letter Rule: same letter = same deterministic seed (identical phrase content).
2. Prime notation (A'): variation of the base phrase (runs through variation stack).
3. Numeric subscripts (A1, B2): alternative seeds within the same letter group.
4. Suffix notation (_var, _inv, _fast, _retro): automatic transformations.

Grammar:
    structure   := segment (space segment)*
    segment     := letter [subscript] [prime] [suffix]
    letter      := A-Z
    subscript   := digit+
    prime       := "'"*
    suffix      := "_" identifier
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from melodica.idea_tool import PhraseSlot


class PhraseTransform(str, Enum):
    ORIGINAL = "original"
    INVERSION = "inversion"
    RETROGRADE = "retrograde"
    RETROGRADE_INVERSION = "retrograde_inversion"
    AUGMENTATION = "augmentation"
    DIMINUTION = "diminution"
    VAR = "var"
    FAST = "fast"


_SUFFIX_MAP: dict[str, PhraseTransform] = {
    "var": PhraseTransform.VAR,
    "inv": PhraseTransform.INVERSION,
    "retro": PhraseTransform.RETROGRADE,
    "retro_inv": PhraseTransform.RETROGRADE_INVERSION,
    "fast": PhraseTransform.FAST,
    "aug": PhraseTransform.AUGMENTATION,
    "dim": PhraseTransform.DIMINUTION,
}


@dataclass(frozen=True)
class ParsedSegment:
    """A single parsed segment from a structure string."""
    letter: str
    subscript: str = ""
    prime_count: int = 0
    suffix: str = ""
    bars: int = 4

    @property
    def label(self) -> str:
        parts = [self.letter]
        if self.subscript:
            parts.append(self.subscript)
        return "".join(parts)

    @property
    def base_label(self) -> str:
        return self.letter + self.subscript

    @property
    def transform(self) -> PhraseTransform:
        if self.suffix and self.suffix in _SUFFIX_MAP:
            return _SUFFIX_MAP[self.suffix]
        if self.prime_count > 0:
            if self.prime_count == 1:
                return PhraseTransform.VAR
            elif self.prime_count == 2:
                return PhraseTransform.INVERSION
            else:
                return PhraseTransform.RETROGRADE_INVERSION
        return PhraseTransform.ORIGINAL

    @property
    def has_variation(self) -> bool:
        return self.prime_count > 0 or (self.suffix != "" and self.suffix != "original")


_SEGMENT_RE = re.compile(
    r"^([A-Z])"          # letter
    r"(\d*)?"            # optional subscript
    r"('+)*?"            # optional primes
    r"(?:_([a-z_]+))?$"  # optional suffix
)

_COMPACT_SEGMENT_RE = re.compile(
    r"([A-Z]\d*'*|(?:_[a-z]+)?)"  
)


def parse_structure(structure: str, bars_per_segment: int = 4) -> list[ParsedSegment]:
    tokens = structure.strip().split()

    if not tokens:
        return []

    if len(tokens) == 1 and not re.search(r"[_']", tokens[0]):
        segments: list[ParsedSegment] = []
        for ch in tokens[0]:
            if ch.isalpha() and ch.isupper():
                segments.append(ParsedSegment(letter=ch, bars=bars_per_segment))
        return segments

    if len(tokens) == 1 and re.search(r"[A-Z].*[A-Z]", tokens[0]):
        expanded_tokens = _split_compact(tokens[0])
        return [_parse_token(t, bars_per_segment) for t in expanded_tokens if _parse_token(t, bars_per_segment) is not None]

    result: list[ParsedSegment] = []
    for token in tokens:
        seg = _parse_token(token, bars_per_segment)
        if seg is not None:
            result.append(seg)
    return result


def _split_compact(token: str) -> list[str]:
    """Split compact notation like AA'BB or AB_fastCD into individual tokens."""
    parts: list[str] = []
    i = 0
    while i < len(token):
        if token[i].isupper():
            start = i
            i += 1
            # Collect digits (subscript)
            while i < len(token) and token[i].isdigit():
                i += 1
            # Collect primes
            while i < len(token) and token[i] == "'":
                i += 1
            # Collect optional suffix starting with '_'
            if i < len(token) and token[i] == "_":
                i += 1
                while i < len(token) and (token[i].islower() or token[i] == "_"):
                    i += 1
            parts.append(token[start:i])
        else:
            i += 1
    return parts


def _parse_token(token: str, bars: int) -> ParsedSegment | None:
    m = _SEGMENT_RE.match(token)
    if not m:
        return None
    letter = m.group(1)
    subscript = m.group(2) or ""
    primes = m.group(3) or ""
    suffix = m.group(4) or ""
    return ParsedSegment(
        letter=letter,
        subscript=subscript,
        prime_count=len(primes),
        suffix=suffix,
        bars=bars,
    )


def structure_to_slots(
    structure: str,
    bars_per_segment: int = 4,
) -> "list[PhraseSlot]":
    from melodica.idea_tool import PhraseSlot
    segments = parse_structure(structure, bars_per_segment)
    slots: "list[PhraseSlot]" = []
    for seg in segments:
        if seg.letter == "R":
            slots.append(PhraseSlot(kind="rest", bars=seg.bars, label="R"))
        else:
            slots.append(PhraseSlot(
                kind="play",
                bars=seg.bars,
                label=_build_slot_label(seg),
            ))
    return slots


def _build_slot_label(seg: ParsedSegment) -> str:
    label = seg.base_label
    if seg.has_variation:
        label += f":{seg.transform.value}"
    return label


@dataclass
class PhrasePool:
    """
    Shared pool of generated phrase notes, keyed by (track_name, base_label).

    Implements the RC "Letter Rule": same letter = same seed = same content.
    When a slot references a phrase already in the pool, the generator is
    skipped and the stored notes are reused (optionally transformed).
    """
    _pool: dict[str, list[Any]] = field(default_factory=dict)

    def key(self, track_name: str, base_label: str) -> str:
        return f"{track_name}::{base_label}"

    def store(self, track_name: str, base_label: str, notes: list[Any]) -> None:
        k = self.key(track_name, base_label)
        self._pool[k] = list(notes)

    def get(self, track_name: str, base_label: str) -> list[Any] | None:
        v = self._pool.get(self.key(track_name, base_label))
        return list(v) if v is not None else None

    def has(self, track_name: str, base_label: str) -> bool:
        return self.key(track_name, base_label) in self._pool

    def clear(self) -> None:
        self._pool.clear()


def parse_slot_label(label: str) -> tuple[str, PhraseTransform]:
    if ":" in label:
        base, transform_str = label.rsplit(":", 1)
        try:
            transform = PhraseTransform(transform_str)
        except ValueError:
            transform = PhraseTransform.ORIGINAL
        return base, transform
    return label, PhraseTransform.ORIGINAL


def apply_phrase_transform(
    notes: list[Any],
    transform: PhraseTransform,
) -> list[Any]:
    if transform == PhraseTransform.ORIGINAL or not notes:
        return list(notes)

    from melodica.types import NoteInfo

    if transform == PhraseTransform.INVERSION:
        return _invert_notes(notes)
    if transform == PhraseTransform.RETROGRADE:
        return _retrograde_notes(notes)
    if transform == PhraseTransform.RETROGRADE_INVERSION:
        return _retrograde_notes(_invert_notes(notes))
    if transform == PhraseTransform.FAST:
        return _diminish_notes(notes, factor=2.0)
    if transform == PhraseTransform.AUGMENTATION:
        return _augment_notes(notes, factor=2.0)
    if transform == PhraseTransform.DIMINUTION:
        return _diminish_notes(notes, factor=2.0)
    if transform == PhraseTransform.VAR:
        return _auto_vary(notes)

    return list(notes)


def _invert_notes(notes: list[Any]) -> list[Any]:
    from melodica.types import NoteInfo
    if len(notes) < 2:
        return list(notes)
    result = [notes[0]]
    for i in range(1, len(notes)):
        interval = notes[i].pitch - notes[i - 1].pitch
        new_pitch = max(0, min(127, result[-1].pitch - interval))
        result.append(NoteInfo(
            pitch=new_pitch,
            start=notes[i].start,
            duration=notes[i].duration,
            velocity=notes[i].velocity,
            articulation=notes[i].articulation,
            expression=dict(notes[i].expression),
        ))
    return result


def _retrograde_notes(notes: list[Any]) -> list[Any]:
    from melodica.types import NoteInfo
    if not notes:
        return []
    min_start = min(n.start for n in notes)
    max_end = max(n.start + n.duration for n in notes)
    phrase_dur = max_end - min_start
    result = []
    for n in reversed(notes):
        rel = n.start - min_start
        new_rel = phrase_dur - (rel + n.duration)
        result.append(NoteInfo(
            pitch=n.pitch,
            start=round(new_rel, 6),
            duration=n.duration,
            velocity=n.velocity,
            articulation=n.articulation,
            expression=dict(n.expression),
        ))
    result.sort(key=lambda x: x.start)
    return result


def _diminish_notes(notes: list[Any], factor: float = 2.0) -> list[Any]:
    from melodica.types import NoteInfo
    return [
        NoteInfo(
            pitch=n.pitch,
            start=round(n.start / factor, 6),
            duration=max(0.0625, n.duration / factor),
            velocity=n.velocity,
            articulation=n.articulation,
            expression=dict(n.expression),
        )
        for n in notes
    ]


def _augment_notes(notes: list[Any], factor: float = 2.0) -> list[Any]:
    from melodica.types import NoteInfo
    return [
        NoteInfo(
            pitch=n.pitch,
            start=round(n.start * factor, 6),
            duration=n.duration * factor,
            velocity=n.velocity,
            articulation=n.articulation,
            expression=dict(n.expression),
        )
        for n in notes
    ]


def _auto_vary(notes: list[Any]) -> list[Any]:
    import random as _rng
    from melodica.types import NoteInfo

    if not notes:
        return []

    transforms = [
        lambda ns: [
            NoteInfo(pitch=max(0, min(127, n.pitch + _rng.randint(-3, 3))),
                     start=n.start, duration=n.duration,
                     velocity=n.velocity, articulation=n.articulation,
                     expression=dict(n.expression))
            for n in ns
        ],
        _invert_notes,
        _retrograde_notes,
        lambda ns: [
            NoteInfo(pitch=n.pitch, start=n.start,
                     duration=max(0.0625, n.duration * _rng.uniform(0.7, 1.3)),
                     velocity=n.velocity, articulation=n.articulation,
                     expression=dict(n.expression))
            for n in ns
        ],
    ]
    chosen = _rng.choice(transforms)
    return chosen(notes)
