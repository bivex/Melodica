"""Guide tone line generator.

Connects 3rd and 7th of each chord through smooth voice leading —
the foundation of jazz comping and arranging. Guide tones define
the harmonic identity of each chord with minimal notes.

Used in:
  - Freddie Green-style guitar comping
  - Jazz piano left-hand comping
  - Arranging for horn sections
  - Walking bass line construction

Players: Freddie Green, Jim Hall, Wynton Kelly.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Quality, Scale
from melodica.utils import nearest_pitch


@dataclass
class GuideToneGenerator(PhraseGenerator):
    """Generate guide tone lines (3rds and 7ths) through chord changes.

    Parameters
    ----------
    voice : str
        "3rd" — follow the 3rd of each chord.
        "7th" — follow the 7th of each chord.
        "both" — output both 3rd and 7th per chord (two-voice).
        "交替" — alternate between 3rd and 7th, choosing closest.
    rhythm_value : float
        Duration of each guide tone in beats (default 4.0 = whole note).
    connect : bool
        Use chromatic passing tones between guide tones for smooth connection.
    velocity_profile : str
        "flat", " legato", "accent_changes" (louder on new chord).
    """

    name: str = field(default="guide_tone", init=False)
    voice: str = "both"
    rhythm_value: float = 4.0
    connect: bool = True
    velocity_profile: str = "accent_changes"
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid = ("3rd", "7th", "both", "alternate")
        if self.voice not in valid:
            raise ValueError(f"voice must be one of {valid}, got {self.voice!r}")

    def _chord_3rd_7th(self, chord: ChordLabel) -> tuple[int, int]:
        """Return pitch classes for 3rd and 7th of chord."""
        root = chord.root
        quality = chord.quality

        if quality in (Quality.MAJOR, Quality.MAJOR7):
            third_pc = (root + 4) % 12
            seventh_pc = (root + 11) % 12
        elif quality in (Quality.MINOR, Quality.MINOR7):
            third_pc = (root + 3) % 12
            seventh_pc = (root + 10) % 12
        elif quality == Quality.DOMINANT7:
            third_pc = (root + 4) % 12
            seventh_pc = (root + 10) % 12
        elif quality == Quality.HALF_DIM7:
            third_pc = (root + 3) % 12
            seventh_pc = (root + 10) % 12
        elif quality == Quality.DIMINISHED:
            third_pc = (root + 3) % 12
            seventh_pc = (root + 9) % 12
        elif quality == Quality.AUGMENTED:
            third_pc = (root + 4) % 12
            seventh_pc = (root + 10) % 12
        else:
            third_pc = (root + 4) % 12
            seventh_pc = (root + 10) % 12

        return third_pc, seventh_pc

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

        prev_3rd: int | None = None
        prev_7th: int | None = None

        for i, chord in enumerate(chords):
            third_pc, seventh_pc = self._chord_3rd_7th(chord)
            chord_start = chord.start
            chord_dur = min(chord.duration, duration_beats - chord_start) if chord_start < duration_beats else chord.duration

            anchor = (low + high) // 2
            if prev_3rd is not None:
                anchor = prev_3rd

            p3 = nearest_pitch(third_pc, anchor)
            p7 = nearest_pitch(seventh_pc, prev_7th if prev_7th is not None else p3)
            p3 = max(low, min(high, p3))
            p7 = max(low, min(high, p7))

            vel = base_vel
            if self.velocity_profile == "accent_changes":
                vel = min(127, base_vel + 8)
            elif self.velocity_profile == "legato":
                vel = max(1, base_vel - 5)

            dur = min(self.rhythm_value, chord_dur)

            if self.voice == "3rd":
                notes.append(NoteInfo(
                    pitch=p3, start=round(chord_start, 4),
                    duration=dur * 0.95, velocity=vel,
                ))
            elif self.voice == "7th":
                notes.append(NoteInfo(
                    pitch=p7, start=round(chord_start, 4),
                    duration=dur * 0.95, velocity=vel,
                ))
            elif self.voice == "both":
                notes.append(NoteInfo(
                    pitch=p3, start=round(chord_start, 4),
                    duration=dur * 0.95, velocity=vel,
                ))
                notes.append(NoteInfo(
                    pitch=p7, start=round(chord_start, 4),
                    duration=dur * 0.95, velocity=max(1, vel - 3),
                ))
            else:  # alternate
                # Pick whichever is closest to previous
                if prev_3rd is not None:
                    if abs(p3 - prev_3rd) <= abs(p7 - prev_3rd):
                        notes.append(NoteInfo(
                            pitch=p3, start=round(chord_start, 4),
                            duration=dur * 0.95, velocity=vel,
                        ))
                    else:
                        notes.append(NoteInfo(
                            pitch=p7, start=round(chord_start, 4),
                            duration=dur * 0.95, velocity=vel,
                        ))
                else:
                    notes.append(NoteInfo(
                        pitch=p3, start=round(chord_start, 4),
                        duration=dur * 0.95, velocity=vel,
                    ))

            # Optional chromatic connection
            if self.connect and i < len(chords) - 1:
                next_chord = chords[i + 1]
                next_3rd_pc, next_7th_pc = self._chord_3rd_7th(next_chord)
                next_3rd = nearest_pitch(next_3rd_pc, p3)

                if abs(next_3rd - p3) > 2:
                    # Insert a passing tone
                    direction = 1 if next_3rd > p3 else -1
                    passing = p3 + direction
                    pass_start = chord_start + dur * 0.75
                    if pass_start < duration_beats and low <= passing <= high:
                        notes.append(NoteInfo(
                            pitch=passing, start=round(pass_start, 4),
                            duration=dur * 0.2, velocity=max(1, vel - 8),
                        ))

            prev_3rd = p3
            prev_7th = p7

        return notes
