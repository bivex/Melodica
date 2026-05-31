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


# ------------------------------------------------------------------
# Tests for 11 new transforms
# ------------------------------------------------------------------

class TestTransposeDiatonic:
    def test_shifts_by_degrees(self):
        from melodica.types_pkg._theory import Scale, Mode
        m = Motif.from_notes([NoteInfo(pitch=60, start=0, duration=1, velocity=60)])
        sc = Scale(root=0, mode=Mode.MAJOR)
        t = m.transpose_diatonic(2, sc)
        # C major: C D E F G A B → 2 degrees up from C = E (64)
        assert t.notes[0].pitch == 64

    def test_negative_degrees(self):
        from melodica.types_pkg._theory import Scale, Mode
        m = Motif.from_notes([NoteInfo(pitch=64, start=0, duration=1, velocity=60)])
        sc = Scale(root=0, mode=Mode.MAJOR)
        t = m.transpose_diatonic(-1, sc)
        # E down 1 degree in C major = D (62)
        assert t.notes[0].pitch == 62


class TestInvertDiatonic:
    def test_mirror_within_scale(self):
        from melodica.types_pkg._theory import Scale, Mode
        m = Motif.from_notes([NoteInfo(pitch=60, start=0, duration=1, velocity=60)])
        sc = Scale(root=0, mode=Mode.MAJOR)
        inv = m.invert_diatonic(sc, axis_degree=0)
        # C at degree 0, mirrored around degree 0 → still C
        assert inv.notes[0].pitch == 60


class TestDisplace:
    def test_shifts_start_times(self):
        m = Motif.from_notes(_make_notes())
        d = m.displace(5.0)
        assert d.notes[0].start == pytest.approx(5.0)
        assert d.notes[2].start == pytest.approx(7.0)

    def test_preserves_pitches(self):
        m = Motif.from_notes(_make_notes())
        d = m.displace(5.0)
        assert [n.pitch for n in d.notes] == [60, 64, 67]


class TestTruncateHead:
    def test_removes_first_n(self):
        m = Motif.from_notes(_make_notes())
        t = m.truncate_head(1)
        pitches = [n.pitch for n in t.notes]
        assert 60 not in pitches
        assert len(pitches) == 2

    def test_removes_all(self):
        m = Motif.from_notes(_make_notes())
        t = m.truncate_head(5)
        assert t.notes == []


class TestTruncateTail:
    def test_removes_last_n(self):
        m = Motif.from_notes(_make_notes())
        t = m.truncate_tail(1)
        pitches = [n.pitch for n in t.notes]
        assert 67 not in pitches
        assert len(pitches) == 2

    def test_zero_removes_nothing(self):
        m = Motif.from_notes(_make_notes())
        t = m.truncate_tail(0)
        assert len(t.notes) == 3


class TestExpand:
    def test_stretches_gaps(self):
        m = Motif.from_notes(_make_notes())
        e = m.expand(2.0)
        # Original: starts at 0, 1, 2 → doubled gaps: 0, 2, 4
        assert e.notes[0].start == pytest.approx(0.0)
        assert e.notes[1].start == pytest.approx(2.0)
        assert e.notes[2].start == pytest.approx(4.0)

    def test_preserves_durations(self):
        m = Motif.from_notes(_make_notes())
        e = m.expand(3.0)
        assert e.notes[0].duration == pytest.approx(1.0)

    def test_bad_factor(self):
        m = Motif.from_notes(_make_notes())
        with pytest.raises(ValueError):
            m.expand(0)


class TestOrnament:
    def test_grace_note(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        m = Motif.from_notes([NoteInfo(pitch=60, start=0, duration=2.0, velocity=70)])
        o = m.ornament("grace", sc)
        # Should produce grace + main note
        assert len(o.notes) == 2
        assert o.notes[0].pitch == 61  # Upper neighbor
        assert o.notes[0].duration < 2.0

    def test_neighbor(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        m = Motif.from_notes([NoteInfo(pitch=60, start=0, duration=1.0, velocity=70)])
        o = m.ornament("neighbor", sc)
        assert len(o.notes) >= 1

    def test_unknown_style_raises(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        m = Motif.from_notes(_make_notes())
        with pytest.raises(ValueError, match="Unknown ornament style"):
            m.ornament("nonexistent", sc)


class TestCanon:
    def test_two_voices(self):
        m = Motif.from_notes(_make_notes())
        c = m.canon(voices=2, delay=4.0, intervals=[0, 7])
        assert len(c.notes) == 6

    def test_single_voice(self):
        m = Motif.from_notes(_make_notes())
        c = m.canon(voices=1, delay=4.0, intervals=[0])
        assert len(c.notes) == 3


class TestWithPedal:
    def test_adds_pedal(self):
        m = Motif.from_notes(_make_notes())
        p = m.with_pedal(36)
        assert len(p.notes) == 4
        pedal = p.notes[-1]
        assert pedal.pitch == 36
        assert pedal.velocity == 60

    def test_pedal_spans_motif(self):
        m = Motif.from_notes(_make_notes())
        p = m.with_pedal(36)
        pedal = p.notes[-1]
        assert pedal.duration >= 3.0

    def test_empty_motif(self):
        m = Motif.from_notes([])
        p = m.with_pedal(36)
        assert p.notes == []


class TestHumanize:
    def test_preserves_note_count(self):
        m = Motif.from_notes(_make_notes())
        h = m.humanize()
        assert len(h.notes) == 3

    def test_preserves_pitches(self):
        m = Motif.from_notes(_make_notes())
        h = m.humanize(timing=0.0, velocity=0.0)
        pitches = [n.pitch for n in h.notes]
        assert pitches == [60, 64, 67]


class TestDevelopNewKwargs:
    def test_truncate_in_chain(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(truncate_head_n=1)
        assert len(d.notes) == 2

    def test_displace_in_chain(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(displace_beats=10.0)
        assert d.notes[0].start == pytest.approx(10.0)

    def test_expand_in_chain(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(expand_factor=2.0)
        assert d.notes[1].start == pytest.approx(2.0)

    def test_pedal_in_chain(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(pedal_pitch=36)
        assert len(d.notes) == 4

    def test_full_chain(self):
        m = Motif.from_notes(_make_notes())
        d = m.develop(
            retrograde=True,
            transpose=5,
            augment_factor=2.0,
            displace_beats=3.0,
        )
        assert len(d.notes) == 3
        # retrograde reverses (last note first, start=2), augment*2 → start=4, displace+3 → 7
        assert d.notes[0].start == pytest.approx(7.0)
