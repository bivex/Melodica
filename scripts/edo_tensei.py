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
edo_tensei.py — Edo Tensei (Impure World Reincarnation) Beat.

64 bars @ 85 BPM (~3.0 min)

  Intro (4) -> Rise (8) -> Theme (16) -> Break (4) -> Theme 2 (16) -> Decay (8) -> Outro (8)

Hirajoshi scale: dark Japanese pentatonic [0, 2, 3, 7, 8]
Vibe: ominous resurrection, shinobi darkness, ancient power awakening.

Register map:
  Sub:       24-36   dark_bass, drone
  Low:       36-48   (drums percussive)
  Mid-low:   48-60   pad, piano dark stabs
  Mid:       60-72   lead melody, horror texture
  Mid-high:  72-84   arp, strings
  High:      84-96   koto/chiptune theme
"""

import sys
import random
import warnings
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, MusicTimeline, KeyLabel
from melodica.generators import GeneratorParams
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.horror_dissonance import HorrorDissonanceGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.chiptune import ChiptuneGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.ostinato import OstinatoGenerator
from melodica.generators.transition import TransitionGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
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


SCALE = Scale(root=2, mode=Mode.HIROJOSHI)  # D Hirajoshi — dark Japanese pentatonic


# ── arrangement ──────────────────────────────────────────────────────────────
# 64 bars = ~3:00 @ 85 BPM

SECTIONS = [
    # Intro: drone + pad emerge from silence. Ancient power stirring.
    ("Intro", 4, ["drone", "dark_pad"]),
    # Rise: horror texture creeps in, chiptune koto hints at the theme. Tension builds.
    ("Rise", 8, ["drone", "dark_pad", "horror", "koto_theme", "riser"]),
    # Theme: full beat drops. Trap drums, dark bass, lead melody, arp, strings.
    (
        "Theme",
        16,
        ["drums", "dark_bass", "dark_pad", "lead", "arp", "strings", "koto_theme", "piano"],
    ),
    # Break: strip to drone + horror + koto. The reincarnation pauses. Tension reset.
    ("Break", 4, ["drone", "horror", "koto_theme"]),
    # Theme 2: everything returns harder. Add ostinato, drums switch to drill variant.
    (
        "Theme 2",
        16,
        ["drums", "dark_bass", "dark_pad", "lead", "arp", "strings", "koto_theme", "piano", "ostinato"],
    ),
    # Decay: beat fades, pad sustains, horror lingers. The jutsu dissipates.
    ("Decay", 8, ["dark_pad", "horror", "strings", "drone"]),
    # Outro: drone + impact. Silence falls.
    ("Outro", 8, ["drone", "impact"]),
]


# ── harmony ──────────────────────────────────────────────────────────────────


def harmonize(bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.25,
        secondary_dom_weight=0.08,
        extension_weight=0.05,
        repetition_penalty=0.06,
        cadence_weight=0.10,
    )
    degs = SCALE.degrees()
    contour = []
    for b in range(bars):
        p = b % 4
        if p == 0:
            pc = int(degs[0])
        elif p == 1:
            pc = int(degs[min(2, len(degs) - 1)])
        elif p == 2:
            pc = int(degs[min(3, len(degs) - 1)])
        else:
            pc = int(degs[0]) if random.random() < 0.5 else int(degs[min(1, len(degs) - 1)])
        contour.append(NoteInfo(pitch=38 + pc, start=b * bpb, duration=bpb - 0.1, velocity=45))
    chords = harmonizer.harmonize(contour, SCALE, bars * bpb)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(
                root=int(degs[0]), quality=Quality.MINOR, start=len(chords) * bpb, duration=bpb
            )
        )
    return chords


# ── tracks ───────────────────────────────────────────────────────────────────


def build(name):
    mods = []
    match name:
        # ── drone: sub-bass D pedal tone ─────────────────────────────────
        case "drone":
            gen = DroneGenerator(
                params=GeneratorParams(density=0.15),
                variant="tonic",
            )
            mods += [LimitNoteRangeModifier(low=24, high=36), VelocityScalingModifier(scale=0.50)]

        # ── dark pad: ominous atmosphere ─────────────────────────────────
        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.20),
                mode="minor_pad",
            )
            mods += [
                LimitNoteRangeModifier(low=48, high=60),
                VelocityScalingModifier(scale=0.35),
                CrescendoModifier(start_vel=20, end_vel=55),
            ]

        # ── trap drums: dark, minimal ───────────────────────────────────
        case "drums":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.50),
                variant="minimal",
            )

        # ── dark bass: doom bass ────────────────────────────────────────
        case "dark_bass":
            gen = DarkBassGenerator(
                params=GeneratorParams(density=0.40),
                mode="doom",
                octave=2,
                velocity_level=0.65,
            )
            mods += [LimitNoteRangeModifier(low=24, high=40), VelocityScalingModifier(scale=0.70)]

        # ── horror texture: ambient dread ───────────────────────────────
        case "horror":
            gen = HorrorDissonanceGenerator(
                params=GeneratorParams(density=0.25),
                variant="ambient_dread",
                dissonance_level=0.5,
                silence_probability=0.3,
                pitch_drift=0.2,
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=72),
                VelocityScalingModifier(scale=0.45),
            ]

        # ── koto theme: chiptune as koto/shamisen ───────────────────────
        case "koto_theme":
            gen = ChiptuneGenerator(
                params=GeneratorParams(density=0.30),
                variant="nes_classic",
                channels=["pulse1"],
                duty_cycle="25%",
                arpeggio_speed=0.25,
                melody_style="jumping",
            )
            mods += [
                LimitNoteRangeModifier(low=84, high=96),
                HumanizeModifier(timing_std=0.02, velocity_std=6),
                VelocityScalingModifier(scale=0.65),
            ]

        # ── lead: dark melody in mid register ───────────────────────────
        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.40),
                style="retro",
                portamento=0.20,
                note_length="mixed",
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=72),
                HumanizeModifier(timing_std=0.02, velocity_std=7),
                VelocityScalingModifier(scale=0.70),
            ]

        # ── arp: dark descending arpeggios ──────────────────────────────
        case "arp":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.45),
                pattern="down",
                note_duration=0.5,
            )
            mods += [
                LimitNoteRangeModifier(low=72, high=84),
                HumanizeModifier(timing_std=0.01, velocity_std=4),
                VelocityScalingModifier(scale=0.55),
            ]

        # ── strings: sustained for dark cinematic ──────────────────────
        case "strings":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.20),
                articulation="sustained",
                section_size="chamber",
                divisi=3,
                dynamic_curve="swell",
            )
            mods += [LimitNoteRangeModifier(low=72, high=84), VelocityScalingModifier(scale=0.45)]

        # ── piano: dark stabs ───────────────────────────────────────────
        case "piano":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.35),
                comp_style="jazz",
                voicing_type="shell",
                accent_pattern="charleston",
                chord_density=0.45,
            )
            mods += [
                LimitNoteRangeModifier(low=48, high=60),
                HumanizeModifier(timing_std=0.02, velocity_std=8),
                VelocityScalingModifier(scale=0.65),
            ]

        # ── ostinato: repeating hirajoshi pattern ───────────────────────
        case "ostinato":
            gen = OstinatoGenerator(
                params=GeneratorParams(density=0.35),
                pattern="1-3-5-3",
                repeat_notes=2,
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=72),
                VelocityScalingModifier(scale=0.55),
                HumanizeModifier(timing_std=0.01, velocity_std=4),
            ]

        # ── transitions ──────────────────────────────────────────────────
        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.25),
                riser_type="synth",
                length_beats=8.0,
                pitch_curve="linear",
                peak_velocity=95,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.3),
                impact_type="boom",
                tail_length=6.0,
                pitch_drop=18,
            )

        case _:
            return None, []

    return gen, mods


# ── instruments ──────────────────────────────────────────────────────────────

INSTRUMENTS = {
    "drone": 89,       # New Age pad
    "dark_pad": 91,    # Pad 3 (choir)
    "drums": 0,
    "dark_bass": 38,   # Synth Bass 1
    "horror": 95,      # Atmosphere
    "koto_theme": 107, # Koto
    "lead": 81,        # Sawtooth Lead
    "arp": 88,         # Bright Pad
    "strings": 45,     # Tremolo Strings
    "piano": 1,        # Bright Piano
    "ostinato": 81,    # Sawtooth Lead
    "riser": 97,
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
    ap = argparse.ArgumentParser(description="Edo Tensei — Hirajoshi Beat")
    ap.add_argument("--tempo", type=int, default=85)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", type=str, default="edo_tensei.mid")
    args = ap.parse_args()

    bars = sum(s[1] for s in SECTIONS)
    secs = bars * 4 / args.tempo * 60
    print(f"Edo Tensei — Hirajoshi Beat")
    print(f"  {secs:.0f}s = {secs / 60:.1f}min ({bars} bars @ {args.tempo} BPM)")
    print(f"  D Hirajoshi [0,2,3,7,8]\n")

    tracks, cc = generate(args.tempo, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"\n  Tracks: {len(tracks)}, Notes: {total}")
    for n, ns in sorted(tracks.items()):
        print(f"    {n:18s}: {len(ns):5d} notes")

    export_multitrack_midi(
        tracks, args.output, bpm=args.tempo, key="Dm", cc_events=cc, instruments=INSTRUMENTS
    )
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
