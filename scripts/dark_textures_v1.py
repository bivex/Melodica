
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
dark_textures_v1.py — Dark Textures Generator.

A cinematic dark-texture composition engine. Focuses on atmospheric,
textural, and timbral exploration using minor tonalities, dissonance,
and slow evolution.

6-act arc:
    1. Void          — pure drone, near silence
    2. Descent       — dark bass emerges from below
    3. Fog           — dense pad textures, semitone clusters
    4. Abyss         — maximum tension, tritones, atonal scatter
    5. Pulse         — mechanical rhythm breaks through
    6. Dissolve      — everything fades to nothing
"""

from __future__ import annotations

import random
import warnings
import argparse
from pathlib import Path
from dataclasses import dataclass

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    MarkovMelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    AmbientPadGenerator,
    DyadGenerator,
    TremoloStringsGenerator,
    ChoraleGenerator,
    CountermelodyGenerator,
    GeneratorParams,
)
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.tension import TensionGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.dynamics import DynamicsCurveGenerator
from melodica.generators.hemiola import HemiolaGenerator
from melodica.generators.downbeat_rest import DownbeatRestGenerator
from melodica.harmonize import (
    FunctionalHarmonizer,
    ChromaticMediantHarmonizer,
    ModalInterchangeHarmonizer,
    GraphSearchHarmonizer,
)
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    StaccatoLegatoModifier,
    LimitNoteRangeModifier,
    AddIntervalModifier,
    ModifierContext,
)
from melodica.composer import NonChordToneGenerator, ArticulationEngine
from melodica.rhythm import (
    BassRhythmGenerator,
    EuclideanRhythmGenerator,
    SmoothRhythmGenerator,
)
from melodica.midi import export_multitrack_midi, GM_INSTRUMENTS
from melodica.render_context import RenderContext


# ---------------------------------------------------------------------------
# Scales — dark palette
# ---------------------------------------------------------------------------
DARK_SCALES = {
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "byzantine": Scale(root=0, mode=Mode.BYZANTINE),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "dorian": Scale(root=0, mode=Mode.DORIAN),
    "diminished": Scale(root=0, mode=Mode.DIMINISHED),
    "persian": Scale(root=0, mode=Mode.PERSIAN),
    "horror_cluster": Scale(root=0, mode=Mode.HORROR_CLUSTER),
    "suspense": Scale(root=0, mode=Mode.SUSPENSE),
}


# ---------------------------------------------------------------------------
# Section definition
# ---------------------------------------------------------------------------
@dataclass
class Section:
    name: str
    bars: int
    scale_name: str
    key_root: int
    mood: str
    density: float
    tracks: list[str]


def build_sections(total_bars: int) -> list[Section]:
    """
    6-act dark texture arc:

    1. Void        — pp, drone only, near silence
    2. Descent     — p, dark bass emerges
    3. Fog         — mp, dense textures + tension
    4. Abyss       — mf, maximum dissonance
    5. Pulse       — mf, mechanical rhythm
    6. Dissolve    — pp, decay to nothing
    """
    template = [
        ("Void", 0.15, "horror_cluster", 0, "void", 0.10, ["drone", "tremolo"]),
        (
            "Descent", 0.18, "hungarian_minor", 0, "descent", 0.25,
            ["dark_bass", "drone", "dynamics"],
        ),
        (
            "Fog", 0.22, "suspense", 0, "fog", 0.45,
            ["dark_pad", "tension", "dark_bass", "ambient", "tremolo"],
        ),
        (
            "Abyss", 0.20, "persian", 0, "abyss", 0.55,
            ["tension", "dark_bass", "dark_pad", "dyads", "hemiola", "tremolo"],
        ),
        (
            "Pulse", 0.15, "diminished", 0, "pulse", 0.50,
            ["dark_bass", "ostinato", "dark_pad", "tension", "downbeat_rest"],
        ),
        ("Dissolve", 0.10, "horror_cluster", 0, "dissolve", 0.12, ["drone", "dynamics"]),
    ]

    raw = [max(1, round(total_bars * r)) for _, r, *_ in template]
    diff = total_bars - sum(raw)
    raw[-1] = max(1, raw[-1] + diff)

    return [
        Section(n, raw[i], sn, kr, m, d, t)
        for i, (n, _, sn, kr, m, d, t) in enumerate(template)
    ]


# ---------------------------------------------------------------------------
# Track pipeline
# ---------------------------------------------------------------------------
TRACK_NAMES = [
    "drone", "dark_bass", "dark_pad", "tension", "ambient",
    "tremolo", "dyads", "ostinato", "dynamics", "hemiola", "downbeat_rest",
]


def make_pipeline(track: str, mood: str, density: float, scale: Scale):
    """Returns (generator, modifiers_list)."""
    params = GeneratorParams(density=density)
    mods: list = []

    match track:
        # ── Drone ──────────────────────────────────────────────
        case "drone":
            gen = DarkPadGenerator(
                params=params,
                mode="tritone_drone" if mood == "void" else "minor_pad",
                chord_dur=16.0 if mood in ("void", "dissolve") else 8.0,
                velocity_level=0.15 if mood in ("void", "dissolve") else 0.25,
                register="low",
                overlap=0.5,
            )

        # ── Dark Bass ──────────────────────────────────────────
        case "dark_bass":
            bass_mode = {
                "descent": "doom",
                "fog": "dub",
                "abyss": "doom",
                "pulse": "industrial",
            }.get(mood, "doom")
            gen = DarkBassGenerator(
                params=params,
                mode=bass_mode,
                octave=2,
                note_duration=8.0 if mood in ("descent", "abyss") else 4.0,
                velocity_level=0.6,
                movement="tritone_walk" if mood == "abyss" else "root_only",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=52))

        # ── Dark Pad ───────────────────────────────────────────
        case "dark_pad":
            pad_mode = {
                "fog": "phrygian_pad",
                "abyss": "dim_cluster",
                "pulse": "minor_pad",
            }.get(mood, "minor_pad")
            gen = DarkPadGenerator(
                params=params,
                mode=pad_mode,
                chord_dur=8.0,
                velocity_level=0.3 if mood != "abyss" else 0.4,
                register="low" if mood == "fog" else "mid",
                overlap=0.4,
            )

        # ── Tension ────────────────────────────────────────────
        case "tension":
            tension_mode = {
                "fog": "semitone_cluster",
                "abyss": "tritone_pulse",
                "pulse": "chromatic_rise",
            }.get(mood, "semitone_cluster")
            gen = TensionGenerator(
                params=params,
                mode=tension_mode,
                note_duration=4.0 if mood == "fog" else 2.0,
                velocity_level=0.3,
                register="mid",
                density=0.5,
            )

        # ── Ambient ────────────────────────────────────────────
        case "ambient":
            gen = AmbientPadGenerator(
                params=params,
                voicing="spread",
                overlap=0.7,
            )
            mods.append(VelocityScalingModifier(scale=0.5))
            mods.append(HumanizeModifier(timing_std=0.05, velocity_std=3))

        # ── Tremolo Strings ────────────────────────────────────
        case "tremolo":
            gen = TremoloStringsGenerator(
                params=params,
                variant="chord",
                bow_speed=0.0625,
                dynamic_swell=mood != "pulse",
            )
            mods.append(VelocityScalingModifier(scale=0.5 if mood == "void" else 0.65))

        # ── Dyads ──────────────────────────────────────────────
        case "dyads":
            gen = DyadGenerator(
                params=params,
                interval_pref=[1, 6, 10],  # m2, tritone, m7 — dark intervals
                motion_mode="contrary",
            )
            mods.append(StaccatoLegatoModifier(amount=0.6))

        # ── Ostinato ───────────────────────────────────────────
        case "ostinato":
            gen = OstinatoGenerator(
                params=params,
                pattern="5-1-4-1-3-1-2-1" if mood == "pulse" else "1-3-5-3",
                repeat_notes=2 if mood == "pulse" else 1,
            )
            if mood == "pulse":
                mods.append(VelocityScalingModifier(scale=0.8))

        # ── Dynamics Curve ─────────────────────────────────────
        case "dynamics":
            curve = "decrescendo" if mood == "dissolve" else "swell"
            gen = DynamicsCurveGenerator(
                params=params,
                curve_type=curve,
                note_duration=4.0,
                pitch_strategy="root",
                strength=1.5,
                velocity_range=(15, 70),
            )

        # ── Hemiola ────────────────────────────────────────────
        case "hemiola":
            gen = HemiolaGenerator(
                params=params,
                pattern="3_over_4",
                pitch_strategy="chord_tone",
                velocity_accent=1.1,
                cycles_per_chord=1,
            )
            mods.append(VelocityScalingModifier(scale=0.7))

        # ── Downbeat Rest ──────────────────────────────────────
        case "downbeat_rest":
            gen = DownbeatRestGenerator(
                params=params,
                mode="caesura",
                caesura_length=1.5,
                subdivision=1.0,
                pitch_strategy="chord_tone",
            )

        # ── Fallback ───────────────────────────────────────────
        case _:
            gen = AmbientPadGenerator(params=params)

    return gen, mods


# ---------------------------------------------------------------------------
# Harmonizer by mood
# ---------------------------------------------------------------------------
def pick_harmonizer(mood: str):
    match mood:
        case "void" | "dissolve":
            return FunctionalHarmonizer(start_with="i", end_with="i")
        case "descent":
            return FunctionalHarmonizer(start_with="i", end_with="i")
        case "fog":
            return ModalInterchangeHarmonizer(borrow_prob=0.4)
        case "abyss":
            return ChromaticMediantHarmonizer(chromatic_prob=0.4)
        case "pulse":
            return GraphSearchHarmonizer()
        case _:
            return FunctionalHarmonizer(start_with="i", end_with="i")


# ---------------------------------------------------------------------------
# Melody contour for harmonization
# ---------------------------------------------------------------------------
def _build_melody_contour(
    scale: Scale, bars: int, beats_per_bar: int, density: float
) -> list[NoteInfo]:
    degs = scale.degrees()
    if not degs:
        return [NoteInfo(pitch=48, start=0.0, duration=8.0, velocity=50)]

    notes: list[NoteInfo] = []
    t = 0.0
    prev_pc = int(degs[0])
    total_beats = bars * beats_per_bar

    while t < total_beats:
        change_every = 4.0 if density < 0.3 else 2.0
        phrase_dur = min(change_every, total_beats - t)

        strong_pc = int(random.choice(degs))
        if t % (beats_per_bar * 4) == 0:
            strong_pc = int(degs[0])

        base = 48  # low register for dark textures
        pitch = base + int(strong_pc)
        while pitch < 36:
            pitch += 12
        while pitch > 60:
            pitch -= 12

        dur = min(phrase_dur - 0.1, 3.0 + random.uniform(0, 2.0))
        dur = max(1.0, dur)

        notes.append(
            NoteInfo(pitch=pitch, start=round(t, 6), duration=round(dur, 6), velocity=50)
        )

        prev_pc = strong_pc
        t += phrase_dur

    return notes


# ---------------------------------------------------------------------------
# Master mix
# ---------------------------------------------------------------------------
MIX = {
    "drone": 0.9,
    "dark_bass": 0.85,
    "dark_pad": 0.7,
    "tension": 0.5,
    "ambient": 0.4,
    "tremolo": 0.55,
    "dyads": 0.6,
    "ostinato": 0.65,
    "dynamics": 0.4,
    "hemiola": 0.5,
    "downbeat_rest": 0.55,
}

_MAX_POLYPHONY = 10


def _master_mix(tracks: dict[str, list[NoteInfo]]) -> dict[str, list[NoteInfo]]:
    result = {}
    for name, notes in tracks.items():
        level = MIX.get(name, 0.5)
        mixed = []
        for n in notes:
            vel = max(10, min(127, int(n.velocity * level) + random.randint(-3, 3)))
            start = n.start + random.uniform(-0.02, 0.02)
            mixed.append(
                NoteInfo(
                    pitch=n.pitch, start=round(start, 6),
                    duration=n.duration, velocity=vel,
                    articulation=n.articulation, expression=n.expression,
                )
            )
        result[name] = sorted(mixed, key=lambda n: n.start)
    return _limit_polyphony(result)


def _limit_polyphony(tracks: dict[str, list[NoteInfo]]) -> dict[str, list[NoteInfo]]:
    all_notes = []
    for name, notes in tracks.items():
        for i, n in enumerate(notes):
            all_notes.append((n.start, name, i))
    all_notes.sort()

    grid: dict[int, int] = {}
    for t, _, _ in all_notes:
        key = int(t * 4)
        grid[key] = grid.get(key, 0) + 1

    peak = max(grid.values()) if grid else 1
    if peak <= _MAX_POLYPHONY:
        return tracks

    result = {}
    for name, notes in tracks.items():
        scaled = []
        for n in notes:
            key = int(n.start * 4)
            poly = grid.get(key, 1)
            if poly > _MAX_POLYPHONY:
                ratio = _MAX_POLYPHONY / poly
                vel = max(15, int(n.velocity * ratio))
            else:
                vel = n.velocity
            scaled.append(
                NoteInfo(
                    pitch=n.pitch, start=n.start, duration=n.duration,
                    velocity=vel, articulation=n.articulation, expression=n.expression,
                )
            )
        result[name] = scaled
    return result


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------
def generate(duration_minutes: float, tempo: int, key_root: int, seed: int | None):
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    total_beats = duration_minutes * 60 * (tempo / 60)
    total_bars = max(8, int(round(total_beats / beats_per_bar)))
    sections = build_sections(total_bars)

    tracks: dict[str, list[NoteInfo]] = {}
    all_chords: list[ChordLabel] = []
    beat_offset = 0.0

    nct = NonChordToneGenerator(passing_prob=0.08, neighbor_prob=0.04)
    art_engine = ArticulationEngine()
    track_contexts: dict[str, RenderContext] = {}
    prev_scale: Scale | None = None

    INSTRUMENT_MAP = {
        "drone": "strings_pad",
        "dark_bass": "cello",
        "dark_pad": "strings_pad",
        "tension": "strings_tremolo",
        "ambient": "strings_pad",
        "tremolo": "strings_tremolo",
        "dyads": "strings_melody",
        "ostinato": "strings_staccato",
        "dynamics": "strings_pad",
        "hemiola": "strings_melody",
        "downbeat_rest": "strings_melody",
    }

    for si, sec in enumerate(sections):
        s_beats = sec.bars * beats_per_bar
        base_scale = DARK_SCALES[sec.scale_name]
        scale = Scale(root=(sec.key_root + key_root) % 12, mode=base_scale.mode)

        if prev_scale is not None and scale != prev_scale:
            root_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            print(
                f"  ♩ Modulation: {root_names[prev_scale.root]} {prev_scale.mode.name} "
                f"→ {root_names[scale.root]} {scale.mode.name}  [{sec.name}]"
            )
        prev_scale = scale

        # Harmonize
        harmonizer = pick_harmonizer(sec.mood)
        melody_contour = _build_melody_contour(scale, sec.bars, beats_per_bar, sec.density)
        local_chords = harmonizer.harmonize(melody_contour, scale, s_beats)
        while len(local_chords) < sec.bars:
            local_chords.append(
                local_chords[-1] if local_chords
                else ChordLabel(
                    root=int(scale.degrees()[0]) if scale.degrees() else 0,
                    quality=Quality.MINOR,
                    start=round(len(local_chords) * beats_per_bar, 6),
                    duration=beats_per_bar,
                )
            )

        for c in local_chords:
            all_chords.append(
                ChordLabel(
                    root=c.root, quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration, degree=c.degree,
                )
            )

        phrase_position = si / max(1, len(sections) - 1)

        for track_name in sec.tracks:
            gen, mods = make_pipeline(track_name, sec.mood, sec.density, scale)

            prev_ctx = track_contexts.get(track_name)
            if prev_ctx is None:
                ctx = RenderContext(
                    phrase_position=phrase_position, current_scale=scale,
                )
            else:
                ctx = RenderContext(
                    prev_pitch=prev_ctx.prev_pitch,
                    prev_velocity=prev_ctx.prev_velocity,
                    prev_chord=prev_ctx.prev_chord,
                    prev_pitches=list(prev_ctx.prev_pitches),
                    phrase_position=phrase_position,
                    current_scale=scale,
                )

            notes = gen.render(local_chords, scale, s_beats, ctx)

            if hasattr(gen, "_last_context") and gen._last_context is not None:
                track_contexts[track_name] = gen._last_context
            elif notes:
                track_contexts[track_name] = ctx.with_end_state(
                    last_pitch=notes[-1].pitch,
                    last_velocity=notes[-1].velocity,
                    last_chord=local_chords[-1] if local_chords else None,
                    current_scale=scale,
                )

            # Apply modifiers
            mctx = ModifierContext(
                duration_beats=s_beats, chords=local_chords, timeline=None, scale=scale,
            )
            for m in mods:
                try:
                    notes = m.modify(notes, mctx)
                except Exception:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)  # noqa: S110

            # NCT for melodic tracks
            if track_name in ("dyads", "hemiola"):
                try:
                    notes = nct.add_non_chord_tones(notes, local_chords, scale)
                except Exception:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)  # noqa: S110

            # Offset and store
            if track_name not in tracks:
                tracks[track_name] = []
            for n in notes:
                tracks[track_name].append(
                    NoteInfo(
                        pitch=n.pitch, start=round(n.start + beat_offset, 6),
                        duration=n.duration, velocity=n.velocity,
                        articulation=n.articulation, expression=n.expression,
                    )
                )

        beat_offset += s_beats

    for k in tracks:
        tracks[k] = sorted(tracks[k], key=lambda n: n.start)

    # Articulations + pedal
    pedal_cc: dict[str, list[tuple[float, int, int]]] = {}
    for track_name in list(tracks.keys()):
        instrument = INSTRUMENT_MAP.get(track_name, "strings_pad")
        tracks[track_name] = art_engine.apply(tracks[track_name], instrument, beat_offset)
        raw = art_engine.add_sustain_pedal_events(tracks[track_name], beat_offset)
        if raw:
            pedal_cc[track_name] = [(e["time"], 64, e["value"]) for e in raw]

    tracks = _master_mix(tracks)
    return tracks, pedal_cc


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser(description="Dark Textures V1")
    p.add_argument("--duration", type=float, default=3.0)
    p.add_argument("--tempo", type=int, default=60)
    p.add_argument("--key", type=int, default=0)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="dark_textures_v1.mid")
    args = p.parse_args()

    duration = max(1.0, min(30.0, args.duration))
    bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual_sec = bars * 4 / args.tempo * 60

    key_name = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"][args.key]
    print(f"Dark Textures V1")
    print(
        f"  {duration:.1f} min requested → {actual_sec / 60:.1f} min actual "
        f"({bars} bars @ {args.tempo} BPM)"
    )
    print(f"  Key: {key_name}")
    print()

    tracks, pedal_cc = generate(duration, args.tempo, args.key, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"  Tracks: {len(tracks)}, Notes: {total}")
    for name, notes in sorted(tracks.items()):
        print(f"    {name:20s}: {len(notes):5d} notes")

    export_multitrack_midi(
        tracks, args.output, bpm=args.tempo, key=f"{key_name}m", cc_events=pedal_cc
    )
    print(f"\n  → {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
