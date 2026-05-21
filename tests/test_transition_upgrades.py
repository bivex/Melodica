# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from pathlib import Path
from melodica.types import (
    NoteInfo,
    Track,
    Scale,
    Mode,
    ChordLabel,
    ModulationEngine,
    Quality,
)
from melodica.composer.transition_coordinator import TransitionCoordinator
from melodica.composer.album_pipeline import compile_continuous_album, Mood
from melodica.types import Mode


def test_transition_coordinator_ducking():
    """Verify TransitionCoordinator ducks/silences notes in the target range."""
    notes = [
        NoteInfo(pitch=60, start=1.0, duration=1.0, velocity=100),  # outside
        NoteInfo(pitch=62, start=8.0, duration=2.0, velocity=100),  # inside [8.0, 12.0]
        NoteInfo(pitch=64, start=15.0, duration=1.0, velocity=100), # outside
    ]
    tracks = {"bass": Track(name="bass", notes=notes)}

    # 1. Ducking with duck_factor = 0.0 (complete silence/removal)
    TransitionCoordinator.apply_ducking(tracks, ["bass"], 8.0, 12.0, duck_factor=0.0)
    # The middle note should be dropped completely
    assert len(tracks["bass"].notes) == 2
    assert tracks["bass"].notes[0].pitch == 60
    assert tracks["bass"].notes[1].pitch == 64

    # 2. Ducking with duck_factor = 0.5 (scaled velocity)
    notes2 = [
        NoteInfo(pitch=60, start=1.0, duration=1.0, velocity=100),
        NoteInfo(pitch=62, start=9.0, duration=1.0, velocity=100),
    ]
    tracks2 = {"bass": Track(name="bass", notes=notes2)}
    TransitionCoordinator.apply_ducking(tracks2, ["bass"], 8.0, 12.0, duck_factor=0.5)
    assert len(tracks2["bass"].notes) == 2
    assert tracks2["bass"].notes[0].velocity == 100
    assert tracks2["bass"].notes[1].velocity == 50  # scaled velocity


def test_transition_coordinator_sweeps():
    """Verify TransitionCoordinator applies CC sweeps correctly."""
    tracks = {"pad": Track(name="pad")}
    cc_events = {}

    # Apply cutoff (CC 74) exponential sweep from 40 to 110 over beat 16.0 to 24.0
    TransitionCoordinator.apply_sweeps(
        tracks, cc_events, ["pad"], 74, 40, 110, 16.0, 24.0, curve_type="exponential", steps=5
    )

    assert "pad" in cc_events
    events = cc_events["pad"]
    assert len(events) == 5
    # Should start at 16.0 with value 40 and end at 24.0 with value 110
    assert events[0][0] == 16.0
    assert events[0][1] == 74
    assert events[0][2] == 40
    assert events[-1][0] == 24.0
    assert events[-1][2] == 110


def test_transition_coordinator_lead_in_fill():
    """Verify TransitionCoordinator correctly integrates a lead-in fill."""
    existing_notes = [
        NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80),
        NoteInfo(pitch=62, start=4.0, duration=4.0, velocity=80),
        NoteInfo(pitch=64, start=8.0, duration=4.0, velocity=80),  # starts after boundary 6.0
    ]
    tracks = {"violin": Track(name="violin", notes=existing_notes)}

    fill_notes = [
        NoteInfo(pitch=70, start=0.0, duration=1.0, velocity=90),
        NoteInfo(pitch=72, start=1.0, duration=1.0, velocity=90),
    ]

    # Apply lead-in fill starting at beat 6.0
    TransitionCoordinator.apply_lead_in_fill(tracks, "violin", fill_notes, 6.0)

    # Note 64 (start=8.0) should have been dropped.
    # Note 60 (start=0.0) and Note 62 (start=4.0) should be retained.
    # Fill notes should be added, shifted to start at 6.0 and 7.0.
    notes = tracks["violin"].notes
    assert len(notes) == 4
    assert notes[0].pitch == 60
    assert notes[0].start == 0.0
    
    assert notes[1].pitch == 70
    assert notes[1].start == 6.0
    
    assert notes[2].pitch == 72
    assert notes[2].start == 7.0

    assert notes[3].pitch == 64
    assert notes[3].start == 8.0


def test_modulation_bridge_generation():
    """Verify DiatonicModulationBridge strategies."""
    scale_a = Scale(root=0, mode=Mode.MAJOR)          # C Major
    scale_b = Scale(root=11, mode=Mode.PHRYGIAN)      # B Phrygian

    # 1. Pivot chord modulation
    bridge_pivot = ModulationEngine.generate_modulation_bridge(
        scale_a, scale_b, length_beats=8.0, strategy="pivot", start_beat=16.0
    )
    assert len(bridge_pivot) == 4
    # All chord durations should be 2.0
    for i, chord in enumerate(bridge_pivot):
        assert chord.duration == 2.0
        assert chord.start == 16.0 + (i * 2.0)

    # 2. Dominant Seventh Chain modulation
    bridge_dom = ModulationEngine.generate_modulation_bridge(
        scale_a, scale_b, length_beats=8.0, strategy="dominant", start_beat=0.0
    )
    assert len(bridge_dom) == 4
    # The secondary dominant should be V7/V of B Phrygian
    # V degree of B Phrygian (root 11) is F# (root 6). V/V is C#7 (root 1).
    assert bridge_dom[1].quality == Quality.DOMINANT7
    assert bridge_dom[1].root == 1  # C#

    # 3. Chromatic slide/tritone substitution modulation
    bridge_chrom = ModulationEngine.generate_modulation_bridge(
        scale_a, scale_b, length_beats=8.0, strategy="chromatic", start_beat=0.0
    )
    assert len(bridge_chrom) == 4
    # The tritone substitution is bII7 of B (C7 -> root 0)
    assert bridge_chrom[1].quality == Quality.DOMINANT7
    assert bridge_chrom[1].root == 0  # C


def test_compile_continuous_album(tmp_path):
    """Verify compile_continuous_album stitches tracks and applies crossfades."""
    # Create two simple tracks
    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
        "cc_events": {"lead": [(0.0, 74, 64)]},
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "cc_events": {"lead": [(0.0, 74, 80)]},
    }

    out_file = tmp_path / "continuous_album.mid"

    # Merge with 2 beats of overlap
    report = compile_continuous_album(
        [t1_meta, t2_meta],
        output_path=out_file,
        overlap_beats=2.0,
        mood=Mood.CHAMBER
    )

    assert out_file.exists()
    assert "profiles" in report
    assert "lead" in report["profiles"]


def test_transition_coordinator_orchestrated():
    """Verify orchestrate_transition coordinates ducking + sweep + fill in one call."""
    from melodica.types import NoteInfo, Track
    from melodica.composer.transition_coordinator import TransitionCoordinator

    # Setup: bass track with notes before and after boundary, pad to be swept
    bass_notes = [
        NoteInfo(pitch=36, start=8.0, duration=1.0, velocity=100),   # inside duck window [12, 16]
        NoteInfo(pitch=36, start=13.0, duration=1.0, velocity=100),  # inside duck window
        NoteInfo(pitch=36, start=20.0, duration=1.0, velocity=100),  # after boundary
    ]
    pad_notes = [NoteInfo(pitch=60, start=0.0, duration=32.0, velocity=80)]
    violin_notes = [
        NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=70),
        NoteInfo(pitch=65, start=4.0, duration=4.0, velocity=70),
        NoteInfo(pitch=67, start=16.0, duration=4.0, velocity=70),  # after boundary — will be replaced by fill
    ]
    fill_notes = [
        NoteInfo(pitch=70, start=0.0, duration=1.0, velocity=90),
        NoteInfo(pitch=72, start=1.0, duration=1.0, velocity=90),
    ]

    tracks = {
        "bass": Track(name="bass", notes=bass_notes),
        "pad": Track(name="pad", notes=pad_notes),
        "violin": Track(name="violin", notes=violin_notes),
    }
    cc_events = {}

    # Orchestrate all three effects at boundary_beat=16.0, pre_duration=4.0
    TransitionCoordinator.orchestrate_transition(
        tracks=tracks,
        cc_events=cc_events,
        boundary_beat=16.0,
        pre_duration=4.0,
        duck_tracks=["bass"],
        duck_factor=0.0,          # full silence in duck window
        sweep_tracks=["pad"],
        sweep_cc=74,
        sweep_start_val=30,
        sweep_end_val=100,
        sweep_curve="exponential",
        fill_track="violin",
        fill_notes=fill_notes,
    )

    # 1. Bass notes in [12.0, 16.0] should be removed, note at 8.0 and 20.0 kept
    bass_pitches = [n.pitch for n in tracks["bass"].notes]
    assert len(tracks["bass"].notes) == 2
    assert all(n.start not in (13.0,) for n in tracks["bass"].notes)

    # 2. CC sweep events should have been added for "pad"
    assert "pad" in cc_events
    assert len(cc_events["pad"]) >= 2
    assert cc_events["pad"][0][1] == 74      # correct CC number
    assert cc_events["pad"][0][2] == 30      # start value
    assert cc_events["pad"][-1][2] == 100    # end value

    # 3. Violin fill was injected at boundary_beat=16.0
    violin_notes_out = tracks["violin"].notes
    fill_starts = [n.start for n in violin_notes_out if n.pitch in (70, 72)]
    assert 16.0 in fill_starts
    assert 17.0 in fill_starts


def test_compile_continuous_album_modulation(tmp_path):
    """Verify compile_continuous_album generates a _transition_pad when keys differ."""
    key_a = Scale(root=0, mode=Mode.MAJOR)          # C Major
    key_b = Scale(root=11, mode=Mode.PHRYGIAN)      # B Phrygian

    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=59, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
        "cc_events": {},
        "key": key_a,
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 90.0,
        "instruments": {"lead": 40},
        "cc_events": {},
        "key": key_b,
    }

    out_file = tmp_path / "modulation_album.mid"
    report = compile_continuous_album(
        [t1_meta, t2_meta],
        output_path=out_file,
        overlap_beats=4.0,
        mood=Mood.CHAMBER,
        modulation_strategy="dominant",
        transition_instrument=89,
    )

    assert out_file.exists()
    # The modulation pad track should appear in the profiles
    assert "profiles" in report
    assert "transition_pad" in report["profiles"]
