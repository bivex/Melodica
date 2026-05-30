"""Motif — thematic development through motivic transformation.

Define a motif once, then develop it: inversion, retrograde, augmentation,
diminution, sequence, fragmentation, and arbitrary chains via develop().
Every transform returns a NEW Motif — originals are never mutated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.types_pkg._notes import NoteInfo


@dataclass(slots=True)
class Motif:
    """Immutable container for a musical motif with transformation methods."""

    _notes: list[NoteInfo] = field(default_factory=list)
    _origin: float = 0.0

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_notes(cls, notes: list[NoteInfo], origin: float = 0.0) -> Motif:
        """Create a motif from a list of notes.

        Notes are stored with start times relative to the earliest note.
        *origin* is the default render offset (absolute beat where motif begins).
        """
        if not notes:
            return cls(_notes=[], _origin=origin)
        min_start = min(n.start for n in notes)
        rel = [
            NoteInfo(
                pitch=n.pitch,
                start=n.start - min_start,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute,
                articulation=n.articulation,
                expression=n.expression,
            )
            for n in notes
        ]
        return cls(_notes=rel, _origin=origin + min_start)

    def render(self, offset: float = 0.0) -> list[NoteInfo]:
        """Return notes at absolute beat positions (origin + offset + relative start)."""
        return [
            NoteInfo(
                pitch=n.pitch,
                start=n.start + self._origin + offset,
                duration=n.duration,
                velocity=n.velocity,
                absolute=n.absolute,
                articulation=n.articulation,
                expression=n.expression,
            )
            for n in self._notes
        ]

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def duration(self) -> float:
        """Span from earliest start to latest end."""
        if not self._notes:
            return 0.0
        return max(n.start + n.duration for n in self._notes) - min(
            n.start for n in self._notes
        )

    @property
    def notes(self) -> list[NoteInfo]:
        """Read-only view of internal notes (relative to origin)."""
        return list(self._notes)

    # ------------------------------------------------------------------
    # Transforms — each returns a NEW Motif
    # ------------------------------------------------------------------

    def transpose(self, semitones: int) -> Motif:
        return Motif(
            _notes=[
                NoteInfo(
                    pitch=n.pitch + semitones,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in self._notes
            ],
            _origin=self._origin,
        )

    def invert(self, center: float | None = None) -> Motif:
        """Mirror pitches around *center* (default: average of min/max pitch)."""
        if not self._notes:
            return Motif(_notes=[], _origin=self._origin)
        if center is None:
            pitches = [n.pitch for n in self._notes]
            center = (min(pitches) + max(pitches)) / 2.0
        return Motif(
            _notes=[
                NoteInfo(
                    pitch=int(round(2 * center - n.pitch)),
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in self._notes
            ],
            _origin=self._origin,
        )

    def retrograde(self) -> Motif:
        """Reverse note order, re-timed so starts remain contiguous."""
        if not self._notes:
            return Motif(_notes=[], _origin=self._origin)
        sorted_notes = sorted(self._notes, key=lambda n: n.start)
        spans = [n.duration for n in sorted_notes]
        gaps = []
        for i in range(1, len(sorted_notes)):
            prev_end = sorted_notes[i - 1].start + sorted_notes[i - 1].duration
            gaps.append(sorted_notes[i].start - prev_end)

        reversed_notes = list(reversed(sorted_notes))
        new_notes: list[NoteInfo] = []
        t = reversed_notes[0].start  # keep original first onset
        new_notes.append(
            NoteInfo(
                pitch=reversed_notes[0].pitch,
                start=t,
                duration=reversed_notes[0].duration,
                velocity=reversed_notes[0].velocity,
                absolute=reversed_notes[0].absolute,
                articulation=reversed_notes[0].articulation,
                expression=reversed_notes[0].expression,
            )
        )
        rev_spans = list(reversed(spans))
        rev_gaps = list(reversed(gaps))
        for i in range(1, len(reversed_notes)):
            gap = rev_gaps[i - 1] if i - 1 < len(rev_gaps) else 0.0
            t += rev_spans[i - 1] + gap
            new_notes.append(
                NoteInfo(
                    pitch=reversed_notes[i].pitch,
                    start=t,
                    duration=reversed_notes[i].duration,
                    velocity=reversed_notes[i].velocity,
                    absolute=reversed_notes[i].absolute,
                    articulation=reversed_notes[i].articulation,
                    expression=reversed_notes[i].expression,
                )
            )
        return Motif(_notes=new_notes, _origin=self._origin)

    def augment(self, factor: float = 2.0) -> Motif:
        """Stretch durations and time gaps by *factor*."""
        if factor <= 0:
            raise ValueError("factor must be positive")
        return Motif(
            _notes=[
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start * factor,
                    duration=n.duration * factor,
                    velocity=n.velocity,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in self._notes
            ],
            _origin=self._origin,
        )

    def diminish(self, factor: float = 2.0) -> Motif:
        """Compress durations and time gaps by *factor*."""
        if factor <= 0:
            raise ValueError("factor must be positive")
        return self.augment(1.0 / factor)

    def sequence(self, intervals: list[int], spacing: float | None = None) -> Motif:
        """Repeat motif at pitch *intervals*, spaced by motif duration or *spacing*."""
        if not intervals:
            return Motif(_notes=list(self._notes), _origin=self._origin)
        gap = spacing if spacing is not None else self.duration
        all_notes: list[NoteInfo] = list(self._notes)
        for interval in intervals:
            shifted = [
                NoteInfo(
                    pitch=n.pitch + interval,
                    start=n.start + gap,
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in all_notes
            ]
            all_notes.extend(shifted)
            gap += self.duration if spacing is None else spacing
        return Motif(_notes=all_notes, _origin=self._origin)

    def fragment(self, start_beat: float = 0.0, end_beat: float | None = None) -> Motif:
        """Extract notes within [start_beat, end_beat) relative to motif start."""
        end = end_beat if end_beat is not None else float("inf")
        subset = [n for n in self._notes if start_beat <= n.start < end]
        offset = min((n.start for n in subset), default=0.0)
        return Motif(
            _notes=[
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start - offset,
                    duration=n.duration,
                    velocity=n.velocity,
                    absolute=n.absolute,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                for n in subset
            ],
            _origin=self._origin,
        )

    # ------------------------------------------------------------------
    # Chain
    # ------------------------------------------------------------------

    def develop(self, **kw) -> Motif:
        """Chain transforms in musical order: fragment → retrograde → invert
        → augment/diminish → transpose → sequence.

        Accepted kwargs: fragment_start, fragment_end, retrograde (bool),
        invert (bool), invert_center, transpose (int), augment_factor,
        diminish_factor, sequence_intervals, sequence_spacing.
        """
        m = self

        # 1. fragment
        fs = kw.get("fragment_start")
        fe = kw.get("fragment_end")
        if fs is not None:
            m = m.fragment(start_beat=fs, end_beat=fe)

        # 2. retrograde
        if kw.get("retrograde", False):
            m = m.retrograde()

        # 3. invert
        if kw.get("invert", False):
            m = m.invert(center=kw.get("invert_center"))

        # 4. augment / diminish
        af = kw.get("augment_factor")
        df = kw.get("diminish_factor")
        if af is not None:
            m = m.augment(af)
        elif df is not None:
            m = m.diminish(df)

        # 5. transpose
        t = kw.get("transpose")
        if t is not None:
            m = m.transpose(t)

        # 6. sequence
        si = kw.get("sequence_intervals")
        if si:
            m = m.sequence(si, spacing=kw.get("sequence_spacing"))

        return m
