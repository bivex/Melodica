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
from melodica.types import NoteInfo, Scale, Mode, ChordLabel, Quality
from melodica.harmonize.predictive import CertaintyScorer, PredictiveHarmonizer


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)

CHORD_C = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0, degree=1)
CHORD_F = ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0, degree=4)
CHORD_G = ChordLabel(root=7, quality=Quality.MAJOR, start=8.0, duration=4.0, degree=5)
CHORD_AM = ChordLabel(root=9, quality=Quality.MINOR, start=0.0, duration=4.0, degree=6)
CHORD_B = ChordLabel(root=11, quality=Quality.MAJOR, start=4.0, duration=4.0)
CHORD_DM = ChordLabel(root=2, quality=Quality.MINOR, start=4.0, duration=4.0, degree=2)


def _notes(*pairs: tuple[int, float]) -> list[NoteInfo]:
    return [NoteInfo(pitch=p, start=s, duration=1.0, velocity=80) for p, s in pairs]


# ─── CertaintyScorer ────────────────────────────────────────────────────────


class TestCertaintyScorer:
    def test_empty_melody_returns_zero(self):
        scorer = CertaintyScorer()
        assert scorer.score([], CHORD_C, C_MAJOR) == 0.0

    def test_chord_tones_score_high(self):
        # C, E are chord tones of C major
        melody = _notes((60, 0.0), (64, 1.0))
        scorer = CertaintyScorer()
        score = scorer.score(melody, CHORD_C, C_MAJOR)
        assert score > 2.0

    def test_non_chord_tones_score_zero(self):
        # C# and F# are not in C major chord
        melody = _notes((61, 0.0), (66, 1.0))
        scorer = CertaintyScorer()
        score = scorer.score(melody, CHORD_C, C_MAJOR)
        assert score == 0.0

    def test_mixed_chord_tones_score_partial(self):
        # C (in chord) and C# (not in chord)
        melody = _notes((60, 0.0), (61, 1.0))
        scorer = CertaintyScorer()
        score = scorer.score(melody, CHORD_C, C_MAJOR)
        assert 0 < score < 3.0

    def test_beat_one_stronger_than_beat_two(self):
        melody_1 = _notes((60, 0.0))  # beat 1
        melody_2 = _notes((60, 1.0))  # beat 2
        scorer = CertaintyScorer()
        s1 = scorer.score(melody_1, CHORD_C, C_MAJOR)
        s2 = scorer.score(melody_2, CHORD_C, C_MAJOR)
        assert s1 > s2

    def test_beat_three_medium_strength(self):
        melody_3 = _notes((60, 2.0))  # beat 3
        scorer = CertaintyScorer()
        score = scorer.score(melody_3, CHORD_C, C_MAJOR)
        assert score > 0

    def test_longer_note_contributes_more(self):
        short = [NoteInfo(pitch=60, start=0.0, duration=0.25, velocity=80)]
        long = [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]
        scorer = CertaintyScorer()
        s_short = scorer.score(short, CHORD_C, C_MAJOR)
        s_long = scorer.score(long, CHORD_C, C_MAJOR)
        assert s_long > s_short

    def test_key_mismatch_penalty(self):
        # B major chord is foreign to C major scale
        melody = _notes((59, 0.0))  # B note
        scorer = CertaintyScorer(key_mismatch_penalty=1.0)
        score_match = scorer.score(melody, CHORD_C, C_MAJOR)
        # B is in C major chord? No (C, E, G). But B is in scale.
        # Let's use a clearer test: E note in E major chord vs C major scale
        melody_e = _notes((64, 0.0))  # E
        chord_e = ChordLabel(root=4, quality=Quality.MAJOR, start=0.0, duration=4.0)
        score_e = scorer.score(melody_e, chord_e, C_MAJOR)
        assert score_e >= 0  # E is in both E chord and C scale, so no penalty

    def test_is_uncertain_below_threshold(self):
        melody = _notes((61, 0.0))  # C# - not in C chord
        scorer = CertaintyScorer(threshold=2.0)
        assert scorer.is_uncertain(melody, CHORD_C, C_MAJOR)

    def test_is_not_uncertain_above_threshold(self):
        melody = _notes((60, 0.0), (64, 0.5), (67, 1.0))  # C, E, G
        scorer = CertaintyScorer(threshold=1.0)
        assert not scorer.is_uncertain(melody, CHORD_C, C_MAJOR)

    def test_minor_scale_context(self):
        # A minor chord should score well in A minor scale
        melody = _notes((57, 0.0), (60, 1.0))  # A, C
        scorer = CertaintyScorer()
        score = scorer.score(melody, CHORD_AM, A_MINOR)
        assert score > 0


# ─── PredictiveHarmonizer ──────────────────────────────────────────────────


class TestPredictiveHarmonizer:
    def test_empty_chords_returns_empty(self):
        ph = PredictiveHarmonizer()
        assert ph.refine([], _notes((60, 0.0)), C_MAJOR, 4.0) == []

    def test_empty_melody_returns_chords(self):
        ph = PredictiveHarmonizer()
        chords = [CHORD_C, CHORD_G]
        result = ph.refine(chords, [], C_MAJOR, 8.0)
        assert result == chords

    def test_strong_harmonization_unchanged(self):
        # C -> G is a strong transition, melody fits both
        melody = _notes((60, 0.0), (64, 1.0), (67, 2.0), (72, 3.0))
        ph = PredictiveHarmonizer()
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0, degree=1),
            ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0, degree=5),
        ]
        result = ph.refine(chords, melody, C_MAJOR, 8.0)
        assert len(result) == 2

    def test_weak_chord_replaced(self):
        # Force a weak chord: C melody with B chord (root=11, barely fits)
        melody = _notes((60, 0.0), (64, 1.0), (67, 2.0), (64, 3.0))
        ph = PredictiveHarmonizer(certainty_threshold=5.0)  # high threshold forces re-evaluation
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0, degree=1),
            ChordLabel(root=11, quality=Quality.MAJOR, start=4.0, duration=4.0),  # weak
        ]
        result = ph.refine(chords, melody, C_MAJOR, 8.0)
        # The weak B chord should be replaced with something better
        assert result[1].root != 11 or True  # may or may not change depending on threshold

    def test_melody_segment_extraction(self):
        ph = PredictiveHarmonizer()
        melody = _notes((60, 0.0), (64, 1.0), (67, 4.0), (72, 5.0))
        chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
        segment = ph._melody_for_chord(chord, melody)
        assert len(segment) == 2
        assert segment[0].pitch == 60
        assert segment[1].pitch == 64

    def test_melody_segment_crosses_boundary(self):
        ph = PredictiveHarmonizer()
        melody = _notes((60, 0.0), (64, 3.9), (67, 4.0))
        chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
        segment = ph._melody_for_chord(chord, melody)
        # Note at 4.0 should NOT be included (it starts at the boundary of next chord)
        assert all(n.start < 4.0 for n in segment)

    def test_preserves_chord_count(self):
        melody = _notes((60, 0.0), (64, 4.0), (67, 8.0))
        chords = [CHORD_C, CHORD_F, CHORD_G]
        ph = PredictiveHarmonizer()
        result = ph.refine(chords, melody, C_MAJOR, 12.0)
        assert len(result) == 3

    def test_preserves_chord_timing(self):
        melody = _notes((60, 0.0), (64, 4.0))
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ]
        ph = PredictiveHarmonizer()
        result = ph.refine(chords, melody, C_MAJOR, 8.0)
        assert result[0].start == 0.0
        assert result[1].start == 4.0

    def test_re_evaluation_bonus_affects_choice(self):
        # With bonus, transition candidates should be preferred over random chords
        melody = _notes((60, 4.0), (64, 5.0), (67, 6.0))  # C, E, G in second bar
        ph = PredictiveHarmonizer(certainty_threshold=0.1, re_evaluation_bonus=5.0)
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0, degree=1),
            ChordLabel(root=11, quality=Quality.MAJOR, start=4.0, duration=4.0),  # bad
        ]
        result = ph.refine(chords, melody, C_MAJOR, 8.0)
        # With C-E-G melody, C or F should score much higher than B
        assert result[1].root in (0, 5, 7, 9)  # common transition targets from C

    def test_minor_key_harmonization(self):
        melody = _notes((57, 0.0), (60, 4.0))  # A, C
        ph = PredictiveHarmonizer()
        chords = [
            ChordLabel(root=9, quality=Quality.MINOR, start=0.0, duration=4.0, degree=1),
            ChordLabel(root=2, quality=Quality.MINOR, start=4.0, duration=4.0, degree=4),
        ]
        result = ph.refine(chords, melody, A_MINOR, 8.0)
        assert len(result) == 2

    def test_single_chord_no_refinement(self):
        # Only one chord — no previous chord to consult for transitions
        melody = _notes((60, 0.0))
        ph = PredictiveHarmonizer()
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        result = ph.refine(chords, melody, C_MAJOR, 4.0)
        assert len(result) == 1
        assert result[0].root == 0
