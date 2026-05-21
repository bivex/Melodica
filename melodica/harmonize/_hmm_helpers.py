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

def _get_cadence_bonus(prev_deg: int, curr_deg: int, scale: Scale | None = None) -> float:
    """
    Get the cadence bonus for transitioning from prev_deg to curr_deg (0-indexed).
    Takes scale modal qualities into account.
    """
    if scale is not None:
        mode = scale.mode
        
        # 1. Primary Church / Diatonic Modes
        if mode in (Mode.DORIAN, Mode.DORIAN_PENTATONIC):
            # Dorian rules:
            # IV -> i (3 -> 0 for Dorian, 2 -> 0 for 5-note pentatonic)
            # ii -> i (1 -> 0)
            # bVII -> i (6 -> 0 for Dorian, 4 -> 0 for 5-note pentatonic)
            dorian_bonuses = {
                (3, 0): 0.8,
                (2, 0): 0.8,
                (1, 0): 0.7,
                (6, 0): 0.6,
                (4, 0): 0.6,
            }
            if (prev_deg, curr_deg) in dorian_bonuses:
                return dorian_bonuses[(prev_deg, curr_deg)]
                
        elif mode in (Mode.PHRYGIAN, Mode.BAYATI):
            # Phrygian rules:
            # bII -> i (1 -> 0): 0.85 (Phrygian cadence)
            # bvii -> i (6 -> 0): 0.7
            # bIII -> i (2 -> 0): 0.5
            phrygian_bonuses = {
                (1, 0): 0.85,
                (6, 0): 0.7,
                (2, 0): 0.5,
            }
            if (prev_deg, curr_deg) in phrygian_bonuses:
                return phrygian_bonuses[(prev_deg, curr_deg)]
                
        elif mode in (Mode.LYDIAN, Mode.YAMAN):
            # Lydian rules:
            # II -> I (1 -> 0): 0.85 (Lydian cadence)
            # vii -> I (6 -> 0): 0.7
            lydian_bonuses = {
                (1, 0): 0.85,
                (6, 0): 0.7,
            }
            if (prev_deg, curr_deg) in lydian_bonuses:
                return lydian_bonuses[(prev_deg, curr_deg)]
                
        elif mode in (Mode.MIXOLYDIAN,):
            # Mixolydian rules:
            # bVII -> I (6 -> 0): 0.8 (Mixolydian flat-seven resolution)
            # v -> I (4 -> 0): 0.7 (Mixolydian minor dominant)
            mixo_bonuses = {
                (6, 0): 0.8,
                (4, 0): 0.7,
            }
            if (prev_deg, curr_deg) in mixo_bonuses:
                return mixo_bonuses[(prev_deg, curr_deg)]
                
        elif mode in (Mode.LOCRIAN,):
            # Locrian rules:
            # bII -> i° (1 -> 0): 0.8
            # bIII -> i° (2 -> 0): 0.6
            locrian_bonuses = {
                (1, 0): 0.8,
                (2, 0): 0.6,
            }
            if (prev_deg, curr_deg) in locrian_bonuses:
                return locrian_bonuses[(prev_deg, curr_deg)]
                
        # 2. Minor & Harmonic Variants
        elif mode in (Mode.HARMONIC_MINOR,):
            # Harmonic minor rules:
            # V -> i (4 -> 0): 0.85 (authentic with leading tone)
            # vii° -> i (6 -> 0): 0.7
            harmonic_bonuses = {
                (4, 0): 0.85,
                (6, 0): 0.7,
            }
            if (prev_deg, curr_deg) in harmonic_bonuses:
                return harmonic_bonuses[(prev_deg, curr_deg)]
                
        elif mode in (Mode.MELODIC_MINOR,):
            # Melodic minor rules:
            # V -> i (4 -> 0): 0.85
            # IV -> i (3 -> 0): 0.75
            melodic_bonuses = {
                (4, 0): 0.85,
                (3, 0): 0.75,
            }
            if (prev_deg, curr_deg) in melodic_bonuses:
                return melodic_bonuses[(prev_deg, curr_deg)]
                
        elif mode in (Mode.NATURAL_MINOR, Mode.AEOLIAN, Mode.AEOLIAN_BB7):
            # Natural minor rules:
            # v -> i (4 -> 0): 0.8 (authentic minor)
            # iv -> i (3 -> 0): 0.7
            # bVII -> i (6 -> 0): 0.6
            nat_minor_bonuses = {
                (4, 0): 0.8,
                (3, 0): 0.7,
                (6, 0): 0.6,
            }
            if (prev_deg, curr_deg) in nat_minor_bonuses:
                return nat_minor_bonuses[(prev_deg, curr_deg)]

        # 3. Jazz & Modern Fusion Modes
        elif mode in (Mode.LYDIAN_DOMINANT, Mode.ACOUSTIC_MAJOR):
            lydian_dom = {
                (1, 0): 0.8,   # II -> I
                (6, 0): 0.7,   # bVII -> I
            }
            if (prev_deg, curr_deg) in lydian_dom:
                return lydian_dom[(prev_deg, curr_deg)]
                
        elif mode in (Mode.MIXOLYDIAN_B6,):
            mixo_b6 = {
                (3, 0): 0.8,   # iv -> I
                (6, 0): 0.7,   # bVII -> I
            }
            if (prev_deg, curr_deg) in mixo_b6:
                return mixo_b6[(prev_deg, curr_deg)]
                
        elif mode in (Mode.DORIAN_B2,):
            dorian_b2 = {
                (1, 0): 0.8,   # bII -> i
                (3, 0): 0.7,   # IV -> i
            }
            if (prev_deg, curr_deg) in dorian_b2:
                return dorian_b2[(prev_deg, curr_deg)]
                
        elif mode in (Mode.LOCRIAN_NAT_2,):
            locrian_nat2 = {
                (1, 0): 0.8,   # ii -> i°
                (2, 0): 0.6,   # bIII -> i°
            }
            if (prev_deg, curr_deg) in locrian_nat2:
                return locrian_nat2[(prev_deg, curr_deg)]
                
        elif mode in (Mode.ALTERED, Mode.SUPER_LOCRIAN, Mode.ALT_BB3, Mode.ALT_BB3_BB7):
            altered = {
                (1, 0): 0.85,  # bII -> I/i
                (4, 0): 0.7,   # bV -> I/i
            }
            if (prev_deg, curr_deg) in altered:
                return altered[(prev_deg, curr_deg)]

        elif mode in (Mode.IONIAN_B5,):
            ionian_b5 = {
                (4, 0): 0.8,   # V -> I
                (3, 0): 0.7,   # bV -> I (or IV -> I)
            }
            if (prev_deg, curr_deg) in ionian_b5:
                return ionian_b5[(prev_deg, curr_deg)]

        # 4. Exotic, Eastern & Folk Modes
        elif mode in (Mode.HUNGARIAN_MINOR, Mode.GYPSY):
            hungarian_minor = {
                (4, 0): 0.85,  # V -> i
                (1, 0): 0.7,   # bII -> i
                (3, 0): 0.6,   # iv -> i
            }
            if (prev_deg, curr_deg) in hungarian_minor:
                return hungarian_minor[(prev_deg, curr_deg)]
                
        elif mode in (Mode.HUNGARIAN_MAJOR,):
            hungarian_major = {
                (1, 0): 0.8,   # II -> I
                (6, 0): 0.7,   # bVII -> I
            }
            if (prev_deg, curr_deg) in hungarian_major:
                return hungarian_major[(prev_deg, curr_deg)]
                
        elif mode in (Mode.BYZANTINE, Mode.PERSIAN, Mode.ARABIAN):
            byzantine = {
                (1, 0): 0.85,  # bII -> I
                (6, 0): 0.75,  # vii° -> I
            }
            if (prev_deg, curr_deg) in byzantine:
                return byzantine[(prev_deg, curr_deg)]

        elif mode in (Mode.SPANISH_8_TONE,):
            spanish_8 = {
                (1, 0): 0.8,   # bII -> i
                (6, 0): 0.85,  # V -> i (degree 6 in 8-tone scale is V)
                (4, 0): 0.7,   # IV -> i (degree 4 in 8-tone scale is IV)
            }
            if (prev_deg, curr_deg) in spanish_8:
                return spanish_8[(prev_deg, curr_deg)]

        elif mode in (Mode.PHRYGIAN_DOMINANT,):
            phryg_dom = {
                (1, 0): 0.85,  # bII -> I
                (4, 0): 0.7,   # v -> I
                (6, 0): 0.8,   # bVII -> I
            }
            if (prev_deg, curr_deg) in phryg_dom:
                return phryg_dom[(prev_deg, curr_deg)]

        elif mode in (Mode.DOUBLE_HARMONIC, Mode.DOUBLE_HARM_MAJOR):
            double_harm = {
                (1, 0): 0.9,   # bII -> I (extremely strong Eastern resolution)
                (6, 0): 0.85,  # VII -> I
            }
            if (prev_deg, curr_deg) in double_harm:
                return double_harm[(prev_deg, curr_deg)]

        # 5. Blues & Bebop Scales
        elif mode in (Mode.BLUES,):
            # C, Eb, F, F#, G, Bb (6 notes)
            blues = {
                (5, 0): 0.8,   # bVII -> I
                (2, 0): 0.7,   # IV -> I
                (4, 0): 0.6,   # v -> I
            }
            if (prev_deg, curr_deg) in blues:
                return blues[(prev_deg, curr_deg)]
                
        elif mode in (Mode.BEBOP_DOMINANT, Mode.BEBOP_DOM_6, Mode.BEBOP_DOM_7, Mode.BEBOP_DOM_8):
            # 8-note scales.
            bebop_dom = {
                (6, 0): 0.8,   # bVII -> I
                (4, 0): 0.8,   # V -> I
            }
            if (prev_deg, curr_deg) in bebop_dom:
                return bebop_dom[(prev_deg, curr_deg)]
                
        elif mode in (Mode.BEBOP_MAJOR,):
            bebop_maj = {
                (4, 0): 0.8,   # V -> I
            }
            if (prev_deg, curr_deg) in bebop_maj:
                return bebop_maj[(prev_deg, curr_deg)]
                
        elif mode in (Mode.BEBOP_MINOR,):
            bebop_min = {
                (4, 0): 0.8,   # V -> i
            }
            if (prev_deg, curr_deg) in bebop_min:
                return bebop_min[(prev_deg, curr_deg)]

        # 6. Pentatonic & Japanese Scales
        elif mode in (Mode.MAJOR_PENTATONIC, Mode.BHUPALI, Mode.SLENDRO_APPROX):
            # C, D, E, G, A (5 notes)
            maj_pent = {
                (3, 0): 0.8,   # V -> I
                (1, 0): 0.7,   # ii -> I
            }
            if (prev_deg, curr_deg) in maj_pent:
                return maj_pent[(prev_deg, curr_deg)]
                
        elif mode in (Mode.MINOR_PENTATONIC,):
            # A, C, D, E, G (5 notes)
            min_pent = {
                (2, 0): 0.8,   # iv -> i
                (4, 0): 0.7,   # bVII -> i
            }
            if (prev_deg, curr_deg) in min_pent:
                return min_pent[(prev_deg, curr_deg)]
                
        elif mode in (Mode.HIROJOSHI,):
            # C, D, Eb, G, Ab (5 notes)
            hirojoshi = {
                (3, 0): 0.8,   # iv -> i
                (1, 0): 0.7,   # ii -> i
            }
            if (prev_deg, curr_deg) in hirojoshi:
                return hirojoshi[(prev_deg, curr_deg)]
                
        elif mode in (Mode.KUMOI, Mode.SUSPENDED_PENTA):
            # C, D, F, G, Bb (5 notes)
            kumoi = {
                (3, 0): 0.8,   # V -> I
            }
            if (prev_deg, curr_deg) in kumoi:
                return kumoi[(prev_deg, curr_deg)]
                
        elif mode in (Mode.JAPANESE,):
            japanese = {
                (1, 0): 0.85,  # bII -> i
                (4, 0): 0.7,   # bVII -> i
            }
            if (prev_deg, curr_deg) in japanese:
                return japanese[(prev_deg, curr_deg)]

        elif mode in (Mode.PELOG_APPROX,):
            # 5-note scale
            pelog = {
                (1, 0): 0.8,   # bII -> I
                (3, 0): 0.7,   # V -> I
            }
            if (prev_deg, curr_deg) in pelog:
                return pelog[(prev_deg, curr_deg)]

        # 7. Symmetric & Messiaen Modes
        elif mode in (Mode.WHOLE_TONE, Mode.MESSIAEN_1):
            whole_tone = {
                (1, 0): 0.6,   # II -> I
                (5, 0): 0.6,   # bVII -> I (index 5)
            }
            if (prev_deg, curr_deg) in whole_tone:
                return whole_tone[(prev_deg, curr_deg)]
                
        elif mode in (Mode.DIMINISHED, Mode.HALF_WHOLE_DIMINISHED, Mode.WHOLE_HALF_DIMINISHED, Mode.MESSIAEN_2):
            dim = {
                (1, 0): 0.75,  # bII -> i
                (4, 0): 0.7,   # bV -> i
                (6, 0): 0.7,   # VI -> i
            }
            if (prev_deg, curr_deg) in dim:
                return dim[(prev_deg, curr_deg)]

        elif mode in (Mode.AUGMENTED,):
            # 6-note scale
            augmented = {
                (2, 0): 0.7,   # III -> I
                (3, 0): 0.75,  # V -> I
            }
            if (prev_deg, curr_deg) in augmented:
                return augmented[(prev_deg, curr_deg)]

        elif mode in (Mode.AUGMENTED_MODE_2, Mode.MESSIAEN_3):
            # 6-note scale
            aug_mode2 = {
                (1, 0): 0.75,  # bII -> I
                (4, 0): 0.7,   # bVI -> I
            }
            if (prev_deg, curr_deg) in aug_mode2:
                return aug_mode2[(prev_deg, curr_deg)]

        elif mode in (Mode.MESSIAEN_4, Mode.MESSIAEN_5, Mode.MESSIAEN_6):
            messiaen_other = {
                (1, 0): 0.7,
                (4, 0): 0.7,
            }
            if (prev_deg, curr_deg) in messiaen_other:
                return messiaen_other[(prev_deg, curr_deg)]

        # 8. Atmospheric & Scriabin Modes
        elif mode in (Mode.PROMETHEUS, Mode.MYSTIC):
            # 6-note scale
            scriabin = {
                (1, 0): 0.7,   # II -> I
                (5, 0): 0.8,   # VII/bVII -> I (index 5)
            }
            if (prev_deg, curr_deg) in scriabin:
                return scriabin[(prev_deg, curr_deg)]

        elif mode in (Mode.ENIGMATIC,):
            enigmatic = {
                (1, 0): 0.8,   # bII -> I
                (6, 0): 0.75,  # vii -> I
            }
            if (prev_deg, curr_deg) in enigmatic:
                return enigmatic[(prev_deg, curr_deg)]

        elif mode in (Mode.SUSPENSE, Mode.HORROR_CLUSTER, Mode.PEDAL_MINOR):
            atmos = {
                (1, 0): 0.75,  # bII -> I/i
                (3, 0): 0.7,   # IV/V -> I/i
            }
            if (prev_deg, curr_deg) in atmos:
                return atmos[(prev_deg, curr_deg)]

        # 9. Microtonal & Experimental
        elif mode in (Mode.QUARTER_TONE_MINOR, Mode.ARABIC_SIKAH):
            microtonal = {
                (1, 0): 0.8,   # neutral II -> I
                (6, 0): 0.7,   # VII -> I
            }
            if (prev_deg, curr_deg) in microtonal:
                return microtonal[(prev_deg, curr_deg)]

        # 10. Neapolitan
        elif mode in (Mode.NEAPOLITAN_MAJOR,):
            neapolitan_maj = {
                (1, 0): 0.85,  # bII -> I (Neapolitan resolution)
                (4, 0): 0.8,   # V -> I
            }
            if (prev_deg, curr_deg) in neapolitan_maj:
                return neapolitan_maj[(prev_deg, curr_deg)]

        elif mode in (Mode.NEAPOLITAN_MINOR,):
            neapolitan_min = {
                (1, 0): 0.85,  # bII -> i
                (4, 0): 0.85,  # V -> i
            }
            if (prev_deg, curr_deg) in neapolitan_min:
                return neapolitan_min[(prev_deg, curr_deg)]

        # 11. Cinematic / Epic
        elif mode in (Mode.ACOUSTIC_MINOR,):
            ac_minor = {
                (4, 0): 0.75,  # v -> i
                (6, 0): 0.7,   # bVII -> i
            }
            if (prev_deg, curr_deg) in ac_minor:
                return ac_minor[(prev_deg, curr_deg)]

        elif mode in (Mode.LYDIAN_MINOR,):
            lyd_minor = {
                (1, 0): 0.8,   # II -> I
                (4, 0): 0.7,   # v -> I
            }
            if (prev_deg, curr_deg) in lyd_minor:
                return lyd_minor[(prev_deg, curr_deg)]

        elif mode in (Mode.LYDIAN_AUG_MODE,):
            lyd_aug = {
                (1, 0): 0.8,   # II -> I
                (6, 0): 0.75,  # VII -> I
            }
            if (prev_deg, curr_deg) in lyd_aug:
                return lyd_aug[(prev_deg, curr_deg)]

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

