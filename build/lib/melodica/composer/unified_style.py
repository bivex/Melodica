"""
composer/unified_style.py — Unified style system.

Layer: Domain
Style: All styles — single source of truth for musical style.

Merges StyleProfile (harmonic behavior) and Style (instrumentation/progressions)
into a single unified system. One style controls everything:
  - Harmonic rules (cadences, dissonance, extensions)
  - Instrumentation (track mapping, MIDI programs)
  - Progressions (chord sequences per section)
  - Rhythm behavior (Markov style, density, syncopation)
  - Melody behavior (step/leap ratio, contour preferences)
  - Performance (articulation, dynamics)

Usage:
    style = get_unified_style("cinematic")
    # style.harmony.dissonance_tolerance → 0.5
    # style.instrumentation["Lead"] → 48
    # style.rhythm.markov_style → "straight"
    # style.melody.steps_probability → 0.85
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.types import Quality, Scale, Mode


# ---------------------------------------------------------------------------
# Sub-profiles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class HarmonyProfile:
    """Harmonic behavior rules."""

    dissonance_tolerance: float = 0.5
    allowed_qualities: tuple[Quality, ...] = (
        Quality.MAJOR,
        Quality.MINOR,
        Quality.DIMINISHED,
        Quality.DOMINANT7,
    )
    secondary_dominants: bool = False
    modal_interchange: bool = False
    extensions: bool = False
    cadence_strength: float = 0.7  # how strongly cadences are enforced
    voice_leading_strict: bool = False
    density: float = 1.0  # chords per bar


@dataclass(frozen=True)
class MelodyProfile:
    """Melodic behavior rules."""

    steps_probability: float = 0.85
    harmony_note_probability: float = 0.64
    note_repetition_probability: float = 0.14
    direction_bias: float = 0.0  # -1 descending, +1 ascending
    register_low: int = 55
    register_high: int = 84
    avoid_notes: bool = False  # use avoid-note logic
    guide_tones: bool = False  # emphasise 3rds and 7ths
    climax_position: float = 0.6  # 0-1, where in phrase the climax is


@dataclass(frozen=True)
class RhythmProfile:
    """Rhythmic behavior rules."""

    markov_style: str = "straight"  # for MarkovRhythmGenerator
    syncopation: float = 0.15
    density: float = 0.5
    gate: float = 0.9
    phrase_length: int = 8


@dataclass(frozen=True)
class InstrumentationProfile:
    """Track-to-instrument mapping."""

    track_mapping: dict[str, str] = field(default_factory=dict)
    instrument_mapping: dict[str, int] = field(default_factory=dict)
    allowed_scales: list[Scale] = field(default_factory=list)
    typical_bpm: float = 120.0


# ---------------------------------------------------------------------------
# Unified Style
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class UnifiedStyle:
    """
    Complete musical style: harmony + melody + rhythm + instrumentation.

    This is the single source of truth for how music should sound.
    All generators and composers read from this style.
    """

    name: str
    harmony: HarmonyProfile = field(default_factory=HarmonyProfile)
    melody: MelodyProfile = field(default_factory=MelodyProfile)
    rhythm: RhythmProfile = field(default_factory=RhythmProfile)
    instrumentation: InstrumentationProfile = field(default_factory=InstrumentationProfile)
    tension_curve: str = "classical"
    progressions: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Built-in styles
# ---------------------------------------------------------------------------

_UNIFIED_STYLES: dict[str, UnifiedStyle] = {}

# Baroque
_UNIFIED_STYLES["baroque"] = UnifiedStyle(
    name="baroque",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.4,
        allowed_qualities=(
            Quality.MAJOR,
            Quality.MINOR,
            Quality.DIMINISHED,
        ),
        secondary_dominants=True,
        voice_leading_strict=True,
        density=1.0,
        cadence_strength=0.9,
    ),
    melody=MelodyProfile(
        steps_probability=0.90,
        harmony_note_probability=0.70,
        note_repetition_probability=0.08,
        register_low=55,
        register_high=84,
    ),
    rhythm=RhythmProfile(
        markov_style="straight",
        syncopation=0.05,
        density=0.6,
        phrase_length=8,
    ),
    tension_curve="classical",
)

# Classical
_UNIFIED_STYLES["classical"] = UnifiedStyle(
    name="classical",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.3,
        allowed_qualities=(
            Quality.MAJOR,
            Quality.MINOR,
            Quality.DIMINISHED,
            Quality.DOMINANT7,
        ),
        secondary_dominants=True,
        voice_leading_strict=True,
        density=1.0,
        cadence_strength=0.9,
    ),
    melody=MelodyProfile(
        steps_probability=0.87,
        harmony_note_probability=0.68,
        note_repetition_probability=0.10,
        register_low=55,
        register_high=84,
    ),
    rhythm=RhythmProfile(
        markov_style="straight",
        syncopation=0.08,
        density=0.55,
        phrase_length=8,
    ),
    tension_curve="classical",
)

# Pop
_UNIFIED_STYLES["pop"] = UnifiedStyle(
    name="pop",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.5,
        allowed_qualities=(
            Quality.MAJOR,
            Quality.MINOR,
            Quality.DOMINANT7,
            Quality.MAJOR7,
            Quality.MINOR7,
        ),
        secondary_dominants=True,
        extensions=True,
        density=1.0,
        cadence_strength=0.5,
    ),
    melody=MelodyProfile(
        steps_probability=0.82,
        harmony_note_probability=0.60,
        note_repetition_probability=0.20,
        register_low=50,
        register_high=82,
    ),
    rhythm=RhythmProfile(
        markov_style="straight",
        syncopation=0.20,
        density=0.55,
        phrase_length=4,
    ),
    tension_curve="build_release",
)

# Jazz
_UNIFIED_STYLES["jazz"] = UnifiedStyle(
    name="jazz",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.8,
        allowed_qualities=(
            Quality.MAJOR7,
            Quality.MINOR7,
            Quality.DOMINANT7,
            Quality.HALF_DIM7,
            Quality.DIMINISHED,
            Quality.AUGMENTED,
        ),
        secondary_dominants=True,
        modal_interchange=True,
        extensions=True,
        density=1.0,
        cadence_strength=0.6,
    ),
    melody=MelodyProfile(
        steps_probability=0.70,
        harmony_note_probability=0.55,
        note_repetition_probability=0.10,
        register_low=48,
        register_high=88,
        avoid_notes=True,
        guide_tones=True,
    ),
    rhythm=RhythmProfile(
        markov_style="swing",
        syncopation=0.40,
        density=0.65,
        phrase_length=8,
    ),
    tension_curve="build_release",
)

# Cinematic
_UNIFIED_STYLES["cinematic"] = UnifiedStyle(
    name="cinematic",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.5,
        allowed_qualities=(
            Quality.MAJOR,
            Quality.MINOR,
            Quality.DOMINANT7,
            Quality.MAJOR7,
            Quality.MINOR7,
            Quality.DIMINISHED,
        ),
        secondary_dominants=True,
        modal_interchange=True,
        extensions=True,
        density=0.5,
        cadence_strength=0.4,
    ),
    melody=MelodyProfile(
        steps_probability=0.85,
        harmony_note_probability=0.64,
        note_repetition_probability=0.14,
        register_low=48,
        register_high=88,
    ),
    rhythm=RhythmProfile(
        markov_style="ballad",
        syncopation=0.10,
        density=0.4,
        phrase_length=8,
    ),
    tension_curve="classical",
)

# EDM
_UNIFIED_STYLES["edm"] = UnifiedStyle(
    name="edm",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.6,
        allowed_qualities=(
            Quality.MAJOR,
            Quality.MINOR,
            Quality.DOMINANT7,
            Quality.SUS2,
            Quality.SUS4,
        ),
        extensions=True,
        density=0.5,
        cadence_strength=0.2,
    ),
    melody=MelodyProfile(
        steps_probability=0.75,
        harmony_note_probability=0.50,
        note_repetition_probability=0.30,
        register_low=48,
        register_high=84,
    ),
    rhythm=RhythmProfile(
        markov_style="driving",
        syncopation=0.15,
        density=0.7,
        phrase_length=4,
    ),
    tension_curve="edm",
)

# Ambient
_UNIFIED_STYLES["ambient"] = UnifiedStyle(
    name="ambient",
    harmony=HarmonyProfile(
        dissonance_tolerance=0.6,
        allowed_qualities=(
            Quality.MAJOR7,
            Quality.MINOR7,
            Quality.MAJOR,
            Quality.MINOR,
            Quality.SUS2,
            Quality.SUS4,
        ),
        extensions=True,
        density=0.25,
        cadence_strength=0.1,
    ),
    melody=MelodyProfile(
        steps_probability=0.92,
        harmony_note_probability=0.70,
        note_repetition_probability=0.25,
        register_low=48,
        register_high=84,
    ),
    rhythm=RhythmProfile(
        markov_style="ballad",
        syncopation=0.02,
        density=0.2,
        phrase_length=16,
    ),
    tension_curve="ambient",
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def get_unified_style(name: str) -> UnifiedStyle:
    """Get a unified style by name. Returns 'pop' as fallback."""
    return _UNIFIED_STYLES.get(name.lower(), _UNIFIED_STYLES["pop"])


def list_styles() -> list[str]:
    """List all available unified style names."""
    return sorted(_UNIFIED_STYLES.keys())


def register_style(style: UnifiedStyle) -> None:
    """Register a custom unified style."""
    _UNIFIED_STYLES[style.name.lower()] = style
