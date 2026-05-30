"""Tests for melodica.composer.motif.Motif"""

import pytest

from melodica.types_pkg._notes import NoteInfo
from melodica.composer.motif import Motif


def _make_notes() -> list[NoteInfo]:
    """C4-E4 ascending triad, quarter notes starting at beat 0."""
    return [
        NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
        NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80),
        NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=80),
    ]


class TestFromNotesAndRender:
    def test_round_trip(self):
        notes = _make_notes()
        m = Motif.from_notes(notes)
        result = m.render()
        assert len(result) == 3
        assert result[0].pitch == 60
        assert result[0].start == 0.0
        assert result[2].pitch == 67
        assert result[2].start == 2.0

    def test_origin_shift(self):
        notes = _make_notes()
        m = Motif.from_notes(notes, origin=10.0)
        result = m.render()
        assert result[0].start == 10.0
        assert result[2].start == 12.0

    def test_render_with_offset(self):
        notes = _make_notes()
        m = Motif.from_notes(notes, origin=5.0)
        result = m.render(offset=3.0)
        assert result[0].start == pytest.approx(8.0)


class TestTranspose:
    def test_up_octave(self):
        m = Motif.from_notes(_make_notes())
        t = m.transpose(12)
        result = t.render()
        assert result[0].pitch == 72
        assert result[2].pitch == 79

    def test_down(self):
        m = Motif.from_notes(_make_notes())
        t = m.transpose(-2)
        assert t.render()[0].pitch == 58


class TestInvert:
    def test_default_center(self):
        m = Motif.from_notes(_make_notes())
        inv = m.invert()
        pitches = [n.pitch for n in inv.render()]
        assert pitches[0] == 67
        assert pitches[2] == 60

    def test_explicit_center(self):
        m = Motif.from_notes(_make_notes())
        inv = m.invert(center=64)
        assert inv.render()[0].pitch == 68  # 2*64 - 60

    def test_empty(self):
        m = Motif.from_notes([])
        assert m.invert().render() == []


class TestRetrograde:
    def test_reverse_order(self):
        m = Motif.from_notes(_make_notes())
        ret = m.retrograde()
        pitches = [n.pitch for n in ret.notes]
        assert pitches == [67, 64, 60]

    def test_empty(self):
        assert Motif.from_notes([]).retrograde().render() == []


class TestAugmentDiminish:
    def test_augment_double(self):
        m = Motif.from_notes(_make_notes())
        a = m.augment(2.0)
        notes = a.notes
        assert notes[0].duration == pytest.approx(2.0)
        assert notes[1].start == pytest.approx(2.0)

    def test_diminish_half(self):
        m = Motif.from_notes(_make_notes())
        d = m.diminish(2.0)
        notes = d.notes
        assert notes[0].duration == pytest.approx(0.5)
        assert notes[1].start == pytest.approx(0.5)

    def test_bad_factor(self):
        m = Motif.from_notes(_make_notes())
        with pytest.raises(ValueError):
            m.augment(0)
        with pytest.raises(ValueError):
            m.diminish(-1)


class TestSequence:
    def test_one_interval(self):
        m = Motif.from_notes(_make_notes())
        seq = m.sequence([7])
        result = seq.render()
        assert len(result) == 6
        assert result[3].pitch == 67

    def test_custom_spacing(self):
        m = Motif.from_notes(_make_notes())
        seq = m.sequence([5], spacing=10.0)
        result = seq.render()
        assert result[3].start > 3.0

    def test_empty_intervals(self):
        m = Motif.from_notes(_make_notes())
        seq = m.sequence([])
        assert len(seq.render()) == 3


class TestFragment:
    def test_subset(self):
        m = Motif.from_notes(_make_notes())
        frag = m.fragment(start_beat=0.5, end_beat=2.5)
        pitches = [n.pitch for n in frag.notes]
        assert 64 in pitches
        assert 60 not in pitches or len(pitches) <= 2

    def test_full_range(self):
        m = Motif.from_notes(_make_notes())
        frag = m.fragment(start_beat=0.0, end_beat=10.0)
        assert len(frag.notes) == 3


class TestDevelop:
    def test_chain_retrograde_transpose(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(retrograde=True, transpose=12)
        pitches = [n.pitch for n in d.notes]
        assert pitches[0] == 79
        assert pitches[2] == 72

    def test_chain_fragment_invert(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(fragment_start=0.5, fragment_end=2.5, invert=True)
        assert len(d.notes) >= 1

    def test_empty_develop(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop()
        assert len(d.render()) == 3


class TestImmutability:
    def test_transpose_does_not_mutate(self):
        m = Motif.from_notes(_make_notes())
        original_pitches = [n.pitch for n in m.notes]
        m.transpose(12)
        assert [n.pitch for n in m.notes] == original_pitches

    def test_invert_does_not_mutate(self):
        m = Motif.from_notes(_make_notes())
        original_pitches = [n.pitch for n in m.notes]
        m.invert()
        assert [n.pitch for n in m.notes] == original_pitches

    def test_retrograde_does_not_mutate(self):
        m = Motif.from_notes(_make_notes())
        original_pitches = [n.pitch for n in m.notes]
        m.retrograde()
        assert [n.pitch for n in m.notes] == original_pitches
