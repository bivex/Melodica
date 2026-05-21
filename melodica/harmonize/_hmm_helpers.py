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

"""
_hmm_helpers.py — Shared helpers and constants for harmonizers.
"""

from __future__ import annotations

import heapq
import math
from dataclasses import dataclass, field

from melodica.types import ChordLabel, Quality, HarmonicFunction, Scale, Mode, NoteInfo

def _chord_pcs_for_degree(root_pc: int, quality: Quality) -> list[int]:
    """Get pitch classes for a chord given its root pitch class and quality."""
    if quality == Quality.MAJOR:
        return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12]
    elif quality == Quality.MINOR:
        return [root_pc, (root_pc + 3) % 12, (root_pc + 7) % 12]
    elif quality == Quality.DIMINISHED:
        return [root_pc, (root_pc + 3) % 12, (root_pc + 6) % 12]
    elif quality == Quality.DOMINANT7:
        return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12, (root_pc + 10) % 12]
    elif quality == Quality.MAJOR7:
        return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12, (root_pc + 11) % 12]
    elif quality == Quality.MINOR7:
        return [root_pc, (root_pc + 3) % 12, (root_pc + 7) % 12, (root_pc + 10) % 12]
    return [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12]
def _voice_leading_cost(pcs_a: list[int], pcs_b: list[int]) -> float:
    """Minimal voice leading distance between two chord pitch-class sets."""
    if not pcs_a or not pcs_b:
        return 6.0
    # For each pc in A, find closest in B
    total = 0.0
    for a in pcs_a:
        best = min(abs(a - b) % 12 for b in pcs_b)
        # Also check wrapping (e.g., 11→0 is distance 1)
        best = min(best, 12 - best)
        total += best
    return total / len(pcs_a)
def _melody_fits_chord(melody_pc: int, chord_pcs: list[int]) -> bool:
    """Check if melody note fits chord."""
    return melody_pc in chord_pcs
def _build_diatonic_chords(scale: Scale) -> list[tuple[int, Quality]]:
    """Build all diatonic chords for a scale."""
    degs = scale.degrees()
    result = []
    for i, root_pc in enumerate(degs):
        deg = i + 1
        # Determine quality from interval pattern
        third = degs[(i + 2) % len(degs)]
        fifth = degs[(i + 4) % len(degs)]
        third_interval = (third - root_pc) % 12
        fifth_interval = (fifth - root_pc) % 12

        if third_interval == 4 and fifth_interval == 7:
            quality = Quality.MAJOR
        elif third_interval == 3 and fifth_interval == 7:
            quality = Quality.MINOR
        elif third_interval == 3 and fifth_interval == 6:
            quality = Quality.DIMINISHED
        elif third_interval == 4 and fifth_interval == 8:
            quality = Quality.AUGMENTED
        else:
            quality = Quality.MAJOR
        result.append((root_pc, quality))
    return result

_CADENCE_BONUSES: dict[tuple[int, int], float] = {
    (4, 0): 0.8,  # V → I  (authentic cadence)
    (1, 4): 0.5,  # ii → V  (half cadence setup)
    (5, 4): 0.6,  # vi → IV (deceptive setup)
    (3, 0): 0.4,  # IV → I  (plagal cadence)
    (6, 4): 0.3,  # vii° → V
}
_FUNCTION_MAP = {0: 0, 3: 1, 5: 2}  # degree → function (T=0, S=1, D=2)
_FUNCTION_RULES_HMM2 = {
    # function → {next_function: weight}
    0: {1: 0.45, 2: 0.40, 0: 0.15},  # T → S or D
    1: {2: 0.65, 0: 0.25, 1: 0.10},  # S → D
    2: {0: 0.60, 1: 0.25, 2: 0.15},  # D → T
}
_SECONDARY_DOMINANTS: dict[int, tuple[int, Quality]] = {
    1: ((7, Quality.DOMINANT7),),  # V7/vi → vi  (not used, vi=5 in 0-index)
    2: ((2, Quality.DOMINANT7),),  # V7/ii
    3: ((6, Quality.DOMINANT7),),  # V7/iii
    4: ((11, Quality.DOMINANT7),),  # V7/IV
    5: ((4, Quality.DOMINANT7),),  # V7/V
}
_EXTENSIONS: dict[int, list[Quality]] = {
    0: [Quality.MAJOR, Quality.MAJOR7, Quality.DOMINANT7],  # I
    1: [Quality.MINOR, Quality.MINOR7],  # ii
    2: [Quality.MINOR, Quality.MINOR7],  # iii
    3: [Quality.MAJOR, Quality.MAJOR7],  # IV
    4: [Quality.MAJOR, Quality.DOMINANT7],  # V
    5: [Quality.MINOR, Quality.MINOR7],  # vi
    6: [Quality.DIMINISHED, Quality.HALF_DIM7],  # vii°
}

MODAL_CADENCES: dict[Mode, dict[tuple[int, int], float]] = {
    # 1. Primary Church / Diatonic Modes
    Mode.DORIAN: {
        (3, 0): 0.8,
        (2, 0): 0.8,
        (1, 0): 0.7,
        (6, 0): 0.6,
        (4, 0): 0.6,
    },
    Mode.DORIAN_PENTATONIC: {
        (3, 0): 0.8,
        (2, 0): 0.8,
        (1, 0): 0.7,
        (6, 0): 0.6,
        (4, 0): 0.6,
    },
    Mode.PHRYGIAN: {
        (1, 0): 0.85,
        (6, 0): 0.7,
        (2, 0): 0.5,
    },
    Mode.BAYATI: {
        (1, 0): 0.85,
        (6, 0): 0.7,
        (2, 0): 0.5,
    },
    Mode.LYDIAN: {
        (1, 0): 0.85,
        (6, 0): 0.7,
    },
    Mode.YAMAN: {
        (1, 0): 0.85,
        (6, 0): 0.7,
    },
    Mode.MIXOLYDIAN: {
        (6, 0): 0.8,
        (4, 0): 0.7,
    },
    Mode.LOCRIAN: {
        (1, 0): 0.8,
        (2, 0): 0.6,
    },

    # 2. Minor & Harmonic Variants
    Mode.HARMONIC_MINOR: {
        (4, 0): 0.85,
        (6, 0): 0.7,
    },
    Mode.MELODIC_MINOR: {
        (4, 0): 0.85,
        (3, 0): 0.75,
    },
    Mode.NATURAL_MINOR: {
        (4, 0): 0.8,
        (3, 0): 0.7,
        (6, 0): 0.6,
    },
    Mode.AEOLIAN: {
        (4, 0): 0.8,
        (3, 0): 0.7,
        (6, 0): 0.6,
    },
    Mode.AEOLIAN_BB7: {
        (4, 0): 0.8,
        (3, 0): 0.7,
        (6, 0): 0.6,
    },

    # 3. Jazz & Modern Fusion Modes
    Mode.LYDIAN_DOMINANT: {
        (1, 0): 0.8,
        (6, 0): 0.7,
    },
    Mode.ACOUSTIC_MAJOR: {
        (1, 0): 0.8,
        (6, 0): 0.7,
    },
    Mode.MIXOLYDIAN_B6: {
        (3, 0): 0.8,
        (6, 0): 0.7,
    },
    Mode.DORIAN_B2: {
        (1, 0): 0.8,
        (3, 0): 0.7,
    },
    Mode.LOCRIAN_NAT_2: {
        (1, 0): 0.8,
        (2, 0): 0.6,
    },
    Mode.ALTERED: {
        (1, 0): 0.85,
        (4, 0): 0.7,
    },
    Mode.SUPER_LOCRIAN: {
        (1, 0): 0.85,
        (4, 0): 0.7,
    },
    Mode.ALT_BB3: {
        (1, 0): 0.85,
        (4, 0): 0.7,
    },
    Mode.ALT_BB3_BB7: {
        (1, 0): 0.85,
        (4, 0): 0.7,
    },
    Mode.IONIAN_B5: {
        (4, 0): 0.8,
        (3, 0): 0.7,
    },

    # 4. Exotic, Eastern & Folk Modes
    Mode.HUNGARIAN_MINOR: {
        (4, 0): 0.85,
        (1, 0): 0.7,
        (3, 0): 0.6,
    },
    Mode.GYPSY: {
        (4, 0): 0.85,
        (1, 0): 0.7,
        (3, 0): 0.6,
    },
    Mode.HUNGARIAN_MAJOR: {
        (1, 0): 0.8,
        (6, 0): 0.7,
    },
    # Byzantine/Persian/Arabian separated musicologically:
    Mode.BYZANTINE: {
        (1, 0): 0.85,
        (6, 0): 0.85,
    },
    Mode.PERSIAN: {
        (1, 0): 0.8,
        (4, 0): 0.75,
    },
    Mode.ARABIAN: {
        (4, 0): 0.85,
        (6, 0): 0.75,
    },
    Mode.SPANISH_8_TONE: {
        (1, 0): 0.8,
        (6, 0): 0.85,
        (4, 0): 0.7,
    },
    Mode.PHRYGIAN_DOMINANT: {
        (1, 0): 0.85,
        (4, 0): 0.7,
        (6, 0): 0.8,
    },
    Mode.DOUBLE_HARMONIC: {
        (1, 0): 0.9,
        (6, 0): 0.85,
    },
    Mode.DOUBLE_HARM_MAJOR: {
        (1, 0): 0.9,
        (6, 0): 0.85,
    },

    # 5. Blues & Bebop Scales
    Mode.BLUES: {
        (5, 0): 0.8,
        (2, 0): 0.7,
        (4, 0): 0.6,
    },
    Mode.BEBOP_DOMINANT: {
        (6, 0): 0.8,
        (4, 0): 0.8,
    },
    Mode.BEBOP_DOM_6: {
        (6, 0): 0.8,
        (4, 0): 0.8,
    },
    Mode.BEBOP_DOM_7: {
        (6, 0): 0.8,
        (4, 0): 0.8,
    },
    Mode.BEBOP_DOM_8: {
        (6, 0): 0.8,
        (4, 0): 0.8,
    },
    Mode.BEBOP_MAJOR: {
        (4, 0): 0.8,
    },
    Mode.BEBOP_MINOR: {
        (4, 0): 0.8,
    },

    # 6. Pentatonic & Japanese Scales
    Mode.MAJOR_PENTATONIC: {
        (3, 0): 0.8,
        (1, 0): 0.7,
    },
    Mode.BHUPALI: {
        (3, 0): 0.8,
        (1, 0): 0.7,
    },
    Mode.SLENDRO_APPROX: {
        (3, 0): 0.8,
        (1, 0): 0.7,
    },
    Mode.MINOR_PENTATONIC: {
        (2, 0): 0.8,
        (4, 0): 0.7,
    },
    Mode.HIROJOSHI: {
        (3, 0): 0.8,
        (1, 0): 0.7,
    },
    Mode.KUMOI: {
        (3, 0): 0.8,
    },
    Mode.SUSPENDED_PENTA: {
        (3, 0): 0.8,
    },
    Mode.JAPANESE: {
        (1, 0): 0.85,
        (4, 0): 0.7,
    },
    Mode.PELOG_APPROX: {
        (1, 0): 0.8,
        (3, 0): 0.7,
    },

    # 7. Symmetric & Messiaen Modes
    Mode.WHOLE_TONE: {
        (1, 0): 0.6,
        (5, 0): 0.6,
    },
    Mode.MESSIAEN_1: {
        (1, 0): 0.6,
        (5, 0): 0.6,
    },
    Mode.DIMINISHED: {
        (1, 0): 0.75,
        (4, 0): 0.7,
        (6, 0): 0.7,
    },
    Mode.HALF_WHOLE_DIMINISHED: {
        (1, 0): 0.75,
        (4, 0): 0.7,
        (6, 0): 0.7,
    },
    Mode.WHOLE_HALF_DIMINISHED: {
        (1, 0): 0.75,
        (4, 0): 0.7,
        (6, 0): 0.7,
    },
    Mode.MESSIAEN_2: {
        (1, 0): 0.75,
        (4, 0): 0.7,
        (6, 0): 0.7,
    },
    Mode.AUGMENTED: {
        (2, 0): 0.7,
        (3, 0): 0.75,
    },
    Mode.AUGMENTED_MODE_2: {
        (1, 0): 0.75,
        (4, 0): 0.7,
    },
    Mode.MESSIAEN_3: {
        (1, 0): 0.75,
        (4, 0): 0.7,
    },
    Mode.MESSIAEN_4: {
        (1, 0): 0.7,
        (4, 0): 0.7,
    },
    Mode.MESSIAEN_5: {
        (1, 0): 0.7,
        (4, 0): 0.7,
    },
    Mode.MESSIAEN_6: {
        (1, 0): 0.7,
        (4, 0): 0.7,
    },

    # 8. Atmospheric & Scriabin Modes
    Mode.PROMETHEUS: {
        (1, 0): 0.7,
        (5, 0): 0.8,
    },
    Mode.MYSTIC: {
        (1, 0): 0.7,
        (5, 0): 0.8,
    },
    Mode.ENIGMATIC: {
        (1, 0): 0.8,
        (6, 0): 0.75,
    },
    Mode.SUSPENSE: {
        (1, 0): 0.75,
        (3, 0): 0.7,
    },
    Mode.HORROR_CLUSTER: {
        (1, 0): 0.75,
        (3, 0): 0.7,
    },
    Mode.PEDAL_MINOR: {
        (1, 0): 0.75,
        (3, 0): 0.7,
    },

    # 9. Microtonal & Experimental
    Mode.QUARTER_TONE_MINOR: {
        (1, 0): 0.8,
        (6, 0): 0.7,
    },
    Mode.ARABIC_SIKAH: {
        (1, 0): 0.8,
        (6, 0): 0.7,
    },

    # 10. Neapolitan
    Mode.NEAPOLITAN_MAJOR: {
        (1, 0): 0.85,
        (4, 0): 0.8,
    },
    Mode.NEAPOLITAN_MINOR: {
        (1, 0): 0.85,
        (4, 0): 0.85,
    },

    # 11. Cinematic / Epic
    Mode.ACOUSTIC_MINOR: {
        (4, 0): 0.75,
        (6, 0): 0.7,
    },
    Mode.LYDIAN_MINOR: {
        (1, 0): 0.8,
        (4, 0): 0.7,
    },
    Mode.LYDIAN_AUG_MODE: {
        (1, 0): 0.8,
        (6, 0): 0.75,
    },
}

def _get_cadence_bonus(prev_deg: int, curr_deg: int, scale: Scale | None = None) -> float:
    """
    Get the cadence bonus for transitioning from prev_deg to curr_deg (0-indexed).
    Takes scale modal qualities into account.
    """
    if scale is not None:
        mode = scale.mode
        if mode in MODAL_CADENCES:
            bonuses = MODAL_CADENCES[mode]
            if (prev_deg, curr_deg) in bonuses:
                return bonuses[(prev_deg, curr_deg)]

        # Generic interval-based minor check (fallback for exotic minor scales)
        intervals = scale.intervals()
        if len(intervals) > 2 and intervals[2] == 3:
            minor_bonuses = {
                (4, 0): 0.8,  # V/v → i (authentic cadence)
                (3, 0): 0.7,  # iv → i (minor plagal cadence)
                (1, 4): 0.6,  # ii° → V/v
                (6, 0): 0.5,  # VII → i (modal cadence)
                (6, 2): 0.4,  # VII → III (relative major resolution)
                (5, 4): 0.4,  # VI → V
            }
            if (prev_deg, curr_deg) in minor_bonuses:
                return minor_bonuses[(prev_deg, curr_deg)]

    # Default to major scale bonuses (handles major / ionian and fallback)
    return _CADENCE_BONUSES.get((prev_deg, curr_deg), 0.0)


# Modal gravity: characteristic scale degrees (0-indexed) for each mode.
# Degrees listed here receive a scoring bonus, guiding the harmonizer toward
# the most "characteristic" chords of the mode.
MODAL_GRAVITY: dict[Mode, list[int]] = {
    # Church / diatonic
    Mode.DORIAN: [0, 3, 4],            # raised 6th (Dorian 6th), IV and I
    Mode.PHRYGIAN: [0, 1, 5],          # flat 2nd (Neapolitan), i and vi
    Mode.LYDIAN: [0, 1, 3],            # raised 4th (#11), II and IV
    Mode.MIXOLYDIAN: [0, 4, 6],        # flat 7th (bVII), V and I
    Mode.LOCRIAN: [0, 1, 3],           # flat 2nd, diminished i
    # Minor variants
    Mode.NATURAL_MINOR: [0, 4, 5],     # i, v, VI
    Mode.AEOLIAN: [0, 4, 5],
    Mode.HARMONIC_MINOR: [0, 4, 6],    # i, V (raised 7th), vii°
    Mode.MELODIC_MINOR: [0, 3, 4],     # i, IV, V (ascending form)
    # Blues
    Mode.BLUES: [0, 3, 4],             # I, iv, v (blue notes)
    # Pentatonic / Japanese
    Mode.MINOR_PENTATONIC: [0, 2, 4],  # i, III, v
    Mode.MAJOR_PENTATONIC: [0, 3, 4],  # I, IV, V
    Mode.KUMOI: [0, 2, 3],
    Mode.HIROJOSHI: [0, 2, 4],
    # Exotic
    Mode.BYZANTINE: [0, 1, 5],         # flat 2nd, i, vi
    Mode.DOUBLE_HARMONIC: [0, 1, 5],
    Mode.HUNGARIAN_MINOR: [0, 1, 4],
    Mode.PERSIAN: [0, 1, 4],
    Mode.PELOG_APPROX: [0, 1, 3],
    # Symmetric
    Mode.WHOLE_TONE: [0, 2, 4],        # every other degree
    Mode.DIMINISHED: [0, 2, 4],
    Mode.HALF_WHOLE_DIMINISHED: [0, 2, 4],
}

