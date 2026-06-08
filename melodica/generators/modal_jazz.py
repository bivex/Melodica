"""Modal jazz generator.

Generates melodic/harmonic material in specific modes used in modal jazz:
  - Dorian (So What, Impressions, Milestones)
  - Mixolydian (cantus firmus, dominant pedal)
  - Lydian (Maiden Voyage, Bright Size Life)
  - Phrygian (flamenco jazz)
  - Aeolian (natural minor)
  - Combined modes (parallel key movement)

Modal jazz emphasizes scale color over chord changes — sustained harmonies
with modes as the primary improvisational framework. Reuses the pitch-pool
architecture from BebopScaleGenerator.

Reference recordings:
  - Miles Davis "Kind of Blue" (dorian, mixolydian)
  - John Coltrane "Impressions" (dorian)
  - Herbie Hancock "Maiden Voyage" (lydian, sus)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch, snap_to_scale

# ---------------------------------------------------------------------------
# Mode definitions (intervals from root in semitones)
# ---------------------------------------------------------------------------

_MODE_INTERVALS = {
    "dorian":     [0, 2, 3, 5, 7, 9, 10],
    "mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "lydian":     [0, 2, 4, 6, 7, 9, 11],
    "phrygian":   [0, 1, 3, 5, 7, 8, 10],
    "aeolian":    [0, 2, 3, 5, 7, 8, 10],
    "ionian":     [0, 2, 4, 5, 7, 9, 11],
}

# Characteristic notes per mode (the notes that define the mode's color)
_CHARACTERISTIC_NOTES = {
    "dorian":     {6, 9},    # natural 6, natural 9
    "mixolydian": {10, 4},   # b7, major 3rd
    "lydian":     {6, 11},   # #4/#11, major 7
    "phrygian":   {1, 8},    # b2, b6
    "aeolian":    {3, 8},    # b3, b6
    "ionian":     {4, 11},   # major 3, major 7
}

# "So What" chord voicing: dorian mode in 4ths
_SO_WHAT_VOICING_DORIAN = [0, 5, 10, 15, 17]  # Dm9 shape


@dataclass
class ModalJazzGenerator(PhraseGenerator):
    """Generate modal jazz lines and voicings.

    Unlike bebop (chord-change driven), modal jazz stays on one chord/mode
    for extended periods (8-32 bars) and emphasizes melodic development
    within the mode's color.

    Parameters
    ----------
    mode : str
        "dorian", "mixolydian", "lydian", "phrygian", "aeolian", "ionian",
        or "auto" (picks from key signature).
    line_style : str
        "scalar" — stepwise motion through the mode.
        "intervallic" — wider intervals, post-bop style.
        "pentatonic_subset" — 5-note subset of the mode.
        "triad_pairs" — alternating triads within the mode.
    rhythm_density : float
        Notes per beat (0.25 = whole, 0.5 = half, 1 = quarter, 2 = eighth).
    accent_characteristic : bool
        Emphasize the characteristic notes of the mode.
    pedal_tone : bool
        Hold a pedal tone (root or 5th) underneath moving lines.
    register_shift : float
        Probability of shifting register up/down an octave (0-1).
    phrase_length : int
        Average phrase length in beats before a rest.
    """

    name: str = field(default="modal_jazz", init=False)
    mode: str = "dorian"
    line_style: str = "scalar"
    rhythm_density: float = 1.0
    accent_characteristic: bool = True
    pedal_tone: bool = False
    register_shift: float = 0.1
    phrase_length: int = 8
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid_modes = set(_MODE_INTERVALS.keys()) | {"auto"}
        if self.mode not in valid_modes:
            raise ValueError(f"mode must be one of {sorted(valid_modes)}, got {self.mode!r}")
        valid_styles = {"scalar", "intervallic", "pentatonic_subset", "triad_pairs"}
        if self.line_style not in valid_styles:
            raise ValueError(f"line_style must be one of {valid_styles}, got {self.line_style!r}")

    def _mode_intervals(self, key: Scale) -> list[int]:
        if self.mode != "auto":
            return _MODE_INTERVALS[self.mode]
        # Pick from key
        mode_str = key.mode.value if hasattr(key.mode, "value") else str(key.mode)
        if "minor" in mode_str or "dorian" in mode_str:
            return _MODE_INTERVALS["dorian"]
        if "lydian" in mode_str:
            return _MODE_INTERVALS["lydian"]
        if "mixolydian" in mode_str:
            return _MODE_INTERVALS["mixolydian"]
        return _MODE_INTERVALS["ionian"]

    def _characteristic_notes(self) -> set[int]:
        mode = self.mode if self.mode != "auto" else "dorian"
        return _CHARACTERISTIC_NOTES.get(mode, set())

    def _build_pitch_pool(self, key: Scale, intervals: list[int]) -> list[int]:
        root_pc = key.root
        pool: list[int] = []
        for octave in range(-1, 4):
            base = ((self.params.key_range_low // 12) + octave) * 12
            for iv in intervals:
                p = base + root_pc + iv
                if self.params.key_range_low <= p <= self.params.key_range_high:
                    pool.append(p)
        pool.sort()
        return list(dict.fromkeys(pool))

    def _pentatonic_subset(self, intervals: list[int]) -> list[int]:
        """Extract a 5-note pentatonic subset from the mode."""
        # Common pentatonic subsets from 7-note modes
        # Take degrees 1, 2, 3, 5, 6 (skip 4th and 7th)
        if len(intervals) >= 7:
            return [intervals[0], intervals[1], intervals[2], intervals[4], intervals[5]]
        return intervals[:5]

    def _triad_pair_degrees(self, intervals: list[int]) -> tuple[list[int], list[int]]:
        """Return two triad subsets from the mode (triad pairs technique)."""
        if len(intervals) >= 7:
            triad1 = [intervals[0], intervals[2], intervals[4]]  # I
            triad2 = [intervals[1], intervals[3], intervals[5]]  # II
            return triad1, triad2
        mid = len(intervals) // 2
        return intervals[:mid], intervals[mid:]

    def _pick_next_pitch(self, pool: list[int], current_idx: int, root_pc: int) -> int:
        if self.line_style == "scalar":
            # Stepwise motion (1 scale step)
            direction = random.choice([-1, 1])
            step = direction * random.choice([1, 1, 1, 2])  # mostly steps
            return max(0, min(len(pool) - 1, current_idx + step))

        if self.line_style == "intervallic":
            # Wider intervals (3rds, 4ths, 5ths)
            leap = random.choice([2, 2, 3, 3, 4, 5])
            direction = random.choice([-1, 1])
            return max(0, min(len(pool) - 1, current_idx + direction * leap))

        if self.line_style == "pentatonic_subset":
            # Move within pentatonic — always sounds good
            direction = random.choice([-1, 1])
            step = direction * random.choice([1, 1, 2])
            return max(0, min(len(pool) - 1, current_idx + step))

        # triad_pairs: alternate between two triads
        direction = random.choice([-1, 1])
        step = direction * random.choice([2, 2, 3])
        return max(0, min(len(pool) - 1, current_idx + step))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        intervals = self._mode_intervals(key)
        char_notes = self._characteristic_notes()
        root_pc = key.root

        # Adjust intervals for pentatonic/triad subsets
        effective_intervals = intervals
        if self.line_style == "pentatonic_subset":
            effective_intervals = self._pentatonic_subset(intervals)
        elif self.line_style == "triad_pairs":
            # Use full scale but pick from triad positions
            effective_intervals = intervals

        pool = self._build_pitch_pool(key, effective_intervals)
        if len(pool) < 3:
            return []

        base_vel = self.base_velocity()
        notes: list[NoteInfo] = []

        # Start near middle of pool
        current_idx = len(pool) // 2
        t = 0.0
        beat_dur = 1.0 / self.rhythm_density if self.rhythm_density > 0 else 1.0
        phrase_count = 0

        while t < duration_beats:
            # Phrase rests
            if phrase_count >= self.phrase_length:
                if random.random() < 0.4:
                    t += beat_dur
                    phrase_count = 0
                    continue
                phrase_count = 0

            pitch = pool[current_idx]
            vel = base_vel

            # Accent characteristic notes
            relative = (pitch % 12 - root_pc) % 12
            if self.accent_characteristic and relative in char_notes:
                vel = min(127, vel + 12)

            # Register shift
            if random.random() < self.register_shift:
                shift = random.choice([7, -7, 12, -12])
                new_idx = current_idx + (shift // 2)
                if 0 <= new_idx < len(pool):
                    current_idx = new_idx
                    pitch = pool[current_idx]

            # Humanize
            t_offset = random.gauss(0, self.params.intel.time_humanization * 0.1)
            v_offset = random.randint(-4, 4)

            notes.append(NoteInfo(
                pitch=pitch,
                start=round(max(0.0, t + t_offset), 4),
                duration=round(beat_dur * 0.85, 4),
                velocity=max(1, min(127, vel + v_offset)),
            ))

            # Pedal tone: add root or 5th below
            if self.pedal_tone and random.random() < 0.3:
                pedal_pc = root_pc if random.random() < 0.5 else (root_pc + 7) % 12
                pedal_p = nearest_pitch(pedal_pc, self.params.key_range_low)
                if self.params.key_range_low <= pedal_p <= self.params.key_range_high:
                    notes.append(NoteInfo(
                        pitch=pedal_p,
                        start=round(max(0.0, t + t_offset), 4),
                        duration=round(beat_dur * 0.85, 4),
                        velocity=max(1, min(127, base_vel - 15)),
                    ))

            # Advance
            current_idx = self._pick_next_pitch(pool, current_idx, root_pc)
            # Clamp
            if current_idx <= 1:
                current_idx = 2
            elif current_idx >= len(pool) - 2:
                current_idx = len(pool) - 3

            t += beat_dur
            phrase_count += 1

        return notes
