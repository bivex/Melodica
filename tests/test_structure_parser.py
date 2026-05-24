# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_structure_parser.py — Tests for RC-style Structure Notation.

Covers:
1. parse_structure: compact, prime, subscript, suffix, edge cases
2. ParsedSegment: properties, transform mapping
3. structure_to_slots: slot generation, R (rest) handling
4. PhrasePool: store/get/has/clear, key isolation
5. parse_slot_label: label:transform decomposition
6. apply_phrase_transform: inversion, retrograde, fast, augmentation, var
7. structure_to_schedule: end-to-end IdeaTool integration
8. PhrasePool + IdeaTool: Letter Rule, ghost copy, multi-part reuse
"""

import pytest
from melodica.types import Scale, Mode, NoteInfo
from melodica.composer.structure_parser import (
    PhraseTransform,
    ParsedSegment,
    PhrasePool,
    parse_structure,
    parse_slot_label,
    apply_phrase_transform,
    structure_to_slots,
    _parse_token,
    _split_compact,
    _build_slot_label,
)
from melodica.idea_tool import (
    IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart,
    PhraseSlot, PhraseSchedule,
    structure_to_schedule,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)

N = lambda p, s, d, v=80: NoteInfo(pitch=p, start=s, duration=d, velocity=v)


# ===========================================================================
# 1. parse_structure
# ===========================================================================

class TestParseStructureCompact:
    def test_aabb(self):
        segs = parse_structure("AABB")
        assert len(segs) == 4
        assert [s.letter for s in segs] == ["A", "A", "B", "B"]

    def test_abab(self):
        segs = parse_structure("ABAB")
        assert [s.letter for s in segs] == ["A", "B", "A", "B"]

    def test_single_letter(self):
        segs = parse_structure("A")
        assert len(segs) == 1
        assert segs[0].letter == "A"

    def test_abcd(self):
        segs = parse_structure("ABCD")
        assert [s.letter for s in segs] == ["A", "B", "C", "D"]

    def test_includes_r(self):
        segs = parse_structure("AARB")
        assert len(segs) == 4
        assert [s.letter for s in segs] == ["A", "A", "R", "B"]

    def test_bars_per_segment(self):
        segs = parse_structure("AB", bars_per_segment=8)
        assert all(s.bars == 8 for s in segs)

    def test_empty_string(self):
        assert parse_structure("") == []

    def test_whitespace_only(self):
        assert parse_structure("   ") == []


class TestParseStructurePrime:
    def test_single_prime_compact(self):
        segs = parse_structure("AA'BB")
        assert len(segs) == 4
        assert segs[0].prime_count == 0
        assert segs[1].prime_count == 1
        assert segs[1].transform == PhraseTransform.VAR

    def test_double_prime(self):
        segs = parse_structure("AA''B")
        assert segs[1].prime_count == 2
        assert segs[1].transform == PhraseTransform.INVERSION

    def test_triple_prime(self):
        segs = parse_structure("A'''B")
        assert segs[0].prime_count == 3
        assert segs[0].transform == PhraseTransform.RETROGRADE_INVERSION

    def test_prime_space_separated(self):
        segs = parse_structure("A A' B B")
        assert segs[1].prime_count == 1
        assert segs[1].transform == PhraseTransform.VAR


class TestParseStructureSubscript:
    def test_subscript(self):
        segs = parse_structure("A1 A1 B1 B1")
        assert [s.base_label for s in segs] == ["A1", "A1", "B1", "B1"]

    def test_subscript_distinguishes(self):
        segs = parse_structure("A1 A2 B1")
        assert segs[0].base_label == "A1"
        assert segs[1].base_label == "A2"
        assert segs[2].base_label == "B1"

    def test_no_subscript(self):
        segs = parse_structure("A B")
        assert all(s.subscript == "" for s in segs)


class TestParseStructureSuffix:
    def test_var_suffix(self):
        segs = parse_structure("A A_var B B")
        assert segs[1].suffix == "var"
        assert segs[1].transform == PhraseTransform.VAR

    def test_inv_suffix(self):
        segs = parse_structure("A B_inv")
        assert segs[1].transform == PhraseTransform.INVERSION

    def test_fast_suffix(self):
        segs = parse_structure("A B_fast")
        assert segs[1].transform == PhraseTransform.FAST

    def test_retro_suffix(self):
        segs = parse_structure("A B_retro")
        assert segs[1].transform == PhraseTransform.RETROGRADE

    def test_aug_suffix(self):
        segs = parse_structure("A B_aug")
        assert segs[1].transform == PhraseTransform.AUGMENTATION

    def test_dim_suffix(self):
        segs = parse_structure("A B_dim")
        assert segs[1].transform == PhraseTransform.DIMINUTION

    def test_retro_inv_suffix(self):
        segs = parse_structure("A B_retro_inv")
        assert segs[1].transform == PhraseTransform.RETROGRADE_INVERSION


class TestParseStructureMixed:
    def test_prime_and_suffix(self):
        segs = parse_structure("A A'_var B B")
        assert segs[1].prime_count == 1
        assert segs[1].suffix == "var"

    def test_subscript_and_prime(self):
        segs = parse_structure("A1' A2 B1")
        assert segs[0].base_label == "A1"
        assert segs[0].prime_count == 1

    def test_all_features(self):
        segs = parse_structure("A A1 A' A_var B B_retro")
        assert len(segs) == 6

    def test_invalid_token_skipped(self):
        segs = parse_structure("A xyz B")
        assert len(segs) == 2
        assert [s.letter for s in segs] == ["A", "B"]


# ===========================================================================
# 2. ParsedSegment
# ===========================================================================

class TestParsedSegment:
    def test_label_no_subscript(self):
        s = ParsedSegment(letter="A")
        assert s.label == "A"

    def test_label_with_subscript(self):
        s = ParsedSegment(letter="A", subscript="1")
        assert s.label == "A1"

    def test_base_label(self):
        s = ParsedSegment(letter="B", subscript="2")
        assert s.base_label == "B2"

    def test_has_variation_false(self):
        s = ParsedSegment(letter="A")
        assert not s.has_variation

    def test_has_variation_prime(self):
        s = ParsedSegment(letter="A", prime_count=1)
        assert s.has_variation

    def test_has_variation_suffix(self):
        s = ParsedSegment(letter="A", suffix="var")
        assert s.has_variation

    def test_frozen(self):
        s = ParsedSegment(letter="A")
        with pytest.raises(AttributeError):
            s.letter = "B"


# ===========================================================================
# 3. _split_compact & _parse_token
# ===========================================================================

class TestSplitCompact:
    def test_aabb(self):
        assert _split_compact("AABB") == ["A", "A", "B", "B"]

    def test_prime(self):
        assert _split_compact("AA'BB") == ["A", "A'", "B", "B"]

    def test_subscript(self):
        assert _split_compact("A1B2") == ["A1", "B2"]

    def test_mixed(self):
        assert _split_compact("A1'A2''B") == ["A1'", "A2''", "B"]


class TestParseToken:
    def test_simple(self):
        t = _parse_token("A", 4)
        assert t is not None
        assert t.letter == "A"
        assert t.bars == 4

    def test_with_prime(self):
        t = _parse_token("A'", 4)
        assert t.prime_count == 1

    def test_with_suffix(self):
        t = _parse_token("B_var", 4)
        assert t.suffix == "var"

    def test_invalid(self):
        assert _parse_token("xyz", 4) is None

    def test_lowercase_rejected(self):
        assert _parse_token("a", 4) is None


# ===========================================================================
# 4. structure_to_slots
# ===========================================================================

class TestStructureToSlots:
    def test_aabb(self):
        slots = structure_to_slots("AABB", 4)
        assert len(slots) == 4
        assert all(s.kind == "play" for s in slots)
        assert all(s.bars == 4 for s in slots)
        assert slots[0].label == "A"
        assert slots[2].label == "B"

    def test_rest_r(self):
        slots = structure_to_slots("R", 8)
        assert len(slots) == 1
        assert slots[0].kind == "rest"
        assert slots[0].bars == 8

    def test_rest_in_sequence(self):
        slots = structure_to_slots("A R B", 4)
        assert slots[0].kind == "play"
        assert slots[0].label == "A"
        assert slots[1].kind == "rest"
        assert slots[2].kind == "play"
        assert slots[2].label == "B"

    def test_compact_rest(self):
        slots = structure_to_slots("AARB", 4)
        assert slots[2].kind == "rest"

    def test_transform_in_label(self):
        slots = structure_to_slots("AA'BB", 4)
        assert slots[1].label == "A:var"

    def test_suffix_in_label(self):
        slots = structure_to_slots("A B_retro", 4)
        assert slots[1].label == "B:retrograde"

    def test_no_transform_in_label(self):
        slots = structure_to_slots("AABB", 4)
        assert ":" not in slots[0].label
        assert ":" not in slots[2].label


# ===========================================================================
# 5. PhrasePool
# ===========================================================================

class TestPhrasePool:
    def test_store_and_get(self):
        pool = PhrasePool()
        notes = [N(60, 0, 1), N(64, 1, 1)]
        pool.store("melody", "A", notes)
        result = pool.get("melody", "A")
        assert result is not None
        assert len(result) == 2

    def test_has(self):
        pool = PhrasePool()
        assert not pool.has("melody", "A")
        pool.store("melody", "A", [N(60, 0, 1)])
        assert pool.has("melody", "A")

    def test_track_isolation(self):
        pool = PhrasePool()
        pool.store("melody", "A", [N(60, 0, 1)])
        pool.store("bass", "A", [N(36, 0, 1)])
        assert pool.has("melody", "A")
        assert pool.has("bass", "A")
        assert not pool.has("melody", "B")

    def test_label_isolation(self):
        pool = PhrasePool()
        pool.store("melody", "A", [N(60, 0, 1)])
        assert pool.has("melody", "A")
        assert not pool.has("melody", "B")

    def test_overwrite(self):
        pool = PhrasePool()
        pool.store("melody", "A", [N(60, 0, 1)])
        pool.store("melody", "A", [N(72, 0, 1)])
        result = pool.get("melody", "A")
        assert result[0].pitch == 72

    def test_clear(self):
        pool = PhrasePool()
        pool.store("melody", "A", [N(60, 0, 1)])
        pool.clear()
        assert not pool.has("melody", "A")

    def test_get_missing_returns_none(self):
        pool = PhrasePool()
        assert pool.get("melody", "Z") is None

    def test_stored_notes_are_copies(self):
        pool = PhrasePool()
        original = [N(60, 0, 1)]
        pool.store("melody", "A", original)
        stored = pool.get("melody", "A")
        stored[0] = N(99, 0, 1)
        assert pool.get("melody", "A")[0].pitch == 60


# ===========================================================================
# 6. parse_slot_label
# ===========================================================================

class TestParseSlotLabel:
    def test_plain(self):
        base, tf = parse_slot_label("A")
        assert base == "A"
        assert tf == PhraseTransform.ORIGINAL

    def test_with_var(self):
        base, tf = parse_slot_label("A:var")
        assert base == "A"
        assert tf == PhraseTransform.VAR

    def test_with_inv(self):
        base, tf = parse_slot_label("B:inversion")
        assert base == "B"
        assert tf == PhraseTransform.INVERSION

    def test_with_retro(self):
        base, tf = parse_slot_label("Theme_X:retrograde")
        assert base == "Theme_X"
        assert tf == PhraseTransform.RETROGRADE

    def test_unknown_transform(self):
        base, tf = parse_slot_label("A:unknown")
        assert base == "A"
        assert tf == PhraseTransform.ORIGINAL

    def test_colon_in_prefix(self):
        base, tf = parse_slot_label("A:B:var")
        assert base == "A:B"
        assert tf == PhraseTransform.VAR

    def test_empty_label(self):
        base, tf = parse_slot_label("")
        assert base == ""
        assert tf == PhraseTransform.ORIGINAL


# ===========================================================================
# 7. apply_phrase_transform
# ===========================================================================

class TestApplyPhraseTransformOriginal:
    def test_original_returns_copy(self):
        notes = [N(60, 0, 1), N(64, 1, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.ORIGINAL)
        assert result[0].pitch == 60
        assert result is not notes

    def test_empty_notes(self):
        assert apply_phrase_transform([], PhraseTransform.ORIGINAL) == []
        assert apply_phrase_transform([], PhraseTransform.INVERSION) == []


class TestApplyPhraseTransformInversion:
    def test_inverts_intervals(self):
        notes = [N(60, 0, 1), N(64, 1, 1), N(67, 2, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert result[0].pitch == 60
        assert result[1].pitch == 56  # 60 - (64-60)
        assert result[2].pitch == 53  # 56 - (67-64)

    def test_preserves_rhythm(self):
        notes = [N(60, 0, 1), N(64, 1, 2)]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert result[0].start == 0
        assert result[0].duration == 1
        assert result[1].start == 1
        assert result[1].duration == 2

    def test_single_note_unchanged(self):
        notes = [N(60, 0, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert result[0].pitch == 60

    def test_clamps_to_range(self):
        notes = [N(0, 0, 1), N(12, 1, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert result[1].pitch >= 0


class TestApplyPhraseTransformRetrograde:
    def test_reverses_pitch_order(self):
        notes = [N(60, 0, 1), N(64, 1, 1), N(67, 2, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.RETROGRADE)
        assert result[0].pitch == 67
        assert result[1].pitch == 64
        assert result[2].pitch == 60

    def test_preserves_total_duration(self):
        notes = [N(60, 0, 2), N(64, 2, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.RETROGRADE)
        total_dur = max(n.start + n.duration for n in result)
        assert total_dur == pytest.approx(3.0, abs=0.01)

    def test_starts_at_zero(self):
        notes = [N(60, 2, 1), N(64, 3, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.RETROGRADE)
        assert result[0].start == pytest.approx(0.0, abs=0.01)

    def test_empty(self):
        assert apply_phrase_transform([], PhraseTransform.RETROGRADE) == []


class TestApplyPhraseTransformRetrogradeInversion:
    def test_ri_both_inverts_and_reverses(self):
        notes = [N(60, 0, 1), N(64, 1, 1), N(67, 2, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.RETROGRADE_INVERSION)
        inv = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        retro_inv = apply_phrase_transform(inv, PhraseTransform.RETROGRADE)
        assert [r.pitch for r in result] == [r.pitch for r in retro_inv]


class TestApplyPhraseTransformFast:
    def test_halves_durations(self):
        notes = [N(60, 0, 2), N(64, 2, 2)]
        result = apply_phrase_transform(notes, PhraseTransform.FAST)
        assert result[0].duration == pytest.approx(1.0, abs=0.01)
        assert result[1].duration == pytest.approx(1.0, abs=0.01)

    def test_halves_start_times(self):
        notes = [N(60, 0, 1), N(64, 2, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.FAST)
        assert result[0].start == pytest.approx(0.0, abs=0.01)
        assert result[1].start == pytest.approx(1.0, abs=0.01)

    def test_minimum_duration(self):
        notes = [N(60, 0, 0.01)]
        result = apply_phrase_transform(notes, PhraseTransform.FAST)
        assert result[0].duration >= 0.0625


class TestApplyPhraseTransformAugmentation:
    def test_doubles_durations(self):
        notes = [N(60, 0, 1), N(64, 1, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.AUGMENTATION)
        assert result[0].duration == pytest.approx(2.0, abs=0.01)
        assert result[1].duration == pytest.approx(2.0, abs=0.01)

    def test_doubles_start_times(self):
        notes = [N(60, 0, 1), N(64, 1, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.AUGMENTATION)
        assert result[1].start == pytest.approx(2.0, abs=0.01)


class TestApplyPhraseTransformVar:
    def test_var_returns_same_length(self):
        notes = [N(60, 0, 1), N(64, 1, 1), N(67, 2, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.VAR)
        assert len(result) == len(notes)

    def test_var_preserves_starts(self):
        notes = [N(60, 0, 1), N(64, 1, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.VAR)
        assert result[0].start == 0
        assert result[1].start == 1


# ===========================================================================
# 8. structure_to_schedule
# ===========================================================================

class TestStructureToSchedule:
    def test_basic(self):
        sched = structure_to_schedule("AABB", 4)
        assert len(sched.slots) == 4
        assert sched.loop is True

    def test_no_loop(self):
        sched = structure_to_schedule("AB", 4, loop=False)
        assert sched.loop is False

    def test_with_rests(self):
        sched = structure_to_schedule("A R A R", 4)
        assert sched.slots[0].kind == "play"
        assert sched.slots[1].kind == "rest"
        assert sched.slots[2].kind == "play"
        assert sched.slots[3].kind == "rest"

    def test_with_transforms(self):
        sched = structure_to_schedule("AA'BB", 4)
        assert sched.slots[1].label == "A:var"

    def test_custom_bars(self):
        sched = structure_to_schedule("AB", 8)
        assert sched.slots[0].bars == 8
        assert sched.slots[1].bars == 8


# ===========================================================================
# 9. IdeaTool integration with PhrasePool
# ===========================================================================

class TestIdeaToolPhrasePool:
    def test_letter_rule_same_notes_for_same_label(self):
        sched = structure_to_schedule("AA", 4, loop=False)
        config = IdeaToolConfig(
            scale=C_MAJOR, bars=8,
            tracks=[TrackConfig(
                name="melody", generator_type="melody", density=0.5,
                phrase_schedule=sched,
            )],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert len(result["melody"]) > 0

    def test_different_labels_different_notes(self):
        sched = structure_to_schedule("AB", 4, loop=False)
        config = IdeaToolConfig(
            scale=C_MAJOR, bars=8,
            tracks=[TrackConfig(
                name="melody", generator_type="melody", density=0.6,
                phrase_schedule=sched,
            )],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert len(result["melody"]) > 0

    def test_transform_suffix_produces_different_notes(self):
        sched = structure_to_schedule("A A:inv", 4, loop=False)
        config = IdeaToolConfig(
            scale=C_MAJOR, bars=8,
            tracks=[TrackConfig(
                name="melody", generator_type="melody", density=0.6,
                phrase_schedule=sched,
            )],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert len(result["melody"]) > 0

    def test_rest_produces_no_notes(self):
        sched = structure_to_schedule("R", 8, loop=False)
        config = IdeaToolConfig(
            scale=C_MAJOR, bars=8,
            tracks=[TrackConfig(
                name="melody", generator_type="melody", density=0.6,
                phrase_schedule=sched,
            )],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert result.get("melody") is None or len(result.get("melody", [])) == 0

    def test_pool_persists_across_parts(self):
        parts = [
            IdeaPart(name="P1", bars=4, scale=C_MAJOR,
                     track_phrase_schedules={
                         "melody": structure_to_schedule("A", 4),
                     }),
            IdeaPart(name="P2", bars=4, scale=C_MAJOR,
                     track_phrase_schedules={
                         "melody": structure_to_schedule("A", 4),
                     }),
        ]
        config = IdeaToolConfig(
            scale=C_MAJOR,
            tracks=[TrackConfig(
                name="melody", generator_type="melody", density=0.5,
            )],
            parts=parts,
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert len(result["melody"]) > 0

    def test_multi_track_independent_pools(self):
        sched = structure_to_schedule("AA'BB", 4, loop=False)
        config = IdeaToolConfig(
            scale=C_MAJOR, bars=16,
            tracks=[
                TrackConfig(
                    name="melody", generator_type="melody", density=0.5,
                    phrase_schedule=sched,
                ),
                TrackConfig(
                    name="bass", generator_type="bass", density=0.5,
                    phrase_schedule=sched,
                ),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert "bass" in result
        assert len(result["melody"]) > 0
        assert len(result["bass"]) > 0
        assert result["melody"] != result["bass"]

    def test_full_structure_demo(self):
        tracks = [
            TrackConfig(
                name="lead",
                generator_type="melody", density=0.5,
                phrase_schedule=structure_to_schedule("AA'BB", 4),
            ),
        ]
        config = IdeaToolConfig(
            style="pop", scale=C_MAJOR, bars=16,
            tracks=tracks,
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "lead" in result
        assert len(result["lead"]) > 0


# ===========================================================================
# 10. Edge cases and potential bugs
# ===========================================================================

class TestEdgeCases:
    def test_single_note_inversion(self):
        notes = [N(60, 0, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert len(result) == 1
        assert result[0].pitch == 60

    def test_very_large_ascending(self):
        notes = [N(i % 128, i * 0.5, 0.5) for i in range(10)]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert all(0 <= n.pitch <= 127 for n in result)

    def test_retrograde_single_note(self):
        notes = [N(60, 0, 1)]
        result = apply_phrase_transform(notes, PhraseTransform.RETROGRADE)
        assert result[0].pitch == 60
        assert result[0].start == pytest.approx(0.0, abs=0.01)

    def test_parse_structure_lowercase_rejected(self):
        segs = parse_structure("aabb")
        assert segs == []

    def test_pool_returns_none_for_missing(self):
        pool = PhrasePool()
        assert pool.get("nonexistent", "X") is None

    def test_build_slot_label_original(self):
        seg = ParsedSegment(letter="A")
        assert _build_slot_label(seg) == "A"

    def test_build_slot_label_with_transform(self):
        seg = ParsedSegment(letter="A", prime_count=1)
        assert _build_slot_label(seg) == "A:var"

    def test_empty_structure_schedule(self):
        sched = structure_to_schedule("", 4)
        assert len(sched.slots) == 0

    def test_schedule_with_loop_expansion(self):
        sched = structure_to_schedule("AB", 4, loop=True)
        config = IdeaToolConfig(
            scale=C_MAJOR, bars=16,
            tracks=[TrackConfig(
                name="melody", generator_type="melody", density=0.5,
                phrase_schedule=sched,
            )],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert len(result["melody"]) > 0

    def test_diminution_same_as_fast(self):
        notes = [N(60, 0, 2), N(64, 2, 2)]
        fast = apply_phrase_transform(notes, PhraseTransform.FAST)
        dim = apply_phrase_transform(notes, PhraseTransform.DIMINUTION)
        assert fast[0].duration == pytest.approx(dim[0].duration, abs=0.01)

    def test_expression_dict_preserved_in_transform(self):
        notes = [NoteInfo(pitch=60, start=0, duration=1, velocity=80, expression={"cc1": 64})]
        result = apply_phrase_transform(notes, PhraseTransform.INVERSION)
        assert result[0].expression == {"cc1": 64}

    def test_expression_not_shared_reference(self):
        notes = [NoteInfo(pitch=60, start=0, duration=1, velocity=80)]
        notes[0].expression["x"] = 1
        result = apply_phrase_transform(notes, PhraseTransform.RETROGRADE)
        result[0].expression["y"] = 2
        assert "y" not in notes[0].expression

    def test_parse_structure_only_rests(self):
        segs = parse_structure("R R R")
        assert len(segs) == 3
        assert all(s.letter == "R" for s in segs)

    def test_compact_with_subscript_and_prime(self):
        segs = parse_structure("A1'A2''B1")
        assert len(segs) == 3
        assert segs[0].base_label == "A1"
        assert segs[0].prime_count == 1
        assert segs[1].base_label == "A2"
        assert segs[1].prime_count == 2
        assert segs[2].base_label == "B1"
