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
generators/downbeat_rest.py — Downbeat rest / anti-accent generator.

Style: Contemporary classical, jazz, progressive, ambient.

Creates rhythmic tension by deliberately avoiding the downbeat (beat 1),
producing breath marks, caesuras, and "holes" in the expected accent pattern.
The silence on the strong beat creates forward momentum and surprise.

Modes:
    "skip"       — skip beat 1 entirely (silent downbeat)
    "delay"      — delay the downbeat note by a fraction (anticipated)
    "caesura"    — insert a rest of configurable length on beat 1
    "breath"     — shorten the last note before downbeat, creating a breath gap
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class DownbeatRestGenerator(PhraseGenerator):
    """
    Downbeat rest / anti-accent generator.

    Creates tension by avoiding or delaying the expected downbeat accent.

    mode:
        How to avoid the downbeat: "skip", "delay", "caesura", "breath".
    delay_amount:
        How much to delay the downbeat (in beats). Only used in "delay" mode.
    caesura_length:
        Length of the rest on beat 1 (in beats). Only used in "caesura" mode.
    subdivision:
        Base subdivision for note placement in beats.
    pitch_strategy:
        How to choose pitches: "chord_tone", "scale_tone", "root".
    """

    name: str = "Downbeat Rest Generator"
    mode: str = "skip"
    delay_amount: float = 0.5
    caesura_length: float = 1.0
    subdivision: float = 1.0
    pitch_strategy: str = "chord_tone"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "skip",
        delay_amount: float = 0.5,
        caesura_length: float = 1.0,
        subdivision: float = 1.0,
        pitch_strategy: str = "chord_tone",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if mode not in ("skip", "delay", "caesura", "breath"):
            raise ValueError(f"Unknown downbeat_rest mode: {mode!r}")
        self.mode = mode
        self.delay_amount = max(0.0625, min(1.0, delay_amount))
        self.caesura_length = max(0.25, min(4.0, caesura_length))
        self.subdivision = max(0.25, min(2.0, subdivision))
        self.pitch_strategy = pitch_strategy
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
        t = 0.0

        while t < duration_beats:
            chord = chord_at(chords, t)
            beat_in_bar = t % 4.0
            is_downbeat = abs(beat_in_bar) < 0.01

            if self.mode == "skip":
                if not is_downbeat:
                    pitch = self._pick_pitch(chord, key)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision,
                            velocity=self._vel(),
                        )
                    )

            elif self.mode == "delay":
                if is_downbeat and t + self.delay_amount < duration_beats:
                    pitch = self._pick_pitch(chord, key)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t + self.delay_amount, 6),
                            duration=max(0.125, self.subdivision - self.delay_amount),
                            velocity=self._vel(1.1),
                        )
                    )
                elif not is_downbeat:
                    pitch = self._pick_pitch(chord, key)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision,
                            velocity=self._vel(),
                        )
                    )

            elif self.mode == "caesura":
                if is_downbeat:
                    pass  # silent downbeat
                elif beat_in_bar < self.caesura_length:
                    pass  # still in caesura zone
                else:
                    pitch = self._pick_pitch(chord, key)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision,
                            velocity=self._vel(),
                        )
                    )

            elif self.mode == "breath":
                pitch = self._pick_pitch(chord, key)
                if is_downbeat:
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision,
                            velocity=self._vel(0.6),
                        )
                    )
                elif abs(beat_in_bar - (4.0 - self.subdivision)) < 0.01:
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision * 0.4,
                            velocity=self._vel(0.5),
                        )
                    )
                else:
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.subdivision,
                            velocity=self._vel(),
                        )
                    )

            t += self.subdivision

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, key: Scale) -> int:
        pcs = chord.pitch_classes()
        if not pcs:
            return key.root * 12 + 60
        if self.pitch_strategy == "root":
            return nearest_pitch(pcs[0], 60)
        if self.pitch_strategy == "scale_tone":
            degrees = key.degrees()
            if degrees:
                return nearest_pitch(int(random.choice(degrees)) % 12, 60)
            return nearest_pitch(pcs[0], 60)
        return nearest_pitch(random.choice(pcs), 60)

    def _vel(self, factor: float = 1.0) -> int:
        base = int(self.params.density * 100)
        return max(1, min(127, int(base * factor)))
