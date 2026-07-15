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

import pytest
from melodica.utils import (
    semitones_up,
    interval_class,
    ascending_interval,
    descending_interval,
    nearest_pitch_below,
    nearest_pitch,
    chord_pitches_open,
    chord_pitches_spread,
    voice_leading_distance,
    pitch_classes_in_window,
    diatonic_transpose,
    compute_simplicity,
    chord_at,
    rebase_chords,
    build_guitar_voicing,
)
from melodica.types import ChordLabel, Quality, NoteInfo, Scale

def test_semitones_up():
    assert semitones_up(60, 4) == 64
    assert semitones_up(120, 10) == 127 # Clamped
    assert semitones_up(4, -10) == 0    # Clamped

def test_interval_class():
    assert interval_class(0, 4) == 4
    assert interval_class(4, 0) == 4
    assert interval_class(0, 11) == 1
    assert interval_class(11, 0) == 1
    assert interval_class(0, 7) == 5

def test_ascending_interval():
    assert ascending_interval(0, 4) == 4
    assert ascending_interval(11, 0) == 1
    assert ascending_interval(4, 4) == 0

def test_descending_interval():
    assert descending_interval(4, 0) == 4
    assert descending_interval(0, 11) == 1
    assert descending_interval(4, 4) == 0

def test_nearest_pitch_below():
    assert nearest_pitch_below(0, 60) == 60
    assert nearest_pitch_below(11, 60) == 59
    assert nearest_pitch_below(0, 5) == 0 # Truncated at 0 case, base = 0
    assert nearest_pitch_below(11, 5) == -1 # Cannot be < 0, returns -1

def test_nearest_pitch():
    # distance to 61 PC=0 (60) vs (72). 60 is closest
    assert nearest_pitch(0, 61) == 60
    # distance to 66: PC=0 -> 60 and 72. 66 is right in middle. Ties broken upward -> 72
    assert nearest_pitch(0, 66) == 72

def test_chord_pitches_open():
    c = ChordLabel(root=0, quality=Quality.MAJOR) # 3 notes
    open_p = chord_pitches_open(c, bass_midi=36)
    assert len(open_p) == 3

    # Small chord length < 3
    c_small = ChordLabel(root=0, quality=Quality.POWER)
    open_small = chord_pitches_open(c_small, bass_midi=36)
    assert len(open_small) == 2

def test_chord_pitches_spread():
    c = ChordLabel(root=0, quality=Quality.MAJOR)
    spread = chord_pitches_spread(c, bass_midi=36)
    assert len(spread) == 3

    c_empty = ChordLabel(root=0, quality=Quality.MAJOR)
    # mock pitch classes empty explicitly
    c_empty.pitch_classes = lambda: []
    assert chord_pitches_spread(c_empty) == []

def test_voice_leading_distance():
    # empty predecessor -> no motion
    assert voice_leading_distance([], [60, 64, 67]) == 0.0
    # backward-compatible value (identity assignment is optimal here)
    assert voice_leading_distance([60, 64, 67], [62, 65, 69]) == 2.0 + 1.0 + 2.0

    # bijectivity: greedy would double-assign 67 and report 5; the true
    # bijective optimum over permutations is 12.
    prev, nxt = [60, 64, 67], [64, 67, 72]
    assert voice_leading_distance(prev, nxt) == 12.0
    # symmetry: a true voice-leading distance is symmetric
    assert voice_leading_distance(nxt, prev) == 12.0

    # pitch-class equivalence: C4 -> C5 is zero motion mod 12
    assert voice_leading_distance([60], [72], equivalence="pitch_class") == 0.0
    assert voice_leading_distance([60], [72], equivalence="register") == 12.0

    # norm variants on [60,64] -> [61,67]: identity assignment 1+3
    assert voice_leading_distance([60, 64], [61, 67], norm="L1") == 4.0
    assert voice_leading_distance([60, 64], [61, 67], norm="L2") == (1 + 9) ** 0.5
    assert voice_leading_distance([60, 64], [61, 67], norm="Linf") == 3.0

    # bass_anchored prevents crossing under pitch-class wraparound:
    # prev=[6,11] -> next=[2,4]; free optimum crosses (5), anchored bass->bass (9)
    assert voice_leading_distance([6, 11], [2, 4], equivalence="pitch_class") == 5.0
    assert voice_leading_distance(
        [6, 11], [2, 4], equivalence="pitch_class", bass_anchored=True
    ) == 9.0

def test_pitch_classes_in_window():
    n1 = NoteInfo(pitch=60, start=0.0, duration=1.0)
    n2 = NoteInfo(pitch=64, start=0.5, duration=1.0)
    
    # Overlaps n1
    assert pitch_classes_in_window([n1, n2], 0.0, 0.4) == {0}
    # Overlaps n1 and n2
    assert pitch_classes_in_window([n1, n2], 0.6, 0.8) == {0, 4}
    # Overlaps neither
    assert pitch_classes_in_window([n1, n2], 2.0, 3.0) == set()

def test_diatonic_transpose():
    from melodica.types import Mode
    c_major = Scale(root=0, mode=Mode.MAJOR)
    g_major = Scale(root=7, mode=Mode.MAJOR) # Actually G major is G A B C D E F#
    
    # Absolute note should return unchanged
    absolute_note = NoteInfo(pitch=60, start=0.0, duration=1.0, absolute=True)
    assert diatonic_transpose(absolute_note, c_major, g_major).pitch == 60
    
    # Diatonic transposition: C (degree 0) in C major -> G (degree 0) in G major
    # C major: C D E F  G A B
    # G major: G A B C  D E F#
    
    # Let's say we have C (60) in C major, want it in G major.
    # C = degree 0 in C major. Degree 0 in G major is G (67).
    # Wait, 60 // 12 = 5. Octave 5, so 5 * 12 + PC = 60 + 7 = 67.
    n_c = NoteInfo(pitch=60, start=0.0, duration=1.0, absolute=False)
    n_g = diatonic_transpose(n_c, c_major, g_major)
    # It should map to G, which is pitch class 7. 60//12 * 12 + 7 = 67.
    assert n_g.pitch == 67

    # Chromatic transposition
    # Gb (pitch class 6) in C major. C major has no Gb.
    # It will fallback to chromatic formula: new_pitch = semitones_up(66, (7-0)%12)
    # 66 + 7 = 73
    n_chromatic = NoteInfo(pitch=66, start=0.0, duration=1.0, absolute=False)
    n_transposed_chromatic = diatonic_transpose(n_chromatic, c_major, g_major)
    assert n_transposed_chromatic.pitch == 73

def test_compute_simplicity():
    # major: [0, 4, 7]
    c = ChordLabel(root=0, quality=Quality.MAJOR)
    assert compute_simplicity(c) == 1.0

    # minor 7: [0, 3, 7] + extension 10
    c_min7 = ChordLabel(root=0, quality=Quality.MINOR7)
    # triade + 1 ext. penalty for minor 7th (ic 10) is 0.2
    # score = 1.0 - 0.2 = 0.8. i > 0 is false.
    assert compute_simplicity(c_min7) == 0.8

    # with more extensions
    c_ext = ChordLabel(root=0, quality=Quality.DOMINANT7)
    c_ext.extensions.append(2) # add major 9th
    # triad: 0, 4, 7
    # extra tones: 10 (minor 7 from dom7), 2 (from extensions)
    # penalty for 10 is 0.2
    # penalty for 2 is 0.4
    # i=0: score -= 0.2 (=0.8)
    # i=1: score -= 0.4 (=0.4), score -= 0.1 (=0.3)
    s = compute_simplicity(c_ext)
    # Expected approx 0.3
    import math
    assert math.isclose(s, 0.3, abs_tol=0.01)


def test_chord_at():
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=2.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=2.0, duration=2.0),
    ]
    assert chord_at(chords, 0.0).root == 0
    assert chord_at(chords, 1.5).root == 0
    assert chord_at(chords, 2.0).root == 5
    assert chord_at(chords, 3.5).root == 5
    assert chord_at([], 0.0) is None


def test_chord_at_localized_slice():
    # A section slice keeps global .start (32, 36, ...) but is queried in local
    # beats (0..16). chord_at must resolve against the slice's own origin instead
    # of silently returning None — the section-rendering footgun.
    slc = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=32.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=36.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=40.0, duration=4.0),
    ]
    assert chord_at(slc, 0.0).root == 0   # was None before the fix
    assert chord_at(slc, 3.9).root == 0
    assert chord_at(slc, 4.0).root == 5
    assert chord_at(slc, 9.5).root == 7
    assert chord_at(slc, 99.0).root == 7  # beyond slice → clamps to last


def test_rebase_chords_shifts_and_does_not_mutate():
    orig = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=32.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=36.0, duration=4.0),
    ]
    rebased = rebase_chords(orig, -32.0)
    assert [c.start for c in rebased] == [0.0, 4.0]      # shifted to local time
    assert [c.start for c in orig] == [32.0, 36.0]        # input untouched
    assert all(r is not o for r, o in zip(rebased, orig))  # shallow copies
    # rebased slice now resolves with plain absolute matching
    assert chord_at(rebased, 0.0).root == 0
    assert chord_at(rebased, 4.0).root == 5


def test_build_guitar_voicing():
    chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=1.0)
    voicing = build_guitar_voicing(chord)
    assert len(voicing) >= 4  # min_voices=4 by default
    assert all(0 <= p <= 127 for p in voicing)
    # Voicing should be sorted ascending
    assert voicing == sorted(voicing)
