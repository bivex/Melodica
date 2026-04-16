
# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-16
# Last Updated: 2026-04-16
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
afro_beat.py — Afrobeats with proper arrangement.

44 bars @ 108 BPM (~2.7 min)

  Intro (4) -> V1 (8) -> Hook (8) -> Break (4) -> V2 (8) -> Hook 2 (8) -> Outro (4)

DNA: afrobeats drums, log drum, shaker, highlife guitar, pad, lead, chops.
Each section has character — no lazy +/- one track.
"""

import sys
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.afrobeats import AfrobeatsGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator
from melodica.generators.highlife_guitar import HighlifeGuitarGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    LimitNoteRangeModifier,
    SwingController,
    CrescendoModifier,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.render_context import RenderContext


SCALE = Scale(root=9, mode=Mode.DORIAN)  # A Dorian — bright but minor


# ── arrangement ──────────────────────────────────────────────────────────────

SECTIONS = [
    # Intro: percussion sets the groove, pad hints at harmony
    ("Intro",   4,  ["afro_perc", "pad"]),

    # V1: full drums + bass enter, guitar starts the pattern — room for vocal
    ("V1",      8,  ["afro_drums", "bass", "guitar", "pad", "shaker"]),

    # Hook: everything opens up — lead, guitar busier, chops, afro perc accents
    ("Hook",    8,  ["afro_drums", "bass", "guitar_hook", "pad", "lead", "chops", "afro_perc", "shaker"]),

    # Break: strip to percussion + guitar + pad — groove keeps, energy drops
    ("Break",   4,  ["afro_perc", "guitar_soft", "pad", "shaker"]),

    # V2: drums + bass back, guitar + chops — busier than V1
    ("V2",      8,  ["afro_drums", "bass", "guitar", "pad", "chops", "shaker"]),

    # Hook 2: same as Hook + riser going in
    ("Hook 2",  8,  ["afro_drums", "bass", "guitar_hook", "pad", "lead", "chops", "afro_perc", "shaker", "riser"]),

    # Outro: groove fades, percussion last to go
    ("Outro",   4,  ["afro_perc", "pad", "impact"]),
]


# ── harmony ──────────────────────────────────────────────────────────────────

def harmonize(bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.25,
        secondary_dom_weight=0.10,
        extension_weight=0.07,
        repetition_penalty=0.08,
        cadence_weight=0.10,
    )
    degs = SCALE.degrees()
    contour = []
    for b in range(bars):
        p = b % 4
        if p == 0:
            pc = int(degs[0])
        elif p == 1:
            pc = int(degs[min(3, len(degs) - 1)])
        elif p == 2:
            pc = int(degs[min(4, len(degs) - 1)] if len(degs) > 4 else degs[min(2, len(degs) - 1)])
        else:
            pc = int(degs[0]) if random.random() < 0.5 else int(degs[min(2, len(degs) - 1)])
        contour.append(NoteInfo(pitch=45 + pc, start=b * bpb, duration=bpb - 0.1, velocity=52))
    chords = harmonizer.harmonize(contour, SCALE, bars * bpb)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(root=int(degs[0]), quality=Quality.MINOR,
                            start=len(chords) * bpb, duration=bpb)
        )
    return chords


# ── tracks ───────────────────────────────────────────────────────────────────

def build(name):
    mods = []
    match name:

        case "afro_drums":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.55),
                variant="afrobeats",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.5,
                percussion_layer=False,
            )

        case "afro_perc":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.45),
                ensemble="west_african",
                density=0.50,
                include_pitched=True,
                call_response=True,
                swing=0.55,
            )

        case "bass":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.45),
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.35,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52),
                     VelocityScalingModifier(scale=0.80)]

        case "guitar":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.55),
                variant="highlife",
                riff_density=0.60,
                palm_mute_ratio=0.30,
                octave_doubling=True,
                interlocking=False,
                pentatonic_bias=0.7,
            )
            mods += [HumanizeModifier(timing_std=0.02, velocity_std=5),
                     VelocityScalingModifier(scale=0.55)]

        case "guitar_hook":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.60),
                variant="afrobeat",
                riff_density=0.75,
                palm_mute_ratio=0.20,
                octave_doubling=True,
                interlocking=True,
                pentatonic_bias=0.65,
            )
            mods += [HumanizeModifier(timing_std=0.02, velocity_std=4),
                     VelocityScalingModifier(scale=0.60)]

        case "guitar_soft":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.30),
                variant="palm_wine",
                riff_density=0.40,
                palm_mute_ratio=0.10,
                octave_doubling=False,
                interlocking=False,
                pentatonic_bias=0.8,
            )
            mods += [VelocityScalingModifier(scale=0.35),
                     HumanizeModifier(timing_std=0.03, velocity_std=3)]

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.25),
                mode="minor_pad",
                chord_dur=8.0,
                velocity_level=0.10,
                register="low",
                overlap=0.5,
            )

        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.40),
                style="retro",
                portamento=0.15,
                note_length="mixed",
            )
            mods += [LimitNoteRangeModifier(low=60, high=80),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     VelocityScalingModifier(scale=0.50)]

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.40),
                processing="pitch_shift",
                density=0.45,
                chop_pattern="syncopated",
                source_pitch=64,
            )
            mods += [VelocityScalingModifier(scale=0.40),
                     HumanizeModifier(timing_std=0.03, velocity_std=4)]

        case "shaker":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.30),
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.45,
                percussion_layer=True,
            )
            mods.append(VelocityScalingModifier(scale=0.40))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.30),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=95,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.3),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=14,
            )

        case _:
            return None, []

    return gen, mods


# ── instruments ──────────────────────────────────────────────────────────────

INSTRUMENTS = {
    "afro_drums":    0,
    "afro_perc":     0,
    "bass":          38,    # Synth Bass 1
    "guitar":        25,    # Nylon Guitar
    "guitar_hook":   28,    # Electric Guitar (clean)
    "guitar_soft":   25,    # Nylon Guitar
    "pad":           90,    # Polysynth pad
    "lead":          81,    # Sawtooth Lead
    "chops":         54,    # Synth Voice
    "shaker":        0,
    "riser":         97,
    "impact":        103,
}

PERC = {"afro_drums", "afro_perc", "shaker"}


# ── generate ─────────────────────────────────────────────────────────────────

def generate(tempo, seed):
    if seed is not None:
        random.seed(seed)

    bpb = 4
    tracks: dict[str, list[NoteInfo]] = {}
    contexts: dict[str, RenderContext] = {}
    art = ArticulationEngine()
    beat_offset = 0.0

    for name, bars, trks in SECTIONS:
        s_beats = bars * bpb
        chords = harmonize(bars, bpb)
        print(f"  [{name:8s}] {bars:2d} bars | {', '.join(trks)}")

        for tn in trks:
            gen, mods = build(tn)
            if gen is None:
                continue

            prev = contexts.get(tn)
            ctx = RenderContext(
                prev_pitch=prev.prev_pitch if prev else None,
                prev_velocity=prev.prev_velocity if prev else None,
                prev_chord=prev.prev_chord if prev else None,
                prev_pitches=list(prev.prev_pitches) if prev else [],
                current_scale=SCALE,
            )

            notes = gen.render(chords, SCALE, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                contexts[tn] = gen._last_context

            mc = ModifierContext(duration_beats=s_beats, chords=chords, timeline=None, scale=SCALE)
            for m in mods:
                try:
                    notes = m.modify(notes, mc)
                except Exception:
                    pass

            if tn not in tracks:
                tracks[tn] = []
            for n in notes:
                tracks[tn].append(NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + beat_offset, 6),
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=n.expression,
                ))

        beat_offset += s_beats

    for k in tracks:
        tracks[k].sort(key=lambda n: n.start)

    cc = {}
    for tn in list(tracks):
        if tn not in PERC:
            tracks[tn] = art.apply(tracks[tn], tn, beat_offset)
            raw = art.add_sustain_pedal_events(tracks[tn], beat_offset)
            if raw:
                cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, cc


def main():
    ap = argparse.ArgumentParser(description="Afro beat")
    ap.add_argument("--tempo", type=int, default=108)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", type=str, default="afro_beat.mid")
    args = ap.parse_args()

    bars = sum(s[1] for s in SECTIONS)
    mins = bars * 4 / args.tempo * 60
    print(f"Afro Beat")
    print(f"  {mins:.1f} min ({bars} bars @ {args.tempo} BPM)")
    print(f"  A Dorian\n")

    tracks, cc = generate(args.tempo, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"\n  Tracks: {len(tracks)}, Notes: {total}")
    for n, ns in sorted(tracks.items()):
        print(f"    {n:18s}: {len(ns):5d} notes")

    export_multitrack_midi(tracks, args.output, bpm=args.tempo, key="Am",
                           cc_events=cc, instruments=INSTRUMENTS)
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
