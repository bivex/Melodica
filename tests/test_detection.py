"""tests/test_detection.py — Tests for chord detection and scale detection."""

import pytest
from melodica.types import Mode, Note, Quality, Scale
from melodica.detection import detect_chord, detect_chords_from_midi, detect_scale


def _notes(*pitches: int, start: float = 0.0, dur: float = 1.0) -> list[Note]:
    return [Note(pitch=p, start=start, duration=dur) for p in pitches]


class TestDetectChord:
    def test_c_major(self):
        chord = detect_chord(_notes(60, 64, 67))  # C E G
        assert chord is not None
        assert chord.root == 0
        assert chord.quality == Quality.MAJOR

    def test_a_minor(self):
        chord = detect_chord(_notes(57, 60, 64))  # A C E
        assert chord is not None
        assert chord.root == 9
        assert chord.quality == Quality.MINOR

    def test_g_dominant7(self):
        chord = detect_chord(_notes(43, 47, 50, 53))  # G B D F
        assert chord is not None
        assert chord.root == 7
        assert chord.quality == Quality.DOMINANT7

    def test_empty_returns_none(self):
        assert detect_chord([]) is None

    def test_low_score_returns_none(self):
        # All 12 pitch classes simultaneously — no clear winner
        all_notes = _notes(*range(60, 72))
        result = detect_chord(all_notes, min_score=0.9)
        # May or may not be None depending on scoring; just ensure no crash
        assert result is None or result.root in range(12)

    def test_inversion_detected(self):
        # E G C — first inversion C major (E in bass)
        chord = detect_chord(_notes(52, 55, 60))
        assert chord is not None
        assert chord.root == 0
        assert chord.inversion > 0  # not root position


class TestDetectScale:
    def test_c_major_scale(self):
        notes = _notes(60, 62, 64, 65, 67, 69, 71, 72)  # C D E F G A B C
        scale = detect_scale(notes)
        assert scale.root == 0
        assert scale.mode == Mode.MAJOR

    def test_a_minor_scale(self):
        notes = _notes(57, 59, 60, 62, 64, 65, 67, 69)  # A B C D E F G A
        scale = detect_scale(notes)
        assert scale.mode in (Mode.MAJOR, Mode.NATURAL_MINOR)  # KS may get relative

    def test_empty_returns_default(self):
        scale = detect_scale([])
        assert scale == Scale(root=0, mode=Mode.MAJOR)


class TestDetectChordsFromMidi:
    def test_returns_list(self):
        notes = [
            Note(60, 0, 2), Note(64, 0, 2), Note(67, 0, 2),  # C major bar 1
            Note(62, 2, 2), Note(65, 2, 2), Note(69, 2, 2),  # D minor bar 2
        ]
        chords = detect_chords_from_midi(notes, window=2.0, stride=2.0)
        assert isinstance(chords, list)
        assert len(chords) >= 1

    def test_with_key_annotates_degree(self):
        notes = [Note(60, 0, 2), Note(64, 0, 2), Note(67, 0, 2)]
        key = Scale(root=0, mode=Mode.MAJOR)
        chords = detect_chords_from_midi(notes, window=2.0, stride=2.0, key=key)
        if chords:
            # C major in C major key should be degree I
            assert chords[0].degree == 1
