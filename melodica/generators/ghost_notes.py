"""
generators/ghost_notes.py — Ghost notes generator for realistic drum patterns.

Layer: Application / Domain
Style: All drum-based genres.

Generates ghost notes — quiet, subtle percussive hits that add groove
and human feel to drum patterns. Essential for realistic-sounding drums.

Targets:
    "snare"    — ghost notes on snare (most common)
    "kick"     — ghost kick hits
    "hihat"    — subtle hi-hat variations
    "tom"      — ghost tom fills

Patterns:
    "funk"     — funk-style ghost notes between backbeats
    "hiphop"   — hip-hop ghost snare rolls
    "jazz"     — jazz ride cymbal ghost notes
    "linear"   — linear ghost notes (no simultaneous hits)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import chord_at


SNARE = 38
KICK = 36
HH_CLOSED = 42
TOM_LOW = 41
TOM_MID = 45
RIM = 37


@dataclass
class GhostNotesGenerator(PhraseGenerator):
    """
    Ghost notes generator for realistic drum patterns.

    target:
        "snare", "kick", "hihat", "tom"
    pattern:
        "funk", "hiphop", "jazz", "linear"
    ghost_velocity:
        Base velocity for ghost notes (should be quiet, 20-50).
    ghost_density:
        Probability of ghost note insertion (0.0-1.0).
    placement:
        "sixteenth", "triplet", "thirty_second" — subdivision grid.
    """

    name: str = "Ghost Notes Generator"
    target: str = "snare"
    pattern: str = "funk"
    ghost_velocity: int = 35
    ghost_density: float = 0.6
    placement: str = "sixteenth"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        target: str = "snare",
        pattern: str = "funk",
        ghost_velocity: int = 35,
        ghost_density: float = 0.6,
        placement: str = "sixteenth",
    ) -> None:
        super().__init__(params)
        self.target = target
        self.pattern = pattern
        self.ghost_velocity = max(10, min(60, ghost_velocity))
        self.ghost_density = max(0.0, min(1.0, ghost_density))
        self.placement = placement

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        last_chord = chords[-1] if chords else None
        pitch = self._get_pitch()

        bar_start = 0.0
        while bar_start < duration_beats:
            if self.pattern == "funk":
                self._render_funk(notes, bar_start, duration_beats, pitch)
            elif self.pattern == "hiphop":
                self._render_hiphop(notes, bar_start, duration_beats, pitch)
            elif self.pattern == "jazz":
                self._render_jazz(notes, bar_start, duration_beats, pitch)
            elif self.pattern == "linear":
                self._render_linear(notes, bar_start, duration_beats, pitch)
            else:
                self._render_funk(notes, bar_start, duration_beats, pitch)
            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_pitch(self) -> int:
        return {
            "snare": SNARE,
            "kick": KICK,
            "hihat": HH_CLOSED,
            "tom": random.choice([TOM_LOW, TOM_MID]),
        }.get(self.target, SNARE)

    def _render_funk(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        sub = self._subdivision()
        # Ghost notes between main backbeats (beats 2 and 4)
        for beat in range(4):
            for s in range(int(1.0 / sub)):
                pos = bar_start + beat + s * sub
                if pos >= total:
                    break
                # Skip downbeats and backbeats (those are main hits)
                if s == 0:
                    continue
                # Higher density near backbeats
                proximity_to_backbeat = min(abs(pos - bar_start - 2), abs(pos - bar_start - 4))
                prob = self.ghost_density * (1.0 - proximity_to_backbeat * 0.3)
                if random.random() < prob:
                    vel = self.ghost_velocity + random.randint(-8, 8)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(pos, 6),
                            duration=sub * 0.5,
                            velocity=max(10, min(60, vel)),
                        )
                    )

    def _render_hiphop(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        # Hip-hop: ghost snare rolls before main snare hits
        for snare_beat in [1.0, 3.0]:
            roll_start = snare_beat - 0.5
            for i in range(4):
                pos = bar_start + roll_start + i * 0.125
                if pos >= total or pos < bar_start:
                    continue
                if random.random() < self.ghost_density:
                    # Crescendo toward snare
                    vel = int(self.ghost_velocity * (0.5 + i * 0.15))
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(pos, 6),
                            duration=0.08,
                            velocity=max(10, min(50, vel)),
                        )
                    )

    def _render_jazz(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        # Jazz: comping ghost notes with swing feel
        swing_ratio = 0.67
        for beat in range(4):
            eighth_1 = bar_start + beat
            eighth_2 = bar_start + beat + swing_ratio * 0.5
            for pos in [eighth_1, eighth_2]:
                if pos >= total:
                    break
                if random.random() < self.ghost_density * 0.4:
                    vel = self.ghost_velocity + random.randint(-5, 10)
                    notes.append(
                        NoteInfo(
                            pitch=RIM if self.target == "snare" else pitch,
                            start=round(pos, 6),
                            duration=0.1,
                            velocity=max(15, min(50, vel)),
                        )
                    )

    def _render_linear(
        self, notes: list[NoteInfo], bar_start: float, total: float, pitch: int
    ) -> None:
        # Linear: ghost notes fill gaps between main hits
        sub = self._subdivision()
        t = bar_start
        while t < min(bar_start + 4.0, total):
            if random.random() < self.ghost_density * 0.3:
                vel = int(self.ghost_velocity * random.uniform(0.6, 1.0))
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=sub * 0.4,
                        velocity=max(10, min(50, vel)),
                    )
                )
            t += sub

    def _subdivision(self) -> float:
        return {
            "sixteenth": 0.25,
            "triplet": 1.0 / 3.0,
            "thirty_second": 0.125,
        }.get(self.placement, 0.25)
