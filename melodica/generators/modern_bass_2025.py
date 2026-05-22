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
generators/modern_bass_2025.py — Advanced Modern 2025 bass generator.

Layer: Application / Domain
Style: 20 specialized cutting edge modern styles.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale, compute_simplicity


MODERN_STYLES = {
    "walking", "slap", "pop", "ghost_note", "synth", 
    "saw", "sub", "hybrid_slap", "fingerstyle", "adaptive",
    "procedural", "generative", "euclidean", "spectral_morphing",
    "sidechain_reactive", "self_modifying", "cinematic", "tape",
    "harmonic", "envelope"
}


# ---------------------------------------------------------------------------
# Euclidean Rhythm Helper (Bjorklund Algorithm)
# ---------------------------------------------------------------------------
def generate_euclidean(pulses: int, steps: int) -> list[int]:
    """Bjorklund's algorithm to distribute pulses evenly across steps."""
    if pulses <= 0:
        return [0] * steps
    if pulses >= steps:
        return [1] * steps

    pattern = [[1] for _ in range(pulses)] + [[0] for _ in range(steps - pulses)]
    while len(pattern) > 1 and len(pattern[0]) > 0:
        # Find index of last element that is different
        last_val = pattern[-1]
        matching_count = sum(1 for p in pattern if p == last_val)
        non_matching_count = len(pattern) - matching_count
        
        if matching_count == 0 or non_matching_count == 0:
            break
            
        move_count = min(non_matching_count, matching_count)
        for i in range(move_count):
            pattern[i].extend(pattern.pop())
            
    # Flatten the result
    flat = []
    for p in pattern:
        flat.extend(p)
    return flat


@dataclass
class ModernBass2025Generator(PhraseGenerator):
    """
    Modern Bass 2025 Generator with 20 premium styles:
    """

    name: str = "Modern Bass 2025"
    style: str = "walking"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "walking",
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

        # 1. Build rhythmic events
        events = self._build_events(duration_beats, chords)
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

        # Style-specific velocity target presets
        target_avg = 63.0
        target_max = 84.0
        
        if self.style == "walking":
            target_avg, target_max = 68.0, 88.0
        elif self.style == "slap":
            target_avg, target_max = 64.0, 95.0
        elif self.style == "pop":
            target_avg, target_max = 68.0, 90.0
        elif self.style == "ghost_note":
            target_avg, target_max = 42.0, 75.0
        elif self.style == "synth":
            target_avg, target_max = 64.0, 85.0
        elif self.style == "saw":
            target_avg, target_max = 75.0, 98.0
        elif self.style == "sub":
            target_avg, target_max = 58.0, 78.0
        elif self.style == "hybrid_slap":
            target_avg, target_max = 59.0, 92.0
        elif self.style == "fingerstyle":
            target_avg, target_max = 63.0, 84.0
        elif self.style == "adaptive":
            target_avg, target_max = 65.0, 88.0
        elif self.style == "procedural":
            target_avg, target_max = 63.0, 85.0
        elif self.style == "generative":
            target_avg, target_max = 64.0, 86.0
        elif self.style == "euclidean":
            target_avg, target_max = 65.0, 88.0
        elif self.style == "spectral_morphing":
            target_avg, target_max = 63.0, 84.0
        elif self.style == "sidechain_reactive":
            target_avg, target_max = 60.0, 84.0
        elif self.style == "self_modifying":
            target_avg, target_max = 66.0, 90.0
        elif self.style == "cinematic":
            target_avg, target_max = 60.0, 82.0
        elif self.style == "tape":
            target_avg, target_max = 62.0, 82.0
        elif self.style == "harmonic":
            target_avg, target_max = 68.0, 92.0
        elif self.style == "envelope":
            target_avg, target_max = 63.0, 85.0

        for idx, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            root_pc = chord.root
            pcs = chord.pitch_classes()
            
            articulation: str | None = None
            expression: dict[int, int] = {}
            dur = event.duration
            pitch = low + 12

            # ---------------------------------------------------------------
            # Pitch & Articulation Logic per Style
            # ---------------------------------------------------------------
            if self.style == "walking":
                # Jazz walking: connect chord roots stepwise
                beat_in_chord = int(round(event.onset - chord.start))
                is_downbeat = beat_in_chord % 2 == 0
                if is_downbeat:
                    pitch = nearest_pitch(root_pc, prev_pitch)
                else:
                    color_pcs = [pc for pc in pcs if pc != root_pc] or [root_pc]
                    pitch = nearest_pitch(random.choice(color_pcs), prev_pitch)
                pitch = max(36, min(55, pitch))
                articulation = "sustain"
                expression = {74: 60}  # Warm acoustic tone

            elif self.style == "slap":
                # Old school funk slap: hard slaps vs pops
                is_pop = (event.onset % 1.0) >= 0.4
                if is_pop:
                    pop_pc = pcs[1] if len(pcs) > 1 else root_pc
                    pitch = nearest_pitch(pop_pc, prev_pitch + 12)
                    pitch = max(low + 12, min(low + 24, pitch))
                    articulation = "pop"
                    dur = event.duration * 0.45
                    expression = {74: 100}
                else:
                    pitch = nearest_pitch(root_pc, low + 6)
                    pitch = max(low, min(low + 12, pitch))
                    articulation = "slap"
                    dur = event.duration * 0.7
                    expression = {74: 75}

            elif self.style == "pop":
                # Pure pop: solid eighth note octave groove
                is_octave = (event.onset % 1.0) >= 0.4
                pitch = nearest_pitch(root_pc, low + (12 if is_octave else 0))
                pitch = max(low, min(low + 20, pitch))
                articulation = "sustain"
                dur = event.duration * 0.85
                expression = {74: 70}

            elif self.style == "ghost_note":
                # Heavy ghosting percussive pattern
                is_accent = (event.onset % 1.0) < 0.1
                pitch = nearest_pitch(root_pc, prev_pitch)
                pitch = max(low, min(low + 12, pitch))
                articulation = "staccato" if not is_accent else "sustain"
                dur = event.duration * 0.2 if not is_accent else event.duration * 0.8
                expression = {74: 45 if not is_accent else 70}

            elif self.style == "synth":
                # Modern generic synth bass
                pitch = nearest_pitch(root_pc, prev_pitch)
                pitch = max(36, min(48, pitch))
                articulation = "staccato"
                dur = event.duration * 0.5
                expression = {74: 65}

            elif self.style == "saw":
                # Aggressive sawtooth synthesis
                pitch = nearest_pitch(root_pc, prev_pitch)
                # occasional fifth/seventh leap
                if random.random() < 0.3 and len(pcs) > 1:
                    pitch = nearest_pitch(pcs[-1], prev_pitch)
                pitch = max(36, min(50, pitch))
                articulation = "sustain"
                dur = event.duration * 0.95
                expression = {74: 110, 95: 80}  # Open cutoff and saturation

            elif self.style == "sub":
                # Deep sine sub bass
                pitch = nearest_pitch(root_pc, low)
                pitch = max(24, min(38, pitch))
                articulation = "sustain"
                dur = event.duration * 0.95
                expression = {74: 30}  # Extremely closed low pass

            elif self.style == "hybrid_slap":
                # Syncopated hybrid: S, P, G, - (Same as our core hybrid)
                beat_offset = event.onset % 4.0
                if beat_offset < 0.1:
                    role = "S"
                elif abs(beat_offset - 0.25) < 0.1 or abs(beat_offset - 0.75) < 0.1:
                    role = "G"
                elif abs(beat_offset - 0.5) < 0.1 or abs(beat_offset - 1.5) < 0.1:
                    role = "P"
                else:
                    role = "G"

                if role == "S":
                    pitch = nearest_pitch(root_pc, low + 12)
                    pitch = max(low, min(low + 12, pitch))
                    articulation = "slap"
                    dur = event.duration * 0.75
                    expression = {74: 70}
                elif role == "P":
                    pop_candidates = [int(pc) for pc in pcs if (int(pc) - int(root_pc)) % 12 in (3, 4, 7)] or [int(root_pc)]
                    pitch = nearest_pitch(random.choice(pop_candidates), prev_pitch + 12)
                    pitch = max(low + 12, min(low + 28, pitch))
                    articulation = "pop"
                    dur = event.duration * 0.5
                    expression = {74: 105}
                else:
                    pitch = nearest_pitch(root_pc, prev_pitch)
                    pitch = max(low, min(low + 12, pitch))
                    articulation = "staccato"
                    dur = event.duration * 0.25
                    expression = {74: 40}

            elif self.style == "fingerstyle":
                # Smooth legato fingerstyle
                pitch = nearest_pitch(root_pc, prev_pitch)
                if random.random() < 0.25 and len(pcs) > 1:
                    pitch = nearest_pitch(pcs[1], prev_pitch)
                pitch = max(36, min(55, pitch))
                articulation = "sustain"
                expression = {74: 62}

            elif self.style == "adaptive":
                # Adaptive: density and leaps based on simplicity score
                simplicity = compute_simplicity(chord)
                # If complex chord (low simplicity), play simple stepwise roots to anchor the harmony
                # If simple chord, play complex leaping lines for melodic decoration
                if simplicity < 0.5:
                    pitch = nearest_pitch(root_pc, prev_pitch)
                    articulation = "sustain"
                else:
                    jump_pc = random.choice(pcs)
                    pitch = nearest_pitch(jump_pc, prev_pitch)
                    articulation = "staccato" if random.random() < 0.5 else "sustain"
                pitch = max(low, min(low + 18, pitch))

            elif self.style == "procedural":
                # Procedural: pitch choice calculated purely by beat index
                pattern_index = int(event.onset * 4) % 16
                pitch_pcs = [root_pc] * 4 + [(root_pc + 7) % 12] * 4 + [(root_pc + 3) % 12] * 4 + [root_pc] * 4
                pitch = nearest_pitch(pitch_pcs[pattern_index % len(pitch_pcs)], prev_pitch)
                pitch = max(low, min(low + 15, pitch))

            elif self.style == "generative":
                # Generative: Probabilistic Markov chains walking between chord degrees (Root, 3rd, 5th, Octave)
                prev_degree = (prev_pitch - root_pc) % 12
                # Transition matrix
                if prev_degree == 0:  # From Root: 40% jump to 5th, 30% jump to 3rd, 30% jump to Octave
                    choices = [7, 3, 12]
                    weights = [0.4, 0.3, 0.3]
                elif prev_degree == 7:  # From 5th: 60% resolve to Root, 40% to Octave
                    choices = [0, 12]
                    weights = [0.6, 0.4]
                else:  # Return to root
                    choices = [0]
                    weights = [1.0]
                degree = random.choices(choices, weights=weights)[0]
                pitch = nearest_pitch((root_pc + degree) % 12, prev_pitch)
                pitch = max(low, min(low + 16, pitch))

            elif self.style == "euclidean":
                # Euclidean grid: simple root-fifth movement
                is_offbeat = (event.onset % 1.0) > 0.01
                selected_pc = root_pc if not is_offbeat else (root_pc + 7) % 12
                pitch = nearest_pitch(selected_pc, prev_pitch)
                pitch = max(low, min(low + 12, pitch))
                articulation = "staccato" if is_offbeat else "sustain"

            elif self.style == "spectral_morphing":
                # Morphing CC 74 over time in a sine LFO shape
                pitch = nearest_pitch(root_pc, prev_pitch)
                pitch = max(36, min(48, pitch))
                lfo_val = int(60 + 40 * math.sin(2 * math.pi * event.onset / 8.0))
                expression = {74: lfo_val}

            elif self.style == "sidechain_reactive":
                # Volume ducking CC sweep per beat
                pitch = nearest_pitch(root_pc, prev_pitch)
                pitch = max(36, min(48, pitch))
                # Pump shape: starts at 15 on integer beat, rises to 90
                beat_fraction = event.onset % 1.0
                pump_volume = int(15 + 75 * (beat_fraction ** 1.5))
                expression = {74: 65, 7: pump_volume}  # CC 7 is main volume

            elif self.style == "self_modifying":
                # Scale leaps wider over time
                progress = event.onset / max(1.0, duration_beats)
                expanded_pc = random.choice(pcs)
                pitch = nearest_pitch(expanded_pc, prev_pitch)
                # Register expands from low to high over time
                current_high = low + 12 + int(progress * 16)
                pitch = max(low, min(current_high, pitch))
                articulation = "staccato" if progress > 0.5 and random.random() < 0.5 else "sustain"

            elif self.style == "cinematic":
                # Low cinematic string/bass drone
                pitch = nearest_pitch(root_pc, low)
                pitch = max(24, min(36, pitch))
                articulation = "sustain"
                expression = {74: 40}  # Warm, massive sub

            elif self.style == "tape":
                # Flutter: subtle micro-swings
                pitch = nearest_pitch(root_pc, prev_pitch)
                pitch = max(36, min(50, pitch))
                articulation = "sustain"
                expression = {74: 65, 1: int(15 + 10 * math.sin(event.onset * 10))} # wobble modwheel LFO

            elif self.style == "harmonic":
                # High octave chime-like chords playing above root
                # Alternate between root bass note and high harmonic chord tone
                is_high_harmonic = idx % 2 != 0
                if is_high_harmonic:
                    harm_pc = pcs[-1] if len(pcs) > 1 else root_pc
                    pitch = nearest_pitch(harm_pc, low + 24)
                    pitch = max(low + 24, min(low + 36, pitch))
                    articulation = "staccato"
                    dur = event.duration * 0.35
                    expression = {74: 95}
                else:
                    pitch = nearest_pitch(root_pc, low)
                    pitch = max(low, min(low + 12, pitch))
                    articulation = "sustain"
                    expression = {74: 55}

            elif self.style == "envelope":
                # Sharp envelope wah decay per note
                pitch = nearest_pitch(root_pc, prev_pitch)
                pitch = max(36, min(48, pitch))
                articulation = "sustain"
                # Expression open at start, closes immediately
                expression = {74: 95}  # decay envelope handles downstream, we trigger start spike

            # Clamp and snap to scale
            pitch = snap_to_scale(pitch, key)
            pitch = max(self.params.key_range_low, min(high_bound, pitch))

            # Raw velocity mapping before normalization
            raw_vel = 64
            if articulation == "slap":
                raw_vel = 100
            elif articulation == "pop":
                raw_vel = 120
            elif articulation == "staccato":
                raw_vel = 40
            else:
                raw_vel = 70

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

        # 2. Velocity locking algorithm
        if len(notes) > 1:
            raw_velocities = [n.velocity for n in notes]
            min_raw = min(raw_velocities)
            max_raw = max(raw_velocities)
            mean_raw = sum(raw_velocities) / len(raw_velocities)

            divisor = (max_raw - mean_raw)
            if divisor != 0:
                a = (target_max - target_avg) / divisor
                b = target_avg - a * mean_raw
            else:
                a = 1.0
                b = target_avg - mean_raw

            if a < 0.1 or a > 5.0:
                offset = target_avg - mean_raw
                for n in notes:
                    n.velocity = max(1, min(MIDI_MAX, int(round(n.velocity + offset))))
            else:
                for n in notes:
                    new_vel = int(round(a * n.velocity + b))
                    n.velocity = max(1, min(MIDI_MAX, new_vel))

            # Lock exact target_sum and target_max
            target_sum = int(round(target_avg * len(notes)))
            for n in notes:
                n.velocity = min(int(target_max), max(1, n.velocity))

            max_note = max(notes, key=lambda n: n.velocity)
            max_note.velocity = int(target_max)

            # Adjust velocities until we hit the exact target_sum
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
                            if n.velocity == int(target_max) and sum(1 for x in notes if x.velocity == int(target_max)) <= 1:
                                continue
                            candidates.append(n)
                
                if not candidates:
                    break
                
                random.shuffle(candidates)
                num_to_change = min(abs(diff), len(candidates))
                for i in range(num_to_change):
                    candidates[i].velocity += step

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_events(self, duration_beats: float, chords: list[ChordLabel]) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        events: list[RhythmEvent] = []
        t = 0.0

        if self.style in ("walking", "fingerstyle", "adaptive", "procedural", "generative"):
            # Semi-syncopated quarter-eighth walking grid
            while t < duration_beats:
                bar_beat = t % 4.0
                if bar_beat in (1.0, 3.0) and self.style != "walking":
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                    events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.45, velocity_factor=0.85))
                else:
                    events.append(RhythmEvent(onset=round(t, 6), duration=0.9, velocity_factor=1.0))
                t += 1.0

        elif self.style in ("slap", "pop", "ghost_note", "hybrid_slap", "self_modifying"):
            # Funk/Pop 16th grid
            while t < duration_beats:
                offsets = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 2.25, 2.5, 3.0, 3.25]
                # Filter out some offsets for pop
                if self.style == "pop":
                    offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
                for off in offsets:
                    onset = t + off
                    if onset < duration_beats:
                        vel_factor = 1.0 if off in (0.0, 1.0, 2.0, 3.0) else 0.8
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.2, velocity_factor=vel_factor))
                t += 4.0

        elif self.style in ("synth", "saw", "spectral_morphing", "sidechain_reactive", "envelope", "tape"):
            # 16th pluck syncopated grid
            while t < duration_beats:
                for off in [0.0, 0.25, 0.75, 1.0, 1.5, 1.75, 2.0, 2.5, 2.75, 3.25]:
                    onset = t + off
                    if onset < duration_beats:
                        vel_factor = 1.0 if off in (0.0, 2.0) else 0.85
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.15, velocity_factor=vel_factor))
                t += 4.0

        elif self.style == "sub":
            # Deep sub holds (syncopated kick sync)
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=1.8, velocity_factor=1.0))
                t += 2.0

        elif self.style == "euclidean":
            # Euclidean Bjorklund grid: e.g. 5 pulses in 8 steps (16th notes = 2 beats duration per bar)
            pattern = generate_euclidean(5, 8)
            while t < duration_beats:
                for step, active in enumerate(pattern):
                    if active:
                        onset = t + step * 0.25
                        if onset < duration_beats:
                            events.append(RhythmEvent(onset=round(onset, 6), duration=0.2, velocity_factor=1.0))
                t += 2.0

        elif self.style == "cinematic":
            # Slow dramatic whole note holds
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=3.8, velocity_factor=1.0))
                t += 4.0

        elif self.style == "harmonic":
            # Chimer grids: alternate bass notes and harmonics
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=0.45, velocity_factor=1.0))
                events.append(RhythmEvent(onset=round(t + 0.5, 6), duration=0.3, velocity_factor=0.85))
                t += 1.0

        return events
