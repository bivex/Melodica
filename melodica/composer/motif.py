"""Motif — thematic development through motivic transformation.

Define a motif once, then develop it: inversion, retrograde, augmentation,
diminution, sequence, fragmentation, diatonic operations, dynamics,
ornamentation, canon, and arbitrary chains via develop().
Every transform returns a NEW Motif — originals are never mutated.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import Scale


def _copy_note(n: NoteInfo, **overrides) -> NoteInfo:
    """Shallow-copy a NoteInfo with optional field overrides."""
    kw = dict(
        pitch=n.pitch, start=n.start, duration=n.duration,
        velocity=n.velocity, absolute=n.absolute,
        articulation=n.articulation, expression=n.expression,
    )
    kw.update(overrides)
    return NoteInfo(**kw)


def _clamp_pitch(p: int) -> int:
    return max(0, min(127, p))


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
        rel = [_copy_note(n, start=n.start - min_start) for n in notes]
        return cls(_notes=rel, _origin=origin + min_start)

    def render(self, offset: float = 0.0) -> list[NoteInfo]:
        """Return notes at absolute beat positions (origin + offset + relative start)."""
        return [
            _copy_note(n, start=n.start + self._origin + offset)
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
            _notes=[_copy_note(n, pitch=_clamp_pitch(n.pitch + semitones))
                    for n in self._notes],
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
            _notes=[_copy_note(n, pitch=_clamp_pitch(int(round(2 * center - n.pitch))))
                    for n in self._notes],
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
        t = reversed_notes[0].start
        new_notes.append(_copy_note(reversed_notes[0], start=t))
        rev_spans = list(reversed(spans))
        rev_gaps = list(reversed(gaps))
        for i in range(1, len(reversed_notes)):
            gap = rev_gaps[i - 1] if i - 1 < len(rev_gaps) else 0.0
            t += rev_spans[i - 1] + gap
            new_notes.append(_copy_note(reversed_notes[i], start=t))
        return Motif(_notes=new_notes, _origin=self._origin)

    def augment(self, factor: float = 2.0) -> Motif:
        """Stretch durations and time gaps by *factor*."""
        if factor <= 0:
            raise ValueError("factor must be positive")
        return Motif(
            _notes=[_copy_note(n, start=n.start * factor, duration=n.duration * factor)
                    for n in self._notes],
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
            shifted = [_copy_note(n, pitch=_clamp_pitch(n.pitch + interval),
                                  start=n.start + gap)
                       for n in all_notes]
            all_notes.extend(shifted)
            gap += self.duration if spacing is None else spacing
        return Motif(_notes=all_notes, _origin=self._origin)

    def fragment(self, start_beat: float = 0.0, end_beat: float | None = None) -> Motif:
        """Extract notes within [start_beat, end_beat) relative to motif start."""
        end = end_beat if end_beat is not None else float("inf")
        subset = [n for n in self._notes if start_beat <= n.start < end]
        offset = min((n.start for n in subset), default=0.0)
        return Motif(
            _notes=[_copy_note(n, start=n.start - offset) for n in subset],
            _origin=self._origin,
        )

    # ------------------------------------------------------------------
    # New transforms
    # ------------------------------------------------------------------

    def transpose_diatonic(self, degrees: int, scale: Scale) -> Motif:
        """Transpose by N scale degrees, snapping each pitch to the scale."""
        degs = scale.degrees()
        n_degs = len(degrees) if isinstance(degrees, list) else len(degs)
        n_degs = len(degs)
        new_notes = []
        for n in self._notes:
            pc = n.pitch % 12
            octave = n.pitch // 12
            # Find nearest scale degree index
            idx = min(range(n_degs), key=lambda i: abs(degs[i] - pc))
            new_idx = idx + degrees
            new_octave = octave + new_idx // n_degs
            new_idx = new_idx % n_degs
            new_pitch = _clamp_pitch(int(round(new_octave * 12 + degs[new_idx])))
            new_notes.append(_copy_note(n, pitch=new_pitch))
        return Motif(_notes=new_notes, _origin=self._origin)

    def invert_diatonic(self, scale: Scale, axis_degree: int = 0) -> Motif:
        """Mirror intervals within a scale (stays diatonic, unlike chromatic invert)."""
        degs = scale.degrees()
        n_degs = len(degs)
        new_notes = []
        for n in self._notes:
            pc = n.pitch % 12
            octave = n.pitch // 12
            idx = min(range(n_degs), key=lambda i: abs(degs[i] - pc))
            dist = idx - axis_degree
            new_idx = axis_degree - dist
            new_octave = octave + (new_idx // n_degs)
            new_idx = new_idx % n_degs
            new_pitch = _clamp_pitch(int(round(new_octave * 12 + degs[new_idx])))
            new_notes.append(_copy_note(n, pitch=new_pitch))
        return Motif(_notes=new_notes, _origin=self._origin)

    def displace(self, beats: float) -> Motif:
        """Shift all note start times by *beats* (rhythmic displacement)."""
        return Motif(
            _notes=[_copy_note(n, start=n.start + beats) for n in self._notes],
            _origin=self._origin,
        )

    def truncate_head(self, n: int) -> Motif:
        """Remove the first *n* notes (by onset order)."""
        sorted_notes = sorted(self._notes, key=lambda x: x.start)
        return Motif(_notes=list(sorted_notes[n:]), _origin=self._origin)

    def truncate_tail(self, n: int) -> Motif:
        """Remove the last *n* notes (by onset order)."""
        sorted_notes = sorted(self._notes, key=lambda x: x.start)
        if n <= 0:
            return Motif(_notes=list(sorted_notes), _origin=self._origin)
        return Motif(_notes=list(sorted_notes[:-n]), _origin=self._origin)

    def expand(self, factor: float) -> Motif:
        """Stretch gaps between note onsets without stretching durations."""
        if factor <= 0:
            raise ValueError("factor must be positive")
        if not self._notes:
            return Motif(_notes=[], _origin=self._origin)
        min_start = min(n.start for n in self._notes)
        return Motif(
            _notes=[_copy_note(n, start=min_start + (n.start - min_start) * factor)
                    for n in self._notes],
            _origin=self._origin,
        )

    def apply_dynamics(self, envelope) -> Motif:
        """Apply a VelocityEnvelope to motif notes. Returns new Motif."""
        from melodica.composer.velocity_envelope import VelocityEnvelope
        new_notes = envelope.apply(self._notes)
        return Motif(_notes=new_notes, _origin=self._origin)

    def ornament(self, style: str, scale: Scale) -> Motif:
        """Add ornamentation: grace, passing, neighbor, cambiata, or spiceup."""
        from melodica.composer.transformers import (
            OneToThree, TwoToThree, TwoToFour, spiceup,
        )
        if style == "spiceup":
            new_notes = spiceup(self._notes, scale, depth=1)
        elif style == "neighbor":
            tr = OneToThree()
            new_notes = []
            for n in self._notes:
                new_notes.extend(tr.transform(scale, n))
        elif style == "passing":
            tr = TwoToThree()
            sorted_notes = sorted(self._notes, key=lambda x: x.start)
            new_notes = []
            for i, n in enumerate(sorted_notes):
                nxt = sorted_notes[i + 1] if i + 1 < len(sorted_notes) else None
                new_notes.extend(tr.transform(scale, n, nxt))
        elif style == "cambiata":
            tr = TwoToFour()
            sorted_notes = sorted(self._notes, key=lambda x: x.start)
            new_notes = []
            for i, n in enumerate(sorted_notes):
                nxt = sorted_notes[i + 1] if i + 1 < len(sorted_notes) else None
                new_notes.extend(tr.transform(scale, n, nxt))
        elif style == "grace":
            new_notes = []
            for n in self._notes:
                # Upper neighbor grace note (short, quiet)
                grace_dur = n.duration * 0.2
                grace_pitch = _clamp_pitch(n.pitch + 1)
                new_notes.append(NoteInfo(
                    pitch=grace_pitch, start=n.start, duration=grace_dur,
                    velocity=max(1, n.velocity - 15),
                ))
                new_notes.append(_copy_note(n, start=n.start + grace_dur,
                                            duration=n.duration - grace_dur))
        else:
            raise ValueError(f"Unknown ornament style: {style!r}")
        return Motif(_notes=new_notes, _origin=self._origin)

    def canon(self, voices: int, delay: float, intervals: list[int]) -> Motif:
        """Generate canon entries — successive voices at intervals with delay."""
        from melodica.composer.transformers import serialize_canon
        voice_notes = [self._notes] * voices
        canon_notes = serialize_canon(voice_notes, delay, intervals)
        return Motif(_notes=canon_notes, _origin=self._origin)

    def with_pedal(self, pitch: int) -> Motif:
        """Add a sustained pedal note spanning the full motif duration."""
        if not self._notes:
            return Motif(_notes=[], _origin=self._origin)
        min_start = min(n.start for n in self._notes)
        max_end = max(n.start + n.duration for n in self._notes)
        pedal = NoteInfo(
            pitch=_clamp_pitch(pitch),
            start=min_start,
            duration=round(max_end - min_start, 6),
            velocity=60,
        )
        return Motif(_notes=self._notes + [pedal], _origin=self._origin)

    def humanize(self, timing: float = 0.01, velocity: float = 3.0) -> Motif:
        """Add slight random timing and velocity variation."""
        new_notes = []
        for n in self._notes:
            new_start = max(0.0, n.start + random.gauss(0, timing))
            new_vel = max(1, min(127, int(n.velocity + random.gauss(0, velocity))))
            new_notes.append(_copy_note(n, start=round(new_start, 6), velocity=new_vel))
        return Motif(_notes=new_notes, _origin=self._origin)

    # ------------------------------------------------------------------
    # Chain
    # ------------------------------------------------------------------

    def develop(self, **kw) -> Motif:
        """Chain transforms in musical order.

        Accepted kwargs (original): fragment_start, fragment_end,
        retrograde (bool), invert (bool), invert_center, transpose (int),
        augment_factor, diminish_factor, sequence_intervals, sequence_spacing.

        New kwargs: truncate_head_n, truncate_tail_n,
        invert_diatonic (bool), invert_diatonic_scale, invert_diatonic_axis,
        transpose_diatonic_degrees, transpose_diatonic_scale,
        displace_beats, expand_factor,
        ornament_style, ornament_scale,
        dynamics_envelope (VelocityEnvelope),
        humanize_timing, humanize_velocity,
        canon_voices, canon_delay, canon_intervals,
        pedal_pitch.
        """
        m = self

        # 1. fragment
        fs = kw.get("fragment_start")
        fe = kw.get("fragment_end")
        if fs is not None:
            m = m.fragment(start_beat=fs, end_beat=fe)

        # 2. truncate
        thn = kw.get("truncate_head_n")
        if thn:
            m = m.truncate_head(thn)
        ttn = kw.get("truncate_tail_n")
        if ttn:
            m = m.truncate_tail(ttn)

        # 3. retrograde
        if kw.get("retrograde", False):
            m = m.retrograde()

        # 4. invert (chromatic)
        if kw.get("invert", False):
            m = m.invert(center=kw.get("invert_center"))

        # 5. invert_diatonic
        if kw.get("invert_diatonic", False):
            sc = kw.get("invert_diatonic_scale")
            if sc is not None:
                m = m.invert_diatonic(sc, axis_degree=kw.get("invert_diatonic_axis", 0))

        # 6. augment / diminish
        af = kw.get("augment_factor")
        df = kw.get("diminish_factor")
        if af is not None:
            m = m.augment(af)
        elif df is not None:
            m = m.diminish(df)

        # 7. expand
        ef = kw.get("expand_factor")
        if ef is not None:
            m = m.expand(ef)

        # 8. transpose (chromatic)
        t = kw.get("transpose")
        if t is not None:
            m = m.transpose(t)

        # 9. transpose_diatonic
        td_deg = kw.get("transpose_diatonic_degrees")
        td_sc = kw.get("transpose_diatonic_scale")
        if td_deg is not None and td_sc is not None:
            m = m.transpose_diatonic(td_deg, td_sc)

        # 10. displace
        db = kw.get("displace_beats")
        if db is not None:
            m = m.displace(db)

        # 11. ornament
        os_ = kw.get("ornament_style")
        osc = kw.get("ornament_scale")
        if os_ is not None and osc is not None:
            m = m.ornament(os_, osc)

        # 12. apply_dynamics
        dyn = kw.get("dynamics_envelope")
        if dyn is not None:
            m = m.apply_dynamics(dyn)

        # 13. humanize
        ht = kw.get("humanize_timing")
        if ht is not None:
            m = m.humanize(timing=ht, velocity=kw.get("humanize_velocity", 3.0))

        # 14. canon
        cv = kw.get("canon_voices")
        if cv is not None:
            m = m.canon(cv, kw.get("canon_delay", 4.0), kw.get("canon_intervals", [0]))

        # 15. with_pedal
        pp = kw.get("pedal_pitch")
        if pp is not None:
            m = m.with_pedal(pp)

        # 16. sequence
        si = kw.get("sequence_intervals")
        if si:
            m = m.sequence(si, spacing=kw.get("sequence_spacing"))

        return m
