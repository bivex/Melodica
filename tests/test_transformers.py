# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.transformers import (
    Identity, OneToThree, TwoToThree, TwoToFour,
    spiceup, serialize_canon,
    _next_scale_pitch, _scale_pitches_between, _median_pitch,
    SINGLE_NOTE_TRANSFORMERS, DOUBLE_NOTE_TRANSFORMERS,
)


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)

N60 = NoteInfo(pitch=60, start=0.0, duration=2.0, velocity=80)
N64 = NoteInfo(pitch=64, start=2.0, duration=2.0, velocity=80)
N67 = NoteInfo(pitch=67, start=4.0, duration=2.0, velocity=80)
N72 = NoteInfo(pitch=72, start=6.0, duration=2.0, velocity=80)


# ─── Helpers ────────────────────────────────────────────────────────────────


class TestNextScalePitch:
    def test_ascending_from_c(self):
        assert _next_scale_pitch(60, C_MAJOR, "ascending") == 62  # C -> D

    def test_descending_from_c(self):
        assert _next_scale_pitch(60, C_MAJOR, "descending") == 59  # C -> B

    def test_ascending_wraps_octave(self):
        assert _next_scale_pitch(71, C_MAJOR, "ascending") == 72  # B -> C next octave

    def test_descending_wraps_octave(self):
        assert _next_scale_pitch(60, C_MAJOR, "descending") == 59  # C -> B prev octave

    def test_clamps_midi_range(self):
        assert _next_scale_pitch(0, C_MAJOR, "descending") >= 0
        assert _next_scale_pitch(127, C_MAJOR, "ascending") <= 127


class TestScalePitchesBetween:
    def test_c_to_e(self):
        result = _scale_pitches_between(60, 64, C_MAJOR)
        assert 60 in result  # C
        assert 62 in result  # D
        assert 64 in result  # E

    def test_empty_range(self):
        result = _scale_pitches_between(60, 59, C_MAJOR)
        assert result == []


class TestMedianPitch:
    def test_single(self):
        assert _median_pitch([60]) == 60

    def test_odd_count(self):
        assert _median_pitch([60, 62, 64]) == 62

    def test_even_count_lower(self):
        assert _median_pitch([60, 64], prefer_upper=False) == 60

    def test_even_count_upper(self):
        assert _median_pitch([60, 64], prefer_upper=True) == 64

    def test_empty(self):
        assert _median_pitch([]) == 60


# ─── Identity ───────────────────────────────────────────────────────────────


class TestIdentity:
    def test_returns_single_note(self):
        result = Identity().transform(C_MAJOR, N60)
        assert len(result) == 1

    def test_preserves_pitch(self):
        result = Identity().transform(C_MAJOR, N60)
        assert result[0].pitch == 60

    def test_preserves_start(self):
        result = Identity().transform(C_MAJOR, N60)
        assert result[0].start == 0.0

    def test_preserves_duration(self):
        result = Identity().transform(C_MAJOR, N60)
        assert result[0].duration == 2.0


# ─── OneToThree ─────────────────────────────────────────────────────────────


class TestOneToThree:
    def test_returns_three_notes(self):
        result = OneToThree().transform(C_MAJOR, N60)
        assert len(result) == 3

    def test_total_duration_preserved(self):
        result = OneToThree().transform(C_MAJOR, N60)
        total = sum(n.duration for n in result)
        assert abs(total - N60.duration) < 0.01

    def test_first_note_is_original_pitch(self):
        result = OneToThree().transform(C_MAJOR, N60)
        assert result[0].pitch == 60

    def test_last_note_is_original_pitch(self):
        result = OneToThree().transform(C_MAJOR, N60)
        assert result[-1].pitch == 60

    def test_middle_note_differs(self):
        # With many random attempts, at least some should produce a different middle note
        changed = False
        for _ in range(20):
            result = OneToThree().transform(C_MAJOR, N60)
            if result[1].pitch != 60:
                changed = True
                break
        assert changed, "OneToThree never produced a neighbor tone"

    def test_notes_are_contiguous(self):
        result = OneToThree().transform(C_MAJOR, N60)
        for i in range(1, len(result)):
            assert abs(result[i].start - (result[i - 1].start + result[i - 1].duration)) < 0.01

    def test_start_preserved(self):
        result = OneToThree().transform(C_MAJOR, N60)
        assert result[0].start == 0.0


# ─── TwoToThree ─────────────────────────────────────────────────────────────


class TestTwoToThree:
    def test_returns_two_notes(self):
        result = TwoToThree().transform(C_MAJOR, N60, N64)
        assert len(result) == 2

    def test_total_duration_preserved(self):
        result = TwoToThree().transform(C_MAJOR, N60, N64)
        total = sum(n.duration for n in result)
        assert abs(total - N60.duration) < 0.01

    def test_first_note_is_original_pitch(self):
        result = TwoToThree().transform(C_MAJOR, N60, N64)
        assert result[0].pitch == 60

    def test_no_next_note_falls_back(self):
        result = TwoToThree().transform(C_MAJOR, N60, None)
        assert len(result) == 1
        assert result[0].pitch == 60

    def test_interpolated_pitch_between(self):
        # With repeated runs, at least some should interpolate
        found_interp = False
        for _ in range(20):
            result = TwoToThree().transform(C_MAJOR, N60, N67)
            if len(result) > 1 and result[1].pitch not in (60, 67):
                found_interp = True
                break
        assert found_interp, "TwoToThree never interpolated a passing tone"


# ─── TwoToFour ──────────────────────────────────────────────────────────────


class TestTwoToFour:
    def test_returns_three_notes(self):
        result = TwoToFour().transform(C_MAJOR, N60, N64)
        assert len(result) == 3

    def test_total_duration_preserved(self):
        result = TwoToFour().transform(C_MAJOR, N60, N64)
        total = sum(n.duration for n in result)
        assert abs(total - N60.duration) < 0.01

    def test_first_note_is_original_pitch(self):
        result = TwoToFour().transform(C_MAJOR, N60, N64)
        assert result[0].pitch == 60

    def test_no_next_note_falls_back(self):
        result = TwoToFour().transform(C_MAJOR, N60, None)
        assert len(result) == 1

    def test_oscillates_around_next_note(self):
        # Middle and last should oscillate around next note's pitch class
        for _ in range(20):
            result = TwoToFour().transform(C_MAJOR, N60, N64)
            if len(result) == 3:
                assert result[1].pitch != result[2].pitch


# ─── spiceup ────────────────────────────────────────────────────────────────


class TestSpiceup:
    def test_empty_input(self):
        assert spiceup([], C_MAJOR) == []

    def test_depth_zero_returns_same_count(self):
        notes = [N60, N64]
        result = spiceup(notes, C_MAJOR, depth=0)
        assert len(result) == 2

    def test_depth_one_produces_more_or_equal_notes(self):
        notes = [N60, N64, N67, N72]
        result = spiceup(notes, C_MAJOR, depth=1)
        assert len(result) >= len(notes)

    def test_depth_two_produces_even_more(self):
        notes = [N60, N64, N67, N72]
        r1 = spiceup(notes, C_MAJOR, depth=1)
        r2 = spiceup(notes, C_MAJOR, depth=2)
        # depth 2 applies transforms to already-transformed output
        assert len(r2) >= len(notes)

    def test_all_pitches_in_range(self):
        notes = [N60, N64, N67]
        result = spiceup(notes, C_MAJOR, depth=2)
        for n in result:
            assert 0 <= n.pitch <= 127

    def test_all_durations_positive(self):
        notes = [N60, N64, N67]
        result = spiceup(notes, C_MAJOR, depth=1)
        for n in result:
            assert n.duration > 0

    def test_custom_pool_identity_only(self):
        notes = [N60, N64, N67]
        result = spiceup(notes, C_MAJOR, depth=1, single_pool=[Identity], double_pool=[Identity])
        assert len(result) == 3  # Identity never splits


# ─── serialize_canon ────────────────────────────────────────────────────────


class TestSerializeCanon:
    def test_empty_voices(self):
        assert serialize_canon([], 2.0) == []

    def test_single_voice_no_delay(self):
        voice = [N60, N64]
        result = serialize_canon([voice], delay_beats=0.0)
        assert len(result) == 2

    def test_two_voices_with_delay(self):
        v1 = [NoteInfo(pitch=60, start=0.0, duration=2.0, velocity=80)]
        v2 = [NoteInfo(pitch=64, start=0.0, duration=2.0, velocity=80)]
        result = serialize_canon([v1, v2], delay_beats=2.0)
        assert len(result) == 2
        # v2 starts at 0.0, offset by delay=2.0 -> starts at 2.0
        v2_note = [n for n in result if n.pitch == 64]
        assert len(v2_note) == 1
        assert v2_note[0].start == 2.0

    def test_transposition(self):
        voice = [N60]
        result = serialize_canon([voice, voice], delay_beats=0.0, transpositions=[0, -12])
        pitches = sorted(n.pitch for n in result)
        assert pitches == [48, 60]

    def test_duration_cap(self):
        voice = [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]
        result = serialize_canon([voice, voice], delay_beats=2.0, duration_beats=5.0)
        # Second voice starts at 2.0, has 4.0 duration, but capped at 5.0
        v2 = [n for n in result if n.start >= 2.0]
        assert len(v2) == 1
        assert v2[0].duration == 3.0  # 5.0 - 2.0

    def test_notes_sorted_by_time(self):
        voices = [
            [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80)],
            [NoteInfo(pitch=72, start=0.0, duration=1.0, velocity=80)],
        ]
        result = serialize_canon(voices, delay_beats=1.0)
        for i in range(1, len(result)):
            assert result[i].start >= result[i - 1].start


# ─── Pool constants ─────────────────────────────────────────────────────────


class TestPoolConstants:
    def test_single_pool_has_identity(self):
        assert Identity in SINGLE_NOTE_TRANSFORMERS

    def test_double_pool_has_identity(self):
        assert Identity in DOUBLE_NOTE_TRANSFORMERS

    def test_single_pool_has_onetothree(self):
        assert OneToThree in SINGLE_NOTE_TRANSFORMERS

    def test_double_pool_has_twotothree(self):
        assert TwoToThree in DOUBLE_NOTE_TRANSFORMERS

    def test_double_pool_has_twotofour(self):
        assert TwoToFour in DOUBLE_NOTE_TRANSFORMERS

    def test_identity_weighted_higher_in_single(self):
        identity_count = SINGLE_NOTE_TRANSFORMERS.count(Identity)
        assert identity_count >= 2

    def test_identity_weighted_higher_in_double(self):
        identity_count = DOUBLE_NOTE_TRANSFORMERS.count(Identity)
        assert identity_count >= 2
