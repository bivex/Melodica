# Copyright (c) 2026 Bivex
#
# Licensed: MIT

"""
reaper_player.py — VST3 instrument host adapter (REAPER batch backend).

Renders Melodica's MIDI output through real VST3 plugins by generating a
REAPER project (.RPP), splicing native plugin presets into the VST state
chunk, then rendering headless via `REAPER -renderproject`.

Unlike pedalboard and DawDreamer, this backend CAN load Surge XT .fxp presets
because REAPER stores the plugin's native state chunk (Surge's `sub3`) in the
project, and a .fxp file contains exactly that same chunk. We splice the .fxp
chunk into a reference REAPER VST block at the byte level.

Usage:
    from melodica.reaper_player import ReaperPlayer

    player = ReaperPlayer()
    player.render_wav(notes, "out.wav", bpm=120,
                      fxp="/Library/Application Support/Surge XT/.../Piano.fxp")

Requirements:
    - REAPER installed (default macOS path; override via reaper_exe)
    - A reference VST state chunk captured once from a default Surge track
      (assets/surge_ref_chunk.txt). Regenerate with capture_reference().

Layer: Infrastructure (adapter) — same tier as midi.py, vst_player.py.
"""

from __future__ import annotations

import base64
import struct
import subprocess
import tempfile
from pathlib import Path

from melodica.types import NoteInfo

# Default macOS REAPER binary
DEFAULT_REAPER_EXE = "/Applications/REAPER.app/Contents/MacOS/REAPER"

# The VST3 identifier line REAPER writes for Surge XT. Captured from a real
# project; the long token is REAPER's VST3 class id and must match the host.
SURGE_VST3_HEADER = (
    '"VST3i: Surge XT (Surge Synth Team) (2->6ch)" "Surge XT.vst3" 0 "" '
    '661331015{ABCDEF019182FAEB566D624153675854} ""'
)

# Reference chunk shipped alongside this module (raw header+state bytes,
# base64-encoded one-per-line exactly as REAPER emits them).
_REF_CHUNK_PATH = Path(__file__).parent / "assets" / "surge_ref_chunk.txt"

_PPQ = 960


# ---------------------------------------------------------------------------
# Surge sub3 chunk splicing
# ---------------------------------------------------------------------------

def _find_sub3(buf: bytes) -> tuple[int, int]:
    """Return (offset, body_size) of the Surge 'sub3' state chunk."""
    off = buf.find(b"sub3")
    if off < 0:
        raise ValueError("no 'sub3' chunk found in VST state")
    size = struct.unpack_from("<I", buf, off + 4)[0]
    return off, size


def _load_ref_vst_bytes() -> bytes:
    """Decode the reference REAPER VST block into raw header+state bytes."""
    if not _REF_CHUNK_PATH.exists():
        raise FileNotFoundError(
            f"reference chunk missing: {_REF_CHUNK_PATH}. "
            "Run ReaperPlayer.capture_reference() once with REAPER available."
        )
    lines = _REF_CHUNK_PATH.read_text().strip().split("\n")
    return b"".join(base64.b64decode(l) for l in lines)


def _splice_fxp(ref_bytes: bytes, fxp_path: str) -> bytes:
    """Replace the reference sub3 chunk with the one from a .fxp file."""
    r_off, r_size = _find_sub3(ref_bytes)
    fdata = Path(fxp_path).read_bytes()
    f_off, f_size = _find_sub3(fdata)
    f_sub3 = fdata[f_off:f_off + 8 + f_size]

    new = ref_bytes[:r_off] + f_sub3 + ref_bytes[r_off + 8 + r_size:]

    # Patch the outer size prefix (8 bytes before sub3 = state size after it)
    pre = r_off - 8
    old_size = struct.unpack_from("<I", ref_bytes, pre)[0]
    new = bytearray(new)
    struct.pack_into("<I", new, pre, old_size + (f_size - r_size))
    return bytes(new)


def _emit_vst_block(vst_bytes: bytes) -> str:
    """Encode raw VST bytes as REAPER's multiline base64 (92, then 210/line)."""
    out = [base64.b64encode(vst_bytes[:92]).decode()]
    rest = vst_bytes[92:]
    for i in range(0, len(rest), 210):
        out.append(base64.b64encode(rest[i:i + 210]).decode())
    return "\n".join(out)


# ---------------------------------------------------------------------------
# MIDI / RPP generation
# ---------------------------------------------------------------------------

def _notes_to_midi_block(notes: list[NoteInfo], bpm: float) -> tuple[str, float]:
    """Build a REAPER inline MIDI <SOURCE MIDI> body. Returns (block, len_sec)."""
    events: list[tuple[int, int, int, int]] = []
    for n in notes:
        on = int(max(0.0, n.start) * _PPQ)
        off = int((n.start + max(1e-3, n.duration)) * _PPQ)
        events.append((on, 0x90, int(n.pitch), int(n.velocity)))
        events.append((off, 0x80, int(n.pitch), 0))
    # note_off before note_on at the same tick
    events.sort(key=lambda e: (e[0], 0 if e[1] == 0x80 else 1))

    lines = ["HASDATA 1 960 QN"]
    last = 0
    for tick, status, pitch, vel in events:
        delta = tick - last
        last = tick
        lines.append(f"E {delta} {status:02x} {pitch:02x} {vel:02x}")
    lines.append(f"E {_PPQ} b0 7b 00")  # all-notes-off tail
    total_ticks = last + _PPQ
    len_sec = (total_ticks / _PPQ) * (60.0 / bpm)
    return "\n".join(lines), len_sec


def _build_rpp(
    vst_block: str,
    notes: list[NoteInfo],
    bpm: float,
    out_wav: str,
    sample_rate: int,
) -> str:
    """Assemble a minimal renderable REAPER project."""
    midi_block, len_sec = _notes_to_midi_block(notes, bpm)
    len_sec += 0.5  # release tail
    return f"""<REAPER_PROJECT 0.1 "7.62" 1
  TEMPO {bpm} 4 4
  SAMPLERATE {sample_rate} 0 0
  RENDER_FILE "{out_wav}"
  RENDER_FMT 0 2 0
  RENDER_1X 0
  RENDER_RANGE 1 0 {len_sec:.6f} 0 0
  RENDER_SRATE {sample_rate}
  RENDER_CHANNELS 2
  <TRACK
    NAME Surge
    <ITEM
      POSITION 0
      LENGTH {len_sec:.6f}
      LOOP 0
      <SOURCE MIDI
{midi_block}
      >
    >
    <FXCHAIN
      <VST {SURGE_VST3_HEADER}
{vst_block}
      >
    >
  >
>
"""


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class ReaperPlayer:
    """Render Melodica output through Surge XT via REAPER batch rendering.

    Supports native .fxp presets by splicing Surge's state chunk into the
    REAPER project.
    """

    def __init__(
        self,
        *,
        reaper_exe: str = DEFAULT_REAPER_EXE,
        sample_rate: int = 44100,
        timeout: float = 120.0,
    ) -> None:
        self._exe = reaper_exe
        self._sr = sample_rate
        self._timeout = timeout
        if not Path(reaper_exe).exists():
            raise FileNotFoundError(f"REAPER not found at {reaper_exe}")

    def render_wav(
        self,
        notes: list[NoteInfo],
        path: str | Path,
        *,
        bpm: float = 120.0,
        fxp: str | None = None,
    ) -> Path:
        """Render notes through Surge XT (optionally with a .fxp preset) to WAV."""
        if not notes:
            raise ValueError("no notes to render")

        ref = _load_ref_vst_bytes()
        vst_bytes = _splice_fxp(ref, fxp) if fxp else ref
        block = _emit_vst_block(vst_bytes)

        out_path = Path(path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)

        rpp = _build_rpp(block, notes, bpm, str(out_path), self._sr)
        with tempfile.NamedTemporaryFile(
            "w", suffix=".rpp", delete=False
        ) as tf:
            rpp_path = tf.name
            tf.write(rpp)
        try:
            subprocess.run(
                [self._exe, "-renderproject", rpp_path, "-nosplash"],
                check=True,
                capture_output=True,
                timeout=self._timeout,
            )
        finally:
            Path(rpp_path).unlink(missing_ok=True)

        if not out_path.exists():
            raise RuntimeError(f"REAPER did not produce {out_path}")
        return out_path

    def render_mp3(
        self,
        notes: list[NoteInfo],
        path: str | Path,
        *,
        bpm: float = 120.0,
        fxp: str | None = None,
    ) -> Path:
        """Render to MP3 (WAV via REAPER, then ffmpeg encode)."""
        path = Path(path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        try:
            self.render_wav(notes, wav_path, bpm=bpm, fxp=fxp)
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav_path,
                 "-codec:a", "libmp3lame", "-b:a", "320k", str(path)],
                check=True,
                capture_output=True,
            )
        finally:
            Path(wav_path).unlink(missing_ok=True)
        return path

    @staticmethod
    def capture_reference(
        out_path: str | Path = _REF_CHUNK_PATH,
        *,
        reaper_exe: str = DEFAULT_REAPER_EXE,
    ) -> Path:
        """Capture a fresh Surge reference VST block via a one-off REAPER run.

        Writes the multiline base64 VST block to out_path. Run once per machine
        (the VST3 class id is host-specific).
        """
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        lua = f"""
local tr_idx = reaper.InsertTrackAtIndex(0, false)
local tr = reaper.GetTrack(0, 0)
local fx = reaper.TrackFX_AddByName(tr, "Surge XT", false, -1)
local ok, chunk = reaper.GetTrackStateChunk(tr, "", false)
local f = io.open("{out_path}.raw", "w")
if f then f:write(chunk); f:close() end
reaper.Main_OnCommand(40004, 0)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".lua", delete=False) as tf:
            lua_path = tf.name
            tf.write(lua)
        try:
            subprocess.run(
                [reaper_exe, "-new", "-nosplash", lua_path],
                check=True, capture_output=True, timeout=60,
            )
        finally:
            Path(lua_path).unlink(missing_ok=True)

        # Extract the <VST ...> base64 block from the captured track chunk
        raw = Path(f"{out_path}.raw").read_text()
        Path(f"{out_path}.raw").unlink(missing_ok=True)
        import re
        m = re.search(r'<VST "[^"]*" "[^"]*"[^\n]*\n(.*?)\n>', raw, re.DOTALL)
        if not m:
            raise RuntimeError("could not find VST block in captured chunk")
        out_path.write_text(m.group(1))
        return out_path
