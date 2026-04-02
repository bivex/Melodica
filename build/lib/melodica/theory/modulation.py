# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo


# ---------------------------------------------------------------------------
# Articulation definitions — all parameters visible, no magic
# ---------------------------------------------------------------------------

@dataclass
class ArticulationProfile:
    """
    Describes how one playing technique sounds and is controlled.

    Every field is a MIDI value (0-127) or a simple string — no hidden math.
    Create your own profiles for custom libraries.
    """
    # --- CC1: Dynamic Layer (sample library layer select) ---
    # Low = soft/quiet timbral layer, High = loud/bright layer.
    # Interpolated across the phrase: starts at cc1_lo, ends at cc1_hi.
    cc1_lo: int = 64
    cc1_hi: int = 64

    # --- CC11: Expression Shape (phrase breathing) ---
    # "ramp"  — grows from quiet to loud (good for crescendo intros)
    # "arc"   — rises then falls, like a bow stroke or breath
    # "spike" — strong attack then fades (good for accents)
    # "flat"  — constant level
    cc11_shape: str = "flat"

    # --- CC3: Vibrato ---
    # If True, notes longer than vibrato_threshold_beats get vibrato.
    vibrato: bool = False
    vibrato_depth: int = 0        # 0-127 (CC3 value)
    vibrato_threshold_beats: float = 1.0  # only on notes longer than this

    # --- CC74: Brightness / Filter Cutoff ---
    # Higher = brighter timbre. 64 = neutral.
    brightness: int = 64

    # --- Note shaping ---
    staccato_length: float | None = None   # if set, caps note duration
    velocity_boost: int = 0                # added to every note velocity
    legato_overlap: float = 0.0            # seconds of overlap for legato transition


# Built-in profiles for standard orchestral articulations.
# Override or extend via ARTICULATION_PROFILES["my_technique"] = ArticulationProfile(...)
ARTICULATION_PROFILES: dict[str, ArticulationProfile] = {
    "sustain": ArticulationProfile(
        cc1_lo=35, cc1_hi=65, cc11_shape="ramp",
        vibrato=True, vibrato_depth=50, brightness=40,
    ),
    "legato": ArticulationProfile(
        cc1_lo=75, cc1_hi=95, cc11_shape="arc",
        vibrato=True, vibrato_depth=70, brightness=55,
        legato_overlap=0.05,
    ),
    "staccato": ArticulationProfile(
        cc1_lo=55, cc1_hi=55, cc11_shape="flat",
        brightness=100, staccato_length=0.25,
    ),
    "marcato": ArticulationProfile(
        cc1_lo=110, cc1_hi=120, cc11_shape="spike",
        brightness=115, velocity_boost=20,
    ),
    "pizzicato": ArticulationProfile(
        cc1_lo=50, cc1_hi=50, cc11_shape="flat",
        brightness=90, staccato_length=0.25,
    ),
    "tremolo": ArticulationProfile(
        cc1_lo=80, cc1_hi=100, cc11_shape="flat",
        brightness=78,
    ),
    "spiccato": ArticulationProfile(
        cc1_lo=60, cc1_hi=60, cc11_shape="flat",
        brightness=95, staccato_length=0.2,
    ),
}

# Keyswitch pitches — one per articulation name.
# Convention: octave -1 (MIDI 0-11), close to Spitfire/BBCSO/OT.
# Override for your library: ARTICULATION_KEYSWITCHES["sustain"] = 24
ARTICULATION_KEYSWITCHES: dict[str, int] = {
    "sustain":   0,   # C-1
    "staccato":  1,   # C#-1
    "marcato":   2,   # D-1
    "legato":    3,   # D#-1
    "pizzicato": 4,   # E-1
    "tremolo":   5,   # F-1
    "spiccato":  6,   # F#-1
}

class ModulationEngine:
    """
    Handles smooth transitions between different keys and modes.
    Implements Pivot Chord and Common Tone logic.
    """

    @staticmethod
    def find_pivot_chords(scale_a: Scale, scale_b: Scale) -> List[Tuple[ChordLabel, int, int]]:
        """
        Find chords that exist in both scales.
        Returns list of (ChordLabel, degree_in_a, degree_in_b).
        """
        pivots = []
        # Check all degrees of scale_a (1-7 usually)
        degs_a = len(scale_a.degrees())
        degs_b = len(scale_b.degrees())
        
        for deg_a in range(1, degs_a + 1):
            chord_a = scale_a.diatonic_chord(deg_a)
            for deg_b in range(1, degs_b + 1):
                chord_b = scale_b.diatonic_chord(deg_b)
                
                # Check if same root pitch class and same quality
                if abs(chord_a.root - chord_b.root) < 0.01 and chord_a.quality == chord_b.quality:
                    pivots.append((chord_a, deg_a, deg_b))
        return pivots

    @staticmethod
    def generate_transition_progression(scale_a: Scale, scale_b: Scale) -> str:
        """
        Creates a string progression that smoothly leads from A to B.
        Example: I -> IV -> [Pivot] -> V(of B) -> I(of B)
        """
        pivots = ModulationEngine.find_pivot_chords(scale_a, scale_b)
        
        if pivots:
            # Use the first pivot chord found
            chord, d_a, d_b = pivots[0]
            # Simple 3-chord cadence: Pivot -> V_of_B -> I_of_B
            # We assume a standard V-I in the target scale for resolution
            return f"[{chord.quality.name} on {d_a}] V I"
        else:
            # Fallback to direct modulation via Dominant of B
            return "V I" # Relative to scale_B


def _cc11_value(shape: str, progress: float) -> int:
    """Compute CC11 at a point within a phrase (0.0 = start, 1.0 = end)."""
    if shape == "arc":
        return max(25, int(120 * 4 * progress * (1.0 - progress)))
    if shape == "ramp":
        return int(30 + 70 * progress)
    if shape == "spike":
        return max(60, int(127 - 67 * progress))
    return 90  # "flat"


def apply_articulation(
    notes: list[NoteInfo],
    articulation: str | ArticulationProfile,
    *,
    phrase_duration: float | None = None,
) -> list[NoteInfo]:
    """
    Apply an articulation to a list of notes.

    Parameters
    ----------
    notes : list[NoteInfo]
        The notes to shape.
    articulation : str or ArticulationProfile
        Either a name like "legato" (looked up in ARTICULATION_PROFILES)
        or an ArticulationProfile directly for full control.
    phrase_duration : float, optional
        Total phrase length in beats. If None, derived from note positions.

    What it does (no hidden side effects):
      - Sets each note's ``articulation`` tag
      - Writes CC1, CC11, CC3, CC74 into ``note.expression`` dict
      - Optionally caps duration (staccato), adds overlap (legato),
        or boosts velocity (marcato)

    Returns the same list (mutated in-place for performance).
    """
    if not notes:
        return notes

    # Resolve profile
    if isinstance(articulation, ArticulationProfile):
        profile = articulation
        art_name = "custom"
    else:
        profile = ARTICULATION_PROFILES.get(articulation)
        art_name = articulation
        if profile is None:
            # Unknown articulation — just tag it, no CC changes
            for n in notes:
                n.articulation = art_name
            return notes

    # Phrase duration for progress calculation
    if phrase_duration and phrase_duration > 0:
        total = phrase_duration
    else:
        total = max((n.start + n.duration for n in notes), default=1.0)
    total = max(total, 0.001)

    for n in notes:
        n.articulation = art_name
        p = max(0.0, min(1.0, n.start / total))

        # --- Duration / velocity shaping ---
        if profile.staccato_length is not None:
            n.duration = min(n.duration, profile.staccato_length)
        if profile.velocity_boost:
            n.velocity = min(127, n.velocity + profile.velocity_boost)
        if profile.legato_overlap > 0:
            n.duration += profile.legato_overlap

        # --- CC1: dynamic layer (interpolated across phrase) ---
        n.expression[1] = int(profile.cc1_lo + (profile.cc1_hi - profile.cc1_lo) * p)

        # --- CC11: expression shape ---
        n.expression[11] = _cc11_value(profile.cc11_shape, p)

        # --- CC3: vibrato on long notes ---
        if profile.vibrato and n.duration > profile.vibrato_threshold_beats:
            n.expression[3] = profile.vibrato_depth

        # --- CC74: brightness ---
        n.expression[74] = profile.brightness

    return notes
