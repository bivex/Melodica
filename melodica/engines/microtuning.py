# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
microtuning.py — Microtonal pitch quantization and pitch-bend rendering.

Converts fractional MIDI pitches into integer NoteInfo with pitch_bend expression
data, enabling microtonal scales (quarter-tone, Arabic, custom) within standard MIDI.
"""

from __future__ import annotations

from melodica.types import NoteInfo, Scale


# Default pitch bend range in semitones (most synths default to ±2)
DEFAULT_BEND_RANGE = 2


class MicrotuningEngine:
    """Quantize fractional pitches to microtonal scales via pitch bend."""

    def __init__(self, bend_range: int = DEFAULT_BEND_RANGE) -> None:
        self.bend_range = bend_range

    def _cents_to_bend(self, cents: float) -> int:
        """Convert cents deviation to MIDI pitch bend value.

        pitch_bend_range semitones = ±8192 units.
        1 cent = 8192 / (bend_range * 100) units.
        """
        return max(-8192, min(8191, int(cents * (8192.0 / (self.bend_range * 100)))))

    def snap_to_scale(self, pitch: float, scale: Scale) -> float:
        """Snap a fractional pitch to the nearest scale degree.

        Returns the snapped pitch as a float (may be fractional for microtonal scales).
        """
        intervals = scale.intervals()
        root_pc = scale.root % 12

        # Build all pitch classes in one octave from scale intervals
        scale_pcs = [(root_pc + iv) % 12.0 for iv in intervals]

        # Find nearest scale degree across surrounding octaves
        octave = int(pitch) // 12
        base_pc = pitch - octave * 12

        best = base_pc
        best_dist = float("inf")
        for oct_offset in range(-1, 2):
            for pc in scale_pcs:
                candidate = pc + (octave + oct_offset) * 12
                dist = abs(pitch - candidate)
                if dist < best_dist:
                    best_dist = dist
                    best = candidate
        return best

    def quantize_pitch(self, pitch: float, scale: Scale) -> tuple[int, dict]:
        """Snap float pitch to nearest scale degree, return (midi_int, expression_dict).

        The expression dict contains a "pitch_bend" key with the deviation curve.
        """
        snapped = self.snap_to_scale(pitch, scale)
        midi_int = int(round(snapped))
        midi_int = max(0, min(127, midi_int))

        deviation_cents = (snapped - midi_int) * 100.0
        if abs(deviation_cents) < 1.0:
            return midi_int, {}

        bend_val = self._cents_to_bend(deviation_cents)
        return midi_int, {"pitch_bend": [(0.0, bend_val)]}

    def render_microtonal_note(
        self,
        pitch: float,
        start: float,
        duration: float,
        velocity: int,
        scale: Scale,
    ) -> NoteInfo:
        """Create a NoteInfo with pitch_bend expression for a microtonal pitch."""
        midi_int, expr = self.quantize_pitch(pitch, scale)
        return NoteInfo(
            pitch=midi_int,
            start=start,
            duration=duration,
            velocity=velocity,
            expression=expr,
        )

    def wrap_notes(self, notes: list[NoteInfo], scale: Scale) -> list[NoteInfo]:
        """Apply microtonal quantization to all notes in a list."""
        result: list[NoteInfo] = []
        for n in notes:
            _, expr = self.quantize_pitch(float(n.pitch), scale)
            merged_expr = {**n.expression, **expr}
            result.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity,
                articulation=n.articulation,
                expression=merged_expr,
            ))
        return result
