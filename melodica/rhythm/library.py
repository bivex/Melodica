"""
rhythm/library.py — Preset Rhythm Library.

Contains standard 4/4 rhythms (straight, dotted, triplets, rests).
"""

from __future__ import annotations

from dataclasses import dataclass
from melodica.rhythm import RhythmEvent, RhythmGenerator


@dataclass
class StaticRhythmGenerator(RhythmGenerator):
    """Simple generator that returns a fixed list of events, optionally looped."""
    events: list[RhythmEvent]
    loop: bool = True

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        if not self.events:
            return []
        
        # Calculate full pattern length from last event
        pattern_len = max((e.onset + e.duration for e in self.events), default=4.0)
        
        result = []
        t = 0.0
        while t < duration_beats:
            for e in self.events:
                onset = t + e.onset
                if onset >= duration_beats:
                    break
                duration = min(e.duration, duration_beats - onset)
                result.append(RhythmEvent(onset=onset, duration=duration, velocity_factor=e.velocity_factor))
            
            if not self.loop:
                break
            t += pattern_len
            
        return result


# ---------------------------------------------------------------------------
# Rhythm Presets Library
# ---------------------------------------------------------------------------

RHYTHM_LIBRARY = {
    # 4/4 Duplet / Straight
    "straight_quarters": [RhythmEvent(i, 1.0) for i in range(4)],
    "straight_8ths": [RhythmEvent(i * 0.5, 0.5) for i in range(8)],
    "straight_16ths": [RhythmEvent(i * 0.25, 0.25) for i in range(16)],
    "whole_note": [RhythmEvent(0.0, 4.0)],
    "2_half_notes": [RhythmEvent(0.0, 2.0), RhythmEvent(2.0, 2.0)],
    
    # Dotted (4/4)
    "dotted_8_16th": [
        RhythmEvent(0.0, 0.75), RhythmEvent(0.75, 0.25),
        RhythmEvent(1.0, 0.75), RhythmEvent(1.75, 0.25),
        RhythmEvent(2.0, 0.75), RhythmEvent(2.75, 0.25),
        RhythmEvent(3.0, 0.75), RhythmEvent(3.75, 0.25),
    ],
    
    # Triplets (4/4)
    "straight_8_triplets": [RhythmEvent(i * (1/3), 1 / 3) for i in range(12)],
    "half_note_triplets": [RhythmEvent(0.0, 4 / 3), RhythmEvent(4 / 3, 4 / 3), RhythmEvent(8 / 3, 4 / 3)],
    "triplet_half_3_triplets": [RhythmEvent(0.0, 4 / 3), RhythmEvent(4 / 3, 2 / 3), RhythmEvent(2.0, 2 / 3), RhythmEvent(8 / 3, 2 / 3), RhythmEvent(10 / 3, 2 / 3)],

    # 4/4 with 32nds / 64ths
    "straight_32nds": [RhythmEvent(i * 0.125, 0.125) for i in range(32)],
    "straight_64ths": [RhythmEvent(i * 0.0625, 0.0625) for i in range(64)],
    "8th_16th_2_32nds": [RhythmEvent(0.0, 0.5), RhythmEvent(0.5, 0.25), RhythmEvent(0.75, 0.125), RhythmEvent(0.875, 0.125)],

    # 4/4 with Rests / Classics
    "Handel_001": [RhythmEvent(0.0, 0.5), RhythmEvent(0.75, 0.25), RhythmEvent(1.0, 1.0)],
    "q_q_rest_pop": [RhythmEvent(0.0, 1.0), RhythmEvent(2.0, 1.0)],
    "8th_8th_rest_loop": [RhythmEvent(0.0, 0.5), RhythmEvent(1.0, 0.5), RhythmEvent(2.0, 0.5), RhythmEvent(3.0, 0.5)],

    # Complex Syncopations & Duplets
    "16th_8th_16th_syncopation": [RhythmEvent(0.0, 0.25), RhythmEvent(0.25, 0.5), RhythmEvent(0.75, 0.25)],
    "six_8ths_q": [RhythmEvent(i * 0.5, 0.5) for i in range(6)] + [RhythmEvent(3.0, 1.0)],
    "q_2_8ths_half": [RhythmEvent(0.0, 1.0), RhythmEvent(1.0, 0.5), RhythmEvent(1.5, 0.5), RhythmEvent(2.0, 2.0)],
    "8th_2_16ths_3_qs": [RhythmEvent(0.0, 0.5), RhythmEvent(0.5, 0.25), RhythmEvent(0.75, 0.25), RhythmEvent(1.0, 1.0), RhythmEvent(2.0, 1.0), RhythmEvent(3.0, 1.0)],
    "dotted_8_3_16ths": [RhythmEvent(0.0, 0.75), RhythmEvent(0.75, 0.25), RhythmEvent(1.0, 0.25), RhythmEvent(1.25, 0.25), RhythmEvent(1.5, 0.25)],
    
    # Rest of user patterns
    "16th_unaccented_dotted_8th": [RhythmEvent(0.0, 0.25), RhythmEvent(0.25, 0.75)],
    "2_16ths_q_loop": [RhythmEvent(0.0, 0.25), RhythmEvent(0.25, 0.25), RhythmEvent(0.5, 1.0)],
    "8_2_16ths_4_16ths_2_qs": [RhythmEvent(0.0, 0.5), RhythmEvent(0.5, 0.25), RhythmEvent(0.75, 0.25), 
                               RhythmEvent(1.0, 0.25), RhythmEvent(1.25, 0.25), RhythmEvent(1.5, 0.25), RhythmEvent(1.75, 0.25),
                               RhythmEvent(2.0, 1.0), RhythmEvent(3.0, 1.0)],
}


def get_rhythm(name: str) -> RhythmGenerator:
    """Helper to get a generator for a named preset."""
    events = RHYTHM_LIBRARY.get(name, RHYTHM_LIBRARY["straight_quarters"])
    return StaticRhythmGenerator(events=events)
