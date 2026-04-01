"""
generators/jersey_club.py — Jersey Club pattern generator.

Layer: Application / Domain
Style: Jersey Club, Baltimore Club, TikTok club.

Generates characteristic Jersey Club elements:
  - Triplet kick pattern (signature bounce)
  - Chopped R&B vocal samples (pitched percussion)
  - Birdman "brrr" sample simulation
  - Stutter break rolls
  - Crisp hi-hats with open hat accents

Variants:
    "classic"     — classic Jersey Club bounce
    "tiktok"      — TikTok-optimized (catchy, shorter loops)
    "dark"        — darker, more aggressive Jersey Club
    "bedroom"     — lo-fi bedroom Jersey Club
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
RIM = 37


@dataclass
class JerseyClubGenerator(PhraseGenerator):
    """
    Jersey Club pattern generator.

    variant:
        "classic", "tiktok", "dark", "bedroom"
    kick_triplet_density:
        Density of triplet kick bounces (0.0-1.0).
    stutter_breaks:
        Whether to include stutter break rolls.
    chopped_samples:
        Whether to include pitched R&B vocal chop hits.
    birdman_sample:
        Whether to include birdman "brrr" style hits.
    """

    name: str = "Jersey Club Generator"
    variant: str = "classic"
    kick_triplet_density: float = 0.7
    stutter_breaks: bool = True
    chopped_samples: bool = True
    birdman_sample: bool = False
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic",
        kick_triplet_density: float = 0.7,
        stutter_breaks: bool = True,
        chopped_samples: bool = True,
        birdman_sample: bool = False,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.kick_triplet_density = max(0.0, min(1.0, kick_triplet_density))
        self.stutter_breaks = stutter_breaks
        self.chopped_samples = chopped_samples
        self.birdman_sample = birdman_sample

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        last_chord = chords[-1] if chords else None

        bar_start = 0.0
        while bar_start < duration_beats:
            # Triplet kicks — the Jersey Club signature
            self._render_kicks(notes, bar_start, duration_beats)

            # Snare/Clap
            self._render_snare(notes, bar_start, duration_beats)

            # Hi-hats
            self._render_hats(notes, bar_start, duration_beats)

            # Stutter breaks
            if self.stutter_breaks:
                self._render_stutter(notes, bar_start, duration_beats)

            # Chopped samples
            if self.chopped_samples:
                self._render_chops(notes, bar_start, duration_beats, last_chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_kicks(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        """Jersey Club triplet kick pattern."""
        # Classic: kick on 1, then triplet bounce on beat 2 and 4
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            vel = 115 if beat in (0, 2) else 95
            notes.append(NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=vel))

            # Triplet bounce after kick (on beats 2 and 4)
            if beat in (1, 3) and random.random() < self.kick_triplet_density:
                triplet = 1.0 / 3.0
                for t in range(3):
                    t_onset = onset + t * triplet
                    if t_onset < total:
                        t_vel = int(80 * (1.0 - t * 0.2))
                        notes.append(
                            NoteInfo(
                                pitch=KICK,
                                start=round(t_onset, 6),
                                duration=triplet * 0.7,
                                velocity=max(40, t_vel),
                            )
                        )

    def _render_snare(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.2, velocity=110)
                )
                notes.append(
                    NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=90)
                )

    def _render_hats(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            is_open = (i == 3 or i == 7) and random.random() < 0.5
            hat = HH_OPEN if is_open else HH_CLOSED
            dur = 0.4 if is_open else 0.12
            vel = 70 if i % 2 == 0 else 55
            notes.append(NoteInfo(pitch=hat, start=round(onset, 6), duration=dur, velocity=vel))

    def _render_stutter(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        """Stutter break rolls."""
        if random.random() < 0.4:
            # Insert stutter at end of bar
            stutter_start = bar_start + 3.5
            roll_len = random.choice([4, 6, 8])
            roll_dur = 0.5 / roll_len
            for r in range(roll_len):
                r_onset = stutter_start + r * roll_dur
                if r_onset < total:
                    vel = int(50 + (r / roll_len) * 40)
                    notes.append(
                        NoteInfo(
                            pitch=SNARE,
                            start=round(r_onset, 6),
                            duration=roll_dur * 0.6,
                            velocity=vel,
                        )
                    )

    def _render_chops(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel | None
    ) -> None:
        """Chopped R&B vocal samples."""
        mid = 72
        root_pc = chord.root if chord else 0
        for off in [0.5, 1.75, 2.5, 3.25]:
            if random.random() < 0.4:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pc = (root_pc + random.choice([0, 4, 7, 11])) % 12
            pitch = nearest_pitch(pc, mid)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=0.2,
                    velocity=55 + random.randint(0, 15),
                )
            )
