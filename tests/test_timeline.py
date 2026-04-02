"""
tests/test_timeline.py — Tests for MusicTimeline.get_key_at().

Covers:
  - get_key_at() with single key
  - get_key_at() with multiple keys (modulation)
  - get_key_at() with empty keys (default)
  - Edge cases: before first key, between keys, at exact boundary
"""

import pytest
from melodica.types import Scale, Mode, ChordLabel, Quality
from melodica.types_pkg._timeline import MusicTimeline, KeyLabel, TimeSignatureLabel


# ===================================================================
# §1 — get_key_at basic
# ===================================================================


class TestGetKeyAt:
    def test_single_key_returns_that_scale(self):
        tl = MusicTimeline(
            chords=[],
            keys=[KeyLabel(scale=Scale(root=0, mode=Mode.MAJOR), start=0, duration=32)],
        )
        assert tl.get_key_at(0).root == 0
        assert tl.get_key_at(16).root == 0
        assert tl.get_key_at(31).root == 0

    def test_empty_keys_returns_c_major_default(self):
        tl = MusicTimeline(chords=[], keys=[])
        key = tl.get_key_at(0)
        assert key.root == 0
        assert key.mode == Mode.MAJOR

    def test_before_first_key_returns_first(self):
        tl = MusicTimeline(
            chords=[],
            keys=[KeyLabel(scale=Scale(root=7, mode=Mode.MAJOR), start=8, duration=24)],
        )
        # At t=0, the only key has start=8 > 0. Implementation returns first key's scale.
        key = tl.get_key_at(0)
        assert key.root == 7  # first (and only) key

    def test_at_key_boundary(self):
        tl = MusicTimeline(
            chords=[],
            keys=[
                KeyLabel(scale=Scale(root=0, mode=Mode.MAJOR), start=0, duration=16),
                KeyLabel(scale=Scale(root=7, mode=Mode.MAJOR), start=16, duration=16),
            ],
        )
        assert tl.get_key_at(16).root == 7
        assert tl.get_key_at(15).root == 0


# ===================================================================
# §2 — Key changes (modulation)
# ===================================================================


class TestModulation:
    def test_two_keys(self):
        tl = MusicTimeline(
            chords=[],
            keys=[
                KeyLabel(scale=Scale(root=0, mode=Mode.MAJOR), start=0, duration=16),
                KeyLabel(scale=Scale(root=2, mode=Mode.DORIAN), start=16, duration=16),
            ],
        )
        assert tl.get_key_at(8).root == 0
        assert tl.get_key_at(8).mode == Mode.MAJOR
        assert tl.get_key_at(24).root == 2
        assert tl.get_key_at(24).mode == Mode.DORIAN

    def test_three_keys(self):
        tl = MusicTimeline(
            chords=[],
            keys=[
                KeyLabel(scale=Scale(root=0, mode=Mode.MAJOR), start=0, duration=8),
                KeyLabel(scale=Scale(root=5, mode=Mode.MAJOR), start=8, duration=8),
                KeyLabel(scale=Scale(root=7, mode=Mode.MIXOLYDIAN), start=16, duration=8),
            ],
        )
        assert tl.get_key_at(4).root == 0
        assert tl.get_key_at(12).root == 5
        assert tl.get_key_at(20).root == 7
        assert tl.get_key_at(20).mode == Mode.MIXOLYDIAN

    def test_unsorted_keys(self):
        """Keys not in start order should still work (sorted internally)."""
        tl = MusicTimeline(
            chords=[],
            keys=[
                KeyLabel(scale=Scale(root=7, mode=Mode.MAJOR), start=16, duration=16),
                KeyLabel(scale=Scale(root=0, mode=Mode.MAJOR), start=0, duration=16),
            ],
        )
        assert tl.get_key_at(8).root == 0
        assert tl.get_key_at(24).root == 7


# ===================================================================
# §3 — MusicTimeline fields
# ===================================================================


class TestMusicTimeline:
    def test_default_fields(self):
        tl = MusicTimeline(chords=[], keys=[])
        assert tl.time_signatures == []
        assert tl.markers == []

    def test_with_chords(self):
        tl = MusicTimeline(
            chords=[ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)],
            keys=[],
        )
        assert len(tl.chords) == 1
