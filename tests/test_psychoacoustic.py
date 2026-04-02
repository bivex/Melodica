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

"""Tests for PsychoacousticVerifier."""

from __future__ import annotations

import pytest

from melodica.types import NoteInfo
from melodica.composer.psychoacoustic import (
    detect_frequency_masking,
    detect_temporal_masking,
    detect_fusion,
    detect_blur,
    detect_register_masking,
    detect_brightness_overload,
    psycho_verify,
    PsychoConfig,
    _freq_masked,
    _temporal_masked,
    _is_fusion,
    _is_blurry,
)


def _note(pitch, start, dur=1.0, vel=80):
    return NoteInfo(pitch=pitch, start=start, duration=dur, velocity=vel)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestFreqMasked:
    def test_loud_masks_quiet_close_pitch(self):
        assert _freq_masked(_note(60, 0, 1, 100), _note(62, 0, 1, 70))

    def test_quiet_doesnt_mask_loud(self):
        assert not _freq_masked(_note(60, 0, 1, 70), _note(62, 0, 1, 100))

    def test_too_far_apart(self):
        assert not _freq_masked(_note(60, 0, 1, 100), _note(72, 0, 1, 70))

    def test_same_pitch(self):
        assert not _freq_masked(_note(60, 0, 1, 100), _note(60, 0, 1, 70))

    def test_velocity_diff_too_small(self):
        assert not _freq_masked(_note(60, 0, 1, 90), _note(62, 0, 1, 80))


class TestTemporalMasked:
    def test_pre_masking(self):
        loud = _note(60, 1.0, 2.0, 100)
        quiet = _note(60, 0.97, 0.05, 60)
        assert _temporal_masked(loud, quiet)

    def test_post_masking(self):
        loud = _note(60, 0.0, 1.0, 100)
        quiet = _note(60, 1.05, 0.05, 60)
        assert _temporal_masked(loud, quiet)

    def test_no_masking_far_apart(self):
        loud = _note(60, 0.0, 1.0, 100)
        quiet = _note(60, 2.0, 0.05, 60)
        assert not _temporal_masked(loud, quiet)


class TestFusion:
    def test_octave_fusion(self):
        assert _is_fusion(_note(60, 0.0), _note(72, 0.0))

    def test_unison_fusion(self):
        assert _is_fusion(_note(60, 0.0), _note(60, 0.0))

    def test_fifth_fusion(self):
        assert _is_fusion(_note(60, 0.0), _note(67, 0.0))

    def test_no_fusion_third(self):
        assert not _is_fusion(_note(60, 0.0), _note(64, 0.0))

    def test_no_fusion_offset(self):
        assert not _is_fusion(_note(60, 0.0), _note(72, 0.1))


class TestBlur:
    def test_blurry(self):
        assert _is_blurry(_note(60, 0.0, 0.01))

    def test_audible(self):
        assert not _is_blurry(_note(60, 0.0, 0.5))


# ---------------------------------------------------------------------------
# Detection tests
# ---------------------------------------------------------------------------


class TestDetectFrequencyMasking:
    def test_finds_masking(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0, 100)],
            "bass": [_note(61, 0.0, 2.0, 60)],
        }
        events = detect_frequency_masking(tracks)
        assert len(events) >= 1

    def test_no_masking_far_apart(self):
        tracks = {
            "melody": [_note(72, 0.0, 2.0, 100)],
            "bass": [_note(48, 0.0, 2.0, 60)],
        }
        events = detect_frequency_masking(tracks)
        assert len(events) == 0


class TestDetectFusion:
    def test_finds_octave_fusion(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "counter": [_note(72, 0.0, 2.0)],
        }
        events = detect_fusion(tracks)
        assert len(events) >= 1


class TestDetectBlur:
    def test_finds_blurry_notes(self):
        tracks = {
            "melody": [_note(60, 0.0, 0.01), _note(62, 0.5, 1.0)],
        }
        events = detect_blur(tracks)
        assert len(events) == 1


class TestDetectBrightnessOverload:
    def test_too_many_high_notes(self):
        tracks = {
            "melody": [_note(84, 0.0, 2.0, 90)],
            "counter": [_note(86, 0.0, 2.0, 85)],
            "arp": [_note(88, 0.0, 2.0, 80)],
        }
        events = detect_brightness_overload(tracks)
        assert len(events) >= 1  # at least one should be flagged


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------


class TestPsychoVerify:
    def test_reduces_velocity_on_masking(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0, 100)],
            "bass": [_note(62, 0.0, 2.0, 60)],
        }
        result, report = psycho_verify(tracks)
        assert report.issues_detected >= 1
        assert report.notes_velocity_reduced >= 1

    def test_transposes_fusion(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "counter": [_note(72, 0.0, 2.0)],
        }
        result, report = psycho_verify(tracks)
        assert report.notes_transposed >= 1

    def test_shortens_blurry(self):
        tracks = {
            "melody": [_note(60, 0.0, 0.01)],
        }
        result, report = psycho_verify(tracks)
        assert report.notes_shortened >= 1
        assert result["melody"][0].duration >= 0.05

    def test_no_issues_no_changes(self):
        tracks = {
            "melody": [_note(72, 0.0, 2.0, 80)],
            "bass": [_note(36, 0.0, 2.0, 80)],
        }
        result, report = psycho_verify(tracks)
        assert report.issues_detected == 0

    def test_preserves_non_note_tracks(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "_chords": ["fake"],
        }
        result, report = psycho_verify(tracks)
        assert "_chords" in result
        assert result["_chords"] == ["fake"]
