"""Tests for melodica.composer.leitmotif.LeitmotifRegistry"""

import pytest

from melodica.composer.motif import Motif
from melodica.composer.leitmotif import Leitmotif, LeitmotifRegistry
from melodica.types_pkg._notes import NoteInfo


def _make_motif(pitches=None):
    pitches = pitches or [60, 64, 67, 72, 67]
    notes = [
        NoteInfo(pitch=p, start=float(i), duration=1.0, velocity=70)
        for i, p in enumerate(pitches)
    ]
    return Motif.from_notes(notes)


class TestRegisterAndGet:
    def test_register_and_get(self):
        reg = LeitmotifRegistry()
        motif = _make_motif()
        entry = reg.register("hero", motif, tags=["protagonist"])
        assert entry.name == "hero"
        assert reg.get("hero") is entry

    def test_get_nonexistent(self):
        reg = LeitmotifRegistry()
        assert reg.get("villain") is None


class TestByTag:
    def test_filter_by_tag(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif(), tags=["protagonist", "brave"])
        reg.register("villain", _make_motif(), tags=["antagonist"])
        reg.register("love", _make_motif(), tags=["protagonist", "tender"])
        result = reg.by_tag("protagonist")
        assert len(result) == 2
        names = {e.name for e in result}
        assert names == {"hero", "love"}

    def test_no_match(self):
        reg = LeitmotifRegistry()
        assert reg.by_tag("missing") == []


class TestRender:
    def test_render_plain(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero")
        assert len(notes) == 5
        assert notes[0].pitch == 60

    def test_render_with_offset(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", offset=10.0)
        assert notes[0].start >= 10.0

    def test_render_transpose(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", transpose=7)
        assert notes[0].pitch == 67  # 60 + 7

    def test_render_invert(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", invert=True)
        # Inverted motif should have different pitches
        original = reg.render("hero")
        assert notes[0].pitch != original[0].pitch

    def test_render_retrograde(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", retrograde=True)
        # Retrograde: last note's pitch becomes first
        original = reg.render("hero")
        assert notes[0].pitch == original[-1].pitch

    def test_render_nonexistent(self):
        reg = LeitmotifRegistry()
        assert reg.render("ghost") == []

    def test_render_augment(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", augment_factor=2.0)
        original = reg.render("hero")
        # Augmented: durations should be doubled
        assert notes[0].duration == pytest.approx(original[0].duration * 2.0)

    def test_render_fragment(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", fragment_start=0.0, fragment_end=2.0)
        # Fragment should have fewer notes (only those starting in [0, 2))
        assert len(notes) <= 3


class TestRenderAll:
    def test_render_all(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif([60, 64, 67]))
        reg.register("villain", _make_motif([55, 58, 62]))
        notes = reg.render_all()
        assert len(notes) >= 6  # 3 from each

    def test_render_all_by_tag(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif(), tags=["protagonist"])
        reg.register("villain", _make_motif(), tags=["antagonist"])
        notes = reg.render_all(tag="protagonist")
        # Only hero motif should be rendered
        pitches = {n.pitch for n in notes}
        assert 60 in pitches  # hero starts at 60

    def test_render_all_sorted(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        reg.register("villain", _make_motif())
        notes = reg.render_all()
        starts = [n.start for n in notes]
        assert starts == sorted(starts)
