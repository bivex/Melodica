# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/chromatic_percussion.py — Chromatic and Mallet Percussion instruments.
Implements dedicated, highly professional generators for Celesta (8), Glockenspiel (9),
Music Box (10), Vibraphone (11), Marimba (12), Xylophone (13), and Dulcimer (15).
"""

from __future__ import annotations

import random
import math
from abc import ABC, abstractmethod

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class _ChromaticPercussionBase(PhraseGenerator, ABC):
    """Abstract base class for chromatic and mallet percussion generators."""

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.note_density = note_density

    def _apply_note_density(self, chords: list[ChordLabel]) -> list[ChordLabel]:
        note_density = getattr(self, "note_density", 1.0)
        if not chords or note_density == 1.0:
            return chords
        
        if note_density <= 0.0:
            return []
        
        if note_density < 1.0:
            new_chords = []
            for i, chord in enumerate(chords):
                prev_val = int((i - 1) * note_density) if i > 0 else -1
                curr_val = int(i * note_density)
                if curr_val > prev_val:
                    new_chords.append(chord)
            return new_chords
        
        subdivisions = max(1, round(note_density))
        if subdivisions <= 1:
            return chords
            
        import dataclasses
        new_chords = []
        for chord in chords:
            sub_dur = chord.duration / subdivisions
            for s in range(subdivisions):
                new_chord = dataclasses.replace(
                    chord,
                    start=chord.start + s * sub_dur,
                    duration=sub_dur
                )
                new_chords.append(new_chord)
        return new_chords

    def _velocity(self, base_val: int) -> int:
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            return random.randint(v_min, v_max)
        return max(1, min(127, base_val + random.randint(-8, 8)))

    def _resolve_pitch(self, pc: int, anchor: int, key: Scale, low: int, high: int) -> int:
        pitch = nearest_pitch(int(pc), anchor)
        pitch = snap_to_scale(pitch, key)
        return max(low, min(high, pitch))


class CelestaGenerator(_ChromaticPercussionBase):
    """
    Celesta Generator (GM program 8).
    Creates dreamy, bell-like, pearly high-register arpeggios or sparkling bell chords.
    """
    name: str = "Celesta Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "dreamy_arpeggio",  # dreamy_arpeggio, sparkling_chords
        pedal: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern
        self.pedal = pedal

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(60, self.params.key_range_low)
        high = min(108, self.params.key_range_high)
        mid = (low + high) // 2

        dur_mult = 1.6 if self.pedal else 0.8

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "dreamy_arpeggio" and len(pcs) >= 2:
                # Flowing ascending pearly run
                sub_dur = chord.duration / len(pcs)
                for i, pc in enumerate(pcs):
                    pitch = self._resolve_pitch(pc, mid + (i - len(pcs)//2)*4, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + i * sub_dur, 6),
                        duration=round(max(0.1, sub_dur * dur_mult), 6),
                        velocity=self._velocity(72),
                    ))
            else:
                # Sparkling chords (plays up to 3 chord tones at high registers)
                for pc in pcs[:3]:
                    pitch = self._resolve_pitch(pc, mid + 12, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start, 6),
                        duration=round(max(0.1, chord.duration * dur_mult), 6),
                        velocity=self._velocity(75),
                    ))

        return sorted(notes, key=lambda x: x.start)


class GlockenspielGenerator(_ChromaticPercussionBase):
    """
    Glockenspiel Generator (GM program 9).
    Renders extremely bright, high-pitched ringing bells, simple melodies, or sparkling runs.
    """
    name: str = "Glockenspiel Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "melodic_accent",  # melodic_accent, sparkling_run
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(72, self.params.key_range_low)
        high = min(108, self.params.key_range_high)
        mid = (low + high) // 2

        prev_pitch = mid + 12

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "sparkling_run" and len(pcs) >= 3:
                # Fast high-pitched run
                sub_dur = chord.duration / 4.0
                for s in range(4):
                    pc = pcs[s % len(pcs)]
                    pitch = self._resolve_pitch(pc, mid + 12 + s * 2, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=0.3,
                        velocity=self._velocity(76),
                    ))
            else:
                # Sparse ringing melodic accent on the first chord tone
                pc = pcs[0]
                pitch = self._resolve_pitch(pc, prev_pitch, key, low, high)
                prev_pitch = pitch
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.6,
                    velocity=self._velocity(82),
                ))

        return sorted(notes, key=lambda x: x.start)


class MusicBoxGenerator(_ChromaticPercussionBase):
    """
    Music Box Generator (GM program 10).
    Renders clockwork mechanical ostinatos, slightly vintage, highly structured.
    """
    name: str = "Music Box Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "clockwork_ostinato",  # clockwork_ostinato, gentle_melody
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(60, self.params.key_range_low)
        high = min(88, self.params.key_range_high)
        mid = (low + high) // 2

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "clockwork_ostinato":
                # Continuous, rigid mechanical arpeggio (e.g. 1 & 2 & 3 & 4 &)
                sub_dur = 0.5  # eighth notes
                steps = max(1, int(chord.duration / sub_dur))
                for s in range(steps):
                    pc = pcs[s % len(pcs)]
                    octave = (s // len(pcs)) * 12
                    pitch = self._resolve_pitch(pc, mid + octave, key, low, high)
                    
                    # High mechanical precision: strict velocity, tiny release decay
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=0.35,
                        velocity=self._velocity(68),
                    ))
            else:
                # Gentle high melody
                pc = random.choice(pcs)
                pitch = self._resolve_pitch(pc, mid + 6, key, low, high)
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=0.4,
                    velocity=self._velocity(72),
                ))

        return sorted(notes, key=lambda x: x.start)


class VibraphoneGenerator(_ChromaticPercussionBase):
    """
    Vibraphone Generator (GM program 11).
    Creates warm chords (up to 4 mallets), sustain pedaling, and motor vibrato sweeps.
    """
    name: str = "Vibraphone Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "warm_chords",  # warm_chords, motor_arpeggio
        motor_speed_hz: float = 6.0,  # motor tremolo speed
        pedal: bool = True,           # sustain pedaling (CC 64)
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern
        self.motor_speed_hz = motor_speed_hz
        self.pedal = pedal

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(53, self.params.key_range_low)
        high = min(89, self.params.key_range_high)
        mid = (low + high) // 2

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "warm_chords":
                # Lush sustained chords, up to 4 mallet voices
                for idx, pc in enumerate(pcs[:4]):
                    pitch = self._resolve_pitch(pc, mid, key, low, high)
                    duration = chord.duration * 0.95
                    
                    # Generate dynamic LFO expression sweeps (simulates spinning motor disc tremolo)
                    expression = {}
                    step = 0.05
                    expr_points = []
                    t = 0.0
                    while t < duration:
                        # 6Hz LFO sweep on CC 11
                        lfo_val = int(85 + 15 * math.sin(t * self.motor_speed_hz * 2.0 * math.pi))
                        expr_points.append((t, lfo_val))
                        t += step
                    if expr_points:
                        expression[11] = expr_points

                    # If pedal is enabled, inject sustain pedal CC 64 messages
                    if self.pedal:
                        # Send pedal release and re-press at start of chord to clear resonance
                        expression[64] = [(0.0, 0), (0.04, 127)]

                    note = NoteInfo(
                        pitch=pitch,
                        start=round(chord.start, 6),
                        duration=round(duration, 6),
                        velocity=self._velocity(70),
                    )
                    if expression:
                        note.expression = expression
                    notes.append(note)
            else:
                # Motor-driven arpeggiating run
                sub_dur = chord.duration / 3.0
                for s in range(3):
                    pc = pcs[s % len(pcs)]
                    pitch = self._resolve_pitch(pc, mid, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=round(sub_dur * 1.5, 6),
                        velocity=self._velocity(74),
                    ))

        return sorted(notes, key=lambda x: x.start)


class MarimbaGenerator(_ChromaticPercussionBase):
    """
    Marimba Generator (GM program 12).
    Generates warm woody arpeggios, double strokes, or continuous rolling tremolos.
    """
    name: str = "Marimba Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "woody_arpeggio",  # woody_arpeggio, rolling_tremolo
        mallets: int = 4,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern
        self.mallets = max(2, min(4, mallets))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(45, self.params.key_range_low)
        high = min(84, self.params.key_range_high)
        mid = (low + high) // 2

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "rolling_tremolo":
                # Continuous high-speed tremolo rolls
                roll_speed = 0.125  # 32nd note rolls
                steps = max(1, int(chord.duration / roll_speed))
                for s in range(steps):
                    pc = pcs[s % min(len(pcs), 2)]  # Roll on root/third
                    pitch = self._resolve_pitch(pc, mid, key, low, high)
                    
                    # Beautiful sinusoidal volume shape on the roll
                    t_frac = s / max(1, steps - 1)
                    swell = int(math.sin(t_frac * math.pi) * 12)
                    
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * roll_speed, 6),
                        duration=roll_speed * 0.95,
                        velocity=max(1, min(127, self._velocity(60) + swell)),
                    ))
            else:
                # Woody chordal arpeggiating blocks (up to active mallet count)
                sub_dur = chord.duration / self.mallets
                for s in range(self.mallets):
                    pc = pcs[s % len(pcs)]
                    pitch = self._resolve_pitch(pc, mid - 6 + s * 4, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=0.22,  # Dry woody decay
                        velocity=self._velocity(68),
                    ))

        return sorted(notes, key=lambda x: x.start)


class XylophoneGenerator(_ChromaticPercussionBase):
    """
    Xylophone Generator (GM program 13).
    Renders sharp, bright, dry staccato lines, rapid runs, or dry skeletal wood accents.
    """
    name: str = "Xylophone Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "dry_staccato_run",  # dry_staccato_run, skeletal_accents
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(65, self.params.key_range_low)
        high = min(96, self.params.key_range_high)
        mid = (low + high) // 2

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "dry_staccato_run":
                # Rapid 16th note dry wood runs
                sub_dur = 0.25
                steps = max(1, int(chord.duration / sub_dur))
                for s in range(steps):
                    pc = pcs[s % len(pcs)]
                    pitch = self._resolve_pitch(pc, mid + (s % 3) * 3, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=0.12,  # Extremely short staccato
                        velocity=self._velocity(84),
                    ))
            else:
                # Dry skeletal accent hits on root/fifth
                for i, pc in enumerate(pcs[:2]):
                    pitch = self._resolve_pitch(pc, mid + i * 7, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start, 6),
                        duration=0.15,
                        velocity=self._velocity(90),
                    ))

        return sorted(notes, key=lambda x: x.start)


class DulcimerGenerator(_ChromaticPercussionBase):
    """
    Hammered Dulcimer Generator (GM program 15).
    Struck wire strings with hand-held mallets. Creates rapid rolls, ringing percussive arpeggios.
    """
    name: str = "Hammered Dulcimer Generator"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "rapid_arpeggio",  # rapid_arpeggio, hammered_roll
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params, note_density=note_density)
        self.pattern = pattern

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        low = max(48, self.params.key_range_low)
        high = min(84, self.params.key_range_high)
        mid = (low + high) // 2

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.pattern == "hammered_roll":
                # High speed hammer bounce effect
                bounce_speed = 0.125
                steps = max(1, int(chord.duration / bounce_speed))
                for s in range(steps):
                    pc = pcs[s % len(pcs)]
                    pitch = self._resolve_pitch(pc, mid, key, low, high)
                    # Tremolo volume shapes
                    vel_mod = 12 if s % 2 == 0 else -12
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * bounce_speed, 6),
                        duration=0.25,  # ringing sustain
                        velocity=max(1, min(127, self._velocity(72) + vel_mod)),
                    ))
            else:
                # Ringing arpeggios
                sub_dur = chord.duration / 3.0
                for s in range(3):
                    pc = pcs[s % len(pcs)]
                    pitch = self._resolve_pitch(pc, mid + 6, key, low, high)
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(chord.start + s * sub_dur, 6),
                        duration=round(sub_dur * 1.6, 6),  # beautiful ringing sustain overlap
                        velocity=self._velocity(76),
                    ))

        return sorted(notes, key=lambda x: x.start)
