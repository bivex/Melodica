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
generators/sequence.py — Musical sequence (motif transposition) generator.

Layer: Application / Domain
Style: Baroque, classical, pop, film music.

A sequence takes a short melodic motif and repeats it at successively
transposed pitch levels. This is one of the most important developmental
techniques in Western music (Pachelbel's Canon, Vivaldi, pop hooks).

Sequence types:
    "diatonic"    — transpose by scale degrees (stays in key)
    "chromatic"   — transpose by fixed semitone interval
    "fifths"      — transpose by circle of fifths
    "descending"  — descending diatonic sequence (most common)
    "ascending"   — ascending diatonic sequence

The generator creates a motif from chord tones / scale tones, then
transposes it stepwise through the progression.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class SequenceGenerator(PhraseGenerator):
    """
    Sequence (motif transposition) generator.

    motif_length:
        Number of notes in the motif (2–8).
    sequence_type:
        "diatonic", "chromatic", "fifths", "descending", "ascending"
    interval_steps:
        For chromatic: semitone interval between repetitions.
        For diatonic: scale degree steps (1 = stepwise).
    repetitions:
        Number of times to repeat/transposed the motif. 0 = auto-fill.
    generate_motif:
        If True, generate a random motif. If False, use motif_notes.
    motif_notes:
        Explicit motif as list of scale degrees (1-based) or semitone offsets.
    """

    name: str = "Sequence Generator"
    motif_length: int = 4
    sequence_type: str = "descending"
    interval_steps: int = 1
    repetitions: int = 0
    generate_motif: bool = True
    motif_notes: list[int] | None = None
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        motif_length: int = 4,
        sequence_type: str = "descending",
        interval_steps: int = 1,
        repetitions: int = 0,
        generate_motif: bool = True,
        motif_notes: list[int] | None = None,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.motif_length = max(2, min(8, motif_length))
        if sequence_type not in ("diatonic", "chromatic", "fifths", "descending", "ascending"):
            raise ValueError(
                f"sequence_type must be 'diatonic', 'chromatic', 'fifths', "
                f"'descending', or 'ascending'; got {sequence_type!r}"
            )
        self.sequence_type = sequence_type
        self.interval_steps = max(1, interval_steps)
        self.repetitions = max(0, repetitions)
        self.generate_motif = generate_motif
        self.motif_notes = motif_notes
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

        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        # Generate or parse the motif
        motif_pcs = self._build_motif(key, chords[0])

        # Compute transposition steps
        steps = self._transposition_steps(key, chords)

        # Build the full pitch sequence
        all_pitches = self._expand_sequence(motif_pcs, steps, anchor, low, high)

        # Build rhythm
        events = self._build_events(duration_beats, len(all_pitches))

        notes: list[NoteInfo] = []
        prev_chord: ChordLabel | None = None
        last_chord: ChordLabel | None = None

        for i, event in enumerate(events):
            if i >= len(all_pitches):
                break

            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitch = all_pitches[i]
            pitch = max(low, min(high, pitch))

            # Accent at the start of each repetition
            is_rep_start = i % self.motif_length == 0
            vel = self._velocity(is_rep_start)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, int(vel * event.velocity_factor))),
                )
            )
            prev_chord = chord

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Motif generation
    # ------------------------------------------------------------------

    def _build_motif(self, key: Scale, chord: ChordLabel) -> list[int]:
        """
        Build a motif as a list of pitch classes (0-11).
        """
        if not self.generate_motif and self.motif_notes:
            # motif_notes are scale degrees (1-based) or semitone offsets
            degs = key.degrees()
            pcs = []
            for d in self.motif_notes:
                idx = (d - 1) % len(degs)
                pcs.append(int(degs[idx]))
            return pcs

        # Generate a random motif
        degs = key.degrees()
        if not degs:
            return [0] * self.motif_length

        pcs: list[int] = []
        # Start on a chord tone
        chord_pcs = chord.pitch_classes()
        start_pc = random.choice(chord_pcs) if chord_pcs else int(degs[0])
        pcs.append(start_pc)

        for _ in range(self.motif_length - 1):
            # Mostly stepwise with occasional leaps
            if random.random() < 0.7 + self.params.complexity * -0.2:
                # Step: move to adjacent scale degree
                current_idx = None
                for j, d in enumerate(degs):
                    if abs(int(d) - pcs[-1]) % 12 == 0:
                        current_idx = j
                        break
                if current_idx is not None:
                    step = random.choice([-1, 1])
                    next_idx = (current_idx + step) % len(degs)
                    pcs.append(int(degs[next_idx]))
                else:
                    pcs.append(int(random.choice(degs)))
            else:
                # Leap to a chord tone
                if chord_pcs:
                    pcs.append(random.choice(chord_pcs))
                else:
                    pcs.append(int(random.choice(degs)))

        return pcs

    # ------------------------------------------------------------------
    # Transposition steps
    # ------------------------------------------------------------------

    def _transposition_steps(self, key: Scale, chords: list[ChordLabel]) -> list[int]:
        """
        Compute the transposition offsets (in semitones) for each repetition.
        Returns a list of semitone offsets relative to the original motif.
        """
        degs = key.degrees()
        n = len(degs) if degs else 7

        if self.sequence_type == "chromatic":
            step = self.interval_steps
            count = self.repetitions or 8
            return [i * step for i in range(count)]

        elif self.sequence_type == "fifths":
            count = self.repetitions or 7
            return [i * 7 for i in range(count)]

        elif self.sequence_type in ("descending", "diatonic"):
            # Descending by scale degrees
            step = (
                -self.interval_steps if self.sequence_type == "descending" else self.interval_steps
            )
            count = self.repetitions or n
            offsets = []
            cumulative = 0
            for i in range(count):
                offsets.append(cumulative)
                # Compute semitone distance for one diatonic step
                degs_list = sorted(degs)
                cumulative += self._diatonic_step_semitones(degs, step)
            return offsets

        elif self.sequence_type == "ascending":
            step = self.interval_steps
            count = self.repetitions or n
            offsets = []
            cumulative = 0
            for i in range(count):
                offsets.append(cumulative)
                cumulative += self._diatonic_step_semitones(degs, step)
            return offsets

        return [0]

    def _diatonic_step_semitones(self, degs: list[float], steps: int) -> int:
        """Compute semitone distance for N diatonic steps."""
        if not degs:
            return steps * 2  # fallback: whole steps
        n = len(degs)
        if steps > 0:
            # Ascending
            full_octaves = steps // n
            remainder = steps % n
            semitones = full_octaves * 12
            if remainder > 0:
                semitones += int(degs[remainder]) - int(degs[0])
                if semitones < 0:
                    semitones += 12
            return max(1, semitones)
        elif steps < 0:
            # Descending
            abs_steps = abs(steps)
            full_octaves = abs_steps // n
            remainder = abs_steps % n
            semitones = full_octaves * 12
            if remainder > 0:
                idx = (n - remainder) % n
                diff = int(degs[0]) - int(degs[idx])
                if diff < 0:
                    diff += 12
                semitones += diff
            return -max(1, semitones)
        return 0

    # ------------------------------------------------------------------
    # Sequence expansion
    # ------------------------------------------------------------------

    def _expand_sequence(
        self,
        motif_pcs: list[int],
        steps: list[int],
        anchor: int,
        low: int,
        high: int,
    ) -> list[int]:
        """Expand motif through all transposition steps."""
        all_pitches: list[int] = []

        for offset in steps:
            for pc in motif_pcs:
                transposed_pc = (pc + offset) % 12
                pitch = nearest_pitch(transposed_pc, anchor + offset)
                # Keep within range
                while pitch < low:
                    pitch += 12
                while pitch > high:
                    pitch -= 12
                all_pitches.append(pitch)

        return all_pitches

    # ------------------------------------------------------------------
    # Rhythm & velocity
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float, target_count: int) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default: evenly spaced eighth notes
        if target_count <= 0:
            target_count = 16
        step = duration_beats / target_count
        step = max(0.25, min(1.0, step))
        t, events = 0.0, []
        while t < duration_beats and len(events) < target_count:
            events.append(RhythmEvent(onset=round(t, 6), duration=step * 0.85))
            t += step
        return events

    def _velocity(self, is_rep_start: bool) -> int:
        base = int(60 + self.params.density * 30)
        if is_rep_start:
            return min(127, int(base * 1.15))
        return base
