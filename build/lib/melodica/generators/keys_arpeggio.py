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
generators/keys_arpeggio.py — Synth arpeggiator with LFO-style modulation.

Layer: Application / Domain

Produces rapid arpeggiated patterns from chord tones with
configurable direction, rate, octave spread, and swing feel.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


ARP_PATTERNS = {"up", "down", "updown", "random", "octave"}


@dataclass
class KeysArpeggioGenerator(PhraseGenerator):
    """
    Synth arpeggios with LFO-style modulation.

    arp_pattern: "up" | "down" | "updown" | "random" | "octave"
    rate: subdivision in beats (0.125 = 16th notes, 0.25 = 8th notes)
    octave_spread: number of octaves to span
    swing: 0.0 (straight) to 0.5 (max shuffle)
    """

    name: str = "Keys Arpeggio"
    arp_pattern: str = "up"
    rate: float = 0.125
    octave_spread: int = 2
    swing: float = 0.0
    lfo_rate: float = 0.0
    lfo_depth: float = 0.0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        arp_pattern: str = "up",
        rate: float = 0.125,
        octave_spread: int = 2,
        swing: float = 0.0,
        lfo_rate: float = 0.0,
        lfo_depth: float = 0.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if arp_pattern not in ARP_PATTERNS:
            raise ValueError(f"arp_pattern must be one of {ARP_PATTERNS}; got {arp_pattern!r}")
        self.arp_pattern = arp_pattern
        self.rate = max(0.05, rate)
        self.octave_spread = max(1, min(4, octave_spread))
        self.swing = max(0.0, min(0.5, swing))
        self.lfo_rate = max(0.0, lfo_rate)
        self.lfo_depth = max(0.0, min(1.0, lfo_depth))
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
        arp_idx = 0

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pool = self._build_pool(chord)
            if not pool:
                continue

            pitch = pool[arp_idx % len(pool)]
            arp_idx += 1

            # LFO modulation on velocity
            lfo_mod = 1.0
            if self.lfo_rate > 0 and self.lfo_depth > 0:
                lfo_mod = 1.0 + self.lfo_depth * 0.3 * math.sin(
                    2 * 3.14159 * self.lfo_rate * event.onset
                )

            vel = int(self._velocity() * event.velocity_factor * lfo_mod)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(0, min(MIDI_MAX, vel)),
                )
            )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_pool(self, chord: ChordLabel) -> list[int]:
        """Build arpeggio pitch pool across octave_spread octaves."""
        pcs = chord.pitch_classes()
        anchor = self.params.key_range_low + 4
        pool = []

        for octave in range(self.octave_spread):
            for pc in pcs:
                p = nearest_pitch(int(pc), anchor + octave * OCTAVE)
                if self.params.key_range_low <= p <= self.params.key_range_high:
                    pool.append(p)

        pool = sorted(set(pool))

        if self.arp_pattern == "down":
            pool = list(reversed(pool))
        elif self.arp_pattern == "updown":
            if len(pool) > 2:
                pool = pool + list(reversed(pool[:-1]))
        elif self.arp_pattern == "random":
            pass  # will randomize per-note selection
        elif self.arp_pattern == "octave":
            # Octave bounce: alternate between low and high octave
            root_pc = chord.bass if chord.bass is not None else chord.root
            low_p = nearest_pitch(int(root_pc), self.params.key_range_low)
            high_p = nearest_pitch(
                int(root_pc), self.params.key_range_low + OCTAVE * self.octave_spread
            )
            pool = [low_p, high_p]

        return pool

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        idx = 0
        while t < duration_beats:
            # Apply swing: even subdivisions delayed
            swing_offset = 0.0
            if idx % 2 == 1 and self.swing > 0:
                swing_offset = self.rate * self.swing

            onset = t + swing_offset
            if onset >= duration_beats:
                break
            dur = min(self.rate * 0.8, duration_beats - onset)
            events.append(RhythmEvent(onset=round(onset, 6), duration=round(dur, 6)))
            t += self.rate
            idx += 1
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
