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
rhythm/groove_template.py — DAW-style groove templates.

Provides per-note timing and velocity offsets that shift events
away from the grid for humanized, style-specific feel.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.rhythm import RhythmEvent


@dataclass(frozen=True)
class GrooveSlot:
    """A single timing/velocity offset at a fractional beat position."""

    position: float       # 0.0–1.0 fractional position within a beat
    timing_offset: float  # seconds (positive = late)
    velocity_factor: float


@dataclass
class GrooveTemplate:
    """Named groove that shifts rhythm events off the grid."""

    name: str
    beats_per_bar: int = 4
    slots: list[GrooveSlot] = field(default_factory=list)

    def apply(self, events: list[RhythmEvent]) -> list[RhythmEvent]:
        """Apply groove offsets to a list of rhythm events."""
        if not self.slots:
            return list(events)

        result: list[RhythmEvent] = []
        for ev in events:
            frac = ev.onset % 1.0
            applied = False
            for slot in self.slots:
                if abs(frac - slot.position) < 0.05:
                    result.append(RhythmEvent(
                        onset=round(ev.onset + slot.timing_offset * 0.01, 6),
                        duration=ev.duration,
                        velocity_factor=ev.velocity_factor * slot.velocity_factor,
                    ))
                    applied = True
                    break
            if not applied:
                result.append(ev)
        return result

    def verify_accuracy(self, notes: list[any], tolerance: float = 0.05) -> dict[str, any]:
        """
        Verify how accurately this groove template was applied to a list of NoteInfo.
        Returns a dictionary with validation metrics:
            - 'accuracy': float (0.0 to 1.0)
            - 'total_notes': int
            - 'matched_notes': int
            - 'details': list of strings with specific slot analysis
        """
        if not notes:
            return {
                "accuracy": 1.0,
                "total_notes": 0,
                "matched_notes": 0,
                "details": ["No notes provided for groove validation."]
            }

        if not self.slots:
            # Straight groove: all notes should land on standard grid coordinates
            total = len(notes)
            matched = sum(1 for n in notes if any(abs((n.start % 1.0) - p) < tolerance for p in [0.0, 0.25, 0.33, 0.5, 0.66, 0.75]))
            accuracy = matched / total if total > 0 else 1.0
            return {
                "accuracy": accuracy,
                "total_notes": total,
                "matched_notes": matched,
                "details": [f"Straight groove validation: {matched}/{total} notes on standard grid points."]
            }

        total = 0
        matched = 0
        details = []
        slot_stats = {s.position: {"expected_shift": s.timing_offset * 0.01, "count": 0, "matched": 0} for s in self.slots}

        for n in notes:
            frac = n.start % 1.0
            total += 1
            
            # Check if this note falls near a slot (taking into account timing shift)
            found_slot = False
            for slot in self.slots:
                expected_shift = slot.timing_offset * 0.01
                # Unshifted position would be start - expected_shift
                unshifted_pos = (n.start - expected_shift) % 1.0
                
                # Check if unshifted_pos matches slot position
                if abs(unshifted_pos - slot.position) < 0.05:
                    found_slot = True
                    slot_stats[slot.position]["count"] += 1
                    # Expected position is slot.position + expected_shift
                    expected_pos = (slot.position + expected_shift) % 1.0
                    if abs(frac - expected_pos) < tolerance:
                        matched += 1
                        slot_stats[slot.position]["matched"] += 1
                    break
            
            # If not matching any swung slot, it should be on a straight subdivision (no shift expected)
            if not found_slot:
                if any(abs(frac - p) < tolerance for p in [0.0, 0.25, 0.33, 0.5, 0.66, 0.75]):
                    matched += 1

        for pos, stats in slot_stats.items():
            details.append(
                f"Slot at position {pos}: matched {stats['matched']}/{stats['count']} notes "
                f"with expected shift of {stats['expected_shift']:.4f} beats."
            )

        accuracy = matched / total if total > 0 else 1.0
        return {
            "accuracy": accuracy,
            "total_notes": total,
            "matched_notes": matched,
            "details": details
        }


# ---------------------------------------------------------------------------
# Presets
# ---------------------------------------------------------------------------

STRAIGHT = GrooveTemplate(name="straight")

SWING_60 = GrooveTemplate(
    name="swing_60",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.5, timing_offset=3.5, velocity_factor=0.88),
    ],
)

HARD_SWING = GrooveTemplate(
    name="hard_swing",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.5, timing_offset=7.0, velocity_factor=0.82),
    ],
)

SHUFFLE = GrooveTemplate(
    name="shuffle",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.5, velocity_factor=1.0),
        GrooveSlot(position=0.33, timing_offset=5.0, velocity_factor=0.85),
        GrooveSlot(position=0.66, timing_offset=2.0, velocity_factor=0.90),
    ],
)

LAID_BACK = GrooveTemplate(
    name="laid_back",
    slots=[
        GrooveSlot(position=0.0, timing_offset=4.0, velocity_factor=0.95),
        GrooveSlot(position=0.25, timing_offset=3.0, velocity_factor=0.88),
        GrooveSlot(position=0.5, timing_offset=5.0, velocity_factor=0.82),
        GrooveSlot(position=0.75, timing_offset=3.5, velocity_factor=0.86),
    ],
)

PUSH = GrooveTemplate(
    name="push",
    slots=[
        GrooveSlot(position=0.0, timing_offset=-3.0, velocity_factor=1.0),
        GrooveSlot(position=0.5, timing_offset=-2.0, velocity_factor=0.90),
        GrooveSlot(position=0.75, timing_offset=-1.5, velocity_factor=0.85),
    ],
)

REGGAE = GrooveTemplate(
    name="reggae",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=0.75),
        GrooveSlot(position=0.5, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.75, timing_offset=6.0, velocity_factor=0.92),
    ],
)

BOSSA_NOVA = GrooveTemplate(
    name="bossa",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.33, timing_offset=3.0, velocity_factor=0.80),
        GrooveSlot(position=0.66, timing_offset=4.0, velocity_factor=0.88),
        GrooveSlot(position=0.75, timing_offset=2.0, velocity_factor=0.72),
    ],
)

HIP_HOP = GrooveTemplate(
    name="hip_hop",
    slots=[
        GrooveSlot(position=0.0, timing_offset=5.0, velocity_factor=1.0),
        GrooveSlot(position=0.25, timing_offset=0.0, velocity_factor=0.70),
        GrooveSlot(position=0.5, timing_offset=3.0, velocity_factor=0.92),
        GrooveSlot(position=0.75, timing_offset=6.0, velocity_factor=0.80),
    ],
)

DRUM_AND_BASS = GrooveTemplate(
    name="dnb",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.25, timing_offset=-1.5, velocity_factor=0.78),
        GrooveSlot(position=0.5, timing_offset=0.0, velocity_factor=0.95),
        GrooveSlot(position=0.75, timing_offset=4.0, velocity_factor=0.88),
    ],
)

WALTZ_RUBATO = GrooveTemplate(
    name="waltz_rubato",
    beats_per_bar=3,
    slots=[
        GrooveSlot(position=0.0, timing_offset=2.0, velocity_factor=1.0),
        GrooveSlot(position=0.33, timing_offset=1.5, velocity_factor=0.75),
        GrooveSlot(position=0.66, timing_offset=3.0, velocity_factor=0.85),
    ],
)

MAZURKA = GrooveTemplate(
    name="mazurka",
    beats_per_bar=3,
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.33, timing_offset=6.0, velocity_factor=0.95),
        GrooveSlot(position=0.66, timing_offset=0.0, velocity_factor=0.70),
    ],
)

BOLERO = GrooveTemplate(
    name="bolero",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.25, timing_offset=1.0, velocity_factor=0.60),
        GrooveSlot(position=0.5, timing_offset=2.0, velocity_factor=0.85),
        GrooveSlot(position=0.75, timing_offset=4.0, velocity_factor=0.92),
    ],
)

SAMBA = GrooveTemplate(
    name="samba",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.25, timing_offset=-1.0, velocity_factor=0.88),
        GrooveSlot(position=0.5, timing_offset=0.0, velocity_factor=0.95),
        GrooveSlot(position=0.75, timing_offset=2.5, velocity_factor=0.90),
    ],
)

FUNK = GrooveTemplate(
    name="funk",
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.25, timing_offset=1.0, velocity_factor=0.82),
        GrooveSlot(position=0.5, timing_offset=0.0, velocity_factor=0.90),
        GrooveSlot(position=0.75, timing_offset=5.0, velocity_factor=0.95),
    ],
)

AFRO_6_8 = GrooveTemplate(
    name="afro_6_8",
    beats_per_bar=6,
    slots=[
        GrooveSlot(position=0.0, timing_offset=0.0, velocity_factor=1.0),
        GrooveSlot(position=0.25, timing_offset=1.5, velocity_factor=0.80),
        GrooveSlot(position=0.5, timing_offset=0.0, velocity_factor=0.92),
        GrooveSlot(position=0.75, timing_offset=2.0, velocity_factor=0.78),
    ],
)

GROOVE_PRESETS: dict[str, GrooveTemplate] = {
    "straight": STRAIGHT,
    "swing_60": SWING_60,
    "hard_swing": HARD_SWING,
    "shuffle": SHUFFLE,
    "laid_back": LAID_BACK,
    "push": PUSH,
    "reggae": REGGAE,
    "bossa": BOSSA_NOVA,
    "hip_hop": HIP_HOP,
    "dnb": DRUM_AND_BASS,
    "waltz_rubato": WALTZ_RUBATO,
    "mazurka": MAZURKA,
    "bolero": BOLERO,
    "samba": SAMBA,
    "funk": FUNK,
    "afro_6_8": AFRO_6_8,
}
