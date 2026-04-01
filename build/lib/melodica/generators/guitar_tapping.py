"""
generators/guitar_tapping.py — Two-hand tapping guitar generator.

Layer: Application / Domain
Style: Shred, prog, metal, math rock.

Two-hand tapping uses both hands on the fretboard for wide-interval
arpeggios and rapid patterns impossible with conventional technique.

Patterns:
    "arpeggio" — tapping through chord tones across wide range
    "scale"    — scalar tapping pattern
    "poly"     — polyphonic tapping (two independent lines)
    "cascade"  — cascading notes from high to low
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class GuitarTappingGenerator(PhraseGenerator):
    """
    Two-hand tapping guitar generator.

    pattern:
        "arpeggio", "scale", "poly", "cascade"
    width_interval:
        Maximum interval in semitones between tapping positions.
    notes_per_cycle:
        Notes per tapping cycle before repeating.
    hammer_velocity:
        Velocity difference between picked and hammered notes.
    """

    name: str = "Guitar Tapping Generator"
    pattern: str = "arpeggio"
    width_interval: int = 12
    notes_per_cycle: int = 6
    hammer_velocity: float = 0.8
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "arpeggio",
        width_interval: int = 12,
        notes_per_cycle: int = 6,
        hammer_velocity: float = 0.8,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.width_interval = max(5, min(24, width_interval))
        self.notes_per_cycle = max(3, min(12, notes_per_cycle))
        self.hammer_velocity = max(0.3, min(1.0, hammer_velocity))
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            seq = self._build_sequence(chord, key, mid)
            t = event.onset
            end = event.onset + event.duration
            vel = self._velocity()
            idx = 0

            while t < end:
                pitch = seq[idx % len(seq)]
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
                n_dur = min(0.125, end - t)

                # Hammer notes softer
                v = int(vel * self.hammer_velocity) if idx % 3 != 0 else vel

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=n_dur * 0.85,
                        velocity=max(1, min(127, v)),
                    )
                )
                t += 0.125
                idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_sequence(self, chord: ChordLabel, key: Scale, anchor: int) -> list[int]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [anchor]

        n = self.notes_per_cycle
        half = self.width_interval // 2

        if self.pattern == "arpeggio":
            low_pos = anchor - half
            high_pos = anchor + half
            seq = []
            for i in range(n):
                pc = pcs[i % len(pcs)]
                if i % 2 == 0:
                    seq.append(nearest_pitch(int(pc), low_pos))
                else:
                    seq.append(nearest_pitch(int(pc), high_pos))
            return seq

        elif self.pattern == "scale":
            degs = key.degrees()
            return [
                nearest_pitch(int(degs[i % len(degs)]), anchor - half + i * 3) for i in range(n)
            ]

        elif self.pattern == "poly":
            # Two interleaved lines
            line_a = [nearest_pitch(int(pcs[i % len(pcs)]), anchor) for i in range(n // 2)]
            line_b = [
                nearest_pitch(int(pcs[i % len(pcs)]), anchor + self.width_interval)
                for i in range(n // 2)
            ]
            seq = []
            for a, b in zip(line_a, line_b):
                seq.extend([a, b])
            return seq[:n]

        else:  # cascade
            high = anchor + half
            return [high - i * (self.width_interval // n) for i in range(n)]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(2.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += dur + 0.5
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
