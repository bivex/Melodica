"""Melody rhythm generation — event builders.

Responsibilities:
  - Build RhythmEvent list from density/syncopation/rhythm_variety
  - Motif-based rhythm patterns
  - Phrase gap handling
"""

from __future__ import annotations

import random

from melodica.rhythm import RhythmEvent, RhythmGenerator


class RhythmBuilder:
    """Builds rhythm events for melody generation."""

    def __init__(
        self,
        params,
        phrase_length: float,
        phrase_rest_probability: float,
        syncopation: float,
        rhythm_variety: float,
        rhythm_motif: list[float] | None,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        self.params = params
        self.phrase_length = phrase_length
        self.phrase_rest_probability = phrase_rest_probability
        self.syncopation = syncopation
        self.rhythm_variety = rhythm_variety
        self.rhythm_motif = rhythm_motif
        self.rhythm = rhythm

    def build_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Generate rhythm events for the given duration."""
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.rhythm_motif is not None and len(self.rhythm_motif) >= 2:
            return self._build_motif_events(duration_beats)

        return self._build_standard_events(duration_beats)

    def _build_standard_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Standard generative rhythm using density and syncopation."""
        base_step = max(0.25, (1.0 - self.params.density) * 2.0)
        events: list[RhythmEvent] = []
        t = 0.0
        dur_pool = self._duration_pool(base_step)
        step_pool = [base_step * 0.5, base_step * 0.75, base_step, base_step, base_step * 1.5]

        while t < duration_beats:
            # Phrase gap
            if self.phrase_length > 0 and t > 0 and t % self.phrase_length < base_step:
                if random.random() < self.phrase_rest_probability:
                    gap = random.choice([0.25, 0.5, 0.5, 1.0])
                    t += gap
                    continue

            # Pick duration
            if self.rhythm_variety > 0 and random.random() < self.rhythm_variety:
                dur = random.choice(dur_pool)
            else:
                dur = max(0.125, base_step - 0.01)

            # Syncopation
            onset = t
            if self.syncopation > 0 and random.random() < self.syncopation:
                shift = random.choice([0.125, 0.25, 0.25, 0.375])
                onset = t + shift

            is_downbeat = onset % 1.0 < 0.1
            vel_factor = random.uniform(1.05, 1.15) if is_downbeat else random.uniform(0.85, 1.0)

            events.append(
                RhythmEvent(
                    onset=round(onset, 6), duration=max(0.1, dur), velocity_factor=vel_factor
                )
            )

            # Advance time
            if self.rhythm_variety > 0 and random.random() < self.rhythm_variety:
                t += random.choice(step_pool)
            else:
                t += base_step

        return events

    def _build_motif_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Build events from a repeating rhythm_motif pattern."""
        motif = self.rhythm_motif
        assert motif is not None  # guaranteed by caller
        base_step = max(0.25, (1.0 - self.params.density) * 2.0)

        events: list[RhythmEvent] = []
        t = 0.0
        motif_idx = 0

        while t < duration_beats:
            # Phrase gap
            if self.phrase_length > 0 and t > 0 and t % self.phrase_length < base_step:
                if random.random() < self.phrase_rest_probability:
                    gap = random.choice([0.25, 0.5, 0.5, 1.0])
                    t += gap
                    continue

            ratio = motif[motif_idx % len(motif)]
            dur = max(0.1, base_step * ratio)

            onset = t
            if self.syncopation > 0 and random.random() < self.syncopation:
                shift = random.choice([0.125, 0.25])
                onset = t + shift

            is_downbeat = onset % 1.0 < 0.1
            vel_factor = random.uniform(1.05, 1.15) if is_downbeat else random.uniform(0.85, 1.0)

            events.append(
                RhythmEvent(onset=round(onset, 6), duration=dur, velocity_factor=vel_factor)
            )
            t += dur
            motif_idx += 1

        return events

    def _duration_pool(self, base_step: float) -> list[float]:
        """Return pool of note durations for rhythmic variety."""
        return [
            max(0.1, base_step * 0.5),
            max(0.125, base_step),
            max(0.125, base_step),
            base_step * 1.5,
            base_step * 2.0,
            max(0.1, base_step * 0.25),
        ]
