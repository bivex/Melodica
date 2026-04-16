
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
lyric_beat.py — Beat built for vocals. Space to breathe, groove to ride.

44 bars @ 78 BPM (~2.8 min)

  Intro (4) -> V1 (8) -> Pre (4) -> Hook (8) -> Break (4) -> V2 (8) -> Hook 2 (8) -> Outro (4)

Each section has its own identity — no copy-paste.
Tracks enter/exit with purpose, not just "add one more".
"""

import sys
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.pluck_sequence import PluckSequenceGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.phonk import PhonkGenerator
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


SCALE = Scale(root=9, mode=Mode.NATURAL_MINOR)  # Am


# ── arrangement ──────────────────────────────────────────────────────────────
#
# Intro:    pad + faint cowbell — mood set, no drums yet
# V1:       drums + 808 + hats — pocket groove, empty space for vocal
# Pre:      riser + 808 slides + ghost snares — tension ramp
# Hook:     full — drums hard, 808 slide, lead, pluck, chops, cowbell
# Break:    pad + half-time 808 + quiet chops — breathe before V2
# V2:       drums + 808 + hats + ghost + chops — busier than V1
# Hook 2:   same as Hook + riser going in
# Outro:    pad + bass fade + impact

SECTIONS = [
    ("Intro",   4,  ["pad", "cowbell_ghost"]),
    ("V1",      8,  ["drums", "bass_808", "hihat", "pad"]),
    ("Pre",     4,  ["bass_slide", "ghost", "riser"]),
    ("Hook",    8,  ["drums_hard", "bass_slide", "hihat_trap", "pad", "lead", "pluck", "chops", "cowbell"]),
    ("Break",   4,  ["pad", "bass_half", "chops_quiet"]),
    ("V2",      8,  ["drums", "bass_808", "hihat", "pad", "ghost", "chops"]),
    ("Hook 2",  8,  ["drums_hard", "bass_slide", "hihat_trap", "pad", "lead", "pluck", "chops", "cowbell", "riser"]),
    ("Outro",   4,  ["pad", "bass_half", "impact"]),
]


# ── harmony ──────────────────────────────────────────────────────────────────

def harmonize(bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.28,
        secondary_dom_weight=0.10,
        extension_weight=0.06,
        repetition_penalty=0.07,
        cadence_weight=0.12,
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
        contour.append(NoteInfo(pitch=45 + pc, start=b * bpb, duration=bpb - 0.1, velocity=50))
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

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.4),
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.30,
            )
            mods += [LimitNoteRangeModifier(low=24, high=48), VelocityScalingModifier(scale=0.85)]

        case "bass_slide":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.5),
                pattern="trap_syncopated",
                slide_type="chromatic",
                slide_probability=0.55,
            )
            mods += [LimitNoteRangeModifier(low=24, high=48), VelocityScalingModifier(scale=0.90)]

        case "bass_half":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.25),
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.15,
            )
            mods += [LimitNoteRangeModifier(low=24, high=48),
                     VelocityScalingModifier(scale=0.55),
                     CrescendoModifier(start_vel=65, end_vel=30)]

        case "drums":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.45),
                variant="standard",
                hat_roll_density=0.20,
                kick_pattern="standard",
            )

        case "drums_hard":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.55),
                variant="standard",
                hat_roll_density=0.40,
                kick_pattern="syncopated",
            )

        case "hihat":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.30),
                pattern="trap_eighth",
                roll_density=0.15,
                open_hat_probability=0.06,
            )
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))

        case "hihat_trap":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.45),
                pattern="trap_triplet",
                roll_density=0.35,
                open_hat_probability=0.05,
            )
            mods += [SwingController(swing_ratio=0.57, grid=0.5),
                     VelocityScalingModifier(scale=0.75)]

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
                portamento=0.18,
                note_length="mixed",
            )
            mods += [LimitNoteRangeModifier(low=60, high=79),
                     HumanizeModifier(timing_std=0.025, velocity_std=5),
                     VelocityScalingModifier(scale=0.50)]

        case "pluck":
            gen = PluckSequenceGenerator(
                params=GeneratorParams(density=0.40),
                pattern="offbeat",
                decay_time=0.2,
                pitch_randomization=0.1,
                pitch_range=4,
            )
            mods += [LimitNoteRangeModifier(low=62, high=80),
                     VelocityScalingModifier(scale=0.40),
                     HumanizeModifier(timing_std=0.02, velocity_std=3)]

        case "ghost":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.25),
                target="snare",
                pattern="hiphop",
                ghost_velocity=30,
                ghost_density=0.45,
                placement="sixteenth",
            )

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.40),
                processing="pitch_shift",
                density=0.45,
                chop_pattern="syncopated",
                source_pitch=64,
            )
            mods += [VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.03, velocity_std=4)]

        case "chops_quiet":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.20),
                processing="formant",
                density=0.25,
                chop_pattern="offbeat",
                source_pitch=60,
            )
            mods += [VelocityScalingModifier(scale=0.25),
                     HumanizeModifier(timing_std=0.05, velocity_std=2)]

        case "cowbell":
            gen = PhonkGenerator(
                params=GeneratorParams(density=0.35),
                variant="classic_phonk",
                cowbell_density=0.60,
                bass_slide_amount=0,
                memphis_chops=False,
                aggression=0.40,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "cowbell_ghost":
            gen = PhonkGenerator(
                params=GeneratorParams(density=0.10),
                variant="lofi_phonk",
                cowbell_density=0.20,
                bass_slide_amount=0,
                memphis_chops=False,
                aggression=0.10,
            )
            mods.append(VelocityScalingModifier(scale=0.20))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.35),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=100,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.3),
                impact_type="boom",
                tail_length=3.5,
                pitch_drop=16,
            )

        case _:
            return None, []

    return gen, mods


# ── instruments ──────────────────────────────────────────────────────────────

INSTRUMENTS = {
    "bass_808":      38,    # Synth Bass 1
    "bass_slide":    38,
    "bass_half":     38,
    "drums":         0,
    "drums_hard":    0,
    "hihat":         0,
    "hihat_trap":    0,
    "pad":           90,    # Polysynth pad
    "lead":          81,    # Sawtooth Lead
    "pluck":         17,    # Percussive Organ
    "ghost":         0,
    "chops":         54,    # Synth Voice
    "chops_quiet":   54,
    "cowbell":       0,
    "cowbell_ghost": 0,
    "riser":         97,
    "impact":        103,
}

PERC = {"drums", "drums_hard", "hihat", "hihat_trap", "ghost", "cowbell", "cowbell_ghost"}


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
    ap = argparse.ArgumentParser(description="Lyric beat — space for vocals")
    ap.add_argument("--tempo", type=int, default=78)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", type=str, default="lyric_beat.mid")
    args = ap.parse_args()

    bars = sum(s[1] for s in SECTIONS)
    mins = bars * 4 / args.tempo * 60
    print(f"Lyric Beat")
    print(f"  {mins:.1f} min ({bars} bars @ {args.tempo} BPM)")
    print(f"  Am\n")

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
