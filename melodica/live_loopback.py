# Copyright (c) 2026 Bivex
#
# Licensed: MIT

"""
live_loopback.py — Live MIDI loopback for DAW integration.

Creates virtual MIDI ports that appear in any DAW (Logic, Ableton, Reaper).
Each Melodica track plays on its own MIDI channel with optional MIDI Clock sync.

Setup in DAW:
    1. Run Melodica script → virtual port "Melodica Bus 1" appears
    2. In DAW: create MIDI tracks
    3. Set each track's input to "Melodica Bus 1", select channel
    4. Load VST instrument on each track
    5. Done — Melodica drives your VSTs live

Usage:
    from melodica.live_loopback import LiveLoopback
    from melodica.types import Track, NoteInfo

    tracks = [
        Track(name="Bass", notes=bass_notes, channel=0, program=38),
        Track(name="Pad", notes=pad_notes, channel=1, program=89),
        Track(name="Lead", notes=lead_notes, channel=2, program=81),
    ]

    lb = LiveLoopback(bpm=100)
    lb.play(tracks, loop=True)
    # ... open DAW, assign channels ...
    lb.stop()

Requires: python-rtmidi (pip install melodica[live])
"""

from __future__ import annotations

import threading
import time

import mido

from melodica.types import NoteInfo, Track

try:
    import rtmidi
except ImportError:
    raise ImportError(
        "python-rtmidi is required. Install with: pip install melodica[live]"
    )


# MIDI Clock byte values
_CLOCK_TICK = 0xF8
_CLOCK_START = 0xFA
_CLOCK_CONTINUE = 0xFB
_CLOCK_STOP = 0xFC


def _build_timeline(tracks: list[Track], bpm: float) -> list[tuple[float, bytes]]:
    """Build sorted (time_sec, raw_midi_bytes) timeline from tracks."""
    beat_sec = 60.0 / bpm
    events: list[tuple[float, bytes]] = []

    for t in tracks:
        ch = t.channel
        # Program change at t=0
        events.append((
            0.0,
            mido.Message("program_change", program=t.program, channel=ch).bytes(),
        ))
        # CC setup at t=0
        for cc, val in [
            (7, t.volume), (10, t.pan), (11, t.expression),
            (1, t.modulation), (73, t.attack), (72, t.release),
            (91, t.reverb), (93, t.chorus), (3, t.vibrato),
            (64, t.sustain_pedal),
        ]:
            events.append((
                0.0,
                mido.Message("control_change", control=cc, value=val, channel=ch).bytes(),
            ))
        # Notes + per-note CC
        for n in t.notes:
            onset = max(0.0, n.start) * beat_sec
            offset = (n.start + n.duration) * beat_sec
            for cc_num, cc_val in n.expression.items():
                if isinstance(cc_num, int) and 0 <= cc_num <= 127:
                    events.append((
                        onset,
                        mido.Message(
                            "control_change",
                            control=cc_num,
                            value=max(0, min(127, cc_val)),
                            channel=ch,
                        ).bytes(),
                    ))
            events.append((
                onset,
                mido.Message("note_on", note=n.pitch, velocity=n.velocity, channel=ch).bytes(),
            ))
            events.append((
                offset,
                mido.Message("note_off", note=n.pitch, velocity=0, channel=ch).bytes(),
            ))

    # note_off before note_on at same tick
    events.sort(key=lambda e: (e[0], 1 if 0x90 <= e[1][0] & 0xF0 <= 0x9F else 0))
    return events


def _song_duration(tracks: list[Track]) -> float:
    end = 0.0
    for t in tracks:
        for n in t.notes:
            end = max(end, n.start + n.duration)
    return end


class LiveLoopback:
    """Live MIDI loopback with MIDI Clock sync for DAW integration.

    Creates a virtual MIDI port that appears in any DAW.
    Sends MIDI Clock (24 PPQN) so DAW can sync to Melodica's tempo.
    Each track plays on its own MIDI channel.

    Parameters:
        bpm:          Tempo.
        port_name:    Virtual port name (visible in DAW).
        clock:        Send MIDI Clock for DAW tempo sync.
        existing_port: Connect to existing port (e.g. "IAC Driver Bus 1")
                       instead of creating a new one.
    """

    def __init__(
        self,
        bpm: float = 120.0,
        *,
        port_name: str = "Melodica Bus 1",
        clock: bool = True,
        existing_port: str | None = None,
    ) -> None:
        self._bpm = bpm
        self._port_name = port_name
        self._send_clock = clock
        self._existing_port = existing_port
        self._midiout: rtmidi.MidiOut | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    @property
    def bpm(self) -> float:
        return self._bpm

    @bpm.setter
    def bpm(self, val: float) -> None:
        self._bpm = val

    @property
    def is_playing(self) -> bool:
        return self._running

    def open(self) -> None:
        """Open the virtual MIDI port."""
        if self._midiout is not None:
            return
        self._midiout = rtmidi.MidiOut()
        if self._existing_port:
            ports = self._midiout.get_ports()
            for i, name in enumerate(ports):
                if self._existing_port in name:
                    self._midiout.open_port(i)
                    return
            self._midiout.close_port()
            self._midiout = None
            raise ValueError(
                f"Port {self._existing_port!r} not found. Available: {ports}"
            )
        else:
            self._midiout.open_virtual_port(self._port_name)

    def close(self) -> None:
        """Stop playback and close the port."""
        self.stop()
        if self._midiout is not None:
            self._midiout.close_port()
            self._midiout = None

    def _send_raw(self, data: bytes) -> None:
        if self._midiout is not None:
            self._midiout.send_message(data)

    def panic(self) -> None:
        """All-notes-off on all channels."""
        if self._midiout is None:
            return
        for ch in range(16):
            self._midiout.send_message(
                mido.Message("control_change", control=123, value=0, channel=ch).bytes()
            )
            # Also send note_off for all notes to be safe
            for note in range(128):
                self._midiout.send_message(
                    mido.Message("note_off", note=note, velocity=0, channel=ch).bytes()
                )

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def play(self, tracks: list[Track], *, loop: bool = True) -> None:
        """Start live playback. Each track on its own MIDI channel.

        Args:
            tracks: Melodica Track objects with notes, channel, program.
            loop:   Loop the arrangement. Default True.
        """
        if self._midiout is None:
            self.open()

        out = self._midiout
        assert out is not None

        self.stop()

        timeline = _build_timeline(tracks, self._bpm)
        duration_beats = _song_duration(tracks)
        duration_sec = duration_beats * (60.0 / self._bpm) + 0.5

        # Pre-compute clock tick positions (24 PPQN)
        clock_interval = 60.0 / self._bpm / 24  # seconds between clock ticks

        # Merge clock ticks into timeline
        all_events: list[tuple[float, bytes, int]] = []  # (time, data, priority)
        for t, raw in timeline:
            all_events.append((t, raw, 1))  # priority 1 = note/cc

        if self._send_clock:
            # Add clock ticks
            num_ticks = int(duration_sec / clock_interval)
            for i in range(num_ticks):
                all_events.append((i * clock_interval, bytes([_CLOCK_TICK]), 0))
            # priority 0 = clock, so clock fires before notes at same time

        all_events.sort(key=lambda e: (e[0], e[2]))

        # Print channel map for the user
        print(f"\n  LiveLoopback @ {self._bpm} BPM")
        print(f"  Port: {self._port_name}")
        print(f"  Tracks → MIDI channels:")
        for t in tracks:
            print(f"    Ch {t.channel:2d} │ {t.name}")
        print(f"  Loop: {'ON' if loop else 'OFF'}")
        print(f"  MIDI Clock: {'ON' if self._send_clock else 'OFF'}")
        print(f"  Duration: {duration_sec:.1f}s ({duration_beats:.0f} beats)")
        print(f"\n  → Open your DAW, set MIDI input to '{self._port_name}'")
        print(f"  → Assign channels to VST tracks")
        print(f"  → Ctrl+C to stop\n")

        self._running = True

        def _play() -> None:
            # Send Start on first iteration, Continue on subsequent
            first = True
            while self._running:
                if self._send_clock:
                    self._send_raw(bytes([_CLOCK_START if first else _CLOCK_CONTINUE]))
                    first = False

                origin = time.time()
                for t, raw, _pri in all_events:
                    if not self._running:
                        break
                    delay = (origin + t) - time.time()
                    if delay > 0:
                        time.sleep(delay)
                    if not self._running:
                        break
                    out.send_message(raw)

                if not self._running:
                    break
                if not loop:
                    break

                # Brief pause between loops to let notes release
                time.sleep(0.05)

            self._send_raw(bytes([_CLOCK_STOP]))
            self.panic()

        self._thread = threading.Thread(target=_play, daemon=True)
        self._thread.start()

    def play_notes(
        self,
        notes: list[NoteInfo],
        *,
        bpm: float | None = None,
        channel: int = 0,
        program: int | None = None,
        loop: bool = True,
    ) -> None:
        """Convenience: play a single NoteInfo list as one track."""
        if bpm is not None:
            self._bpm = bpm
        t = Track(
            name=f"Track Ch {channel}",
            notes=notes,
            channel=channel,
            program=program or 0,
        )
        self.play([t], loop=loop)

    def stop(self) -> None:
        """Stop playback."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def __enter__(self) -> LiveLoopback:
        self.open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
