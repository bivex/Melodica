# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_mandatory_sections.py — Unit tests for the mandatory sectioning feature
in compile_continuous_album.
"""

import pytest
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.album_pipeline import compile_continuous_album, Mood


def test_mandatory_sections_missing(tmp_path):
    """ValueError should be raised when 'sections' key is missing from track metadata."""
    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
    }

    out_file = tmp_path / "continuous_album_fail.mid"

    with pytest.raises(ValueError, match="is missing mandatory 'sections' list"):
        compile_continuous_album(
            [t1_meta, t2_meta],
            output_path=out_file,
            overlap_beats=2.0,
            mood=Mood.CHAMBER
        )


def test_mandatory_sections_empty(tmp_path):
    """ValueError should be raised when 'sections' key is present but empty."""
    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
        "sections": [],
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "sections": [(0.0, Mood.CHAMBER)],
    }

    out_file = tmp_path / "continuous_album_fail.mid"

    with pytest.raises(ValueError, match="is missing mandatory 'sections' list"):
        compile_continuous_album(
            [t1_meta, t2_meta],
            output_path=out_file,
            overlap_beats=2.0,
            mood=Mood.CHAMBER
        )


def test_sections_not_in_order(tmp_path):
    """ValueError should be raised when sections are not in chronological order."""
    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
        # out of order: 16.0 before 8.0
        "sections": [(16.0, Mood.CHAMBER), (8.0, Mood.CINEMATIC)],
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "sections": [(0.0, Mood.CHAMBER)],
    }

    out_file = tmp_path / "continuous_album_fail.mid"

    with pytest.raises(ValueError, match="sections are not in chronological order"):
        compile_continuous_album(
            [t1_meta, t2_meta],
            output_path=out_file,
            overlap_beats=2.0,
            mood=Mood.CHAMBER
        )


def test_valid_sections_and_compilation(tmp_path):
    """Verify compile_continuous_album succeeds and shifts sections when they are valid."""
    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
        "sections": [(0.0, Mood.CHAMBER), (2.0, Mood.CINEMATIC)],
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "sections": [(0.0, Mood.CHAMBER)],
    }

    out_file = tmp_path / "continuous_album_success.mid"

    report = compile_continuous_album(
        [t1_meta, t2_meta],
        output_path=out_file,
        overlap_beats=2.0,
        mood=Mood.CHAMBER
    )

    assert out_file.exists()
    assert "profiles" in report
