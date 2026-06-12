# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
reaper_project.py — Generate a REAPER .RPP project file from Melodica track data.

Layer: Infrastructure (adapter)

Given the same tracks_data + bpm that export_multitrack_midi receives, produces
a ready-to-open .RPP with:
  - Correct tempo
  - One MIDI track per instrument
  - GM program set on each track via REAPER's built-in ReaSynth (or empty FX chain
    so you can drop your own VST)
  - Separate colour-coded track folders: Strings / Brass / Woodwinds / Keys /
    Bass / Percussion / Other
  - Pan and volume from the same sources midi.py uses
  - MIDI items containing all notes, written as inline REAPER MIDI source chunks

Usage:
    from melodica.reaper_project import export_reaper_project
    export_reaper_project(tracks_data, "output/my_album/my_track.rpp", bpm=120.0)

Or via export_multitrack_midi(..., reaper_project=True) — the .rpp is written
next to the .mid file automatically.
"""

from __future__ import annotations

import base64
import struct
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from melodica.types import NoteInfo

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TICKS_PER_BEAT = 960  # PPQ used in generated MIDI items

# REAPER track colours (BGR packed int, alpha=0xff000000 or just use hex).
# These are used to colour-code instrument families visually.
_FAMILY_COLOURS: dict[str, int] = {
    "strings":    0xFF5B7FBF,  # blue-ish
    "brass":      0xFFBF7F3A,  # orange
    "woodwinds":  0xFF3ABF6A,  # green
    "keys":       0xFFBFBF3A,  # yellow
    "bass":       0xFF7F3ABF,  # purple
    "percussion": 0xFFBF3A3A,  # red
    "other":      0xFF606060,  # grey
}

_STRINGS_KW   = ("violin", "viola", "cello", "contrabass", "strings",
                 "tremolo", "pizzicato", "legato", "ensemble")
_BRASS_KW     = ("trumpet", "trombone", "tuba", "horn", "brass")
_WOODWINDS_KW = ("flute", "oboe", "clarinet", "bassoon", "piccolo",
                 "recorder", "pan_flute", "shakuhachi", "sax", "woodwind")
_KEYS_KW      = ("piano", "organ", "harpsichord", "accordion", "celesta",
                 "vibraphone", "marimba", "xylophone", "glock", "bells",
                 "harp", "mallet", "tubular", "chime", "kalimba")
_BASS_KW      = ("bass",)
_PERC_KW      = ("drum", "percussion", "perc", "kit", "taiko", "ghost",
                 "timpani", "snare", "kick", "cymbal", "hihat")


def _instrument_family(name: str) -> str:
    low = name.lower()
    if any(k in low for k in _PERC_KW):
        return "percussion"
    if any(k in low for k in _BASS_KW):
        return "bass"
    if any(k in low for k in _STRINGS_KW):
        return "strings"
    if any(k in low for k in _BRASS_KW):
        return "brass"
    if any(k in low for k in _WOODWINDS_KW):
        return "woodwinds"
    if any(k in low for k in _KEYS_KW):
        return "keys"
    return "other"


# ---------------------------------------------------------------------------
# MIDI item builder — inline REAPER source chunk
# ---------------------------------------------------------------------------

_PERC_KEYWORDS = ("drum", "percussion", "perc", "kit", "taiko", "ghost")


def _is_percussion(name: str) -> bool:
    return any(k in name.lower() for k in _PERC_KEYWORDS)


def _notes_to_reaper_midi_chunk(
    notes: list[NoteInfo],
    bpm: float,
    channel: int,
    program: int,
) -> list[str]:
    """
    Build the MIDI source lines for a REAPER inline <SOURCE MIDI> block.
    Returns a list of text lines (without the outer <SOURCE MIDI> / > tags).
    """
    tpb = TICKS_PER_BEAT

    # Collect events: (tick, priority, type, b1, b2)
    # priority: lower = earlier in tie-break (note_off=0 before note_on=1)
    events: list[tuple[int, int, str, int, int]] = []

    # Program change at tick 0
    events.append((0, 0, "prog", program, 0))

    for n in notes:
        pitch = int(round(float(n.pitch)))
        pitch = max(0, min(127, pitch))
        vel = max(1, min(127, int(n.velocity)))
        on_tick = max(0, round(float(n.start) * tpb))
        dur_ticks = max(1, round(float(n.duration) * tpb))
        off_tick = on_tick + dur_ticks

        events.append((on_tick,  1, "on",  pitch, vel))
        events.append((off_tick, 0, "off", pitch, 0))

    events.sort(key=lambda e: (e[0], e[1]))

    lines: list[str] = []
    lines.append(f"HASDATA 1 {tpb} QN")

    prev_tick = 0
    for tick, _pri, etype, b1, b2 in events:
        delta = tick - prev_tick
        prev_tick = tick
        if etype == "prog":
            status = 0xC0 | channel
            lines.append(f"E {delta} {status:02x} {b1:02x} 00")
        elif etype == "on":
            status = 0x90 | channel
            lines.append(f"E {delta} {status:02x} {b1:02x} {b2:02x}")
        elif etype == "off":
            status = 0x80 | channel
            lines.append(f"E {delta} {status:02x} {b1:02x} 00")

    # All-notes-off tail
    lines.append(f"E 0 b{channel:x} 7b 00")
    lines.append("E 1 ff 2f 00")  # end-of-track meta

    return lines


# ---------------------------------------------------------------------------
# Track colour helper
# ---------------------------------------------------------------------------

def _track_colour(name: str) -> int:
    family = _instrument_family(name)
    return _FAMILY_COLOURS.get(family, _FAMILY_COLOURS["other"])


# ---------------------------------------------------------------------------
# RPP builder
# ---------------------------------------------------------------------------

def _beat_to_seconds(beat: float, bpm: float) -> float:
    return beat * 60.0 / bpm


def export_reaper_project(
    tracks_data: dict[str, list[NoteInfo]],
    path: str | Path,
    *,
    bpm: float = 120.0,
    time_sig: tuple[int, int] = (4, 4),
    instruments: dict[str, int] | None = None,
    volumes: dict[str, int] | None = None,
    sample_rate: int = 48000,
) -> None:
    """
    Write a REAPER .RPP project file.

    Parameters mirror export_multitrack_midi so they can be forwarded directly.

    tracks_data : { "TrackName": [NoteInfo, ...], ... }
    path        : output .rpp file path
    bpm         : project tempo
    time_sig    : (numerator, denominator)
    instruments : { "TrackName": gm_program (0-127) }
    volumes     : { "TrackName": cc7 value (0-127) }
    sample_rate : project sample rate (default 48000)
    """
    from melodica.midi import GM_INSTRUMENTS  # avoid circular at module load

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Compute total project length in seconds (max note end + 2 s tail)
    max_beat = 0.0
    for notes in tracks_data.values():
        for n in notes:
            end = float(n.start) + float(n.duration)
            if end > max_beat:
                max_beat = end
    project_len = _beat_to_seconds(max_beat, bpm) + 2.0

    ts_num, ts_den = time_sig

    lines: list[str] = []

    def w(text: str, indent: int = 0) -> None:
        lines.append("  " * indent + text)

    # ---- Project header ----
    w("<REAPER_PROJECT 0.1 \"7.0\" 1700000000")
    w(f"  TEMPO {bpm:.6f} {ts_num} {ts_den}")
    w(f"  SAMPLERATE {sample_rate} 0 0")
    w(f"  RENDER_FILE \"\"")
    w(f"  RENDER_FMT 0 2 0")
    w(f"  RENDER_1X 0")
    w(f"  RENDER_RANGE 1 0 {project_len:.6f} 0 0")
    w(f"  RENDER_RESAMPLE 3 0 1")

    # Master track (empty, just for global bus)
    w("  <MASTERTRACK")
    w("    VOLPAN 1 0 1 -1")
    w("    DEFCHAN 0")
    w("  >")

    # ---- Instrument tracks ----
    # Assign channels: percussion → ch9, rest skip ch9
    track_channel: dict[str, int] = {}
    next_ch = 0
    for name in tracks_data:
        if _is_percussion(name):
            track_channel[name] = 9
        else:
            if next_ch == 9:
                next_ch = 10
            track_channel[name] = next_ch
            next_ch += 1
            if next_ch > 15:
                next_ch = 15  # clamp; beyond 16 tracks share last channel

    for name, notes in tracks_data.items():
        if not notes:
            continue

        channel = track_channel[name]

        # Resolve GM program
        program = 0
        if instruments and name in instruments:
            program = instruments[name]
        else:
            low = name.lower()
            if low in GM_INSTRUMENTS:
                program = GM_INSTRUMENTS[low]
            else:
                for key in sorted(GM_INSTRUMENTS.keys(), key=len, reverse=True):
                    if key in low:
                        program = GM_INSTRUMENTS[key]
                        break

        # Volume: cc7 → linear REAPER fader (0-127 → 0.0-1.0 approx)
        vol_cc = volumes.get(name, 100) if volumes else 100
        vol_lin = vol_cc / 100.0

        colour = _track_colour(name)

        # Track start/end in seconds
        min_beat = min((float(n.start) for n in notes), default=0.0)
        max_beat_t = max((float(n.start) + float(n.duration) for n in notes), default=0.0)
        item_start = _beat_to_seconds(min_beat, bpm)
        item_len   = _beat_to_seconds(max_beat_t - min_beat, bpm) + 0.1

        midi_lines = _notes_to_reaper_midi_chunk(notes, bpm, channel, program)

        w("  <TRACK")
        w(f"    NAME \"{name}\"")
        w(f"    PEAKCOL {colour}")
        w(f"    VOLPAN {vol_lin:.6f} 0 1 -1")
        w(f"    MIDIOUT -1")
        w(f"    ISBUS 0 0")
        w("    <ITEM")
        w(f"      POSITION {item_start:.6f}")
        w(f"      LENGTH {item_len:.6f}")
        w(f"      NAME \"{name}\"")
        w(f"      VOLPAN 1 0 1 -1")
        w("      <SOURCE MIDI")
        for ml in midi_lines:
            w(f"        {ml}")
        w("      >")
        w("    >")
        w("  >")

    w(">")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
