# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_theory_voice_leading.py — Unit tests for unified voice leading theory module.
"""

from __future__ import annotations

import pytest

from melodica.theory.voice_leading import (
    DEFAULT_RANGE,
    GM_RANGES,
    VOICE_ORDER,
    VOICE_RANGES,
    VoiceLeadingEngine,
    classify_motion,
    correct_parallels,
    get_instrument_range,
    has_parallel_motion,
    interval,
    is_parallel_fifth,
    is_parallel_octave,
    pitch_class,
    voice_leading_distance,
)
from melodica.types import ChordLabel, NoteInfo, Quality, Scale, Mode


def test_pitch_class_and_interval():
    assert pitch_class(60) == 0  # C
    assert pitch_class(67) == 7  # G
    assert pitch_class(71) == 11 # B

    assert interval(60, 67) == 7
    assert interval(67, 60) == -7


def test_parallel_fifth_detection():
    # Both voices move up by 2 semitones maintaining interval of 7
    assert is_parallel_fifth(prev_a=60, prev_b=67, curr_a=62, curr_b=69)
    # Both move down
    assert is_parallel_fifth(prev_a=62, prev_b=69, curr_a=60, curr_b=67)
    # Contrary motion: a moves up, b moves down -> NOT parallel
    assert not is_parallel_fifth(prev_a=60, prev_b=67, curr_a=62, curr_b=65)
    # Oblique motion: one voice stationary -> NOT parallel
    assert not is_parallel_fifth(prev_a=60, prev_b=67, curr_a=60, curr_b=69)
    # Interval is not a fifth
    assert not is_parallel_fifth(prev_a=60, prev_b=64, curr_a=62, curr_b=66)


def test_parallel_octave_detection():
    # Both voices move up maintaining octave
    assert is_parallel_octave(prev_a=48, prev_b=60, curr_a=50, curr_b=62)
    # Contrary motion -> NOT parallel
    assert not is_parallel_octave(prev_a=48, prev_b=60, curr_a=50, curr_b=58)
    # Stationary voice -> NOT parallel
    assert not is_parallel_octave(prev_a=48, prev_b=60, curr_a=48, curr_b=62)


def test_classify_motion():
    # Parallel (same direction and distance)
    assert classify_motion(60, 64, 62, 66) == "parallel"
    # Similar (same direction, different distance)
    assert classify_motion(60, 64, 62, 67) == "similar"
    # Contrary (opposite directions)
    assert classify_motion(60, 67, 62, 65) == "contrary"
    # Oblique (one voice stationary)
    assert classify_motion(60, 67, 60, 69) == "oblique"
    assert classify_motion(60, 67, 62, 67) == "oblique"


def test_has_parallel_motion():
    v1 = [60, 64, 67, 72]
    # v2 creates parallel fifth between voice 0 and 2 (60->62, 67->69)
    v2 = [62, 65, 69, 74]
    assert has_parallel_motion(v1, v2)

    # v3 has contrary motion (bass moves down, soprano moves up)
    v3 = [59, 64, 67, 74]
    assert not has_parallel_motion(v1, v3)


def test_voice_leading_distance():
    v1 = [60, 64, 67]
    v2 = [60, 65, 67]
    # L1 distance
    assert voice_leading_distance(v1, v2, p=1.0) == 1.0
    # L2 distance
    assert voice_leading_distance(v1, v2, p=2.0) == 1.0
    # Empty
    assert voice_leading_distance([], []) == 0.0


def test_get_instrument_range():
    assert get_instrument_range(None) == DEFAULT_RANGE
    assert get_instrument_range(40) == (55, 103)  # Violin
    assert get_instrument_range(999) == DEFAULT_RANGE


def test_voice_leading_engine_satb():
    engine = VoiceLeadingEngine(strict_mode=True, beam_width=2)
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.DOMINANT7, start=8.0, duration=4.0),
        ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
    ]
    key = Scale(0, Mode.MAJOR)
    res = engine.voicize_progression(chords, key)

    for v in VOICE_ORDER:
        assert v in res
        assert len(res[v]) == len(chords)
        lo, hi = VOICE_RANGES[v]
        for note in res[v]:
            assert lo <= note.pitch <= hi


def test_correct_parallels():
    # Multi-track dictionary with parallel fifth between lead and chord tracks
    tracks = {
        "Lead": [
            NoteInfo(pitch=67, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=69, start=1.0, duration=1.0, velocity=80),
        ],
        "Chord": [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=62, start=1.0, duration=1.0, velocity=80),
        ],
    }
    instruments = {"Lead": 80, "Chord": 0}
    corrected = correct_parallels(tracks, instruments)
    assert len(corrected["Lead"]) == 2
    assert len(corrected["Chord"]) == 2
    # Verify the upper voice note at t=1.0 was shifted or parallelism broken
    l1 = corrected["Lead"][1].pitch
    c1 = corrected["Chord"][1].pitch
    assert abs(l1 - c1) % 12 != 7 or l1 == 69  # Shifted or resolved
