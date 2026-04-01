"""
generators/victory_fanfare.py — Victory / Fanfare / Game event music generator.

Layer: Application / Domain
Style: Victory themes, fanfares, game over, title screen.

Generates short victory/event musical phrases:
  - Victory fanfare (triumphant, major key)
  - Game over (minor, descending)
  - Title screen (memorable, looping)
  - Level complete (ascending, celebratory)
  - Continue screen (tension, countdown)

Variants:
    "victory"       — triumphant victory fanfare
    "game_over"     — sad game over theme
    "title_screen"  — memorable title theme
    "level_complete" — level completion jingle
    "continue"      — continue/timeout screen
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch


@dataclass
class VictoryFanfareGenerator(PhraseGenerator):
    """Victory / Fanfare / Game event music generator."""

    name: str = "Victory Fanfare Generator"
    variant: str = "victory"
    register: int = 5
    dynamics: str = "forte"
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "victory",
        register: int = 5,
        dynamics: str = "forte",
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.register = max(3, min(6, register))
        self.dynamics = dynamics

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        root_pc = key.root
        base = root_pc + self.register * 12
        vel = {"piano": 50, "mezzo": 70, "forte": 90, "fortissimo": 110}.get(self.dynamics, 90)

        if self.variant == "victory":
            # Triumphant ascending fanfare
            intervals = [0, 4, 7, 12, 12, 7, 12, 16]
            durs = [0.2, 0.2, 0.2, 0.4, 0.2, 0.2, 0.2, 0.8]
            t = 0.0
            for i, iv in enumerate(intervals):
                pitch = max(36, min(108, base + iv))
                v = min(MIDI_MAX, vel + int(i / len(intervals) * 20))
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=durs[i], velocity=v))
                t += durs[i]
            # Chord underneath
            if chords:
                ch = chords[0]
                for pc in ch.pitch_classes()[:3]:
                    p = nearest_pitch(pc, 60)
                    notes.append(NoteInfo(pitch=p, start=0.0, duration=2.0, velocity=vel - 20))

        elif self.variant == "game_over":
            # Descending, sad
            intervals = [0, -1, -3, -5, -8, -12]
            durs = [0.4, 0.4, 0.4, 0.4, 0.6, 1.5]
            t = 0.0
            for i, iv in enumerate(intervals):
                pitch = max(36, min(96, base + iv))
                v = max(20, vel - i * 10)
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=durs[i], velocity=v))
                t += durs[i]

        elif self.variant == "title_screen":
            # Memorable, looping theme
            melody = [0, 4, 7, 4, 0, 2, 4, 7, 9, 7, 4, 2]
            durs = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
            t = 0.0
            for i, iv in enumerate(melody):
                pitch = max(48, min(96, base + iv))
                notes.append(
                    NoteInfo(pitch=pitch, start=round(t, 6), duration=durs[i] * 0.8, velocity=vel)
                )
                t += durs[i]

        elif self.variant == "level_complete":
            # Ascending scale run + chord
            t = 0.0
            for i in range(8):
                pitch = max(48, min(96, base + i * 2))
                notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=0.15, velocity=vel))
                t += 0.15
            # Final chord
            if chords:
                ch = chords[0] if chords else None
                if ch:
                    for pc in ch.pitch_classes()[:4]:
                        p = nearest_pitch(pc, base)
                        notes.append(
                            NoteInfo(
                                pitch=max(48, min(96, p)),
                                start=round(t, 6),
                                duration=1.0,
                                velocity=min(MIDI_MAX, vel + 10),
                            )
                        )

        elif self.variant == "continue":
            # Countdown tension
            t = 0.0
            for i in range(10):
                pitch = base
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(t, 6), duration=0.3, velocity=max(30, vel - i * 5)
                    )
                )
                t += 0.4

        last_chord = chords[-1] if chords else None
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
