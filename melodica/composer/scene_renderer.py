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

"""
composer/scene_renderer.py — Render SceneGraph into stitched multi-track output.

Supports transition types: CUT, FADE, CROSSFADE, MODULATION.
Each scene is rendered via produce_track() then stitched with offsets.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from melodica.composer.automation import AutomationCurve
from melodica.types import (
    NoteInfo,
    TransitionType,
    Scene,
    SceneGraph,
    SceneTransition,
)

if TYPE_CHECKING:
    from melodica.types import ChordLabel, Scale


@dataclass
class StitchResult:
    """Result of rendering a SceneGraph."""

    tracks: dict[str, list[NoteInfo]]
    instruments: dict[str, int]
    tempo_events: list[tuple[float, float]]
    cc_events: dict[str, list[tuple[float, int, int]]]
    duration: float  # total beats


def render_scene(
    scene: Scene,
    instruments: dict[str, int],
    path: str | Path,
    **pipeline_kw,
) -> dict[str, list[NoteInfo]]:
    """
    Render a single scene via produce_track().

    Returns the rendered tracks dict (raw NoteInfo lists).
    """
    from melodica.composer.album_pipeline import produce_track

    tracks = scene.tracks
    if tracks is None:
        return {}

    produce_track(
        tracks=tracks,
        bpm=scene.bpm,
        instruments=instruments,
        path=path,
        mood=pipeline_kw.get("mood"),
        key=scene.key,
        verbose=pipeline_kw.get("verbose", False),
        psycho_verify_enabled=pipeline_kw.get("psycho_verify_enabled", True),
        pipeline=pipeline_kw.get("pipeline"),
    )
    return tracks


def _track_duration(tracks: dict[str, list[NoteInfo]]) -> float:
    """Compute the max end beat across all tracks."""
    dur = 0.0
    for name, notes in tracks.items():
        if name.startswith("_"):
            continue
        if notes and isinstance(notes[0], NoteInfo):
            end = max(n.start + n.duration for n in notes)
            if end > dur:
                dur = end
    return dur


def render_scene_graph(
    graph: SceneGraph,
    instruments: dict[str, int],
    output_path: str | Path,
    **pipeline_kw,
) -> StitchResult:
    """
    Render all scenes in default_order and stitch them with transitions.

    For scenes with pre-rendered tracks, uses them directly.
    For scenes without tracks, calls render_scene() first.
    """
    ordered = graph.ordered_scenes()
    if not ordered:
        return StitchResult(
            tracks={},
            instruments={},
            tempo_events=[],
            cc_events={},
            duration=0.0,
        )

    combined_tracks: dict[str, list[NoteInfo]] = {}
    combined_instruments: dict[str, int] = {}
    combined_cc: dict[str, list[tuple[float, int, int]]] = {}
    combined_tempo: list[tuple[float, float]] = []

    offset = 0.0

    for idx, scene in enumerate(ordered):
        # Get or render tracks for this scene
        scene_tracks = scene.tracks
        if scene_tracks is None:
            scene_tracks = {}

        # Find transition to next scene
        next_idx = idx + 1
        transition = None
        if next_idx < len(ordered):
            next_scene = ordered[next_idx]
            transition = graph.get_transition(scene.id, next_scene.id)
            if transition is None:
                transition = SceneTransition(
                    from_scene=scene.id,
                    to_scene=next_scene.id,
                )

        # Namespace tracks and shift to current offset
        for name, notes in scene_tracks.items():
            if name.startswith("_"):
                continue
            namespaced = f"{scene.id}__{name}"
            notes_copy = copy.deepcopy(notes)
            for n in notes_copy:
                n.shift_time(offset)
            if namespaced not in combined_tracks:
                combined_tracks[namespaced] = []
            combined_tracks[namespaced].extend(notes_copy)

            if name in instruments and namespaced not in combined_instruments:
                combined_instruments[namespaced] = instruments[name]

        # Tempo event at scene start
        combined_tempo.append((offset, scene.bpm))

        # Advance offset by scene duration
        scene_dur = _track_duration(scene_tracks) if scene_tracks else scene.duration_beats

        # Apply transition (affects offset for next scene)
        if transition is not None and idx < len(ordered) - 1:
            offset = _apply_transition(
                transition=transition,
                scene=scene,
                scene_id=scene.id,
                next_scene=ordered[next_idx],
                offset=offset,
                scene_dur=scene_dur,
                scene_tracks=scene_tracks,
                combined_tracks=combined_tracks,
                combined_cc=combined_cc,
                combined_instruments=combined_instruments,
                instruments=instruments,
            )
        else:
            offset += scene_dur

    # Sort notes and CC events
    for name in combined_tracks:
        combined_tracks[name].sort(key=lambda n: n.start)
    for name in combined_cc:
        combined_cc[name].sort(key=lambda ev: ev[0])
    combined_tempo.sort(key=lambda ev: ev[0])

    return StitchResult(
        tracks=combined_tracks,
        instruments=combined_instruments,
        tempo_events=combined_tempo,
        cc_events=combined_cc,
        duration=offset,
    )


def _apply_transition(
    transition: SceneTransition,
    scene: Scene,
    scene_id: str,
    next_scene: Scene,
    offset: float,
    scene_dur: float,
    scene_tracks: dict[str, list[NoteInfo]],
    combined_tracks: dict[str, list[NoteInfo]],
    combined_cc: dict[str, list[tuple[float, int, int]]],
    combined_instruments: dict[str, int],
    instruments: dict[str, int],
) -> float:
    """Apply a transition between scenes and return new offset."""

    if transition.type == TransitionType.CUT:
        return _apply_cut(offset, scene_dur)

    if transition.type == TransitionType.FADE:
        return _apply_fade(
            transition,
            scene_id,
            next_scene,
            offset,
            scene_dur,
            scene_tracks,
            combined_tracks,
            combined_cc,
            combined_instruments,
            instruments,
        )

    if transition.type == TransitionType.CROSSFADE:
        return _apply_crossfade(
            transition,
            scene_id,
            next_scene,
            offset,
            scene_dur,
            scene_tracks,
            combined_tracks,
            combined_cc,
            combined_instruments,
            instruments,
        )

    if transition.type == TransitionType.MODULATION:
        return _apply_modulation(
            transition=transition,
            scene=scene,
            scene_id=scene.id,
            next_scene=next_scene,
            offset=offset,
            scene_dur=scene_dur,
            scene_tracks=scene_tracks,
            combined_tracks=combined_tracks,
            combined_cc=combined_cc,
            combined_instruments=combined_instruments,
            instruments=instruments,
        )

    # Fallback: treat as CUT
    return _apply_cut(offset, scene_dur)


def _apply_cut(offset: float, scene_dur: float) -> float:
    """CUT: splice at barline, no overlap."""
    return offset + scene_dur


def _apply_fade(
    transition: SceneTransition,
    scene_id: str,
    next_scene: Scene,
    offset: float,
    scene_dur: float,
    scene_tracks: dict[str, list[NoteInfo]],
    combined_tracks: dict[str, list[NoteInfo]],
    combined_cc: dict[str, list[tuple[float, int, int]]],
    combined_instruments: dict[str, int],
    instruments: dict[str, int],
) -> float:
    """FADE: velocity envelope on fade zone, no overlap."""
    fade_beats = transition.duration_bars * next_scene.time_signature[0]
    if fade_beats <= 0:
        fade_beats = 4.0

    fade_start = offset + scene_dur - fade_beats
    fade_end = offset + scene_dur

    # Fade out outgoing tracks (CC7)
    for name in scene_tracks:
        if name.startswith("_"):
            continue
        ns = f"{scene_id}__{name}"
        fade_out = AutomationCurve.linear(
            7,
            100,
            0,
            fade_start,
            fade_end,
            steps=10,
        )
        if ns not in combined_cc:
            combined_cc[ns] = []
        combined_cc[ns].extend(fade_out)

    return offset + scene_dur


def _apply_crossfade(
    transition: SceneTransition,
    scene_id: str,
    next_scene: Scene,
    offset: float,
    scene_dur: float,
    scene_tracks: dict[str, list[NoteInfo]],
    combined_tracks: dict[str, list[NoteInfo]],
    combined_cc: dict[str, list[tuple[float, int, int]]],
    combined_instruments: dict[str, int],
    instruments: dict[str, int],
) -> float:
    """CROSSFADE: overlapping render with crossfade envelopes."""
    xfade_beats = transition.duration_bars * next_scene.time_signature[0]
    if xfade_beats <= 0:
        xfade_beats = 4.0

    # Fade out outgoing
    fade_start = offset + scene_dur - xfade_beats
    fade_end = offset + scene_dur
    for name in scene_tracks:
        if name.startswith("_"):
            continue
        ns = f"{scene_id}__{name}"
        fade_out = AutomationCurve.linear(
            7,
            100,
            0,
            fade_start,
            fade_end,
            steps=10,
        )
        if ns not in combined_cc:
            combined_cc[ns] = []
        combined_cc[ns].extend(fade_out)

    # Overlap: next scene starts before current ends
    return offset + scene_dur - xfade_beats


def _apply_modulation(
    transition: SceneTransition,
    scene: Scene,
    scene_id: str,
    next_scene: Scene,
    offset: float,
    scene_dur: float,
    scene_tracks: dict[str, list[NoteInfo]],
    combined_tracks: dict[str, list[NoteInfo]],
    combined_cc: dict[str, list[tuple[float, int, int]]],
    combined_instruments: dict[str, int],
    instruments: dict[str, int],
) -> float:
    """MODULATION: pivot chord bridge between different keys."""
    from melodica.theory.modulation import ModulationEngine
    from melodica.theory import CHORD_TEMPLATES

    bridge_beats = transition.duration_bars * next_scene.time_signature[0]
    if bridge_beats <= 0:
        bridge_beats = 4.0

    bridge_start = offset + scene_dur

    # Choose strategy based on whether a pivot chord is provided
    if transition.pivot_chord is not None:
        strategy = "pivot"
    else:
        # Auto-detect: use pivot if keys share common chords, else dominant
        pivots = ModulationEngine.find_pivot_chords(scene.key, next_scene.key)
        strategy = "pivot" if pivots else "dominant"

    # Generate the modulation bridge progression
    bridge_chords = ModulationEngine.generate_modulation_bridge(
        from_scale=scene.key,
        to_scale=next_scene.key,
        length_beats=bridge_beats,
        strategy=strategy,
        start_beat=bridge_start,
    )

    # Build pad notes for bridge chords
    bridge_notes: list[NoteInfo] = []
    for chord in bridge_chords:
        template = CHORD_TEMPLATES.get(chord.quality, [0, 4, 7])
        base_midi = 48 + int(chord.root)
        for interval in template:
            pitch = base_midi + interval
            if 0 <= pitch <= 127:
                bridge_notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=chord.start,
                        duration=chord.duration * 0.95,
                        velocity=55,
                    )
                )

    # Add bridge as a transition_pad track
    pad_name = f"{scene_id}__transition_pad"
    if bridge_notes:
        if pad_name not in combined_tracks:
            combined_tracks[pad_name] = []
        combined_tracks[pad_name].extend(bridge_notes)
        combined_instruments[pad_name] = 89  # Pad 2 Warm

        # Fade the pad in and out
        pad_fade_in = AutomationCurve.linear(
            7,
            0,
            80,
            bridge_start,
            bridge_start + bridge_beats * 0.5,
            steps=5,
        )
        pad_fade_out = AutomationCurve.linear(
            7,
            80,
            0,
            bridge_start + bridge_beats * 0.5,
            bridge_start + bridge_beats,
            steps=5,
        )
        if pad_name not in combined_cc:
            combined_cc[pad_name] = []
        combined_cc[pad_name].extend(pad_fade_in)
        combined_cc[pad_name].extend(pad_fade_out)

    return bridge_start + bridge_beats
