#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
#
# Standalone test script for verifying dynamic cadence bonuses across all modes.
# Run with: python3 scratch/test_modes_cadences.py

import sys
import os

# Ensure the project root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from melodica.types import Scale, Mode
from melodica.harmonize._hmm_helpers import _get_cadence_bonus

def test_modes():
    print("Initializing dynamic cadence bonus test for all modes...")
    
    # 1. Primary Church / Diatonic Modes
    dorian = Scale(root=0, mode=Mode.DORIAN)
    assert _get_cadence_bonus(3, 0, dorian) == 0.8
    assert _get_cadence_bonus(1, 0, dorian) == 0.7
    assert _get_cadence_bonus(6, 0, dorian) == 0.6

    dorian_penta = Scale(root=0, mode=Mode.DORIAN_PENTATONIC)
    assert _get_cadence_bonus(2, 0, dorian_penta) == 0.8
    assert _get_cadence_bonus(1, 0, dorian_penta) == 0.7
    assert _get_cadence_bonus(4, 0, dorian_penta) == 0.6

    phrygian = Scale(root=0, mode=Mode.PHRYGIAN)
    assert _get_cadence_bonus(1, 0, phrygian) == 0.85
    assert _get_cadence_bonus(6, 0, phrygian) == 0.7
    assert _get_cadence_bonus(2, 0, phrygian) == 0.5

    bayati = Scale(root=0, mode=Mode.BAYATI)
    assert _get_cadence_bonus(1, 0, bayati) == 0.85
    assert _get_cadence_bonus(6, 0, bayati) == 0.7
    assert _get_cadence_bonus(2, 0, bayati) == 0.5

    lydian = Scale(root=0, mode=Mode.LYDIAN)
    assert _get_cadence_bonus(1, 0, lydian) == 0.85
    assert _get_cadence_bonus(6, 0, lydian) == 0.7

    yaman = Scale(root=0, mode=Mode.YAMAN)
    assert _get_cadence_bonus(1, 0, yaman) == 0.85
    assert _get_cadence_bonus(6, 0, yaman) == 0.7

    mixolydian = Scale(root=0, mode=Mode.MIXOLYDIAN)
    assert _get_cadence_bonus(6, 0, mixolydian) == 0.8
    assert _get_cadence_bonus(4, 0, mixolydian) == 0.7

    locrian = Scale(root=0, mode=Mode.LOCRIAN)
    assert _get_cadence_bonus(1, 0, locrian) == 0.8
    assert _get_cadence_bonus(2, 0, locrian) == 0.6

    # 2. Minor & Harmonic Variants
    harmonic_minor = Scale(root=0, mode=Mode.HARMONIC_MINOR)
    assert _get_cadence_bonus(4, 0, harmonic_minor) == 0.85
    assert _get_cadence_bonus(6, 0, harmonic_minor) == 0.7

    melodic_minor = Scale(root=0, mode=Mode.MELODIC_MINOR)
    assert _get_cadence_bonus(4, 0, melodic_minor) == 0.85
    assert _get_cadence_bonus(3, 0, melodic_minor) == 0.75

    natural_minor = Scale(root=0, mode=Mode.NATURAL_MINOR)
    assert _get_cadence_bonus(4, 0, natural_minor) == 0.8
    assert _get_cadence_bonus(3, 0, natural_minor) == 0.7
    assert _get_cadence_bonus(6, 0, natural_minor) == 0.6

    aeolian = Scale(root=0, mode=Mode.AEOLIAN)
    assert _get_cadence_bonus(4, 0, aeolian) == 0.8
    assert _get_cadence_bonus(3, 0, aeolian) == 0.7
    assert _get_cadence_bonus(6, 0, aeolian) == 0.6

    aeolian_bb7 = Scale(root=0, mode=Mode.AEOLIAN_BB7)
    assert _get_cadence_bonus(4, 0, aeolian_bb7) == 0.8
    assert _get_cadence_bonus(3, 0, aeolian_bb7) == 0.7
    assert _get_cadence_bonus(6, 0, aeolian_bb7) == 0.6

    # 3. Jazz & Modern Fusion Modes
    lydian_dominant = Scale(root=0, mode=Mode.LYDIAN_DOMINANT)
    assert _get_cadence_bonus(1, 0, lydian_dominant) == 0.8
    assert _get_cadence_bonus(6, 0, lydian_dominant) == 0.7

    acoustic_major = Scale(root=0, mode=Mode.ACOUSTIC_MAJOR)
    assert _get_cadence_bonus(1, 0, acoustic_major) == 0.8
    assert _get_cadence_bonus(6, 0, acoustic_major) == 0.7

    mixolydian_b6 = Scale(root=0, mode=Mode.MIXOLYDIAN_B6)
    assert _get_cadence_bonus(3, 0, mixolydian_b6) == 0.8
    assert _get_cadence_bonus(6, 0, mixolydian_b6) == 0.7

    dorian_b2 = Scale(root=0, mode=Mode.DORIAN_B2)
    assert _get_cadence_bonus(1, 0, dorian_b2) == 0.8
    assert _get_cadence_bonus(3, 0, dorian_b2) == 0.7

    locrian_nat2 = Scale(root=0, mode=Mode.LOCRIAN_NAT_2)
    assert _get_cadence_bonus(1, 0, locrian_nat2) == 0.8
    assert _get_cadence_bonus(2, 0, locrian_nat2) == 0.6

    altered = Scale(root=0, mode=Mode.ALTERED)
    assert _get_cadence_bonus(1, 0, altered) == 0.85
    assert _get_cadence_bonus(4, 0, altered) == 0.7

    super_locrian = Scale(root=0, mode=Mode.SUPER_LOCRIAN)
    assert _get_cadence_bonus(1, 0, super_locrian) == 0.85
    assert _get_cadence_bonus(4, 0, super_locrian) == 0.7

    alt_bb3 = Scale(root=0, mode=Mode.ALT_BB3)
    assert _get_cadence_bonus(1, 0, alt_bb3) == 0.85
    assert _get_cadence_bonus(4, 0, alt_bb3) == 0.7

    alt_bb3_bb7 = Scale(root=0, mode=Mode.ALT_BB3_BB7)
    assert _get_cadence_bonus(1, 0, alt_bb3_bb7) == 0.85
    assert _get_cadence_bonus(4, 0, alt_bb3_bb7) == 0.7

    ionian_b5 = Scale(root=0, mode=Mode.IONIAN_B5)
    assert _get_cadence_bonus(4, 0, ionian_b5) == 0.8
    assert _get_cadence_bonus(3, 0, ionian_b5) == 0.7

    # 4. Exotic, Eastern & Folk Modes
    hungarian_minor = Scale(root=0, mode=Mode.HUNGARIAN_MINOR)
    assert _get_cadence_bonus(4, 0, hungarian_minor) == 0.85
    assert _get_cadence_bonus(1, 0, hungarian_minor) == 0.7
    assert _get_cadence_bonus(3, 0, hungarian_minor) == 0.6

    gypsy = Scale(root=0, mode=Mode.GYPSY)
    assert _get_cadence_bonus(4, 0, gypsy) == 0.85
    assert _get_cadence_bonus(1, 0, gypsy) == 0.7
    assert _get_cadence_bonus(3, 0, gypsy) == 0.6

    hungarian_major = Scale(root=0, mode=Mode.HUNGARIAN_MAJOR)
    assert _get_cadence_bonus(1, 0, hungarian_major) == 0.8
    assert _get_cadence_bonus(6, 0, hungarian_major) == 0.7

    byzantine = Scale(root=0, mode=Mode.BYZANTINE)
    assert _get_cadence_bonus(1, 0, byzantine) == 0.85
    assert _get_cadence_bonus(6, 0, byzantine) == 0.75

    persian = Scale(root=0, mode=Mode.PERSIAN)
    assert _get_cadence_bonus(1, 0, persian) == 0.85
    assert _get_cadence_bonus(6, 0, persian) == 0.75

    arabian = Scale(root=0, mode=Mode.ARABIAN)
    assert _get_cadence_bonus(1, 0, arabian) == 0.85
    assert _get_cadence_bonus(6, 0, arabian) == 0.75

    spanish_8 = Scale(root=0, mode=Mode.SPANISH_8_TONE)
    assert _get_cadence_bonus(1, 0, spanish_8) == 0.8
    assert _get_cadence_bonus(6, 0, spanish_8) == 0.85
    assert _get_cadence_bonus(4, 0, spanish_8) == 0.7

    phryg_dom = Scale(root=0, mode=Mode.PHRYGIAN_DOMINANT)
    assert _get_cadence_bonus(1, 0, phryg_dom) == 0.85
    assert _get_cadence_bonus(4, 0, phryg_dom) == 0.7
    assert _get_cadence_bonus(6, 0, phryg_dom) == 0.8

    double_harm = Scale(root=0, mode=Mode.DOUBLE_HARMONIC)
    assert _get_cadence_bonus(1, 0, double_harm) == 0.9
    assert _get_cadence_bonus(6, 0, double_harm) == 0.85

    double_harm_maj = Scale(root=0, mode=Mode.DOUBLE_HARM_MAJOR)
    assert _get_cadence_bonus(1, 0, double_harm_maj) == 0.9
    assert _get_cadence_bonus(6, 0, double_harm_maj) == 0.85

    # 5. Blues & Bebop Scales
    blues = Scale(root=0, mode=Mode.BLUES)
    assert _get_cadence_bonus(5, 0, blues) == 0.8
    assert _get_cadence_bonus(2, 0, blues) == 0.7
    assert _get_cadence_bonus(4, 0, blues) == 0.6

    bebop_dom = Scale(root=0, mode=Mode.BEBOP_DOMINANT)
    assert _get_cadence_bonus(6, 0, bebop_dom) == 0.8
    assert _get_cadence_bonus(4, 0, bebop_dom) == 0.8

    bebop_dom_6 = Scale(root=0, mode=Mode.BEBOP_DOM_6)
    assert _get_cadence_bonus(6, 0, bebop_dom_6) == 0.8
    assert _get_cadence_bonus(4, 0, bebop_dom_6) == 0.8

    bebop_dom_7 = Scale(root=0, mode=Mode.BEBOP_DOM_7)
    assert _get_cadence_bonus(6, 0, bebop_dom_7) == 0.8
    assert _get_cadence_bonus(4, 0, bebop_dom_7) == 0.8

    bebop_dom_8 = Scale(root=0, mode=Mode.BEBOP_DOM_8)
    assert _get_cadence_bonus(6, 0, bebop_dom_8) == 0.8
    assert _get_cadence_bonus(4, 0, bebop_dom_8) == 0.8

    bebop_maj = Scale(root=0, mode=Mode.BEBOP_MAJOR)
    assert _get_cadence_bonus(4, 0, bebop_maj) == 0.8

    bebop_min = Scale(root=0, mode=Mode.BEBOP_MINOR)
    assert _get_cadence_bonus(4, 0, bebop_min) == 0.8

    # 6. Pentatonic & Japanese Scales
    maj_pent = Scale(root=0, mode=Mode.MAJOR_PENTATONIC)
    assert _get_cadence_bonus(3, 0, maj_pent) == 0.8
    assert _get_cadence_bonus(1, 0, maj_pent) == 0.7

    bhupali = Scale(root=0, mode=Mode.BHUPALI)
    assert _get_cadence_bonus(3, 0, bhupali) == 0.8
    assert _get_cadence_bonus(1, 0, bhupali) == 0.7

    slendro = Scale(root=0, mode=Mode.SLENDRO_APPROX)
    assert _get_cadence_bonus(3, 0, slendro) == 0.8
    assert _get_cadence_bonus(1, 0, slendro) == 0.7

    min_pent = Scale(root=0, mode=Mode.MINOR_PENTATONIC)
    assert _get_cadence_bonus(2, 0, min_pent) == 0.8
    assert _get_cadence_bonus(4, 0, min_pent) == 0.7

    hirojoshi = Scale(root=0, mode=Mode.HIROJOSHI)
    assert _get_cadence_bonus(3, 0, hirojoshi) == 0.8
    assert _get_cadence_bonus(1, 0, hirojoshi) == 0.7

    kumoi = Scale(root=0, mode=Mode.KUMOI)
    assert _get_cadence_bonus(3, 0, kumoi) == 0.8

    susp_penta = Scale(root=0, mode=Mode.SUSPENDED_PENTA)
    assert _get_cadence_bonus(3, 0, susp_penta) == 0.8

    japanese = Scale(root=0, mode=Mode.JAPANESE)
    assert _get_cadence_bonus(1, 0, japanese) == 0.85
    assert _get_cadence_bonus(4, 0, japanese) == 0.7

    pelog = Scale(root=0, mode=Mode.PELOG_APPROX)
    assert _get_cadence_bonus(1, 0, pelog) == 0.8
    assert _get_cadence_bonus(3, 0, pelog) == 0.7

    # 7. Symmetric & Messiaen Modes
    whole_tone = Scale(root=0, mode=Mode.WHOLE_TONE)
    assert _get_cadence_bonus(1, 0, whole_tone) == 0.6
    assert _get_cadence_bonus(5, 0, whole_tone) == 0.6

    messiaen_1 = Scale(root=0, mode=Mode.MESSIAEN_1)
    assert _get_cadence_bonus(1, 0, messiaen_1) == 0.6
    assert _get_cadence_bonus(5, 0, messiaen_1) == 0.6

    diminished = Scale(root=0, mode=Mode.DIMINISHED)
    assert _get_cadence_bonus(1, 0, diminished) == 0.75
    assert _get_cadence_bonus(4, 0, diminished) == 0.7
    assert _get_cadence_bonus(6, 0, diminished) == 0.7

    half_whole_dim = Scale(root=0, mode=Mode.HALF_WHOLE_DIMINISHED)
    assert _get_cadence_bonus(1, 0, half_whole_dim) == 0.75
    assert _get_cadence_bonus(4, 0, half_whole_dim) == 0.7
    assert _get_cadence_bonus(6, 0, half_whole_dim) == 0.7

    whole_half_dim = Scale(root=0, mode=Mode.WHOLE_HALF_DIMINISHED)
    assert _get_cadence_bonus(1, 0, whole_half_dim) == 0.75
    assert _get_cadence_bonus(4, 0, whole_half_dim) == 0.7
    assert _get_cadence_bonus(6, 0, whole_half_dim) == 0.7

    messiaen_2 = Scale(root=0, mode=Mode.MESSIAEN_2)
    assert _get_cadence_bonus(1, 0, messiaen_2) == 0.75
    assert _get_cadence_bonus(4, 0, messiaen_2) == 0.7
    assert _get_cadence_bonus(6, 0, messiaen_2) == 0.7

    augmented = Scale(root=0, mode=Mode.AUGMENTED)
    assert _get_cadence_bonus(2, 0, augmented) == 0.7
    assert _get_cadence_bonus(3, 0, augmented) == 0.75

    augmented_mode2 = Scale(root=0, mode=Mode.AUGMENTED_MODE_2)
    assert _get_cadence_bonus(1, 0, augmented_mode2) == 0.75
    assert _get_cadence_bonus(4, 0, augmented_mode2) == 0.7

    messiaen_3 = Scale(root=0, mode=Mode.MESSIAEN_3)
    assert _get_cadence_bonus(1, 0, messiaen_3) == 0.75
    assert _get_cadence_bonus(4, 0, messiaen_3) == 0.7

    messiaen_4 = Scale(root=0, mode=Mode.MESSIAEN_4)
    assert _get_cadence_bonus(1, 0, messiaen_4) == 0.7
    assert _get_cadence_bonus(4, 0, messiaen_4) == 0.7

    messiaen_5 = Scale(root=0, mode=Mode.MESSIAEN_5)
    assert _get_cadence_bonus(1, 0, messiaen_5) == 0.7
    assert _get_cadence_bonus(4, 0, messiaen_5) == 0.7

    messiaen_6 = Scale(root=0, mode=Mode.MESSIAEN_6)
    assert _get_cadence_bonus(1, 0, messiaen_6) == 0.7
    assert _get_cadence_bonus(4, 0, messiaen_6) == 0.7

    # 8. Atmospheric & Scriabin Modes
    prometheus = Scale(root=0, mode=Mode.PROMETHEUS)
    assert _get_cadence_bonus(1, 0, prometheus) == 0.7
    assert _get_cadence_bonus(5, 0, prometheus) == 0.8

    mystic = Scale(root=0, mode=Mode.MYSTIC)
    assert _get_cadence_bonus(1, 0, mystic) == 0.7
    assert _get_cadence_bonus(5, 0, mystic) == 0.8

    enigmatic = Scale(root=0, mode=Mode.ENIGMATIC)
    assert _get_cadence_bonus(1, 0, enigmatic) == 0.8
    assert _get_cadence_bonus(6, 0, enigmatic) == 0.75

    suspense = Scale(root=0, mode=Mode.SUSPENSE)
    assert _get_cadence_bonus(1, 0, suspense) == 0.75
    assert _get_cadence_bonus(3, 0, suspense) == 0.7

    horror = Scale(root=0, mode=Mode.HORROR_CLUSTER)
    assert _get_cadence_bonus(1, 0, horror) == 0.75
    assert _get_cadence_bonus(3, 0, horror) == 0.7

    pedal = Scale(root=0, mode=Mode.PEDAL_MINOR)
    assert _get_cadence_bonus(1, 0, pedal) == 0.75
    assert _get_cadence_bonus(3, 0, pedal) == 0.7

    # 9. Microtonal & Experimental
    quarter_tone = Scale(root=0, mode=Mode.QUARTER_TONE_MINOR)
    assert _get_cadence_bonus(1, 0, quarter_tone) == 0.8
    assert _get_cadence_bonus(6, 0, quarter_tone) == 0.7

    arabic_sikah = Scale(root=0, mode=Mode.ARABIC_SIKAH)
    assert _get_cadence_bonus(1, 0, arabic_sikah) == 0.8
    assert _get_cadence_bonus(6, 0, arabic_sikah) == 0.7

    # 10. Neapolitan
    neapolitan_maj = Scale(root=0, mode=Mode.NEAPOLITAN_MAJOR)
    assert _get_cadence_bonus(1, 0, neapolitan_maj) == 0.85
    assert _get_cadence_bonus(4, 0, neapolitan_maj) == 0.8

    neapolitan_min = Scale(root=0, mode=Mode.NEAPOLITAN_MINOR)
    assert _get_cadence_bonus(1, 0, neapolitan_min) == 0.85
    assert _get_cadence_bonus(4, 0, neapolitan_min) == 0.85

    # 11. Cinematic / Epic
    ac_minor = Scale(root=0, mode=Mode.ACOUSTIC_MINOR)
    assert _get_cadence_bonus(4, 0, ac_minor) == 0.75
    assert _get_cadence_bonus(6, 0, ac_minor) == 0.7

    lyd_minor = Scale(root=0, mode=Mode.LYDIAN_MINOR)
    assert _get_cadence_bonus(1, 0, lyd_minor) == 0.8
    assert _get_cadence_bonus(4, 0, lyd_minor) == 0.7

    lyd_aug = Scale(root=0, mode=Mode.LYDIAN_AUG_MODE)
    assert _get_cadence_bonus(1, 0, lyd_aug) == 0.8
    assert _get_cadence_bonus(6, 0, lyd_aug) == 0.75

    print("All mode-specific HMM cadence bonus tests passed successfully!")

if __name__ == "__main__":
    try:
        test_modes()
    except AssertionError as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    sys.exit(0)
