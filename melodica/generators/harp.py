# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/harp.py — Concert harp generator.

Arpeggios, rolled chords, glissandi, bisbigliando (rapid alternating fingers),
and enharmonic pedal-aware pitch spelling.

Range: Cb1 (MIDI 24) – G#7 (MIDI 103) — 47 strings, 7 pedals.
Layer: Application / Domain
Style: Classical, cinematic, Celtic, impressionist.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_at


# Harp range: 47 strings from Cb1 to G#7
HARP_LOW = 24   # Cb1 / C1
HARP_HIGH = 103  # G#7

# Pedal positions for standard tuning: C D E F G A B
# Each pedal has 3 positions: flat (-1), natural (0), sharp (+1)

# Common harp glissando scales (pedal settings)
GLISSANDO_SCALES = {
    "diatonic": [0, 2, 4, 5, 7, 9, 11],     # major scale PCs
    "pentatonic": [0, 2, 4, 7, 9],            # pentatonic
    "whole_tone": [0, 2, 4, 6, 8, 10],        # whole tone
    "diminished": [0, 2, 3, 5, 6, 8, 9, 11],  # octatonic
}


@dataclass
class HarpGenerator(PhraseGenerator):
    """
    Concert harp with arpeggios, rolled chords, glissandi, and bisbigliando.

    pattern:
        "arpeggio"     — spread chord tones across range in sequence
        "rolled_chord" — rapid bottom-to-top chord spread
        "glissando"    — sweep across full range
        "bisbigliando" — rapid alternation between two adjacent notes
        " repeated_note" —same string repeated (like a pulse)
        "broken_chord" — broken pattern: root-5th-3rd-root octave

    direction:
        "up", "down", "up_down"

    spread_speed:
        Beats between each note in arpeggio/rolled_chord (default 0.125 = 32nd).
    """

    name: str = "Harp"

    pattern: str = "arpeggio"
    direction: str = "up"
    spread_speed: float = 0.125
    octave_span: int = 3  # how many octaves to spread across
    glissando_scale: str = "diatonic"
    velocity_decay: float = 0.92  # per-note velocity decay in rolls

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "arpeggio",
        direction: str = "up",
        spread_speed: float = 0.125,
        octave_span: int = 3,
        glissando_scale: str = "diatonic",
        velocity_decay: float = 0.92,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.direction = direction
        self.spread_speed = max(0.03125, spread_speed)
        self.octave_span = max(1, min(5, octave_span))
        self.glissando_scale = glissando_scale
        self.velocity_decay = velocity_decay
        # Clamp to harp range
        self.params.key_range_low = max(self.params.key_range_low, HARP_LOW)
        self.params.key_range_high = min(self.params.key_range_high, HARP_HIGH)

    def _build_harp_note(
        self,
        pitch: int,
        onset: float,
        duration: float,
        vel: int,
        key: Scale | None = None,
    ) -> NoteInfo:
        """
        Unified high-fidelity concert harp string pluck builder.
        Implements register-dependent decay curves, hammer/pluck jitter, and string detuning buzz.
        """
        # 1. Pluck timing jitter
        jitter = random.uniform(-0.003, 0.003)
        onset_h = max(0.0, onset + jitter)
        
        # 2. Register-Dependent Resonance Decay (CC 11)
        # Low strings ring long, high strings decay very rapidly
        if pitch < 48:
            decay_time = max(4.0, duration)
            max_decay = 40
        elif pitch < 72:
            decay_time = min(3.0, duration)
            max_decay = 75
        else:
            decay_time = min(1.0, duration)
            max_decay = 105
            
        steps = 8
        cc11_list = []
        for s in range(steps + 1):
            progress = s / steps
            t_rel = progress * decay_time
            val = int(127 - max_decay * (progress ** 0.8))
            cc11_list.append((t_rel, max(0, min(127, val))))
            
        expression = {11: cc11_list}
        
        # 3. High-Velocity Pluck String Detuning Buzz
        if vel >= 95:
            # String impact detuning decressing rapidly in first 80ms
            pb_list = [
                (0.0, 45),
                (0.04, 20),
                (0.08, 0),
            ]
            expression["pitch_bend"] = pb_list
            
        note = NoteInfo(
            pitch=pitch,
            start=round(onset_h, 6),
            duration=round(duration, 6),
            velocity=max(1, min(127, vel)),
        )
        note.expression = expression
        return note

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        dispatch = {
            "arpeggio": self._render_arpeggio,
            "rolled_chord": self._render_rolled_chord,
            "glissando": self._render_glissando,
            "bisbigliando": self._render_bisbigliando,
            "repeated_note": self._render_repeated_note,
            "broken_chord": self._render_broken_chord,
        }
        render_fn = dispatch.get(self.pattern, self._render_arpeggio)
        return render_fn(chords, key, duration_beats)

    def _base_velocity(self) -> int:
        if self.params.velocity_range:
            return (self.params.velocity_range[0] + self.params.velocity_range[1]) // 2
        return int(60 + self.params.density * 25)

    def _expand_chord_to_range(self, pcs: list[int], anchor: int) -> list[int]:
        """Expand chord pitch classes across the harp range."""
        result = []
        for octave in range(self.octave_span):
            for pc in pcs:
                pitch = nearest_pitch(int(pc), anchor + octave * 12)
                if HARP_LOW <= pitch <= HARP_HIGH:
                    result.append(pitch)
        return sorted(set(result))

    # -----------------------------------------------------------------------

    def _render_arpeggio(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        anchor = (HARP_LOW + min(HARP_HIGH, self.params.key_range_high)) // 2
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._base_velocity()

            expanded = self._expand_chord_to_range(pcs, anchor)
            if self.direction == "down":
                expanded = list(reversed(expanded))
            elif self.direction == "up_down":
                expanded = expanded + list(reversed(expanded[:-1]))

            for i, pitch in enumerate(expanded):
                onset = chord.start + i * self.spread_speed
                if onset >= chord.start + chord.duration:
                    break

                note_vel = max(1, min(127, int(vel * (self.velocity_decay ** i))))
                note_vel += random.randint(-3, 3)

                notes.append(self._build_harp_note(
                    pitch=pitch,
                    onset=onset,
                    duration=max(0.1, chord.duration - (onset - chord.start) - 0.05),
                    vel=note_vel,
                    key=key,
                ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_rolled_chord(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        """Fast bottom-to-top chord spread — all notes in <0.5 beats."""
        notes: list[NoteInfo] = []
        anchor = (HARP_LOW + min(HARP_HIGH, self.params.key_range_high)) // 2
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            vel = self._base_velocity()
            expanded = self._expand_chord_to_range(pcs, anchor)
            if self.direction == "down":
                expanded = list(reversed(expanded))

            # Roll speed: fit all notes within 0.3 beats
            roll_speed = min(self.spread_speed, 0.3 / max(len(expanded), 1))

            for i, pitch in enumerate(expanded):
                onset = chord.start + i * roll_speed
                note_vel = max(1, min(127, vel + random.randint(-4, 2)))

                notes.append(self._build_harp_note(
                    pitch=pitch,
                    onset=onset,
                    duration=max(0.15, chord.duration * 0.8),
                    vel=note_vel,
                    key=key,
                ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_glissando(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        """Full-range sweep using a diatonic/whole-tone/pentatonic scale."""
        notes: list[NoteInfo] = []
        scale_pcs = GLISSANDO_SCALES.get(self.glissando_scale, [0, 2, 4, 5, 7, 9, 11])
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            vel = self._base_velocity()
            dur = chord.duration

            # Build glissando pitch list across full range
            start_pitch = HARP_LOW + 12  # start from C2
            end_pitch = min(HARP_HIGH, self.params.key_range_high) - 12

            gliss_pitches = []
            current = start_pitch
            while current <= end_pitch:
                if current % 12 in scale_pcs:
                    gliss_pitches.append(current)
                current += 1

            if self.direction == "down":
                gliss_pitches = list(reversed(gliss_pitches))

            if not gliss_pitches:
                elapsed += chord.duration
                continue

            step = dur / max(len(gliss_pitches), 1)

            for i, pitch in enumerate(gliss_pitches):
                onset = chord.start + i * step
                # Velocity curve: swell in the middle
                t = i / max(len(gliss_pitches) - 1, 1)
                note_vel = int(vel * (0.6 + 0.4 * math.sin(t * math.pi)))
                note_vel = max(1, min(127, note_vel + random.randint(-2, 2)))

                notes.append(self._build_harp_note(
                    pitch=pitch,
                    onset=onset,
                    duration=max(0.04, step * 1.2),
                    vel=note_vel,
                    key=key,
                ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_bisbigliando(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        """Rapid alternation between two adjacent notes — whispering texture."""
        notes: list[NoteInfo] = []
        anchor = (HARP_LOW + min(HARP_HIGH, self.params.key_range_high)) // 2
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            vel = self._base_velocity() - 15  # bisbigliando is quiet
            vel = max(30, vel)

            # Pick two adjacent pitches
            pc_a = pcs[0]
            pc_b = pcs[1] if len(pcs) > 1 else (pcs[0] + 2) % 12
            pitch_a = nearest_pitch(int(pc_a), anchor)
            pitch_b = nearest_pitch(int(pc_b), anchor + 2)

            # Alternate rapidly
            grain = 0.125  # 32nd notes
            t = chord.start
            toggle = False
            while t < chord.start + chord.duration:
                pitch = pitch_a if toggle else pitch_b
                note_vel = max(1, min(127, vel + random.randint(-5, 5)))

                notes.append(self._build_harp_note(
                    pitch=pitch,
                    onset=t,
                    duration=grain * 0.7,
                    vel=note_vel,
                    key=key,
                ))
                toggle = not toggle
                t += grain

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_repeated_note(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        """Pulse on a single string — root note repeated."""
        notes: list[NoteInfo] = []
        anchor = (HARP_LOW + min(HARP_HIGH, self.params.key_range_high)) // 2
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            vel = self._base_velocity()
            pitch = nearest_pitch(int(pcs[0]), anchor)
            pitch = snap_to_scale(pitch, key)
            pitch = max(HARP_LOW, min(HARP_HIGH, pitch))

            interval = max(0.25, 1.0 - self.params.density * 0.75)
            t = chord.start
            while t < chord.start + chord.duration:
                note_vel = max(1, min(127, vel + random.randint(-4, 4)))
                notes.append(self._build_harp_note(
                    pitch=pitch,
                    onset=t,
                    duration=max(0.08, interval * 0.6),
                    vel=note_vel,
                    key=key,
                ))
                t += interval

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_broken_chord(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        """Classic broken chord pattern: root-5th-3rd-octave repeating."""
        notes: list[NoteInfo] = []
        anchor = (HARP_LOW + min(HARP_HIGH, self.params.key_range_high)) // 2
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if len(pcs) < 3:
                elapsed += chord.duration
                continue

            vel = self._base_velocity()
            # Pattern indices: root, fifth, third, octave
            pattern_indices = [0, min(4, len(pcs) - 1), 1, 0]

            t = chord.start
            idx = 0
            while t < chord.start + chord.duration:
                pc_idx = pattern_indices[idx % len(pattern_indices)]
                octave_shift = (idx // len(pattern_indices)) * 12
                pc = pcs[pc_idx % len(pcs)]
                pitch = nearest_pitch(int(pc), anchor + octave_shift)
                pitch = snap_to_scale(pitch, key)
                pitch = max(HARP_LOW, min(HARP_HIGH, pitch))

                note_vel = max(1, min(127, vel + random.randint(-3, 3)))

                notes.append(self._build_harp_note(
                    pitch=pitch,
                    onset=t,
                    duration=max(0.1, self.spread_speed * 3),
                    vel=note_vel,
                    key=key,
                ))
                t += self.spread_speed * 2
                idx += 1

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes
