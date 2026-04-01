"""
generators/afrobeats.py — Afrobeats and Amapiano pattern generator.

Layer: Application / Domain
Style: Afrobeats, Amapiano, Afro-pop, Afropiano.

Generates characteristic African pop elements:
  - Log drum patterns
  - Shaker/percussion grooves
  - Call-response percussive elements
  - Amapiano piano chords
  - Bouncy bass patterns

Variants:
    "afrobeats"  — standard Afrobeats grooves
    "amapiano"   — South African Amapiano (log drums, shakers)
    "afro_pop"   — polished Afro-pop production style
    "afro_rock"  — Afro-rock fusion
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
SHAKER = 70
CLAP = 39
LOG_DRUM_LOW = 62  # D4 area
LOG_DRUM_HIGH = 74


@dataclass
class AfrobeatsGenerator(PhraseGenerator):
    """
    Afrobeats/Amapiano pattern generator.

    variant:
        "afrobeats", "amapiano", "afro_pop", "afro_rock"
    log_drum_density:
        Density of log drum hits (0.0-1.0). Amapiano signature element.
    shaker_pattern:
        "eighth", "sixteenth", "triplet" — shaker subdivision.
    include_piano:
        Whether to include Amapiano-style piano chords.
    bounce_amount:
        How much rhythmic bounce/swing (0.0-1.0).
    percussion_layer:
        Whether to include additional percussion (congas, etc).
    """

    name: str = "Afrobeats Generator"
    variant: str = "afrobeats"
    log_drum_density: float = 0.6
    shaker_pattern: str = "sixteenth"
    include_piano: bool = True
    bounce_amount: float = 0.5
    percussion_layer: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "afrobeats",
        log_drum_density: float = 0.6,
        shaker_pattern: str = "sixteenth",
        include_piano: bool = True,
        bounce_amount: float = 0.5,
        percussion_layer: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.log_drum_density = max(0.0, min(1.0, log_drum_density))
        self.shaker_pattern = shaker_pattern
        self.include_piano = include_piano
        self.bounce_amount = max(0.0, min(1.0, bounce_amount))
        self.percussion_layer = percussion_layer

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

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            # Kick
            self._render_kick(notes, bar_start, duration_beats)

            # Snare/Clap
            self._render_snare(notes, bar_start, duration_beats)

            # Hi-hats / Shakers
            self._render_hihats(notes, bar_start, duration_beats)

            # Log drums (Amapiano signature)
            if self.variant in ("amapiano", "afro_pop"):
                self._render_log_drums(notes, bar_start, duration_beats, chord)

            # Piano chords
            if self.include_piano:
                self._render_piano(notes, bar_start, duration_beats, chord)

            # Percussion
            if self.percussion_layer:
                self._render_percussion(notes, bar_start, duration_beats)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_kick(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        bounce = self.bounce_amount * 0.1
        # Afrobeats kick: 4-on-floor with bounce
        for beat in range(4):
            onset = bar_start + beat + (bounce if beat % 2 == 1 else 0)
            if onset < total:
                vel = 100 if beat in (0, 2) else 85
                notes.append(
                    NoteInfo(
                        pitch=KICK,
                        start=round(onset, 6),
                        duration=0.3,
                        velocity=vel,
                    )
                )

    def _render_snare(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # Backbeat on 2 and 4
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=SNARE,
                        start=round(onset, 6),
                        duration=0.2,
                        velocity=105,
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=CLAP,
                        start=round(onset, 6),
                        duration=0.15,
                        velocity=85,
                    )
                )

    def _render_hihats(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        sub = {"eighth": 0.5, "sixteenth": 0.25, "triplet": 1.0 / 3.0}.get(
            self.shaker_pattern, 0.25
        )
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            # Skip some for groove
            if random.random() < 0.8:
                vel = 60 if idx % 2 == 0 else 45
                vel += random.randint(-5, 5)
                # Open hat on offbeats sometimes
                is_open = random.random() < 0.1
                hat = HH_OPEN if is_open else SHAKER if self.variant == "amapiano" else HH_CLOSED
                notes.append(
                    NoteInfo(
                        pitch=hat,
                        start=round(t, 6),
                        duration=0.3 if is_open else sub * 0.7,
                        velocity=max(20, min(80, vel)),
                    )
                )
            t += sub
            idx += 1

    def _render_log_drums(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        """Amapiano log drum pattern — pitched percussive hits."""
        root_pc = chord.root
        third_pc = (root_pc + 3) % 12
        fifth_pc = (root_pc + 7) % 12

        # Characteristic log drum rhythm
        offsets = [0.0, 0.75, 1.5, 2.25, 2.75, 3.5]
        pcs_cycle = [root_pc, fifth_pc, third_pc, root_pc, fifth_pc, third_pc]

        for i, offset in enumerate(offsets):
            if random.random() > self.log_drum_density:
                continue
            onset = bar_start + offset
            if onset >= total:
                continue

            pc = pcs_cycle[i % len(pcs_cycle)]
            pitch = max(LOG_DRUM_LOW, min(LOG_DRUM_HIGH, nearest_pitch(pc, LOG_DRUM_LOW + 6)))
            vel = 70 + random.randint(-10, 10)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=0.3,
                    velocity=vel,
                )
            )

    def _render_piano(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        """Amapiano-style piano chords — bright, rhythmic."""
        root_pc = chord.root
        mid = 60
        is_minor = chord.quality.name in ("MINOR", "MIN7")

        third_pc = (root_pc + (3 if is_minor else 4)) % 12
        fifth_pc = (root_pc + 7) % 12
        seventh_pc = (root_pc + 10) % 12

        pcs = [root_pc, third_pc, fifth_pc, seventh_pc]

        # Rhythmic stab pattern
        for stab_offset in [0.0, 1.5, 2.0, 3.0]:
            if stab_offset > 0 and random.random() < 0.3:
                continue
            onset = bar_start + stab_offset
            if onset >= total:
                continue

            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                vel = 60 + random.randint(-5, 5)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=0.8,
                        velocity=vel,
                    )
                )

    def _render_percussion(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        """Additional percussion layer (shaker ghost hits)."""
        # Subtle ghost shaker hits
        sub = 0.5
        t = bar_start + 0.25  # Offset from main grid
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.3:
                notes.append(
                    NoteInfo(
                        pitch=SHAKER,
                        start=round(t, 6),
                        duration=0.08,
                        velocity=30 + random.randint(0, 15),
                    )
                )
            t += sub
