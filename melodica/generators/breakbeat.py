"""
generators/breakbeat.py — Breakbeat drum pattern generator.

Layer: Application / Domain
Style: Drum & bass, jungle, breakbeat hardcore, IDM.

Breakbeats are syncopated drum patterns derived from sampled funk
breaks. This generator recreates the feel of chopped breakbeats.

Variants:
    "amen"     — Amen Brother break (the most sampled break in history)
    "funky"    — Funky Drummer style
    "think"    — Think break style
    "dnb"      — Drum & bass (double-time)
    "idm"      — Glitchy, complex IDM rhythms
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
RIM = 37
TOM_LOW = 41
TOM_MID = 45
TOM_HIGH = 50


@dataclass
class BreakbeatGenerator(PhraseGenerator):
    """
    Breakbeat drum pattern generator.

    variant:
        "amen", "funky", "think", "dnb", "idm"
    chop_probability:
        Probability of chopping/rearranging beats within a bar.
    ghost_notes:
        Include ghost notes (very soft snare/hat hits).
    double_time:
        If True, play at double speed (for DnB).
    """

    name: str = "Breakbeat Generator"
    variant: str = "amen"
    chop_probability: float = 0.3
    ghost_notes: bool = True
    double_time: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "amen",
        chop_probability: float = 0.3,
        ghost_notes: bool = True,
        double_time: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.chop_probability = max(0.0, min(1.0, chop_probability))
        self.ghost_notes = ghost_notes
        self.double_time = double_time
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

        notes: list[NoteInfo] = []
        last_chord = chords[-1]
        speed = 0.5 if self.double_time else 1.0

        t = 0.0
        while t < duration_beats:
            pattern = self._get_pattern()
            for pitch, offset, vel in pattern:
                onset = t + offset * speed
                if onset < duration_beats:
                    dur = 0.15 if pitch in (HH_CLOSED, HH_OPEN) else 0.25
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=dur,
                            velocity=max(1, min(127, vel)),
                        )
                    )

            # Ghost notes
            if self.ghost_notes:
                for _ in range(random.randint(1, 3)):
                    ghost_onset = t + round(random.uniform(0, 3.9) * speed, 2)
                    if ghost_onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=random.choice([SNARE, HH_CLOSED]),
                                start=round(ghost_onset, 6),
                                duration=0.08,
                                velocity=random.randint(30, 50),
                            )
                        )

            t += 4.0 * speed

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_pattern(self) -> list[tuple[int, float, int]]:
        """Return (pitch, beat_offset, velocity) tuples."""
        if self.variant == "amen":
            return [
                (KICK, 0.0, 110),
                (HH_CLOSED, 0.0, 70),
                (HH_CLOSED, 0.5, 55),
                (SNARE, 1.0, 110),
                (HH_CLOSED, 1.0, 65),
                (HH_CLOSED, 1.5, 55),
                (KICK, 2.0, 100),
                (HH_CLOSED, 2.0, 70),
                (SNARE, 2.5, 90),
                (HH_CLOSED, 2.75, 50),
                (SNARE, 3.0, 105),
                (HH_CLOSED, 3.0, 65),
                (KICK, 3.5, 95),
            ]
        elif self.variant == "funky":
            return [
                (KICK, 0.0, 110),
                (HH_CLOSED, 0.0, 70),
                (HH_CLOSED, 0.5, 60),
                (SNARE, 1.0, 110),
                (KICK, 1.5, 90),
                (HH_CLOSED, 1.5, 65),
                (KICK, 2.0, 105),
                (HH_CLOSED, 2.0, 70),
                (HH_CLOSED, 2.5, 55),
                (SNARE, 3.0, 110),
                (KICK, 3.5, 95),
                (HH_CLOSED, 3.5, 60),
            ]
        elif self.variant == "think":
            return [
                (KICK, 0.0, 110),
                (HH_OPEN, 0.0, 75),
                (SNARE, 1.0, 110),
                (HH_CLOSED, 1.25, 55),
                (KICK, 2.0, 100),
                (HH_OPEN, 2.0, 70),
                (SNARE, 3.0, 110),
                (TOM_LOW, 3.5, 80),
            ]
        elif self.variant == "dnb":
            return [
                (KICK, 0.0, 115),
                (HH_CLOSED, 0.0, 70),
                (HH_CLOSED, 0.25, 50),
                (SNARE, 0.5, 110),
                (HH_CLOSED, 0.5, 60),
                (HH_CLOSED, 0.75, 50),
                (KICK, 1.0, 95),
                (HH_CLOSED, 1.25, 55),
                (SNARE, 1.5, 100),
                (HH_CLOSED, 1.75, 50),
                (KICK, 2.0, 110),
                (SNARE, 2.5, 105),
                (KICK, 3.0, 90),
                (SNARE, 3.5, 95),
            ]
        else:  # idm
            # Glitchy, randomized
            hits = []
            for i in range(random.randint(8, 16)):
                offset = round(random.uniform(0, 3.9), 2)
                pitch = random.choice([KICK, SNARE, HH_CLOSED, TOM_HIGH, RIM])
                vel = random.randint(50, 115)
                hits.append((pitch, offset, vel))
            return sorted(hits, key=lambda x: x[1])
