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
generators/ornamentation.py — Baroque/Classical ornament generator.

Layer: Application / Domain
Style: Baroque, Classical, Romantic keyboard / orchestral writing.

Produces standard ornaments:
    "mordent"            — upper neighbor shake (przedsięwzięcie)
    "lower_mordent"      — lower neighbor shake (prall)
    "turn"               — upper→main→lower→main
    "inverted_turn"      — lower→main→upper→main
    "gruppetto"          — full turn with chromatic alteration option
    "shake"              — long trill with prepared start
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
class OrnamentationGenerator(PhraseGenerator):
    """
    Classical ornament generator.

    ornament_type:
        "mordent", "lower_mordent", "turn", "inverted_turn", "gruppetto", "shake"
    neighbor_interval:
        1 = half step (chromatic), 2 = whole step (diatonic). 0 = auto from scale.
    speed:
        Subdivision for the ornamental notes (0.0625 = 64th, 0.125 = 32nd).
    base_note:
        How to choose the sustained note:
        "chord_tone" — pick from chord tones
        "scale_tone" — pick from scale
        "prev_note"  — continue from previous
    density_ornaments:
        Probability of placing an ornament on each eligible event (0–1).
    """

    name: str = "Ornamentation Generator"
    ornament_type: str = "mordent"
    neighbor_interval: int = 0
    speed: float = 0.125
    base_note: str = "chord_tone"
    density_ornaments: float = 0.8
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        ornament_type: str = "mordent",
        neighbor_interval: int = 0,
        speed: float = 0.125,
        base_note: str = "chord_tone",
        density_ornaments: float = 0.8,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if ornament_type not in (
            "mordent",
            "lower_mordent",
            "turn",
            "inverted_turn",
            "gruppetto",
            "shake",
        ):
            raise ValueError(f"Unknown ornament_type: {ornament_type!r}")
        self.ornament_type = ornament_type
        self.neighbor_interval = neighbor_interval
        self.speed = max(0.03125, min(0.25, speed))
        self.base_note = base_note
        self.density_ornaments = max(0.0, min(1.0, density_ornaments))
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
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            base = self._pick_base(chord, prev_pitch, key, low, high)
            n_interval = self._resolve_interval(base, key)

            if random.random() > self.density_ornaments:
                # Plain note, no ornament
                notes.append(
                    NoteInfo(
                        pitch=base,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity())),
                    )
                )
                prev_pitch = base
                continue

            ornament_notes = self._render_ornament(
                base, n_interval, event.onset, event.duration, low, high
            )
            notes.extend(ornament_notes)
            if ornament_notes:
                prev_pitch = ornament_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------

    def _pick_base(self, chord: ChordLabel, prev: int, key: Scale, low: int, high: int) -> int:
        if self.base_note == "chord_tone":
            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
        elif self.base_note == "scale_tone":
            degs = key.degrees()
            pc = int(random.choice(degs)) if degs else chord.root
        else:
            return prev
        return max(low, min(high, nearest_pitch(pc, prev)))

    def _resolve_interval(self, base: int, key: Scale) -> int:
        if self.neighbor_interval > 0:
            return self.neighbor_interval
        # Auto: find closest scale degree that is 1-2 semitones away
        degs = key.degrees()
        base_pc = base % 12
        best = 1  # default half step
        for d in degs:
            diff = (int(d) - base_pc) % 12
            if diff in (1, 2):
                best = diff
                break
        return best

    def _render_ornament(
        self, base: int, interval: int, onset: float, dur: float, low: int, high: int
    ) -> list[NoteInfo]:
        upper = max(low, min(high, base + interval))
        lower = max(low, min(high, base - interval))
        vel = self._velocity()
        spd = self.speed
        notes: list[NoteInfo] = []
        t = onset
        end = onset + dur

        def _n(pitch: int, start: float, duration: float) -> NoteInfo:
            return NoteInfo(
                pitch=max(low, min(high, pitch)),
                start=round(start, 6),
                duration=duration,
                velocity=max(1, min(127, vel)),
            )

        if self.ornament_type == "mordent":
            # main–upper–main
            notes.append(_n(base, t, spd))
            t += spd
            if t < end:
                notes.append(_n(upper, t, spd))
                t += spd
            if t < end:
                notes.append(_n(base, t, max(0.05, end - t)))

        elif self.ornament_type == "lower_mordent":
            # main–lower–main
            notes.append(_n(base, t, spd))
            t += spd
            if t < end:
                notes.append(_n(lower, t, spd))
                t += spd
            if t < end:
                notes.append(_n(base, t, max(0.05, end - t)))

        elif self.ornament_type == "turn":
            # upper–main–lower–main
            notes.append(_n(upper, t, spd))
            t += spd
            if t < end:
                notes.append(_n(base, t, spd))
                t += spd
            if t < end:
                notes.append(_n(lower, t, spd))
                t += spd
            if t < end:
                notes.append(_n(base, t, max(0.05, end - t)))

        elif self.ornament_type == "inverted_turn":
            # lower–main–upper–main
            notes.append(_n(lower, t, spd))
            t += spd
            if t < end:
                notes.append(_n(base, t, spd))
                t += spd
            if t < end:
                notes.append(_n(upper, t, spd))
                t += spd
            if t < end:
                notes.append(_n(base, t, max(0.05, end - t)))

        elif self.ornament_type == "gruppetto":
            # main–upper–main–lower–main (5 notes)
            notes.append(_n(base, t, spd))
            t += spd
            if t < end:
                notes.append(_n(upper, t, spd))
                t += spd
            if t < end:
                notes.append(_n(base, t, spd))
                t += spd
            if t < end:
                notes.append(_n(lower, t, spd))
                t += spd
            if t < end:
                notes.append(_n(base, t, max(0.05, end - t)))

        elif self.ornament_type == "shake":
            # Extended trill: upper–main–upper–main–…
            while t < end:
                notes.append(_n(upper, t, spd))
                t += spd
                if t < end:
                    notes.append(_n(base, t, spd))
                    t += spd
            if notes:
                # End on main note
                notes[-1] = _n(base, notes[-1].start, notes[-1].duration)

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.9))
            t += 1.0
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 30)
