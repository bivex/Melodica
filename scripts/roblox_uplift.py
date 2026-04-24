# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-24
# Last Updated: 2026-04-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.
"""
roblox_uplift.py — Roblox Uplift Theme.

40 bars @ 128 BPM (~1.9 min)

  Intro (4) -> Verse (8) -> Build (4) -> Drop (8) -> Break (4) -> Drop 2 (8) -> Outro (4)

DNA: chiptune hook, supersaw uplift, driving house beat, bright arps,
     choir swells, brass stabs. Game energy with cinematic scale.
"""

import sys
import random
import warnings
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, MusicTimeline, KeyLabel
from melodica.generators import GeneratorParams
from melodica.generators.four_on_floor import FourOnFloorGenerator
from melodica.generators.chiptune import ChiptuneGenerator
from melodica.generators.supersaw_pad import SupersawPadGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.transition import TransitionGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.stinger import StingerGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    LimitNoteRangeModifier,
    CrescendoModifier,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.render_context import RenderContext


SCALE = Scale(root=0, mode=Mode.MAJOR)  # C Major — bright, uplifting


# ── arrangement ──────────────────────────────────────────────────────────────

SECTIONS = [
    # Intro: chiptune hook alone — establishes the theme, sparse
    ("Intro", 4, ["chip_lead"]),
    # Verse: drums + bass + ostinato enter, pad underlays — still restrained
    ("Verse", 8, ["drums", "bass", "chip_bass", "ostinato", "pad"]),
    # Build: arp rises, transition energy, piano stabs, riser — tension
    ("Build", 4, ["drums", "bass", "pad", "arp", "piano", "build_up", "riser"]),
    # Drop: full explosion — lead, pluck arp, brass, choir, everything hits
    (
        "Drop",
        8,
        ["drums", "bass", "pad", "lead", "arp", "chip_lead", "brass", "choir", "piano"],
    ),
    # Break: silence then choir + stinger — cinematic reset
    ("Break", 4, ["choir", "stinger", "pad_quiet"]),
    # Drop 2: everything back, choir louder, brass hits harder — peak energy
    (
        "Drop 2",
        8,
        ["drums", "bass", "pad", "lead", "arp", "chip_lead", "brass", "choir", "piano", "ostinato"],
    ),
    # Outro: chiptune callback + impact — the hook bookends the track
    ("Outro", 4, ["chip_lead", "impact"]),
]


# ── harmony ──────────────────────────────────────────────────────────────────


def harmonize(bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=6,
        melody_weight=0.30,
        secondary_dom_weight=0.15,
        extension_weight=0.10,
        repetition_penalty=0.04,
        cadence_weight=0.15,
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
            pc = int(degs[0]) if random.random() < 0.55 else int(degs[min(4, len(degs) - 1)])
        contour.append(NoteInfo(pitch=48 + pc, start=b * bpb, duration=bpb - 0.1, velocity=50))
    chords = harmonizer.harmonize(contour, SCALE, bars * bpb)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(
                root=int(degs[0]), quality=Quality.MAJOR, start=len(chords) * bpb, duration=bpb
            )
        )
    return chords


# ── tracks ───────────────────────────────────────────────────────────────────


def build(name):
    mods = []
    match name:
        # ── chiptune: the hook ────────────────────────────────────────────
        case "chip_lead":
            gen = ChiptuneGenerator(
                params=GeneratorParams(density=0.50),
                variant="nes_classic",
                channels=["pulse1"],
                duty_cycle="50%",
                arpeggio_speed=0.125,
                melody_style="arpeggio",
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=84),
                HumanizeModifier(timing_std=0.01, velocity_std=6),
                VelocityScalingModifier(scale=0.60),
            ]

        case "chip_bass":
            gen = ChiptuneGenerator(
                params=GeneratorParams(density=0.40),
                variant="nes_classic",
                channels=["triangle"],
                melody_style="stepwise",
            )
            mods += [LimitNoteRangeModifier(low=36, high=48), VelocityScalingModifier(scale=0.55)]

        # ── drums ────────────────────────────────────────────────────────
        case "drums":
            gen = FourOnFloorGenerator(
                params=GeneratorParams(density=0.60),
                variant="house",
            )

        # ── bass ─────────────────────────────────────────────────────────
        case "bass":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.50),
                waveform="saw",
                pattern="plucked",
            )
            mods += [LimitNoteRangeModifier(low=36, high=52), VelocityScalingModifier(scale=0.70)]

        # ── pad: big uplifting supersaw ──────────────────────────────────
        case "pad":
            gen = SupersawPadGenerator(
                params=GeneratorParams(density=0.25),
                variant="trance",
                voice_count=5,
                detune_amount=0.14,
                release_time=1.5,
                sidechain_feel=True,
            )

        case "pad_quiet":
            gen = SupersawPadGenerator(
                params=GeneratorParams(density=0.15),
                variant="ambient",
                voice_count=3,
                detune_amount=0.05,
                release_time=2.5,
                sidechain_feel=False,
            )
            mods += [VelocityScalingModifier(scale=0.20), CrescendoModifier(start_vel=20, end_vel=55)]

        # ── arp: bright 16th-note arpeggios ──────────────────────────────
        case "arp":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.55),
                pattern="up",
                note_duration=0.25,
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=84),
                HumanizeModifier(timing_std=0.008, velocity_std=3),
                VelocityScalingModifier(scale=0.40),
            ]

        # ── lead: main melody ────────────────────────────────────────────
        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.50),
                style="retro",
                portamento=0.08,
                note_length="mixed",
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=84),
                HumanizeModifier(timing_std=0.012, velocity_std=7),
                VelocityScalingModifier(scale=0.60),
            ]

        # ── ostinato: repeating hook pattern ─────────────────────────────
        case "ostinato":
            gen = OstinatoGenerator(
                params=GeneratorParams(density=0.50),
                pattern="1-3-5-3",
                repeat_notes=2,
            )
            mods += [
                LimitNoteRangeModifier(low=64, high=80),
                VelocityScalingModifier(scale=0.40),
                HumanizeModifier(timing_std=0.01, velocity_std=4),
            ]

        # ── piano: rhythmic chord stabs ──────────────────────────────────
        case "piano":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.50),
                comp_style="pop",
                voicing_type="close",
                accent_pattern="syncopated",
                chord_density=0.60,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=7),
                VelocityScalingModifier(scale=0.45),
            ]

        # ── choir: epic swells ───────────────────────────────────────────
        case "choir":
            gen = ChoirAahsGenerator(
                params=GeneratorParams(density=0.25),
                voice_count=4,
                dynamics="mf",
                vibrato=0.20,
                syllable="aah",
            )
            mods += [VelocityScalingModifier(scale=0.30), CrescendoModifier(start_vel=30, end_vel=75)]

        # ── brass: triumphant stabs ──────────────────────────────────────
        case "brass":
            gen = BrassSectionGenerator(
                params=GeneratorParams(density=0.30),
                articulation="fanfare",
                voicing="open",
                intensity=0.75,
                divisi_count=3,
                breath_gap=2.5,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.01, velocity_std=5)]

        # ── transitions ──────────────────────────────────────────────────
        case "build_up":
            gen = TransitionGenerator(
                params=GeneratorParams(density=0.45),
                transition_type="build",
                length_beats=16.0,
                octave_range=2,
                rhythm_acceleration=1.5,
                pitch_strategy="chord_tone",
            )

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.30),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=105,
            )

        case "stinger":
            gen = StingerGenerator(
                params=GeneratorParams(density=0.3),
                stinger_type="achievement",
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.3),
                impact_type="boom",
                tail_length=4.0,
                pitch_drop=12,
            )

        case _:
            return None, []

    return gen, mods


# ── instruments ──────────────────────────────────────────────────────────────

INSTRUMENTS = {
    "chip_lead": 80,   # Synth Square — 8-bit character
    "chip_bass": 38,   # Synth Bass 1
    "drums": 0,
    "bass": 38,        # Synth Bass 1
    "pad": 90,         # Polysynth pad
    "pad_quiet": 90,
    "arp": 88,         # Bright Pad
    "lead": 81,        # Sawtooth Lead
    "ostinato": 88,    # Bright Pad
    "piano": 1,        # Bright Piano
    "choir": 53,       # Choir Aahs
    "brass": 62,       # Brass Section
    "build_up": 81,
    "riser": 97,
    "stinger": 56,     # Trumpet
    "impact": 103,
}

PERC = {"drums"}


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

            abs_chords = [
                ChordLabel(
                    root=c.root,
                    quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration,
                    degree=c.degree,
                )
                for c in chords
            ]

            section_timeline = MusicTimeline(
                chords=abs_chords,
                keys=[KeyLabel(scale=SCALE, start=0, duration=s_beats)],
            )
            mc = ModifierContext(
                duration_beats=s_beats, chords=abs_chords, timeline=section_timeline, scale=SCALE
            )
            for m in mods:
                try:
                    notes = m.modify(notes, mc)
                except Exception as e:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)

            if tn not in tracks:
                tracks[tn] = []
            for n in notes:
                tracks[tn].append(
                    NoteInfo(
                        pitch=n.pitch,
                        start=round(n.start + beat_offset, 6),
                        duration=n.duration,
                        velocity=n.velocity,
                        articulation=n.articulation,
                        expression=n.expression,
                    )
                )

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
    ap = argparse.ArgumentParser(description="Roblox Uplift Theme")
    ap.add_argument("--tempo", type=int, default=128)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", type=str, default="roblox_uplift.mid")
    args = ap.parse_args()

    bars = sum(s[1] for s in SECTIONS)
    mins = bars * 4 / args.tempo * 60
    print(f"Roblox Uplift Theme")
    print(f"  {mins:.1f} min ({bars} bars @ {args.tempo} BPM)")
    print(f"  C Major\n")

    tracks, cc = generate(args.tempo, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"\n  Tracks: {len(tracks)}, Notes: {total}")
    for n, ns in sorted(tracks.items()):
        print(f"    {n:18s}: {len(ns):5d} notes")

    export_multitrack_midi(
        tracks, args.output, bpm=args.tempo, key="C", cc_events=cc, instruments=INSTRUMENTS
    )
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
