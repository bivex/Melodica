"""Melody fill processing — passings and note smoothing.

Responsibilities:
  - Add passing tones between notes with large intervallic leaps
  - Snap fill notes to scale
"""

from __future__ import annotations

from melodica.types import NoteInfo, Scale
from melodica.utils import snap_to_scale


class FillProcessor:
    """Adds passing tones to smooth large melodic leaps."""

    def __init__(self, note_range_low: int | None, note_range_high: int | None, params):
        self.note_range_low = note_range_low if note_range_low is not None else params.key_range_low
        self.note_range_high = (
            note_range_high if note_range_high is not None else params.key_range_high
        )

    def fill_leaps(self, notes: list[NoteInfo], key: Scale) -> list[NoteInfo]:
        """Insert passing tones between notes with leaps > 4 semitones."""
        if len(notes) < 2:
            return notes

        result = [notes[0]]
        fills_added = 0
        max_fills = max(4, len(notes) // 2)

        for i in range(1, len(notes)):
            gap = notes[i].pitch - notes[i - 1].pitch
            abs_gap = abs(gap)

            if abs_gap > 4 and fills_added < max_fills:
                direction = 1 if gap > 0 else -1
                num_fills = min(abs_gap // 3, 4) if abs_gap > 7 else 1
                span = notes[i].start - notes[i - 1].start

                for fill_idx in range(num_fills):
                    if num_fills == 1:
                        frac = 0.5
                        step = min(abs_gap // 2, 4)
                    else:
                        frac = (fill_idx + 1) / (num_fills + 1)
                        step = round(abs_gap * frac)

                    pass_pitch = notes[i - 1].pitch + direction * max(1, step)
                    pass_start = notes[i - 1].start + span * frac

                    # Resolve key at fill position
                    active_key = key.get_key_at(pass_start) if hasattr(key, "get_key_at") else key
                    pass_pitch = snap_to_scale(
                        max(self.note_range_low, min(self.note_range_high, pass_pitch)), active_key
                    )

                    pass_dur = min(notes[i - 1].duration, 0.25)

                    result.append(
                        NoteInfo(
                            pitch=pass_pitch,
                            start=round(pass_start, 6),
                            duration=pass_dur,
                            velocity=max(1, min(127, int(notes[i].velocity * 0.65))),
                        )
                    )
                    fills_added += 1

            result.append(notes[i])

        return result
