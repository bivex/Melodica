# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import mido
import pytest
from pathlib import Path
from melodica.types import NoteInfo
from melodica.midi import export_multitrack_midi


def test_expressive_midi_pedal_and_lfo(tmp_path: Path):
    path = tmp_path / "expressive_test.mid"
    
    # We create a harp track (keyboard/pedal inst) and a cello track (expressive solo inst)
    # Both have a single long note (3.0 beats duration)
    tracks_data = {
        "harp": [
            NoteInfo(pitch=60, start=0.0, duration=3.0, velocity=80)
        ],
        "cello": [
            NoteInfo(pitch=64, start=0.0, duration=3.0, velocity=80)
        ]
    }
    
    # Run export with humanize=True and custom track volumes mapping
    export_multitrack_midi(
        tracks_data,
        path,
        bpm=60.0,
        volumes={"harp": 100, "cello": 90},
        humanize=True
    )
    
    assert path.exists()
    
    mid = mido.MidiFile(str(path))
    
    # Track 0: Global meta track
    # Track 1: harp
    # Track 2: cello
    assert len(mid.tracks) == 3
    
    # Let's inspect the harp track events
    harp_track = mid.tracks[1]
    harp_cc_controls = []
    harp_cc_values = {}
    
    for msg in harp_track:
        if msg.type == "control_change":
            harp_cc_controls.append((msg.control, msg.value))
            if msg.control not in harp_cc_values:
                harp_cc_values[msg.control] = []
            harp_cc_values[msg.control].append(msg.value)
            
    # harp track should have CC7 Volume = 100
    assert (7, 100) in harp_cc_controls
    
    # harp track should have automatic CC64 sustain pedal events
    assert 64 in harp_cc_values
    assert 127 in harp_cc_values[64] # pedal pressed
    assert 0 in harp_cc_values[64]   # pedal released
    
    # Let's inspect the cello track events
    cello_track = mid.tracks[2]
    cello_cc_controls = []
    cello_cc_values = {}
    
    for msg in cello_track:
        if msg.type == "control_change":
            cello_cc_controls.append((msg.control, msg.value))
            if msg.control not in cello_cc_values:
                cello_cc_values[msg.control] = []
            cello_cc_values[msg.control].append(msg.value)
            
    # cello track should have CC7 Volume = 90
    assert (7, 90) in cello_cc_controls
    
    # cello track should have advanced CC11 (Expression) breathing events
    assert 11 in cello_cc_values
    assert len(cello_cc_values[11]) > 5 # Finer time steps
    
    # cello track should have automatic CC1 (Modulation) delayed vibrato events
    assert 1 in cello_cc_values
    # Check that vibrato LFO value builds up over time (first CC1 is smaller than later ones)
    assert cello_cc_values[1][0] < max(cello_cc_values[1])
