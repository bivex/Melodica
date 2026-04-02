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
generators/guitar_sweep.py — Sweep picking arpeggio generator.

Layer: Application / Domain

Wide-interval arpeggios played with one continuous pick motion,
simulating guitar sweep picking technique.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


SWEEP_DIRECTIONS = {"up", "down", "both"}


@dataclass
class GuitarSweepGenerator(PhraseGenerator):
    """
    Sweep picking arpeggios.

    sweep_direction: "up" | "down" | "both"
    note_count: number of notes per sweep (3–7 typical)
    speed: time between notes in beats (0.08 = very fast)
    let_ring: if True, notes sustain; if False, staccato
    """

    name: str = "Guitar Sweep"
    sweep_direction: str = "down"
    note_count: int = 5
    speed: float = 0.08
    let_ring: bool = False
    velocity_curve: float = 0.8
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        sweep_direction: str = "down",
        note_count: int = 5,
        speed: float = 0.08,
        let_ring: bool = False,
        velocity_curve: float = 0.8,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if sweep_direction not in SWEEP_DIRECTIONS:
            raise ValueError(
                f"sweep_direction must be one of {SWEEP_DIRECTIONS}; got {sweep_direction!r}"
            )
        self.sweep_direction = sweep_direction
        self.note_count = max(3, min(7, note_count))
        self.speed = max(0.03, min(0.5, speed))
        self.let_ring = let_ring
        self.velocity_curve = max(0.0, min(1.0, velocity_curve))
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

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            sweep_pitches = self._build_sweep(chord)
            if not sweep_pitches:
                continue

            base_vel = int(self._velocity() * event.velocity_factor)

            for i, pitch in enumerate(sweep_pitches):
                # Velocity curve: louder at extremes, softer in middle
                progress = i / max(len(sweep_pitches) - 1, 1)
                vel_boost = 1.0 + self.velocity_curve * 0.2 * (abs(2.0 * progress - 1.0) ** 0.5)
                vel = int(base_vel * vel_boost)

                note_start = event.onset + i * self.speed
                if note_start >= duration_beats:
                    break

                if self.let_ring:
                    note_dur = max(0.1, event.duration - i * self.speed)
                else:
                    note_dur = self.speed * 0.8

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(note_start, 6),
                        duration=round(note_dur, 6),
                        velocity=max(0, min(MIDI_MAX, vel)),
                        articulation=None if self.let_ring else "staccato",
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_sweep(self, chord: ChordLabel) -> list[int]:
        """Build sweep arpeggio pitch sequence."""
        pcs = chord.pitch_classes()
        anchor_low = self.params.key_range_low + 12
        anchor_high = self.params.key_range_high - 12

        # Build ascending arpeggio across note_count notes
        pitches = []
        anchor = anchor_low
        for i in range(self.note_count):
            pc = pcs[i % len(pcs)]
            octave_offset = (i // len(pcs)) * OCTAVE
            p = nearest_pitch(int(pc), anchor + octave_offset)
            if self.params.key_range_low <= p <= self.params.key_range_high:
                pitches.append(p)

        pitches = sorted(set(pitches))

        # Apply direction
        if self.sweep_direction == "down":
            pitches = list(reversed(pitches))
        elif self.sweep_direction == "both":
            if len(pitches) > 2:
                pitches = pitches + list(reversed(pitches[:-1]))

        return pitches

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Space sweeps apart by their total duration + gap
        sweep_dur = self.note_count * self.speed
        gap = max(0.25, sweep_dur * 0.5)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(sweep_dur, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=round(dur, 6)))
            t += sweep_dur + gap
        return events

    def _velocity(self) -> int:
        return int(65 + self.params.density * 30)
