# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
Tests for VSTPlayer and _render_mp3 in album_welcome_to_home.

All VST/pedalboard/ffmpeg calls are mocked — no real plugins required.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from melodica.types import NoteInfo


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _notes(n: int = 4, start_offset: float = 0.0) -> list[NoteInfo]:
    return [
        NoteInfo(pitch=60 + i, start=start_offset + float(i), duration=1.0, velocity=64)
        for i in range(n)
    ]


def _audio(samples: int = 44100, channels: int = 2) -> np.ndarray:
    return np.zeros((channels, samples), dtype=np.float32)


def _fake_tmp(path: str = "/tmp/fake.wav"):
    """Return a mock NamedTemporaryFile context manager."""
    inner = MagicMock()
    inner.name = path
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=inner)
    cm.__exit__ = MagicMock(return_value=False)
    return cm


def _fake_audio_file_cls():
    """Return a fake AudioFile class usable as a context manager."""
    inst = MagicMock()
    inst.__enter__ = MagicMock(return_value=inst)
    inst.__exit__ = MagicMock(return_value=False)
    cls = MagicMock(return_value=inst)
    return cls, inst


def _inject_pedalboard(monkeypatch: pytest.MonkeyPatch):
    """Inject stub pedalboard modules into sys.modules."""
    pb: types.ModuleType = types.ModuleType("pedalboard")
    pb_io: types.ModuleType = types.ModuleType("pedalboard.io")

    fake_vst_cls = MagicMock()
    setattr(pb, "VST3Plugin", fake_vst_cls)
    setattr(pb, "Pedalboard", MagicMock())

    af_cls, af_inst = _fake_audio_file_cls()
    setattr(pb_io, "AudioFile", af_cls)

    monkeypatch.setitem(sys.modules, "pedalboard", pb)
    monkeypatch.setitem(sys.modules, "pedalboard.io", pb_io)
    return fake_vst_cls, af_cls, af_inst


# ---------------------------------------------------------------------------
# VSTPlayer unit tests
# ---------------------------------------------------------------------------

class TestVSTPlayer:

    def test_plugin_lazy_loaded(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        from melodica.vst_player import VSTPlayer
        mock_cls = MagicMock()
        with patch("melodica.vst_player.VST3Plugin", mock_cls):
            player = VSTPlayer("/fake/Surge.vst3")
            mock_cls.assert_not_called()
            _ = player.plugin
            mock_cls.assert_called_once()

    def test_render_notes_returns_audio(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        audio = _audio()
        mock_plugin_inst = MagicMock(return_value=audio)
        mock_cls = MagicMock(return_value=mock_plugin_inst)

        from melodica.vst_player import VSTPlayer
        with patch("melodica.vst_player.VST3Plugin", mock_cls):
            player = VSTPlayer("/fake/Surge.vst3", normalize=False)
            result = player.render_notes(_notes(), bpm=120.0)

        assert result.shape == (2, 44100)
        mock_plugin_inst.assert_called_once()

    @pytest.mark.skip(reason="Tied to old peak normalization logic (dropped for 32-bit float workflow)")
    def test_normalize_scales_to_09(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        loud = np.ones((2, 100), dtype=np.float32) * 2.0
        mock_cls = MagicMock(return_value=MagicMock(return_value=loud))

        from melodica.vst_player import VSTPlayer
        with patch("melodica.vst_player.VST3Plugin", mock_cls):
            player = VSTPlayer("/fake/Surge.vst3", normalize=True)
            result = player.render_notes(_notes(), bpm=120.0)

        assert pytest.approx(float(np.max(np.abs(result))), abs=1e-5) == 0.9

    def test_normalize_false_unchanged(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        loud = np.ones((2, 100), dtype=np.float32) * 2.0
        mock_cls = MagicMock(return_value=MagicMock(return_value=loud))

        from melodica.vst_player import VSTPlayer
        with patch("melodica.vst_player.VST3Plugin", mock_cls):
            player = VSTPlayer("/fake/Surge.vst3", normalize=False)
            result = player.render_notes(_notes(), bpm=120.0)

        assert float(np.max(np.abs(result))) == pytest.approx(2.0)

    def test_context_manager_closes_plugin(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        mock_cls = MagicMock()

        from melodica.vst_player import VSTPlayer
        with patch("melodica.vst_player.VST3Plugin", mock_cls):
            with VSTPlayer("/fake/Surge.vst3") as player:
                _ = player.plugin
            assert player._plugin is None

    def test_load_preset_fxp_calls_loader(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        mock_cls = MagicMock()

        from melodica.vst_player import VSTPlayer
        with patch("melodica.vst_player.VST3Plugin", mock_cls), \
             patch("melodica.vst_player._load_surge_fxp", return_value=7) as mock_fxp:
            player = VSTPlayer("/fake/Surge.vst3")
            result = player.load_preset("/some/preset.fxp")

        mock_fxp.assert_called_once()
        assert result == 7

    def test_load_preset_non_fxp_delegates(self, monkeypatch: pytest.MonkeyPatch):
        _inject_pedalboard(monkeypatch)
        mock_plugin_inst = MagicMock()
        mock_cls = MagicMock(return_value=mock_plugin_inst)

        from melodica.vst_player import VSTPlayer
        with patch("melodica.vst_player.VST3Plugin", mock_cls):
            player = VSTPlayer("/fake/Surge.vst3")
            player.load_preset("/some/preset.vstpreset")

        mock_plugin_inst.load_preset.assert_called_once_with("/some/preset.vstpreset")


# ---------------------------------------------------------------------------
# _render_mp3 tests
# ---------------------------------------------------------------------------

def _load_album_mod(monkeypatch: pytest.MonkeyPatch):
    """Reload album module with pedalboard injected."""
    import importlib
    _inject_pedalboard(monkeypatch)
    import scripts.albums.ambient.album_welcome_to_home as mod
    importlib.reload(mod)
    return mod


class TestRenderMp3:

    def test_empty_tracks_no_ffmpeg(self, monkeypatch: pytest.MonkeyPatch):
        mod = _load_album_mod(monkeypatch)
        with patch("subprocess.run") as mock_sub, \
             patch("tempfile.NamedTemporaryFile", return_value=_fake_tmp()), \
             patch("pathlib.Path.unlink"):
            mod._render_mp3({}, Path("/out/track.mid"), 120.0)
        mock_sub.assert_not_called()

    def test_no_preset_skips_track(self, monkeypatch: pytest.MonkeyPatch):
        mod = _load_album_mod(monkeypatch)
        with patch("subprocess.run") as mock_sub, \
             patch("tempfile.NamedTemporaryFile", return_value=_fake_tmp()), \
             patch("pathlib.Path.unlink"):
            mod._render_mp3(
                {"unknown": _notes()},
                Path("/out/track.mid"),
                120.0,
                track_presets={"piano": "/p/piano.fxp"},
            )
        mock_sub.assert_not_called()

    def test_fresh_player_per_track(self, monkeypatch: pytest.MonkeyPatch):
        """Two tracks → two separate VSTPlayer instantiations."""
        mod = _load_album_mod(monkeypatch)
        audio = _audio()
        mock_plugin = MagicMock(return_value=audio)
        mock_vst_cls = MagicMock(return_value=mock_plugin)

        presets = {"piano": "/p/piano.fxp", "harp": "/p/harp.fxp"}
        tracks = {"piano": _notes(), "harp": _notes()}

        with patch("melodica.vst_player.VST3Plugin", mock_vst_cls), \
             patch("subprocess.run"), \
             patch("tempfile.NamedTemporaryFile", return_value=_fake_tmp()), \
             patch("pathlib.Path.unlink"):
            mod._render_mp3(tracks, Path("/out/track.mid"), 120.0, track_presets=presets)

        assert mock_vst_cls.call_count == 2

    def test_ffmpeg_produces_mp3(self, monkeypatch: pytest.MonkeyPatch):
        mod = _load_album_mod(monkeypatch)
        audio = _audio()
        mock_vst_cls = MagicMock(return_value=MagicMock(return_value=audio))

        with patch("melodica.vst_player.VST3Plugin", mock_vst_cls), \
             patch("melodica.vst_player.VSTPlayer.load_preset", return_value=1), \
             patch("subprocess.run") as mock_sub, \
             patch("tempfile.NamedTemporaryFile", return_value=_fake_tmp()), \
             patch("pathlib.Path.unlink"):
            mod._render_mp3(
                {"piano": _notes()},
                Path("/out/track.mid"),
                120.0,
                track_presets={"piano": "/p/piano.fxp"},
            )

        mock_sub.assert_called_once()
        cmd: list[str] = mock_sub.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert any(a.endswith(".mp3") for a in cmd)
        assert "320k" in cmd

    @pytest.mark.skip(reason="Tied to old peak normalization logic (dropped for 32-bit float workflow)")
    def test_mix_peak_normalised(self, monkeypatch: pytest.MonkeyPatch):
        mod = _load_album_mod(monkeypatch)
        loud = np.ones((2, 44100), dtype=np.float32) * 5.0
        mock_vst_cls = MagicMock(return_value=MagicMock(return_value=loud))

        written: list[np.ndarray] = []

        class CaptureAudioFile:
            def __init__(self, *a, **kw): pass
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def write(self, buf: np.ndarray): written.append(buf.copy())

        with patch("melodica.vst_player.VST3Plugin", mock_vst_cls), \
             patch("melodica.vst_player.VSTPlayer.load_preset", return_value=1), \
             patch("subprocess.run"), \
             patch("tempfile.NamedTemporaryFile", return_value=_fake_tmp()), \
             patch("pathlib.Path.unlink"), \
             patch("pedalboard.io.AudioFile", CaptureAudioFile):
            mod._render_mp3(
                {"piano": _notes()},
                Path("/out/track.mid"),
                120.0,
                track_presets={"piano": "/p/piano.fxp"},
            )

        assert written, "AudioFile.write was never called"
        peak = float(np.max(np.abs(written[0])))
        assert peak == pytest.approx(0.9, abs=1e-4)

    def test_buffer_alignment_no_crash(self, monkeypatch: pytest.MonkeyPatch):
        """Short + long track buffers are padded and summed without error."""
        mod = _load_album_mod(monkeypatch)

        call_idx = 0
        audios = [_audio(22050), _audio(88200)]

        def factory(*a, **kw):
            nonlocal call_idx
            inst = MagicMock()
            inst.return_value = audios[min(call_idx, len(audios) - 1)]
            call_idx += 1
            return inst

        mock_vst_cls = MagicMock(side_effect=factory)

        with patch("melodica.vst_player.VST3Plugin", mock_vst_cls), \
             patch("subprocess.run"), \
             patch("tempfile.NamedTemporaryFile", return_value=_fake_tmp()), \
             patch("pathlib.Path.unlink"):
            mod._render_mp3(
                {"piano": _notes(), "harp": _notes()},
                Path("/out/track.mid"),
                120.0,
                track_presets={"piano": "/p/piano.fxp", "harp": "/p/harp.fxp"},
            )
        # No exception = pass
