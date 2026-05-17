"""Melody rhythm generation — groove-aware event builders.

Responsibilities:
  - GrooveProfile: per-beat strength values for natural accent patterns
  - Build RhythmEvent list from density/syncopation/rhythm_variety
  - Motif-based rhythm patterns with beat-aware duration pools
  - Phrase gap handling
"""

from __future__ import annotations

import math
import random

from melodica.rhythm import RhythmEvent, RhythmGenerator


class GrooveProfile:
    """Defines beat strength per subdivision for natural accent patterns."""

    # 4/4 groove: beat 1 strongest, beat 3 secondary strong
    _DEFAULT_STRENGTHS: dict[float, float] = {
        0.0: 1.0,   # beat 1
        1.0: 0.7,   # beat 2
        2.0: 0.9,   # beat 3
        3.0: 0.6,   # beat 4
    }
    _OFFBEAT_STRENGTH = 0.4
    _SIXTEENTH_STRENGTH = 0.2

    def beat_strength(self, onset: float) -> float:
        """Return continuous beat strength (0.0-1.0) for a given onset."""
        beat = onset % 4.0
        # Check if near a strong beat position
        for strong_beat, strength in self._DEFAULT_STRENGTHS.items():
            if abs(beat - strong_beat) < 0.1:
                return strength
        # Offbeat (x.5 positions)
        frac = onset % 1.0
        if abs(frac - 0.5) < 0.15:
            return self._OFFBEAT_STRENGTH
        # Sixteenth note positions
        return self._SIXTEENTH_STRENGTH


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
        groove: GrooveProfile | None = None,
    ) -> None:
        self.params = params
        self.phrase_length = phrase_length
        self.phrase_rest_probability = phrase_rest_probability
        self.syncopation = syncopation
        self.rhythm_variety = rhythm_variety
        self.rhythm_motif = rhythm_motif
        self.rhythm = rhythm
        self.groove = groove or GrooveProfile()

    def build_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Generate rhythm events for the given duration."""
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.rhythm_motif is not None and len(self.rhythm_motif) >= 2:
            return self._build_motif_events(duration_beats)

        return self._build_groove_events(duration_beats)

    def _build_groove_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Groove-aware rhythm generation with beat strength."""
        base_step = max(0.25, (1.0 - self.params.density) * 2.0)
        events: list[RhythmEvent] = []
        t = 0.0

        # Generate a short rhythmic motif to tile (3-5 events)
        tile_motif = self._generate_tile_motif(base_step)

        tile_idx = 0

        while t < duration_beats:
            # Phrase gap
            if self.phrase_length > 0 and t > 0 and t % self.phrase_length < base_step:
                if random.random() < self.phrase_rest_probability:
                    gap = random.choice([0.25, 0.5, 0.5, 1.0])
                    t += gap
                    tile_idx = 0  # reset motif at phrase boundary
                    continue

            beat_str = self.groove.beat_strength(t)

            # Pick duration based on beat strength
            if self.rhythm_variety > 0 and random.random() < self.rhythm_variety:
                dur = self._duration_for_beat(beat_str, base_step, tile_motif, tile_idx)
            else:
                dur = max(0.125, base_step - 0.01)

            # Syncopation
            onset = t
            if self.syncopation > 0 and random.random() < self.syncopation:
                shift = random.choice([0.125, 0.25, 0.25, 0.375])
                onset = t + shift

            # Velocity factor from groove strength
            vel_factor = 0.7 + 0.3 * self.groove.beat_strength(onset)

            events.append(
                RhythmEvent(
                    onset=round(onset, 6), duration=max(0.1, dur), velocity_factor=vel_factor
                )
            )

            # Advance time
            if self.rhythm_variety > 0 and random.random() < self.rhythm_variety:
                t += random.choice([base_step * 0.5, base_step * 0.75, base_step, base_step, base_step * 1.5])
            else:
                t += base_step

            tile_idx += 1

        return events

    def _build_motif_events(self, duration_beats: float) -> list[RhythmEvent]:
        """Build events from a repeating rhythm_motif pattern."""
        motif = self.rhythm_motif
        assert motif is not None
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

            vel_factor = 0.7 + 0.3 * self.groove.beat_strength(onset)

            events.append(
                RhythmEvent(onset=round(onset, 6), duration=dur, velocity_factor=vel_factor)
            )
            t += dur
            motif_idx += 1

        return events

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _generate_tile_motif(self, base_step: float) -> list[float]:
        """Generate a short rhythmic motif (3-5 relative durations) for tiling."""
        length = random.choice([3, 4, 4, 5])
        pool = [0.5, 0.75, 1.0, 1.0, 1.5, 2.0]
        return [random.choice(pool) for _ in range(length)]

    def _duration_for_beat(
        self, beat_strength: float, base_step: float, tile_motif: list[float], tile_idx: int
    ) -> float:
        """Pick duration based on beat strength and optional tile motif."""
        # Strong beats → longer durations
        if beat_strength > 0.8:
            long_pool = [base_step, base_step * 1.5, base_step * 2.0]
            return max(0.1, random.choice(long_pool))
        elif beat_strength > 0.5:
            mid_pool = [base_step * 0.75, base_step, base_step, base_step * 1.5]
            return max(0.1, random.choice(mid_pool))
        else:
            short_pool = [base_step * 0.25, base_step * 0.5, base_step * 0.5, base_step * 0.75]
            return max(0.1, random.choice(short_pool))

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
