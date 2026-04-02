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

import pytest
from pathlib import Path
from melodica.midi import from_midi, from_midi_bytes, notes_to_midi, chords_to_midi
from melodica.types import Note, NoteInfo, ChordLabel, Quality

def test_notes_to_midi_and_from_midi(tmp_path: Path):
    midi_file = tmp_path / "test.mid"
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100),
        NoteInfo(pitch=64, start=1.0, duration=0.5, velocity=80),
    ]
    notes_to_midi(notes, midi_file)
    
    # Read back
    read_notes = from_midi(midi_file)
    assert len(read_notes) == 2
    
    assert read_notes[0].pitch == 60
    assert read_notes[0].start == 0.0
    assert read_notes[0].duration == 1.0
    assert read_notes[0].velocity == 100

    assert read_notes[1].pitch == 64
    assert read_notes[1].start == 1.0
    assert read_notes[1].duration == 0.5
    assert read_notes[1].velocity == 80


def test_from_midi_bytes():
    # Write a simple midi to bytes
    import mido
    import io
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_off", note=60, velocity=0, time=480))
    
    bio = io.BytesIO()
    mid.save(file=bio)
    midi_bytes = bio.getvalue()
    
    notes = from_midi_bytes(midi_bytes)
    assert len(notes) == 1
    assert notes[0].pitch == 60
    assert notes[0].start == 0.0
    assert notes[0].duration == 1.0


def test_from_midi_invalid_track():
    from unittest.mock import patch, MagicMock
    import mido
    mid = mido.MidiFile(ticks_per_beat=480)
    mid.tracks.append(mido.MidiTrack())
    
    # Create valid midi in memory via bytes for this test
    import io
    bio = io.BytesIO()
    mid.save(file=bio)
    
    with pytest.raises(IndexError, match="out of range"):
        from_midi_bytes(bio.getvalue(), track=5)


def test_from_midi_note_on_velocity_zero(tmp_path: Path):
    import mido
    midi_file = tmp_path / "zero_vel.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    # note_on with velocity=0 acts as note_off
    track.append(mido.Message("note_on", note=60, velocity=0, time=480))
    mid.save(str(midi_file))
    
    notes = from_midi(midi_file)
    assert len(notes) == 1
    assert notes[0].duration == 1.0


def test_from_midi_no_note_off(tmp_path: Path):
    import mido
    midi_file = tmp_path / "no_off.mid"
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.Message("note_on", note=60, velocity=64, time=0))
    track.append(mido.Message("note_on", note=64, velocity=64, time=240)) # +0.5 beats
    # Deliberately do not add note_off
    mid.save(str(midi_file))
    
    notes = from_midi(midi_file)
    assert len(notes) == 2
    # The max duration defaults from the formula for truncated notes.
    # last_beat = 0.5. For pitch 60, max(0.5 - 0, 0.25) -> 0.5
    # For pitch 64, max(0.5 - 0.5, 0.25) -> 0.25
    assert notes[0].duration == 0.5
    assert notes[1].duration == 0.25


def test_chords_to_midi(tmp_path: Path):
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, duration=1.0, start=0.0),
        ChordLabel(root=5, quality=Quality.MAJOR, duration=1.0, start=1.0),
    ]
    out_file = tmp_path / "chords.mid"
    chords_to_midi(chords, out_file)
    
    read_notes = from_midi(out_file)
    assert len(read_notes) == 6 # 3 notes per chord
    
    # Test valid alternate voicings
    chords_to_midi(chords, out_file, voicing="spread")
    chords_to_midi(chords, out_file, voicing="open")
    
    with pytest.raises(ValueError, match="voicing must be one of"):
        chords_to_midi(chords, out_file, voicing="invalid_voicing")
