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


# ------------------------------------------------------------------
# Tests for new LeitmotifRegistry capabilities
# ------------------------------------------------------------------

class TestVariants:
    def test_register_variant(self):
        reg = LeitmotifRegistry()
        m = _make_motif()
        reg.register("hero", m)
        variant = Motif.from_notes([
            NoteInfo(pitch=72, start=0.0, duration=1.0, velocity=70),
        ])
        reg.register_variant("hero", "high", variant)
        notes = reg.render("hero", variant="high")
        assert notes[0].pitch == 72

    def test_nonexistent_leitmotif_raises(self):
        reg = LeitmotifRegistry()
        with pytest.raises(KeyError):
            reg.register_variant("ghost", "v1", _make_motif())

    def test_default_variant_exists(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        entry = reg.get("hero")
        assert "default" in entry._variants


class TestEvolve:
    def test_evolve_creates_variant(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        result = reg.evolve("hero", "dark", transpose=-6, retrograde=True)
        assert result is not None
        entry = reg.get("hero")
        assert "dark" in entry._variants

    def test_evolve_logs(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        reg.evolve("hero", "dark", transpose=-6)
        entry = reg.get("hero")
        assert len(entry._evolution_log) == 1
        assert "dark" in entry._evolution_log[0]

    def test_evolve_from_variant(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        reg.evolve("hero", "v1", transpose=5)
        reg.evolve("hero", "v2", source_variant="v1", transpose=7)
        v2 = reg.get("hero")._variants["v2"]
        assert v2 is not None


class TestRenderFor:
    def test_mood_dark(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render_for("hero", "dark")
        assert len(notes) > 0
        # Dark: inverted + transposed down 6
        original = reg.render("hero")
        assert notes[0].pitch != original[0].pitch

    def test_mood_ethereal(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render_for("hero", "ethereal")
        # Ethereal: augment x3 + transpose +12
        assert notes[0].pitch == _make_motif().notes[0].pitch + 12

    def test_unknown_mood_falls_back(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render_for("hero", "unknown_mood")
        original = reg.render("hero")
        assert [n.pitch for n in notes] == [n.pitch for n in original]

    def test_intensity_scales(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        normal = reg.render_for("hero", "urgent", intensity=1.0)
        intense = reg.render_for("hero", "urgent", intensity=2.0)
        # Higher intensity = larger diminish factor = shorter durations
        assert intense[0].duration < normal[0].duration


class TestLayer:
    def test_layer_two_motifs(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif([60, 64, 67]))
        reg.register("villain", _make_motif([55, 58, 62]))
        notes = reg.layer(["hero", "villain"], [0.0, 10.0])
        assert len(notes) == 6
        starts = [n.start for n in notes]
        assert starts == sorted(starts)

    def test_layer_with_transforms(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif([60, 64, 67]))
        reg.register("villain", _make_motif([55, 58, 62]))
        notes = reg.layer(["hero", "villain"], [0.0, 0.0], transpose=7)
        assert all(n.pitch >= 62 for n in notes)


class TestCounterMotif:
    def test_generates_contrasting_motif(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        reg = LeitmotifRegistry()
        # Ascending motif: 60, 64, 67
        reg.register("hero", _make_motif([60, 64, 67]))
        counter = reg.counter_motif("hero", sc)
        counter_pitches = [n.pitch for n in counter.notes]
        # Inverted intervals: delta from first is negated
        # orig deltas: 0, +4, +7 → counter: 0, -4, -7 → 60, 56, 53
        assert counter_pitches == [60, 56, 53]
        assert counter_pitches[-1] <= counter_pitches[0]

    def test_custom_rhythm(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif([60, 64, 67]))
        counter = reg.counter_motif("hero", sc, rhythm_pattern=[2.0, 1.0, 0.5])
        durations = [n.duration for n in counter.notes]
        assert durations[0] == pytest.approx(2.0)

    def test_nonexistent_raises(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        reg = LeitmotifRegistry()
        with pytest.raises(KeyError):
            reg.counter_motif("ghost", sc)

    def test_empty_motif(self):
        from melodica.types_pkg._theory import Scale, Mode
        sc = Scale(root=0, mode=Mode.MAJOR)
        reg = LeitmotifRegistry()
        reg.register("empty", Motif.from_notes([]))
        counter = reg.counter_motif("empty", sc)
        assert counter.notes == []


class TestRenderVariant:
    def test_render_uses_variant(self):
        reg = LeitmotifRegistry()
        m = _make_motif()
        reg.register("hero", m)
        reg.evolve("hero", "bright", transpose=12)
        notes = reg.render("hero", variant="bright")
        assert notes[0].pitch >= 72  # Transposed up 12

    def test_render_fallback_to_default(self):
        reg = LeitmotifRegistry()
        reg.register("hero", _make_motif())
        notes = reg.render("hero", variant="nonexistent")
        original = reg.render("hero")
        assert [n.pitch for n in notes] == [n.pitch for n in original]
