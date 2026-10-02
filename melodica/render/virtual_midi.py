# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.render.virtual_midi — Virtual MIDI ports and real-time loopback.
"""

from __future__ import annotations

from melodica.live_loopback import LiveLoopbackManager
from melodica.virtual_midi import (
    VirtualMidiIn,
    VirtualMidiOut,
    detect_available_ports,
)

__all__ = [
    "VirtualMidiOut",
    "VirtualMidiIn",
    "LiveLoopbackManager",
    "detect_available_ports",
]
