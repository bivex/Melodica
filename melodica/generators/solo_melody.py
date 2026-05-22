# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/solo_melody.py — Expressive Solo Melody Generator.

Layer: Application / Domain
Style: Improvised virtuoso solos (Shred Guitar, Jazz Fusion, Space Synth, Blues Lick).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale

SOLO_STYLES = {"shred_guitar", "jazz_fusion", "space_synth", "blues_lick"}


@dataclass
class SoloMelodyGenerator(PhraseGenerator):
    """
    Expressive Solo Melody Generator.
    Simulates a live musician improvising high-fidelity solos.
    """

    name: str = "Solo Melody"
    style: str = "blues_lick"
    vibrato_depth: float = 0.5
    blues_notes: bool = True
    chromaticism: float = 0.4
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "blues_lick",
        vibrato_depth: float = 0.5,
        blues_notes: bool = True,
        chromaticism: float = 0.4,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if style not in SOLO_STYLES:
            raise ValueError(f"style must be one of {SOLO_STYLES}; got {style!r}")
        self.style = style
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        self.blues_notes = blues_notes
        self.chromaticism = max(0.0, min(1.0, chromaticism))
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

        # 1. Build rhythmic solo events
        events = self._build_events(duration_beats)
        if not events:
            return []

        notes: list[NoteInfo] = []
        low = max(48, self.params.key_range_low)
        high = min(88, self.params.key_range_high)
        mid = (low + high) // 2

        prev_pitch = (
            context.prev_pitch
            if context and context.prev_pitch is not None
            else mid
        )
        last_chord: ChordLabel | None = None

        for idx, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            root_pc = chord.root
            pcs = chord.pitch_classes()
            
            pitch = prev_pitch
            expression: dict[int, int] = {}
            articulation = "sustain"
            dur = event.duration

            # ---------------------------------------------------------------
            # Pitch Selection Algorithms per Style
            # ---------------------------------------------------------------
            if self.style == "blues_lick":
                # minor pentatonic + blues flatted 5th
                # Blues scale intervals: 0, 3, 5, 6, 7, 10
                blues_steps = [0, 3, 5, 6, 7, 10]
                if not self.blues_notes:
                    blues_steps = [0, 3, 5, 7, 10]  # pure minor pentatonic
                
                selected_step = random.choice(blues_steps)
                target_pitch = root_pc + selected_step
                
                # Check for enclosure: approach target pitch by a half-step
                is_enclosure = random.random() < self.chromaticism and idx > 0
                if is_enclosure:
                    offset = 1 if random.random() < 0.5 else -1
                    pitch = nearest_pitch(target_pitch + offset, prev_pitch)
                    articulation = "staccato"
                else:
                    pitch = nearest_pitch(target_pitch, prev_pitch)
                
                # Expressive mod wheel (vibrato) on sustained notes
                if dur > 0.6:
                    expression = {1: int(40 + 50 * self.vibrato_depth)}

            elif self.style == "shred_guitar":
                # Fast linear scalar runs and sweeps
                is_fast_run = (event.duration < 0.25)
                if is_fast_run:
                    # step-wise scale motion (mostly minor second or major second)
                    step = random.choice([-2, -1, 1, 2])
                    pitch = prev_pitch + step
                else:
                    # outline chord tones or large leaps
                    leap_pc = random.choice(pcs) if pcs else root_pc
                    pitch = nearest_pitch(leap_pc, prev_pitch + 12)
                
                # Extreme pitch bending simulation via CC 74 cutoff filter
                if not is_fast_run:
                    expression = {74: 105, 1: int(60 * self.vibrato_depth)}
                    articulation = "accent"
                else:
                    articulation = "legato"

            elif self.style == "jazz_fusion":
                # Triplet bebop chromatic enclosures and wide intervals
                is_enclosure = (idx % 3 == 0) and idx > 0
                if is_enclosure:
                    # Enclose the target chord tone (Root or 5th) by playing 1 semitone above, then below
                    target_tone = root_pc
                    if random.random() < 0.5 and len(pcs) > 2:
                        target_tone = pcs[2]  # fifth
                    pitch = nearest_pitch(target_tone + 1, prev_pitch)
                    articulation = "legato"
                else:
                    # outline chord degrees
                    chord_tone = random.choice(pcs) if pcs else root_pc
                    pitch = nearest_pitch(chord_tone, prev_pitch)
                
                pitch = max(low - 6, min(high + 6, pitch))

            elif self.style == "space_synth":
                # Lyrical, sweeping, massive filter opens
                # Slower vocal-like movements
                pitch = nearest_pitch(root_pc, prev_pitch)
                # occasional fifth/seventh leap
                if random.random() < 0.4 and len(pcs) > 1:
                    pitch = nearest_pitch(pcs[-1], prev_pitch)
                
                # Continuous CC 74 sweeping filter
                lfo_val = int(55 + 40 * math.sin(event.onset * 1.5))
                expression = {74: lfo_val}
                if dur > 1.0:
                    expression[1] = int(50 + 40 * self.vibrato_depth)  # massive vibrato

            # Clamp and snap to scale bounds
            pitch = snap_to_scale(pitch, key)
            pitch = max(low, min(high, pitch))

            # Dynamic velocity mapping
            vel = 72
            if articulation == "accent":
                vel = 110
            elif articulation == "legato":
                vel = 65
            elif articulation == "staccato":
                vel = 48
            else:
                vel = 80

            # Subtle random humanization variation
            vel += random.randint(-6, 6)
            vel = max(1, min(127, vel))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation=articulation,
                    expression=expression,
                )
            )
            prev_pitch = pitch

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

        if self.style == "blues_lick":
            # Syncopated blues rhythm: mix of eighths, triplets, dotted notes, and rests
            while t < duration_beats:
                bar_offset = t % 4.0
                if bar_offset == 0.0:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.45, velocity_factor=0.8))
                    t += 1.0
                elif bar_offset == 1.0:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.9, velocity_factor=1.1))
                    t += 1.0
                elif bar_offset == 2.0:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.45, velocity_factor=0.8))
                    t += 1.0
                else:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.3, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.33, 6), duration=0.3, velocity_factor=0.85))
                    events.append(RhythmEvent(onset=round(t + 0.66, 6), duration=0.3, velocity_factor=0.9))
                    t += 1.0

        elif self.style == "shred_guitar":
            # Rapid 16th/24th bursts with dramatic rests
            while t < duration_beats:
                # Trigger shred run on beat 1 & 3 of bars
                run_offsets = [0.0, 0.166, 0.33, 0.5, 0.66, 0.83, 1.0, 1.25, 1.5, 1.75]
                for off in run_offsets:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.15, velocity_factor=1.0))
                # Add a long soaring note at the end of the run
                onset = t + 2.0
                if onset < duration_beats:
                    events.append(RhythmEvent(onset=round(onset, 6), duration=1.7, velocity_factor=1.1))
                t += 4.0

        elif self.style == "jazz_fusion":
            # Angular swing eighths and syncopated rests
            while t < duration_beats:
                for off in [0.0, 0.33, 0.66, 1.0, 1.5, 1.83, 2.0, 2.5, 2.83, 3.0]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.25, velocity_factor=1.0))
                t += 4.0

        elif self.style == "space_synth":
            # Long whole note drones mixed with syncopated offbeats
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=2.2, velocity_factor=1.0))
                # syncopated 16th plucks on offbeats
                events.append(RhythmEvent(onset=round(t + 2.5, 6), duration=0.3, velocity_factor=0.85))
                events.append(RhythmEvent(onset=round(t + 3.25, 6), duration=0.3, velocity_factor=0.9))
                t += 4.0

        return events
