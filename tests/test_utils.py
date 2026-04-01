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
    assert nearest_pitch_below(11, 5) == 0 # Cannot be < 0, max(0, base) -> 0

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
    assert voice_leading_distance([], [60, 64, 67]) == 0.0
    assert voice_leading_distance([60, 64, 67], [62, 65, 69]) == 2.0 + 1.0 + 2.0

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


def test_build_guitar_voicing():
    chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=1.0)
    voicing = build_guitar_voicing(chord)
    assert len(voicing) >= 4  # min_voices=4 by default
    assert all(0 <= p <= 127 for p in voicing)
    # Voicing should be sorted ascending
    assert voicing == sorted(voicing)
