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
generators/stealth_state.py — Stealth game state machine music generator.

Layer: Application / Domain
Style: Stealth game audio, Metal Gear Solid, Hitman, Dishonored.

Generates music that adapts to stealth states:
  - hidden: quiet, minimal, sparse ambient
  - caution: subtle pulse, added tension
  - alert: drums enter, rhythm drives
  - pursuit: full combat intensity
  - evading: post-pursuit tension

Each state has characteristic density, rhythm, and dynamics.
Parameter `stealth_state` controls which state is active.
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
TIMPANI = 47


@dataclass
class StealthStateGenerator(PhraseGenerator):
    """
    Stealth game state machine music generator.

    stealth_state:
        "hidden", "caution", "alert", "pursuit", "evading"
    transition_speed:
        How quickly the music changes between states (0.0-1.0).
        0 = instant switch, 1 = gradual morph.
    heartbeat:
        Whether to include heartbeat-like pulse in hidden/caution.
    """

    name: str = "Stealth State Generator"
    stealth_state: str = "hidden"
    transition_speed: float = 0.5
    heartbeat: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        stealth_state: str = "hidden",
        transition_speed: float = 0.5,
        heartbeat: bool = True,
    ) -> None:
        super().__init__(params)
        self.stealth_state = stealth_state
        self.transition_speed = max(0.0, min(1.0, transition_speed))
        self.heartbeat = heartbeat

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

            state = self.stealth_state
            if state == "hidden":
                self._render_hidden(notes, bar_start, duration_beats, chord, low)
            elif state == "caution":
                self._render_caution(notes, bar_start, duration_beats, chord, low)
            elif state == "alert":
                self._render_alert(notes, bar_start, duration_beats, chord, low)
            elif state == "pursuit":
                self._render_pursuit(notes, bar_start, duration_beats, chord, low)
            elif state == "evading":
                self._render_evading(notes, bar_start, duration_beats, chord, low)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_hidden(self, notes, bar_start, total, chord, low):
        """Almost silent — heartbeat, distant drones."""
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        # Soft drone
        if bar_start < total:
            notes.append(
                NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=25)
            )
        # Heartbeat: two soft hits
        if self.heartbeat and bar_start + 1 < total:
            notes.append(
                NoteInfo(pitch=TIMPANI, start=round(bar_start + 1, 6), duration=0.3, velocity=30)
            )
            notes.append(
                NoteInfo(pitch=TIMPANI, start=round(bar_start + 1.4, 6), duration=0.3, velocity=22)
            )

    def _render_caution(self, notes, bar_start, total, chord, low):
        """Subtle pulse, tension building."""
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        # Pulsing bass
        for i in range(4):
            onset = bar_start + i
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.8, velocity=45)
                )
        # Added strings tension
        mid = 60
        for pc in chord.pitch_classes()[:2]:
            p = nearest_pitch(pc, mid)
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=p, start=round(bar_start, 6), duration=3.8, velocity=35)
                )
        # Heartbeat faster
        if self.heartbeat:
            for beat in [0.5, 1.5]:
                if bar_start + beat < total:
                    notes.append(
                        NoteInfo(
                            pitch=TIMPANI,
                            start=round(bar_start + beat, 6),
                            duration=0.2,
                            velocity=40,
                        )
                    )

    def _render_alert(self, notes, bar_start, total, chord, low):
        """Drums enter, rhythm drives, tension peaks."""
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        # Driving bass
        for beat in range(4):
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.6, velocity=70)
                )
        # Drums
        if bar_start < total:
            notes.append(NoteInfo(pitch=KICK, start=round(bar_start, 6), duration=0.3, velocity=85))
        if bar_start + 2 < total:
            notes.append(
                NoteInfo(pitch=SNARE, start=round(bar_start + 2, 6), duration=0.2, velocity=80)
            )
        # Tension strings
        mid = 60
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            pc = chord.pitch_classes()[i % len(chord.pitch_classes())]
            pitch_s = nearest_pitch(pc, mid)
            notes.append(NoteInfo(pitch=pitch_s, start=round(onset, 6), duration=0.4, velocity=60))

    def _render_pursuit(self, notes, bar_start, total, chord, low):
        """Full combat/driving intensity."""
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        vel = 100
        # Fast bass
        for beat in range(4):
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.4, velocity=vel)
                )
        # Aggressive drums
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            notes.append(NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.2, velocity=vel))
            if beat in (1, 3):
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.2, velocity=vel - 5)
                )
        # Driving strings
        mid = 60
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            pc = chord.pitch_classes()[i % len(chord.pitch_classes())]
            notes.append(
                NoteInfo(
                    pitch=nearest_pitch(pc, mid), start=round(onset, 6), duration=0.3, velocity=75
                )
            )

    def _render_evading(self, notes, bar_start, total, chord, low):
        """Post-pursuit tension — sparser than pursuit, but still tense."""
        pitch = max(low, nearest_pitch(chord.root, low + 6))
        for beat in [0, 2]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=1.5, velocity=55)
                )
        if bar_start < total:
            notes.append(NoteInfo(pitch=KICK, start=round(bar_start, 6), duration=0.3, velocity=65))
        # Tension strings — tremolo
        mid = 60
        pc = chord.pitch_classes()[0]
        for i in range(4):
            onset = bar_start + i
            if onset < total:
                notes.append(
                    NoteInfo(
                        pitch=nearest_pitch(pc, mid),
                        start=round(onset, 6),
                        duration=0.8,
                        velocity=50,
                    )
                )
