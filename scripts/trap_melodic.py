
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
trap_melodic.py — Melodic trap with counter-melodies, call-response, and arp layers.

48 bars @ 140 BPM (half-time feel = 70 BPM groove)

  Intro (4) -> V1 (8) -> Pre (4) -> Hook (8) -> Break (4) -> V2 (8) -> Hook 2 (8) -> Outro (4)

Melodic philosophy:
  - Lead melody is king — MelodyGenerator with high harmony bias, tight range
  - Counter-melody answers the lead — contrary motion, different register
  - Arp layer fills the mid-range — converging pattern, soft
  - Call-response phrasing between lead and counter on hooks
  - 808 slides on hooks, basic on verses
  - Everything leaves space — no walls of sound
"""

import sys
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    GeneratorParams,
    MelodyGenerator,
    MarkovMelodyGenerator,
    CountermelodyGenerator,
    ArpeggiatorGenerator,
    ChordGenerator,
)
from melodica.generators.melody import MelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.call_response import CallResponseGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    LimitNoteRangeModifier,
    SwingController,
    CrescendoModifier,
    StaccatoLegatoModifier,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.render_context import RenderContext


SCALE = Scale(root=0, mode=Mode.HARMONIC_MINOR)  # C harmonic minor


# ── arrangement ──────────────────────────────────────────────────────────────

SECTIONS = [
    # Intro: pad whispers, arp hint, ghost hats — mood set
    ("Intro",   4,  ["pad", "arp_ghost", "hh_spare"]),

    # V1: drums + 808 enter, lead melody starts — vocal space
    ("V1",      8,  ["drums", "bass", "hihat", "pad", "lead"]),

    # Pre: counter-melody joins, ghost snares, 808 starts sliding — tension
    ("Pre",     4,  ["drums", "bass_slide", "hihat", "pad", "lead", "counter", "ghost"]),

    # Hook: everything — lead, counter, arp bright, call-response, chops
    ("Hook",    8,  ["drums_hard", "bass_slide", "hihat_trap", "pad", "lead_hook", "counter_hook",
                     "arp", "call_resp", "chops", "ghost"]),

    # Break: pad + lead + counter only — intimate, melodic
    ("Break",   4,  ["pad", "lead_soft", "counter_soft"]),

    # V2: drums + bass back, lead + counter, chops — full melodic verse
    ("V2",      8,  ["drums", "bass", "hihat", "pad", "lead", "counter", "chops"]),

    # Hook 2: same as Hook + riser
    ("Hook 2",  8,  ["drums_hard", "bass_slide", "hihat_trap", "pad", "lead_hook", "counter_hook",
                     "arp", "call_resp", "chops", "ghost", "riser"]),

    # Outro: pad + arp ghost + lead fade
    ("Outro",   4,  ["pad", "arp_ghost", "lead_fade", "impact"]),
]


# ── harmony ──────────────────────────────────────────────────────────────────

def harmonize(bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.30,
        secondary_dom_weight=0.12,
        extension_weight=0.08,
        repetition_penalty=0.07,
        cadence_weight=0.14,
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

        # ── melody family ──────────────────────────────────────────────

        case "lead":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.50),
                harmony_note_probability=0.72,
                note_range_low=60,
                note_range_high=76,
                note_repetition_probability=0.12,
                steps_probability=0.88,
            )
            mods += [HumanizeModifier(timing_std=0.02, velocity_std=6),
                     VelocityScalingModifier(scale=0.55)]

        case "lead_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.55),
                harmony_note_probability=0.78,
                note_range_low=62,
                note_range_high=79,
                note_repetition_probability=0.08,
                steps_probability=0.85,
            )
            mods += [HumanizeModifier(timing_std=0.015, velocity_std=5),
                     VelocityScalingModifier(scale=0.62)]

        case "lead_soft":
            gen = MarkovMelodyGenerator(
                params=GeneratorParams(density=0.30),
                harmony_note_probability=0.80,
                note_range_low=62,
                note_range_high=74,
                note_repetition_probability=0.20,
            )
            mods += [VelocityScalingModifier(scale=0.35),
                     HumanizeModifier(timing_std=0.03, velocity_std=3)]

        case "lead_fade":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.25),
                harmony_note_probability=0.75,
                note_range_low=60,
                note_range_high=72,
                note_repetition_probability=0.15,
                steps_probability=0.90,
            )
            mods += [CrescendoModifier(start_vel=50, end_vel=20),
                     HumanizeModifier(timing_std=0.04, velocity_std=3)]

        # ── counter-melody family ─────────────────────────────────────

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.40),
                motion_preference="contrary",
                dissonance_on_weak=True,
                interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=67, high=84),
                     VelocityScalingModifier(scale=0.40),
                     HumanizeModifier(timing_std=0.03, velocity_std=4)]

        case "counter_hook":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.50),
                motion_preference="mixed",
                dissonance_on_weak=True,
                interval_limit=9,
            )
            mods += [LimitNoteRangeModifier(low=67, high=84),
                     VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "counter_soft":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.25),
                motion_preference="oblique",
                dissonance_on_weak=False,
                interval_limit=5,
            )
            mods += [LimitNoteRangeModifier(low=67, high=80),
                     VelocityScalingModifier(scale=0.28),
                     HumanizeModifier(timing_std=0.04, velocity_std=2)]

        # ── arp ───────────────────────────────────────────────────────

        case "arp":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.50),
                pattern="converge",
                note_duration=0.35,
                octaves=2,
                voicing="spread",
            )
            mods += [LimitNoteRangeModifier(low=60, high=84),
                     VelocityScalingModifier(scale=0.40),
                     HumanizeModifier(timing_std=0.01, velocity_std=3)]

        case "arp_ghost":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.20),
                pattern="up_down",
                note_duration=0.5,
                octaves=1,
                voicing="spread",
            )
            mods += [LimitNoteRangeModifier(low=60, high=79),
                     VelocityScalingModifier(scale=0.22)]

        # ── call-response ─────────────────────────────────────────────

        case "call_resp":
            gen = CallResponseGenerator(
                params=GeneratorParams(density=0.40),
                call_length=3.0,
                response_length=1.0,
                call_direction="up",
                response_direction="down",
            )
            mods += [LimitNoteRangeModifier(low=64, high=84),
                     VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        # ── drums ─────────────────────────────────────────────────────

        case "drums":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.45),
                variant="standard",
                hat_roll_density=0.25,
                kick_pattern="standard",
            )

        case "drums_hard":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.55),
                variant="standard",
                hat_roll_density=0.45,
                kick_pattern="syncopated",
            )

        case "hihat":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.30),
                pattern="trap_eighth",
                roll_density=0.20,
                open_hat_probability=0.06,
            )
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))

        case "hihat_trap":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.45),
                pattern="trap_triplet",
                roll_density=0.40,
                open_hat_probability=0.04,
            )
            mods += [SwingController(swing_ratio=0.57, grid=0.5),
                     VelocityScalingModifier(scale=0.75)]

        case "hh_spare":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.12),
                pattern="sparse",
                roll_density=0.0,
                open_hat_probability=0.15,
            )
            mods.append(VelocityScalingModifier(scale=0.25))

        case "ghost":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.25),
                target="snare",
                pattern="hiphop",
                ghost_velocity=28,
                ghost_density=0.40,
                placement="sixteenth",
            )

        # ── bass ──────────────────────────────────────────────────────

        case "bass":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.40),
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.30,
            )
            mods += [LimitNoteRangeModifier(low=24, high=48),
                     VelocityScalingModifier(scale=0.85)]

        case "bass_slide":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.50),
                pattern="trap_syncopated",
                slide_type="chromatic",
                slide_probability=0.55,
            )
            mods += [LimitNoteRangeModifier(low=24, high=48),
                     VelocityScalingModifier(scale=0.90)]

        # ── pad ───────────────────────────────────────────────────────

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.25),
                mode="minor_pad",
                chord_dur=8.0,
                velocity_level=0.10,
                register="low",
                overlap=0.5,
            )

        # ── chops ─────────────────────────────────────────────────────

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.35),
                processing="pitch_shift",
                density=0.40,
                chop_pattern="syncopated",
                source_pitch=65,
            )
            mods += [VelocityScalingModifier(scale=0.38),
                     HumanizeModifier(timing_std=0.03, velocity_std=4)]

        # ── fx ────────────────────────────────────────────────────────

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
                pitch_drop=16,
            )

        case _:
            return None, []

    return gen, mods


# ── instruments ──────────────────────────────────────────────────────────────

INSTRUMENTS = {
    "lead":          81,    # Sawtooth Lead
    "lead_hook":     81,
    "lead_soft":     81,
    "lead_fade":     81,
    "counter":       52,    # Synth Strings 2
    "counter_hook":  52,
    "counter_soft":  52,
    "arp":           17,    # Percussive Organ
    "arp_ghost":     17,
    "call_resp":     80,    # Lead Square
    "drums":         0,
    "drums_hard":    0,
    "hihat":         0,
    "hihat_trap":    0,
    "hh_spare":      0,
    "ghost":         0,
    "bass":          38,    # Synth Bass 1
    "bass_slide":    38,
    "pad":           90,    # Polysynth pad
    "chops":         54,    # Synth Voice
    "riser":         97,
    "impact":        103,
}

PERC = {"drums", "drums_hard", "hihat", "hihat_trap", "hh_spare", "ghost"}


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
    ap = argparse.ArgumentParser(description="Melodic trap — melodies & counter-melodies")
    ap.add_argument("--tempo", type=int, default=140)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", type=str, default="trap_melodic.mid")
    args = ap.parse_args()

    bars = sum(s[1] for s in SECTIONS)
    mins = bars * 4 / args.tempo * 60
    print(f"Melodic Trap")
    print(f"  {mins:.1f} min ({bars} bars @ {args.tempo} BPM, half-time feel)")
    print(f"  C Harmonic Minor\n")

    tracks, cc = generate(args.tempo, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"\n  Tracks: {len(tracks)}, Notes: {total}")
    for n, ns in sorted(tracks.items()):
        print(f"    {n:18s}: {len(ns):5d} notes")

    export_multitrack_midi(tracks, args.output, bpm=args.tempo, key="Cm",
                           cc_events=cc, instruments=INSTRUMENTS)
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
