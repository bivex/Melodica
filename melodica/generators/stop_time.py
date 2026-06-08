"""Stop-time comping generator.

Generates the classic jazz stop-time pattern where the ensemble plays
staccato accents on specific beats with silence in between — creating
dramatic tension and rhythmic propulsion. Used in:

  - Big band shout choruses
  - Jazz blues heads (e.g., Billie's Bounce, Now's the Time)
  - Bebop heads with built-in stops
  - Call-and-response between soloist and rhythm section

Players: Count Basie, Duke Ellington, Art Blakey, Miles Davis.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class StopTimeGenerator(PhraseGenerator):
    """Generate stop-time comping patterns.

    Parameters
    ----------
    pattern : str
        "big_four" — accent on beat 1, rest on 2-3-4.
        "half_note" — accent on 1 and 3.
        "syncopated" — accent on 1 and the & of 2.
        "shuffle" — accent on 1, & of 2, 3, & of 4.
        "free" — random accent placement.
    accent_note : str
        "root" — accent the chord root.
        "chord_tone" — accent a random chord tone.
        "shell" — accent root + 3rd or root + 7th.
    accent_duration : float
        Duration of each accent in beats (staccato = short).
    rest_velocity : int
        Velocity for ghost notes during rests (0 = silence).
    fill_last_beat : bool
        Play a pickup note on the last beat targeting the next chord.
    """

    name: str = field(default="stop_time", init=False)
    pattern: str = "big_four"
    accent_note: str = "chord_tone"
    accent_duration: float = 0.3
    rest_velocity: int = 0
    fill_last_beat: bool = True
    params: GeneratorParams = field(default_factory=GeneratorParams)

    _PATTERNS: dict[str, list[float]] = field(
        default_factory=lambda: {
            "big_four": [0.0],
            "half_note": [0.0, 2.0],
            "syncopated": [0.0, 1.5],
            "shuffle": [0.0, 1.5, 2.0, 3.5],
            "free": [],
        },
        init=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        valid = tuple(self._PATTERNS.keys())
        if self.pattern not in valid:
            raise ValueError(f"pattern must be one of {valid}, got {self.pattern!r}")
        valid_notes = ("root", "chord_tone", "shell")
        if self.accent_note not in valid_notes:
            raise ValueError(f"accent_note must be one of {valid_notes}")

    def _accent_positions(self) -> list[float]:
        if self.pattern == "free":
            n = random.randint(1, 3)
            positions = sorted(random.sample([0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5], n))
            return positions
        return self._PATTERNS[self.pattern]

    def _accent_pitch(self, chord: ChordLabel, low: int, high: int) -> list[int]:
        root = chord.root
        pcs = chord.pitch_classes()

        if self.accent_note == "root":
            p = nearest_pitch(root, (low + high) // 2)
            return [max(low, min(high, p))]

        if self.accent_note == "shell":
            seventh_pc = root + 10 if len(pcs) > 3 else root + 7
            seventh_pc %= 12
            anchor = (low + high) // 2
            p_root = max(low, min(high, nearest_pitch(root, anchor)))
            p_7 = max(low, min(high, nearest_pitch(seventh_pc, p_root)))
            return [p_root, p_7]

        # chord_tone
        if pcs:
            pc = int(random.choice(pcs))
            p = nearest_pitch(pc, (low + high) // 2)
            return [max(low, min(high, p))]
        p = nearest_pitch(root, (low + high) // 2)
        return [max(low, min(high, p))]

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        base_vel = self.base_velocity()
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        t = 0.0
        bar = 0

        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += 4.0
                bar += 1
                continue

            positions = self._accent_positions()
            pitches = self._accent_pitch(chord, low, high)

            for pos in positions:
                onset = t + pos
                if onset >= duration_beats:
                    break

                accent_vel = min(127, base_vel + 10 + random.randint(-3, 3))

                for pi, pitch in enumerate(pitches):
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(onset + pi * 0.02, 4),
                        duration=self.accent_duration,
                        velocity=accent_vel,
                    ))

            # Optional pickup to next chord
            if self.fill_last_beat and t + 4.0 < duration_beats:
                next_chord = chord_at(chords, t + 4.0)
                if next_chord and next_chord.root != chord.root:
                    target = nearest_pitch(next_chord.root, pitches[-1] if pitches else (low + high) // 2)
                    target = max(low, min(high, target))
                    # Chromatic approach from half-step below
                    approach = max(low, target - 1)
                    pickup_t = t + 3.5
                    if pickup_t < duration_beats:
                        notes.append(NoteInfo(
                            pitch=approach,
                            start=round(pickup_t, 4),
                            duration=0.4,
                            velocity=max(1, base_vel - 10),
                        ))

            t += 4.0
            bar += 1

        return notes
