# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.render.dsp — Audio DSP mastering and NumPy effect processors.

Exposes high-end DSP processing via Pedalboard mastering desks and mathematical
custom DSP effects (sidechain ducking, Haas widening, soft clipping).
"""

from __future__ import annotations

from melodica.dsp_effects import (
    auto_duck,
    haas_widener,
    normalize_peak,
    saturate,
    soft_clip,
)
from melodica.dsp_mastering import (
    DSPMasteringDesk,
    MasteringPreset,
    HAVE_PEDALBOARD,
)

__all__ = [
    "DSPMasteringDesk",
    "MasteringPreset",
    "HAVE_PEDALBOARD",
    "normalize_peak",
    "haas_widener",
    "auto_duck",
    "soft_clip",
    "saturate",
]
