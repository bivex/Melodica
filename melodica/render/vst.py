# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.render.vst — VST3 instrument host adapter.

Renders Melodica's note collections through real VST3 plugins directly
to WAV audio arrays without needing an interactive DAW.
"""

from __future__ import annotations

from melodica.vst_player import VSTPlayer

__all__ = ["VSTPlayer"]
