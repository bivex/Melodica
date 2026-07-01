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

from .modes import Mode, ScaleDefinition, MODE_DATABASE, get_mode_intervals, pick_modes
from .chords import Quality, CHORD_TEMPLATES
from .voicing import chord_to_notes, inversions, voice_motion_cost, voice_lead
from .tonality_bridge import (
    HAVE_TONALITY,
    analyze_progression,
    name_chord_label,
    recommend_next,
    verify_progression,
    voice_lead_exact,
    voice_leading_distance,
)
