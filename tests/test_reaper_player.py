# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
Tests for melodica.reaper_player.

Pure helpers (sub3 splicing, MIDI/RPP generation, base64 block emission) are
tested directly with synthetic and real chunk bytes. Player methods are tested
with subprocess/REAPER mocked — no REAPER process is launched.
"""

from __future__ import annotations

import base64
import struct
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from melodica.types import NoteInfo
from melodica import reaper_player as rp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_sub3(body: bytes, *, prefix_size: int | None = None) -> bytes:
    """Build a minimal blob containing an 8-byte outer prefix + sub3 chunk.

    Layout mirrors what _splice_fxp expects:
      [outer prefix: <I size><I ver>][ 'sub3' ][<I body_size>][ body ]
    """
    sub3 = b"sub3" + struct.pack("<I", len(body)) + body
    pre_size = prefix_size if prefix_size is not None else len(sub3)
    prefix = struct.pack("<I", pre_size) + struct.pack("<I", 1)
    return prefix + sub3


def _notes(n: int = 3) -> list[NoteInfo]:
    return [
        NoteInfo(pitch=60 + i, start=float(i), duration=1.0, velocity=80)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# _find_sub3
# ---------------------------------------------------------------------------

class TestFindSub3:

    def test_finds_offset_and_size(self):
        blob = _make_sub3(b"HELLO_PATCH")
        off, size = rp._find_sub3(blob)
        assert blob[off:off + 4] == b"sub3"
        assert size == len(b"HELLO_PATCH")

    def test_raises_when_missing(self):
        with pytest.raises(ValueError, match="no 'sub3'"):
            rp._find_sub3(b"no chunk here")


# ---------------------------------------------------------------------------
# _splice_fxp
# ---------------------------------------------------------------------------

class TestSpliceFxp:

    def test_replaces_body_and_patches_prefix(self, tmp_path: Path):
        ref = _make_sub3(b"DEFAULT_PATCH_BODY", prefix_size=100)
        fxp_body = b"REAL_PIANO_PATCH"
        fxp_file = tmp_path / "piano.fxp"
        # .fxp also carries a sub3 chunk (with arbitrary leading bytes)
        fxp_file.write_bytes(b"CcnK\x00\x00\x00\x00" + _make_sub3(fxp_body))

        out = rp._splice_fxp(ref, str(fxp_file))

        # spliced body present, old body gone
        assert fxp_body in out
        assert b"DEFAULT_PATCH_BODY" not in out

        # outer prefix size adjusted by the body-size delta
        r_off, _ = rp._find_sub3(ref)
        new_off, new_size = rp._find_sub3(out)
        new_prefix = struct.unpack_from("<I", out, new_off - 8)[0]
        delta = len(fxp_body) - len(b"DEFAULT_PATCH_BODY")
        assert new_prefix == 100 + delta
        assert new_size == len(fxp_body)

    def test_preserves_surrounding_bytes(self, tmp_path: Path):
        # bytes before the prefix and after the sub3 chunk must survive
        core = _make_sub3(b"OLD", prefix_size=11)
        ref = b"<<<HEAD>>>" + core + b"<<<TAIL>>>"
        fxp_file = tmp_path / "p.fxp"
        fxp_file.write_bytes(_make_sub3(b"NEWBODY"))

        out = rp._splice_fxp(ref, str(fxp_file))
        assert out.startswith(b"<<<HEAD>>>")
        assert out.endswith(b"<<<TAIL>>>")
        assert b"NEWBODY" in out


# ---------------------------------------------------------------------------
# _emit_vst_block
# ---------------------------------------------------------------------------

class TestEmitVstBlock:

    def test_first_line_is_92_bytes(self):
        data = bytes(range(256)) * 4  # 1024 bytes
        block = rp._emit_vst_block(data)
        lines = block.split("\n")
        assert base64.b64decode(lines[0]) == data[:92]

    def test_round_trip_reconstructs_input(self):
        data = bytes((i * 7) % 256 for i in range(1000))
        block = rp._emit_vst_block(data)
        lines = block.split("\n")
        rebuilt = b"".join(base64.b64decode(l) for l in lines)
        assert rebuilt == data

    def test_body_lines_decode_to_210_bytes(self):
        data = bytes(500)  # 92 + 408 -> body lines of 210, 198
        block = rp._emit_vst_block(data)
        lines = block.split("\n")
        # first body line (index 1) is 210 bytes
        assert len(base64.b64decode(lines[1])) == 210


# ---------------------------------------------------------------------------
# _notes_to_midi_block
# ---------------------------------------------------------------------------

class TestNotesToMidiBlock:

    def test_has_data_header(self):
        block, _ = rp._notes_to_midi_block(_notes(1), bpm=120)
        assert block.startswith("HASDATA 1 960 QN")

    def test_note_on_and_off_emitted(self):
        block, _ = rp._notes_to_midi_block(
            [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100)], bpm=120
        )
        # note_on 0x90 pitch 0x3c vel 0x64, note_off 0x80
        assert "90 3c 64" in block
        assert "80 3c 00" in block

    def test_length_scales_with_bpm(self):
        notes = [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]
        _, len_120 = rp._notes_to_midi_block(notes, bpm=120)
        _, len_60 = rp._notes_to_midi_block(notes, bpm=60)
        # half the tempo -> roughly double the duration
        assert len_60 == pytest.approx(len_120 * 2, rel=0.01)

    def test_note_off_before_note_on_same_tick(self):
        # two notes where one ends exactly as another starts
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80),
        ]
        block, _ = rp._notes_to_midi_block(notes, bpm=120)
        lines = [l for l in block.split("\n") if l.startswith("E ")]
        # find indices of the note_off for pitch 60 and note_on for pitch 64
        off_idx = next(i for i, l in enumerate(lines) if "80 3c 00" in l)
        on_idx = next(i for i, l in enumerate(lines) if "90 40" in l)
        assert off_idx < on_idx


# ---------------------------------------------------------------------------
# _build_rpp
# ---------------------------------------------------------------------------

class TestBuildRpp:

    def test_contains_required_sections(self):
        rpp = rp._build_rpp("BLOCKB64", _notes(2), bpm=140,
                            out_wav="/tmp/out.wav", sample_rate=48000)
        assert rpp.startswith("<REAPER_PROJECT")
        assert "TEMPO 140 4 4" in rpp
        assert "SAMPLERATE 48000" in rpp
        assert 'RENDER_FILE "/tmp/out.wav"' in rpp
        assert "RENDER_SRATE 48000" in rpp
        assert "<SOURCE MIDI" in rpp
        assert "BLOCKB64" in rpp
        assert rp.SURGE_VST3_HEADER in rpp

    def test_release_tail_added(self):
        # len_sec in RENDER_RANGE should exceed the raw MIDI length (tail +0.5)
        notes = [NoteInfo(pitch=60, start=0.0, duration=2.0, velocity=80)]
        _, raw_len = rp._notes_to_midi_block(notes, bpm=120)
        rpp = rp._build_rpp("B", notes, bpm=120, out_wav="/x.wav", sample_rate=44100)
        import re
        m = re.search(r"RENDER_RANGE 1 0 ([\d.]+)", rpp)
        assert m is not None
        assert float(m.group(1)) == pytest.approx(raw_len + 0.5, abs=1e-5)


# ---------------------------------------------------------------------------
# ReaperPlayer (subprocess mocked)
# ---------------------------------------------------------------------------

class TestReaperPlayer:

    def test_init_raises_when_exe_missing(self):
        with pytest.raises(FileNotFoundError, match="REAPER not found"):
            rp.ReaperPlayer(reaper_exe="/nonexistent/REAPER")

    def _player(self) -> rp.ReaperPlayer:
        # bypass the exe-exists check
        with patch.object(rp.Path, "exists", return_value=True):
            return rp.ReaperPlayer(reaper_exe="/fake/REAPER")

    def test_render_wav_empty_notes_raises(self):
        player = self._player()
        with pytest.raises(ValueError, match="no notes"):
            player.render_wav([], "/tmp/out.wav")

    def test_render_wav_invokes_reaper_and_returns_path(self, tmp_path: Path):
        player = self._player()
        out = tmp_path / "render.wav"

        captured_cmd = {}

        def fake_run(cmd, **kwargs):
            captured_cmd["cmd"] = cmd
            # simulate REAPER producing the file
            out.write_bytes(b"RIFF....WAVEfake")
            return MagicMock(returncode=0)

        with patch("melodica.reaper_player._load_ref_vst_bytes",
                   return_value=_make_sub3(b"REFBODY")), \
             patch("subprocess.run", side_effect=fake_run):
            result = player.render_wav(_notes(2), out, bpm=120)

        assert result == out.resolve()
        cmd = captured_cmd["cmd"]
        assert cmd[0] == "/fake/REAPER"
        assert "-renderproject" in cmd
        assert "-nosplash" in cmd

    def test_render_wav_raises_if_no_output(self, tmp_path: Path):
        player = self._player()
        out = tmp_path / "missing.wav"

        with patch("melodica.reaper_player._load_ref_vst_bytes",
                   return_value=_make_sub3(b"REF")), \
             patch("subprocess.run", return_value=MagicMock(returncode=0)):
            with pytest.raises(RuntimeError, match="did not produce"):
                player.render_wav(_notes(1), out)

    def test_render_wav_splices_when_fxp_given(self, tmp_path: Path):
        player = self._player()
        out = tmp_path / "r.wav"
        fxp = tmp_path / "p.fxp"
        fxp.write_bytes(_make_sub3(b"PIANOBODY"))

        with patch("melodica.reaper_player._load_ref_vst_bytes",
                   return_value=_make_sub3(b"DEFAULT", prefix_size=15)) as mref, \
             patch("melodica.reaper_player._splice_fxp",
                   wraps=rp._splice_fxp) as mspl, \
             patch("subprocess.run",
                   side_effect=lambda *a, **k: out.write_bytes(b"w") or MagicMock()):
            player.render_wav(_notes(1), out, fxp=str(fxp))

        mref.assert_called_once()
        mspl.assert_called_once()
        # splice called with ref bytes + the fxp path
        assert mspl.call_args[0][1] == str(fxp)

    def test_render_mp3_calls_ffmpeg(self, tmp_path: Path):
        player = self._player()
        out_mp3 = tmp_path / "track.mp3"
        calls = []

        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return MagicMock(returncode=0)

        with patch.object(player, "render_wav", return_value=tmp_path / "x.wav") as mrw, \
             patch("subprocess.run", side_effect=fake_run):
            result = player.render_mp3(_notes(1), out_mp3, bpm=110, fxp=None)

        assert result == out_mp3
        mrw.assert_called_once()
        # ffmpeg invoked with mp3 target + 320k
        ff = calls[-1]
        assert ff[0] == "ffmpeg"
        assert str(out_mp3) in ff
        assert "320k" in ff


# ---------------------------------------------------------------------------
# Reference asset integration (uses the real shipped chunk if present)
# ---------------------------------------------------------------------------

class TestReferenceAsset:

    def test_real_reference_loads_and_has_sub3(self):
        if not rp._REF_CHUNK_PATH.exists():
            pytest.skip("reference chunk asset not present")
        ref = rp._load_ref_vst_bytes()
        off, size = rp._find_sub3(ref)
        assert off > 0
        assert size > 0
        # round-trips through the block emitter
        block = rp._emit_vst_block(ref)
        rebuilt = b"".join(base64.b64decode(l) for l in block.split("\n"))
        assert rebuilt == ref
