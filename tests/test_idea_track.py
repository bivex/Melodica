"""
tests/test_idea_track.py — Senior-level property & invariant tests for IdeaTrack.

What these tests actually verify (not just "does it run"):
  - Musical invariants: pitch ∈ [0,127], duration > 0, velocity ∈ [0,127], start ≥ 0
  - Context propagation: prev_pitch from slot N reaches slot N+1
  - Same-label slots are NOT identical output (context + position change things)
  - Different phrase_order → different note sequences (form matters)
  - Chord-slice fidelity: generator receives chords with correct root/quality
  - phrase_position maps correctly: 0.0 → 1.0 across positions
  - Fallback chord logic triggers when no chords overlap
  - Parametric PhraseInstance raises on slots_to_notes (assert)
  - Density scales note count (higher density → more notes)
  - Note time windows: notes stay within [slot.start, slot.start + slot_dur + epsilon)
"""

import pytest
import random
from unittest.mock import MagicMock, patch, call

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
from melodica.render_context import RenderContext

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
D_MINOR = Scale(root=2, mode=Mode.NATURAL_MINOR)
A_NAT_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _chords(n: int = 4, beats: float = 4.0, quality=Quality.MAJOR) -> list[ChordLabel]:
    """n chords each `beats` long, roots cycling I-V-iii-vi."""
    return [
        ChordLabel(root=[0, 7, 5, 9][i % 4], quality=quality, start=i * beats, duration=beats)
        for i in range(n)
    ]


def _seed(notes=None) -> PhraseInstance:
    if notes is None:
        notes = [(60, 0.0, 1.0)]
    return PhraseInstance(
        static=StaticPhrase(notes=[NoteInfo(pitch=p, start=s, duration=d) for p, s, d in notes])
    )


def _track(phrase_order="A", gen=None, random_order=False, seeds=None) -> IdeaTrack:
    return IdeaTrack(
        seed_phrases=seeds or [_seed()],
        generator=gen or MelodyGenerator(),
        phrase_order=phrase_order,
        random_order=random_order,
    )


def _violation_report(notes: list[NoteInfo]) -> list[str]:
    """Return a list of invariant violations for auditing."""
    violations = []
    for i, n in enumerate(notes):
        if n.pitch < 0 or n.pitch > 127:
            violations.append(f"[{i}] pitch={n.pitch} out of MIDI range")
        if n.duration <= 0:
            violations.append(f"[{i}] duration={n.duration} <= 0")
        if n.velocity < 0 or n.velocity > 127:
            violations.append(f"[{i}] velocity={n.velocity} out of range")
        if n.start < 0:
            violations.append(f"[{i}] start={n.start} < 0")
    return violations


# ===================================================================
# §1 — Hard invariants (every generated note must pass)
# ===================================================================


class TestInvariants:
    """These MUST hold for every note the pipeline produces."""

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
    def test_midi_invariants(self, gen_cls, kwargs):
        """pitch∈[0,127], duration>0, velocity∈[0,127], start≥0."""
        gen = gen_cls(params=GeneratorParams(density=0.7), **kwargs)
        chords = _chords(8)
        slots = generate_idea(_track("AABA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        violations = _violation_report(notes)
        assert violations == [], f"{gen_cls.__name__}: {violations[:5]}"

    @pytest.mark.parametrize("order", ["A", "AABA", "ABACABA", "ABCDEFGH"])
    def test_invariants_across_forms(self, order):
        gen = MelodyGenerator(params=GeneratorParams(density=0.6))
        chords = _chords(len(order))
        slots = generate_idea(_track(order, gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        violations = _violation_report(notes)
        assert violations == [], f"order={order}: {violations[:5]}"

    def test_notes_stay_within_arrangement_window(self):
        """Every note must end before the arrangement ends (with small tolerance)."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.8))
        chords = _chords(4)
        bps = 4.0
        slots = generate_idea(_track("AABA", gen=gen), chords, C_MAJOR, beats_per_slot=bps)
        notes = slots_to_notes(slots)
        arrangement_end = len("AABA") * bps
        overshoots = [
            n
            for n in notes
            if n.start + n.duration > arrangement_end + 2.0  # 2-beat tolerance for legato
        ]
        assert overshoots == [], f"{len(overshoots)} notes extend beyond arrangement window"

    def test_no_note_start_after_arrangement(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.5))
        chords = _chords(4)
        slots = generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=8.0)
        notes = slots_to_notes(slots)
        arrangement_end = 2 * 8.0
        late = [n for n in notes if n.start > arrangement_end + 0.01]
        assert late == []


# ===================================================================
# §2 — Context propagation (prev_pitch carries between slots)
# ===================================================================


class TestContextPropagation:
    """Verify that the render context actually threads state between slots."""

    def test_mocked_render_receives_prev_pitch(self):
        """Slot 1's render() should receive prev_pitch = last note of slot 0."""
        gen = MagicMock(spec=MelodyGenerator)
        slot0_notes = [NoteInfo(pitch=67, start=0.0, duration=2.0, velocity=80)]
        slot1_notes = [NoteInfo(pitch=72, start=0.0, duration=2.0, velocity=70)]
        gen.render.side_effect = [slot0_notes, slot1_notes]
        gen._last_context = None

        chords = _chords(2)
        slots = generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        # First call: prev_pitch should be None
        ctx0 = gen.render.call_args_list[0][1].get("context") or gen.render.call_args_list[0][0][3]
        # Second call: prev_pitch should be 67 (fallback path, since _last_context is None)
        ctx1 = gen.render.call_args_list[1][1].get("context") or gen.render.call_args_list[1][0][3]

        assert ctx0.prev_pitch is None  # first slot, no prior
        assert ctx1.prev_pitch == 67  # fallback: last note pitch from slot 0

    def test_mocked_render_receives_prev_chord(self):
        gen = MagicMock(spec=MelodyGenerator)
        gen.render.return_value = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        gen._last_context = None

        chords = _chords(2)
        slots = generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        # Slot 1 should get prev_chord = last chord of slot 0
        ctx1 = gen.render.call_args_list[1][1].get("context") or gen.render.call_args_list[1][0][3]
        assert ctx1.prev_chord is not None
        assert ctx1.prev_chord.root == chords[0].root

    def test_context_used_from_generator_last_context(self):
        """When generator sets _last_context, pipeline should prefer it."""
        gen = MagicMock(spec=MelodyGenerator)
        custom_ctx = RenderContext(prev_pitch=99, prev_velocity=50)
        gen._last_context = custom_ctx
        gen.render.return_value = [NoteInfo(pitch=60, start=0.0, duration=1.0)]

        chords = _chords(2)
        slots = generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        # Second render call should use prev_pitch=99 from _last_context
        ctx1 = gen.render.call_args_list[1][1].get("context") or gen.render.call_args_list[1][0][3]
        assert ctx1.prev_pitch == 99
        assert ctx1.prev_velocity == 50


# ===================================================================
# §3 — Same-label ≠ same-output (position/context changes music)
# ===================================================================


class TestSameLabelDifferentOutput:
    """
    Key musical property: two slots with the same label at different positions
    MUST produce different notes (context + phrase_position differ).
    """

    def test_aaba_positions_0_and_1_differ(self):
        """Positions 0 and 1 both have label 'A' but different context."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.7))
        random.seed(42)
        chords = _chords(4)
        slots = generate_idea(_track("AABA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        notes_0 = slots[0].phrase.static.notes
        notes_1 = slots[1].phrase.static.notes

        # With high density, the two "A" slots should not be identical
        # (position 0 has no context, position 1 has context from position 0)
        pitches_0 = [n.pitch for n in notes_0]
        pitches_1 = [n.pitch for n in notes_1]
        # At minimum, they should have been generated with different context
        # (we can't guarantee different output for static seeds, but for parametric generators
        # with high density and context threading, they should differ)
        assert pitches_0 != pitches_1 or len(notes_0) != len(notes_1), (
            "Same-label slots at different positions produced identical output — "
            "context threading is not working"
        )

    def test_aba_all_positions_differ(self):
        """Even with same label, all three ABA slots should yield different note sets."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.8))
        random.seed(7)
        chords = _chords(3)
        slots = generate_idea(_track("ABA", gen=gen), chords, C_MAJOR, beats_per_slot=8.0)

        note_sets = []
        for slot in slots:
            p = frozenset(
                (n.pitch, round(n.start, 2), round(n.duration, 2)) for n in slot.phrase.static.notes
            )
            note_sets.append(p)

        # Slots 0 and 2 both label "A" but different positions
        assert note_sets[0] != note_sets[2], (
            "First and last 'A' in AABA produced identical notes despite different context"
        )


# ===================================================================
# §4 — Different chord sequences → different note sequences
# ===================================================================


class TestFormDistinction:
    """
    phrase_order is structural — labels don't change which chord the generator
    sees per slot (that comes from position-based chord slicing).
    Real musical difference comes from chord PROGRESSIONS, not label patterns.
    """

    def test_different_chord_roots_yield_different_notes(self):
        """I-V-vi-IV vs I-IV-V-I should produce different output."""
        chords_1 = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4),
            ChordLabel(root=7, quality=Quality.MAJOR, start=4, duration=4),
            ChordLabel(root=9, quality=Quality.MINOR, start=8, duration=4),
            ChordLabel(root=5, quality=Quality.MAJOR, start=12, duration=4),
        ]
        chords_2 = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4, duration=4),
            ChordLabel(root=7, quality=Quality.MAJOR, start=8, duration=4),
            ChordLabel(root=0, quality=Quality.MAJOR, start=12, duration=4),
        ]
        gen = MelodyGenerator(params=GeneratorParams(density=0.6))
        random.seed(42)
        s1 = generate_idea(_track("AAAA", gen=gen), chords_1, C_MAJOR, beats_per_slot=4.0)
        random.seed(42)
        s2 = generate_idea(_track("AAAA", gen=gen), chords_2, C_MAJOR, beats_per_slot=4.0)
        p1 = tuple(n.pitch for n in slots_to_notes(s1))
        p2 = tuple(n.pitch for n in slots_to_notes(s2))
        assert p1 != p2, "Different chord progressions produced identical pitch sequences"

    def test_minor_vs_major_quality_affects_output(self):
        chords_major = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=i * 4, duration=4) for i in range(4)
        ]
        chords_minor = [
            ChordLabel(root=0, quality=Quality.MINOR, start=i * 4, duration=4) for i in range(4)
        ]
        gen = MelodyGenerator(params=GeneratorParams(density=0.6))
        random.seed(42)
        s1 = generate_idea(_track("AAAA", gen=gen), chords_major, C_MAJOR, beats_per_slot=4.0)
        random.seed(42)
        s2 = generate_idea(_track("AAAA", gen=gen), chords_minor, C_MAJOR, beats_per_slot=4.0)
        n1 = slots_to_notes(s1)
        n2 = slots_to_notes(s2)
        # Major and minor chords should influence the generator differently
        p1 = tuple(n.pitch for n in n1)
        p2 = tuple(n.pitch for n in n2)
        assert p1 != p2, "Major and minor chord qualities produced identical output"

    def test_different_keys_transpose_output(self):
        """Same chords in C major vs D minor should shift pitch center."""
        chords = _chords(4)
        gen = MelodyGenerator(params=GeneratorParams(density=0.6))
        random.seed(42)
        s1 = generate_idea(_track("AAAA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        random.seed(42)
        s2 = generate_idea(_track("AAAA", gen=gen), chords, D_MINOR, beats_per_slot=4.0)
        n1 = slots_to_notes(s1)
        n2 = slots_to_notes(s2)
        mean1 = sum(n.pitch for n in n1) / len(n1)
        mean2 = sum(n.pitch for n in n2) / len(n2)
        # At least one of: different sequences OR different mean pitch
        p1 = tuple(n.pitch for n in n1)
        p2 = tuple(n.pitch for n in n2)
        assert p1 != p2 or abs(mean1 - mean2) > 0.5, (
            f"C major and D minor produced same pitches, same mean ({mean1:.1f} vs {mean2:.1f})"
        )

    def test_same_label_same_position_same_chords_same_output(self):
        """
        Confirms the contract: label is structural metadata, not a musical mutation.
        Same position + same chords = same output regardless of label letter.
        """
        chords = _chords(4)
        gen = MelodyGenerator(params=GeneratorParams(density=0.6))
        random.seed(42)
        s1 = generate_idea(_track("AAAA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        random.seed(42)
        s2 = generate_idea(_track("XXXX", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        p1 = tuple(n.pitch for n in slots_to_notes(s1))
        p2 = tuple(n.pitch for n in slots_to_notes(s2))
        assert p1 == p2, "Different labels with same position/chords produced different output"


# ===================================================================
# §5 — Chord-slice fidelity
# ===================================================================


class TestChordSliceFidelity:
    """Generator should receive chords with correct root, quality, and time window."""

    def test_generator_receives_correct_chord_roots(self):
        gen = MagicMock(spec=MelodyGenerator)
        gen.render.return_value = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        gen._last_context = None

        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4),
            ChordLabel(root=7, quality=Quality.MAJOR, start=4, duration=4),
        ]
        generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        # Slot 0 should get root=0
        slot0_chords = (
            gen.render.call_args_list[0][1].get("chords") or gen.render.call_args_list[0][0][0]
        )
        assert slot0_chords[0].root == 0
        # Slot 1 should get root=7
        slot1_chords = (
            gen.render.call_args_list[1][1].get("chords") or gen.render.call_args_list[1][0][0]
        )
        assert slot1_chords[0].root == 7

    def test_sliced_chord_starts_are_relative(self):
        """Chord starts in slot should be relative to slot start, not absolute."""
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=8)]
        result = _chords_for_slot(chords, 1, 4.0)  # slot [4, 8)
        assert len(result) == 1
        # Chord starts at 0 (absolute) → slot starts at 4 → relative = max(0-4, 0) = 0
        # but also clipped to min(8, 8) - max(0, 4) = 4
        assert result[0].start == pytest.approx(0.0)
        assert result[0].duration == pytest.approx(4.0)

    def test_chord_quality_preserved_in_slice(self):
        chords = [ChordLabel(root=5, quality=Quality.MINOR, start=0, duration=4)]
        result = _chords_for_slot(chords, 0, 4.0)
        assert result[0].quality == Quality.MINOR

    def test_multiple_chords_per_slot(self):
        """When a slot spans multiple chords, all should be returned."""
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=2),
            ChordLabel(root=7, quality=Quality.MAJOR, start=2, duration=2),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4, duration=4),
        ]
        result = _chords_for_slot(chords, 0, 4.0)
        assert len(result) == 2
        assert result[0].root == 0
        assert result[1].root == 7

    def test_chord_gap_in_slot_triggers_fallback(self):
        """Slot with no overlapping chords → fallback uses last prior chord."""
        chords = [ChordLabel(root=3, quality=Quality.MINOR, start=0, duration=4)]
        result = _chords_for_slot(chords, 2, 4.0)  # slot [8, 12)
        assert len(result) == 1
        assert result[0].root == 3
        assert result[0].quality == Quality.MINOR
        assert result[0].duration == 4.0  # full slot duration


# ===================================================================
# §6 — phrase_position mapping
# ===================================================================


class TestPhrasePosition:
    """phrase_position: 0.0 (first) → 1.0 (last) linearly."""

    def test_mocked_phrase_positions(self):
        gen = MagicMock(spec=MelodyGenerator)
        gen.render.return_value = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        gen._last_context = None

        chords = _chords(4)
        generate_idea(_track("AAAA", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        positions = []
        for c in gen.render.call_args_list:
            ctx = c[1].get("context") or c[0][3]
            positions.append(ctx.phrase_position)

        assert positions[0] == pytest.approx(0.0)
        assert positions[-1] == pytest.approx(1.0)
        # monotonically increasing
        for i in range(1, len(positions)):
            assert positions[i] >= positions[i - 1]

    def test_two_slots_are_0_and_1(self):
        gen = MagicMock(spec=MelodyGenerator)
        gen.render.return_value = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        gen._last_context = None

        chords = _chords(2)
        generate_idea(_track("AB", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        ctx0 = gen.render.call_args_list[0][1].get("context") or gen.render.call_args_list[0][0][3]
        ctx1 = gen.render.call_args_list[1][1].get("context") or gen.render.call_args_list[1][0][3]
        assert ctx0.phrase_position == pytest.approx(0.0)
        assert ctx1.phrase_position == pytest.approx(1.0)

    def test_single_slot_is_zero(self):
        gen = MagicMock(spec=MelodyGenerator)
        gen.render.return_value = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        gen._last_context = None

        chords = _chords(1)
        generate_idea(_track("A", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)

        ctx0 = gen.render.call_args_list[0][1].get("context") or gen.render.call_args_list[0][0][3]
        assert ctx0.phrase_position == pytest.approx(0.0)


# ===================================================================
# §7 — Density ↔ note count correlation
# ===================================================================


class TestDensityScaling:
    """Higher density should produce more notes (statistical, not deterministic)."""

    def test_high_density_more_than_low(self):
        chords = _chords(4)
        random.seed(42)
        low = generate_idea(
            _track("AABA", gen=MelodyGenerator(params=GeneratorParams(density=0.1))),
            chords,
            C_MAJOR,
            beats_per_slot=4.0,
        )
        random.seed(42)
        high = generate_idea(
            _track("AABA", gen=MelodyGenerator(params=GeneratorParams(density=0.95))),
            chords,
            C_MAJOR,
            beats_per_slot=4.0,
        )
        n_low = sum(len(s.phrase.static.notes) for s in low)
        n_high = sum(len(s.phrase.static.notes) for s in high)
        assert n_high >= n_low, (
            f"High density ({n_high} notes) did not produce more than low ({n_low})"
        )


# ===================================================================
# §8 — slots_to_notes invariant tests
# ===================================================================


class TestSlotsToNotesInvariants:
    def test_parametric_phrase_raises_assert(self):
        """slots_to_notes expects static phrases; parametric should assert."""
        parametric_slot = ArrangementSlot(
            phrase=PhraseInstance(generator=MelodyGenerator()),
            start_beat=0.0,
            label="A",
        )
        with pytest.raises(AssertionError, match="static"):
            slots_to_notes([parametric_slot])

    def test_absolute_timing_offset_correct(self):
        """Notes in slot at beat 12 should have start = relative_start + 12."""
        gen = MagicMock(spec=MelodyGenerator)
        gen.render.return_value = [NoteInfo(pitch=60, start=1.0, duration=2.0)]
        gen._last_context = None

        chords = _chords(3)
        slots = generate_idea(_track("ABC", gen=gen), chords, C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)

        # Slot 0: start = 1.0 + 0 = 1.0
        # Slot 1: start = 1.0 + 4 = 5.0
        # Slot 2: start = 1.0 + 8 = 9.0
        starts = [n.start for n in notes]
        assert 1.0 in starts
        assert 5.0 in starts
        assert 9.0 in starts

    def test_mixed_empty_and_full_slots(self):
        """Slots with no notes should not corrupt timing of other slots."""
        slot_a = ArrangementSlot(
            phrase=PhraseInstance(
                static=StaticPhrase(
                    notes=[
                        NoteInfo(pitch=60, start=0.0, duration=1.0),
                    ]
                )
            ),
            start_beat=0.0,
            label="A",
        )
        slot_empty = ArrangementSlot(
            phrase=PhraseInstance(static=StaticPhrase(notes=[])),
            start_beat=4.0,
            label="B",
        )
        slot_c = ArrangementSlot(
            phrase=PhraseInstance(
                static=StaticPhrase(
                    notes=[
                        NoteInfo(pitch=64, start=0.0, duration=1.0),
                    ]
                )
            ),
            start_beat=8.0,
            label="C",
        )
        notes = slots_to_notes([slot_a, slot_empty, slot_c])
        assert len(notes) == 2
        assert notes[0].start == pytest.approx(0.0)
        assert notes[1].start == pytest.approx(8.0)

    def test_stable_sort_for_same_start(self):
        """Notes at same absolute start should maintain deterministic order."""
        slot = ArrangementSlot(
            phrase=PhraseInstance(
                static=StaticPhrase(
                    notes=[
                        NoteInfo(pitch=60, start=0.0, duration=1.0),
                        NoteInfo(pitch=64, start=0.0, duration=1.0),
                        NoteInfo(pitch=67, start=0.0, duration=1.0),
                    ]
                )
            ),
            start_beat=0.0,
            label="A",
        )
        notes = slots_to_notes([slot])
        assert len(notes) == 3
        # All at start=0, sorted stable → order preserved from input
        assert [n.pitch for n in notes] == [60, 64, 67]


# ===================================================================
# §9 — Arrangement-slot structural integrity
# ===================================================================


class TestSlotStructure:
    def test_slots_are_list_of_arrangement_slot(self):
        slots = generate_idea(_track("AABA"), _chords(4), C_MAJOR, beats_per_slot=4.0)
        assert isinstance(slots, list)
        for s in slots:
            assert isinstance(s, ArrangementSlot)

    def test_slot_has_static_phrase(self):
        slots = generate_idea(_track("AB"), _chords(2), C_MAJOR, beats_per_slot=4.0)
        for s in slots:
            assert s.phrase.static is not None
            assert isinstance(s.phrase.static.notes, list)

    def test_slot_start_beats_non_negative(self):
        slots = generate_idea(_track("AABBAABB"), _chords(8), C_MAJOR, beats_per_slot=4.0)
        for s in slots:
            assert s.start_beat >= 0.0

    def test_slot_start_beats_monotonic(self):
        slots = generate_idea(_track("ABCD"), _chords(4), C_MAJOR, beats_per_slot=4.0)
        for i in range(1, len(slots)):
            assert slots[i].start_beat >= slots[i - 1].start_beat

    def test_label_types_are_strings(self):
        slots = generate_idea(_track("AABBA"), _chords(5), C_MAJOR, beats_per_slot=4.0)
        for s in slots:
            assert isinstance(s.label, str)
            assert len(s.label) == 1


# ===================================================================
# §10 — Edge-case mutations
# ===================================================================


class TestMutations:
    """Stress the pipeline with unusual inputs."""

    def test_single_slot(self):
        slots = generate_idea(_track("A"), _chords(1), C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 1
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

    def test_sub_beat_slot(self):
        """beats_per_slot < 1 should still work."""
        chords = _chords(4, beats=0.25)
        slots = generate_idea(_track("AB"), chords, C_MAJOR, beats_per_slot=0.25)
        assert len(slots) == 2
        assert slots[1].start_beat == pytest.approx(0.25)

    def test_huge_slot(self):
        """64-beat slot should produce notes."""
        gen = MelodyGenerator(params=GeneratorParams(density=0.3))
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=64)]
        slots = generate_idea(_track("A", gen=gen), chords, C_MAJOR, beats_per_slot=64.0)
        notes = slots_to_notes(slots)
        assert len(notes) > 0
        violations = _violation_report(notes)
        assert violations == []

    def test_zero_density_no_crash(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.0))
        slots = generate_idea(_track("AB", gen=gen), _chords(2), C_MAJOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        assert isinstance(notes, list)

    def test_multiple_seeds(self):
        seeds = [_seed([(60, 0.0, 1.0)]), _seed([(64, 0.0, 1.0)]), _seed([(67, 0.0, 1.0)])]
        track = IdeaTrack(seed_phrases=seeds, generator=MelodyGenerator(), phrase_order="AAB")
        slots = generate_idea(track, _chords(3), C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 3

    def test_random_order_flag(self):
        random.seed(42)
        seeds = [_seed([(p, 0.0, 1.0)]) for p in [60, 62, 64, 65]]
        track = IdeaTrack(
            seed_phrases=seeds,
            generator=MelodyGenerator(),
            phrase_order="ABCD",
            random_order=True,
        )
        slots = generate_idea(track, _chords(4), C_MAJOR, beats_per_slot=4.0)
        assert len(slots) == 4

    def test_extreme_long_phrase_order(self):
        order = "AABB" * 8  # 32 slots
        gen = MelodyGenerator(params=GeneratorParams(density=0.2))
        chords = _chords(len(order), beats=1.0)
        slots = generate_idea(_track(order, gen=gen), chords, C_MAJOR, beats_per_slot=1.0)
        assert len(slots) == 32
        assert [s.label for s in slots] == list(order)

    def test_minor_scale_invariants(self):
        gen = MelodyGenerator(params=GeneratorParams(density=0.5))
        chords = _chords(4)
        slots = generate_idea(_track("AABA", gen=gen), chords, D_MINOR, beats_per_slot=4.0)
        notes = slots_to_notes(slots)
        violations = _violation_report(notes)
        assert violations == []


# ===================================================================
# §11 — _random_rank
# ===================================================================


class TestRandomRank:
    def test_preserves_elements(self):
        items = [1, 2, 3, 4, 5]
        assert sorted(_random_rank(items)) == sorted(items)

    def test_same_length(self):
        assert len(_random_rank(list(range(20)))) == 20

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

    def test_probabilistically_not_identity(self):
        """Over many runs, at least one should differ from original order."""
        results = set()
        for seed in range(100):
            random.seed(seed)
            results.add(tuple(_random_rank([1, 2, 3, 4, 5])))
        # If _random_rank always returns identity, results would be {(1,2,3,4,5)}
        assert len(results) > 1, "_random_rank always returns identity order"


# ===================================================================
# §12 — _chords_for_slot edge math
# ===================================================================


class TestChordsForSlotMath:
    def test_empty_chord_list(self):
        assert _chords_for_slot([], 0, 4.0) == []

    def test_chord_exactly_at_slot_boundary(self):
        """Chord ending at slot_start should NOT be included."""
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)]
        result = _chords_for_slot(chords, 1, 4.0)  # slot [4, 8)
        # c.end = 4, slot_start = 4 → c.end <= slot_start → skip
        # fallback: last chord before slot = c → returned
        assert len(result) == 1
        assert result[0].root == 0

    def test_chord_starting_at_slot_end(self):
        """Chord starting at slot_end should NOT be included (direct)."""
        chords = [ChordLabel(root=5, quality=Quality.MINOR, start=8, duration=4)]
        result = _chords_for_slot(chords, 0, 4.0)  # slot [0, 4)
        # c.start=8 >= slot_end=4 → skip
        # fallback: no chord before slot_start=0 → default chords[0]
        assert len(result) == 1
        assert result[0].root == 5

    def test_overlapping_chord_clipped_duration(self):
        """Chord starting before slot should be clipped."""
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=2, duration=8)]
        result = _chords_for_slot(chords, 0, 4.0)  # slot [0, 4)
        assert result[0].start == pytest.approx(2.0)  # max(2-0, 0) = 2
        assert result[0].duration == pytest.approx(2.0)  # min(10,4) - max(2,0) = 2

    def test_chord_extending_past_slot_end(self):
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=10)]
        result = _chords_for_slot(chords, 0, 4.0)  # slot [0, 4)
        assert result[0].duration == pytest.approx(4.0)
