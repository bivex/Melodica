# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
engines/fibril_engine.py — Advanced Polyphonic Performance Engine.

Direct implementation of the FIBRIL 'Cascading Harmonic Construction System'.
Features:
- Normalized Probability Maps (128-slot)
- Constraint-based voice allocation
- Rank-by-rank processing (Priority driven)
- Root/Fifth forced voicing
- Gaussian spatial preference
"""

from __future__ import annotations
import math
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional, Any

from melodica import types
from melodica.types import ChordLabel, HarmonizationRequest, NoteInfo, Scale, Quality

# ============================================================================
# CORE FIBRIL LOGIC
# ============================================================================

class NormalizedProbabilityMap:
    """A 128-element probability array that always sums to 1.0."""
    def __init__(self, tolerance: float = 1e-6):
        self.probs = [1.0/128] * 128
        self.forbidden: Set[int] = set()
        self.tolerance = tolerance

    def zero_notes(self, notes: List[int]):
        for n in notes:
            if 0 <= n < 128:
                self.probs[n] = 0.0
                self.forbidden.add(n)
        self.normalize()

    def boost_notes(self, notes: List[int], factor: float):
        for n in notes:
            if 0 <= n < 128 and n not in self.forbidden:
                self.probs[n] *= factor
        self.normalize()

    def apply_gaussian(self, center: int, spread: float, strength: float):
        for n in range(128):
            if n not in self.forbidden:
                dist = abs(n - center)
                factor = math.exp(-(dist**2) / (2 * (spread/2)**2))
                self.probs[n] *= (1.0 + strength * factor)
        self.normalize()

    def normalize(self):
        for n in self.forbidden: self.probs[n] = 0.0
        total = sum(p for i, p in enumerate(self.probs) if i not in self.forbidden)
        if total <= self.tolerance:
            allowed = [i for i in range(128) if i not in self.forbidden]
            if not allowed: return
            p_uniform = 1.0 / len(allowed)
            for i in range(128): self.probs[i] = p_uniform if i in allowed else 0.0
        else:
            for i in range(128):
                if i not in self.forbidden: self.probs[i] /= total

@dataclass
class FibrilRank:
    number: int
    tonicization: int # 1-8
    priority: int
    density: int = 0
    gci: int = 1

    def get_root_pc(self, key_center: int) -> int:
        if self.tonicization == 8: return (key_center + 4) % 12 # Subtonic trick
        offsets = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
        return (key_center + offsets.get(self.tonicization, 0)) % 12

class FibrilEngine:
    """The full Allocation Engine based on FIBRIL classes."""
    def __init__(self):
        self.ranks = [
            FibrilRank(1, 2, 5), FibrilRank(2, 3, 3), FibrilRank(3, 1, 1),
            FibrilRank(4, 5, 2), FibrilRank(5, 6, 6), FibrilRank(6, 4, 4),
            FibrilRank(7, 7, 7), FibrilRank(8, 8, 8)
        ]
        self.priority_order = [3, 4, 2, 6, 1, 5, 7, 8] # R3, R4, R2...
        self.max_voices = 48

    def harmonize(self, req: HarmonizationRequest) -> list[ChordLabel]:
        """Adapt FIBRIL to Melodica chord structure."""
        # This engine actually produces VOICINGS, but we map it to ChordLabels
        # to satisfy the Melodica Harmonizer interface.
        duration = max(n.start + n.duration for n in req.melody)
        step = req.chord_rhythm
        chords = []
        t = 0.0
        while t < duration:
            # Analyze window to set rank densities
            window = [n for n in req.melody if t <= n.start < t + step]
            if not window:
                chords.append(ChordLabel(root=req.key.root, quality=Quality.MAJOR, start=t, duration=step, degree=1))
            else:
                chord = self._generate_step_chord(window, req.key, t, step)
                chords.append(chord)
            t += step
        return chords

    def _generate_step_chord(self, notes: list[NoteInfo], key: Scale, start: float, dur: float) -> ChordLabel:
        # 1. Reset and set densities based on melody intensity
        active_pcs = set(n.pitch % 12 for n in notes)
        avg_vel = sum(n.velocity for n in notes) / len(notes)
        
        for r in self.ranks:
            r.density = 0
            # If melody hits this rank's degree, activate it
            root_pc = r.get_root_pc(key.root)
            if root_pc in active_pcs:
                r.density = max(1, int(avg_vel / 24)) # Map intensity to density
        
        # 2. Process ranks in priority order
        active_voices: List[int] = []
        ordered = sorted([r for r in self.ranks if r.density > 0], 
                         key=lambda x: self.priority_order.index(x.number))
        
        if not ordered:
            return ChordLabel(root=key.root, quality=Quality.MAJOR, start=start, duration=dur, degree=1)

        # Record the 'winning' rank for the label
        primary_rank = ordered[0]
        
        # FIBRIL would now run the probability loop to pick exactly 'primary_rank.density' notes
        # We simulate the most active rank's quality
        chord = key.diatonic_chord(primary_rank.tonicization)
        
        # Add FIBRIL metadata for potential voicing generators
        label = ChordLabel(root=chord.root, quality=chord.quality, start=start, duration=dur, degree=primary_rank.tonicization)
        label.fibril_metadata = {
            "voices": self.allocate_voices(ordered, key.root),
            "total_density": sum(r.density for r in ordered)
        }
        return label

    def allocate_voices(self, active_ranks: list[FibrilRank], key_center: int) -> list[int]:
        """Simulate the cascading probability allocation."""
        allocated = []
        prob_map = NormalizedProbabilityMap()
        
        # Hard block extreme ranges
        prob_map.zero_notes(list(range(0, 23)) + list(range(97, 128)))
        
        for rank in active_ranks:
            for _ in range(rank.density):
                if len(allocated) >= self.max_voices: break
                
                # Apply constraints for this voice
                # A. Prevent duplicates
                prob_map.zero_notes(allocated)
                
                # B. Gaussian Spatial Bias (Poisson-like)
                center = 60 + ((rank.gci - 5) // 3) * 12
                prob_map.apply_gaussian(center, (rank.density//2 or 1)*12, 2.0)
                
                # C. Root Force (if not yet voiced)
                root_pc = rank.get_root_pc(key_center)
                if not any(v % 12 == root_pc for v in allocated):
                    prob_map.boost_notes([n for n in range(128) if n%12 == root_pc], 5.0)

                # D. Perfect Fifth Boost
                for v in allocated:
                    fifths = [n for n in range(128) if abs(n - v) % 12 == 7]
                    prob_map.boost_notes(fifths, 4.0)

                # Selection
                weights = prob_map.probs
                roll = random.random()
                curr = 0.0
                for midi, p in enumerate(weights):
                    curr += p
                    if roll <= curr:
                        allocated.append(midi)
                        break
        return allocated
