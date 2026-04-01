"""
generators/trap_drums.py — Trap drum pattern generator.

Layer: Application / Domain
Style: Trap, hip-hop, drill, modern rap.

Trap drums feature:
  - Rapid hi-hat rolls (32nd notes, triplet rolls)
  - 808 sub-bass on beats 1 and 3
  - Snare on beats 2 and 4 (or displaced)
  - Sparse, booming kick patterns

Variants:
    "standard"  — classic trap pattern
    "drill"     — UK/NY drill (sliding 808, syncopated)
    "melodic"   — melodic trap (more hi-hat variation)
    "minimal"   — sparse, atmospheric trap
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# GM-ish mapping
KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
SUB_808 = 36  # Low C


@dataclass
class TrapDrumsGenerator(PhraseGenerator):
    """
    Trap drum pattern generator.

    variant:
        "standard", "drill", "melodic", "minimal"
    hat_roll_density:
        How many hi-hat rolls per bar (0.0–1.0).
    kick_pattern:
        "standard" (beats 1, 3), "syncopated" (displaced), "sparse" (beat 1 only)
    open_hat_probability:
        Probability of open hi-hat hits.
    clap_on_two:
        If True, clap on beat 2 (standard). If False, clap on beat 3.
    """

    name: str = "Trap Drums Generator"
    variant: str = "standard"
    hat_roll_density: float = 0.5
    kick_pattern: str = "standard"
    open_hat_probability: float = 0.2
    clap_on_two: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "standard",
        hat_roll_density: float = 0.5,
        kick_pattern: str = "standard",
        open_hat_probability: float = 0.2,
        clap_on_two: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.hat_roll_density = max(0.0, min(1.0, hat_roll_density))
        self.kick_pattern = kick_pattern
        self.open_hat_probability = max(0.0, min(1.0, open_hat_probability))
        self.clap_on_two = clap_on_two
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
        low = self.params.key_range_low
        last_chord = chords[-1]

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            # 808/sub on beats 1 and (3)
            sub_pitch = max(low, nearest_pitch(chord.root, low + 12))
            self._add_note(notes, sub_pitch, bar_start, 3.5, 100, duration_beats)
            if self.kick_pattern != "sparse":
                self._add_note(notes, sub_pitch, bar_start + 2, 1.5, 90, duration_beats)

            # Kick
            if self.kick_pattern == "standard":
                self._add_note(notes, KICK, bar_start, 0.3, 110, duration_beats)
                self._add_note(notes, KICK, bar_start + 2, 0.3, 100, duration_beats)
            elif self.kick_pattern == "syncopated":
                self._add_note(notes, KICK, bar_start, 0.3, 110, duration_beats)
                self._add_note(notes, KICK, bar_start + 2.5, 0.3, 95, duration_beats)
                self._add_note(notes, KICK, bar_start + 3.5, 0.3, 85, duration_beats)
            else:
                self._add_note(notes, KICK, bar_start, 0.3, 110, duration_beats)

            # Snare/Clap on 2 and 4
            clap_beat = 1 if self.clap_on_two else 2
            self._add_note(notes, SNARE, bar_start + clap_beat, 0.3, 110, duration_beats)
            self._add_note(notes, CLAP, bar_start + clap_beat, 0.3, 90, duration_beats)
            self._add_note(notes, SNARE, bar_start + 3, 0.3, 110, duration_beats)
            self._add_note(notes, CLAP, bar_start + 3, 0.3, 90, duration_beats)

            # Hi-hats
            if self.variant in ("standard", "drill"):
                # Eighth-note hats with rolls
                for i in range(8):
                    onset = bar_start + i * 0.5
                    is_open = random.random() < self.open_hat_probability
                    hat = HH_OPEN if is_open else HH_CLOSED
                    vel = 80 if i % 2 == 0 else 65

                    # Rolls: insert 32nd-note subdivisions
                    if random.random() < self.hat_roll_density and i < 7:
                        for r in range(3):
                            roll_onset = onset + r * 0.125
                            self._add_note(notes, HH_CLOSED, roll_onset, 0.08, 60, duration_beats)

                    self._add_note(notes, hat, onset, 0.15, vel, duration_beats)

            elif self.variant == "melodic":
                # More complex hat patterns
                for i in range(16):
                    onset = bar_start + i * 0.25
                    if random.random() < 0.8:
                        vel = 75 + random.randint(-10, 10)
                        self._add_note(notes, HH_CLOSED, onset, 0.1, max(1, vel), duration_beats)

            elif self.variant == "minimal":
                # Sparse hats
                for beat in [0, 1, 2, 3]:
                    self._add_note(notes, HH_CLOSED, bar_start + beat, 0.15, 70, duration_beats)
                    if random.random() < 0.3:
                        self._add_note(
                            notes, HH_CLOSED, bar_start + beat + 0.5, 0.1, 55, duration_beats
                        )

            bar_start += 4.0

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _add_note(
        self, notes: list, pitch: int, onset: float, dur: float, vel: int, total: float
    ) -> None:
        if 0 <= onset < total:
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=dur,
                    velocity=max(1, min(127, vel)),
                )
            )
