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
generators/tremolo_strings.py — Sustained string tremolo (bow tremolo) generator.

Layer: Application / Domain
Style: Orchestral, film scoring, ambient.

Unlike tremolo_picking (guitar), this produces sustained bowed tremolo:
rapid bow strokes on sustained notes/chords, creating a shimmering texture.

Variants:
    "single"  — tremolo on one note
    "chord"   — tremolo on chord voicing (divisi strings)
    "octave"  — tremolo on octave doubling
    "cluster" — tremolo on adjacent scale tones (dissonant shimmer)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed, snap_to_scale


@dataclass
class TremoloStringsGenerator(PhraseGenerator):
    """
    Sustained bowed string tremolo generator.

    variant:
        "single", "chord", "octave", "cluster"
    bow_speed:
        Subdivision in beats (0.0625 = very fast shimmer).
    dynamic_swell:
        If True, apply slow dynamic swells across the tremolo.
    """

    name: str = "Tremolo Strings Generator"
    variant: str = "chord"
    bow_speed: float = 0.0625
    dynamic_swell: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "chord",
        bow_speed: float = 0.0625,
        dynamic_swell: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.bow_speed = max(0.02, min(0.2, bow_speed))
        self.dynamic_swell = dynamic_swell
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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitches = self._pick_pitches(chord, mid, key)
            end = min(event.onset + event.duration, duration_beats)
            t = event.onset
            total_dur = end - event.onset
            note_idx = 0

            while t < end:
                for p in pitches:
                    if t >= end:
                        break
                    n_dur = min(self.bow_speed, end - t)
                    vel = self._dynamic(t - event.onset, total_dur, note_idx)
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(t, 6),
                            duration=n_dur * 0.85,
                            velocity=max(1, min(127, vel)),
                        )
                    )
                    t += self.bow_speed
                    note_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitches(self, chord: ChordLabel, anchor: int, key: Scale) -> list[int]:
        low = self.params.key_range_low
        high = self.params.key_range_high

        if self.variant == "single":
            root = nearest_pitch(chord.root, anchor)
            root = snap_to_scale(root, key)
            return [max(low, min(high, root))]
        elif self.variant == "chord":
            return [max(low, min(high, snap_to_scale(p, key))) for p in chord_pitches_closed(chord, anchor)]
        elif self.variant == "octave":
            root = nearest_pitch(chord.root, anchor)
            root = snap_to_scale(root, key)
            return [max(low, min(high, root)), min(127, snap_to_scale(root + 12, key))]
        elif self.variant == "cluster":
            root = nearest_pitch(chord.root, anchor)
            root = snap_to_scale(root, key)
            return [max(low, min(high, snap_to_scale(root + i, key))) for i in range(3)]
        return [max(low, min(high, snap_to_scale(nearest_pitch(chord.root, anchor), key)))]

    def _dynamic(self, elapsed: float, total: float, note_idx: int) -> int:
        base = int(45 + self.params.density * 25)
        if self.dynamic_swell and total > 0:
            progress = elapsed / total
            swell = 0.7 + 0.3 * (1.0 - abs(2.0 * progress - 1.0))
            base = int(base * swell)
        # Slight bow variation
        base += random.randint(-2, 2)
        return max(1, base)

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(4.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += 4.0
        return events
