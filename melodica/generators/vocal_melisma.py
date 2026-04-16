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
generators/vocal_melisma.py — Melismatic vocal run generator.

Layer: Application / Domain

Produces melismatic vocal runs with ornaments and style-specific contours.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


STYLES = {"rnb", "gospel", "opera", "pop"}

_STYLE_RUNS: dict[str, list[int]] = {
    "rnb": [0, 1, 2, 1, 0, -1, 0, 2],
    "gospel": [0, 2, 4, 5, 4, 2, 0, -1, 0],
    "opera": [0, 2, 4, 7, 4, 2, 0],
    "pop": [0, 1, 2, 3, 2, 1, 0],
}


@dataclass
class VocalMelismaGenerator(PhraseGenerator):
    name: str = "Vocal Melisma"
    style: str = "rnb"
    run_length: int = 4
    ornament_prob: float = 0.4
    vibrato_depth: float = 0.3
    register_center: int = 60
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "rnb",
        run_length: int = 4,
        ornament_prob: float = 0.4,
        vibrato_depth: float = 0.3,
        register_center: int = 60,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if style not in STYLES:
            raise ValueError(f"style must be one of {STYLES}; got {style!r}")
        self.style = style
        self.run_length = max(2, min(16, run_length))
        self.ornament_prob = max(0.0, min(1.0, ornament_prob))
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        self.register_center = max(48, min(84, register_center))
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
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        last_chord: ChordLabel | None = None
        prev_pitch = context.prev_pitch if context and context.prev_pitch else self.register_center

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            run_pitches = self._build_run(chord, prev_pitch, key)
            if not run_pitches:
                continue

            note_dur = event.duration / len(run_pitches)
            base_vel = int(self._velocity() * event.velocity_factor)

            for i, pitch in enumerate(run_pitches):
                note_start = event.onset + i * note_dur
                if note_start >= duration_beats:
                    break
                arc = 1.0 + 0.15 * math.sin(3.14159 * i / max(len(run_pitches) - 1, 1))
                vel = int(base_vel * arc)

                if random.random() < self.ornament_prob and i > 0:
                    gp = snap_to_scale(
                        max(
                            self.params.key_range_low,
                            min(self.params.key_range_high, pitch + random.choice([-1, 1])),
                        ),
                        key,
                    )
                    gd = min(0.05, note_dur * 0.3)
                    notes.append(
                        NoteInfo(
                            pitch=gp,
                            start=round(note_start - gd, 6),
                            duration=round(gd, 6),
                            velocity=max(1, int(vel * 0.5)),
                            articulation="staccato",
                        )
                    )

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(note_start, 6),
                        duration=round(max(0.05, note_dur * 0.9), 6),
                        velocity=max(0, min(MIDI_MAX, vel)),
                    )
                )
                prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_run(self, chord: ChordLabel, anchor: int, key: Scale | None = None) -> list[int]:
        contour = _STYLE_RUNS.get(self.style, _STYLE_RUNS["rnb"])
        pcs = chord.pitch_classes()
        pitches, cur = [], anchor
        for i in range(self.run_length):
            pc = int(pcs[contour[i % len(contour)] % len(pcs)])
            p = nearest_pitch(pc, cur)
            if key is not None:
                p = snap_to_scale(p, key)
            if self.params.key_range_low <= p <= self.params.key_range_high:
                pitches.append(p)
                cur = p
        return pitches

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            rd = min(random.uniform(0.75, 1.5), duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=round(rd, 6)))
            t += rd + random.uniform(0.25, 0.75)
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 40)
