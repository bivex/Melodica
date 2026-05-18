# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18
# Last Updated: 2026-05-18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.types import Scale, Mode
from melodica.theory.chords import Quality

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)

@pytest.mark.parametrize("symbol,expected_quality", [
    ("Imystic",   Quality.SCRIABIN_MYSTIC),
    ("V7b9",      Quality.DOM7_FLAT9),
    ("IV7s11",    Quality.DOM7_SHARP11),
    ("bVIIphryg", Quality.PHRYGIAN_MAJOR),
    ("iitc",      Quality.TONE_CLUSTER),
    ("Icl4",      Quality.CLUSTER_4TH),
    ("ioct",      Quality.OCTATONIC_CLUSTER),
    ("V7alt",     Quality.ALTERED_DOMINANT),
    ("ivq4",      Quality.STACK_OF_4THS),
    ("Ispec",     Quality.SPECTRAL_CHORD),
])
def test_custom_qualities(symbol, expected_quality):
    chord = C_MAJOR.parse_roman(symbol)
    assert chord.quality == expected_quality
