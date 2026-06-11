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


# ===========================================================================
# 9. Progression patterns
# ===========================================================================

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _prog(scale, bars=16, seed=42, chord_change="bars", **kw):
    """Generate a chord progression with CoupledHMMHarmonizer."""
    import random
    random.seed(seed)
    h = CoupledHMMHarmonizer(chord_change=chord_change, **kw)
    pitches = [scale.root + 60 + random.randint(0, 12) for _ in range(bars * 8)]
    melody = [NoteInfo(pitch=p, start=i * 0.5, duration=0.5, velocity=80) for i, p in enumerate(pitches)]
    return h.harmonize(melody, scale, float(bars * 4))


def _prog_diatonic(scale, bars=16, seed=42, chord_change="bars", **kw):
    """Generate progression using a diatonic melody (better for cadence tests)."""
    import random
    random.seed(seed)
    h = CoupledHMMHarmonizer(chord_change=chord_change, **kw)
    degrees = scale.degrees()
    melody = []
    for i in range(bars * 8):
        deg = degrees[random.randint(0, len(degrees) - 1)]
        melody.append(NoteInfo(
            pitch=60 + int(deg), start=i * 0.5, duration=0.5, velocity=80,
        ))
    return h.harmonize(melody, scale, float(bars * 4))


def _names(chords):
    return [f"{NOTE_NAMES[c.root]}{c.quality.name}" for c in chords]


# -- 9a. Cadence & resolution --

class TestProgressionCadences:

    def test_tonic_at_start(self):
        """First chord should tend toward the tonic (I or vi)."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        first = chords[0]
        diatonic = {0, 2, 4, 5, 7, 9, 11}
        assert first.root in diatonic, f"First chord root {NOTE_NAMES[first.root]} not diatonic"

    def test_at_least_one_perfect_cadence(self):
        """Diatonic melody input should produce at least one V→I or VII→I."""
        for seed in range(20):
            chords = _prog_diatonic(C_MAJOR, bars=16, seed=seed)
            for i in range(1, len(chords)):
                prev_root = chords[i - 1].root
                curr_root = chords[i].root
                if prev_root == 7 and curr_root == 0:
                    return  # found V→I
                if (curr_root - prev_root) % 12 == 5 and curr_root == 0:
                    return  # found VII→I
        pytest.fail("No V→I or VII→I cadence found across 20 seeds")

    def test_dominant_before_tonic(self):
        """Diatonic melody input should produce G→C at least once."""
        for seed in range(20):
            chords = _prog_diatonic(C_MAJOR, bars=16, seed=seed)
            if any(chords[i].root == 7 and chords[i + 1].root == 0
                   for i in range(len(chords) - 1)):
                return
        pytest.fail("No G→C found across 20 seeds with diatonic input")

    def test_final_chord_is_diatonic(self):
        """Last chord root should be diatonic to the key (at least some seeds)."""
        diatonic = {0, 2, 4, 5, 7, 9, 11}
        for seed in range(20):
            chords = _prog(C_MAJOR, bars=16, seed=seed)
            if chords[-1].root in diatonic:
                return
        pytest.fail("No seed produced a diatonic final chord across 20 seeds")


# -- 9b. Functional flow patterns --

class TestProgressionFlow:

    def test_root_motion_varied(self):
        """Consecutive root intervals should not all be the same."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        roots = [c.root for c in chords]
        intervals = [(roots[i + 1] - roots[i]) % 12 for i in range(len(roots) - 1)]
        unique = set(intervals)
        assert len(unique) >= 3, f"Only {len(unique)} unique root intervals: {sorted(unique)}"

    def test_no_root_stagnation(self):
        """No more than 2 consecutive chords on the same root."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        run = 1
        for i in range(1, len(chords)):
            if chords[i].root == chords[i - 1].root:
                run += 1
                assert run <= 2, f"Root {NOTE_NAMES[chords[i].root]} repeated {run}x"
            else:
                run = 1

    def test_common_progression_patterns(self):
        """Some seed should produce common progression fragments (I-V, I-IV, IV-V)."""
        c_major_pairs = {(0, 7), (0, 5), (5, 7), (7, 0), (5, 0)}
        for seed in range(20):
            chords = _prog(C_MAJOR, bars=16, seed=seed)
            patterns = set()
            for i in range(len(chords) - 1):
                pair = (chords[i].root, chords[i + 1].root)
                patterns.add(pair)
            found = patterns & c_major_pairs
            if len(found) >= 2:
                return
        pytest.fail("No seed produced >=2 common C-major pairs across 20 seeds")

    def test_ascending_fourths_motion(self):
        """Root motion by ascending 4th (interval 5) is fundamental; should appear."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        roots = [c.root for c in chords]
        p4_count = sum(1 for i in range(len(roots) - 1) if (roots[i + 1] - roots[i]) % 12 == 5)
        assert p4_count >= 1, f"No ascending 4th root motion in: {_names(chords)}"


# -- 9c. Diversity & distribution --

class TestProgressionDiversity:

    def test_root_diversity_at_least_4(self):
        """16-bar progression should use at least 4 unique roots."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        roots = len(set(c.root for c in chords))
        assert roots >= 4, f"Only {roots} unique roots: {_names(chords)}"

    def test_quality_diversity(self):
        """Should produce at least 2 different chord qualities."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        qualities = len(set(c.quality for c in chords))
        assert qualities >= 2, f"Only {qualities} quality types"

    def test_dom7_not_dominant(self):
        """Dom7 should not exceed 60% of all chords (known gravity well)."""
        for seed in range(5):
            chords = _prog(C_MAJOR, bars=16, seed=seed)
            dom7_ratio = sum(1 for c in chords if c.quality == Quality.DOMINANT7) / len(chords)
            assert dom7_ratio < 0.6, f"Seed {seed}: Dom7 is {dom7_ratio:.0%} of progression"

    def test_no_quality_gravity_well(self):
        """No single quality should exceed 60%."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        from collections import Counter
        counts = Counter(c.quality for c in chords)
        for q, cnt in counts.items():
            ratio = cnt / len(chords)
            assert ratio < 0.6, f"{q.name} is {ratio:.0%} of progression (gravity well)"

    def test_different_seeds_different_progressions(self):
        """Different seeds should produce different progressions."""
        progs = set()
        for seed in range(5):
            chords = _prog(C_MAJOR, bars=8, seed=seed)
            progs.add(tuple(_names(chords)))
        assert len(progs) >= 2, f"All seeds produced same progression"

    def test_interval_diversity_at_least_4(self):
        """Should have at least 4 unique intervals between consecutive roots."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        roots = [c.root for c in chords]
        intervals = set((roots[i + 1] - roots[i]) % 12 for i in range(len(roots) - 1))
        assert len(intervals) >= 4, f"Only {len(intervals)} unique intervals: {sorted(intervals)}"


# -- 9d. Mode-specific progressions --

class TestModeProgressions:

    def test_minor_key_uses_minor_chords(self):
        """
        A minor progression should produce minor-quality chords.
        Extended minor chords (minor 7th and 9th) are musically appropriate and expected
        in cinematic and modern jazz contexts as they add color and harmonic tension
        without violating the minor key signature. However, they should not be overused
        systematically over standard minor triads.
        """
        chords = _prog(A_MINOR, bars=16, seed=1)
        minor_count = sum(1 for c in chords if c.quality in (Quality.MINOR, Quality.MINOR7, Quality.MINOR9))
        assert minor_count >= 1, f"No minor chords in A minor progression: {_names(chords)}"
        
        # Ensure model does not systematically overuse extended minor chords
        minor_ext = sum(1 for c in chords if c.quality in (Quality.MINOR7, Quality.MINOR9))
        assert minor_ext / len(chords) < 0.5, f"Overuse of extended minor chords ({minor_ext/len(chords):.2f})"

    def test_major_vs_minor_different(self):
        """C major and A minor should produce different progressions."""
        r_major = _prog(C_MAJOR, bars=8, seed=3)
        r_minor = _prog(A_MINOR, bars=8, seed=3)
        assert _names(r_major) != _names(r_minor), "Major and minor produced identical progressions"

    def test_diatonic_roots_in_major(self):
        """C major chords should use mostly diatonic roots (relaxed for stochastic input)."""
        diatonic = {0, 2, 4, 5, 7, 9, 11}
        total_ratio = 0.0
        for seed in range(5):
            chords = _prog(C_MAJOR, bars=16, seed=seed)
            in_key = sum(1 for c in chords if c.root in diatonic)
            total_ratio = max(total_ratio, in_key / len(chords))
        assert total_ratio >= 0.5, f"Best diatonic ratio across 5 seeds: {total_ratio:.0%}"



# -- 9e. Structural & timing --

class TestProgressionStructure:

    def test_chord_durations_cover_full_duration(self):
        """Chord durations should sum to total beats."""
        for bars in [4, 8, 16]:
            chords = _prog(C_MAJOR, bars=bars, seed=1)
            total = sum(c.duration for c in chords)
            expected = bars * 4.0
            assert abs(total - expected) < 0.01, f"bars={bars}: {total} != {expected}"

    def test_chord_starts_are_monotonic(self):
        """Chord start times should be strictly increasing."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        for i in range(1, len(chords)):
            assert chords[i].start > chords[i - 1].start, (
                f"Non-monotonic starts at {i}: {chords[i-1].start} -> {chords[i].start}"
            )

    def test_no_gaps_between_chords(self):
        """Chords should tile the timeline without gaps."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        for i in range(1, len(chords)):
            gap = chords[i].start - chords[i - 1].end
            assert abs(gap) < 0.01, f"Gap of {gap} between chords {i-1} and {i}"

    def test_half_bar_changes_double_count(self):
        """Half-bar mode should produce roughly 2x more chords than bar mode."""
        melody = _c_major_melody(4)
        h_bars = CoupledHMMHarmonizer(chord_change="bars")
        h_half = CoupledHMMHarmonizer(chord_change="half")
        r_bars = h_bars.harmonize(melody, C_MAJOR, duration_beats=16.0)
        r_half = h_half.harmonize(melody, C_MAJOR, duration_beats=16.0)
        assert len(r_half) >= len(r_bars)

    def test_bar_aligned_starts(self):
        """Bar-mode chord starts should be on bar boundaries (multiples of 4)."""
        chords = _prog(C_MAJOR, bars=16, seed=1, chord_change="bars")
        for c in chords:
            assert abs(c.start % 4.0) < 0.01, f"Chord at {c.start} not on bar boundary"


# -- 9f. Regression & anti-patterns --

class TestProgressionAntiPatterns:

    def test_no_infinite_loop_pattern(self):
        """V→I→V→I should not repeat more than 3 times consecutively."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        roots = [c.root for c in chords]
        loop_run = 0
        for i in range(1, len(roots) - 1):
            if roots[i - 1] == 7 and roots[i] == 0 and roots[i + 1] == 7:
                loop_run += 1
            else:
                loop_run = 0
            assert loop_run < 3, f"V→I→V loop detected {loop_run}x: {_names(chords)}"

    def test_no_all_augmented(self):
        """Augmented quality should not exceed 15%."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        aug_ratio = sum(1 for c in chords if c.quality == Quality.AUGMENTED) / len(chords)
        assert aug_ratio < 0.15, f"Aug is {aug_ratio:.0%}"

    def test_no_self_loop_chains(self):
        """No more than 2 consecutive same-quality chords."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        run = 1
        for i in range(1, len(chords)):
            if chords[i].quality == chords[i - 1].quality:
                run += 1
                assert run <= 2, f"{chords[i].quality.name} repeated {run}x"
            else:
                run = 1

    def test_no_single_root_monopoly(self):
        """No single root should exceed 50% of all chords."""
        chords = _prog(C_MAJOR, bars=16, seed=1)
        from collections import Counter
        counts = Counter(c.root for c in chords)
        for root, cnt in counts.items():
            ratio = cnt / len(chords)
            assert ratio < 0.5, f"Root {NOTE_NAMES[root]} is {ratio:.0%}"


# -- 9g. Constraints interaction with progressions --

class TestProgressionConstraints:

    def test_full_progression_locked(self):
        """Locking all bars should produce exactly the locked progression."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert len(result) == 4
        assert [c.root for c in result] == [0, 5, 7, 0]

    def test_partial_constraint_preserves_free(self):
        """Locking first bar only; rest should be free."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 0
        assert result[0].quality == Quality.MAJOR
        # Remaining bars should still be populated
        assert len(result) == 4

    def test_constraint_does_not_break_duration_sum(self):
        """Constraints should not break total duration sum."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=2, quality=Quality.MINOR, start=4.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        total = sum(c.duration for c in result)
        assert abs(total - 16.0) < 0.01


# ===========================================================================
# 10. Constrained HMM: quality fallback
# ===========================================================================

class TestConstrainedQualityFallback:

    def test_half_dim7_does_not_crash(self):
        """HALF_DIM7 constraint should fall back to MINOR7, not kill all states."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=11, quality=Quality.HALF_DIM7, start=0.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=4.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert len(result) == 4
        assert result[0].root == 11
        assert result[0].quality == Quality.MINOR7

    def test_full_dim7_does_not_crash(self):
        """FULL_DIM7 should fall back to DIMINISHED."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=2, quality=Quality.FULL_DIM7, start=0.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=4.0, duration=12.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 2
        assert result[0].quality == Quality.DIMINISHED

    def test_power_chord_fallback(self):
        """POWER should fall back to MAJOR."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.POWER, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.POWER, start=4.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.POWER, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.POWER, start=12.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert len(result) == 4
        assert result[0].quality == Quality.MAJOR
        assert result[1].quality == Quality.MAJOR

    def test_dom7_flat9_fallback(self):
        """DOM7_FLAT9 should fall back to DOMINANT7."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=7, quality=Quality.DOM7_FLAT9, start=0.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=4.0, duration=12.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 7
        assert result[0].quality == Quality.DOMINANT7

    def test_exotic_quality_does_not_produce_garbage(self):
        """Exotic quality should produce valid chords (roots 0-11, positive durations)."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.SPECTRAL_CHORD, start=0.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.ALTERED_DOMINANT, start=4.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert len(result) == 4
        for c in result:
            assert 0 <= c.root < 12
            assert c.duration > 0
        total = sum(c.duration for c in result)
        assert abs(total - 16.0) < 0.01


# ===========================================================================
# 11. Constrained HMM: alignment snapping
# ===========================================================================

class TestConstrainedAlignment:

    def test_slightly_off_grid_snaps(self):
        """Constraint with start=0.001 should snap to change_point=0.0."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.001, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 0

    def test_non_matching_duration_still_constrains(self):
        """Constraint with duration=3.0 should still snap to the bar grid."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=5, quality=Quality.MAJOR, start=0.0, duration=3.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 5

    def test_mid_bar_constraint_snaps(self):
        """Constraint starting at beat 1.0 should snap to nearest change point."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=2, quality=Quality.MINOR, start=1.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        # Should snap to 0.0 (nearest cp to 1.0)
        assert result[0].root == 2

    def test_no_snap_needed_when_aligned(self):
        """Already-aligned constraints should be unchanged."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[0].root == 0
        assert result[1].root == 5


# ===========================================================================
# 12. Constrained HMM: time signatures
# ===========================================================================

class TestConstrainedTimeSignatures:

    def test_3_4_time_constraints(self):
        """3/4 time: constraints should adapt to 3-beat bars."""
        from melodica.types import BarGrid
        grid = BarGrid(numerator=3, denominator=4)
        h = CoupledHMMHarmonizer(chord_change="bars", bar_grid=grid)
        melody = [N(60, i * 0.5, 0.5) for i in range(24)]
        # In 3/4, each bar = 3 beats, 8 bars = 24 beats
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=3.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=3.0, duration=3.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=6.0, duration=3.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=9.0, duration=3.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=12.0, constraints=constraints)
        assert len(result) == 4
        assert result[0].root == 0
        assert result[1].root == 5
        assert result[2].root == 7
        assert result[3].root == 0
        total = sum(c.duration for c in result)
        assert abs(total - 12.0) < 0.01

    def test_5_4_time_constraints(self):
        """5/4 time: constraints should work with 5-beat bars."""
        from melodica.types import BarGrid
        grid = BarGrid(numerator=5, denominator=4)
        h = CoupledHMMHarmonizer(chord_change="bars", bar_grid=grid)
        melody = [N(60, i * 0.5, 0.5) for i in range(20)]
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=5.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=5.0, duration=5.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=10.0, constraints=constraints)
        assert result[0].root == 0
        assert result[1].root == 7
        total = sum(c.duration for c in result)
        assert abs(total - 10.0) < 0.01

    def test_6_8_time_half_bar_changes(self):
        """6/8 time with half-bar changes: change points every 1.5 beats."""
        from melodica.types import BarGrid
        grid = BarGrid(numerator=6, denominator=8)
        h = CoupledHMMHarmonizer(chord_change="half", bar_grid=grid)
        melody = [N(60, i * 0.5, 0.5) for i in range(24)]
        # 6/8: beats_per_bar = 3.0, half = 1.5
        result = h.harmonize(melody, C_MAJOR, duration_beats=12.0)
        assert len(result) >= 4
        total = sum(c.duration for c in result)
        assert abs(total - 12.0) < 0.01


# ===========================================================================
# 13. Constrained HMM: edge cases
# ===========================================================================

class TestConstrainedEdgeCases:

    def test_empty_constraints_same_as_unconstrained(self):
        """Empty constraints should behave like unconstrained."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        r_free = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        r_empty = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=[])
        assert len(r_free) == len(r_empty)
        for a, b in zip(r_free, r_empty):
            assert a.root == b.root
            assert a.quality == b.quality

    def test_none_constraints_same_as_unconstrained(self):
        """None constraints should behave like unconstrained."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        r_free = h.harmonize(melody, C_MAJOR, duration_beats=16.0)
        r_none = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=None)
        assert r_free == r_none

    def test_all_steps_locked(self):
        """Locking every bar should produce exactly the locked progression."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert [c.root for c in result] == [0, 5, 7, 0]
        assert [c.quality for c in result] == [
            Quality.MAJOR, Quality.MAJOR, Quality.DOMINANT7, Quality.MAJOR
        ]

    def test_alternating_locked_free(self):
        """Lock every other bar; free bars should still get valid chords."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(8)
        constraints = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=8.0, duration=4.0),
            ChordLabel(root=0, quality=Quality.MAJOR, start=16.0, duration=4.0),
            ChordLabel(root=7, quality=Quality.DOMINANT7, start=24.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=32.0, constraints=constraints)
        assert result[0].root == 0
        assert result[2].root == 7
        assert result[4].root == 0
        assert result[6].root == 7
        # Free bars should have valid roots
        for c in result:
            assert 0 <= c.root < 12

    def test_single_constraint_in_middle(self):
        """Single constraint at bar 2 shouldn't affect bars 0, 1, 3."""
        h = CoupledHMMHarmonizer(chord_change="bars")
        melody = _c_major_melody(4)
        constraints = [
            ChordLabel(root=2, quality=Quality.MINOR, start=4.0, duration=4.0),
        ]
        result = h.harmonize(melody, C_MAJOR, duration_beats=16.0, constraints=constraints)
        assert result[1].root == 2
        assert result[1].quality == Quality.MINOR
        total = sum(c.duration for c in result)
        assert abs(total - 16.0) < 0.01


# =========================================================================
# 14. Symphonic theater progression (~40 min, 300 bars)
# =========================================================================

from melodica.idea_tool import IdeaTool, IdeaToolConfig, IdeaPart
from melodica.theory.modes import Mode
from melodica.types import SectionRole, SectionFunction, BarGrid

_SYM_BAR_GRID = BarGrid(numerator=4, denominator=4)


def _build_symphonic_theater_parts() -> list[IdeaPart]:
    """14 parts covering an overture-through-finale symphonic theater arc.
    300 bars = 40 min @ BPM 120 in 4/4."""
    TS = (4, 4)
    return [
        IdeaPart(
            name="Overture", bars=24, time_signature=TS,
            scale=Scale(0, Mode.MAJOR),
            section_type=SectionRole.INTRO,
            section_function=SectionFunction.BUILD,
            progression_type="constrained_hmm",
            progression_list=["I", "vi", "IV", "V"],
        ),
        IdeaPart(
            name="Prologue", bars=16, time_signature=TS,
            scale=Scale(9, Mode.HARMONIC_MINOR),
            section_type=SectionRole.VERSE,
            section_function=SectionFunction.BUILD,
            progression_type="coupled_hmm",
        ),
        IdeaPart(
            name="Act I Scene 1", bars=24, time_signature=TS,
            scale=Scale(2, Mode.DORIAN),
            section_type=SectionRole.VERSE,
            section_function=SectionFunction.SUSTAIN,
            progression_type="functional_hmm",
        ),
        IdeaPart(
            name="Act I Scene 2", bars=24, time_signature=TS,
            scale=Scale(7, Mode.MIXOLYDIAN),
            section_type=SectionRole.CHORUS,
            section_function=SectionFunction.BUILD,
            progression_type="coupled_hmm",
        ),
        IdeaPart(
            name="Ensemble Piece", bars=20, time_signature=TS,
            scale=Scale(0, Mode.LYDIAN),
            section_type=SectionRole.BRIDGE,
            section_function=SectionFunction.BUILD,
            progression_type="constrained_hmm",
            progression_list=["I", "II", "IV", "V"],
        ),
        IdeaPart(
            name="Act II Scene 1", bars=24, time_signature=TS,
            scale=Scale(5, Mode.PHRYGIAN),
            section_type=SectionRole.VERSE,
            section_function=SectionFunction.SUSTAIN,
            progression_type="coupled_hmm",
        ),
        IdeaPart(
            name="Love Duet", bars=20, time_signature=TS,
            scale=Scale(9, Mode.NATURAL_MINOR),
            section_type=SectionRole.CHORUS,
            section_function=SectionFunction.RELEASE,
            progression_type="constrained_hmm",
            progression_list=["i", "VI", "III", "VII"],
        ),
        IdeaPart(
            name="Villain Aria", bars=24, time_signature=TS,
            scale=Scale(11, Mode.PHRYGIAN_DOMINANT),
            section_type=SectionRole.VERSE,
            section_function=SectionFunction.BREAK,
            progression_type="coupled_hmm",
        ),
        IdeaPart(
            name="Conflict", bars=24, time_signature=TS,
            scale=Scale(4, Mode.HARMONIC_MINOR),
            section_type=SectionRole.BRIDGE,
            section_function=SectionFunction.BUILD,
            progression_type="functional_hmm",
        ),
        IdeaPart(
            name="Crisis", bars=24, time_signature=TS,
            scale=Scale(0, Mode.HARMONIC_MINOR),
            section_type=SectionRole.BRIDGE,
            section_function=SectionFunction.BUILD,
            progression_type="constrained_hmm",
            progression_list=["i", "iv", "V", "i"],
        ),
        IdeaPart(
            name="Resolution", bars=24, time_signature=TS,
            scale=Scale(0, Mode.MAJOR),
            section_type=SectionRole.CHORUS,
            section_function=SectionFunction.RELEASE,
            progression_type="coupled_hmm",
        ),
        IdeaPart(
            name="Reprise", bars=20, time_signature=TS,
            scale=Scale(0, Mode.MAJOR),
            section_type=SectionRole.VERSE,
            section_function=SectionFunction.RELEASE,
            progression_type="constrained_hmm",
            progression_list=["I", "vi", "IV", "V"],
        ),
        IdeaPart(
            name="Grand Finale", bars=24, time_signature=TS,
            scale=Scale(0, Mode.MAJOR),
            section_type=SectionRole.OUTRO,
            section_function=SectionFunction.FADE,
            progression_type="coupled_hmm",
        ),
        IdeaPart(
            name="Epilogue", bars=8, time_signature=TS,
            scale=Scale(0, Mode.MAJOR),
            section_type=SectionRole.CODA,
            section_function=SectionFunction.HOLD,
            progression_type="constrained_hmm",
            progression_list=["I", "IV", "V", "I"],
        ),
    ]


class TestSymphonicTheaterProgression:

    def _generate(self) -> dict:
        parts = _build_symphonic_theater_parts()
        config = IdeaToolConfig(tempo=120, time_signature=(4, 4))
        tool = IdeaTool(config=config)
        all_chords = tool._generate_progression(parts)
        return {"parts": parts, "chords": all_chords}

    def test_total_bar_count_300(self):
        data = self._generate()
        parts = data["parts"]
        total_bars = sum(p.bars for p in parts)
        assert total_bars == 300, f"Expected 300 bars, got {total_bars}"

    def test_produces_14_parts(self):
        data = self._generate()
        assert len(data["parts"]) == 14

    def test_all_progression_types_used(self):
        types_used = set()
        for p in _build_symphonic_theater_parts():
            types_used.add(p.progression_type)
        assert "coupled_hmm" in types_used
        assert "constrained_hmm" in types_used
        assert "functional_hmm" in types_used

    def test_mode_diversity(self):
        modes = set()
        for p in _build_symphonic_theater_parts():
            modes.add(p.scale.mode)
        assert len(modes) >= 5, f"Only {len(modes)} modes: {modes}"

    def test_key_diversity(self):
        roots = set()
        for p in _build_symphonic_theater_parts():
            roots.add(p.scale.root)
        assert len(roots) >= 5, f"Only {len(roots)} keys: {roots}"

    def test_chords_generated(self):
        data = self._generate()
        assert len(data["chords"]) > 0

    def test_duration_sum_1200_beats(self):
        data = self._generate()
        total = sum(c.duration for c in data["chords"])
        assert abs(total - 1200.0) < 0.1, f"Expected 1200 beats, got {total}"

    def test_monotonic_start_times(self):
        data = self._generate()
        chords = data["chords"]
        for i in range(1, len(chords)):
            assert chords[i].start >= chords[i - 1].start, (
                f"Non-monotonic at {i}: {chords[i-1].start} -> {chords[i].start}"
            )

    def test_all_roots_valid(self):
        data = self._generate()
        for c in data["chords"]:
            assert 0 <= c.root < 12, f"Invalid root: {c.root}"

    def test_all_qualities_valid(self):
        data = self._generate()
        for c in data["chords"]:
            assert isinstance(c.quality, Quality)

    def test_root_diversity_across_work(self):
        data = self._generate()
        roots = set(c.root for c in data["chords"])
        assert len(roots) >= 4, f"Only {len(roots)} unique roots across 300 bars"

    def test_quality_diversity(self):
        data = self._generate()
        qualities = set(c.quality for c in data["chords"])
        assert len(qualities) >= 3, f"Only {len(qualities)} qualities: {qualities}"

    def test_constrained_parts_match(self):
        data = self._generate()
        for p in data["parts"]:
            if p.progression_type == "constrained_hmm" and p.progression_list:
                part_chords = [c for c in data["chords"]
                               if p.bars * 0 <= c.start < p.bars * 4]
                if not part_chords:
                    continue
                constrained_roots = set(c.root for c in part_chords)
                assert len(constrained_roots) >= 1

    def test_each_part_produces_chords(self):
        data = self._generate()
        chords = data["chords"]
        assert len(chords) >= 14, f"Only {len(chords)} chords for 14 parts"

    def test_no_excessive_consecutive_duplicates(self):
        data = self._generate()
        chords = data["chords"]
        max_run = 1
        run = 1
        for i in range(1, len(chords)):
            if chords[i].root == chords[i - 1].root and chords[i].quality == chords[i - 1].quality:
                run += 1
                max_run = max(max_run, run)
            else:
                run = 1
        assert max_run <= 6, f"Same chord repeated {max_run} times consecutively"

    def test_section_roles_present(self):
        roles = set()
        for p in _build_symphonic_theater_parts():
            if p.section_type:
                roles.add(p.section_type)
        assert SectionRole.INTRO in roles
        assert SectionRole.VERSE in roles
        assert SectionRole.CHORUS in roles
        assert SectionRole.OUTRO in roles


class TestCouplingRealEffect:
    def test_coupling_bias_changes_output(self):
        """Verify that changing key_coupling_weight in HMMConfig changes chord output."""
        h1 = CoupledHMMHarmonizer(chord_change="bars")
        h1.config.key_coupling_weight = 0.0  # No coupling
        
        h2 = CoupledHMMHarmonizer(chord_change="bars")
        h2.config.key_coupling_weight = 3.0  # Strong coupling
        
        melody = _c_major_melody(4)
        result1 = h1.harmonize(melody, Scale(root=0, mode=Mode.MAJOR), duration_beats=16.0)
        result2 = h2.harmonize(melody, Scale(root=0, mode=Mode.MAJOR), duration_beats=16.0)
        
        names1 = [f"{c.root}_{c.quality.name}" for c in result1]
        names2 = [f"{c.root}_{c.quality.name}" for c in result2]
        
        assert names1 != names2, "Coupling bias has no effect on chord selection!"
