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
generators/fills.py — Musical fills, turnarounds, and endings generator.

Layer: Application / Domain
Style: All genres — jazz turnarounds, rock fills, classical cadential runs.

Fills bridge the gap between phrases. Common types:
    "turnaround"    — jazz ii-V-I turnaround (bars 11-12 of 12-bar blues)
    "descending"    — scale run descending to tonic
    "ascending"     — scale run ascending
    "chromatic"     — chromatic descent/ascent fill
    "arpeggio_up"   — arpeggiated chord tones upward
    "arpeggio_down" — arpeggiated chord tones downward
    "blues_fill"    — blues pentatonic fill with bends
    "drum_fill"     — rhythmic fill pattern (percussive)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# Blues scale intervals
BLUES = [0, 3, 5, 6, 7, 10]


@dataclass
class FillGenerator(PhraseGenerator):
    """
    Fill / turnaround / ending generator.

    fill_type:
        Type of fill. See list above.
    fill_length:
        Duration in beats of the fill (default 2.0).
    position:
        Where to place the fill within each phrase:
        "end"   — fill at the end of each chord region
        "start" — fill at the beginning
        "middle" — fill in the middle
    velocity_curve:
        "crescendo" — getting louder
        "diminuendo" — getting softer
        "accented" — forte at start, fade
    """

    name: str = "Fill Generator"
    fill_type: str = "descending"
    fill_length: float = 2.0
    position: str = "end"
    velocity_curve: str = "crescendo"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        fill_type: str = "descending",
        fill_length: float = 2.0,
        position: str = "end",
        velocity_curve: str = "crescendo",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if fill_type not in (
            "turnaround",
            "descending",
            "ascending",
            "chromatic",
            "arpeggio_up",
            "arpeggio_down",
            "blues_fill",
            "drum_fill",
        ):
            raise ValueError(f"Unknown fill_type: {fill_type!r}")
        self.fill_type = fill_type
        self.fill_length = max(0.5, min(8.0, fill_length))
        self.position = position
        self.velocity_curve = velocity_curve
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

            # Determine if this event should have a fill
            fill_onset = event.onset
            fill_dur = min(self.fill_length, duration_beats - fill_onset)
            if fill_dur <= 0:
                continue

            if self.fill_type == "turnaround":
                fill_notes = self._turnaround(
                    chord, key, fill_onset, fill_dur, prev_pitch, low, high
                )
            elif self.fill_type in ("descending", "ascending"):
                fill_notes = self._scale_run(
                    chord, key, fill_onset, fill_dur, prev_pitch, low, high
                )
            elif self.fill_type == "chromatic":
                fill_notes = self._chromatic_run(fill_onset, fill_dur, prev_pitch, low, high)
            elif self.fill_type in ("arpeggio_up", "arpeggio_down"):
                fill_notes = self._arpeggio_fill(chord, fill_onset, fill_dur, prev_pitch, low, high)
            elif self.fill_type == "blues_fill":
                fill_notes = self._blues_fill(
                    chord, key, fill_onset, fill_dur, prev_pitch, low, high
                )
            else:  # drum_fill
                fill_notes = self._drum_fill(fill_onset, fill_dur, chord.root, low, high)

            # Apply velocity curve
            fill_notes = self._apply_vel_curve(fill_notes)

            notes.extend(fill_notes)
            if fill_notes:
                prev_pitch = fill_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Fill types
    # ------------------------------------------------------------------

    def _turnaround(
        self,
        chord: ChordLabel,
        key: Scale,
        onset: float,
        dur: float,
        prev: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        """Jazz turnaround: ii-V-I chromatic enclosure into root."""
        root = chord.root
        pcs = chord.pitch_classes()
        target = nearest_pitch(root, prev)
        # Walk down from target
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / max(steps, 1)
        for i in range(steps):
            p = target - i
            p = max(low, min(high, p))
            notes.append(
                NoteInfo(
                    pitch=p, start=round(t, 6), duration=step_dur * 0.85, velocity=self._velocity()
                )
            )
            t += step_dur
        return notes

    def _scale_run(
        self,
        chord: ChordLabel,
        key: Scale,
        onset: float,
        dur: float,
        prev: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        degs = key.degrees()
        if not degs:
            degs = [0]
        ascending = self.fill_type == "ascending"
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / steps
        pitch = prev
        for i in range(steps):
            if ascending:
                pitch += 2 if i % 2 == 0 else 1
            else:
                pitch -= 2 if i % 2 == 0 else 1
            pitch = max(low, min(high, pitch))
            if not key.contains(pitch % 12):
                pitch = nearest_pitch(chord.root, pitch)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=step_dur * 0.85,
                    velocity=self._velocity(),
                )
            )
            t += step_dur
        return notes

    def _chromatic_run(
        self,
        onset: float,
        dur: float,
        prev: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / steps
        direction = random.choice([-1, 1])
        for i in range(steps):
            p = prev + direction * i
            p = max(low, min(high, p))
            notes.append(
                NoteInfo(
                    pitch=p, start=round(t, 6), duration=step_dur * 0.85, velocity=self._velocity()
                )
            )
            t += step_dur
        return notes

    def _arpeggio_fill(
        self,
        chord: ChordLabel,
        onset: float,
        dur: float,
        prev: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        pcs = chord.pitch_classes()
        if not pcs:
            return []
        ascending = self.fill_type == "arpeggio_up"
        pitches = [nearest_pitch(int(pc), prev) for pc in pcs]
        if ascending:
            pitches.sort()
        else:
            pitches.sort(reverse=True)
        # Add octave extension
        if ascending:
            pitches.append(pitches[0] + 12)
        else:
            pitches.insert(0, pitches[0] - 12)
        pitches = [max(low, min(high, p)) for p in pitches]

        notes = []
        t = onset
        step_dur = dur / max(len(pitches), 1)
        for p in pitches:
            notes.append(
                NoteInfo(
                    pitch=p, start=round(t, 6), duration=step_dur * 0.85, velocity=self._velocity()
                )
            )
            t += step_dur
        return notes

    def _blues_fill(
        self,
        chord: ChordLabel,
        key: Scale,
        onset: float,
        dur: float,
        prev: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        root = chord.root
        pool = [(root + ivl) % 12 for ivl in BLUES]
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / steps
        pitch = prev
        for i in range(steps):
            if random.random() < 0.6:
                # Blues scale step
                pc = random.choice(pool)
                pitch = nearest_pitch(pc, pitch)
            else:
                pitch += random.choice([-1, -2, 1, 2])
            pitch = max(low, min(high, pitch))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=step_dur * 0.85,
                    velocity=self._velocity(),
                )
            )
            t += step_dur
        return notes

    def _drum_fill(
        self,
        onset: float,
        dur: float,
        root_pc: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        """Rhythmic fill on a single pitch (simulates a drum fill)."""
        pitch = nearest_pitch(root_pc, (low + high) // 2)
        pitch = max(low, min(high, pitch))
        # Accelerating rhythm: half → quarter → eighth → sixteenth
        notes = []
        t = onset
        subdivisions = [0.5, 0.5, 0.25, 0.25, 0.125, 0.125]
        for sd in subdivisions:
            if t >= onset + dur:
                break
            rem = min(sd, onset + dur - t)
            notes.append(
                NoteInfo(
                    pitch=pitch, start=round(t, 6), duration=rem * 0.8, velocity=self._velocity()
                )
            )
            t += sd
        return notes

    def _apply_vel_curve(self, notes: list[NoteInfo]) -> list[NoteInfo]:
        if not notes or len(notes) < 2:
            return notes
        n = len(notes)
        for i, note in enumerate(notes):
            progress = i / max(n - 1, 1)
            if self.velocity_curve == "crescendo":
                factor = 0.7 + 0.3 * progress
            elif self.velocity_curve == "diminuendo":
                factor = 1.0 - 0.3 * progress
            else:  # accented
                factor = 1.0 if i == 0 else 0.8
            notes[i] = NoteInfo(
                pitch=note.pitch,
                start=note.start,
                duration=note.duration,
                velocity=max(1, min(127, int(note.velocity * factor))),
                articulation=note.articulation,
                expression=dict(note.expression),
            )
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Place fills at the end of each 4-bar region
        t, events = 0.0, []
        fill_interval = max(self.fill_length, 4.0)
        while t < duration_beats:
            fill_start = t + fill_interval - self.fill_length
            if fill_start < duration_beats:
                events.append(
                    RhythmEvent(
                        onset=round(max(0, fill_start), 6),
                        duration=min(self.fill_length, duration_beats - fill_start),
                    )
                )
            t += fill_interval
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 35)
