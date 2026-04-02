# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import io
import tempfile
from pathlib import Path

import mido
import pytest
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.types import MusicTimeline, KeyLabel, TimeSignatureLabel, MarkerLabel
from melodica.midi import export_multitrack_midi, export_midi, notes_to_midi


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _make_notes(pitch: int, count: int = 4) -> list[NoteInfo]:
    return [NoteInfo(pitch=pitch, start=float(i), duration=0.5, velocity=80) for i in range(count)]


class TestExportMultitrackBasic:
    def test_single_track(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi({"Melody": _make_notes(60)}, path)
        assert path.exists()

        mid = mido.MidiFile(filename=str(path))
        # Global meta track + 1 data track
        assert len(mid.tracks) == 2

    def test_multiple_tracks(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi(
            {
                "Melody": _make_notes(60),
                "Bass": _make_notes(36),
                "Chords": _make_notes(48),
            },
            path,
        )

        mid = mido.MidiFile(filename=str(path))
        assert len(mid.tracks) == 4  # global + 3

    def test_track_names(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi(
            {
                "Melody": _make_notes(60),
                "Bass": _make_notes(36),
            },
            path,
        )

        mid = mido.MidiFile(filename=str(path))
        track_names = []
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "track_name":
                    track_names.append(msg.name)
        assert "Melody" in track_names
        assert "Bass" in track_names

    def test_channels_assigned(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi(
            {
                "A": _make_notes(60),
                "B": _make_notes(64),
            },
            path,
        )

        mid = mido.MidiFile(filename=str(path))
        channels = set()
        for track in mid.tracks[1:]:
            for msg in track:
                if hasattr(msg, "channel"):
                    channels.add(msg.channel)
        assert len(channels) == 2

    def test_note_roundtrip(self, tmp_path):
        path = tmp_path / "test.mid"
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100),
            NoteInfo(pitch=64, start=1.0, duration=0.5, velocity=80),
            NoteInfo(pitch=67, start=2.0, duration=2.0, velocity=110),
        ]
        export_multitrack_midi({"Track": notes}, path)

        mid = mido.MidiFile(filename=str(path))
        note_ons = []
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "note_on" and msg.velocity > 0:
                    note_ons.append(msg.note)
        assert note_ons == [60, 64, 67]

    def test_empty_tracks(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi({"Empty": []}, path)
        mid = mido.MidiFile(filename=str(path))
        assert len(mid.tracks) == 2  # global + empty track


class TestExportMultitrackTempo:
    def test_default_tempo(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi({"T": _make_notes(60)}, path)

        mid = mido.MidiFile(filename=str(path))
        tempo_msgs = [m for m in mid.tracks[0] if m.type == "set_tempo"]
        assert len(tempo_msgs) == 1
        bpm = mido.tempo2bpm(tempo_msgs[0].tempo)
        assert abs(bpm - 120.0) < 0.1

    def test_custom_tempo(self, tmp_path):
        path = tmp_path / "test.mid"
        export_multitrack_midi({"T": _make_notes(60)}, path, bpm=140.0)

        mid = mido.MidiFile(filename=str(path))
        tempo_msgs = [m for m in mid.tracks[0] if m.type == "set_tempo"]
        bpm = mido.tempo2bpm(tempo_msgs[0].tempo)
        assert abs(bpm - 140.0) < 0.1


class TestExportMultitrackCC:
    def test_cc_events(self, tmp_path):
        path = tmp_path / "test.mid"
        cc = {
            "Melody": [
                (0.0, 64, 127),  # sustain on at beat 0
                (2.0, 64, 0),  # sustain off at beat 2
            ],
        }
        export_multitrack_midi({"Melody": _make_notes(60)}, path, cc_events=cc)

        mid = mido.MidiFile(filename=str(path))
        cc_msgs = []
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "control_change":
                    cc_msgs.append((msg.control, msg.value))
        assert (64, 127) in cc_msgs
        assert (64, 0) in cc_msgs

    def test_per_note_expression(self, tmp_path):
        path = tmp_path / "test.mid"
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80, expression={11: 100}),
            NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80, expression={11: 50}),
        ]
        export_multitrack_midi({"Expr": notes}, path)

        mid = mido.MidiFile(filename=str(path))
        cc11_vals = []
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "control_change" and msg.control == 11:
                    cc11_vals.append(msg.value)
        assert 100 in cc11_vals
        assert 50 in cc11_vals


class TestExportMultitrackTimeline:
    def test_key_signature_changes(self, tmp_path):
        path = tmp_path / "test.mid"
        timeline = MusicTimeline(
            keys=[
                KeyLabel(scale=C_MAJOR, start=0.0, duration=8.0),
                KeyLabel(scale=Scale(root=7, mode=Mode.MAJOR), start=8.0, duration=8.0),
            ],
        )
        export_multitrack_midi({"T": _make_notes(60)}, path, timeline=timeline)

        mid = mido.MidiFile(filename=str(path))
        key_sigs = [m for m in mid.tracks[0] if m.type == "key_signature"]
        assert len(key_sigs) >= 2

    def test_time_signature_changes(self, tmp_path):
        path = tmp_path / "test.mid"
        timeline = MusicTimeline(
            time_signatures=[
                TimeSignatureLabel(numerator=4, denominator=4, start=0.0),
                TimeSignatureLabel(numerator=3, denominator=4, start=8.0),
            ],
        )
        export_multitrack_midi({"T": _make_notes(60)}, path, timeline=timeline)

        mid = mido.MidiFile(filename=str(path))
        time_sigs = [m for m in mid.tracks[0] if m.type == "time_signature"]
        assert len(time_sigs) >= 2

    def test_markers(self, tmp_path):
        path = tmp_path / "test.mid"
        timeline = MusicTimeline(
            markers=[
                MarkerLabel(text="Intro", start=0.0),
                MarkerLabel(text="Verse", start=8.0),
            ],
        )
        export_multitrack_midi({"T": _make_notes(60)}, path, timeline=timeline)

        mid = mido.MidiFile(filename=str(path))
        markers = [m for m in mid.tracks[0] if m.type == "marker"]
        marker_texts = [m.text for m in markers]
        assert "Intro" in marker_texts
        assert "Verse" in marker_texts


class TestExportMidi:
    def test_basic_export(self, tmp_path):
        from melodica.types import Track

        path = tmp_path / "test.mid"
        notes = _make_notes(60)
        tracks = [Track(name="Melody", notes=notes, channel=0, program=73)]
        export_midi(tracks, path)
        assert path.exists()

        mid = mido.MidiFile(filename=str(path))
        assert len(mid.tracks) == 2

    def test_program_change(self, tmp_path):
        from melodica.types import Track

        path = tmp_path / "test.mid"
        tracks = [Track(name="Lead", notes=_make_notes(60), channel=0, program=73)]
        export_midi(tracks, path)

        mid = mido.MidiFile(filename=str(path))
        pc_msgs = []
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "program_change":
                    pc_msgs.append(msg.program)
        assert 73 in pc_msgs

    def test_volume_pan_cc(self, tmp_path):
        from melodica.types import Track

        path = tmp_path / "test.mid"
        tracks = [Track(name="Bass", notes=_make_notes(36), channel=0, volume=100, pan=32)]
        export_midi(tracks, path)

        mid = mido.MidiFile(filename=str(path))
        cc_vals = {}
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "control_change":
                    cc_vals[msg.control] = msg.value
        assert cc_vals.get(7) == 100  # volume
        assert cc_vals.get(10) == 32  # pan

    def test_keyswitch_events(self, tmp_path):
        from melodica.types import Track

        path = tmp_path / "test.mid"
        tracks = [
            Track(
                name="Strings",
                notes=_make_notes(60),
                channel=0,
                keyswitch_events=[(0.0, 36), (4.0, 37)],
            )
        ]
        export_midi(tracks, path)

        mid = mido.MidiFile(filename=str(path))
        # Keyswitches are very short notes (1 tick)
        ks_pitches = set()
        for track in mid.tracks[1:]:
            for msg in track:
                if msg.type == "note_on" and msg.velocity > 0:
                    ks_pitches.add(msg.note)
        assert 36 in ks_pitches
        assert 37 in ks_pitches
