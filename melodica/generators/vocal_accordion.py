# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/vocal_accordion.py — Vocal and folk accordion generators.
Implements VocalScatGenerator, GregorianChantGenerator, and MusetteAccordionGenerator.
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


class VocalScatGenerator(PhraseGenerator):
    """
    Vocal Scat Generator.
    Produces syncopated jazz swing scat melodies with start pitch scoops (glides).
    """
    name: str = "Jazz Vocal Scat"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        scat_complexity: float = 0.5,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.scat_complexity = max(0.0, min(1.0, scat_complexity))
        self.note_density = note_density
        # Register: F3 (53) to C6 (84)
        self.params.key_range_low = max(53, self.params.key_range_low)
        self.params.key_range_high = min(84, self.params.key_range_high)

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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = mid

        for i, chord in enumerate(chords):
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            # Jazz syncopation: shift offbeat notes slightly
            start_t = chord.start
            is_offbeat = (start_t % 0.5 > 0.05)
            if is_offbeat and self.scat_complexity > 0.3:
                # push/pull timing slightly
                start_t += random.choice([-0.05, 0.05])

            vel = int(72 + random.uniform(-8, 8))
            dur = chord.duration * 0.82

            # Start pitch scoops (gliding up from 1 or 2 semitones below)
            expression = {}
            if random.random() < 0.5:
                bend_range = 2
                scoop_diff = -1 - (1 if random.random() < self.scat_complexity else 0)
                start_bend = int(scoop_diff * (8192.0 / bend_range))
                expression["pitch_bend"] = [(0.0, start_bend), (0.08, 0)]

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(start_t, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="staccato" if is_offbeat else "sustain",
                    expression=expression,
                )
            )

        return sorted(notes, key=lambda x: x.start)

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


class GregorianChantGenerator(PhraseGenerator):
    """
    Gregorian Chant Vocal Generator.
    Produces slow, monophonic medieval liturgical vocal lines
    with CC 91 reverb send and slow CC 11 breath swells.
    """
    name: str = "Gregorian Chant"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        reverb_presence: float = 0.7,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.reverb_presence = max(0.0, min(1.0, reverb_presence))
        self.note_density = note_density
        # Register: G2 (43) to G4 (67)
        self.params.key_range_low = max(43, self.params.key_range_low)
        self.params.key_range_high = min(67, self.params.key_range_high)

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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = mid

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            pc = random.choice(pcs)
            pitch = nearest_pitch(pc, prev_pitch)
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))
            prev_pitch = pitch

            vel = int(64 + random.uniform(-4, 4))
            dur = chord.duration * 0.95

            # Swelling expression (CC 11) and Reverb (CC 91)
            expression = {}
            if self.reverb_presence > 0:
                expression[91] = int(self.reverb_presence * 127)

            expression[11] = [
                (0.0, 30),
                (dur * 0.3, 85),
                (dur * 0.7, 80),
                (dur, 20)
            ]

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation="sustain",
                    expression=expression,
                )
            )

        return sorted(notes, key=lambda x: x.start)

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


class MusetteAccordionGenerator(PhraseGenerator):
    """
    Musette Accordion Generator.
    Produces classic French accordion lines with detuned double-reed beating effect.
    """
    name: str = "Musette Accordion"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        detune_cents: float = 15.0,     # detuning beating depth
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.detune_cents = max(0.0, min(30.0, detune_cents))
        self.note_density = note_density
        # Register: F3 (53) to A6 (93)
        self.params.key_range_low = max(53, self.params.key_range_low)
        self.params.key_range_high = min(93, self.params.key_range_high)

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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_pitch = mid

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            # Voice up to 3 chord tones
            voiced_pitches = []
            for pc in pcs[:3]:
                p = nearest_pitch(pc, mid)
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                voiced_pitches.append(p)
            voiced_pitches = sorted(list(set(voiced_pitches)))

            vel = int(76 + random.uniform(-6, 6))
            dur = chord.duration * 0.92

            for p in voiced_pitches:
                # Double-reed musette detune beating:
                # Trigger two notes, one slightly sharp, one slightly flat
                bend_range = 2
                detune_bend = int(self.detune_cents * 81.92 / bend_range)

                # Sharp Reed note
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(chord.start, 6),
                        duration=round(dur, 6),
                        velocity=vel,
                        articulation="sustain",
                        expression={"pitch_bend": [(0.0, detune_bend)]},
                    )
                )

                # Flat Reed note
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(chord.start + 0.006, 6),  # tiny delay
                        duration=round(dur, 6),
                        velocity=max(1, vel - 6),
                        articulation="sustain",
                        expression={"pitch_bend": [(0.0, -detune_bend)]},
                    )
                )

        return sorted(notes, key=lambda x: x.start)

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
