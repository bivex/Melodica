# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Licensed: MIT

"""
virtual_midi.py — Real-time virtual MIDI port adapter for macOS.

Connects Melodica's generative output directly to DAWs (Logic, Ableton, Reaper)
and VST instruments through macOS virtual MIDI ports.

Two modes:
  1. Custom virtual port — creates a new port visible in any DAW's MIDI routing.
  2. IAC Driver — connects to an existing IAC bus configured in Audio MIDI Setup.

Typical setup:
    # Mode 1: custom virtual port (appears in DAW automatically)
    from melodica.virtual_midi import VirtualMidiOut
    vmo = VirtualMidiOut("Melodica")
    vmo.open()
    vmo.play_notes(notes, bpm=90)

    # Mode 2: send to IAC Driver (must be enabled in Audio MIDI Setup first)
    vmo = VirtualMidiOut("Melodica")
    vmo.open("IAC Driver Bus 1")
    vmo.play_tracks(tracks, bpm=120)

Requires: python-rtmidi
Install:  pip install melodica[live]

Layer: Infrastructure (adapter) — mirrors midi.py for real-time I/O.
"""

from __future__ import annotations

import threading
import time
from contextlib import contextmanager
from typing import Generator

import mido

from melodica.types import NoteInfo, Track

try:
    import rtmidi  # noqa: F401
except ImportError:
    raise ImportError(
        "python-rtmidi is required for virtual MIDI ports. "
        "Install with: pip install melodica[live]"
    )


def list_output_ports() -> list[str]:
    """Return names of all available MIDI output ports (includes IAC buses)."""
    midiout = rtmidi.MidiOut()
    ports = midiout.get_ports()
    midiout.close_port()
    return list(ports)


# ---------------------------------------------------------------------------
# Core adapter
# ---------------------------------------------------------------------------


class VirtualMidiOut:
    """Real-time MIDI output through a virtual or existing port.

    Usage:
        vmo = VirtualMidiOut("Melodica Port")
        vmo.open()                         # creates virtual port
        vmo.play_notes(notes, bpm=120)
        ...
        vmo.close()

    Or as context manager:
        with VirtualMidiOut("Melodica Port") as vmo:
            vmo.play_notes(notes, bpm=120)
    """

    def __init__(self, name: str = "Melodica") -> None:
        self._name = name
        self._midiout: rtmidi.MidiOut | None = None
        self._running = False
        self._thread: threading.Thread | None = None

    @property
    def port_name(self) -> str:
        return self._name

    def open(self, existing_port: str | None = None) -> None:
        """Open the port.

        Args:
            existing_port: If given, connect to this existing port
                           (e.g. "IAC Driver Bus 1"). Otherwise create a new
                           virtual port named ``self._name``.
        """
        if self._midiout is not None:
            return

        self._midiout = rtmidi.MidiOut()

        if existing_port:
            ports = self._midiout.get_ports()
            for i, name in enumerate(ports):
                if existing_port in name:
                    self._midiout.open_port(i)
                    return
            self._midiout.close_port()
            self._midiout = None
            raise ValueError(
                f"Port {existing_port!r} not found. "
                f"Available ports: {ports}\n"
                "Tip: enable IAC Driver in Audio MIDI Setup → MIDI Studio"
            )
        else:
            self._midiout.open_virtual_port(self._name)

    def close(self) -> None:
        """Stop playback and close the port."""
        self.stop()
        if self._midiout is not None:
            self._midiout.close_port()
            self._midiout = None

    # ------------------------------------------------------------------
    # Low-level send
    # ------------------------------------------------------------------

    def send(self, msg: mido.Message) -> None:
        """Send a single mido Message."""
        if self._midiout is None:
            raise RuntimeError("Port is not open. Call open() first.")
        self._midiout.send_message(msg.bytes())

    def panic(self) -> None:
        """All-notes-off on every channel."""
        if self._midiout is None:
            return
        for ch in range(16):
            self._midiout.send_message(
                mido.Message("control_change", control=123, value=0, channel=ch).bytes()
            )

    # ------------------------------------------------------------------
    # Playback control
    # ------------------------------------------------------------------

    def stop(self) -> None:
        """Stop current playback and silence all notes."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None
        self.panic()

    def wait(self) -> None:
        """Block until current playback finishes."""
        if self._thread is not None:
            self._thread.join()

    # ------------------------------------------------------------------
    # High-level playback — NoteInfo list
    # ------------------------------------------------------------------

    def play_notes(
        self,
        notes: list[NoteInfo],
        *,
        bpm: float = 120.0,
        channel: int = 0,
        program: int | None = None,
        loop: bool = False,
    ) -> None:
        """Play a list of NoteInfo in real-time.

        Args:
            notes:   Notes to play.
            bpm:     Tempo.
            channel: MIDI channel (0-15).
            program: If set, send program_change before playback.
            loop:    Loop until stop() is called.
        """
        if self._midiout is None:
            self.open()

        out = self._midiout
        assert out is not None

        beat_sec = 60.0 / bpm

        if program is not None:
            self.send(mido.Message("program_change", program=program, channel=channel))

        # Build sorted event list: (abs_time_sec, msg_bytes)
        events: list[tuple[float, bytes]] = []
        for n in notes:
            onset = max(0.0, n.start) * beat_sec
            offset = (n.start + n.duration) * beat_sec
            events.append((
                onset,
                mido.Message("note_on", note=n.pitch, velocity=n.velocity, channel=channel).bytes(),
            ))
            events.append((
                offset,
                mido.Message("note_off", note=n.pitch, velocity=0, channel=channel).bytes(),
            ))

        events.sort(key=lambda e: e[0])

        def _play() -> None:
            while True:
                origin = time.time()
                for t, raw in events:
                    if not self._running:
                        return
                    delay = (origin + t) - time.time()
                    if delay > 0:
                        time.sleep(delay)
                    if not self._running:
                        return
                    out.send_message(raw)
                if not loop:
                    break
            self.panic()

        self.stop()
        self._running = True
        self._thread = threading.Thread(target=_play, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # High-level playback — Track list
    # ------------------------------------------------------------------

    def play_tracks(
        self,
        tracks: list[Track],
        *,
        bpm: float = 120.0,
        loop: bool = False,
    ) -> None:
        """Play multiple Track objects in real-time.

        Each track uses its own MIDI channel and sends its own
        program-change + CC setup at t=0.
        """
        if self._midiout is None:
            self.open()

        out = self._midiout
        assert out is not None

        beat_sec = 60.0 / bpm

        # Build combined event timeline across all tracks
        events: list[tuple[float, bytes]] = []

        for t in tracks:
            ch = t.channel
            # Program change at t=0
            events.append((
                0.0,
                mido.Message("program_change", program=t.program, channel=ch).bytes(),
            ))
            # CC setup at t=0
            for cc_num, cc_val in [
                (7, t.volume), (10, t.pan), (11, t.expression),
                (1, t.modulation), (73, t.attack), (72, t.release),
                (91, t.reverb), (93, t.chorus), (3, t.vibrato),
                (64, t.sustain_pedal),
            ]:
                events.append((
                    0.0,
                    mido.Message("control_change", control=cc_num, value=cc_val, channel=ch).bytes(),
                ))
            # Notes
            for n in t.notes:
                onset = max(0.0, n.start) * beat_sec
                offset = (n.start + n.duration) * beat_sec
                events.append((
                    onset,
                    mido.Message("note_on", note=n.pitch, velocity=n.velocity, channel=ch).bytes(),
                ))
                events.append((
                    offset,
                    mido.Message("note_off", note=n.pitch, velocity=0, channel=ch).bytes(),
                ))
                # Per-note expression CCs
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

        # Sort: note_off before note_on at same timestamp
        events.sort(key=lambda e: (e[0], 1 if b"\x90" <= e[1][:1] <= b"\x9f" else 0))

        def _play() -> None:
            while True:
                origin = time.time()
                for t, raw in events:
                    if not self._running:
                        return
                    delay = (origin + t) - time.time()
                    if delay > 0:
                        time.sleep(delay)
                    if not self._running:
                        return
                    out.send_message(raw)
                if not loop:
                    break
            self.panic()

        self.stop()
        self._running = True
        self._thread = threading.Thread(target=_play, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> VirtualMidiOut:
        self.open()
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Convenience — one-shot playback
# ---------------------------------------------------------------------------

def play(
    notes: list[NoteInfo],
    *,
    bpm: float = 120.0,
    port: str | None = None,
    channel: int = 0,
    program: int | None = None,
    loop: bool = False,
) -> VirtualMidiOut:
    """One-liner: play notes through a virtual port.

    Args:
        notes:   NoteInfo list.
        bpm:     Tempo.
        port:    Existing port name (e.g. "IAC Driver Bus 1") or None for
                 a new virtual port called "Melodica".
        channel: MIDI channel.
        program: GM program number (optional).
        loop:    Loop playback.

    Returns:
        The VirtualMidiOut (call .stop() to halt, .wait() to block).
    """
    vmo = VirtualMidiOut("Melodica")
    vmo.open(existing_port=port)
    vmo.play_notes(notes, bpm=bpm, channel=channel, program=program, loop=loop)
    return vmo


def play_tracks(
    tracks: list[Track],
    *,
    bpm: float = 120.0,
    port: str | None = None,
    loop: bool = False,
) -> VirtualMidiOut:
    """One-liner: play tracks through a virtual port."""
    vmo = VirtualMidiOut("Melodica")
    vmo.open(existing_port=port)
    vmo.play_tracks(tracks, bpm=bpm, loop=loop)
    return vmo
