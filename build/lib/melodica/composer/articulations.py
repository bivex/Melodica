"""
composer/articulations.py — Articulation & modulation engine.

Applies per-note articulations and per-track CC automation:
- Staccato, legato, pizzicato, tremolo, marcato
- Modulation wheel (CC1) for vibrato
- Expression (CC11) for dynamic swells
- Sustain pedal (CC64) for legato connections
- Pitch bend for slides
- Reverb (CC91), Chorus (CC93)
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.types import NoteInfo


# ---------------------------------------------------------------------------
# Articulation profiles per instrument/mood
# ---------------------------------------------------------------------------


@dataclass
class ArticulationProfile:
    """Defines how an instrument should be articulated."""

    name: str
    default_articulation: str = "sustain"
    sustain_pedal_pattern: str = "auto"  # "auto", "always", "never"
    modulation_base: int = 0  # CC1 vibrato base (0-127)
    modulation_curve: str = "none"  # "none", "vibrato_in", "vibrato_out", "tremolo"
    expression_curve: str = "none"  # "none", "crescendo", "decrescendo", "swell", "fade_in"
    reverb_level: int = 64  # CC91 (0-127)
    chorus_level: int = 0  # CC93 (0-127)
    velocity_humanize: int = 5  # random jitter
    duration_factor: float = 1.0  # staccato=0.3, legato=1.2
    pitch_bend_slide: int = 0  # MIDI pitch-bend units at note onset for slide-in effect
                               # (negative = slide up from below, e.g. -2048 ≈ -0.5 semitone)


# Built-in profiles
PROFILES: dict[str, ArticulationProfile] = {
    # Strings
    "strings_melody": ArticulationProfile(
        name="strings_melody",
        default_articulation="sustain",
        modulation_base=40,
        modulation_curve="vibrato_in",
        expression_curve="swell",
        reverb_level=80,
        chorus_level=30,
    ),
    "strings_staccato": ArticulationProfile(
        name="strings_staccato",
        default_articulation="staccato",
        duration_factor=0.3,
        reverb_level=60,
    ),
    "strings_pad": ArticulationProfile(
        name="strings_pad",
        default_articulation="sustain",
        sustain_pedal_pattern="always",
        expression_curve="fade_in",
        reverb_level=100,
        chorus_level=40,
        modulation_base=20,
    ),
    "strings_tremolo": ArticulationProfile(
        name="strings_tremolo",
        default_articulation="tremolo",
        modulation_base=80,
        modulation_curve="tremolo",
        reverb_level=70,
    ),
    "cello": ArticulationProfile(
        name="cello",
        default_articulation="sustain",
        modulation_base=30,
        modulation_curve="vibrato_in",
        expression_curve="crescendo",
        reverb_level=70,
        chorus_level=20,
        pitch_bend_slide=-1500,  # gentle slide up into each note (~-0.37 semitone)
    ),
    # Brass
    "brass_fanfare": ArticulationProfile(
        name="brass_fanfare",
        default_articulation="marcato",
        expression_curve="swell",
        reverb_level=90,
        modulation_base=10,
    ),
    "brass_legato": ArticulationProfile(
        name="brass_legato",
        default_articulation="legato",
        sustain_pedal_pattern="auto",
        expression_curve="crescendo",
        reverb_level=85,
        duration_factor=1.1,
        pitch_bend_slide=-2048,  # subtle slide into legato lines (~-0.5 semitone)
    ),
    # Woodwind
    "harp": ArticulationProfile(
        name="harp",
        default_articulation="staccato",
        duration_factor=0.4,
        reverb_level=100,
        modulation_base=0,
    ),
    "flute": ArticulationProfile(
        name="flute",
        default_articulation="sustain",
        modulation_base=50,
        modulation_curve="vibrato_in",
        expression_curve="swell",
        reverb_level=90,
    ),
    # Percussion
    "timpani": ArticulationProfile(
        name="timpani",
        default_articulation="marcato",
        reverb_level=60,
        velocity_humanize=8,
    ),
    "snare": ArticulationProfile(
        name="snare",
        default_articulation="staccato",
        duration_factor=0.15,
        reverb_level=30,
    ),
    # Choir
    "choir_ah": ArticulationProfile(
        name="choir_ah",
        default_articulation="sustain",
        sustain_pedal_pattern="always",
        expression_curve="swell",
        reverb_level=120,
        chorus_level=60,
        modulation_base=15,
    ),
    # Piano
    "piano": ArticulationProfile(
        name="piano",
        default_articulation="sustain",
        expression_curve="none",
        reverb_level=50,
    ),
}


# ---------------------------------------------------------------------------
# Articulation Engine
# ---------------------------------------------------------------------------


class ArticulationEngine:
    """
    Applies articulations and CC automation to note sequences.

    Takes raw notes and enriches them with:
    - articulation flags
    - CC expression curves
    - sustain pedal events
    - velocity humanization
    """

    def __init__(self, profiles: dict[str, ArticulationProfile] | None = None):
        self.profiles = profiles or PROFILES

    def apply(
        self,
        notes: list[NoteInfo],
        instrument: str,
        total_beats: float,
    ) -> list[NoteInfo]:
        """Apply articulation profile to notes."""
        profile = self.profiles.get(instrument, PROFILES["strings_melody"])
        result = []

        for i, n in enumerate(notes):
            # Build expression dict (CC automation)
            expr: dict[int, int] = {}

            # Expression curve (CC11)
            if profile.expression_curve != "none":
                t = n.start / max(total_beats, 0.1)
                expr[11] = self._expression_value(profile.expression_curve, t)

            # Modulation curve (CC1)
            if profile.modulation_curve != "none":
                t = n.start / max(total_beats, 0.1)
                expr[1] = self._modulation_value(
                    profile.modulation_curve, t, profile.modulation_base
                )

            # Sustain pedal (CC64)
            if profile.sustain_pedal_pattern == "always":
                expr[64] = 127
            elif profile.sustain_pedal_pattern == "auto":
                # Sustain for legato connections
                if i < len(notes) - 1:
                    gap = notes[i + 1].start - (n.start + n.duration)
                    if gap < 0.05:  # legato
                        expr[64] = 127
                    else:
                        expr[64] = 0

            # Reverb & Chorus (CC91, CC93)
            expr[91] = profile.reverb_level
            expr[93] = profile.chorus_level

            # Pitch bend slide-in: apply on non-first notes so the bend resolves naturally
            # when the note starts (the previous note's pitch bend reset handles resolution)
            if profile.pitch_bend_slide != 0 and i > 0:
                expr["pitch_bend"] = profile.pitch_bend_slide

            # Velocity humanize
            vel = n.velocity + random.randint(-profile.velocity_humanize, profile.velocity_humanize)
            vel = max(1, min(127, vel))

            # Duration factor
            dur = n.duration * profile.duration_factor

            result.append(
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=round(dur, 6),
                    velocity=vel,
                    articulation=profile.default_articulation,
                    expression=expr,
                )
            )

        return result

    def _expression_value(self, curve: str, t: float) -> int:
        """CC11 value at position t (0.0-1.0)."""
        match curve:
            case "crescendo":
                return int(40 + t * 87)  # 40 → 127
            case "decrescendo":
                return int(127 - t * 87)  # 127 → 40
            case "swell":
                return int(40 + 87 * (1.0 - abs(2 * t - 1)))  # peak at middle
            case "fade_in":
                return int(20 + min(t * 2, 1.0) * 107)  # 20 → 127 in first half
            case "fade_out":
                return int(127 - max(0, (t - 0.5) * 2) * 107)  # 127 → 20 in second half
            case _:
                return 100

    def _modulation_value(self, curve: str, t: float, base: int) -> int:
        """CC1 value at position t (0.0-1.0)."""
        match curve:
            case "vibrato_in":
                # Start without vibrato, add gradually
                if t < 0.3:
                    return 0
                return int(base * ((t - 0.3) / 0.7))
            case "vibrato_out":
                # Start with vibrato, fade out
                if t > 0.7:
                    return int(base * (1.0 - (t - 0.7) / 0.3))
                return base
            case "tremolo":
                # Oscillating
                import math

                return int(base * (0.5 + 0.5 * math.sin(t * math.pi * 8)))
            case _:
                return base

    def add_sustain_pedal_events(
        self,
        notes: list[NoteInfo],
        total_beats: float,
    ) -> list[dict]:
        """Generate standalone sustain pedal CC64 events for MIDI export."""
        events = []
        pedal_on = False
        for i, n in enumerate(notes):
            if i < len(notes) - 1:
                gap = notes[i + 1].start - (n.start + n.duration)
                if gap < 0.05 and not pedal_on:
                    events.append({"type": "cc64", "value": 127, "time": n.start})
                    pedal_on = True
                elif gap >= 0.05 and pedal_on:
                    events.append({"type": "cc64", "value": 0, "time": n.start + n.duration})
                    pedal_on = False
        if pedal_on:
            events.append({"type": "cc64", "value": 0, "time": total_beats})
        return events
