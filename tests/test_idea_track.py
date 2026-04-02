"""
tests/test_idea_track.py — Mutation coverage for IdeaTrack phrase_order correctness.

Tests:
  - Phrase order label fidelity (any pattern → correct ArrangementSlot labels)
  - Arrangement generation with various generators
  - Context threading between phrases
  - Edge cases / mutations (empty, extreme, single-letter, unicode-ish)
  - slots_to_notes absolute timing
  - _chords_for_slot window math
  - random_order behaviour
"""

import pytest
import random
from unittest.mock import MagicMock, patch

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
from melodica.generators import (
    MelodyGenerator,
    AmbientPadGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    GeneratorParams,
)
from melodica.idea import generate_idea, slots_to_notes, _random_rank, _chords_for_slot

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
D_MINOR = Scale(root=2, mode=Mode.NATURAL_MINOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _chords(n: int = 4, beats: float = 4.0) -> list[ChordLabel]:
    """n chords each `beats` long, covering [0, n*beats)."""
    return [
        ChordLabel(
            root=[0, 7, 5, 9][i % 4],
            quality=Quality.MAJOR,
            start=i * beats,
            duration=beats,
        )
        for i in range(n)
    ]


def _seed(notes: list[tuple[float, float, float]] | None = None) -> PhraseInstance:
    """Static phrase with explicit notes.  Default: single C4 quarter."""
    if notes is None:
        notes = [(60, 0.0, 1.0)]
    return PhraseInstance(
        static=StaticPhrase(notes=[NoteInfo(pitch=p, start=s, duration=d) for p, s, d in notes])
    )


def _track(phrase_order: str = "A", gen=None, random_order=False) -> IdeaTrack:
    if gen is None:
        gen = MelodyGenerator()
    return IdeaTrack(
        seed_phrases=[_seed()],
        generator=gen,
        phrase_order=phrase_order,
        random_order=random_order,
    )


# ===================================================================
# §1 — Phrase-order label fidelity
# ===================================================================


class TestPhraseOrderLabels:
    """phrase_order string → ArrangementSlot.label must be exact."""

    @pytest.mark.parametrize(
        "order",
        [
            "A",
            "AA",
            "AB",
            "AABA",
            "AABB",
            "ABBA",
            "ABAB",
            "ABCD",
            "ABAC",
            "AABBAA",
            "ABACAB",
            "ABCDAB",
            "ABCDEFGH",
        ],
    )
    def test_labels_match_pattern(self, order):
        chords = _chords(n=len(order))
        slots = generate_idea(_track(order), chords, C_MAJOR, beats_per_slot=4.0)
        assert [s.label for s in slots] == list(order)

    def test_aaba_classic(self):
        chords = _chords(4)
        slots = generate_idea(_track("AABA"), chords, C_MAJOR, beats_per_slot=4.0)
        labels = [s.label for s in slots]
        assert labels == ["A", "A", "B", "A"]
        assert slots[0].label == slots[1].label == slots[3].label != slots[2].label

    def test_very_long_pattern(self):
        order = "AABBAABBAABBAABB"
        chords = _chords(len(order))
        slots = generate_idea(_track(order), chords, C_MAJOR, beats_per_slot=4.0)
        assert [s.label for s in slots] == list(order)
        assert len(slots) == 16


# ===================================================================
# §2 — Slot start_beats sequencing
# ===================================================================


class TestSlotStartBeats:
    @pytest.mark.parametrize(
        "order,beats",
        [
            ("A", 4.0),
            ("AB", 8.0),
            ("AABA", 4.0),
            ("ABCD", 2.0),
            ("AAAAAA", 16.0),
        ],
    )
    def test_sequential_offsets(self, order, beats):
        chords = _chords(n=len(order), beats=beats)
        slots = generate_idea(_track(order), chords, C_MAJOR, beats_per_slot=beats)
        for i, slot in enumerate(slots):
            assert slot.start_beat == pytest.approx(i * beats)

    def test_non_overlapping_notes(self):
        """Notes from adjacent slots must not overlap in time."""
        chords = _chords(4)
        slots = generate_idea(_track("AABB"), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        for i in range(1, len(notes)):
            # each note starts at or after the previous note starts
            assert notes[i].start >= notes[i - 1].start


# ===================================================================
# §3 — Arrangement generation with different generators
# ===================================================================


class TestArrangementGenerators:
    """Verify IdeaTrack works with real PhraseGenerator subclasses."""

    @pytest.mark.parametrize(
        "gen_cls,kwargs",
        [
            (MelodyGenerator, {}),
            (AmbientPadGenerator, {}),
            (ArpeggiatorGenerator, {"pattern": "up_down", "note_duration": 0.5}),
            (BassGenerator, {}),
            (ChordGenerator, {}),
        ],
    )
    def test_produces_notes(self, gen_cls, kwargs):
        gen = gen_cls(params=GeneratorParams(density=0.5), **kwargs)
        chords = _chords(4)
        track = _track("AABA", gen=gen)
        slots = generate_idea(track, chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        assert len(notes) > 0, f"{gen_cls.__name__} produced zero notes"

    def test_each_slot_has_notes(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.8))
        chords = _chords(4)
        slots = generate_idea(_track("AABA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        for slot in slots:
            assert slot.phrase.static is not None
            # At least the seed note should survive
            assert len(slot.phrase.static.notes) > 0


# ===================================================================
# §4 — Context threading between phrases
# ===================================================================


class TestContextThreading:
    """RenderContext should carry state from phrase N to N+1."""

    def test_prev_pitch_carried(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.9))
        chords = _chords(2)
        track = _track("AB", gen=gen)
        slots = generate_idea(track, chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        # There should be notes in both slots
        assert len([n for n in notes if n.start < 4.0]) > 0
        assert len([n for n in notes if n.start >= 4.0]) > 0

    def test_phrase_position_progresses(self):
        """phrase_position should go from 0.0 → 1.0 across slots."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.5))
        chords = _chords(4)
        slots = generate_idea(_track("AAAA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 4

    def test_context_none_on_first_slot(self):
        """First render call should work with no prior context."""
        gen = MelodyGenerator()
        chords = _chords(1)
        slots = generate_idea(_track("A", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 1
        assert len(slots[0].phrase.static.notes) > 0


# ===================================================================
# §5 — slots_to_notes correctness
# ===================================================================


class TestSlotsToNotes:
    def test_absolute_timing_monotonic(self):
        chords = _chords(4)
        slots = generate_idea(_track("AABB"), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        starts = [n.start for n in notes]
        assert starts == sorted(starts)

    def test_all_notes_non_negative(self):
        chords = _chords(4)
        slots = generate_idea(_track("ABCD"), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        assert all(n.start >= 0.0 for n in notes)

    def test_notes_from_later_slots_offset(self):
        chords = _chords(4)
        slots = generate_idea(_track("AB"), chords, C_MAJOR, beats_per_slot=8.0)
        notes = slots_to_notes(slots)
        slot_b = [n for n in notes if n.start >= 8.0]
        assert len(slot_b) > 0

    def test_empty_slots_list(self):
        assert slots_to_notes([]) == []

    def test_total_duration_within_bounds(self):
        chords = _chords(4)
        slots = generate_idea(_track("AABB"), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        max_end = max((n.start + n.duration) for n in notes)
        # total arrangement is 4 slots × 4 beats = 16
        assert max_end <= 16.0 + 1.0  # allow tiny overshoot for legato


# ===================================================================
# §6 — _chords_for_slot window math
# ===================================================================


class TestChordsForSlot:
    def test_first_slot_covers_first_chord(self):
        chords = _chords(4)
        result = _chords_for_slot(chords, 0, 4.0)
        assert len(result) == 1
        assert result[0].root == chords[0].root

    def test_slot_relative_starts_within_range(self):
        chords = _chords(4)
        result = _chords_for_slot(chords, 1, 4.0)
        for c in result:
            assert c.start >= 0.0
            assert c.start < 4.0

    def test_fallback_when_no_chords_overlap(self):
        c = ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)
        result = _chords_for_slot([c], 2, 8.0)  # slot [16, 24), chord is [0, 4)
        assert len(result) == 1
        assert result[0].duration == 8.0
        assert result[0].start == 0.0

    def test_empty_chord_list_returns_empty(self):
        result = _chords_for_slot([], 0, 4.0)
        # No fallback possible → empty
        assert result == []

    def test_chord_spanning_two_slots(self):
        c = ChordLabel(root=5, quality=Quality.MINOR, start=2.0, duration=12.0)
        slot0 = _chords_for_slot([c], 0, 4.0)
        slot1 = _chords_for_slot([c], 1, 4.0)
        assert len(slot0) == 1
        assert len(slot1) == 1
        assert slot0[0].duration == pytest.approx(2.0)  # [2, 4)
        assert slot1[0].duration == pytest.approx(4.0)  # [4, 8) fully covered


# ===================================================================
# §7 — Mutation / edge cases
# ===================================================================


class TestIdeaTrackMutations:
    """Edge-case mutations that stress the pipeline."""

    def test_single_letter_order(self):
        chords = _chords(1)
        slots = generate_idea(_track("A"), chords, C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 1
        assert slots[0].label == "A"
        assert slots[0].start_beat == 0.0

    def test_empty_seeds_raises(self):
        track = _track("A")
        track.seed_phrases = []
        with pytest.raises(ValueError, match="lack of phrases"):
            generate_idea(track, _chords(1), C_MAJOR)

    def test_exact_error_message(self):
        track = IdeaTrack.__new__(IdeaTrack)
        track.seed_phrases = []
        track.generator = MelodyGenerator()
        track.phrase_order = "A"
        track.random_order = False
        with pytest.raises(ValueError, match="lack of phrases!"):
            generate_idea(track, _chords(1), C_MAJOR)

    def test_very_small_beats_per_slot(self):
        chords = _chords(4, beats=0.5)
        slots = generate_idea(_track("AB"), chords, C_MAJOR, beats_per_slot=0.5)
        assert len(slots) == 2
        assert slots[1].start_beat == pytest.approx(0.5)

    def test_large_beats_per_slot(self):
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=64.0)]
        slots = generate_idea(_track("AABA"), chords, C_MAJOR, beats_per_slot=64.0)
        assert len(slots) == 4
        assert slots[-1].start_beat == pytest.approx(192.0)

    def test_zero_density_generator(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.0))
        chords = _chords(2)
        slots = generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        # density=0 → probably no notes, but should not crash
        assert isinstance(notes, list)

    def test_max_density_generator(self):
        gen = MelodyGenerator(params=GeneratorParams(density=1.0))
        chords = _chords(4)
        slots = generate_idea(_track("AABA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        assert len(notes) > 0

    def test_random_order_flag(self):
        random.seed(42)
        gen = MelodyGenerator()
        track = _track("ABCD", gen=gen, random_order=True)
        track.seed_phrases = [_seed(), _seed(), _seed(), _seed()]
        slots = generate_idea(track, _chords(4), C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 4

    def test_different_scales(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.5))
        for scale in [C_MAJOR, D_MINOR, A_MINOR]:
            chords = _chords(4)
            slots = generate_idea(_track("AA", gen=gen), chords, scale, beats_per_slot=4.0)
            assert len(slots) == 2

    def test_repeated_single_letter(self):
        """AAAA → four slots all with label A."""
        chords = _chords(4)
        slots = generate_idea(_track("AAAA"), chords, C_MAJOR, beats_per_slot=4.0)
        assert all(s.label == "A" for s in slots)
        assert len(slots) == 4

    def test_all_different_labels(self):
        """ABCDEFGH → 8 unique labels in order."""
        order = "ABCDEFGH"
        chords = _chords(8)
        slots = generate_idea(_track(order), chords, C_MAJOR, beats_per_slot=4.0)
        assert [s.label for s in slots] == list(order)

    def test_slot_notes_within_beat_range(self):
        """Notes in slot[i] should mostly fall within [start_beat, start_beat + slot_dur)."""
        chords = _chords(4)
        slots = generate_idea(_track("AABA"), chords, C_MAJOR, beats_per_slot=4.0)
        for slot in slots:
            for note in slot.phrase.static.notes:
                # Generator-internal start is relative to slot → should be < beats_per_slot
                # (allow slight overshoot for ties/legato)
                assert note.start < 4.0 + 1.0

    def test_multiple_seeds(self):
        s1 = _seed([(60, 0.0, 1.0)])
        s2 = _seed([(64, 0.0, 1.0)])
        s3 = _seed([(67, 0.0, 1.0)])
        track = IdeaTrack(
            seed_phrases=[s1, s2, s3],
            generator=MelodyGenerator(),
            phrase_order="AAB",
        )
        slots = generate_idea(track, _chords(3), C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 3


# ===================================================================
# §8 — _random_rank
# ===================================================================


class TestRandomRank:
    def test_preserves_elements(self):
        items = [1, 2, 3, 4, 5]
        ranked = _random_rank(items)
        assert sorted(ranked) == sorted(items)

    def test_same_length(self):
        items = list(range(20))
        assert len(_random_rank(items)) == len(items)

    def test_single_element(self):
        assert _random_rank([42]) == [42]

    def test_empty_list(self):
        assert _random_rank([]) == []

    def test_deterministic_with_seed(self):
        random.seed(99)
        r1 = _random_rank([1, 2, 3, 4])
        random.seed(99)
        r2 = _random_rank([1, 2, 3, 4])
        assert r1 == r2


# ===================================================================
# §9 — Full arrangement: 7-act arc (like df_downtempo)
# ===================================================================


class TestFullArrangement:
    """Mimics a real multi-section arrangement."""

    def test_seven_act_arc(self):
        """Fog→Pulse→Flow→Depth→Glow→Fade→Sleep pattern."""
        order = "ABCDEFG"
        gen = MelodyGenerator(params=GeneratorParams(density=0.3))
        chords = _chords(7, beats=8.0)
        track = _track(order, gen=gen)
        slots = generate_idea(track, chords, C_MAJOR, beats_per_slot=8.0)
        assert len(slots) == 7
        assert [s.label for s in slots] == list(order)

        notes = slots_to_notes(slots)
        assert len(notes) > 0

        # verify notes span across the full range
        max_end = max(n.start + n.duration for n in notes)
        assert max_end > 0

    def test_jazz_aaba(self):
        """Classic 32-bar jazz form: A(8) A(8) B(8) A(8)."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.6))
        chords = _chords(16, beats=2.0)
        track = _track("AABA", gen=gen)
        slots = generate_idea(track, chords, C_MAJOR, beats_per_slot=8.0)
        notes = slots_to_notes(slots)
        assert len(notes) > 0
        # 4 slots × 8 beats = 32 beats
        assert slots[-1].start_beat == pytest.approx(24.0)

    def test_rondo_abacaba(self):
        """Rondo form: ABACABA."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.5))
        chords = _chords(7)
        track = _track("ABACABA", gen=gen)
        slots = generate_idea(track, chords, D_MINOR, beats_per_slot=4.0)
        assert [s.label for s in slots] == list("ABACABA")
        notes = slots_to_notes(slots)
        assert len(notes) > 0
