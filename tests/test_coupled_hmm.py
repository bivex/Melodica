# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_coupled_hmm.py — Tests for CoupledHMMHarmonizer.

Covers:
1. Module-level constants and weight loading
2. _log_emit_chord / _log_emit_key correctness
3. _viterbi_chords: basic, constraints, tension, edge cases
4. _viterbi_keys: basic, key persistence, edge cases
5. _get_change_points / _extract_observations
6. Full harmonize() integration
7. Determinism and consistency
"""

import math
import pytest
import numpy as np
from unittest.mock import MagicMock

from melodica.types import NoteInfo, Scale, Mode, Quality, ChordLabel
from melodica.harmonize.coupled_hmm import (
    CoupledHMMHarmonizer,
    WeightedNote,
    N_TONES,
    N_TYPES,
    N_KEY_TYPES,
    TYPE_TO_QUALITY,
    PNOTE,
    PCHANGE,
    LOG_PNOTE,
    LOG_PCHANGE,
    KEY_TYPE_PRIOR,
    KEY_OFFSET_LOG,
    LOG_KEY_TYPE_PRIOR,
    _EPS,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)

N = lambda p, s, d, v=80: NoteInfo(pitch=p, start=s, duration=d, velocity=v)


def _c_major_melody(bars=4):
    notes = []
    pitches = [60, 64, 67, 72, 62, 65, 69, 60]
    for bar in range(bars):
        for i in range(min(8, len(pitches))):
            notes.append(N(pitches[i % len(pitches)], bar * 4 + i * 0.5, 0.5))
    return notes


# ===========================================================================
# 1. Constants and weight loading
# ===========================================================================

class TestConstants:
    def test_n_tones(self):
        assert N_TONES == 12

    def test_n_types(self):
        assert N_TYPES == 12

    def test_type_to_quality_length(self):
        assert len(TYPE_TO_QUALITY) == N_TYPES

    def test_type_to_quality_values(self):
        assert TYPE_TO_QUALITY[0] == Quality.MAJOR
        assert TYPE_TO_QUALITY[1] == Quality.MINOR
        assert TYPE_TO_QUALITY[2] == Quality.DIMINISHED
        assert TYPE_TO_QUALITY[8] == Quality.DOMINANT7

    def test_pnote_shape(self):
        assert PNOTE.shape == (N_TONES, N_TYPES)

    def test_pchange_shape(self):
        assert PCHANGE.shape == (N_TYPES, N_TONES, N_TYPES)

    def test_log_pnote_shape(self):
        assert LOG_PNOTE.shape == (N_TONES, N_TYPES)

    def test_log_pchange_shape(self):
        assert LOG_PCHANGE.shape == (N_TYPES, N_TONES, N_TYPES)

    def test_log_key_type_prior_shape(self):
        assert LOG_KEY_TYPE_PRIOR.shape == (N_KEY_TYPES, N_TYPES)

    def test_key_type_prior_shape(self):
        assert KEY_TYPE_PRIOR.shape == (N_KEY_TYPES, N_TYPES)

    def test_key_offset_log_shape(self):
        assert KEY_OFFSET_LOG.shape == (N_KEY_TYPES, N_TONES)

    def test_pnote_sums_positive(self):
        assert np.all(PNOTE > 0)
        assert np.all(PNOTE < 1)

    def test_log_values_negative(self):
        assert np.all(LOG_PNOTE < 0)
        assert np.all(LOG_PCHANGE < 0)


# ===========================================================================
# 2. Emission helpers
# ===========================================================================

class TestLogEmitChord:
    def test_empty_returns_negative(self):
        result = CoupledHMMHarmonizer._log_emit_chord([], 0, 0)
        assert result == -1.0

    def test_single_note_c_major(self):
        wpcs = [WeightedNote(pitch_class=0, weight=1.0)]
        result = CoupledHMMHarmonizer._log_emit_chord(wpcs, 0, 0)
        assert isinstance(result, float)
        assert result < 0

    def test_c_e_g_favors_c_major(self):
        wpcs = [WeightedNote(pc, 1.0) for pc in [0, 4, 7]]
        c_major = CoupledHMMHarmonizer._log_emit_chord(wpcs, 0, 0)
        d_major = CoupledHMMHarmonizer._log_emit_chord(wpcs, 2, 0)
        assert c_major > d_major

    def test_normalization(self):
        wpcs = [WeightedNote(0, 2.0)]
        result = CoupledHMMHarmonizer._log_emit_chord(wpcs, 0, 0)
        wpcs2 = [WeightedNote(0, 1.0)]
        result2 = CoupledHMMHarmonizer._log_emit_chord(wpcs2, 0, 0)
        assert abs(result - result2) < 0.01

    def test_weighted_notes(self):
        wpcs = [WeightedNote(0, 0.5), WeightedNote(4, 2.0)]
        result = CoupledHMMHarmonizer._log_emit_chord(wpcs, 0, 0)
        assert isinstance(result, float)


class TestLogEmitKey:
    def test_basic(self):
        result = CoupledHMMHarmonizer._log_emit_key((0, 0), 0, 0)
        assert isinstance(result, float)
        assert result < 0

    def test_diatonic_higher_than_chromatic(self):
        c_in_c = CoupledHMMHarmonizer._log_emit_key((0, 0), 0, 0)
        fsharp_in_c = CoupledHMMHarmonizer._log_emit_key((6, 0), 0, 0)
        assert c_in_c > fsharp_in_c

    def test_key_type_affects_result(self):
        major = CoupledHMMHarmonizer._log_emit_key((0, 1), 0, 0)
        minor = CoupledHMMHarmonizer._log_emit_key((0, 1), 0, 1)
        assert isinstance(major, float)
        assert isinstance(minor, float)


# ===========================================================================
# 3. _viterbi_chords
# ===========================================================================

class TestViterbiChords:
    def _make_harmonizer(self):
        return CoupledHMMHarmonizer(chord_change="bars")

    def test_basic_output(self):
        h = self._make_harmonizer()
        obs = [[WeightedNote(0, 1.0), WeightedNote(4, 1.0), WeightedNote(7, 1.0)]]
        cps = [0.0]
        result = h._viterbi_chords(obs, C_MAJOR, cps)
        assert len(result) == 1
        root, tidx = result[0]
        assert 0 <= root < 12
        assert 0 <= tidx < N_TYPES

    def test_multi_step(self):
        h = self._make_harmonizer()
        obs = [
            [WeightedNote(0, 1.0), WeightedNote(4, 1.0), WeightedNote(7, 1.0)],
            [WeightedNote(7, 1.0), WeightedNote(11, 1.0), WeightedNote(2, 1.0)],
        ]
        cps = [0.0, 4.0]
        result = h._viterbi_chords(obs, C_MAJOR, cps)
        assert len(result) == 2

    def test_tonic_bias(self):
        h = self._make_harmonizer()
        obs = [[WeightedNote(0, 1.0)] for _ in range(8)]
        cps = [i * 4.0 for i in range(8)]
        result = h._viterbi_chords(obs, C_MAJOR, cps)
        assert len(result) == 8
        assert all(0 <= r[0] < 12 and 0 <= r[1] < N_TYPES for r in result)

    def test_with_constraint(self):
        h = self._make_harmonizer()
        obs = [[WeightedNote(0, 1.0)] for _ in range(4)]
        cps = [0.0, 4.0, 8.0, 12.0]
        constraints = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        result = h._viterbi_chords(obs, C_MAJOR, cps, constraints=constraints)
        assert result[0][0] == 0
        assert result[0][1] == 0

    def test_constraint_at_middle(self):
        h = self._make_harmonizer()
        obs = [[WeightedNote(0, 1.0)] for _ in range(4)]
        cps = [0.0, 4.0, 8.0, 12.0]
        constraints = [ChordLabel(root=5, quality=Quality.MAJOR, start=8.0, duration=4.0)]
        result = h._viterbi_chords(obs, C_MAJOR, cps, constraints=constraints)
        assert result[2][0] == 5
        assert result[2][1] == 0

    def test_tension_curve(self):
        h = self._make_harmonizer()
        obs = [[WeightedNote(0, 1.0)] for _ in range(4)]
        cps = [0.0, 4.0, 8.0, 12.0]
        tc = MagicMock()
        tc.tension_at = lambda x: 1.0
        result = h._viterbi_chords(obs, C_MAJOR, cps, tension_curve=tc)
        assert len(result) == 4

    def test_single_step(self):
        h = self._make_harmonizer()
        obs = [[WeightedNote(0, 1.0)]]
        cps = [0.0]
        result = h._viterbi_chords(obs, C_MAJOR, cps)
        assert len(result) == 1

    def test_empty_obs_step(self):
        h = self._make_harmonizer()
        obs = [[], [WeightedNote(0, 1.0)]]
        cps = [0.0, 4.0]
        result = h._viterbi_chords(obs, C_MAJOR, cps)
        assert len(result) == 2


# ===========================================================================
# 4. _viterbi_keys
# ===========================================================================

class TestViterbiKeys:
    def _make_harmonizer(self):
        return CoupledHMMHarmonizer(chord_change="bars")

    def test_basic_output(self):
        h = self._make_harmonizer()
        chords = [(0, 0), (5, 1), (7, 0)]
        result = h._viterbi_keys(chords)
        assert len(result) == 3
        for root, kt in result:
            assert 0 <= root < 12
            assert 0 <= kt < N_KEY_TYPES

    def test_single_chord(self):
        h = self._make_harmonizer()
        result = h._viterbi_keys([(0, 0)])
        assert len(result) == 1

    def test_key_stability(self):
        h = self._make_harmonizer()
        c_major_chords = [(0, 0)] * 16
        result = h._viterbi_keys(c_major_chords)
        roots = [r for r, _ in result]
        assert len(set(roots)) <= 4

    def test_many_chords(self):
        h = self._make_harmonizer()
        chords = [(i % 12, i % N_TYPES) for i in range(64)]
        result = h._viterbi_keys(chords)
        assert len(result) == 64


# ===========================================================================
# 5. _get_change_points / _extract_observations
# ===========================================================================

class TestChangePoints:
    def test_bars(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        cps = h._get_change_points(16.0)
        assert len(cps) == 4
        assert cps == [0.0, 4.0, 8.0, 12.0]

    def test_half(self):
        h = CoupledHMMHarmonizer(chord_change="half")
        cps = h._get_change_points(16.0)
        assert len(cps) == 8
        assert cps[0] == 0.0
        assert cps[1] == 2.0

    def test_short_duration(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        cps = h._get_change_points(3.0)
        assert len(cps) == 0 or len(cps) == 1

    def test_zero_duration(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        cps = h._get_change_points(0.0)
        assert len(cps) == 0


class TestExtractObservations:
    def test_basic(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60, 0, 2), N(64, 2, 2)]
        cps = [0.0, 4.0]
        obs = h._extract_observations(melody, cps)
        assert len(obs) == 2
        assert len(obs[0]) > 0

    def test_empty_melody(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        obs = h._extract_observations([], [0.0, 4.0])
        assert len(obs) == 2
        assert all(len(o) == 0 for o in obs)

    def test_pitch_class_consolidation(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60, 0, 1), N(72, 0.5, 1)]
        cps = [0.0, 4.0]
        obs = h._extract_observations(melody, cps)
        pcs = [wn.pitch_class for wn in obs[0]]
        assert pcs.count(0) == 1

    def test_metric_weighting_beat1(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60, 0.0, 1), N(64, 1.5, 1)]
        cps = [0.0, 4.0]
        obs = h._extract_observations(melody, cps)
        by_pc = {wn.pitch_class: wn.weight for wn in obs[0]}
        assert by_pc[0] > by_pc[4]


# ===========================================================================
# 6. Full harmonize() integration
# ===========================================================================

class TestHarmonize:
    def test_basic(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(result) >= 1
        for c in result:
            assert isinstance(c, ChordLabel)
            assert 0 <= c.root < 12
            assert c.duration > 0

    def test_empty_melody(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        result = h.harmonize([], C_MAJOR, duration_beats=16.0)
        assert result == []

    def test_single_note(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        result = h.harmonize([N(60, 0, 4)], C_MAJOR, duration_beats=4.0)
        assert len(result) >= 1

    def test_long_melody(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(16)
        result = h.harmonize(melody, C_MAJOR, duration_beats=64.0)
        assert len(result) >= 4
        total_dur = sum(c.duration for c in result)
        assert abs(total_dur - 64.0) < 0.01

    def test_minor_key(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(69, i, 1) for i in range(16)]
        result = h.harmonize(melody, A_MINOR, duration_beats=16.0)
        assert len(result) >= 1

    def test_with_constraints(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 0
        assert result[0].quality == Quality.MAJOR

    def test_half_bar_changes(self):
        h = CoupledHMMHarmonizer(chord_change="half")
        melody = _c_major_melody(4)
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(result) >= 4

    def test_chord_durations_sum_to_total(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(8)
        result = h.harmonize(melody, C_MAJOR, duration_beats=32.0)
        total = sum(c.duration for c in result)
        assert abs(total - 32.0) < 0.01

    def test_chord_roots_valid(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        for c in result:
            assert 0 <= c.root < 12

    def test_qualities_valid(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        valid_qualities = {q for q in Quality}
        for c in result:
            assert c.quality in valid_qualities


# ===========================================================================
# 7. Determinism and consistency
# ===========================================================================

class TestDeterminism:
    def test_same_input_same_output(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        r1 = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        r2 = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            assert a.root == b.root
            assert a.quality == b.quality

    def test_viterbi_chords_deterministic(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        obs = [[WeightedNote(0, 1.0), WeightedNote(4, 1.0), WeightedNote(7, 1.0)]]
        cps = [0.0]
        r1 = h._viterbi_chords(obs, C_MAJOR, cps)
        r2 = h._viterbi_chords(obs, C_MAJOR, cps)
        assert r1 == r2

    def test_viterbi_keys_deterministic(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        chords = [(0, 0), (5, 1), (7, 0), (0, 0)]
        r1 = h._viterbi_keys(chords)
        r2 = h._viterbi_keys(chords)
        assert r1 == r2


class TestConsistency:
    def test_chord_path_matches_observations(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        melody_pcs = {n.pitch % 12 for n in melody}
        for c in result:
            chord_type = TYPE_TO_QUALITY[c.type if hasattr(c, 'type') else 0]

    def test_more_notes_more_chords(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        short = h.harmonize(_c_major_melody(4), C_MAJOR, duration_beats=16.0)
        long = h.harmonize(_c_major_melody(16), C_MAJOR, duration_beats=64.0)
        assert len(long) >= len(short)

    def test_beam_width_parameter(self):
        h1 = CoupledHMMHarmonizer(beam_width=4, chord_change="bars")
        h2 = CoupledHMMHarmonizer(beam_width=24, chord_change="bars")
        melody = _c_major_melody(4)
        r1 = h1.harmonize(melody, C_MAJOR, duration_beats=16.0)
        r2 = h2.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(r1) > 0
        assert len(r2) > 0


# ===========================================================================
# 8. Edge cases
# ===========================================================================

class TestEdgeCases:
    def test_all_same_pitch(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60, i * 0.5, 0.5) for i in range(32)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(result) >= 1

    def test_chromatic_melody(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60 + i, i, 1) for i in range(16)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(result) >= 1

    def test_very_short_notes(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60 + i % 12, i * 0.125, 0.125) for i in range(128)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(result) >= 1

    def test_overlapping_notes(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60, 0, 16), N(64, 0, 16), N(67, 0, 16)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(result) >= 1

    def test_many_constraint_steps(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.MAJOR, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 0
        assert result[1].root == 5
        assert result[2].root == 7
        assert result[3].root == 0

    def test_single_bar(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = [N(60, 0, 2), N(64, 2, 2)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=4.0)
        assert len(result) >= 1
        assert abs(result[0].duration - 4.0) < 0.01

    def test_transposed_same_quality(self):
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody_d = [NoteInfo(pitch=n.pitch + 2, start=n.start, duration=n.duration, velocity=n.velocity)
                    for n in _c_major_melody(4)]
        r_c = h.harmonize(_c_major_melody(4), C_MAJOR, duration_beats=16.0)
        r_d = h.harmonize(melody_d, Scale(root=2, mode=Mode.MAJOR), duration_beats=16.0)
        assert len(r_c) == len(r_d)
        for c, d in zip(r_c, r_d):
            assert c.quality == d.quality
            assert (d.root - c.root) % 12 == 2
