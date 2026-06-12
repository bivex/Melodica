"""generators/tone_row.py — 12-tone row generator (serialism).

Implements the four classical row transformations:
  P  — Prime (original row)
  I  — Inversion (intervals mirrored)
  R  — Retrograde (reversed)
  RI — Retrograde Inversion

Usage
-----
    from melodica.generators.tone_row import ToneRow, ToneRowGenerator

    row = ToneRow.from_pitches([0,11,3,4,8,7,9,6,1,5,2,10])
    notes = ToneRowGenerator(row=row, pitch_center=60, velocity=72).generate(
        start_beat=0.0, note_duration=0.5, form="P", transposition=0
    )

    # Or use a random row:
    row = ToneRow.random()
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.types_pkg._notes import NoteInfo


# ---------------------------------------------------------------------------
# ToneRow — the row and its 4 transformations
# ---------------------------------------------------------------------------

@dataclass
class ToneRow:
    """A 12-tone row with P/I/R/RI transformations.

    The row is stored as a list of 12 pitch classes (0–11).
    """

    _pcs: list[int] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def from_pitches(cls, pitch_classes: list[int]) -> ToneRow:
        """Create from a list of 12 pitch classes (0–11).

        Raises ValueError if the list is not a valid 12-tone row.
        """
        pcs = [p % 12 for p in pitch_classes]
        if len(pcs) != 12 or len(set(pcs)) != 12:
            raise ValueError(
                f"A 12-tone row must contain all 12 pitch classes exactly once. Got: {pcs}"
            )
        return cls(_pcs=pcs)

    @classmethod
    def random(cls, seed: int | None = None) -> ToneRow:
        """Generate a random 12-tone row."""
        pcs = list(range(12))
        rng = random.Random(seed)
        rng.shuffle(pcs)
        return cls(_pcs=pcs)

    @classmethod
    def from_interval_pattern(cls, intervals: list[int]) -> ToneRow:
        """Build a row from a list of 11 intervals (in semitones).

        The first pitch class is always 0; each subsequent PC is determined
        by the interval from the previous one.
        """
        if len(intervals) != 11:
            raise ValueError("Need exactly 11 intervals for a 12-tone row.")
        pcs = [0]
        for iv in intervals:
            pcs.append((pcs[-1] + iv) % 12)
        if len(set(pcs)) != 12:
            raise ValueError(f"Interval pattern produces duplicate pitch classes: {pcs}")
        return cls(_pcs=pcs)

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def pcs(self) -> list[int]:
        return list(self._pcs)

    # ------------------------------------------------------------------
    # Transformations
    # ------------------------------------------------------------------

    def prime(self, transposition: int = 0) -> list[int]:
        """P(n) — original row transposed by n semitones."""
        return [(p + transposition) % 12 for p in self._pcs]

    def inversion(self, transposition: int = 0) -> list[int]:
        """I(n) — intervals mirrored, transposed by n."""
        first = self._pcs[0]
        inverted = [first]
        for i in range(1, 12):
            interval = (self._pcs[i] - self._pcs[i - 1]) % 12
            inverted.append((inverted[-1] - interval) % 12)
        return [(p + transposition) % 12 for p in inverted]

    def retrograde(self, transposition: int = 0) -> list[int]:
        """R(n) — reversed row, transposed by n."""
        return [(p + transposition) % 12 for p in reversed(self._pcs)]

    def retrograde_inversion(self, transposition: int = 0) -> list[int]:
        """RI(n) — retrograde of inversion, transposed by n."""
        inv = self.inversion(0)
        return [(p + transposition) % 12 for p in reversed(inv)]

    def transform(self, form: str, transposition: int = 0) -> list[int]:
        """Apply transformation by name: 'P', 'I', 'R', 'RI'."""
        form = form.upper()
        if form == "P":
            return self.prime(transposition)
        elif form == "I":
            return self.inversion(transposition)
        elif form == "R":
            return self.retrograde(transposition)
        elif form == "RI":
            return self.retrograde_inversion(transposition)
        else:
            raise ValueError(f"Unknown row form: {form!r}. Use P, I, R, or RI.")

    # ------------------------------------------------------------------
    # Row matrix
    # ------------------------------------------------------------------

    def matrix(self) -> list[list[int]]:
        """Return the full 12×12 row matrix (P0..P11)."""
        return [self.prime(t) for t in range(12)]

    def __repr__(self) -> str:
        return f"ToneRow({self._pcs})"


# ---------------------------------------------------------------------------
# ToneRowGenerator — converts a row transformation to NoteInfo
# ---------------------------------------------------------------------------

@dataclass
class ToneRowGenerator:
    """Converts a ToneRow transformation into a list of NoteInfo.

    Parameters
    ----------
    row : ToneRow
        The 12-tone row to use.
    pitch_center : int
        MIDI pitch for the first PC of the row. Subsequent notes are voiced
        nearest to the previous note (voice-leading friendly).
    velocity : int
        Base velocity for all notes.
    velocity_accents : list[float] | None
        Per-position velocity multipliers (length 12). None = flat dynamics.
        Example: [1.2, 0.9, 1.0, 0.9, 1.1, 0.9, 1.0, 0.9, 1.2, 0.9, 1.0, 0.9]
    """

    row: ToneRow
    pitch_center: int = 60
    velocity: int = 70
    velocity_accents: list[float] | None = None

    def generate(
        self,
        start_beat: float = 0.0,
        note_duration: float = 0.5,
        form: str = "P",
        transposition: int = 0,
        *,
        repeats: int = 1,
        gap: float = 0.0,
    ) -> list[NoteInfo]:
        """Generate notes for one or more row statements.

        Parameters
        ----------
        start_beat : float
            Beat position of the first note.
        note_duration : float
            Duration of each note in beats.
        form : str
            Row form: 'P', 'I', 'R', 'RI'.
        transposition : int
            Transposition in semitones (0–11).
        repeats : int
            Number of times to state the row (with optional gap).
        gap : float
            Silence between row repetitions in beats.

        Returns
        -------
        list[NoteInfo]
        """
        pcs = self.row.transform(form, transposition)
        accents = self.velocity_accents or [1.0] * 12
        notes: list[NoteInfo] = []

        row_dur = 12 * note_duration + gap
        prev_pitch = self.pitch_center

        for rep in range(repeats):
            base = start_beat + rep * row_dur
            for i, pc in enumerate(pcs):
                # Voice nearest to previous pitch
                oct_ = prev_pitch // 12
                candidate = pc + oct_ * 12
                # Check neighbouring octaves for closest
                best = candidate
                for oct_off in (-1, 0, 1):
                    cand = pc + (oct_ + oct_off) * 12
                    if abs(cand - prev_pitch) < abs(best - prev_pitch):
                        best = cand
                best = max(0, min(127, best))
                prev_pitch = best

                vel_mult = accents[i % len(accents)]
                vel = max(1, min(127, int(self.velocity * vel_mult)))

                notes.append(NoteInfo(
                    pitch=best,
                    start=round(base + i * note_duration, 6),
                    duration=round(note_duration * 0.9, 6),
                    velocity=vel,
                ))

        return notes

    def generate_hexachords(
        self,
        start_beat: float = 0.0,
        note_duration: float = 0.5,
        form: str = "P",
        transposition: int = 0,
    ) -> tuple[list[NoteInfo], list[NoteInfo]]:
        """Return the two hexachords (first/second half) separately.

        Useful for contrapuntal textures where hexachords are distributed
        between two voices.
        """
        all_notes = self.generate(start_beat, note_duration, form, transposition)
        return all_notes[:6], all_notes[6:]
