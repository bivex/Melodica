"""
composer/style_profiles.py — Style conditioning system.

Different musical styles have different norms:
- cadence types
- dissonance tolerance
- chord density
- voice leading strictness
- harmonic rhythm
- allowed chord types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from melodica.types import Quality


@dataclass
class StyleProfile:
    """
    Defines harmonic norms for a musical style.

    cadence_preferences: weights for different cadence types
    dissonance_tolerance: 0.0 = strict, 1.0 = free
    density: preferred chord change rate (chords per bar)
    voice_leading_strict: how strictly to enforce voice leading rules
    allowed_qualities: chord qualities used in this style
    tension_curve: default tension curve type
    repetition_tolerance: how much chord repetition is OK (0=never, 1=always)
    """

    name: str = "pop"
    cadence_preferences: dict[str, float] = field(default_factory=dict)
    dissonance_tolerance: float = 0.5
    density: float = 1.0  # chords per bar
    voice_leading_strict: bool = False
    allowed_qualities: list[Quality] = field(default_factory=list)
    tension_curve: str = "classical"
    repetition_tolerance: float = 0.3
    secondary_dominants: bool = False
    modal_interchange: bool = False
    extensions: bool = False


# Built-in style profiles
STYLES: dict[str, StyleProfile] = {
    "baroque": StyleProfile(
        name="baroque",
        cadence_preferences={
            "authentic": 0.8,  # V → I
            "plagal": 0.3,  # IV → I
            "deceptive": 0.2,  # V → vi
            "half": 0.5,  # ? → V
        },
        dissonance_tolerance=0.4,
        density=1.0,
        voice_leading_strict=True,
        allowed_qualities=[Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED],
        tension_curve="classical",
        repetition_tolerance=0.1,
        secondary_dominants=True,
        modal_interchange=False,
        extensions=False,
    ),
    "classical": StyleProfile(
        name="classical",
        cadence_preferences={
            "authentic": 0.9,
            "plagal": 0.4,
            "deceptive": 0.3,
            "half": 0.6,
        },
        dissonance_tolerance=0.3,
        density=1.0,
        voice_leading_strict=True,
        allowed_qualities=[Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED, Quality.DOMINANT7],
        tension_curve="classical",
        repetition_tolerance=0.15,
        secondary_dominants=True,
        modal_interchange=False,
        extensions=False,
    ),
    "pop": StyleProfile(
        name="pop",
        cadence_preferences={
            "authentic": 0.7,
            "plagal": 0.6,  # IV → I is common in pop
            "deceptive": 0.3,
            "half": 0.4,
        },
        dissonance_tolerance=0.6,
        density=1.0,
        voice_leading_strict=False,
        allowed_qualities=[
            Quality.MAJOR,
            Quality.MINOR,
            Quality.MAJOR7,
            Quality.MINOR7,
            Quality.DOMINANT7,
        ],
        tension_curve="build_release",
        repetition_tolerance=0.5,
        secondary_dominants=False,
        modal_interchange=True,
        extensions=True,
    ),
    "jazz": StyleProfile(
        name="jazz",
        cadence_preferences={
            "authentic": 0.6,
            "plagal": 0.3,
            "deceptive": 0.5,
            "half": 0.5,
            "tritone_sub": 0.7,  # bII7 → I
        },
        dissonance_tolerance=0.8,
        density=2.0,
        voice_leading_strict=False,
        allowed_qualities=[
            Quality.MAJOR7,
            Quality.MINOR7,
            Quality.DOMINANT7,
            Quality.HALF_DIM7,
            Quality.FULL_DIM7,
            Quality.MINOR,
            Quality.MAJOR,
        ],
        tension_curve="classical",
        repetition_tolerance=0.2,
        secondary_dominants=True,
        modal_interchange=True,
        extensions=True,
    ),
    "cinematic": StyleProfile(
        name="cinematic",
        cadence_preferences={
            "authentic": 0.5,
            "plagal": 0.4,
            "deceptive": 0.6,
            "half": 0.5,
        },
        dissonance_tolerance=0.7,
        density=0.5,
        voice_leading_strict=False,
        allowed_qualities=[Quality.MAJOR, Quality.MINOR, Quality.MAJOR7, Quality.MINOR7],
        tension_curve="classical",
        repetition_tolerance=0.4,
        secondary_dominants=False,
        modal_interchange=True,
        extensions=True,
    ),
    "edm": StyleProfile(
        name="edm",
        cadence_preferences={
            "authentic": 0.5,
            "plagal": 0.3,
            "deceptive": 0.2,
            "half": 0.4,
        },
        dissonance_tolerance=0.5,
        density=0.5,
        voice_leading_strict=False,
        allowed_qualities=[Quality.MAJOR, Quality.MINOR, Quality.SUS2, Quality.SUS4],
        tension_curve="edm",
        repetition_tolerance=0.7,
        secondary_dominants=False,
        modal_interchange=False,
        extensions=False,
    ),
}


def get_style(name: str) -> StyleProfile:
    """Get a style profile by name."""
    if name in STYLES:
        return STYLES[name]
    return STYLES["pop"]
