# Copyright (c) 2026 Bivex
#
# Licensed: MIT

"""
dawdreamer_player.py — VST3 instrument host adapter (DawDreamer backend).

Renders Melodica's MIDI output through real VST3 plugins offline using
DawDreamer's RenderEngine. Drop-in alternative to vst_player.VSTPlayer with
a richer parameter surface (e.g. Surge XT exposes 2855 params vs 775 under
pedalboard) and reliable save_state/load_state preset persistence.

Usage:
    from melodica.dawdreamer_player import DawDreamerPlayer

    player = DawDreamerPlayer("/Library/Audio/Plug-Ins/VST3/Surge XT.vst3")
    player.render_wav(notes, bpm=120, path="out.wav")

Preset workflow (Surge XT cannot load .fxp headless; .vstpreset only):
    # one-time: configure a patch (GUI or params), then snapshot its state
    player.save_state("piano.bin")
    # forever after: load headless
    player.load_state("piano.bin")

Requires: dawdreamer (pip install dawdreamer). Python <= 3.12 — no 3.13 wheels yet.

Layer: Infrastructure (adapter) — same tier as midi.py and vst_player.py.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import numpy as np

try:
    import dawdreamer as daw
except ImportError:
    raise ImportError(
        "dawdreamer is required for the DawDreamer backend. "
        "Install with: pip install dawdreamer (Python <= 3.12)"
    )

from melodica.types import NoteInfo, Track


def _total_duration(notes: list[NoteInfo], bpm: float) -> float:
    beat_sec = 60.0 / bpm
    if not notes:
        return 1.0
    return max(n.start + n.duration for n in notes) * beat_sec + 0.5


def _total_tracks_duration(tracks: list[Track], bpm: float) -> float:
    beat_sec = 60.0 / bpm
    end = 0.0
    for t in tracks:
        for n in t.notes:
            end = max(end, n.start + n.duration)
    return end * beat_sec + 0.5


class DawDreamerPlayer:
    """Load a VST3 instrument and render Melodica output through DawDreamer.

    Usage:
        player = DawDreamerPlayer("/Library/Audio/Plug-Ins/VST3/Surge XT.vst3")
        player.render_wav(notes, bpm=120, path="out.wav")
    """

    def __init__(
        self,
        vst_path: str | Path,
        *,
        plugin_name: str | None = None,
        sample_rate: int = 44100,
        block_size: int = 512,
        normalize: bool = True,
    ) -> None:
        self._path = str(vst_path)
        self._plugin_name = plugin_name
        self._sr = sample_rate
        self._bs = block_size
        self._normalize = normalize
        self._engine: daw.RenderEngine | None = None
        self._synth: daw.PluginProcessor | None = None

    # ------------------------------------------------------------------
    # Lazy engine / plugin
    # ------------------------------------------------------------------

    @property
    def engine(self) -> daw.RenderEngine:
        if self._engine is None:
            self._engine = daw.RenderEngine(self._sr, self._bs)
        return self._engine

    @property
    def synth(self) -> daw.PluginProcessor:
        if self._synth is None:
            kw: dict = {}
            if self._plugin_name:
                kw["plugin_name"] = self._plugin_name
            self._synth = self.engine.make_plugin_processor("synth", self._path, **kw)
        return self._synth

    @property
    def name(self) -> str:
        return self.synth.get_name()

    @property
    def num_parameters(self) -> int:
        return self.synth.get_plugin_parameter_size()

    def parameters(self) -> list[dict]:
        """Full parameter descriptions (index, name, range, etc.)."""
        return self.synth.get_plugin_parameters_description()

    def set_parameter(self, index: int, value: float) -> None:
        self.synth.set_parameter(index, value)

    def get_parameter(self, index: int) -> float:
        return self.synth.get_parameter(index)

    # ------------------------------------------------------------------
    # Preset state (the reliable headless path)
    # ------------------------------------------------------------------

    def save_state(self, path: str | Path) -> None:
        """Snapshot the plugin's full state to a file for headless reuse."""
        self.synth.save_state(str(path))

    def load_state(self, path: str | Path) -> None:
        """Restore plugin state previously written by save_state."""
        self.synth.load_state(str(path))

    def load_vst3_preset(self, path: str | Path) -> bool:
        """Load a native .vstpreset file (NOT VST2 .fxp)."""
        return self.synth.load_vst3_preset(str(path))

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        if not self._normalize:
            return audio
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.9
        return audio

    def _load_notes(self, notes: list[NoteInfo], bpm: float, channel: int = 0) -> None:
        """Push NoteInfo events into the plugin in absolute seconds."""
        beat_sec = 60.0 / bpm
        self.synth.clear_midi()
        for n in notes:
            start = max(0.0, n.start) * beat_sec
            dur = max(1e-3, n.duration * beat_sec)
            self.synth.add_midi_note(
                int(n.pitch), int(n.velocity), start, dur, beats=False
            )

    def render_notes(
        self,
        notes: list[NoteInfo],
        *,
        bpm: float = 120.0,
        channel: int = 0,
        program: int | None = None,  # noqa: ARG002 — kept for API parity
    ) -> np.ndarray:
        """Render NoteInfo list. Returns float32 array (channels, samples)."""
        self._load_notes(notes, bpm, channel)
        duration = _total_duration(notes, bpm)
        self.engine.load_graph([(self.synth, [])])
        self.engine.render(duration)
        audio = self.engine.get_audio()
        return self._normalize_audio(audio)

    def render_tracks(
        self,
        tracks: list[Track],
        *,
        bpm: float = 120.0,
    ) -> np.ndarray:
        """Render multiple Tracks through the same plugin, summed.

        NOTE: a single plugin instance renders one timbre. For distinct
        per-track timbres, load each track's saved state and render separately.
        """
        all_notes: list[NoteInfo] = []
        for t in tracks:
            all_notes.extend(t.notes)
        return self.render_notes(all_notes, bpm=bpm)

    # ------------------------------------------------------------------
    # Save to file
    # ------------------------------------------------------------------

    def render_wav(
        self,
        notes: list[NoteInfo],
        path: str | Path,
        *,
        bpm: float = 120.0,
        channel: int = 0,
        program: int | None = None,
    ) -> Path:
        """Render NoteInfo list and save as 16-bit PCM WAV (stdlib only)."""
        audio = self.render_notes(notes, bpm=bpm, channel=channel, program=program)
        return self._write_wav(audio, path)

    def _write_wav(self, audio: np.ndarray, path: str | Path) -> Path:
        """Write a (channels, samples) float32 array as 16-bit PCM WAV."""
        import wave

        path = Path(path)
        # (channels, samples) -> interleaved (samples, channels)
        interleaved = audio.T
        clipped = np.clip(interleaved, -1.0, 1.0)
        pcm = (clipped * 32767.0).astype("<i2")
        with wave.open(str(path), "wb") as w:
            w.setnchannels(audio.shape[0])
            w.setsampwidth(2)
            w.setframerate(self._sr)
            w.writeframes(pcm.tobytes())
        return path

    def render_mp3(
        self,
        notes: list[NoteInfo],
        path: str | Path,
        *,
        bpm: float = 120.0,
        channel: int = 0,
        program: int | None = None,
    ) -> Path:
        """Render and save as MP3 (requires ffmpeg)."""
        path = Path(path)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        try:
            self.render_wav(notes, wav_path, bpm=bpm, channel=channel, program=program)
            subprocess.run(
                ["ffmpeg", "-y", "-i", wav_path,
                 "-codec:a", "libmp3lame", "-b:a", "320k", str(path)],
                check=True,
                capture_output=True,
            )
        finally:
            Path(wav_path).unlink(missing_ok=True)
        return path

    def close(self) -> None:
        self._synth = None
        self._engine = None

    def __enter__(self) -> DawDreamerPlayer:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()
