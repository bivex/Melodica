# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22 19:15
# Last Updated: 2026-05-22 19:15
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/modern_bass_2025.py — Modern 2025 bass generator.

Layer: Application / Domain
Style: Neo Soul, Velvet Bass, Hybrid Slap, Analog Pluck, Crescendo Return.

Implements the cutting edge sound design and performance trends of 2025 basslines
with mathematically controlled velocity pocketing and automated controller sweeps.
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


MODERN_STYLES = {"velvet_soul", "hybrid_slap", "analog_pluck", "crescendo_return"}


@dataclass
class ModernBass2025Generator(PhraseGenerator):
    """
    Modern 2025 Bass Generator.

    style:
        "velvet_soul"       — Warm pocket fingerstyle/walking bass (avg 63, max 84).
        "hybrid_slap"       — Syncopated future funk / alt-R&B slap with heavy ghost notes (avg 59, max 91-93).
        "analog_pluck"      — Saw + sine layered tight pluck with short decay (avg 63, max 84).
        "crescendo_return"  — Cinematic bass returns and filter-opening swells (starts 31, ends 68+).
    """

    name: str = "Modern Bass 2025"
    style: str = "velvet_soul"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "velvet_soul",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if style not in MODERN_STYLES:
            raise ValueError(f"style must be one of {MODERN_STYLES}; got {style!r}")
        self.style = style
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

        # 1. Build rhythmic onset events
        events = self._build_events(duration_beats)
        if not events:
            return []

        notes: list[NoteInfo] = []
        low = max(24, self.params.key_range_low)
        mid = low + 12
        high_bound = self.params.key_range_high

        prev_pitch = (
            context.prev_pitch
            if context and context.prev_pitch is not None
            else low + 12
        )
        last_chord: ChordLabel | None = None

        # Determine target metrics based on style
        target_avg = 63.0
        target_max = 84.0
        if self.style == "hybrid_slap":
            target_avg = 59.0
            target_max = 92.0
        elif self.style == "analog_pluck":
            target_avg = 63.0
            target_max = 84.0

        for idx, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            root_pc = chord.root
            pcs = chord.pitch_classes()

            # Determine Note Role / Pitch / Articulation
            articulation: str | None = None
            expression: dict[int, int] = {}
            dur = event.duration

            if self.style == "velvet_soul":
                # Velvet Soul: warm walking or smooth syncopation
                # Prefers chord tones (root, 3rd, 5th, 7th) with smooth legato voice leading
                beat_in_chord = int(round(event.onset - chord.start))
                is_downbeat = beat_in_chord % 2 == 0

                if is_downbeat:
                    pitch_candidates = [root_pc]
                else:
                    # Select color tones (3rd, 5th, 7th)
                    pitch_candidates = [
                        pc for pc in pcs if pc != root_pc
                    ] or [root_pc]
                
                selected_pc = random.choice(pitch_candidates)
                pitch = nearest_pitch(selected_pc, prev_pitch)
                
                # Keep within warm bass register (MIDI 36 to 55)
                pitch = max(36, min(55, pitch))
                pitch = snap_to_scale(pitch, key)
                articulation = "sustain"
                # Soft tape saturation feel: simulated via subtle pitch class variation or CC 74 (closed filter)
                expression = {74: 65}  # Warm, low-passed character

            elif self.style == "hybrid_slap":
                # Hybrid Slap: S (Slap), P (Pop), G (Ghost), - (Rest)
                # Pattern repeats every 4 beats
                beat_offset = event.onset % 4.0
                
                # Assign role based on 16th note subdivisions
                if beat_offset < 0.1:
                    role = "S"
                elif abs(beat_offset - 0.25) < 0.1:
                    role = "G"
                elif abs(beat_offset - 0.5) < 0.1:
                    role = "P"
                elif abs(beat_offset - 0.75) < 0.1:
                    role = "G"
                elif abs(beat_offset - 1.0) < 0.1:
                    role = "S"
                elif abs(beat_offset - 1.5) < 0.1:
                    role = "P"
                elif abs(beat_offset - 2.0) < 0.1:
                    role = "S"
                elif abs(beat_offset - 2.25) < 0.1:
                    role = "G"
                elif abs(beat_offset - 2.5) < 0.1:
                    role = "P"
                elif abs(beat_offset - 3.0) < 0.1:
                    role = "S"
                elif abs(beat_offset - 3.25) < 0.1:
                    role = "G"
                else:
                    role = "G"

                if role == "S":
                    # Slap: low-register roots or fifths
                    pitch = nearest_pitch(root_pc, low + 12)
                    pitch = max(low, min(low + 12, pitch))
                    articulation = "slap"
                    dur = event.duration * 0.75
                    expression = {74: 70}  # Moderately bright slap transient
                elif role == "P":
                    # Pop: mid-high register octaves or dominant color tones
                    pop_candidates = [
                        int(pc) for pc in pcs if (int(pc) - int(root_pc)) % 12 in (3, 4, 7)
                    ] or [int(root_pc)]
                    selected_pc = random.choice(pop_candidates)
                    # Pop at least an octave higher
                    pitch = nearest_pitch(selected_pc, prev_pitch + 12)
                    pitch = max(low + 12, min(low + 28, pitch))
                    articulation = "pop"
                    dur = event.duration * 0.5
                    expression = {74: 105}  # Pop click attack in 1-2 kHz (simulated by open LPF)
                else:
                    # Ghost note: muted, soft, rhythmic percussive notes
                    pitch = nearest_pitch(root_pc, prev_pitch)
                    pitch = max(low, min(low + 12, pitch))
                    articulation = "staccato"
                    dur = event.duration * 0.25
                    expression = {74: 40}  # Soft, muted frequency spectrum

                pitch = snap_to_scale(pitch, key)

            elif self.style == "analog_pluck":
                # Analog Pluck: Saw + sine layered short-decay pluck
                pitch_candidates = [root_pc]
                if len(pcs) > 1 and random.random() < 0.4:
                    pitch_candidates.append(pcs[1])  # fifth or third for color
                selected_pc = random.choice(pitch_candidates)
                pitch = nearest_pitch(selected_pc, prev_pitch)
                # Keep in classic synth-bass register (MIDI 36 to 48)
                pitch = max(36, min(48, pitch))
                pitch = snap_to_scale(pitch, key)
                articulation = "staccato"
                dur = 0.15  # Extremely short decay
                expression = {74: 75, 1: 30}  # Fast pluck contour, moderate saturation harmonics

            else:
                # crescendo_return: Cinematic bass swells starting at 31, rising to 68+
                pitch = nearest_pitch(root_pc, low + 12)
                pitch = max(low, min(low + 12, pitch))
                pitch = snap_to_scale(pitch, key)
                articulation = "sustain"
                
                # Progress fraction through the total duration
                progress = event.onset / max(1.0, duration_beats)
                
                # Sweep LPF (CC 74) from closed (30) to wide open (100) to emulate widening harmonics
                expression = {74: int(30 + progress * 70)}

            pitch = max(self.params.key_range_low, min(high_bound, pitch))

            # Temporary raw velocity (will be normalized below to guarantee target mean and max)
            raw_vel = 64
            if self.style == "velvet_soul":
                # Base velocity with small accent variation
                raw_vel = 70 if articulation == "sustain" else 60
            elif self.style == "hybrid_slap":
                if articulation == "slap":
                    raw_vel = 100
                elif articulation == "pop":
                    raw_vel = 120
                else:
                    raw_vel = 35
            elif self.style == "analog_pluck":
                raw_vel = 75 if random.random() < 0.3 else 60
            else:
                # Crescendo: starts at 31, rises to 68
                progress = event.onset / max(1.0, duration_beats)
                raw_vel = int(31 + progress * (68 - 31))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(dur, 6),
                    velocity=raw_vel,
                    articulation=articulation,
                    expression=expression,
                )
            )
            prev_pitch = pitch

        # 2. Velocity target post-processing
        # This mathematical layer guarantees that we match the user's pocket stats precisely.
        if self.style in ("velvet_soul", "hybrid_slap", "analog_pluck") and len(notes) > 1:
            raw_velocities = [n.velocity for n in notes]
            min_raw = min(raw_velocities)
            max_raw = max(raw_velocities)
            mean_raw = sum(raw_velocities) / len(raw_velocities)

            # Apply scale-and-shift transform: V'_i = a * V_i + b
            # We want: max(V') = target_max, mean(V') = target_avg
            # We also ensure b is non-negative and velocities stay within [1, 127]
            divisor = (max_raw - mean_raw)
            if divisor != 0:
                a = (target_max - target_avg) / divisor
                b = target_avg - a * mean_raw
            else:
                a = 1.0
                b = target_avg - mean_raw

            # If the calculated scale is too extreme, fall back to simple offset
            if a < 0.1 or a > 5.0:
                offset = target_avg - mean_raw
                for n in notes:
                    n.velocity = max(1, min(MIDI_MAX, int(round(n.velocity + offset))))
            else:
                for n in notes:
                    new_vel = int(round(a * n.velocity + b))
                    n.velocity = max(1, min(MIDI_MAX, new_vel))

            # Fine-tune the sum of velocities to match target_sum exactly
            target_sum = int(round(target_avg * len(notes)))
            
            # Ensure no note exceeds target_max
            for n in notes:
                n.velocity = min(int(target_max), max(1, n.velocity))

            # Make sure at least one note is exactly at target_max
            max_note = max(notes, key=lambda n: n.velocity)
            max_note.velocity = int(target_max)

            # Adjust the rest of the notes to hit the exact target_sum
            for _ in range(100):
                current_sum = sum(n.velocity for n in notes)
                diff = target_sum - current_sum
                if diff == 0:
                    break
                
                step = 1 if diff > 0 else -1
                candidates = []
                for n in notes:
                    if step == 1:
                        if n.velocity < int(target_max):
                            candidates.append(n)
                    else:
                        if n.velocity > 1:
                            # Keep at least one note at target_max
                            if n.velocity == int(target_max) and sum(1 for x in notes if x.velocity == int(target_max)) <= 1:
                                continue
                            candidates.append(n)
                
                if not candidates:
                    break
                
                # Distribute the difference
                random.shuffle(candidates)
                num_to_change = min(abs(diff), len(candidates))
                for i in range(num_to_change):
                    candidates[i].velocity += step

        elif self.style == "crescendo_return" and notes:
            # For crescendo, guarantee start velocity is exactly 31 and peak is exactly 68
            if len(notes) == 1:
                notes[0].velocity = 68
            else:
                for idx, n in enumerate(notes):
                    progress = idx / (len(notes) - 1)
                    n.velocity = int(round(31 + progress * (68 - 31)))

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        events: list[RhythmEvent] = []
        t = 0.0

        if self.style == "velvet_soul":
            # Walking quarter notes interspersed with syncopated eighths
            while t < duration_beats:
                bar_beat = t % 4.0
                if bar_beat in (1.0, 3.0):
                    # Eighth-note division
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.45, velocity_factor=0.85))
                else:
                    # Quarter-note division
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.9, velocity_factor=1.0))
                t += 1.0

        elif self.style == "hybrid_slap":
            # 16th note syncopated grid
            while t < duration_beats:
                for off in [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.25, 2.5, 3.0, 3.25]:
                    onset = t + off
                    if onset < duration_beats:
                        # Emphasize downbeats
                        vel_factor = 1.0 if off in (0.0, 1.0, 2.0, 3.0) else 0.8
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.2, velocity_factor=vel_factor))
                t += 4.0

        elif self.style == "analog_pluck":
            # Tight 16th note pluck groove
            while t < duration_beats:
                for off in [0.0, 0.25, 0.75, 1.0, 1.5, 1.75, 2.0, 2.5, 2.75, 3.25]:
                    onset = t + off
                    if onset < duration_beats:
                        vel_factor = 1.0 if off in (0.0, 2.0) else 0.85
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.15, velocity_factor=vel_factor))
                t += 4.0

        else:  # crescendo_return
            # Pulsing 8th notes to smooth out the swell
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                t += 0.5

        return events
