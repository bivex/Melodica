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
generators/lofi_hiphop.py — Lo-Fi Hip-Hop pattern generator.

Layer: Application / Domain
Style: Lo-fi hip-hop, chillhop, bedroom pop, study beats.

Generates characteristic lo-fi elements:
  - Dusty chord progressions with 7th/9th extensions
  - Swung drum patterns with ghost notes
  - Vinyl crackle simulation via velocity noise
  - Tape-stop effects
  - Melodic bass lines

Variants:
    "chill"      — relaxed, standard lo-fi
    "jazzy"      — jazz-influenced with extended chords
    "nostalgic"  — melancholic, minor-key focus
    "upbeat"     — more energetic lo-fi with swing
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
RIM = 37


@dataclass
class LoFiHipHopGenerator(PhraseGenerator):
    """
    Lo-Fi Hip-Hop pattern generator.

    variant:
        "chill", "jazzy", "nostalgic", "upbeat"
    swing_ratio:
        Amount of swing (0.5 = straight, 0.67 = medium swing).
    chord_voicing:
        "rootless", "seventh", "ninth", "eleventh" — chord extension level.
    include_drums:
        Whether to include drum pattern alongside chords.
    include_bass:
        Whether to include bass line.
    vinyl_noise:
        Simulate vinyl crackle via velocity variation (0.0-1.0).
    tape_stop:
        Probability of tape-stop effect at phrase end (0.0-1.0).
    """

    name: str = "Lo-Fi Hip-Hop Generator"
    variant: str = "chill"
    swing_ratio: float = 0.62
    chord_voicing: str = "ninth"
    include_drums: bool = True
    include_bass: bool = True
    vinyl_noise: float = 0.3
    tape_stop: float = 0.1
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "chill",
        swing_ratio: float = 0.62,
        chord_voicing: str = "ninth",
        include_drums: bool = True,
        include_bass: bool = True,
        vinyl_noise: float = 0.3,
        tape_stop: float = 0.1,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.swing_ratio = max(0.5, min(0.75, swing_ratio))
        self.chord_voicing = chord_voicing
        self.include_drums = include_drums
        self.include_bass = include_bass
        self.vinyl_noise = max(0.0, min(1.0, vinyl_noise))
        self.tape_stop = max(0.0, min(1.0, tape_stop))

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

            # Chords with extensions
            self._render_chords(notes, bar_start, duration_beats, chord)

            # Bass
            if self.include_bass:
                self._render_bass(notes, bar_start, duration_beats, chord)

            # Drums
            if self.include_drums:
                self._render_drums(notes, bar_start, duration_beats)

            bar_start += 4.0

        # Tape stop at end
        if random.random() < self.tape_stop and notes:
            self._apply_tape_stop(notes, duration_beats)

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_chords(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        root_pc = chord.root
        mid = 60  # Middle C area

        # Build chord tones with extensions
        pcs = [root_pc]
        if self.chord_voicing in ("seventh", "ninth", "eleventh"):
            third = (root_pc + (3 if chord.quality.name in ("MINOR", "MIN7") else 4)) % 12
            pcs.append(third)
            fifth = (root_pc + 7) % 12
            pcs.append(fifth)
            seventh = (root_pc + 10) % 12
            pcs.append(seventh)
        if self.chord_voicing in ("ninth", "eleventh"):
            ninth = (root_pc + 14) % 12
            pcs.append(ninth)
        if self.chord_voicing == "eleventh":
            eleventh = (root_pc + 17) % 12
            pcs.append(eleventh)

        # Lo-fi chord rhythm: stab on beat 1, sometimes beat 3
        for stab_beat in [0.0, 2.0]:
            if stab_beat > 0 and random.random() > 0.6:
                continue

            # Swing adjustment for beat 3
            if stab_beat == 2.0 and self.variant in ("jazzy", "upbeat"):
                stab_beat += (self.swing_ratio - 0.5) * 0.5

            onset = bar_start + stab_beat
            if onset >= total:
                continue

            # Vinyl noise: velocity variation
            base_vel = 65
            vel_noise = int(random.gauss(0, self.vinyl_noise * 15))

            for pc in pcs:
                pitch = nearest_pitch(pc, mid)
                dur = 2.0 if self.variant == "chill" else 1.5
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=dur,
                        velocity=max(30, min(MIDI_MAX, base_vel + vel_noise)),
                    )
                )

    def _render_bass(
        self, notes: list[NoteInfo], bar_start: float, total: float, chord: ChordLabel
    ) -> None:
        root_pc = chord.root
        low = max(36, self.params.key_range_low)
        pitch = max(low, nearest_pitch(root_pc, low + 6))

        # Lo-fi bass: root on beat 1, fifth or octave on beat 3
        for beat, vel_base in [(0.0, 75), (2.0, 60)]:
            onset = bar_start + beat
            if onset >= total:
                continue

            actual_pitch = pitch
            if beat == 2.0 and random.random() < 0.4:
                fifth_pc = (root_pc + 7) % 12
                actual_pitch = max(low, nearest_pitch(fifth_pc, pitch))

            vel_noise = int(random.gauss(0, self.vinyl_noise * 10))
            notes.append(
                NoteInfo(
                    pitch=actual_pitch,
                    start=round(onset, 6),
                    duration=1.8,
                    velocity=max(30, min(MIDI_MAX, vel_base + vel_noise)),
                )
            )

    def _render_drums(self, notes: list[NoteInfo], bar_start: float, total: float) -> None:
        swing = self.swing_ratio

        for beat in range(4):
            # Kick on 1 and 3
            if beat in (0, 2):
                onset = bar_start + beat
                if onset < total:
                    vel = 85 + int(random.gauss(0, self.vinyl_noise * 8))
                    notes.append(
                        NoteInfo(
                            pitch=KICK,
                            start=round(onset, 6),
                            duration=0.3,
                            velocity=max(40, min(100, vel)),
                        )
                    )

            # Snare/Rim on 2 and 4
            if beat in (1, 3):
                onset = bar_start + beat
                if onset < total:
                    if self.variant == "nostalgic":
                        pitch = RIM
                        vel = 65
                    else:
                        pitch = SNARE
                        vel = 80
                    vel += int(random.gauss(0, self.vinyl_noise * 8))
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=0.2,
                            velocity=max(30, min(100, vel)),
                        )
                    )

            # Hi-hats with swing
            eighth_1 = bar_start + beat
            eighth_2 = bar_start + beat + swing * 0.5

            for pos in [eighth_1, eighth_2]:
                if pos >= total:
                    continue
                # Skip some for space
                if random.random() < 0.15:
                    continue
                vel = 55 if pos == eighth_1 else 40
                vel += int(random.gauss(0, self.vinyl_noise * 6))
                notes.append(
                    NoteInfo(
                        pitch=HH_CLOSED,
                        start=round(pos, 6),
                        duration=0.1,
                        velocity=max(20, min(80, vel)),
                    )
                )

    def _apply_tape_stop(self, notes: list[NoteInfo], duration_beats: float) -> None:
        """Simulate tape stop by gradually lowering pitch of last notes."""
        stop_start = duration_beats - 1.0
        for i, note in enumerate(notes):
            if note.start >= stop_start:
                # Lower pitch gradually
                distance = note.start - stop_start
                pitch_drop = int(distance * 6)  # 6 semitones per beat
                notes[i] = NoteInfo(
                    pitch=max(24, note.pitch - pitch_drop),
                    start=note.start,
                    duration=note.duration * (1.0 + distance * 0.3),
                    velocity=max(1, int(note.velocity * (1.0 - distance * 0.5))),
                )
