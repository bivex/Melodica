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

"""tests/test_idea.py — Tests for the Idea Tool six-stage pipeline."""

import pytest
from melodica.types import (
    ArrangementSlot,
    ChordLabel,
    IdeaTrack,
    Mode,
    NoteInfo,
    PhraseInstance,
    Quality,
    Scale,
    StaticPhrase,
)
from melodica.generators.melody import MelodyGenerator
from melodica.idea import generate_idea, slots_to_notes, _random_rank, _chords_for_slot


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=8.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=12.0, duration=4.0),
    ]


def _seed() -> PhraseInstance:
    return PhraseInstance(static=StaticPhrase(notes=[
        NoteInfo(pitch=60, start=0.0, duration=1.0),
    ]))


def _track(phrase_order: str = "AA", random_order: bool = False) -> IdeaTrack:
    return IdeaTrack(
        seed_phrases=[_seed()],
        generator=MelodyGenerator(),
        phrase_order=phrase_order,
        random_order=random_order,
    )


class TestGenerateIdea:
    def test_returns_arrangement_slots(self):
        slots = generate_idea(_track("AABA"), _chords(), C_MAJOR, beats_per_slot=4.0)
        assert isinstance(slots, list)
        assert len(slots) == 4  # "AABA" has 4 positions

    def test_slot_labels_match_phrase_order(self):
        slots = generate_idea(_track("ABBA"), _chords(), C_MAJOR, beats_per_slot=4.0)
        labels = [s.label for s in slots]
        assert labels == ["A", "B", "B", "A"]

    def test_slot_start_beats_are_sequential(self):
        slots = generate_idea(_track("AABB"), _chords(), C_MAJOR, beats_per_slot=4.0)
        for i, slot in enumerate(slots):
            assert slot.start_beat == pytest.approx(i * 4.0)

    def test_empty_seeds_raises(self):
        track = _track("A")
        track.seed_phrases = []
        with pytest.raises(ValueError, match="lack of phrases"):
            generate_idea(track, _chords(), C_MAJOR)


    def test_lack_of_phrases_message(self):
        """Exact error message must be preserved."""
        from melodica.idea import generate_idea
        track = IdeaTrack.__new__(IdeaTrack)
        track.seed_phrases = []
        track.generator = MelodyGenerator()
        track.phrase_order = "A"
        track.random_order = False
        with pytest.raises(ValueError, match="lack of phrases!"):
            generate_idea(track, _chords(), C_MAJOR)

    def test_random_order_flag(self):
        track = _track("ABCD", random_order=True)
        # Add more seeds
        track.seed_phrases = [_seed(), _seed(), _seed(), _seed()]
        slots = generate_idea(track, _chords(), C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 4

    def test_static_phrases_in_output(self):
        slots = generate_idea(_track("AA"), _chords(), C_MAJOR, beats_per_slot=4.0)
        for slot in slots:
            assert slot.phrase.static is not None


class TestSlotsToNotes:
    def test_absolute_timing(self):
        slots = generate_idea(_track("AB"), _chords(), C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        # All notes should have start >= 0
        assert all(n.start >= 0.0 for n in notes)
        # Notes from second slot must start >= 4.0
        slot_b_notes = [n for n in notes if n.start >= 4.0]
        assert slot_b_notes  # second slot contributed notes

    def test_sorted_by_start(self):
        slots = generate_idea(_track("AABB"), _chords(), C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        starts = [n.start for n in notes]
        assert starts == sorted(starts)


class TestChordsForSlot:
    def test_returns_correct_window(self):
        chords = _chords()
        slot = _chords_for_slot(chords, 0, 4.0)
        assert all(c.start < 4.0 for c in slot)

    def test_adjusted_start(self):
        chords = _chords()
        slot = _chords_for_slot(chords, 1, 4.0)  # window [4, 8)
        assert all(c.start >= 0.0 for c in slot)  # relative to slot


class TestRandomRank:
    def test_preserves_all_elements(self):
        items = [1, 2, 3, 4, 5]
        ranked = _random_rank(items)
        assert sorted(ranked) == sorted(items)

    def test_returns_same_length(self):
        items = list(range(10))
        assert len(_random_rank(items)) == len(items)
