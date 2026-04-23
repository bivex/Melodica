#!/usr/bin/env python3
"""
demo_virtual_midi.py — Quick demo of real-time MIDI output to DAW/VST.

Usage:
    pip install melodica[live]
    python scripts/demo_virtual_midi.py

Setup:
    Option A — IAC Driver (recommended):
        1. Open Audio MIDI Setup
        2. Window → Show MIDI Studio
        3. Double-click IAC Driver → check "Device is online"
        4. Add a bus if needed (Bus 1 exists by default)

    Option B — Virtual port:
        Just run the script. A "Melodica" port appears in your DAW automatically.

    Then in your DAW:
        1. Create a MIDI track
        2. Set input to "IAC Driver Bus 1" or "Melodica"
        3. Load a VST instrument
        4. Run this script
"""

from __future__ import annotations

import random
import sys
import time

# ── Configuration ──────────────────────────────────────────────────────────
USE_IAC = False              # True → send to IAC Driver; False → create virtual port
IAC_PORT_NAME = "IAC Driver Bus 1"
VIRTUAL_PORT_NAME = "Melodica"
BPM = 90
# ───────────────────────────────────────────────────────────────────────────


def main() -> None:
    try:
        from melodica.virtual_midi import VirtualMidiOut, list_output_ports
    except ImportError:
        print("Install python-rtmidi first: pip install melodica[live]")
        sys.exit(1)

    # Show available ports
    print("Available MIDI output ports:")
    for name in list_output_ports():
        print(f"  • {name}")
    print()

    # Open port
    vmo = VirtualMidiOut(VIRTUAL_PORT_NAME)
    if USE_IAC:
        print(f"Connecting to {IAC_PORT_NAME!r}...")
        vmo.open(existing_port=IAC_PORT_NAME)
    else:
        print(f"Creating virtual port {VIRTUAL_PORT_NAME!r}...")
        print("→ Open your DAW and set MIDI input to this port")
        vmo.open()

    print(f"Playing at {BPM} BPM. Press Ctrl+C to stop.\n")

    try:
        demo_arp(vmo)
    except KeyboardInterrupt:
        pass
    finally:
        vmo.stop()
        vmo.close()
        print("\nStopped.")


def demo_arp(vmo: VirtualMidiOut) -> None:
    """Simple arpeggio demo with evolving pattern."""
    from melodica.types import NoteInfo

    # C major arp pattern (quarter notes, 2 bars)
    pattern = [60, 64, 67, 72, 67, 64, 60, 64]
    beat = 0.0

    print("Playing arpeggio loop. Ctrl+C to stop.")
    vmo.send(mido_msg("program_change", program=46))  # Harp

    while True:
        notes = []
        for pitch in pattern:
            vel = random.randint(60, 100)
            notes.append(NoteInfo(pitch=pitch, start=beat, duration=0.9, velocity=vel))
            beat += 1.0

        vmo.play_notes(notes, bpm=BPM, channel=0, loop=False)
        vmo.wait()
        beat = 0.0


def mido_msg(typ: str, **kw: int) -> object:
    import mido
    return mido.Message(typ, **kw)


if __name__ == "__main__":
    main()
