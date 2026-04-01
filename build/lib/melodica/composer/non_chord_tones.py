"""
composer/non_chord_tones.py — Non-chord tone generator.

Adds musical ornaments on top of a harmonized progression:
- Passing tones (between chord tones)
- Neighbor tones (above/below chord tone)
- Suspensions (held note creates dissonance, then resolves)
- Anticipations (next chord tone arrives early)
- Pedal points (sustained bass note)
- Appoggiatura (leap to dissonance, stepwise resolution)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.types import NoteInfo, ChordLabel, Scale
from melodica.utils import nearest_pitch


@dataclass
class NonChordToneGenerator:
    """
    Adds non-chord tones to an existing note sequence.

    passing_prob:    probability of inserting passing tone between steps
    neighbor_prob:   probability of adding neighbor tone
    suspension_prob: probability of creating suspension
    anticipation_prob: probability of anticipation
    """

    passing_prob: float = 0.2
    neighbor_prob: float = 0.1
    suspension_prob: float = 0.1
    anticipation_prob: float = 0.05

    def add_non_chord_tones(
        self,
        notes: list[NoteInfo],
        chords: list[ChordLabel],
        key: Scale,
    ) -> list[NoteInfo]:
        """Add non-chord tones to existing notes."""
        if len(notes) < 2:
            return notes

        result = []
        sorted_notes = sorted(notes, key=lambda n: n.start)

        for i, note in enumerate(sorted_notes):
            result.append(note)

            # Find chord for this note
            chord = None
            for c in chords:
                if c.start <= note.start < c.start + c.duration:
                    chord = c
                    break
            if chord is None:
                continue

            chord_pcs = set(chord.pitch_classes())
            is_chord_tone = note.pitch % 12 in chord_pcs

            # Passing tone: if next note is a chord tone at a different pitch
            if i < len(sorted_notes) - 1 and random.random() < self.passing_prob:
                next_note = sorted_notes[i + 1]
                gap = next_note.pitch - note.pitch
                if 2 <= abs(gap) <= 4:
                    # Insert passing tone in between
                    pass_pitch = note.pitch + (1 if gap > 0 else -1)
                    pass_pitch = max(0, min(127, pass_pitch))
                    mid_time = (note.start + note.duration + next_note.start) / 2
                    pass_dur = min(note.duration * 0.4, 0.2)
                    result.append(
                        NoteInfo(
                            pitch=pass_pitch,
                            start=round(mid_time, 6),
                            duration=round(pass_dur, 6),
                            velocity=max(1, int(note.velocity * 0.7)),
                        )
                    )

            # Neighbor tone: add note above or below
            if random.random() < self.neighbor_prob and is_chord_tone:
                direction = random.choice([-2, 2])
                neighbor_pitch = note.pitch + direction
                if key.contains(neighbor_pitch % 12) or key.contains((neighbor_pitch + 1) % 12):
                    neighbor_pitch = max(0, min(127, neighbor_pitch))
                    neighbor_start = note.start + note.duration * 0.3
                    neighbor_dur = note.duration * 0.3
                    result.append(
                        NoteInfo(
                            pitch=neighbor_pitch,
                            start=round(neighbor_start, 6),
                            duration=round(neighbor_dur, 6),
                            velocity=max(1, int(note.velocity * 0.6)),
                        )
                    )

            # Suspension: delay resolution of next note
            if (
                i < len(sorted_notes) - 1
                and random.random() < self.suspension_prob
                and is_chord_tone
            ):
                next_note = sorted_notes[i + 1]
                if next_note.pitch != note.pitch:
                    # Hold current note a bit longer (suspension)
                    extended_dur = note.duration * 1.3
                    # Then resolve down
                    result.append(
                        NoteInfo(
                            pitch=next_note.pitch,
                            start=round(note.start + extended_dur, 6),
                            duration=round(note.duration * 0.5, 6),
                            velocity=max(1, int(note.velocity * 0.9)),
                        )
                    )

        # Sort by onset
        result.sort(key=lambda n: n.start)
        return result

    def add_pedal_point(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        pedal_pc: int | None = None,
    ) -> list[NoteInfo]:
        """Generate a sustained pedal point (bass note)."""
        if not chords:
            return []

        if pedal_pc is None:
            pedal_pc = chords[0].root

        pedal_pitch = nearest_pitch(pedal_pc, 36)  # low register
        pedal_pitch = max(24, min(60, pedal_pitch))

        return [
            NoteInfo(
                pitch=pedal_pitch,
                start=0.0,
                duration=round(duration_beats, 6),
                velocity=60,
            )
        ]
