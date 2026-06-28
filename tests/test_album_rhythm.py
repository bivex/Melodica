# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""Tests for the mandatory-rhythm contract on album production entry points.

Covers:
  - apply_rhythm_events (RhythmEvent -> NoteInfo bridge) edge cases
  - _resolve_rhythm (name lookup + protocol pass-through + unknown name)
  - produce_track / produce_album / compile_continuous_album require rhythm
  - produce_track with a named rhythm lays notes onto the grid
  - AlbumNarrative requires the rhythm field
"""

import pytest

from melodica.types import NoteInfo, Scale, Mode, parse_progression
from melodica.rhythm import RhythmEvent, apply_rhythm_events
from melodica.rhythm.library import RHYTHM_LIBRARY, DYNAMIC_RHYTHM_REGISTRY
from melodica.composer.album_pipeline import (
    produce_track,
    produce_album,
    compile_continuous_album,
    AlbumNarrative,
    Mood,
    _resolve_rhythm,
)


# Shared production fixtures (key/chords/genre/time_signature are now mandatory
# alongside rhythm — see test_album_required_fields.py for their contract).
KEY = Scale(root=0, mode=Mode.MAJOR)
CHORDS = parse_progression("I - V - vi - IV", KEY)
GENRE = "lofi"
TIME_SIG = (4, 4)


# A grid that is robust to loop filling: every 2 beats, dur 1.
QUARTERS_EVENTS = [RhythmEvent(float(i), 1.0) for i in range(4)]


class _StubRhythmGenerator:
    """Minimal duck-typed rhythm generator (no RhythmGenerator base needed)."""

    def __init__(self, events):
        self._events = events

    def generate(self, duration_beats):
        # Loop-fill the fixed event list to cover duration_beats.
        span = sum(e.duration for e in self._events) or 1.0
        out = []
        t = 0.0
        i = 0
        while t < duration_beats:
            ev = self._events[i % len(self._events)]
            out.append(RhythmEvent(onset=round(t, 6),
                                   duration=ev.duration,
                                   velocity_factor=ev.velocity_factor))
            t += ev.duration
            i += 1
        return out


def _notes(pitches_starts):
    """Build a list[NoteInfo] from (pitch, start) tuples, dur=2.0, vel=100."""
    return [
        NoteInfo(pitch=p, start=s, duration=2.0, velocity=100)
        for p, s in pitches_starts
    ]


# ---------------------------------------------------------------------------
# apply_rhythm_events
# ---------------------------------------------------------------------------


class TestApplyRhythmEvents:
    def test_empty_notes_passthrough(self):
        assert apply_rhythm_events([], QUARTERS_EVENTS) == []

    def test_empty_events_passthrough(self):
        notes = _notes([(60, 0.0), (62, 1.0)])
        assert apply_rhythm_events(notes, []) is notes

    def test_reimposes_grid_and_keeps_pitch(self):
        notes = _notes([(60, 0.0), (64, 1.0), (67, 2.0)])
        events = [RhythmEvent(0.0, 1.0), RhythmEvent(1.0, 1.0), RhythmEvent(2.0, 1.0)]
        out = apply_rhythm_events(notes, events)

        assert [n.start for n in out] == [0.0, 1.0, 2.0]
        assert all(n.duration == pytest.approx(1.0) for n in out)
        # Pitches carried from the closest source notes.
        assert [n.pitch for n in out] == [60, 64, 67]

    def test_velocity_scaled_and_clamped(self):
        notes = _notes([(60, 0.0)])
        # 1.5x of 100 -> 150 clamped to 127; 0.0x -> 1 (floor clamp).
        events = [RhythmEvent(0.0, 1.0, 1.5), RhythmEvent(0.5, 0.5, 0.0)]
        out = apply_rhythm_events(notes, events)
        assert out[0].velocity == 127
        assert out[1].velocity == 1

    def test_result_is_sorted(self):
        notes = _notes([(60, 0.0)])
        events = [RhythmEvent(2.0, 1.0), RhythmEvent(0.0, 1.0), RhythmEvent(1.0, 1.0)]
        out = apply_rhythm_events(notes, events)
        assert [n.start for n in out] == [0.0, 1.0, 2.0]


# ---------------------------------------------------------------------------
# _resolve_rhythm
# ---------------------------------------------------------------------------


class TestResolveRhythm:
    def test_unknown_name_raises(self):
        with pytest.raises(ValueError, match="Unknown rhythm name"):
            _resolve_rhythm("definitely_not_a_rhythm_xyzzy")

    def test_known_name_returns_generator(self):
        # straight_quarters is the hardcoded fallback — always present.
        gen = _resolve_rhythm("straight_quarters")
        assert hasattr(gen, "generate")

    def test_generator_instance_passthrough(self):
        gen = _StubRhythmGenerator(QUARTERS_EVENTS)
        assert _resolve_rhythm(gen) is gen

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError, match="rhythm must be a name"):
            _resolve_rhythm(42)


# ---------------------------------------------------------------------------
# produce_track rhythm contract
# ---------------------------------------------------------------------------


def _track_dict():
    return {
        "lead": _notes([(60, 0.0), (62, 0.5), (64, 1.0), (65, 1.5)]),
    }


class TestProduceTrackRhythm:
    def test_requires_rhythm(self, tmp_path):
        with pytest.raises(ValueError, match="rhythm is required"):
            produce_track(
                tracks=_track_dict(),
                bpm=120,
                instruments={"lead": 0},
                path=tmp_path / "out.mid",
                verbose=False,
                rhythm=None,
            )

    def test_unknown_rhythm_name_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown rhythm name"):
            produce_track(
                tracks=_track_dict(),
                bpm=120,
                instruments={"lead": 0},
                path=tmp_path / "out.mid",
                verbose=False,
                rhythm="not_a_real_rhythm",
                key=KEY,
                chords=CHORDS,
                genre=GENRE,
                time_signature=TIME_SIG,
            )

    def test_named_rhythm_runs_pipeline(self, tmp_path):
        report = produce_track(
            tracks=_track_dict(),
            bpm=120,
            instruments={"lead": 0},
            path=tmp_path / "out.mid",
            mood=Mood.AMBIENT,
            verbose=False,
            rhythm="straight_quarters",
            key=KEY,
            chords=CHORDS,
            genre=GENRE,
            time_signature=TIME_SIG,
        )
        # Report dict is returned on success (non-return_state path).
        assert isinstance(report, dict)
        assert "profiles" in report or "mood" in report

    def test_lays_notes_onto_grid(self):
        # Exercise the rhythm stage in isolation — downstream stages (humanize,
        # entropy) deliberately add micro-timing, so we verify the grid is
        # imposed HERE rather than asserting the full pipeline stays on-grid.
        from melodica.composer.album_pipeline import _stage_rhythm

        kw = {
            "tracks": _track_dict(),
            "rhythm": "straight_quarters",
        }
        out = _stage_rhythm(kw)
        notes = out["tracks"]["lead"]
        assert notes, "rhythm stage should keep at least one note"
        # straight_quarters is onsets at integer beats; after the rhythm stage
        # every note onset must be very close to an integer beat.
        for n in notes:
            frac = n.start - round(n.start)
            assert abs(frac) < 0.05, f"note onset {n.start} off the integer grid"


# ---------------------------------------------------------------------------
# produce_album / compile_continuous_album rhythm contract
# ---------------------------------------------------------------------------


class TestAlbumAndContinuousRhythm:
    def test_produce_album_requires_rhythm(self, tmp_path):
        with pytest.raises(ValueError, match="rhythm is required"):
            produce_album(
                tracks_list=[
                    (_track_dict(), 120, {"lead": 0}, "a.mid", Mood.AMBIENT),
                ],
                output_dir=str(tmp_path),
                rhythm=None,
            )

    def test_compile_continuous_album_requires_rhythm(self, tmp_path):
        meta = {
            "tracks": _track_dict(),
            "bpm": 120.0,
            "instruments": {"lead": 0},
        }
        with pytest.raises(ValueError, match="rhythm is required"):
            compile_continuous_album(
                tracks_metadata=[meta],
                output_path=tmp_path / "out.mid",
                rhythm=None,
            )

    def test_compile_continuous_album_runs_with_rhythm(self, tmp_path):
        meta = {
            "tracks": _track_dict(),
            "bpm": 120.0,
            "instruments": {"lead": 0},
            "key": KEY,
        }
        report = compile_continuous_album(
            tracks_metadata=[meta],
            output_path=tmp_path / "out.mid",
            mood=Mood.AMBIENT,
            rhythm="straight_quarters",
            chords=CHORDS,
            genre=GENRE,
            time_signature=TIME_SIG,
        )
        assert isinstance(report, dict)


# ---------------------------------------------------------------------------
# AlbumNarrative requires rhythm field
# ---------------------------------------------------------------------------


class TestAlbumNarrativeRhythm:
    def test_missing_rhythm_field_raises(self):
        # rhythm is a required dataclass field (no default) -> TypeError on
        # construction when omitted.
        with pytest.raises(TypeError):
            AlbumNarrative(
                output_dir="output/x",
                seed_motif=[NoteInfo(60, 0.0, 1.0)],
                harmonic_journey=[Scale(root=0, mode=Mode.MAJOR)],
                tempos=[120.0],
                track_configs=[[]],
                transformations=["original"],
                sections_list=[[(0.0, "Theme")]],
                instruments_maps=[{"lead": 0}],
                moods=[Mood.AMBIENT],
                names=["track1"],
            )
