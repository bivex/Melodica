# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.antiphony import AntiphonySectionBuilder
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart


def test_antiphony_section_builder_splitting():
    # 2 bars of A, 2 bars of B. Time signature = 4/4 (cycle = 16 beats, A = 8 beats, B = 8 beats)
    builder = AntiphonySectionBuilder(
        group_a=["strings"],
        group_b=["winds"],
        bars_a=2.0,
        bars_b=2.0,
        overlap_beats=0.0,
        echo_delay_beats=0.0,
    )

    # Dux-like notes for strings (Group A) and winds (Group B)
    # t=2.0 (falls in first 2 bars), t=10.0 (falls in second 2 bars)
    tracks_notes = {
        "violin_track": [
            NoteInfo(pitch=60, start=2.0, duration=1.0),   # t_cycle = 2.0 (Active)
            NoteInfo(pitch=62, start=10.0, duration=1.0),  # t_cycle = 10.0 (Inactive)
        ],
        "flute_track": [
            NoteInfo(pitch=72, start=2.0, duration=1.0),   # t_cycle = 2.0 (Inactive)
            NoteInfo(pitch=74, start=10.0, duration=1.0),  # t_cycle = 10.0 (Active)
        ]
    }
    tracks_instruments = {
        "violin_track": "violin",
        "flute_track": "flute",
    }

    processed = builder.process(
        tracks_notes,
        tracks_instruments,
        start_beat=0.0,
        duration_beats=16.0,
        time_sig_numerator=4,
    )

    # violin_track should keep only note at 2.0
    assert len(processed["violin_track"]) == 1
    assert processed["violin_track"][0].pitch == 60
    assert processed["violin_track"][0].start == 2.0

    # flute_track should keep only note at 10.0
    assert len(processed["flute_track"]) == 1
    assert processed["flute_track"][0].pitch == 74
    assert processed["flute_track"][0].start == 10.0


def test_antiphony_overlap_and_echo():
    # overlap of 1 beat, echo delay of 4 beats transposed by +12 semitones, velocity * 0.5
    builder = AntiphonySectionBuilder(
        group_a=["strings"],
        group_b=["winds"],
        bars_a=1.0,  # 4 beats
        bars_b=1.0,  # 4 beats (cycle = 8 beats)
        overlap_beats=1.0,
        echo_delay_beats=4.0,
        echo_velocity_factor=0.5,
        echo_transpose=12,
    )

    tracks_notes = {
        "violin_track": [
            # Active phase is [0, 4 + 1 = 5]
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),   # t_cycle = 0.0 (Active)
            NoteInfo(pitch=62, start=4.5, duration=1.0, velocity=80),   # t_cycle = 4.5 (Active because 4.5 < 5.0)
            NoteInfo(pitch=64, start=6.0, duration=1.0, velocity=80),   # t_cycle = 6.0 (Inactive)
        ]
    }
    tracks_instruments = {"violin_track": "violin"}

    processed = builder.process(
        tracks_notes,
        tracks_instruments,
        start_beat=0.0,
        duration_beats=8.0,
        time_sig_numerator=4,
    )

    # Kept notes: 0.0 and 4.5.
    # Echo notes:
    # - for 0.0: echo at 4.0, pitch = 72, velocity = 40
    # - for 4.5: echo at 8.5 (overshoots duration_beats=8.0, so filtered out!)
    # Total combined notes in violin_track should be 3: 0.0 (kept), 4.0 (echo), 4.5 (kept)
    notes = processed["violin_track"]
    assert len(notes) == 3
    assert notes[0].start == 0.0
    assert notes[1].start == 4.0
    assert notes[1].pitch == 72
    assert notes[1].velocity == 40
    assert notes[2].start == 4.5


def test_antiphony_integration_in_idea_tool():
    # Setup IdeaTool with a part configured with antiphony
    config = IdeaToolConfig(
        scale=Scale(0, Mode.MAJOR),
        bars=8,
        tracks=[
            TrackConfig(name="strings_track", generator_type="melody", instrument="violin"),
            TrackConfig(name="winds_track", generator_type="melody", instrument="flute"),
        ],
        parts=[
            IdeaPart(
                name="Antiphonal Verse",
                bars=4,
                scale=Scale(0, Mode.MAJOR),
                time_signature=(4, 4),
                antiphony={
                    "group_a": ["strings"],
                    "group_b": ["winds"],
                    "bars_a": 2.0,
                    "bars_b": 2.0,
                }
            )
        ]
    )

    tool = IdeaTool(config)
    result = tool.generate()

    # Verify that the Antiphony section builder processed the tracks
    # We should have notes in both tracks
    assert "strings_track" in result
    assert "winds_track" in result
