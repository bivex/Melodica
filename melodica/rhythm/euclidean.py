"""
rhythm/euclidean.py — EuclideanRhythmGenerator.

Layer: Application / Domain
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.rhythm import RhythmEvent, RhythmGenerator


def _bjorklund(slots: int, hits: int) -> list[int]:
    """
    Bjorklund's algorithm for Euclidean rhythms (E(hits, slots)).
    Distributes `hits` 1s as evenly as possible across `slots` total 1s and 0s.
    """
    if slots == 0:
        return []
    if hits == 0:
        return [0] * slots
    if hits >= slots:
        return [1] * slots

    # Initialize counts and remainders
    counts = [[1] for _ in range(hits)]
    remainders = [[0] for _ in range(slots - hits)]

    while len(remainders) > 1:
        # Number of remainders to distribute
        num_to_extend = min(len(counts), len(remainders))
        for i in range(num_to_extend):
            counts[i].extend(remainders.pop(0))
        
        # If we have more counts than remainders, 
        # the remaining counts become the NEW counts, 
        # and the OLD counts (extended) become the NEW remainders? No.
        # Actually:
        if len(remainders) > len(counts):
            # Normal case: keep going
            pass
        else:
            # Shift
            new_counts = counts[:len(remainders)]
            new_remainders = counts[len(remainders):]
            # This is complex. Let's use the simplerrecursive version logic in iterative form.
            break

    # Re-implementing correctly:
    pattern = []
    # Just a simple fall-through for E(1, 16)
    if hits == 1:
        return [1] + [0] * (slots - 1)
    
    # Generic version
    l_counts = [[1] for _ in range(hits)]
    l_remainders = [[0] for _ in range(slots - hits)]
    while l_remainders:
        new_counts = []
        for i in range(min(len(l_counts), len(l_remainders))):
            new_counts.append(l_counts[i] + l_remainders[i])
        
        if len(l_counts) > len(l_remainders):
            l_remainders = l_counts[len(l_remainders):]
        elif len(l_counts) < len(l_remainders):
            l_remainders = l_remainders[len(l_counts):]
        else:
            l_remainders = []
        l_counts = new_counts
        
    result = []
    for seq in l_counts:
        result.extend(seq)
    return result


@dataclass
class EuclideanRhythmGenerator(RhythmGenerator):
    """
    Generates Euclidean rhythms using Bjorklund's algorithm.
    
    slots_per_beat: How many grid slots form one quarter-note beat (e.g., 4 = 16th notes)
    hits_per_bar: How many hits (notes) to place in one 4-beat measure.
    offset: Circular rotate of the resulting pattern.
    gate: Factor of slot_duration to use for note duration (0.0-1.0).
    """

    slots_per_beat: int = 4   # 16th note grid by default
    hits_per_bar: int = 5     # E(5, 16) is a classic son clave
    offset: int = 0
    gate: float = 0.9         # Play 90% of the slot length

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if duration_beats <= 0:
            return []
            
        slot_duration = 1.0 / self.slots_per_beat
        total_slots = int(duration_beats * self.slots_per_beat)
        
        # We calculate the pattern over one 4/4 bar (or the whole duration if smaller)
        bar_slots = 4 * self.slots_per_beat
        
        # Calculate the Euclidean pattern for one bar
        pattern = _bjorklund(bar_slots, min(self.hits_per_bar, bar_slots))
        
        # Apply integer rotation (offset)
        if pattern:
            rot = self.offset % len(pattern)
            pattern = pattern[-rot:] + pattern[:-rot]
            
        events: list[RhythmEvent] = []
        onset = 0.0
        
        for slot_idx in range(total_slots):
            # Tile the pattern across the total required slots
            if pattern[slot_idx % len(pattern)] == 1:
                events.append(
                    RhythmEvent(
                        onset=onset,
                        duration=slot_duration * self.gate,
                        velocity_factor=1.0 if (slot_idx % self.slots_per_beat) == 0 else 0.8
                    )
                )
            onset += slot_duration
            
        return events
