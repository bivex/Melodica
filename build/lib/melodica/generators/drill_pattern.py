"""
generators/drill_pattern.py — UK/NY Drill pattern generator.

Layer: Application / Domain
Style: UK Drill, NY Drill, Brooklyn Drill.

Complete drill pattern generator producing characteristic elements:
  - Sliding 808 bass with pitch bends
  - Stutter hi-hat rolls (3-5-7 note bursts)
  - Off-beat snare/clap placement
  - Sparse kick patterns
  - Dark piano chord stabs

Variants:
    "uk_drill"       — UK drill (syncopated, sliding 808)
    "ny_drill"       — NY/Brooklyn drill (harder, more aggressive)
    "melodic_drill"  — melodic drill with piano emphasis
    "dark_drill"     — atmospheric, minimal drill
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
CLAP = 39


@dataclass
class DrillPatternGenerator(PhraseGenerator):
    """
    UK/NY Drill complete pattern generator.

    variant:
        "uk_drill", "ny_drill", "melodic_drill", "dark_drill"
    slide_amount:
        How much 808 slides between notes in semitones (0-12).
    stutter_intensity:
        Density of hi-hat stutter rolls (0.0-1.0).
    snare_displacement:
        How far snare is displaced from beat 2/4 in sixteenths (0-4).
    include_piano:
        Whether to include dark piano chord stabs.
    """

    name: str = "Drill Pattern Generator"
    variant: str = "uk_drill"
    slide_amount: int = 7
    stutter_intensity: float = 0.5
    snare_displacement: int = 1
    include_piano: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "uk_drill",
        slide_amount: int = 7,
        stutter_intensity: float = 0.5,
        snare_displacement: int = 1,
        include_piano: bool = True,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.slide_amount = max(0, min(12, slide_amount))
        self.stutter_intensity = max(0.0, min(1.0, stutter_intensity))
        self.snare_displacement = max(0, min(4, snare_displacement))
        self.include_piano = include_piano

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
        low = max(24, self.params.key_range_low)
        last_chord = chords[-1]

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            root_pc = chord.root

            # 808 Bass
            self._render_808(notes, bar_start, duration_beats, root_pc, low, chord)

            # Kick
            self._render_kick(notes, bar_start, duration_beats)

            # Snare
            self._render_snare(notes, bar_start, duration_beats)

            # Hi-hats
            self._render_hihats(notes, bar_start, duration_beats)

            # Piano stabs
            if self.include_piano:
                self._render_piano(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_808(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        root_pc: int,
        low: int,
        chord: ChordLabel,
    ) -> None:
        base_pitch = max(low, min(low + 12, nearest_pitch(root_pc, low + 6)))

        if self.variant == "uk_drill":
            offsets = [(0.0, 1.5), (1.5, 0.5), (2.5, 1.3)]
        elif self.variant == "ny_drill":
            offsets = [(0.0, 1.8), (2.0, 0.8), (3.0, 0.8)]
        elif self.variant == "melodic_drill":
            offsets = [(0.0, 2.5), (2.75, 1.0)]
        else:  # dark_drill
            offsets = [(0.0, 3.5), (3.5, 0.4)]

        prev_pitch = base_pitch
        for offset, dur in offsets:
            onset = bar_start + offset
            if onset >= total:
                continue

            pitch = base_pitch
            # Slide: alternate between root and fifth or other intervals
            if random.random() < 0.5:
                slide_pc = (root_pc + self.slide_amount) % 12
                pitch = max(low, min(low + 12, nearest_pitch(slide_pc, prev_pitch)))

            # Extended slide note
            actual_dur = dur + 0.3 if self.variant in ("uk_drill", "ny_drill") else dur
            vel = 100 if offset == 0.0 else 85

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=min(actual_dur, 3.8),
                    velocity=vel,
                )
            )

            # Slide chromatic walk
            if prev_pitch != pitch and self.slide_amount > 0:
                step = 1 if pitch > prev_pitch else -1
                pos = prev_pitch
                walk_start = onset - 0.25
                while pos != pitch and walk_start < total:
                    if walk_start >= bar_start:
                        notes.append(
                            NoteInfo(
                                pitch=max(low, pos),
                                start=round(max(bar_start, walk_start), 6),
                                duration=0.08,
                                velocity=max(1, vel - 30),
                            )
                        )
                    pos += step
                    walk_start += 0.06
            prev_pitch = pitch

    def _render_kick(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        if self.variant == "ny_drill":
            kick_offsets = [0.0, 1.0, 2.0, 3.0]
        elif self.variant == "dark_drill":
            kick_offsets = [0.0, 2.5]
        else:
            kick_offsets = [0.0, 2.0]

        for off in kick_offsets:
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=KICK,
                        start=round(onset, 6),
                        duration=0.3,
                        velocity=110,
                    )
                )

    def _render_snare(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # Displaced snares characteristic of drill
        disp = self.snare_displacement * 0.25
        for beat in [1, 3]:
            onset = bar_start + beat + disp
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=SNARE,
                        start=round(onset, 6),
                        duration=0.25,
                        velocity=110,
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=CLAP,
                        start=round(onset, 6),
                        duration=0.2,
                        velocity=85,
                    )
                )

    def _render_hihats(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        # Eighth note base
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break

            vel = 80 if i % 2 == 0 else 60

            # Stutter roll
            if random.random() < self.stutter_intensity and i in (3, 5, 7):
                roll_len = random.choice([3, 5, 7])
                roll_dur = 0.25 / roll_len
                for r in range(roll_len):
                    roll_onset = onset - 0.25 + r * roll_dur
                    if bar_start <= roll_onset < total:
                        notes.append(
                            NoteInfo(
                                pitch=HH_CLOSED,
                                start=round(roll_onset, 6),
                                duration=roll_dur * 0.6,
                                velocity=int(45 + (r / roll_len) * 35),
                            )
                        )

            is_open = random.random() < 0.1
            hat = HH_OPEN if is_open else HH_CLOSED
            notes.append(
                NoteInfo(
                    pitch=hat,
                    start=round(onset, 6),
                    duration=0.3 if is_open else 0.12,
                    velocity=vel,
                )
            )

    def _render_piano(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
    ) -> None:
        # Dark piano stabs — minor chord voicings
        root_pc = chord.root
        third_pc = (root_pc + 3) % 12  # Minor third for dark sound
        fifth_pc = (root_pc + 7) % 12
        seventh_pc = (root_pc + 10) % 12  # Minor 7th

        piano_low = 60
        pcs = [root_pc, third_pc, fifth_pc, seventh_pc]

        # Stab on beat 1 and sometimes beat 3
        for stab_beat in [0, 2]:
            if random.random() > 0.6 and stab_beat > 0:
                continue
            onset = bar_start + stab_beat
            if onset >= total:
                continue
            for pc in pcs:
                pitch = nearest_pitch(pc, piano_low)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=1.5,
                        velocity=70 + random.randint(-5, 5),
                    )
                )
