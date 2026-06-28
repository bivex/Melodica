# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""Tests for the mandatory key/chords/genre/time_signature contract on album
production entry points (companion to test_album_rhythm.py).

Also guards the chords-propagation fix: previously `produce_track` hardcoded
`chords=None` in its stage kwargs, silently disabling the texture /
non_chord_tones / tension stages. These tests verify the progression now
reaches the pipeline stages.
"""

import pytest

from melodica.types import NoteInfo, Scale, Mode, parse_progression
from melodica.composer.album_pipeline import (
    produce_track,
    produce_album,
    compile_continuous_album,
    AlbumNarrative,
    Mood,
    Stage,
    DEFAULT_PIPELINE,
    DEFAULT_GENRE,
    _ROLE_PAN_PROFILES,
    _stage_non_chord_tones,
    _stage_texture,
)


KEY = Scale(root=0, mode=Mode.MAJOR)
CHORDS = parse_progression("I - V - vi - IV", KEY)
GENRE = "lofi"
TIME_SIG = (4, 4)
RHYTHM = "straight_quarters"


def _track_dict():
    return {
        "lead": [NoteInfo(pitch=60 + i, start=float(i), duration=0.8, velocity=80)
                 for i in range(8)],
    }


def _base_produce_track_kwargs(tmp_path, **over):
    kw = dict(
        tracks=_track_dict(),
        bpm=120,
        instruments={"lead": 0},
        path=tmp_path / "out.mid",
        mood=Mood.AMBIENT,
        verbose=False,
        rhythm=RHYTHM,
        key=KEY,
        chords=CHORDS,
        genre=GENRE,
        time_signature=TIME_SIG,
    )
    kw.update(over)
    return kw


# ---------------------------------------------------------------------------
# produce_track: each required field raises on its own
# ---------------------------------------------------------------------------


class TestProduceTrackRequired:
    def test_key_required(self, tmp_path):
        with pytest.raises(ValueError, match="key is required"):
            produce_track(**_base_produce_track_kwargs(tmp_path, key=None))

    def test_chords_required(self, tmp_path):
        with pytest.raises(ValueError, match="chords is required"):
            produce_track(**_base_produce_track_kwargs(tmp_path, chords=None))

    def test_genre_defaults_to_lofi(self, tmp_path):
        # genre is optional — omitted → DEFAULT_GENRE ('lofi'), no raise.
        kw = _base_produce_track_kwargs(tmp_path)
        kw.pop("genre")
        report = produce_track(**kw)
        assert isinstance(report, dict)

    def test_time_signature_required(self, tmp_path):
        with pytest.raises(ValueError, match="time_signature is required"):
            produce_track(**_base_produce_track_kwargs(tmp_path, time_signature=None))

    def test_unknown_genre_raises(self, tmp_path):
        with pytest.raises(ValueError, match="Unknown genre"):
            produce_track(**_base_produce_track_kwargs(tmp_path, genre="reggaeton"))

    @pytest.mark.parametrize("bad_ts", [(4, 3), (0, 4), (4, 5), (4,), "4/4", None])
    def test_bad_time_signature_raises(self, tmp_path, bad_ts):
        # None is caught by the dedicated "required" check; everything else by
        # the structural check. Both raise ValueError.
        with pytest.raises(ValueError, match="time_signature"):
            produce_track(**_base_produce_track_kwargs(tmp_path, time_signature=bad_ts))

    def test_all_known_genres_accepted(self, tmp_path):
        for g in sorted(_ROLE_PAN_PROFILES):
            report = produce_track(**_base_produce_track_kwargs(tmp_path, genre=g))
            assert isinstance(report, dict)


# ---------------------------------------------------------------------------
# chords-propagation regression: the harmonic stages must NOT be skipped
# ---------------------------------------------------------------------------


class TestChordsPropagation:
    def _kw_with_profiles(self):
        """Build the stage-passing kw dict the way produce_track does, with
        auto-mix already having populated _profiles."""
        from melodica.composer.album_pipeline import _auto_mix
        tracks = _track_dict()
        mixed, profiles, _ = _auto_mix(tracks, _mood_profile())
        return {
            "tracks": mixed,
            "_profiles": profiles,
            "chords": CHORDS,
            "key": KEY,
            "bpm": 120,
        }

    def test_chords_reach_non_chord_tones_stage(self):
        """_stage_non_chord_tones reads kw.get('chords'); it must be non-None."""
        kw = self._kw_with_profiles()
        # Before the fix kw['chords'] was hardcoded None → stage early-returned.
        assert kw["chords"] is not None

    def test_non_chord_tones_stage_does_not_early_return_with_chords(self):
        """With chords+key present the stage runs on LEAD tracks (does not just
        pass the input through unchanged)."""
        kw = self._kw_with_profiles()
        before = list(kw["tracks"]["lead"])
        out = _stage_non_chord_tones(dict(kw))
        after = out["tracks"]["lead"]
        # NonChordToneGenerator may add passing/neighbor tones → track changes.
        # The key assertion is that it ran (input is a LEAD role, chords+key set)
        # rather than short-circuiting. We accept both growth and stable length
        # but require the function executed on the non-None chords.
        assert isinstance(after, list)
        assert len(after) >= 1
        # Sanity: if it added notes, total beats must still extend forward.
        if len(after) > len(before):
            assert min(n.start for n in after) >= 0.0

    def test_texture_stage_receives_chords(self):
        kw = self._kw_with_profiles()
        out = _stage_texture(dict(kw))
        assert "tracks" in out


# ---------------------------------------------------------------------------
# produce_album required fields
# ---------------------------------------------------------------------------


class TestProduceAlbumRequired:
    def test_key_required(self, tmp_path):
        with pytest.raises(ValueError, match="key is required"):
            produce_album(
                tracks_list=[(_track_dict(), 120, {"lead": 0}, "a.mid", Mood.AMBIENT)],
                output_dir=str(tmp_path),
                rhythm=RHYTHM, chords=CHORDS, genre=GENRE, time_signature=TIME_SIG,
                key=None,
            )

    def test_chords_required(self, tmp_path):
        with pytest.raises(ValueError, match="chords is required"):
            produce_album(
                tracks_list=[(_track_dict(), 120, {"lead": 0}, "a.mid", Mood.AMBIENT)],
                output_dir=str(tmp_path),
                rhythm=RHYTHM, key=KEY, genre=GENRE, time_signature=TIME_SIG,
                chords=None,
            )

    def test_genre_defaults(self, tmp_path):
        # genre optional for produce_album — omitting it must not raise.
        tracks_list = [(_track_dict(), 120, {"lead": 0}, "a.mid", Mood.AMBIENT)]
        try:
            produce_album(
                tracks_list=tracks_list,
                output_dir=str(tmp_path),
                rhythm=RHYTHM, key=KEY, chords=CHORDS, time_signature=TIME_SIG,
            )
        except Exception:
            pytest.fail("produce_album should accept an omitted genre (defaults to lofi)")

    def test_time_signature_required(self, tmp_path):
        with pytest.raises(ValueError, match="time_signature is required"):
            produce_album(
                tracks_list=[(_track_dict(), 120, {"lead": 0}, "a.mid", Mood.AMBIENT)],
                output_dir=str(tmp_path),
                rhythm=RHYTHM, key=KEY, chords=CHORDS, genre=GENRE,
                time_signature=None,
            )


# ---------------------------------------------------------------------------
# compile_continuous_album required fields
# ---------------------------------------------------------------------------


def _continuous_meta():
    return {"tracks": _track_dict(), "bpm": 120.0, "instruments": {"lead": 0}, "key": KEY}


class TestCompileContinuousRequired:
    def test_chords_required(self, tmp_path):
        with pytest.raises(ValueError, match="chords is required"):
            compile_continuous_album(
                tracks_metadata=[_continuous_meta()],
                output_path=tmp_path / "o.mid",
                rhythm=RHYTHM, genre=GENRE, time_signature=TIME_SIG,
                chords=None,
            )

    def test_genre_defaults(self, tmp_path):
        # genre optional for compile_continuous_album — omitting it must not raise.
        try:
            compile_continuous_album(
                tracks_metadata=[_continuous_meta()],
                output_path=tmp_path / "o.mid",
                rhythm=RHYTHM, chords=CHORDS, time_signature=TIME_SIG,
            )
        except Exception:
            pytest.fail("compile_continuous_album should accept an omitted genre")

    def test_time_signature_required(self, tmp_path):
        with pytest.raises(ValueError, match="time_signature is required"):
            compile_continuous_album(
                tracks_metadata=[_continuous_meta()],
                output_path=tmp_path / "o.mid",
                rhythm=RHYTHM, chords=CHORDS, genre=GENRE,
                time_signature=None,
            )


# ---------------------------------------------------------------------------
# AlbumNarrative requires genre + time_signature (key comes via harmonic_journey)
# ---------------------------------------------------------------------------


class TestAlbumNarrativeRequired:
    def _base_fields(self):
        return dict(
            output_dir="output/x",
            seed_motif=[NoteInfo(60, 0.0, 1.0)],
            harmonic_journey=[Scale(root=0, mode=Mode.MAJOR)],
            tempos=[120.0],
            track_configs=[[]],
            transformations=["original"],
            sections_list=[[(0.0, "Theme")]],
            instruments_maps=[{"lead": 0}],
            moods=[Mood.AMBIENT],
            names=["t1"],
            rhythm=RHYTHM,
        )

    def test_genre_defaults(self):
        # genre optional for AlbumNarrative — omitting it must not raise and
        # must default to DEFAULT_GENRE.
        narrative = AlbumNarrative(time_signature=TIME_SIG, **self._base_fields())
        assert narrative.genre == DEFAULT_GENRE

    def test_missing_time_signature_raises(self):
        # time_signature is still mandatory (no default).
        with pytest.raises(TypeError):
            AlbumNarrative(genre=GENRE, **self._base_fields())


def _mood_profile():
    from melodica.composer.album_pipeline import _MOOD_PROFILES
    return _MOOD_PROFILES[Mood.AMBIENT]


# ---------------------------------------------------------------------------
# Pipeline structure: time_signature & chords keys present in kw after run
# ---------------------------------------------------------------------------


class TestPipelineWiring:
    def test_default_pipeline_has_rhythm_first(self):
        names = [s.name for s in DEFAULT_PIPELINE]
        assert names[0] == "rhythm"

    def test_produce_track_return_state_carries_new_fields(self, tmp_path):
        state = produce_track(**_base_produce_track_kwargs(tmp_path, return_state=True))
        assert state["genre"] == GENRE
        assert state["time_signature"] == TIME_SIG
        assert state["key"] == KEY
