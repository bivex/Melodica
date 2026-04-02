# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/phonk.py — Phonk/Memphis pattern generator.

Layer: Application / Domain
Style: Phonk, Memphis rap, drift phonk, cowbell phonk.

Generates characteristic Phonk elements:
  - Cowbell-driven patterns
  - Memphis vocal chop simulation (via pitched percussion)
  - Drift phonk bass slides
  - Lo-fi filtered drums
  - Aggressive 808 patterns

Variants:
    "classic_phonk"  — classic Memphis-influenced phonk
    "drift_phonk"    — drift phonk (cowbell-heavy, aggressive)
    "lofi_phonk"     — lo-fi filtered phonk
    "aggressive"     — hard-hitting modern phonk
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
COWBELL = 56
CLAP = 39
RIM = 37


@dataclass
class PhonkGenerator(PhraseGenerator):
    """
    Phonk/Memphis pattern generator.

    variant:
        "classic_phonk", "drift_phonk", "lofi_phonk", "aggressive"
    cowbell_density:
        Density of cowbell hits (0.0-1.0). Phonk signature element.
    bass_slide_amount:
        Amount of 808 pitch sliding in semitones (0-12).
    filter_cutoff:
        Simulated filter cutoff (0.0 = dark, 1.0 = bright).
    Memphis_chops:
        Whether to include Memphis-style pitched percussion hits.
    aggression:
        Overall intensity/hardness of the pattern (0.0-1.0).
    """

    name: str = "Phonk Generator"
    variant: str = "classic_phonk"
    cowbell_density: float = 0.7
    bass_slide_amount: int = 5
    filter_cutoff: float = 0.4
    memphis_chops: bool = True
    aggression: float = 0.6
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "classic_phonk",
        cowbell_density: float = 0.7,
        bass_slide_amount: int = 5,
        filter_cutoff: float = 0.4,
        memphis_chops: bool = True,
        aggression: float = 0.6,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.cowbell_density = max(0.0, min(1.0, cowbell_density))
        self.bass_slide_amount = max(0, min(12, bass_slide_amount))
        self.filter_cutoff = max(0.0, min(1.0, filter_cutoff))
        self.memphis_chops = memphis_chops
        self.aggression = max(0.0, min(1.0, aggression))

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

            # 808 Bass
            self._render_bass(notes, bar_start, duration_beats, chord, low)

            # Kick
            self._render_kick(notes, bar_start, duration_beats)

            # Snare
            self._render_snare(notes, bar_start, duration_beats)

            # Cowbell (Phonk signature)
            self._render_cowbell(notes, bar_start, duration_beats)

            # Hi-hats
            self._render_hihats(notes, bar_start, duration_beats)

            # Memphis chops
            if self.memphis_chops:
                self._render_memphis(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_bass(
        self,
        notes: list[NoteInfo],
        bar_start: float,
        total: float,
        chord: ChordLabel,
        low: int,
    ) -> None:
        root_pc = chord.root
        base_pitch = max(low, min(low + 12, nearest_pitch(root_pc, low + 6)))

        if self.variant == "drift_phonk":
            offsets = [(0.0, 3.0), (3.0, 0.8)]
        elif self.variant == "aggressive":
            offsets = [(0.0, 1.5), (1.5, 0.5), (2.5, 1.3)]
        else:
            offsets = [(0.0, 2.0), (2.0, 1.8)]

        prev_pitch = base_pitch
        for offset, dur in offsets:
            onset = bar_start + offset
            if onset >= total:
                continue

            pitch = base_pitch
            # Slide to fifth or other interval
            if random.random() < 0.5 and self.bass_slide_amount > 0:
                slide_pc = (root_pc + self.bass_slide_amount) % 12
                pitch = max(low, min(low + 12, nearest_pitch(slide_pc, prev_pitch)))

            vel = int(95 * (1.0 + self.aggression * 0.2))

            # Extended note for drift phonk
            actual_dur = dur + 0.5 if self.variant == "drift_phonk" else dur

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=min(actual_dur, 3.8),
                    velocity=min(MIDI_MAX, vel),
                )
            )
            prev_pitch = pitch

    def _render_kick(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        if self.variant == "aggressive":
            offsets = [0.0, 1.0, 2.0, 3.0]
        else:
            offsets = [0.0, 2.0]

        for off in offsets:
            onset = bar_start + off
            if onset < total:
                vel = int(110 * (1.0 + self.aggression * 0.15))
                notes.append(
                    NoteInfo(
                        pitch=KICK,
                        start=round(onset, 6),
                        duration=0.3,
                        velocity=min(MIDI_MAX, vel),
                    )
                )

    def _render_snare(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=SNARE,
                        start=round(onset, 6),
                        duration=0.25,
                        velocity=115,
                    )
                )
                if self.aggression > 0.5:
                    notes.append(
                        NoteInfo(
                            pitch=CLAP,
                            start=round(onset, 6),
                            duration=0.2,
                            velocity=90,
                        )
                    )

    def _render_cowbell(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        """Cowbell — the Phonk signature sound."""
        if self.variant == "drift_phonk":
            # Heavy cowbell: sixteenth notes with accents
            for i in range(16):
                onset = bar_start + i * 0.25
                if onset >= total:
                    break
                if random.random() < self.cowbell_density:
                    vel = 90 if i % 4 == 0 else 60
                    vel += random.randint(-5, 5)
                    notes.append(
                        NoteInfo(
                            pitch=COWBELL,
                            start=round(onset, 6),
                            duration=0.1,
                            velocity=max(30, min(MIDI_MAX, vel)),
                        )
                    )
        else:
            # Classic cowbell pattern: eighth notes
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset >= total:
                    break
                if random.random() < self.cowbell_density:
                    vel = 80 if i % 2 == 0 else 60
                    notes.append(
                        NoteInfo(
                            pitch=COWBELL,
                            start=round(onset, 6),
                            duration=0.15,
                            velocity=vel,
                        )
                    )

    def _render_hihats(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        if self.variant == "lofi_phonk":
            # Filtered hats: slower, lower velocity
            for i in range(4):
                onset = bar_start + i
                if onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=HH_CLOSED,
                            start=round(onset, 6),
                            duration=0.15,
                            velocity=45,
                        )
                    )
        else:
            # Standard eighth-note hats
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset >= total:
                    break
                vel = 70 if i % 2 == 0 else 55
                notes.append(
                    NoteInfo(
                        pitch=HH_CLOSED,
                        start=round(onset, 6),
                        duration=0.1,
                        velocity=vel,
                    )
                )

    def _render_memphis(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        """Memphis-style pitched percussion hits."""
        root_pc = chord.root
        # Use rim/clave-like hits at various pitches
        for off in [0.5, 1.75, 3.25]:
            if random.random() < 0.5:
                continue
            onset = bar_start + off
            if onset >= total:
                continue
            pitch = nearest_pitch(root_pc, 72)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=0.08,
                    velocity=50 + random.randint(0, 15),
                )
            )
