"""LeitmotifRegistry — semantic binding layer for thematic motifs.

Maps named motifs to characters, places, emotions via tags, and provides
render() with chainable transforms using Motif.develop().
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.composer.motif import Motif
from melodica.types_pkg._notes import NoteInfo


@dataclass(slots=True)
class Leitmotif:
    """A named, tagged motif with instrument and register preferences."""

    name: str
    motif: Motif
    tags: list[str]
    default_instrument: int
    default_velocity: int
    register: int  # 0=low, 1=mid, 2=high


@dataclass
class LeitmotifRegistry:
    """Central registry for leitmotifs with semantic tag queries."""

    _motifs: dict[str, Leitmotif] = field(default_factory=dict)

    def register(
        self,
        name: str,
        motif: Motif,
        tags: list[str] | None = None,
        instrument: int = 48,
        velocity: int = 70,
        register: int = 1,
    ) -> Leitmotif:
        entry = Leitmotif(
            name=name,
            motif=motif,
            tags=tags or [],
            default_instrument=instrument,
            default_velocity=velocity,
            register=register,
        )
        self._motifs[name] = entry
        return entry

    def get(self, name: str) -> Leitmotif | None:
        return self._motifs.get(name)

    def by_tag(self, tag: str) -> list[Leitmotif]:
        return [m for m in self._motifs.values() if tag in m.tags]

    def render(
        self,
        name: str,
        *,
        offset: float = 0.0,
        transpose: int = 0,
        augment_factor: float | None = None,
        diminish_factor: float | None = None,
        invert: bool = False,
        retrograde: bool = False,
        fragment_start: float | None = None,
        fragment_end: float | None = None,
        sequence_intervals: list[int] | None = None,
        sequence_spacing: float | None = None,
    ) -> list[NoteInfo]:
        """Render a named motif with optional transforms, returning notes at *offset*."""
        entry = self._motifs.get(name)
        if entry is None:
            return []

        developed = entry.motif.develop(
            transpose=transpose if transpose != 0 else None,
            augment_factor=augment_factor,
            diminish_factor=diminish_factor,
            invert=invert,
            retrograde=retrograde,
            fragment_start=fragment_start,
            fragment_end=fragment_end,
            sequence_intervals=sequence_intervals,
            sequence_spacing=sequence_spacing,
        )
        return developed.render(offset=offset)

    def render_all(
        self,
        *,
        tag: str | None = None,
        offset: float = 0.0,
        **transform_kw,
    ) -> list[NoteInfo]:
        """Render all motifs (optionally filtered by tag) and merge."""
        entries = (
            self.by_tag(tag) if tag else list(self._motifs.values())
        )
        all_notes: list[NoteInfo] = []
        for entry in entries:
            notes = self.render(entry.name, offset=offset, **transform_kw)
            all_notes.extend(notes)
        all_notes.sort(key=lambda n: n.start)
        return all_notes
