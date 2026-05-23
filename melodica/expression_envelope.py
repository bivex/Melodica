# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
expression_envelope.py — Per-note MPE expression envelope generator.

Generates ADSR-shaped CC curves for per-note expression (CC11), timbre (CC74),
and vibrato (CC1) that can be attached to NoteInfo.expression dicts.

These curves leverage the per-note channel allocation already present in midi.py
to give each note independent expression control — the core of MPE.

Usage:
    from melodica.expression_envelope import MPEEnvelope

    env = MPEEnvelope(attack=0.1, decay=0.05, sustain_level=0.85, release=0.15)
    note.expression.update(env.to_cc11(note.duration))
    note.expression.update(env.to_cc74(note.duration, brightness=0.7))
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class MPEEnvelope:
    """ADSR envelope for per-note MPE expression curves."""

    attack: float = 0.1   # Fraction of note duration (0.0-1.0)
    decay: float = 0.05   # Fraction of note duration
    sustain_level: float = 0.85  # 0.0-1.0 sustain level
    release: float = 0.15  # Fraction of note duration

    def _adsr_points(self, duration: float, steps: int, base_val: int, peak_val: int) -> list[tuple[float, int]]:
        """Generate (relative_time, cc_value) points following ADSR shape."""
        if duration < 0.1 or steps < 2:
            return []

        attack_end = self.attack * duration
        decay_end = attack_end + self.decay * duration
        release_start = duration - self.release * duration
        sustain_val = base_val + (peak_val - base_val) * self.sustain_level

        points = []
        for i in range(steps + 1):
            t = (i / steps) * duration
            if t <= attack_end and attack_end > 0:
                # Attack: ramp up
                frac = t / attack_end
                val = base_val + (peak_val - base_val) * frac
            elif t <= decay_end and decay_end > attack_end:
                # Decay: settle to sustain
                frac = (t - attack_end) / (decay_end - attack_end)
                val = peak_val + (sustain_val - peak_val) * frac
            elif t < release_start:
                # Sustain: hold
                val = sustain_val
            else:
                # Release: fade out
                release_dur = duration - release_start
                if release_dur > 0:
                    frac = (t - release_start) / release_dur
                    val = sustain_val + (base_val * 0.3 - sustain_val) * frac
                else:
                    val = sustain_val

            points.append((round(t, 4), max(0, min(127, int(val)))))

        return points

    def to_cc11(self, duration: float, steps_per_beat: int = 4) -> dict[int, list[tuple[float, int]]]:
        """Generate CC11 (Expression) ADSR curve as expression dict entry."""
        steps = max(4, int(duration * steps_per_beat))
        points = self._adsr_points(duration, steps, base_val=40, peak_val=110)
        return {11: points} if points else {}

    def to_cc74(self, duration: float, brightness: float = 0.7, steps_per_beat: int = 4) -> dict[int, list[tuple[float, int]]]:
        """Generate CC74 (Timbre/Brightness) curve.

        brightness: 0.0 = dark/muted, 1.0 = bright/harsh
        """
        steps = max(4, int(duration * steps_per_beat))
        base = int(30 + 40 * brightness)
        peak = int(70 + 57 * brightness)
        points = self._adsr_points(duration, steps, base_val=base, peak_val=peak)
        return {74: points} if points else {}

    def to_cc1_vibrato(self, duration: float, depth: float = 0.3, rate: float = 5.5,
                       delay: float = 0.15, steps_per_beat: int = 8) -> dict[int, list[tuple[float, int]]]:
        """Generate CC1 (Modulation/Vibrato) with delayed onset.

        depth: 0.0-1.0 vibrato intensity
        rate: cycles per second
        delay: fraction of note before vibrato starts
        """
        if duration < 0.3 or depth < 0.05:
            return {}

        steps = max(6, int(duration * steps_per_beat))
        delay_time = delay * duration
        amplitude = depth * 40  # Max swing in CC value

        points = []
        for i in range(steps + 1):
            t = (i / steps) * duration
            if t < delay_time:
                val = 0
            else:
                t_active = t - delay_time
                ramp = min(1.0, t_active / 0.5)  # Ramp up over 0.5 beats
                phase = t_active * 2.0 * math.pi * rate
                val = int(ramp * amplitude * (0.5 + 0.5 * math.sin(phase)))

            points.append((round(t, 4), max(0, min(127, val))))

        return {1: points} if points else {}

    def to_pitch_bend_vibrato(self, duration: float, cents: float = 15.0, rate: float = 5.5,
                               delay: float = 0.2, steps_per_beat: int = 8) -> dict[str, list[tuple[float, int]]]:
        """Generate per-note pitch bend vibrato curve.

        cents: peak deviation in cents (e.g., 15 = gentle vibrato)
        rate: cycles per second
        delay: fraction of note before vibrato starts
        """
        if duration < 0.3 or abs(cents) < 1.0:
            return {}

        steps = max(6, int(duration * steps_per_beat))
        delay_time = delay * duration
        # 8192 = full range in ±2 semitones; 1 semitone = 100 cents
        # bend_per_cent = 8192 / (200) = ~41
        amplitude = cents * 41.0

        points = []
        for i in range(steps + 1):
            t = (i / steps) * duration
            if t < delay_time:
                val = 0
            else:
                t_active = t - delay_time
                ramp = min(1.0, t_active / 0.5)
                phase = t_active * 2.0 * math.pi * rate
                val = int(ramp * amplitude * math.sin(phase))

            points.append((round(t, 4), max(-8192, min(8191, val))))

        return {"pitch_bend": points} if points else {}


def mpe_expression_for_instrument(instrument: str, duration: float, velocity: int = 80) -> dict:
    """Generate appropriate MPE expression curves for a given instrument type.

    Returns a dict suitable for merging into NoteInfo.expression.
    """
    env = _instrument_envelope(instrument, velocity)
    expr: dict = {}
    expr.update(env.to_cc11(duration))

    brightness = _instrument_brightness(instrument)
    if duration > 0.5:
        expr.update(env.to_cc74(duration, brightness=brightness))

    # Vibrato for sustained instruments
    if _has_vibrato(instrument) and duration > 0.8:
        rate = _vibrato_rate(instrument)
        depth = _vibrato_depth(instrument)
        if velocity > 60:
            depth *= min(1.0, velocity / 100.0)
        expr.update(env.to_cc1_vibrato(duration, depth=depth, rate=rate))

    return expr


def _instrument_envelope(instrument: str, velocity: int = 80) -> MPEEnvelope:
    """Return appropriate ADSR envelope for instrument type."""
    vel_factor = min(1.0, velocity / 100.0)

    envelopes = {
        "strings": MPEEnvelope(attack=0.15, decay=0.05, sustain_level=0.85, release=0.2),
        "violin": MPEEnvelope(attack=0.08, decay=0.03, sustain_level=0.9, release=0.15),
        "viola": MPEEnvelope(attack=0.1, decay=0.04, sustain_level=0.85, release=0.18),
        "cello": MPEEnvelope(attack=0.12, decay=0.04, sustain_level=0.88, release=0.2),
        "contrabass": MPEEnvelope(attack=0.2, decay=0.06, sustain_level=0.8, release=0.25),
        "choir": MPEEnvelope(attack=0.2, decay=0.08, sustain_level=0.82, release=0.3),
        "french_horn": MPEEnvelope(attack=0.18, decay=0.06, sustain_level=0.85, release=0.25),
        "trumpet": MPEEnvelope(attack=0.03, decay=0.05, sustain_level=0.8, release=0.1),
        "trombone": MPEEnvelope(attack=0.08, decay=0.05, sustain_level=0.82, release=0.15),
        "brass": MPEEnvelope(attack=0.06, decay=0.05, sustain_level=0.85, release=0.15),
        "oboe": MPEEnvelope(attack=0.04, decay=0.06, sustain_level=0.78, release=0.1),
        "bassoon": MPEEnvelope(attack=0.1, decay=0.06, sustain_level=0.75, release=0.15),
        "flute": MPEEnvelope(attack=0.08, decay=0.04, sustain_level=0.85, release=0.15),
        "harp": MPEEnvelope(attack=0.02, decay=0.3, sustain_level=0.3, release=0.4),
        "piano": MPEEnvelope(attack=0.01, decay=0.4, sustain_level=0.2, release=0.3),
        "timpani": MPEEnvelope(attack=0.01, decay=0.5, sustain_level=0.1, release=0.3),
    }

    env = envelopes.get(instrument, MPEEnvelope())
    # Brighter attacks for louder notes
    env.sustain_level = min(1.0, env.sustain_level * (0.85 + 0.15 * vel_factor))
    return env


def _instrument_brightness(instrument: str) -> float:
    """Return brightness factor (0.0-1.0) for CC74 curves."""
    brightness = {
        "violin": 0.75, "viola": 0.65, "cello": 0.55, "contrabass": 0.35,
        "strings": 0.6, "choir": 0.5, "french_horn": 0.45, "trumpet": 0.85,
        "trombone": 0.65, "brass": 0.7, "oboe": 0.8, "bassoon": 0.4,
        "flute": 0.7, "harp": 0.8, "piano": 0.75, "timpani": 0.3,
    }
    return brightness.get(instrument, 0.6)


def _has_vibrato(instrument: str) -> bool:
    """Whether this instrument typically uses vibrato."""
    return instrument in (
        "violin", "viola", "cello", "flute", "oboe", "bassoon",
        "choir", "french_horn", "trumpet", "trombone", "brass",
    )


def _vibrato_rate(instrument: str) -> float:
    """Typical vibrato rate in Hz for instrument."""
    rates = {
        "violin": 6.0, "viola": 5.5, "cello": 5.0, "contrabass": 4.0,
        "flute": 5.0, "oboe": 5.5, "bassoon": 4.5,
        "choir": 5.5, "french_horn": 4.5, "trumpet": 5.5,
        "trombone": 5.0, "brass": 5.0,
    }
    return rates.get(instrument, 5.5)


def _vibrato_depth(instrument: str) -> float:
    """Typical vibrato depth (0.0-1.0) for instrument."""
    depths = {
        "violin": 0.4, "viola": 0.35, "cello": 0.3, "contrabass": 0.15,
        "flute": 0.25, "oboe": 0.3, "bassoon": 0.2,
        "choir": 0.25, "french_horn": 0.2, "trumpet": 0.15,
        "trombone": 0.2, "brass": 0.2,
    }
    return depths.get(instrument, 0.25)
