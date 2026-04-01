"""Tests for HarmonicVerifier — cross-track cacophony prevention."""

from __future__ import annotations

from melodica.types import NoteInfo
from melodica.composer.harmonic_verifier import (
    detect_clashes,
    detect_parallel_fifths,
    verify_and_fix,
    VerifierConfig,
    _notes_overlap,
    _interval,
)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _note(pitch, start, dur=1.0, vel=80):
    return NoteInfo(pitch=pitch, start=start, duration=dur, velocity=vel)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------


class TestInterval:
    def test_unison(self):
        assert _interval(60, 60) == 0

    def test_minor_second(self):
        assert _interval(60, 61) == 1

    def test_tritone(self):
        assert _interval(60, 66) == 6

    def test_octave_wraps(self):
        assert _interval(60, 72) == 0

    def test_reverse(self):
        assert _interval(65, 60) == 5


class TestOverlap:
    def test_exact_overlap(self):
        assert _notes_overlap(_note(60, 0.0), _note(61, 0.0))

    def test_partial_overlap(self):
        assert _notes_overlap(_note(60, 0.0, 2.0), _note(61, 1.0, 2.0))

    def test_no_overlap(self):
        assert not _notes_overlap(_note(60, 0.0, 1.0), _note(61, 2.0, 1.0))

    def test_with_window(self):
        assert _notes_overlap(_note(60, 0.0, 1.0), _note(61, 1.1, 1.0), window=0.2)


class TestDetectClashes:
    def test_finds_minor_second_clash(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "bass": [_note(61, 0.0, 2.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.0)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 1
        assert clashes[0].interval == 1
        assert clashes[0].severity == "strong"

    def test_finds_tritone_clash(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "pad": [_note(66, 0.0, 2.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.0)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 1
        assert clashes[0].interval == 6

    def test_ignores_consonant(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "bass": [_note(64, 0.0, 2.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.0)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 0  # major 3rd is consonant

    def test_ignores_non_overlapping(self):
        tracks = {
            "melody": [_note(60, 0.0, 1.0)],
            "bass": [_note(61, 2.0, 1.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.0)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 0

    def test_tolerance_allows_mild(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "bass": [_note(62, 0.0, 2.0)],  # M2 = mild
        }
        # High tolerance should allow M2
        config = VerifierConfig(dissonance_tolerance=0.8)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 0

    def test_tolerance_blocks_strong(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "bass": [_note(61, 0.0, 2.0)],  # m2 = strong
        }
        config = VerifierConfig(dissonance_tolerance=0.5)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 1

    def test_very_brief_clash_ignored(self):
        tracks = {
            "melody": [_note(60, 0.0, 0.001)],
            "bass": [_note(61, 0.0, 0.001)],
        }
        config = VerifierConfig(dissonance_tolerance=0.0, window=0.0001)
        clashes = detect_clashes(tracks, config)
        assert len(clashes) == 0


class TestDetectParallelFifths:
    def test_finds_parallel_fifths(self):
        tracks = {
            "melody": [_note(60, 0.0, 1.0), _note(62, 1.0, 1.0)],
            "bass": [_note(67, 0.0, 1.0), _note(69, 1.0, 1.0)],
        }
        events = detect_parallel_fifths(tracks)
        assert len(events) >= 1

    def test_no_parallel_with_consonant(self):
        tracks = {
            "melody": [_note(60, 0.0, 1.0), _note(62, 1.0, 1.0)],
            "bass": [_note(64, 0.0, 1.0), _note(65, 1.0, 1.0)],
        }
        events = detect_parallel_fifths(tracks)
        assert len(events) == 0


class TestVerifyAndFix:
    def test_transposes_clashing_note(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0, vel=80)],
            "bass": [_note(61, 0.0, 2.0, vel=60)],
        }
        config = VerifierConfig(
            dissonance_tolerance=0.0,
            fix_transpose=True,
            fix_remove=False,
            fix_velocity=False,
            fix_shorten=False,
        )
        fixed, report = verify_and_fix(tracks, config)
        assert report.clashes_detected >= 1
        assert report.clashes_fixed >= 1
        assert report.notes_transposed >= 1
        # The clashing note should have been transposed
        assert fixed["bass"][0].pitch != 61

    def test_reduces_velocity_when_no_transpose(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0, vel=80)],
            "bass": [_note(61, 0.0, 2.0, vel=60)],
        }
        config = VerifierConfig(
            dissonance_tolerance=0.0,
            fix_transpose=False,
            fix_velocity=True,
            fix_shorten=False,
        )
        fixed, report = verify_and_fix(tracks, config)
        assert report.notes_velocity_reduced >= 1
        # Lower velocity note should be even lower
        assert fixed["bass"][0].velocity < 60

    def test_no_clashes_no_changes(self):
        tracks = {
            "melody": [_note(60, 0.0, 2.0)],
            "bass": [_note(48, 0.0, 2.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.5)
        fixed, report = verify_and_fix(tracks, config)
        assert report.clashes_detected == 0
        assert report.clashes_fixed == 0

    def test_polyphony_reduction(self):
        # Create a track with 20 simultaneous notes
        notes = [_note(60 + i, 0.0, 4.0) for i in range(20)]
        tracks = {"dense": notes}
        config = VerifierConfig(max_polyphony=5)
        fixed, report = verify_and_fix(tracks, config)
        assert report.polyphony_reduced > 0

    def test_preserves_non_clashing_tracks(self):
        tracks = {
            "melody": [_note(72, 0.0, 2.0)],
            "bass": [_note(36, 0.0, 2.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.5)
        fixed, report = verify_and_fix(tracks, config)
        assert fixed["melody"][0].pitch == 72
        assert fixed["bass"][0].pitch == 36

    def test_report_accuracy(self):
        tracks = {
            "a": [_note(60, 0.0, 2.0)],
            "b": [_note(61, 0.0, 2.0)],
        }
        config = VerifierConfig(dissonance_tolerance=0.0, fix_velocity=True)
        _, report = verify_and_fix(tracks, config)
        assert report.clashes_detected >= 1
        assert report.clashes_fixed >= 1
