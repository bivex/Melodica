# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
orchestration_rules.py — Instrument range validation and orchestration assistance.

Provides InstrumentRange database for 30 orchestral instruments, validation/clamping
of note ranges, register identification, and orchestration blending analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.types import NoteInfo


@dataclass
class InstrumentRange:
    """Playable range and characteristics for an orchestral instrument."""

    name: str
    min_midi: int
    max_midi: int
    comfortable_low: int
    comfortable_high: int
    transposition: int = 0
    register_names: dict[str, tuple[int, int]] = field(default_factory=dict)


@dataclass
class OrchestrationWarning:
    """Validation result for an out-of-range note."""

    instrument: str
    pitch: int
    message: str
    severity: str  # "info", "warning", "error"


# ---------------------------------------------------------------------------
# Instrument database — concert pitch MIDI ranges
# ---------------------------------------------------------------------------

INSTRUMENTS: dict[str, InstrumentRange] = {
    "violin": InstrumentRange(
        "violin", 55, 103, 60, 96,
        register_names={"lowest": (55, 59), "low": (60, 71), "middle": (72, 83), "high": (84, 95), "extreme": (96, 103)},
    ),
    "viola": InstrumentRange(
        "viola", 48, 91, 53, 84,
        register_names={"lowest": (48, 52), "low": (53, 65), "middle": (66, 77), "high": (78, 84), "extreme": (85, 91)},
    ),
    "cello": InstrumentRange(
        "cello", 36, 79, 41, 72,
        register_names={"lowest": (36, 40), "low": (41, 53), "middle": (54, 65), "high": (66, 72), "extreme": (73, 79)},
    ),
    "contrabass": InstrumentRange(
        "contrabass", 28, 67, 31, 55,
        register_names={"lowest": (28, 30), "low": (31, 43), "middle": (44, 55), "high": (56, 67)},
    ),
    "flute": InstrumentRange(
        "flute", 60, 96, 67, 91,
        register_names={"low": (60, 72), "middle": (73, 84), "high": (85, 96)},
    ),
    "piccolo": InstrumentRange(
        "piccolo", 72, 108, 79, 103,
        register_names={"low": (72, 84), "middle": (85, 96), "high": (97, 108)},
    ),
    "oboe": InstrumentRange(
        "oboe", 58, 93, 65, 84,
        register_names={"low": (58, 70), "middle": (71, 82), "high": (83, 93)},
    ),
    "english_horn": InstrumentRange(
        "english_horn", 53, 87, 60, 79,
        register_names={"low": (53, 65), "middle": (66, 77), "high": (78, 87)},
    ),
    "clarinet": InstrumentRange(
        "clarinet", 50, 91, 55, 84,
        register_names={"chalumeau": (50, 64), "throat": (65, 70), "clarino": (71, 84), "extreme": (85, 91)},
    ),
    "bass_clarinet": InstrumentRange(
        "bass_clarinet", 38, 79, 43, 72,
        register_names={"low": (38, 53), "middle": (54, 67), "high": (68, 79)},
    ),
    "bassoon": InstrumentRange(
        "bassoon", 34, 75, 41, 67,
        register_names={"lowest": (34, 40), "low": (41, 53), "middle": (54, 65), "high": (66, 75)},
    ),
    "contrabassoon": InstrumentRange(
        "contrabassoon", 22, 56, 25, 48,
        register_names={"low": (22, 36), "middle": (37, 48), "high": (49, 56)},
    ),
    "french_horn": InstrumentRange(
        "french_horn", 34, 77, 41, 70,
        register_names={"lowest": (34, 40), "low": (41, 53), "middle": (54, 65), "high": (66, 70), "extreme": (71, 77)},
    ),
    "trumpet": InstrumentRange(
        "trumpet", 55, 82, 60, 77,
        register_names={"low": (55, 64), "middle": (65, 72), "high": (73, 77), "extreme": (78, 82)},
    ),
    "trombone": InstrumentRange(
        "trombone", 40, 75, 45, 67,
        register_names={"pedal": (40, 44), "low": (45, 55), "middle": (56, 65), "high": (66, 75)},
    ),
    "bass_trombone": InstrumentRange(
        "bass_trombone", 34, 70, 38, 62,
        register_names={"pedal": (34, 37), "low": (38, 50), "middle": (51, 62), "high": (63, 70)},
    ),
    "tuba": InstrumentRange(
        "tuba", 26, 62, 31, 53,
        register_names={"pedal": (26, 30), "low": (31, 43), "middle": (44, 53), "high": (54, 62)},
    ),
    "harp": InstrumentRange(
        "harp", 23, 103, 36, 84,
        register_names={"low": (23, 47), "middle": (48, 72), "high": (73, 103)},
    ),
    "piano": InstrumentRange(
        "piano", 21, 108, 36, 96,
        register_names={"low": (21, 47), "middle": (48, 71), "high": (72, 96), "extreme": (97, 108)},
    ),
    "timpani": InstrumentRange(
        "timpani", 36, 60, 40, 55,
        register_names={"low": (36, 45), "middle": (46, 55), "high": (56, 60)},
    ),
    "marimba": InstrumentRange(
        "marimba", 36, 96, 48, 84,
        register_names={"low": (36, 59), "middle": (60, 79), "high": (80, 96)},
    ),
    "vibraphone": InstrumentRange(
        "vibraphone", 53, 89, 60, 84,
        register_names={"low": (53, 65), "middle": (66, 77), "high": (78, 89)},
    ),
    "xylophone": InstrumentRange(
        "xylophone", 60, 96, 65, 91,
        register_names={"low": (60, 71), "middle": (72, 83), "high": (84, 96)},
    ),
    "glockenspiel": InstrumentRange(
        "glockenspiel", 72, 108, 79, 103,
        register_names={"low": (72, 84), "high": (85, 108)},
    ),
    "celesta": InstrumentRange(
        "celesta", 60, 108, 72, 96,
        register_names={"low": (60, 77), "high": (78, 108)},
    ),
    "choir_soprano": InstrumentRange(
        "choir_soprano", 60, 81, 64, 77,
    ),
    "choir_alto": InstrumentRange(
        "choir_alto", 55, 74, 57, 70,
    ),
    "choir_tenor": InstrumentRange(
        "choir_tenor", 48, 67, 50, 64,
    ),
    "choir_bass": InstrumentRange(
        "choir_bass", 36, 60, 40, 57,
    ),
    "organ": InstrumentRange(
        "organ", 21, 108, 21, 108,
        register_names={"pedal": (21, 47), "manual_low": (48, 71), "manual_high": (72, 108)},
    ),
}


class OrchestrationRules:
    """Validate and assist with orchestral instrument ranges."""

    def validate(self, notes: list[NoteInfo], instrument: str) -> list[OrchestrationWarning]:
        """Check notes against instrument range, return warnings."""
        ir = INSTRUMENTS.get(instrument)
        if ir is None:
            return [OrchestrationWarning(instrument, 0, f"Unknown instrument: {instrument}", "error")]

        warnings: list[OrchestrationWarning] = []
        for n in notes:
            if n.pitch < ir.min_midi:
                warnings.append(OrchestrationWarning(
                    instrument, n.pitch,
                    f"Pitch {n.pitch} below range ({ir.min_midi}–{ir.max_midi})", "error"))
            elif n.pitch > ir.max_midi:
                warnings.append(OrchestrationWarning(
                    instrument, n.pitch,
                    f"Pitch {n.pitch} above range ({ir.min_midi}–{ir.max_midi})", "error"))
            elif n.pitch < ir.comfortable_low:
                warnings.append(OrchestrationWarning(
                    instrument, n.pitch,
                    f"Pitch {n.pitch} in extended low register", "info"))
            elif n.pitch > ir.comfortable_high:
                warnings.append(OrchestrationWarning(
                    instrument, n.pitch,
                    f"Pitch {n.pitch} in extended high register", "info"))
        return warnings

    def clamp_to_range(self, notes: list[NoteInfo], instrument: str) -> list[NoteInfo]:
        """Force notes into instrument's playable range."""
        ir = INSTRUMENTS.get(instrument)
        if ir is None:
            return notes
        return [
            NoteInfo(
                pitch=max(ir.min_midi, min(ir.max_midi, n.pitch)),
                start=n.start, duration=n.duration, velocity=n.velocity,
                articulation=n.articulation, expression=n.expression,
            )
            for n in notes
        ]

    def suggest_octave(self, instrument: str, target_pitch: int) -> int:
        """Return the nearest octave where this pitch class is in comfortable range."""
        ir = INSTRUMENTS.get(instrument)
        if ir is None:
            return target_pitch

        pc = target_pitch % 12
        best = target_pitch
        best_dist = float("inf")
        for octave_offset in range(-3, 4):
            candidate = pc + ((ir.comfortable_low // 12 + octave_offset) * 12)
            if ir.comfortable_low <= candidate <= ir.comfortable_high:
                dist = abs(candidate - target_pitch)
                if dist < best_dist:
                    best_dist = dist
                    best = candidate
        return best

    def register_at(self, instrument: str, midi_pitch: int) -> str:
        """Return register name for a pitch on the given instrument."""
        ir = INSTRUMENTS.get(instrument)
        if ir is None:
            return "unknown"
        for reg_name, (lo, hi) in ir.register_names.items():
            if lo <= midi_pitch <= hi:
                return reg_name
        if midi_pitch < ir.min_midi:
            return "below_range"
        return "above_range"

    def blend_with(self, instrument_a: str, instrument_b: str) -> dict:
        """Analyze range overlap between two instruments for blending."""
        a = INSTRUMENTS.get(instrument_a)
        b = INSTRUMENTS.get(instrument_b)
        if a is None or b is None:
            return {"error": "Unknown instrument"}

        overlap_low = max(a.comfortable_low, b.comfortable_low)
        overlap_high = min(a.comfortable_high, b.comfortable_high)
        overlap = max(0, overlap_high - overlap_low + 1)

        return {
            "instrument_a": instrument_a,
            "instrument_b": instrument_b,
            "a_range": (a.min_midi, a.max_midi),
            "b_range": (b.min_midi, b.max_midi),
            "overlap_range": (overlap_low, overlap_high) if overlap > 0 else None,
            "overlap_semitones": overlap,
            "blend_quality": "strong" if overlap > 24 else "moderate" if overlap > 12 else "weak",
        }
