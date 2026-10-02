# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.score.compiler — Compiles Song IR into multi-track note events and MIDI.

Connects the score format to the generation pipeline:
- Unrolls form schedules and chord progressions
- Resolves instrument profiles and generators
- Applies swing/humanize feel modifier stacks
- Exports rich Type-1 MIDI with section markers, chord meta events, and channel isolation
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import mido

from melodica.generate.family import MalletFamily, PluckedFamily, WindBrassFamily
from melodica.generate.profile import get_profile
from melodica.generators import (
    AmbientPadGenerator,
    BassGenerator,
    ChordGenerator,
    DrumKitPatternGenerator,
    GeneratorParams,
    MelodyGenerator,
    WalkingBassGenerator,
)
from melodica.midi import export_multitrack_midi
from melodica.modifiers import ModifierContext, ModifierPipeline
from melodica.modifiers.rhythmic import HumanizeModifier, SwingController
from melodica.score.ir import Song, TrackArrange
from melodica.score.parser import parse_song
from melodica.types import ChordLabel, MarkerLabel, MusicTimeline, NoteInfo, Scale


def _try_profile_generator(track: TrackArrange, params: GeneratorParams) -> tuple[Any, int] | None:
    inst_name = (track.instrument or track.name or "").lower().strip()
    try:
        prof = get_profile(inst_name)
        if prof.family == "plucked":
            gen = PluckedFamily(
                prof,
                params=params,
                style=track.style or track.params.get("style"),
                note_density=track.density,
            )
        elif prof.family == "wind_brass":
            gen = WindBrassFamily(
                prof,
                params=params,
                note_density=track.density,
            )
        else:
            gen = MalletFamily(
                prof,
                params=params,
                pattern=track.params.get("pattern"),
                note_density=track.density,
            )
        return gen, prof.gm_program
    except (KeyError, FileNotFoundError):
        return None


def _try_drum_generator(track: TrackArrange, params: GeneratorParams) -> tuple[Any, int] | None:
    name_l = track.name.lower().strip()
    if "drum" in name_l or "beat" in name_l or track.family == "drums":
        drum_style = (track.style or track.groove or "rock").lower().strip()
        gen = DrumKitPatternGenerator(
            params=params,
            style=drum_style,
            hihat_pattern="eighth",
        )
        return gen, 0
    return None


def _try_bass_generator(track: TrackArrange, params: GeneratorParams) -> tuple[Any, int] | None:
    name_l = track.name.lower().strip()
    style = (track.style or "").lower().strip()
    if "bass" in name_l or track.family == "bass":
        if style == "walking" or track.algorithm == "walking_bass":
            return WalkingBassGenerator(params=params), 32
        gen = BassGenerator(params=params, style="root_fifth" if style == "roots" else "root_only")
        gm = 33 if "finger" in style else (38 if "synth" in style else 32)
        return gen, gm
    return None


def _try_pad_or_lead_generator(track: TrackArrange, params: GeneratorParams) -> tuple[Any, int] | None:
    name_l = track.name.lower().strip()
    if "pad" in name_l or "ambient" in name_l or "string" in name_l:
        return AmbientPadGenerator(params=params, voicing="spread"), 89
    if "lead" in name_l or "melody" in name_l or "solo" in name_l:
        gen = MelodyGenerator(
            params=params,
            phrase_contour="arch",
            harmony_note_probability=0.7,
        )
        return gen, 80
    return None


def _build_track_generator(track: TrackArrange) -> tuple[Any, int]:
    """
    Instantiate the appropriate generator and resolve GM program for a TrackArrange specification.
    Returns (generator_instance, gm_program).
    """
    params = GeneratorParams(density=max(0.01, min(1.0, track.density)))
    if track.range:
        params.key_range_low, params.key_range_high = track.range

    builders = [
        _try_profile_generator,
        _try_drum_generator,
        _try_bass_generator,
        _try_pad_or_lead_generator,
    ]
    for b in builders:
        res = b(track, params)
        if res is not None:
            return res

    # Fallback: Chordal accompaniment
    return ChordGenerator(params=params, voicing_type="open"), 0


def _shift_octaves(notes: list[NoteInfo], octaves: int) -> list[NoteInfo]:
    if octaves == 0:
        return notes
    shift = octaves * 12
    return [
        NoteInfo(
            pitch=max(0, min(127, n.pitch + shift)),
            start=n.start,
            duration=n.duration,
            velocity=n.velocity,
            absolute=n.absolute,
            articulation=n.articulation,
            expression=n.expression,
        )
        for n in notes
    ]


def _apply_feel(
    notes: list[NoteInfo],
    song: Song,
    all_chords: list[ChordLabel],
    markers: list[tuple[str, float]],
) -> list[NoteInfo]:
    f = song.feel.lower()
    if not notes or ("swing" not in f and "human" not in f):
        return notes

    pipeline = ModifierPipeline(base_notes=notes)
    if "swing8" in f:
        pipeline.add_modifier(SwingController(swing_ratio=0.58, grid=0.5))
    elif "swing16" in f:
        pipeline.add_modifier(SwingController(swing_ratio=0.58, grid=0.25))
    pipeline.add_modifier(HumanizeModifier(timing_std=0.012, velocity_std=3.0))

    marker_labels = [MarkerLabel(text=name, start=b) for name, b in markers]
    timeline = MusicTimeline(chords=all_chords, markers=marker_labels)
    mod_ctx = ModifierContext(
        duration_beats=song.total_beats(),
        chords=all_chords,
        timeline=timeline,
        scale=song.key,
    )
    return pipeline.process(mod_ctx)


def compile_song_tracks(song: Song) -> tuple[dict[str, list[NoteInfo]], dict[str, int]]:
    """
    Execute generators for all arranged tracks in Song, yielding note sequences and GM programs.
    """
    if song.seed is not None:
        random.seed(song.seed)

    markers, all_chords = song.unrolled_timeline()
    total_beats = song.total_beats()

    tracks_notes: dict[str, list[NoteInfo]] = {}
    instruments_map: dict[str, int] = {}

    arrange_tracks = dict(song.arrange) or {
        "Lead": TrackArrange(name="Lead", instrument="piano"),
        "Chords": TrackArrange(name="Chords", instrument="piano"),
        "Bass": TrackArrange(name="Bass", style="walking"),
    }

    for track_name, track_cfg in arrange_tracks.items():
        gen, gm_prog = _build_track_generator(track_cfg)
        instruments_map[track_name] = gm_prog

        rendered = gen.render(all_chords, song.key, total_beats)
        rendered = _shift_octaves(rendered, track_cfg.octave_shift)
        rendered = _apply_feel(rendered, song, all_chords, markers)

        tracks_notes[track_name] = rendered

    return tracks_notes, instruments_map


def song_to_midi(
    song: Song | str | Path,
    output_path: str | Path | None = None,
) -> mido.MidiFile:
    """
    Compile a Song IR (or .song file / string) into a Type-1 multitrack MIDI file.
    Includes global markers for each section, chord progression, and channel isolation.
    """
    if not isinstance(song, Song):
        song = parse_song(song)

    tracks_notes, instruments_map = compile_song_tracks(song)
    markers, all_chords = song.unrolled_timeline()

    marker_labels = [MarkerLabel(text=sec_name, start=beat) for sec_name, beat in markers]
    timeline = MusicTimeline(
        chords=all_chords,
        markers=marker_labels,
    )

    save_path = Path(output_path) if output_path else Path("output") / f"{song.title.lower().replace(' ', '_')}.mid"
    save_path.parent.mkdir(parents=True, exist_ok=True)

    export_multitrack_midi(
        tracks_data=tracks_notes,
        path=save_path,
        bpm=song.tempo,
        key=song.key,
        time_sig=song.time_signature,
        timeline=timeline,
        instruments=instruments_map,
        diagnose=False,
    )

    return mido.MidiFile(save_path)


# Aliases for convenience
compile_song_to_midi = song_to_midi
compile_song_to_tracks = compile_song_tracks
