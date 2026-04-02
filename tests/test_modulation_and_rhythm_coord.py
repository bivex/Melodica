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

"""
Tests for:
  - Modulation: per-section key changes in Composition/MusicDirector
  - RhythmCoordinator: shared rhythm grid across tracks in a section
"""
from __future__ import annotations

import pytest

from melodica.types import Scale, Mode
from melodica.render_context import RenderContext
from melodica.composition import Section, Composition, MusicDirector, _CoordinatedRhythm
from melodica.rhythm import EuclideanRhythmGenerator, RhythmCoordinator

# Presets confirmed to exist in presets/
_MELODY_PRESET = "lead_melody"
_BASS_PRESET = "melody_default"


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _make_composition(sections_spec: list[dict]) -> Composition:
    base_key = Scale(root=0, mode=Mode.MAJOR)
    comp = Composition(name="Test", key=base_key)
    for spec in sections_spec:
        comp.add_section(
            name=spec.get("name", "A"),
            duration=spec.get("duration", 4.0),
            progression=spec.get("progression", "I IV V I"),
            tracks=spec.get("tracks", {"Lead": _MELODY_PRESET}),
            key=spec.get("key", None),
            shared_rhythm=spec.get("shared_rhythm", None),
        )
    return comp


# ─────────────────────────────────────────────────────────────
# RenderContext: current_scale field
# ─────────────────────────────────────────────────────────────

class TestRenderContextScale:
    def test_default_current_scale_is_none(self):
        ctx = RenderContext()
        assert ctx.current_scale is None

    def test_with_end_state_threads_current_scale(self):
        key = Scale(root=9, mode=Mode.NATURAL_MINOR)
        ctx = RenderContext()
        ctx2 = ctx.with_end_state(current_scale=key)
        assert ctx2.current_scale == key

    def test_with_end_state_preserves_existing_scale_when_not_overridden(self):
        key = Scale(root=5, mode=Mode.MAJOR)
        ctx = RenderContext(current_scale=key)
        ctx2 = ctx.with_end_state(last_pitch=60)
        assert ctx2.current_scale == key

    def test_with_end_state_replaces_scale(self):
        key_a = Scale(root=0, mode=Mode.MAJOR)
        key_b = Scale(root=2, mode=Mode.DORIAN)
        ctx = RenderContext(current_scale=key_a)
        ctx2 = ctx.with_end_state(current_scale=key_b)
        assert ctx2.current_scale == key_b


# ─────────────────────────────────────────────────────────────
# Section: new fields
# ─────────────────────────────────────────────────────────────

class TestSectionNewFields:
    def test_section_key_defaults_to_none(self):
        s = Section(name="Verse", duration_beats=8.0, progression="I V", tracks={})
        assert s.key is None

    def test_section_shared_rhythm_defaults_to_none(self):
        s = Section(name="Chorus", duration_beats=8.0, progression="I", tracks={})
        assert s.shared_rhythm is None

    def test_section_accepts_key_override(self):
        key = Scale(root=9, mode=Mode.NATURAL_MINOR)
        s = Section(name="Bridge", duration_beats=4.0, progression="Im", tracks={}, key=key)
        assert s.key == key

    def test_section_accepts_shared_rhythm(self):
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        s = Section(name="Drop", duration_beats=8.0, progression="I", tracks={}, shared_rhythm=rgen)
        assert s.shared_rhythm is rgen


# ─────────────────────────────────────────────────────────────
# Composition.add_section: new kwargs forwarded
# ─────────────────────────────────────────────────────────────

class TestCompositionAddSection:
    def test_add_section_with_key(self):
        comp = Composition(name="T", key=Scale(root=0, mode=Mode.MAJOR))
        new_key = Scale(root=7, mode=Mode.MAJOR)
        comp.add_section("B", 8.0, "I V", {"Lead": _MELODY_PRESET}, key=new_key)
        assert comp.sections[-1].key == new_key

    def test_add_section_with_shared_rhythm(self):
        comp = Composition(name="T", key=Scale(root=0, mode=Mode.MAJOR))
        rgen = EuclideanRhythmGenerator(hits_per_bar=8)
        comp.add_section("D", 8.0, "I", {"Lead": _MELODY_PRESET}, shared_rhythm=rgen)
        assert comp.sections[-1].shared_rhythm is rgen

    def test_add_section_without_new_kwargs_still_works(self):
        comp = Composition(name="T", key=Scale(root=0, mode=Mode.MAJOR))
        comp.add_section("A", 4.0, "I IV", {"Lead": _MELODY_PRESET})
        assert comp.sections[-1].key is None
        assert comp.sections[-1].shared_rhythm is None


# ─────────────────────────────────────────────────────────────
# Modulation: MusicDirector uses per-section key
# ─────────────────────────────────────────────────────────────

class TestModulation:
    def test_single_section_no_override_uses_composition_key(self):
        comp = _make_composition([{"name": "Intro", "progression": "I V I"}])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        # index 0 = global stub; index 1 = first (and only) section key
        assert arr.timeline.keys[1].scale == comp.key

    def test_section_key_override_changes_timeline_key(self):
        new_key = Scale(root=9, mode=Mode.NATURAL_MINOR)
        comp = _make_composition([
            {"name": "Verse", "progression": "I IV V I"},
            {"name": "Bridge", "progression": "Im IVm Vm Im", "key": new_key},
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert arr.timeline.keys[2].scale == new_key

    def test_multiple_key_changes(self):
        c_major = Scale(root=0, mode=Mode.MAJOR)
        g_major = Scale(root=7, mode=Mode.MAJOR)
        d_major = Scale(root=2, mode=Mode.MAJOR)
        comp = Composition(name="Multi", key=c_major)
        for k, prog in [(None, "I V I"), (g_major, "I V I"), (d_major, "I V I")]:
            comp.add_section("S", 4.0, prog, {"Lead": _MELODY_PRESET}, key=k)
        director = MusicDirector(c_major)
        arr = director.render(comp)
        # keys[0]=global stub, keys[1]=C, keys[2]=G, keys[3]=D
        assert arr.timeline.keys[1].scale == c_major
        assert arr.timeline.keys[2].scale == g_major
        assert arr.timeline.keys[3].scale == d_major

    def test_modulation_produces_notes(self):
        new_key = Scale(root=9, mode=Mode.NATURAL_MINOR)
        comp = _make_composition([
            {"name": "Verse", "progression": "I IV V I"},
            {"name": "Bridge", "progression": "Im IVm", "key": new_key},
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert sum(len(t.notes) for t in arr.tracks) > 0

    def test_composition_without_section_key_is_backward_compatible(self):
        comp = _make_composition([
            {"name": "A", "progression": "I V"},
            {"name": "B", "progression": "IV I"},
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert arr.total_beats == 8.0

    def test_section_key_used_for_chord_parsing(self):
        """Chords appended to timeline must belong to the section's effective key."""
        a_minor = Scale(root=9, mode=Mode.NATURAL_MINOR)
        comp = _make_composition([
            {"name": "Bridge", "progression": "Im IVm", "key": a_minor},
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        # At least some chord root in the timeline should be from A minor (roots: 9,0,2,4,5,7,11)
        a_minor_pcs = set(a_minor.degrees())
        roots = {c.root for c in arr.timeline.chords}
        assert roots & a_minor_pcs  # non-empty intersection


# ─────────────────────────────────────────────────────────────
# RhythmCoordinator → MusicDirector integration
# ─────────────────────────────────────────────────────────────

class TestRhythmCoordinatorIntegration:
    def test_shared_rhythm_produces_notes(self):
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        comp = _make_composition([
            {"name": "A", "progression": "I IV V I",
             "tracks": {"Lead": _MELODY_PRESET},
             "shared_rhythm": rgen}
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert sum(len(t.notes) for t in arr.tracks) > 0

    def test_shared_rhythm_aligns_onsets_across_tracks(self):
        """Tracks using shared_rhythm must have the same number of notes.
        Both presets use melody_default (no humanizer), so onsets stay clean and
        can be compared exactly after rendering.
        """
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        comp = _make_composition([
            {"name": "A", "progression": "I IV V I",
             # Use the same preset (no humanizer modifier) so onsets are not shifted
             "tracks": {"Melody1": _BASS_PRESET, "Melody2": _BASS_PRESET},
             "shared_rhythm": rgen,
             "duration": 4.0}
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        onsets_by_track = {
            t.name: sorted({round(n.start, 4) for n in t.notes})
            for t in arr.tracks
        }
        if len(onsets_by_track) >= 2:
            vals = list(onsets_by_track.values())
            assert vals[0] == vals[1], (
                f"Shared rhythm should produce equal onsets, got {vals}"
            )

    def test_section_without_shared_rhythm_uses_generator_own_rhythm(self):
        comp = _make_composition([
            {"name": "A", "progression": "I IV",
             "tracks": {"Lead": _MELODY_PRESET}}
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert sum(len(t.notes) for t in arr.tracks) > 0

    def test_rhythm_coordinator_per_section_independent(self):
        """Each section creates its own coordinator — different durations don't interfere."""
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        comp = _make_composition([
            {"name": "A", "duration": 4.0, "progression": "I IV",
             "tracks": {"Lead": _MELODY_PRESET}, "shared_rhythm": rgen},
            {"name": "B", "duration": 8.0, "progression": "V I",
             "tracks": {"Lead": _MELODY_PRESET}, "shared_rhythm": rgen},
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert arr.total_beats == 12.0

    def test_modulation_and_shared_rhythm_combined(self):
        """Per-section key + shared_rhythm must both work simultaneously."""
        new_key = Scale(root=9, mode=Mode.NATURAL_MINOR)
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        comp = _make_composition([
            {"name": "Verse", "progression": "I IV V I",
             "tracks": {"Lead": _MELODY_PRESET, "Bass": _BASS_PRESET}},
            {"name": "Bridge", "progression": "Im IVm",
             "key": new_key,
             "tracks": {"Lead": _MELODY_PRESET, "Bass": _BASS_PRESET},
             "shared_rhythm": rgen},
        ])
        director = MusicDirector(comp.key)
        arr = director.render(comp)
        assert arr.total_beats == 8.0
        assert arr.timeline.keys[2].scale == new_key


# ─────────────────────────────────────────────────────────────
# _CoordinatedRhythm unit tests
# ─────────────────────────────────────────────────────────────

class TestCoordinatedRhythm:
    def test_delegates_to_coordinator(self):
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        coord = RhythmCoordinator(rgen)
        coord.register("Bass")
        cr = _CoordinatedRhythm(coord, "Bass")
        events = cr.generate(4.0)
        assert len(events) > 0

    def test_returns_same_events_for_different_tracks(self):
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        coord = RhythmCoordinator(rgen)
        coord.register("A")
        coord.register("B")
        cr_a = _CoordinatedRhythm(coord, "A")
        cr_b = _CoordinatedRhythm(coord, "B")
        assert cr_a.generate(4.0) == cr_b.generate(4.0)

    def test_cached_events_are_copies(self):
        """Clearing the returned list must not affect coordinator cache."""
        rgen = EuclideanRhythmGenerator(hits_per_bar=4)
        coord = RhythmCoordinator(rgen)
        coord.register("T")
        cr = _CoordinatedRhythm(coord, "T")
        first = cr.generate(4.0)
        first.clear()
        second = cr.generate(4.0)
        assert len(second) > 0
