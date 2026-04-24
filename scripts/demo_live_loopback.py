#!/usr/bin/env python3
"""
demo_live_loopback.py — Live MIDI loopback demo.

Generates a multi-track arrangement and plays it live through a virtual
MIDI port. Open your DAW, assign channels to VST instruments, and listen.

Usage:
    pip install melodica[live]
    python scripts/demo_live_loopback.py

    Then in DAW:
        1. Create 3 MIDI tracks
        2. Input: "Melodica Bus 1"
        3. Track 1 → Channel 1 (Bass) → load VST
        4. Track 2 → Channel 2 (Pad)  → load VST
        5. Track 3 → Channel 3 (Lead) → load VST
"""

from __future__ import annotations

import signal
import sys

from melodica.live_loopback import LiveLoopback
from melodica.types import NoteInfo, Track, Scale, Mode, ChordLabel
from melodica.generators.melody import MelodyGenerator

BPM = 90
KEY = Scale(root=0, mode=Mode.NATURAL_MINOR)  # Am


def build_arrangement() -> list[Track]:
    # Chord progression: Am - F - C - G (4 bars each, 16 total)
    chords = [
        ChordLabel(root=9, quality=0, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=0, start=4.0, duration=4.0),
        ChordLabel(root=0, quality=0, start=8.0, duration=4.0),
        ChordLabel(root=7, quality=0, start=12.0, duration=4.0),
    ]

    # Generate melody
    gen = MelodyGenerator()
    melody = gen.render(chords, KEY, duration_beats=16.0)

    # Bass: root notes
    bass: list[NoteInfo] = []
    for c in chords:
        root = c.root
        for beat in range(4):
            bass.append(NoteInfo(
                pitch=root + 36,
                start=c.start + beat,
                duration=0.9,
                velocity=85 + (10 if beat % 2 == 0 else 0),
            ))

    # Pad: sustained chords
    pad: list[NoteInfo] = []
    for c in chords:
        for offset in [0, 4, 7]:
            pad.append(NoteInfo(
                pitch=c.root + offset + 48,
                start=c.start,
                duration=c.duration,
                velocity=55,
            ))

    return [
        Track(name="Bass", notes=bass, channel=1, program=38),
        Track(name="Pad", notes=pad, channel=2, program=89),
        Track(name="Lead", notes=melody, channel=3, program=81),
    ]


def main() -> None:
    tracks = build_arrangement()
    print(f"Generated {sum(len(t.notes) for t in tracks)} notes across {len(tracks)} tracks")

    lb = LiveLoopback(bpm=BPM, port_name="Melodica Bus 1", clock=True)

    def _sigint(sig: int, frame: object) -> None:
        print("\nStopping...")
        lb.stop()
        lb.close()
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint)

    lb.open()
    lb.play(tracks, loop=True)

    # Block until Ctrl+C
    try:
        while True:
            signal.pause()
    except AttributeError:
        # signal.pause() not available on some platforms
        while True:
            import time
            time.sleep(1)


if __name__ == "__main__":
    main()
