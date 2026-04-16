
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
upbeat_rnb.py — Upbeat R&B with pocket groove, Rhodes comping, and soul.

48 bars @ 98 BPM (~3.3 min)

  Intro (4) -> V1 (8) -> Pre (4) -> Hook (8) -> Break (4) -> V2 (8) -> Hook 2 (8) -> Outro (4)

DNA:
  - MelodyGenerator / MarkovMelodyGenerator for intelligent melodies
  - CountermelodyGenerator for hook counter-lines
  - GrooveGenerator drives the pocket (soul/funk)
  - WalkingBass + BassSlap for melodic low-end
  - PianoComp (Rhodes) with syncopated rootless voicings
  - ModernChordPattern with min7/maj9 — the R&B extended harmony sound
  - OrganDrawbars gospel pad underneath
  - GuitarStrumming funk dead-strum stabs
  - BackbeatGenerator chop mode on 2 & 4
  - GhostNotesGenerator funk feel
  - Vocal chops for hooks
"""

import sys
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.groove import GrooveGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.bass_slap import BassSlapGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.modern_chord import ModernChordPatternGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.backbeat import BackbeatGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.markov import MarkovMelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
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


SCALE = Scale(root=10, mode=Mode.DORIAN)  # Bb Dorian — soul/R&B


# ── arrangement ──────────────────────────────────────────────────────────────

SECTIONS = [
    # Intro: Rhodes whispers, bass hint, groove tease — mood set
    ("Intro",   4,  ["keys_warmup", "bass_hint", "groove_hint"]),

    # V1: pocket locks — groove, walking bass, keys comp, organ pad, melody starts
    ("V1",      8,  ["groove", "bass", "keys_comp", "organ", "backbeat", "ghost", "melody"]),

    # Pre: bass goes slap, chords busier, backbeat intensifies — tension ramp
    ("Pre",     4,  ["bass_slap", "keys_busy", "backbeat_up", "organ", "ghost", "melody_pre", "riser"]),

    # Hook: everything — groove full, slap bass, funk guitar, chops, melody + counter
    ("Hook",    8,  ["groove_full", "bass_slap_hook", "keys_hook", "guitar_funk", "chops",
                     "backbeat_hook", "ghost_hook", "melody_hook", "counter"]),

    # Break: strip to Rhodes + organ + walking bass + solo melody — breathe
    ("Break",   4,  ["keys_soft", "organ_soft", "bass_walk", "melody_solo"]),

    # V2: groove back, guitar enters, chops — busier than V1
    ("V2",      8,  ["groove", "bass", "keys_comp", "guitar_funk", "ghost", "chops", "melody"]),

    # Hook 2: same as Hook + riser going in
    ("Hook 2",  8,  ["groove_full", "bass_slap_hook", "keys_hook", "guitar_funk", "chops",
                     "backbeat_hook", "ghost_hook", "melody_hook", "counter", "riser"]),

    # Outro: Rhodes + organ fade, walking bass, impact
    ("Outro",   4,  ["keys_soft", "organ_soft", "bass_walk", "impact"]),
]


# ── harmony ──────────────────────────────────────────────────────────────────

def harmonize(bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.22,
        secondary_dom_weight=0.12,
        extension_weight=0.10,
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
            pc = int(degs[min(3, len(degs) - 1)])
        elif p == 2:
            pc = int(degs[min(4, len(degs) - 1)] if len(degs) > 4 else degs[min(2, len(degs) - 1)])
        else:
            pc = int(degs[0]) if random.random() < 0.5 else int(degs[min(2, len(degs) - 1)])
        contour.append(NoteInfo(pitch=46 + pc, start=b * bpb, duration=bpb - 0.1, velocity=48))
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

        # ── groove ──────────────────────────────────────────────────

        case "groove_hint":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.15),
                groove_pattern="soul",
                ghost_note_vel=25,
                accent_vel=80,
            )
            mods.append(VelocityScalingModifier(scale=0.25))

        case "groove":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.45),
                groove_pattern="soul",
                ghost_note_vel=30,
                accent_vel=105,
            )
            mods.append(HumanizeModifier(timing_std=0.01, velocity_std=6))

        case "groove_full":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.55),
                groove_pattern="funk_1",
                ghost_note_vel=32,
                accent_vel=110,
            )
            mods += [HumanizeModifier(timing_std=0.01, velocity_std=5),
                     SwingController(swing_ratio=0.56, grid=0.5)]

        # ── bass ────────────────────────────────────────────────────

        case "bass_hint":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.15),
                approach_style="mixed",
                connect_roots=True,
                add_chromatic_passing=False,
                swing_eighth_ratio=0.62,
            )
            mods += [LimitNoteRangeModifier(low=30, high=50),
                     VelocityScalingModifier(scale=0.30)]

        case "bass":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.45),
                approach_style="mixed",
                connect_roots=True,
                add_chromatic_passing=True,
                swing_eighth_ratio=0.65,
            )
            mods += [LimitNoteRangeModifier(low=30, high=54),
                     VelocityScalingModifier(scale=0.70),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "bass_walk":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.30),
                approach_style="diatonic",
                connect_roots=True,
                add_chromatic_passing=False,
                swing_eighth_ratio=0.60,
            )
            mods += [LimitNoteRangeModifier(low=30, high=50),
                     VelocityScalingModifier(scale=0.45),
                     CrescendoModifier(start_vel=60, end_vel=30)]

        case "bass_slap":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.50),
                slap_pattern="funky",
                ghost_note_prob=0.35,
                pop_probability=0.40,
                octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=55),
                     VelocityScalingModifier(scale=0.72),
                     HumanizeModifier(timing_std=0.01, velocity_std=5)]

        case "bass_slap_hook":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.55),
                slap_pattern="slap_pop",
                ghost_note_prob=0.40,
                pop_probability=0.50,
                octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=55),
                     VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.01, velocity_std=4)]

        # ── keys (Rhodes / EP) ──────────────────────────────────────

        case "keys_warmup":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15),
                comp_style="pop",
                voicing_type="rootless",
                accent_pattern="syncopated",
                chord_density=0.40,
            )
            mods += [VelocityScalingModifier(scale=0.25),
                     HumanizeModifier(timing_std=0.03, velocity_std=4)]

        case "keys_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.40),
                comp_style="jazz",
                voicing_type="rootless",
                accent_pattern="syncopated",
                chord_density=0.65,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76),
                     VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.56, grid=0.5)]

        case "keys_busy":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.50),
                extension="min7",
                stab_pattern="dense",
                voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76),
                     VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.45),
                extension="maj9",
                stab_pattern="syncopated",
                voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76),
                     VelocityScalingModifier(scale=0.50),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.5)]

        case "keys_soft":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.20),
                comp_style="pop",
                voicing_type="shell",
                accent_pattern="2_4",
                chord_density=0.35,
            )
            mods += [LimitNoteRangeModifier(low=48, high=72),
                     VelocityScalingModifier(scale=0.30),
                     HumanizeModifier(timing_std=0.04, velocity_std=3)]

        # ── organ ───────────────────────────────────────────────────

        case "organ":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.25),
                registration="gospel",
                leslie_speed="slow",
                percussion=True,
                vibrato=False,
                sustain_bars=1.0,
            )

        case "organ_soft":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.15),
                registration="ballad",
                leslie_speed="slow",
                percussion=False,
                vibrato=True,
                sustain_bars=1.5,
            )
            mods.append(VelocityScalingModifier(scale=0.30))

        # ── guitar ──────────────────────────────────────────────────

        case "guitar_funk":
            gen = GuitarStrummingGenerator(
                params=GeneratorParams(density=0.45),
                strum_pattern="funk",
                palm_mute_ratio=0.35,
                accent_velocity=1.15,
                dead_strums=True,
                strum_delay=0.012,
                string_count=6,
            )
            mods += [LimitNoteRangeModifier(low=40, high=67),
                     VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.015, velocity_std=5),
                     SwingController(swing_ratio=0.56, grid=0.5)]

        # ── backbeat ────────────────────────────────────────────────

        case "backbeat":
            gen = BackbeatGenerator(
                params=GeneratorParams(density=0.35),
                mode="chop",
                accent_velocity=0.90,
                ghost_velocity=0.35,
                subdivision=0.5,
                pitch_strategy="chord_tone",
            )

        case "backbeat_up":
            gen = BackbeatGenerator(
                params=GeneratorParams(density=0.45),
                mode="ghost",
                accent_velocity=1.05,
                ghost_velocity=0.40,
                subdivision=0.5,
                pitch_strategy="chord_tone",
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "backbeat_hook":
            gen = BackbeatGenerator(
                params=GeneratorParams(density=0.50),
                mode="chop",
                accent_velocity=1.10,
                ghost_velocity=0.40,
                subdivision=0.5,
                pitch_strategy="chord_tone",
            )
            mods += [VelocityScalingModifier(scale=0.60),
                     HumanizeModifier(timing_std=0.01, velocity_std=4)]

        # ── ghost notes ─────────────────────────────────────────────

        case "ghost":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.30),
                target="snare",
                pattern="funk",
                ghost_velocity=32,
                ghost_density=0.45,
                placement="sixteenth",
            )
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))

        case "ghost_hook":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.40),
                target="snare",
                pattern="funk",
                ghost_velocity=35,
                ghost_density=0.55,
                placement="sixteenth",
            )
            mods += [SwingController(swing_ratio=0.56, grid=0.5),
                     VelocityScalingModifier(scale=0.65)]

        # ── melody — professional melodic intelligence ──────────────

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.40),
                harmony_note_probability=0.68,
                note_range_low=58,
                note_range_high=79,
                note_repetition_probability=0.12,
                steps_probability=0.88,
                random_movement=0.75,
                first_note="any_chord",
                last_note="last_chord_root",
                after_leap="step_opposite",
                climax="first_plus_maj3",
            )
            mods += [LimitNoteRangeModifier(low=58, high=79),
                     VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.55, grid=0.5)]

        case "melody_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.50),
                harmony_note_probability=0.72,
                note_range_low=60,
                note_range_high=82,
                note_repetition_probability=0.08,
                steps_probability=0.85,
                random_movement=0.70,
                first_note="chord_root",
                last_note="last_chord_root",
                after_leap="step_opposite",
                climax="up_5th",
                penultimate_step_above=True,
            )
            mods += [LimitNoteRangeModifier(low=60, high=82),
                     VelocityScalingModifier(scale=0.55),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.5)]

        case "melody_pre":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45),
                harmony_note_probability=0.65,
                note_range_low=58,
                note_range_high=80,
                note_repetition_probability=0.10,
                steps_probability=0.90,
                random_movement=0.70,
                first_note="scale",
                last_note="any",
                after_leap="step_any",
                climax="up_octave",
            )
            mods += [LimitNoteRangeModifier(low=58, high=80),
                     VelocityScalingModifier(scale=0.42),
                     CrescendoModifier(start_vel=40, end_vel=72),
                     HumanizeModifier(timing_std=0.02, velocity_std=5)]

        case "melody_solo":
            gen = MarkovMelodyGenerator(
                params=GeneratorParams(density=0.35),
                harmony_note_probability=0.75,
                note_range_low=58,
                note_range_high=77,
                note_repetition_probability=0.18,
                direction_bias=0.05,
            )
            mods += [LimitNoteRangeModifier(low=58, high=77),
                     VelocityScalingModifier(scale=0.40),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     CrescendoModifier(start_vel=55, end_vel=30)]

        # ── counter-melody ──────────────────────────────────────────

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.35),
                motion_preference="mixed",
                dissonance_on_weak=True,
                interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=65, high=84),
                     VelocityScalingModifier(scale=0.38),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.5)]

        # ── chops ───────────────────────────────────────────────────

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.40),
                processing="pitch_shift",
                density=0.45,
                chop_pattern="syncopated",
                source_pitch=65,
            )
            mods += [VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.5)]

        # ── fx ──────────────────────────────────────────────────────

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.30),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=90,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.3),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=12,
            )

        case _:
            return None, []

    return gen, mods


# ── instruments ──────────────────────────────────────────────────────────────

INSTRUMENTS = {
    "groove_hint":       0,
    "groove":            0,
    "groove_full":       0,
    "bass_hint":         33,    # Electric Bass (finger)
    "bass":              33,
    "bass_walk":         33,
    "bass_slap":         36,    # Slap Bass 1
    "bass_slap_hook":    36,
    "keys_warmup":        4,    # Electric Piano 1 (Rhodes)
    "keys_comp":          4,
    "keys_busy":          4,
    "keys_hook":          4,
    "keys_soft":          4,
    "organ":             16,    # Drawbar Organ
    "organ_soft":        16,
    "guitar_funk":       27,    # Clean Guitar
    "backbeat":           0,
    "backbeat_up":        0,
    "backbeat_hook":      0,
    "ghost":              0,
    "ghost_hook":         0,
    "melody":            82,    # Sawtooth Lead
    "melody_hook":       82,
    "melody_pre":        82,
    "melody_solo":        5,    # Electric Piano 2 (DX Rhodes)
    "counter":           52,    # Synth Strings 2
    "chops":             54,    # Synth Voice
    "riser":             97,
    "impact":            103,
}

PERC = {"groove_hint", "groove", "groove_full", "backbeat", "backbeat_up", "backbeat_hook",
        "ghost", "ghost_hook"}


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
                dur = n.duration
                if dur <= 0.001:
                    dur = 0.1
                tracks[tn].append(NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + beat_offset, 6),
                    duration=dur,
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
            tracks[tn] = [n for n in tracks[tn] if n.duration > 0.001]
            raw = art.add_sustain_pedal_events(tracks[tn], beat_offset)
            if raw:
                cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, cc


def main():
    ap = argparse.ArgumentParser(description="Upbeat R&B — pocket & soul")
    ap.add_argument("--tempo", type=int, default=98)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--output", type=str, default="upbeat_rnb.mid")
    args = ap.parse_args()

    bars = sum(s[1] for s in SECTIONS)
    mins = bars * 4 / args.tempo * 60
    print(f"Upbeat R&B")
    print(f"  {mins:.1f} min ({bars} bars @ {args.tempo} BPM)")
    print(f"  Bb Dorian\n")

    tracks, cc = generate(args.tempo, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"\n  Tracks: {len(tracks)}, Notes: {total}")
    for n, ns in sorted(tracks.items()):
        print(f"    {n:20s}: {len(ns):5d} notes")

    out = Path("output") / args.output
    export_multitrack_midi(tracks, str(out), bpm=args.tempo, key="Bbm",
                           cc_events=cc, instruments=INSTRUMENTS)
    print(f"\n  -> {out} ({out.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
