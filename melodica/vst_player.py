# Copyright (c) 2026 Bivex
#
# Licensed: MIT

"""
vst_player.py — VST3 instrument host adapter.

Renders Melodica's MIDI output through real VST3 plugins (Surge XT, Vital, etc.)
directly to WAV/audio without needing a DAW.

Usage:
    from melodica.vst_player import VSTPlayer

    player = VSTPlayer("/Library/Audio/Plug-Ins/VST3/Surge XT.vst3")
    player.play_notes(notes, bpm=120)
    player.render_wav(notes, bpm=120, path="output.wav")

Requires: pedalboard (pip install pedalboard)

Layer: Infrastructure (adapter) — same tier as midi.py and virtual_midi.py.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import mido
import numpy as np

try:
    from pedalboard import VST3Plugin
    from pedalboard.io import AudioFile
except ImportError:
    raise ImportError(
        "pedalboard is required for VST playback. Install with: pip install pedalboard"
    )

from melodica.types import NoteInfo, Track


def list_vst3_plugins(search_paths: list[str] | None = None) -> list[dict[str, str]]:
    """Scan standard VST3 directories and return found plugins.

    Returns:
        [{"name": "Surge XT", "path": "...", "plugin_name": None}, ...]
        plugin_name is set when a .vst3 bundle contains multiple plugins (e.g. Serum2).
    """
    if search_paths is None:
        search_paths = [
            "/Library/Audio/Plug-Ins/VST3",
            str(Path.home() / "Library" / "Audio" / "Plug-Ins" / "VST3"),
        ]

    results: list[dict[str, str]] = []
    for base in search_paths:
        base_path = Path(base)
        if not base_path.exists():
            continue
        for child in sorted(base_path.iterdir()):
            if child.suffix != ".vst3":
                continue
            try:
                names = VST3Plugin.get_plugin_names_for_file(str(child))
            except Exception:
                names = []
            if names:
                for name in names:
                    results.append({"name": name, "path": str(child), "plugin_name": name})
            else:
                results.append({"name": child.stem, "path": str(child), "plugin_name": ""})
    return results


def _notes_to_mido_messages(
    notes: list[NoteInfo],
    bpm: float,
    channel: int = 0,
    program: int | None = None,
) -> list[mido.Message]:
    """Convert NoteInfo list to timed mido Messages for pedalboard."""
    beat_sec = 60.0 / bpm
    msgs: list[mido.Message] = []

    if program is not None:
        msgs.append(mido.Message("program_change", program=program, channel=channel, time=0))

    for n in notes:
        onset = max(0.0, n.start) * beat_sec
        offset = (n.start + n.duration) * beat_sec
        msgs.append(
            mido.Message("note_on", note=n.pitch, velocity=n.velocity, channel=channel, time=onset)
        )
        msgs.append(
            mido.Message("note_off", note=n.pitch, velocity=0, channel=channel, time=offset)
        )

    return msgs


def _tracks_to_mido_messages(tracks: list[Track], bpm: float) -> list[mido.Message]:
    """Convert Track list to timed mido Messages for pedalboard."""
    beat_sec = 60.0 / bpm
    msgs: list[mido.Message] = []

    for t in tracks:
        ch = t.channel
        msgs.append(
            mido.Message("program_change", program=t.program, channel=ch, time=0)
        )
        for n in t.notes:
            onset = max(0.0, n.start) * beat_sec
            offset = (n.start + n.duration) * beat_sec
            msgs.append(
                mido.Message("note_on", note=n.pitch, velocity=n.velocity, channel=ch, time=onset)
            )
            msgs.append(
                mido.Message("note_off", note=n.pitch, velocity=0, channel=ch, time=offset)
            )

    return msgs


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


class VSTPlayer:
    """Load a VST3 instrument and render Melodica output through it.

    Usage:
        player = VSTPlayer("/Library/Audio/Plug-Ins/VST3/Surge XT.vst3")
        player.render_wav(notes, bpm=120, path="out.wav")
    """

    def __init__(
        self,
        vst_path: str | Path,
        *,
        plugin_name: str | None = None,
        sample_rate: int = 44100,
        normalize: bool = True,
    ) -> None:
        self._path = str(vst_path)
        self._plugin_name = plugin_name
        self._sr = sample_rate
        self._normalize = normalize
        self._plugin: VST3Plugin | None = None

    @property
    def plugin(self) -> VST3Plugin:
        if self._plugin is None:
            kw: dict = {}
            if self._plugin_name:
                kw["plugin_name"] = self._plugin_name
            self._plugin = VST3Plugin(self._path, **kw)
        return self._plugin

    @property
    def name(self) -> str:
        return self.plugin.name

    @property
    def parameters(self) -> dict:
        return dict(self.plugin.parameters)

    def set_parameter(self, name: str, value: float) -> None:
        self.plugin.parameters[name] = value

    # ------------------------------------------------------------------
    # Render to numpy array
    # ------------------------------------------------------------------

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        if not self._normalize:
            return audio
        peak = np.max(np.abs(audio))
        if peak > 0:
            audio = audio / peak * 0.9
        return audio

    def render_notes(
        self,
        notes: list[NoteInfo],
        *,
        bpm: float = 120.0,
        channel: int = 0,
        program: int | None = None,
    ) -> np.ndarray:
        """Render NoteInfo list through the VST instrument. Returns float32 array (2, samples)."""
        msgs = _notes_to_mido_messages(notes, bpm, channel, program)
        duration = _total_duration(notes, bpm)
        audio = self.plugin(msgs, duration=duration, sample_rate=self._sr, reset=True)
        return self._normalize_audio(audio)

    def render_tracks(
        self,
        tracks: list[Track],
        *,
        bpm: float = 120.0,
    ) -> np.ndarray:
        """Render Track list through the VST instrument. Returns float32 array (2, samples)."""
        msgs = _tracks_to_mido_messages(tracks, bpm)
        duration = _total_tracks_duration(tracks, bpm)
        audio = self.plugin(msgs, duration=duration, sample_rate=self._sr, reset=True)
        return self._normalize_audio(audio)

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
        """Render NoteInfo list and save as WAV."""
        audio = self.render_notes(notes, bpm=bpm, channel=channel, program=program)
        path = Path(path)
        with AudioFile(str(path), "w", self._sr, audio.shape[0]) as f:
            f.write(audio)
        return path

    def render_tracks_wav(
        self,
        tracks: list[Track],
        path: str | Path,
        *,
        bpm: float = 120.0,
    ) -> Path:
        """Render Track list and save as WAV."""
        audio = self.render_tracks(tracks, bpm=bpm)
        path = Path(path)
        with AudioFile(str(path), "w", self._sr, audio.shape[0]) as f:
            f.write(audio)
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
        self.render_wav(notes, wav_path, bpm=bpm, channel=channel, program=program)
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-codec:a", "libmp3lame", "-b:a", "320k", str(path)],
            check=True,
            capture_output=True,
        )
        Path(wav_path).unlink(missing_ok=True)
        return path

    def play_notes(
        self,
        notes: list[NoteInfo],
        *,
        bpm: float = 120.0,
        channel: int = 0,
        program: int | None = None,
    ) -> None:
        """Render and play through speakers (requires ffmpeg + afplay on macOS)."""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            wav_path = tmp.name
        self.render_wav(notes, wav_path, bpm=bpm, channel=channel, program=program)
        subprocess.run(["afplay", wav_path], check=True)
        Path(wav_path).unlink(missing_ok=True)

    def close(self) -> None:
        if self._plugin is not None:
            del self._plugin
            self._plugin = None

    def __enter__(self) -> VSTPlayer:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
