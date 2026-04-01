"""
rhythm/probabilistic.py — ProbabilisticRhythmGenerator.

Layer: Application / Domain
"""

from __future__ import annotations

import random as _random
from dataclasses import dataclass

from melodica.rhythm import RhythmEvent, RhythmGenerator


@dataclass
class ProbabilisticRhythmGenerator(RhythmGenerator):
    """
    Generates rhythm stochastically based on strong/weak beat probabilities.

    grid_resolution: e.g., 0.25 for 16th notes.
    density: 0.0 - 1.0 global base probability of a hit.
    downbeat_weight: Extra chance modifier for downbeats (0.0 - 1.0+).
    syncopation: Extra chance modifier for weak offbeats (0.0 - 1.0+).
    gate: Factor of slot_duration to use for note duration (0.0-1.0).
    seed: RNG seed for reproducible output. None = non-deterministic.
    """

    grid_resolution: float = 0.25
    density: float = 0.5
    downbeat_weight: float = 0.3  # Added to density on downbeats
    syncopation: float = 0.0      # Added to density on weak offbeats
    gate: float = 0.9
    seed: int | None = None

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if duration_beats <= 0:
            return []

        rng = _random.Random(self.seed)
        events: list[RhythmEvent] = []
        onset = 0.0

        while onset < duration_beats - 0.001:
            # Determine metric position
            is_downbeat = (onset % 1.0) == 0.0
            is_upbeat = (onset % 0.5) == 0.0 and not is_downbeat
            is_offbeat = not is_downbeat and not is_upbeat
            
            # Calculate probability for this slot
            # Weighting: multiplying density by weight ensures 0 density = 0 notes
            prob = self.density
            if is_downbeat:
                prob *= (1.0 + self.downbeat_weight)
            elif is_offbeat:
                # offbeats are generally less likely unless syncopated
                prob *= (0.5 + self.syncopation)
            else:
                # upbeats (0.5, 1.5 etc) - neutral or slightly lower
                prob *= 0.8
                
            # If density is 1.0, we ALWAYS want a hit regardless of modifiers
            if self.density >= 1.0:
                prob = 1.0
                
            # Clamp
            prob = max(0.0, min(1.0, prob))
            
            # Evaluate hit
            if rng.random() < prob:
                velocity_mod = 1.0 if is_downbeat else (0.85 if is_upbeat else 0.7)
                events.append(
                    RhythmEvent(
                        onset=onset,
                        duration=self.grid_resolution * self.gate,
                        velocity_factor=velocity_mod
                    )
                )
                
            onset += self.grid_resolution
            
        return events
