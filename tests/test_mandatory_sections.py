# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_mandatory_sections.py — Unit tests for the intelligent sectioning feature
in Melodica.
"""

import pytest
from pathlib import Path

from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.album_pipeline import compile_continuous_album, Mood, detect_sections_intelligently


def test_intelligent_section_fallback(tmp_path):
    """Verify that when sections are missing or empty, they are automatically auto-detected."""
    t1_notes = {"lead": [NoteInfo(pitch=60, start=float(i), duration=0.8, velocity=80) for i in range(16)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=float(i), duration=0.8, velocity=80) for i in range(16)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "sections": [],  # empty list
    }

    out_file = tmp_path / "continuous_album_auto.mid"

    # Should NOT raise ValueError anymore, but succeed using auto-detected sections
    report = compile_continuous_album(
        [t1_meta, t2_meta],
        output_path=out_file,
        overlap_beats=2.0,
        mood=Mood.CHAMBER
    )

    assert out_file.exists()
    assert "profiles" in report


def test_sections_not_in_order(tmp_path):
    """ValueError should be raised when manually specified sections are not in chronological order."""
    t1_notes = {"lead": [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]}
    t2_notes = {"lead": [NoteInfo(pitch=64, start=0.0, duration=4.0, velocity=80)]}

    t1_meta = {
        "tracks": t1_notes,
        "bpm": 100.0,
        "instruments": {"lead": 73},
        # out of order: 16.0 before 8.0
        "sections": [(16.0, "Theme"), (8.0, "Climax")],
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "sections": [(0.0, "Intro")],
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
        "sections": [(0.0, "Intro"), (2.0, "Theme")],
    }
    t2_meta = {
        "tracks": t2_notes,
        "bpm": 120.0,
        "instruments": {"lead": 73},
        "sections": [(0.0, "Intro")],
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


def test_detect_sections_intelligently():
    """Verify detect_sections_intelligently identifies intro, theme, climax, and fade."""
    # Build a timeline of notes with distinct energy dynamics:
    # 0-16 beats: low energy (1 note, velocity 40)
    # 16-48 beats: medium energy (2 tracks, velocity 80)
    # 48-64 beats: high energy (4 tracks, velocity 110)
    # 64-80 beats: low energy (1 note, velocity 40)
    tracks = {
        "pad": [NoteInfo(pitch=60, start=float(i), duration=1.0, velocity=40) for i in range(80)],
        "bass": [NoteInfo(pitch=36, start=float(i), duration=1.0, velocity=80) for i in range(16, 64)],
        "lead": [NoteInfo(pitch=72, start=float(i), duration=1.0, velocity=90) for i in range(16, 64)],
        "heavy": [NoteInfo(pitch=80, start=float(i), duration=1.0, velocity=110) for i in range(48, 64)]
    }

    sections = detect_sections_intelligently(tracks, bpm=120.0)

    # First section should be Intro
    assert sections[0][1] == "Intro"

    # Climax should happen around beat 48.0 (index where 'heavy' starts)
    climax_starts = [start for start, label in sections if label == "Climax"]
    assert len(climax_starts) > 0
    assert min(climax_starts) >= 32.0  # Climax should be detected in the latter half / peaks

    # Final section should be Fade
    assert sections[-1][1] == "Fade"

