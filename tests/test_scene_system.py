# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-21
# Last Updated: 2026-05-21
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""Tests for Scene system — types, graph, rendering, transitions."""

from __future__ import annotations

import pytest

from melodica.types import (
    Scale,
    ChordLabel,
    NoteInfo,
    Scene,
    SceneTransition,
    SceneGraph,
    TransitionType,
)
from melodica.theory import Mode


def _c_major():
    return Scale(root=0, mode=Mode.MAJOR)


def _d_minor():
    return Scale(root=2, mode=Mode.NATURAL_MINOR)


def _note(pitch, start, dur=1.0, vel=80):
    return NoteInfo(pitch=pitch, start=start, duration=dur, velocity=vel)


# ---------------------------------------------------------------------------
# Step 1: Scene container
# ---------------------------------------------------------------------------


class TestSceneConstruction:
    def test_basic(self):
        s = Scene(id="v1", label="Verse", key=_c_major(), bpm=120, mood="cinematic")
        assert s.id == "v1"
        assert s.bpm == 120
        assert s.time_signature == (4, 4)
        assert s.section_type == "verse"
        assert s.tags == []

    def test_defaults(self):
        s = Scene(id="x", label="X", key=_c_major(), bpm=100, mood="dark")
        assert s.progression is None
        assert s.tracks is None
        assert s.duration_bars == 8

    def test_custom_duration(self):
        s = Scene(
            id="x",
            label="X",
            key=_c_major(),
            bpm=120,
            mood="m",
            duration_bars=16,
            time_signature=(3, 4),
        )
        assert s.duration_bars == 16
        assert s.time_signature == (3, 4)
        assert s.duration_beats == 48  # 16 * 3
        assert s.duration_seconds == pytest.approx(24.0)  # 48 / 2

    def test_with_tracks(self):
        tracks = {"melody": [_note(60, 0.0), _note(64, 1.0)]}
        s = Scene(id="x", label="X", key=_c_major(), bpm=120, mood="m", tracks=tracks)
        assert len(s.tracks["melody"]) == 2


class TestSceneTransitionType:
    def test_cut(self):
        assert TransitionType.CUT.value == "cut"

    def test_fade(self):
        assert TransitionType.FADE.value == "fade"

    def test_crossfade(self):
        assert TransitionType.CROSSFADE.value == "crossfade"

    def test_modulation(self):
        assert TransitionType.MODULATION.value == "modulation"


class TestSceneTransitionConstruction:
    def test_defaults_to_cut(self):
        t = SceneTransition(from_scene="a", to_scene="b")
        assert t.type == TransitionType.CUT
        assert t.duration_bars == 0.0
        assert t.pivot_chord is None

    def test_fade_with_duration(self):
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.FADE, duration_bars=2.0
        )
        assert t.type == TransitionType.FADE
        assert t.duration_bars == 2.0


class TestSceneGraphConstruction:
    def test_basic(self):
        s1 = Scene(id="intro", label="Intro", key=_c_major(), bpm=100, mood="m")
        s2 = Scene(id="verse", label="Verse", key=_c_major(), bpm=120, mood="m")
        g = SceneGraph(scenes={"intro": s1, "verse": s2}, default_order=["intro", "verse"])
        assert len(g.scenes) == 2
        assert g.default_order == ["intro", "verse"]

    def test_rejects_unknown_ids(self):
        with pytest.raises(ValueError, match="Unknown scene IDs"):
            SceneGraph(scenes={}, default_order=["missing"])

    def test_get_transition_found(self):
        t = SceneTransition(from_scene="a", to_scene="b", type=TransitionType.FADE)
        g = SceneGraph(scenes={}, default_order=[], transitions=[t])
        found = g.get_transition("a", "b")
        assert found is t

    def test_get_transition_not_found(self):
        g = SceneGraph(scenes={}, default_order=[])
        assert g.get_transition("a", "b") is None

    def test_ordered_scenes(self):
        s1 = Scene(id="a", label="A", key=_c_major(), bpm=100, mood="m")
        s2 = Scene(id="b", label="B", key=_c_major(), bpm=120, mood="m")
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["b", "a"])
        assert g.ordered_scenes() == [s2, s1]

    def test_default_order_allows_repeats(self):
        s = Scene(id="chorus", label="Chorus", key=_c_major(), bpm=120, mood="m")
        g = SceneGraph(scenes={"chorus": s}, default_order=["chorus", "chorus"])
        assert len(g.ordered_scenes()) == 2


# ---------------------------------------------------------------------------
# Step 2: SceneGraph rendering (CUT)
# ---------------------------------------------------------------------------


class TestRenderSceneGraph:
    def test_empty_graph(self):
        from melodica.composer.scene_renderer import render_scene_graph

        g = SceneGraph(scenes={}, default_order=[])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        assert result.tracks == {}
        assert result.duration == 0.0

    def test_single_scene_cut(self):
        from melodica.composer.scene_renderer import render_scene_graph

        tracks = {"melody": [_note(60, 0.0, 4.0), _note(64, 4.0, 4.0)]}
        s = Scene(id="v1", label="Verse", key=_c_major(), bpm=120, mood="m", tracks=tracks)
        g = SceneGraph(scenes={"v1": s}, default_order=["v1"])
        result = render_scene_graph(g, instruments={"melody": 1}, output_path="/tmp/test.mid")
        assert "v1__melody" in result.tracks
        assert len(result.tracks["v1__melody"]) == 2
        assert result.duration == 8.0

    def test_two_scenes_cut(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="intro",
            label="Intro",
            key=_c_major(),
            bpm=100,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="verse",
            label="Verse",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0, 4.0)]},
        )
        g = SceneGraph(scenes={"intro": s1, "verse": s2}, default_order=["intro", "verse"])
        result = render_scene_graph(
            g, instruments={"pad": 89, "melody": 1}, output_path="/tmp/test.mid"
        )
        # Both tracks should exist with namespace prefix
        assert "intro__pad" in result.tracks
        assert "verse__melody" in result.tracks
        # Verse melody should be offset by intro duration (8.0)
        assert result.tracks["verse__melody"][0].start == 8.0
        assert result.duration == 12.0

    def test_tempo_events_per_scene(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=100,
            mood="m",
            tracks={"x": [_note(60, 0.0, 4.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=140,
            mood="m",
            tracks={"y": [_note(64, 0.0, 4.0)]},
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        tempos = {ev[0]: ev[1] for ev in result.tempo_events}
        assert 0.0 in tempos and tempos[0.0] == 100
        assert 4.0 in tempos and tempos[4.0] == 140

    def test_instruments_namespaced(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s = Scene(
            id="s",
            label="S",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0, 2.0)]},
        )
        g = SceneGraph(scenes={"s": s}, default_order=["s"])
        result = render_scene_graph(g, instruments={"melody": 42}, output_path="/tmp/test.mid")
        assert result.instruments["s__melody"] == 42

    def test_repeated_scene_gets_separate_namespace(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s = Scene(
            id="chorus",
            label="Chorus",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        g = SceneGraph(scenes={"chorus": s}, default_order=["chorus", "chorus"])
        result = render_scene_graph(g, instruments={"lead": 1}, output_path="/tmp/test.mid")
        # Same namespaced key, but notes from both instances
        notes = result.tracks["chorus__lead"]
        assert len(notes) == 2
        # Second instance shifted by first's duration
        assert notes[0].start == 0.0
        assert notes[1].start == 4.0

    def test_underscore_tracks_excluded(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s = Scene(
            id="s",
            label="S",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0)], "_chords": ["fake"]},
        )
        g = SceneGraph(scenes={"s": s}, default_order=["s"])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        assert "s__melody" in result.tracks
        assert "s___chords" not in result.tracks


# ---------------------------------------------------------------------------
# Step 3: FADE + CROSSFADE transitions
# ---------------------------------------------------------------------------


class TestFadeTransition:
    def test_fade_creates_cc7_envelope(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.FADE, duration_bars=2.0
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(
            g, instruments={"pad": 89, "lead": 1}, output_path="/tmp/test.mid"
        )
        # CC7 events should exist for the faded track
        assert "a__pad" in result.cc_events
        cc = result.cc_events["a__pad"]
        assert len(cc) > 0
        # First value should be near 100, last near 0
        assert cc[0][2] >= 90  # start near full volume
        assert cc[-1][2] <= 10  # end near zero

    def test_fade_no_overlap(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.FADE, duration_bars=2.0
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        # FADE = no overlap, next scene starts after first ends
        assert result.tracks["b__lead"][0].start == 8.0

    def test_fade_default_duration(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        # duration_bars=0 → defaults to 4 beats
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.FADE, duration_bars=0.0
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        cc = result.cc_events["a__pad"]
        # Fade should span 4 beats ending at 8.0
        assert cc[-1][0] == pytest.approx(8.0)
        assert cc[0][0] == pytest.approx(4.0)


class TestCrossfadeTransition:
    def test_crossfade_creates_overlap(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.CROSSFADE, duration_bars=2.0
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        # Next scene starts 8.0 - 8.0 (2 bars * 4 beats) = offset 4.0
        # Wait: xfade_beats = 2.0 * 4 = 8.0, but scene_dur is 8.0
        # So next starts at offset + 8.0 - 8.0 = offset = 0.0? No, offset for first scene is 0
        # After first scene: offset = 0 + 8.0 - 8.0 = 0.0
        # But the first scene's notes are shifted to offset=0, so next starts at 0.0
        # That means overlapping at beat 0. Let's just check it's less than 8.0
        next_start = result.tracks["b__lead"][0].start
        assert next_start < 8.0  # overlap means next starts before first ends

    def test_crossfade_creates_cc7_fadeout(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.CROSSFADE, duration_bars=1.0
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        # Should have CC7 fade-out for outgoing track
        assert "a__pad" in result.cc_events
        cc = result.cc_events["a__pad"]
        assert cc[0][2] >= 90  # starts loud
        assert cc[-1][2] <= 10  # ends quiet

    def test_crossfade_with_shorter_scene(self):
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"pad": [_note(48, 0.0, 12.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"lead": [_note(60, 0.0, 4.0)]},
        )
        t = SceneTransition(
            from_scene="a", to_scene="b", type=TransitionType.CROSSFADE, duration_bars=1.0
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        # xfade_beats = 1.0 * 4 = 4.0, scene_dur = 12.0
        # Next starts at 0 + 12.0 - 4.0 = 8.0
        assert result.tracks["b__lead"][0].start == 8.0


# ---------------------------------------------------------------------------
# Step 4: MODULATION transition
# ---------------------------------------------------------------------------


class TestModulationTransition:
    def test_modulation_generates_bridge_notes(self):
        """MODULATION inserts a transition_pad track with bridge chords."""
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_d_minor(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(62, 0.0, 8.0)]},
        )
        t = SceneTransition(
            from_scene="a",
            to_scene="b",
            type=TransitionType.MODULATION,
            duration_bars=2.0,
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={"melody": 1}, output_path="/tmp/test.mid")
        # Should have a transition_pad track
        pad_names = [k for k in result.tracks if "transition_pad" in k]
        assert len(pad_names) == 1
        bridge_notes = result.tracks[pad_names[0]]
        assert len(bridge_notes) > 0

    def test_modulation_advances_offset(self):
        """MODULATION advances offset by scene_dur + bridge_beats."""
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_d_minor(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(62, 0.0, 4.0)]},
        )
        # 2 bars * 4/4 = 8 beats of bridge
        t = SceneTransition(
            from_scene="a",
            to_scene="b",
            type=TransitionType.MODULATION,
            duration_bars=2.0,
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        # b__melody should start after a__melody (8.0) + bridge (8.0)
        assert result.tracks["b__melody"][0].start == 16.0
        assert result.duration == 20.0

    def test_modulation_default_duration_is_4_beats(self):
        """duration_bars=0.0 → bridge defaults to 4 beats."""
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_d_minor(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(62, 0.0, 8.0)]},
        )
        t = SceneTransition(
            from_scene="a",
            to_scene="b",
            type=TransitionType.MODULATION,
            duration_bars=0.0,
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        # b__melody: 8.0 (a dur) + 4.0 (default bridge) = 12.0
        assert result.tracks["b__melody"][0].start == 12.0

    def test_modulation_includes_cc7_fade_on_pad(self):
        """Bridge pad gets CC7 fade-in and fade-out envelopes."""
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(
            id="a",
            label="A",
            key=_c_major(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(60, 0.0, 8.0)]},
        )
        s2 = Scene(
            id="b",
            label="B",
            key=_d_minor(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(62, 0.0, 8.0)]},
        )
        t = SceneTransition(
            from_scene="a",
            to_scene="b",
            type=TransitionType.MODULATION,
            duration_bars=2.0,
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        result = render_scene_graph(g, instruments={}, output_path="/tmp/test.mid")
        pad_names = [k for k in result.cc_events if "transition_pad" in k]
        assert len(pad_names) == 1
        cc = result.cc_events[pad_names[0]]
        assert len(cc) >= 2  # fade-in + fade-out CC events
        # Should contain both rising and falling segments
        values = [ev[2] for ev in cc]
        assert min(values) <= 10
        assert max(values) >= 70

    def test_modulation_falls_back_to_cut_without_tracks(self):
        """If from_scene has no tracks the transition still completes."""
        from melodica.composer.scene_renderer import render_scene_graph

        s1 = Scene(id="a", label="A", key=_c_major(), bpm=120, mood="m", tracks=None)  # no tracks
        s2 = Scene(
            id="b",
            label="B",
            key=_d_minor(),
            bpm=120,
            mood="m",
            tracks={"melody": [_note(62, 0.0, 4.0)]},
        )
        t = SceneTransition(
            from_scene="a",
            to_scene="b",
            type=TransitionType.MODULATION,
            duration_bars=2.0,
        )
        g = SceneGraph(scenes={"a": s1, "b": s2}, default_order=["a", "b"], transitions=[t])
        # duration_beats of scene with no tracks = 0
        result = render_scene_graph(g, instruments={"melody": 1}, output_path="/tmp/test.mid")
        assert "b__melody" in result.tracks
