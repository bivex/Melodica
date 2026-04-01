"""
generators/drum_kit_pattern.py — Full drum kit pattern generator across genres.

Layer: Application / Domain
Style: Rock, jazz, latin, funk, hip-hop.

Produces bar-length drum patterns using General MIDI drum map pitches.
Each style has a characteristic kick/snare/hat pattern with optional fills.

Drum map (MIDI):
    kick=36, snare=38, hh_closed=42, hh_open=46,
    tom_low=41, tom_mid=45, tom_high=50, crash=49, ride=51
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
TOM_LOW = 41
TOM_MID = 45
TOM_HIGH = 50
CRASH = 49
RIDE = 51

STYLE_PATTERNS: dict[str, list[tuple[int, float, int]]] = {
    "rock": [
        (KICK, 0.0, 110),
        (HH_CLOSED, 0.0, 70),
        (HH_CLOSED, 0.5, 55),
        (SNARE, 1.0, 110),
        (HH_CLOSED, 1.0, 65),
        (HH_CLOSED, 1.5, 55),
        (KICK, 2.0, 105),
        (HH_CLOSED, 2.0, 70),
        (HH_CLOSED, 2.5, 55),
        (SNARE, 3.0, 110),
        (HH_CLOSED, 3.0, 65),
        (KICK, 3.5, 95),
        (HH_CLOSED, 3.5, 55),
    ],
    "jazz": [
        (KICK, 0.0, 85),
        (RIDE, 0.0, 70),
        (RIDE, 0.5, 60),
        (SNARE, 0.75, 50),
        (RIDE, 1.0, 70),
        (RIDE, 1.5, 60),
        (KICK, 1.5, 80),
        (SNARE, 1.75, 50),
        (RIDE, 2.0, 70),
        (RIDE, 2.5, 60),
        (KICK, 2.5, 85),
        (SNARE, 2.75, 50),
        (RIDE, 3.0, 70),
        (RIDE, 3.5, 60),
        (KICK, 3.5, 80),
    ],
    "latin": [
        (KICK, 0.0, 100),
        (HH_CLOSED, 0.0, 65),
        (SNARE, 0.5, 80),
        (HH_CLOSED, 0.5, 55),
        (KICK, 1.0, 95),
        (HH_CLOSED, 1.0, 65),
        (SNARE, 1.5, 80),
        (HH_CLOSED, 1.5, 55),
        (KICK, 2.0, 100),
        (HH_CLOSED, 2.0, 65),
        (SNARE, 2.5, 85),
        (HH_CLOSED, 2.5, 55),
        (KICK, 3.0, 95),
        (HH_CLOSED, 3.0, 65),
        (SNARE, 3.5, 80),
        (HH_CLOSED, 3.5, 55),
    ],
    "funk": [
        (KICK, 0.0, 110),
        (HH_CLOSED, 0.0, 70),
        (SNARE, 0.5, 60),
        (HH_CLOSED, 0.25, 50),
        (SNARE, 1.0, 110),
        (HH_CLOSED, 0.5, 55),
        (KICK, 1.25, 90),
        (HH_CLOSED, 0.75, 50),
        (KICK, 2.0, 105),
        (HH_CLOSED, 1.0, 65),
        (SNARE, 2.5, 90),
        (HH_CLOSED, 1.25, 50),
        (SNARE, 3.0, 100),
        (HH_CLOSED, 1.5, 55),
        (KICK, 3.5, 95),
        (HH_CLOSED, 1.75, 50),
    ],
    "hiphop": [
        (KICK, 0.0, 115),
        (SNARE, 1.0, 110),
        (KICK, 2.0, 110),
        (SNARE, 3.0, 105),
        (HH_CLOSED, 0.0, 60),
        (HH_CLOSED, 1.0, 55),
        (HH_CLOSED, 2.0, 60),
        (HH_CLOSED, 3.0, 55),
    ],
}


@dataclass
class DrumKitPatternGenerator(PhraseGenerator):
    """
    Full drum kit patterns across genres.

    style:
        "rock", "jazz", "latin", "funk", "hiphop"
    hihat_pattern:
        "eighth", "sixteenth", "open"
    fill_frequency:
        Probability of a fill at the end of a bar (0.0–1.0).
    """

    name: str = "Drum Kit Pattern Generator"
    style: str = "rock"
    hihat_pattern: str = "eighth"
    fill_frequency: float = 0.2
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "rock",
        hihat_pattern: str = "eighth",
        fill_frequency: float = 0.2,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.style = style
        self.hihat_pattern = hihat_pattern
        self.fill_frequency = max(0.0, min(1.0, fill_frequency))
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
        bar_idx = 0
        t = 0.0

        while t < duration_beats:
            pattern = STYLE_PATTERNS.get(self.style, STYLE_PATTERNS["rock"])
            for pitch, offset, vel in pattern:
                onset = t + offset
                if onset < duration_beats:
                    dur = 0.12 if pitch in (HH_CLOSED, HH_OPEN, RIDE) else 0.25
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=dur,
                            velocity=max(1, min(127, vel)),
                        )
                    )

            # Extra hi-hat subdivision
            if self.hihat_pattern == "sixteenth":
                for sub in [0.25, 0.75, 1.25, 1.75, 2.25, 2.75, 3.25, 3.75]:
                    onset = t + sub
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED,
                                start=round(onset, 6),
                                duration=0.08,
                                velocity=random.randint(40, 55),
                            )
                        )
            elif self.hihat_pattern == "open":
                for sub in [0.5, 1.5, 2.5, 3.5]:
                    onset = t + sub
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=HH_OPEN,
                                start=round(onset, 6),
                                duration=0.4,
                                velocity=random.randint(55, 70),
                            )
                        )

            # Fill at end of bar
            if random.random() < self.fill_frequency:
                fill_start = t + 3.0
                for i, tom in enumerate([TOM_HIGH, TOM_MID, TOM_LOW]):
                    onset = fill_start + i * 0.25
                    if onset < duration_beats:
                        notes.append(
                            NoteInfo(
                                pitch=tom,
                                start=round(onset, 6),
                                duration=0.2,
                                velocity=random.randint(80, 110),
                            )
                        )

            t += 4.0
            bar_idx += 1

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
