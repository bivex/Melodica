# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.render — Rendering and audio production layer.

Houses mixing desks, panning algorithms, DSP mastering, VST rendering,
DAW integrations (Reaper, DawDreamer), and virtual MIDI routing.
"""

from __future__ import annotations

from melodica.render.mix import (
    Role,
    PanReport,
    PanValidator,
    DEFAULT_GENRE,
    _analyze_track,
    _auto_spread_panning,
    _auto_mix,
    _sidechain_duck,
    _apply_humanization,
    _auto_master,
    _shape_dynamics,
    _generate_pan_automation,
    _generate_entry_fades,
    _generate_reverb_sends,
    _generate_delay_sends,
)

__all__ = [
    "Role",
    "PanReport",
    "PanValidator",
    "DEFAULT_GENRE",
    "_analyze_track",
    "_auto_spread_panning",
    "_auto_mix",
    "_sidechain_duck",
    "_apply_humanization",
    "_auto_master",
    "_shape_dynamics",
    "_generate_pan_automation",
    "_generate_entry_fades",
    "_generate_reverb_sends",
    "_generate_delay_sends",
]
