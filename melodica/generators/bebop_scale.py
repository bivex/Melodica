"""Bebop scale generator with chromatic passing tones.

Bebop scales add a chromatic passing tone to standard 7-tone scales
so that chord tones consistently fall on strong beats (1, 3, 5, 7
in eighth-note runs). This is the foundation of bop improvisation
from Charlie Parker through John Coltrane.

Three main bebop scales:
  - Dominant bebop: Mixolydian + major 7th passing tone (8 notes)
  - Major bebop: Ionian + #5/b6 passing tone (8 notes)
  - Minor bebop: Dorian + major 3rd passing tone (8 notes)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale

# ---------------------------------------------------------------------------
# Scale definitions (intervals from root in semitones)
# ---------------------------------------------------------------------------

_BEBOP_DOMINANT = [0, 2, 4, 5, 7, 9, 10, 11]  # Mixolydian + maj7
_BEBOP_MAJOR = [0, 2, 4, 5, 7, 8, 9, 11]  # Ionian + #5
_BEBOP_MINOR = [0, 2, 3, 4, 5, 7, 9, 10]  # Dorian + maj3
_BEBOP_BLUES = [0, 2, 3, 4, 5, 7, 9, 10, 11]  # Minor bebop + #5

# Chord tones by quality (intervals from root)
_CHORD_TONES_DOMINANT = {0, 4, 7, 10}
_CHORD_TONES_MAJOR = {0, 4, 7, 11}
_CHORD_TONES_MINOR = {0, 3, 7, 10}


@dataclass
class BebopScaleGenerator(PhraseGenerator):
    """Generate bebop scale runs with chromatic passing tones.

    Parameters
    ----------
    scale_type : str
        "dominant" (default), "major", "minor", or "blues".
    direction : str
        "ascending", "descending", or "mixed".
    rhythm_value : float
        Note duration in beats (default 0.5 = eighth notes).
    accent_chord_tones : bool
        Boost velocity on chord tones.
    range_span : int
        How many octaves to cover in a run (1-3).
    """

    name: str = field(default="bebop_scale", init=False)
    scale_type: str = "dominant"
    direction: str = "mixed"
    rhythm_value: float = 0.5
    accent_chord_tones: bool = True
    range_span: int = 2
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        if self.scale_type not in ("dominant", "major", "minor", "blues"):
            raise ValueError(f"scale_type must be dominant/major/minor/blues, got {self.scale_type!r}")
        if self.direction not in ("ascending", "descending", "mixed"):
            raise ValueError(f"direction must be ascending/descending/mixed, got {self.direction!r}")

    def _scale_intervals(self) -> list[int]:
        return {
            "dominant": _BEBOP_DOMINANT,
            "major": _BEBOP_MAJOR,
            "minor": _BEBOP_MINOR,
            "blues": _BEBOP_BLUES,
        }[self.scale_type]

    def _chord_tone_set(self) -> set[int]:
        return {
            "dominant": _CHORD_TONES_DOMINANT,
            "major": _CHORD_TONES_MAJOR,
            "minor": _CHORD_TONES_MINOR,
            "blues": _CHORD_TONES_MINOR,
        }[self.scale_type]

    def _build_pitch_pool(self, key: Scale) -> list[int]:
        """Build full pitch pool across range_span octaves."""
        intervals = self._scale_intervals()
        root_pc = key.root
        low = self.params.key_range_low
        pool: list[int] = []
        for octave in range(-1, self.range_span + 1):
            base = ((low // 12) + octave) * 12
            for iv in intervals:
                p = base + root_pc + iv
                if self.params.key_range_low <= p <= self.params.key_range_high:
                    pool.append(p)
        pool.sort()
        return list(dict.fromkeys(pool))

    def _is_chord_tone(self, pitch: int, root_pc: int) -> bool:
        pc = pitch % 12
        relative = (pc - root_pc) % 12
        return relative in self._chord_tone_set()

    def _is_passing_tone(self, pitch: int, root_pc: int) -> bool:
        """Non-chord tone — the chromatic note added to the scale."""
        return not self._is_chord_tone(pitch, root_pc)

    def _pick_direction(self, pos: int) -> int:
        if self.direction == "ascending":
            return 1
        if self.direction == "descending":
            return -1
        # mixed: favor runs of 4-8 notes in one direction
        if pos % 8 < 5:
            return 1
        return -1

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        pool = self._build_pitch_pool(key)
        if len(pool) < 3:
            return []

        root_pc = key.root
        chord_root_pc = chords[0].root if chords else root_pc
        chord_tones = self._chord_tone_set()
        base_vel = self.base_velocity()
        notes: list[NoteInfo] = []

        # Start on a chord tone near the middle of the range
        mid_idx = len(pool) // 2
        current_idx = mid_idx
        # Walk to nearest chord tone
        for offset in range(len(pool)):
            for candidate in (mid_idx + offset, mid_idx - offset):
                if 0 <= candidate < len(pool):
                    rel = (pool[candidate] % 12 - root_pc) % 12
                    if rel in chord_tones:
                        current_idx = candidate
                        break
            else:
                continue
            break

        t = 0.0
        pos = 0
        while t < duration_beats:
            pitch = pool[current_idx]
            vel = base_vel

            # Accent chord tones
            if self.accent_chord_tones and self._is_chord_tone(pitch, root_pc):
                vel = min(127, vel + 12)
            elif self._is_passing_tone(pitch, root_pc):
                vel = max(1, vel - 8)

            # Humanize
            if self.params.intel.time_humanization > 0:
                t_offset = random.gauss(0, self.params.intel.time_humanization * 0.1)
            else:
                t_offset = 0.0

            vel = max(1, min(127, vel + random.randint(-4, 4)))

            notes.append(NoteInfo(
                pitch=pitch,
                start=round(max(0.0, t + t_offset), 4),
                duration=round(self.rhythm_value * 0.9, 4),
                velocity=vel,
                articulation="legato" if self._is_passing_tone(pitch, root_pc) else None,
            ))

            # Advance
            direction = self._pick_direction(pos)
            step = direction

            # Occasional direction change or leap
            if random.random() < 0.15:
                step = -step
            if random.random() < self.params.leap_probability:
                step *= 2

            current_idx = max(0, min(len(pool) - 1, current_idx + step))
            t += self.rhythm_value
            pos += 1

            # Bounce at range boundaries
            if current_idx <= 1:
                current_idx = 2
            elif current_idx >= len(pool) - 2:
                current_idx = len(pool) - 3

        return notes
