# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-22
# Last Updated: 2026-05-22
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
album_afrobeat.py — "Afro Pulse" World-Afro Album.

6 cuts crossing the full Afrobeat / Afro-fusion spectrum:

  1. Lagos Run       — Classic Afrobeats / Fela Kuti | F Dorian      | 112 BPM
  2. Amapiano Rave   — Amapiano / Marimba Groove    | C Major        | 122 BPM
  3. Deep Abyss      — Afro House / Black Coffee    | G minor        | 124 BPM
  4. Drill Djembe    — Afro Drill / Burna Boy       | D Phrygian     | 130 BPM
  5. Coco Bounce     — Candomblé / Samba-Afro       | A minor        | 110 BPM
  6. Soukous Sunset  — Soukous / Highlife Guitar    | Bb Mixolydian  | 118 BPM

Uses produce_track() pipeline for auto-mix, psychoacoustic, mastering.
"""

import sys
import random
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, KeyLabel, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.afrobeats import AfrobeatsGenerator
from melodica.generators.afro_percussion import AfroPercussionGenerator
from melodica.generators.highlife_guitar import HighlifeGuitarGenerator
from melodica.generators.afro_house import AfroHouseGenerator
from melodica.generators.afro_drill import AfroDrillGenerator
from melodica.generators.afro_samba import AfroSambaGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.dark_pad import DarkPadGenerator
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
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.render_context import RenderContext
from melodica.rhythm.groove_template import SWING_60, LAID_BACK, HIP_HOP, SHUFFLE, FUNK, PUSH


# ═══════════════════════════════════════════════════════════════════════════════
# Harmony engine
# ═══════════════════════════════════════════════════════════════════════════════


def harmonize(scale, bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.25,
        secondary_dom_weight=0.10,
        extension_weight=0.06,
        repetition_penalty=0.08,
        cadence_weight=0.12,
    )
    degs = scale.degrees()
    contour = []
    for bar in range(bars):
        pos = bar % 4
        if pos == 0:
            pc = int(degs[0])
        elif pos == 1:
            pc = int(degs[min(2, len(degs) - 1)])
        elif pos == 2:
            pc = int(degs[min(4, len(degs) - 1)] if len(degs) > 4 else degs[0])
        else:
            pc = int(degs[0]) if random.random() < 0.6 else int(degs[min(3, len(degs) - 1)])
        contour.append(NoteInfo(pitch=44 + pc, start=bar * bpb, duration=bpb - 0.1, velocity=55))
    s_beats = bars * bpb
    chords = harmonizer.harmonize(contour, scale, s_beats)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(
                root=int(degs[0]),
                quality=Quality.MINOR,
                start=len(chords) * bpb,
                duration=bpb,
            )
        )
    return chords


# ═══════════════════════════════════════════════════════════════════════════════
# Arrangement engine — shared across all tracks
# ═══════════════════════════════════════════════════════════════════════════════


def map_section_type(name: str) -> str:
    n = name.lower()
    if "intro" in n:
        return "intro"
    if "pre" in n:
        return "pre_chorus"
    if "hook" in n or "chorus" in n:
        return "chorus"
    if "outro" in n:
        return "outro"
    if "break" in n or "bridge" in n:
        return "bridge"
    return "verse"


def generate_track(scale, sections, build_fn, bpb=4):
    tracks: dict[str, list[NoteInfo]] = {}
    contexts: dict[str, RenderContext] = {}
    art = ArticulationEngine()
    beat_offset = 0.0

    grooved_sections: dict[tuple[str, str], tuple[any, list[NoteInfo]]] = {}

    for name, bars, trks in sections:
        s_beats = bars * bpb
        chords = harmonize(scale, bars, bpb)

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

        print(f"  [{name:10s}] {bars:2d} bars | {', '.join(trks)}")

        for tn in trks:
            result = build_fn(tn)
            if result is None:
                continue
            gen, mods = result

            prev = contexts.get(tn)
            ctx = RenderContext(
                prev_pitch=prev.prev_pitch if prev else None,
                prev_velocity=prev.prev_velocity if prev else None,
                prev_chord=prev.prev_chord if prev else None,
                prev_pitches=list(prev.prev_pitches) if prev else [],
                current_scale=scale,
            )
            ctx.section_type = map_section_type(name)
            ctx.auto_fills = True

            notes = gen.render(chords, scale, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                contexts[tn] = gen._last_context

            section_timeline = MusicTimeline(
                chords=abs_chords,
                keys=[KeyLabel(scale=scale, start=0, duration=s_beats)],
            )
            mc = ModifierContext(
                duration_beats=s_beats, chords=abs_chords, timeline=section_timeline, scale=scale
            )
            for m in mods:
                try:
                    notes = m.modify(notes, mc)
                except Exception as e:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)

            if tn not in tracks:
                tracks[tn] = []

            section_notes = []
            for n in notes:
                dur = n.duration if n.duration > 0.001 else 0.1
                note_info = NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + beat_offset, 6),
                    duration=dur,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=n.expression,
                )
                tracks[tn].append(note_info)
                section_notes.append(note_info)

            if hasattr(gen, "groove_template") and gen.groove_template is not None:
                key = (tn, gen.groove_template.name)
                if key not in grooved_sections:
                    grooved_sections[key] = (gen.groove_template, [])
                grooved_sections[key][1].extend(section_notes)

        beat_offset += s_beats

    for k in tracks:
        tracks[k].sort(key=lambda n: n.start)

    cc = {}
    for k in list(tracks):
        tracks[k] = art.apply(tracks[k], k, beat_offset)
        tracks[k] = [n for n in tracks[k] if n.duration > 0.001]
        raw = art.add_sustain_pedal_events(tracks[k], beat_offset)
        if raw:
            cc[k] = [(e["time"], 64, e["value"]) for e in raw]

    if grooved_sections:
        print("\n  [Groove Accuracy Validation]")
        for (tn, gt_name), (template, notes) in sorted(grooved_sections.items()):
            res = template.verify_accuracy(notes)
            accuracy_pct = res["accuracy"] * 100
            matched = res["matched_notes"]
            total = res["total_notes"]
            bar_len = 20
            filled_len = int(round(bar_len * res["accuracy"]))
            bar = "█" * filled_len + "░" * (bar_len - filled_len)
            print(
                f"    • {tn:15s} | Groove: {gt_name:10s} | {bar} | {accuracy_pct:5.1f}% ({matched}/{total} notes matched)"
            )
        print()

    return tracks, cc, beat_offset


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 1 — Lagos Run (Classic Afrobeats / Fela Kuti-style)
# F Dorian | 112 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_1 = Scale(root=5, mode=Mode.DORIAN)  # F Dorian

SECTIONS_1 = [
    ("Intro", 4, ["afro_perc_intro"]),
    ("V1", 8, ["afro_drums", "bass_808", "guitar_afro", "pad", "shaker"]),
    ("Pre", 4, ["afro_perc_call", "pad", "shaker", "riser"]),
    (
        "Hook",
        8,
        ["afro_drums", "bass_808", "guitar_hook", "pad", "lead", "chops", "afro_perc_full"],
    ),
    ("Break", 4, ["afro_perc_balafon", "pad", "shaker"]),
    ("V2", 8, ["afro_drums", "bass_808", "guitar_afro", "pad", "chops", "shaker"]),
    (
        "Hook 2",
        8,
        [
            "afro_drums",
            "bass_808_swing",
            "guitar_hook",
            "pad",
            "lead",
            "chops",
            "afro_perc_full",
            "riser",
        ],
    ),
    ("Outro", 4, ["afro_perc_outro", "pad", "impact"]),
]

INSTRUMENTS_1 = {
    "afro_drums": 0,
    "bass_808": 38,
    "bass_808_swing": 38,
    "afro_perc_intro": 0,
    "afro_perc_call": 0,
    "afro_perc_full": 0,
    "afro_perc_balafon": 0,
    "afro_perc_outro": 0,
    "guitar_afro": 25,
    "guitar_hook": 28,
    "pad": 92,
    "lead": 81,
    "chops": 54,
    "shaker": 0,
    "riser": 97,
    "impact": 103,
}

PERC_1 = {
    "afro_drums",
    "afro_perc_intro",
    "afro_perc_call",
    "afro_perc_full",
    "afro_perc_balafon",
    "afro_perc_outro",
    "shaker",
}


def build_1(name):
    mods = []
    params = GeneratorParams(density=0.55)

    match name:
        case "afro_drums":
            gen = AfrobeatsGenerator(
                params=params,
                variant="afrobeats",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.55,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.82))

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.40,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "bass_808_swing":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.50,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "afro_perc_intro":
            # Sparse djembe intro with no crash
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.30),
                ensemble="west_african",
                density=0.35,
                include_pitched=False,
                call_response=False,
                swing=0.52,
            )
            mods.append(VelocityScalingModifier(scale=0.50))

        case "afro_perc_call":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.45),
                ensemble="west_african",
                density=0.50,
                include_pitched=True,
                call_response=True,
                swing=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.52))

        case "afro_perc_full":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.55),
                ensemble="west_african",
                density=0.60,
                include_pitched=True,
                call_response=True,
                swing=0.57,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "afro_perc_balafon":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.40),
                ensemble="south_african",
                density=0.45,
                include_pitched=True,
                call_response=True,
                swing=0.53,
            )
            mods.append(VelocityScalingModifier(scale=0.50))

        case "afro_perc_outro":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.30),
                ensemble="cuban_afro",
                density=0.40,
                include_pitched=True,
                call_response=False,
                swing=0.54,
            )
            mods.append(VelocityScalingModifier(scale=0.45))

        case "guitar_afro":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.60),
                variant="afrobeat",
                riff_density=0.65,
                palm_mute_ratio=0.30,
                octave_doubling=False,
                interlocking=False,
                pentatonic_bias=0.7,
            )
            mods += [
                HumanizeModifier(timing_std=0.02, velocity_std=5),
                VelocityScalingModifier(scale=0.50),
            ]

        case "guitar_hook":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.70),
                variant="afrobeat",
                riff_density=0.80,
                palm_mute_ratio=0.15,
                octave_doubling=True,
                interlocking=True,
                pentatonic_bias=0.65,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=4),
                VelocityScalingModifier(scale=0.60),
            ]

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.25),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.15,
                register="mid",
                overlap=0.4,
            )

        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.40),
                style="retro",
                portamento=0.20,
                note_length="mixed",
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=79),
                HumanizeModifier(timing_std=0.02, velocity_std=4),
                VelocityScalingModifier(scale=0.55),
            ]

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.40),
                processing="pitch_shift",
                density=0.45,
                chop_pattern="syncopated",
                source_pitch=65,
            )
            mods += [
                VelocityScalingModifier(scale=0.38),
                HumanizeModifier(timing_std=0.03, velocity_std=3),
            ]

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
            mods.append(VelocityScalingModifier(scale=0.35))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.35),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=92,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.30),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=14,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 2 — Amapiano Rave (Amapiano / Marimba Groove)
# C Major | 122 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_2 = Scale(root=0, mode=Mode.MAJOR)  # C Major

SECTIONS_2 = [
    ("Intro", 4, ["pad_airy", "afro_perc_marimba"]),
    ("V1", 8, ["afro_drum_amap", "bass_lin", "piano_amp", "pad", "shaker"]),
    ("Pre", 4, ["pad", "afro_perc_full", "shaker", "riser"]),
    (
        "Hook",
        8,
        ["afro_drum_amap", "bass_808", "log_full", "piano_amp", "pad", "lead_amp", "chops_amp"],
    ),
    ("Break", 4, ["afro_perc_conga", "pad", "piano_bare"]),
    ("V2", 8, ["afro_drum_amap", "bass_lin", "log_lite", "pad", "piano_amp", "shaker"]),
    (
        "Hook 2",
        8,
        [
            "afro_drum_amap",
            "bass_808",
            "log_full",
            "piano_amp",
            "pad",
            "lead_amp",
            "chops_amp",
            "riser",
        ],
    ),
    ("Outro", 4, ["afro_perc_marimba", "pad", "impact"]),
]

INSTRUMENTS_2 = {
    "afro_drum_amap": 0,
    "bass_lin": 38,
    "bass_808": 38,
    "afro_perc_marimba": 0,
    "afro_perc_full": 0,
    "afro_perc_conga": 0,
    "log_full": 0,
    "log_lite": 0,
    "piano_amp": 0,
    "piano_bare": 0,
    "pad_airy": 92,
    "pad": 92,
    "lead_amp": 81,
    "chops_amp": 54,
    "shaker": 0,
    "riser": 97,
    "impact": 103,
}

PERC_2 = {"afro_drum_amap", "afro_perc_marimba", "afro_perc_full", "afro_perc_conga", "shaker"}


def build_2(name):
    mods = []
    params = GeneratorParams(density=0.50)

    match name:
        case "afro_drum_amap":
            gen = AfrobeatsGenerator(
                params=params,
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.52,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.80))

        case "bass_lin":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.30,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.78))

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="rolling",
                slide_type="chromatic",
                slide_probability=0.55,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.82))

        case "afro_perc_marimba":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.35),
                ensemble="south_african",
                density=0.40,
                include_pitched=True,
                call_response=False,
                swing=0.54,
            )
            mods.append(VelocityScalingModifier(scale=0.48))

        case "afro_perc_full":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.55),
                ensemble="south_african",
                density=0.60,
                include_pitched=True,
                call_response=True,
                swing=0.56,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "afro_perc_conga":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.42),
                ensemble="cuban_afro",
                density=0.50,
                include_pitched=False,
                call_response=True,
                swing=0.53,
            )
            mods.append(VelocityScalingModifier(scale=0.50))

        case "log_full":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.65),
                variant="amapiano",
                log_drum_density=0.8,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.50,
                percussion_layer=True,
            )
            mods.append(VelocityScalingModifier(scale=0.58))

        case "log_lite":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.45),
                variant="amapiano",
                log_drum_density=0.4,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.50,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.45))

        case "piano_amp":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.55),
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="eighth",
                include_piano=True,
                bounce_amount=0.50,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "piano_bare":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.30),
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=True,
                bounce_amount=0.48,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.42))

        case "pad_airy":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.14,
                register="high",
                overlap=0.5,
            )

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.16,
                register="mid",
                overlap=0.45,
            )

        case "lead_amp":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.50),
                style="supersaw",
                portamento=0.25,
                note_length="mixed",
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=79),
                HumanizeModifier(timing_std=0.02, velocity_std=4),
                VelocityScalingModifier(scale=0.58),
            ]

        case "chops_amp":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.45),
                processing="pitch_shift",
                density=0.50,
                chop_pattern="syncopated",
                source_pitch=60,
            )
            mods += [
                VelocityScalingModifier(scale=0.42),
                HumanizeModifier(timing_std=0.02, velocity_std=3),
            ]

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
            mods.append(VelocityScalingModifier(scale=0.38))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.35),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=95,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.30),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=12,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 3 — Deep Abyss (Afro House / Black Coffee-style Deep House)
# G minor | 124 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_3 = Scale(root=7, mode=Mode.NATURAL_MINOR)  # G minor

SECTIONS_3 = [
    ("Intro", 4, ["pad_sub", "marimba_low"]),
    ("V1", 8, ["afro_house_kick", "bass_808", "marimba_pulse", "pad", "percu_conga"]),
    ("Pre", 4, ["pad", "marimba_busy", "strings_sub", "riser"]),
    (
        "Hook",
        8,
        [
            "afro_house_kick",
            "bass_808_slide",
            "marimba_pulse",
            "pad",
            "elec_pad",
            "chants",
            "percu_full",
        ],
    ),
    ("Break", 4, ["marimba_solo", "pad", "percu_conga"]),
    ("V2", 8, ["afro_house_kick", "bass_808", "marimba_pulse", "pad", "elec_pad", "percu full"]),
    (
        "Hook 2",
        8,
        [
            "afro_house_kick_hats",
            "bass_808_slide",
            "marimba_pulse",
            "pad",
            "elec_pad",
            "chants",
            "strings_sub",
            "riser",
        ],
    ),
    ("Outro", 4, ["marimba_low", "pad_sub", "impact"]),
]

INSTRUMENTS_3 = {
    "afro_house_kick": 0,
    "afro_house_kick_hats": 0,
    "bass_808": 38,
    "bass_808_slide": 38,
    "marimba_low": 0,
    "marimba_pulse": 0,
    "marimba_busy": 0,
    "marimba_solo": 0,
    "pad_sub": 92,
    "pad": 92,
    "elec_pad": 92,
    "strings_sub": 48,
    "chants": 54,
    "percu_conga": 0,
    "percu_full": 0,
    "riser": 97,
    "impact": 103,
}

PERC_3 = {
    "afro_house_kick",
    "afro_house_kick_hats",
    "marimba_low",
    "marimba_pulse",
    "marimba_busy",
    "marimba_solo",
    "percu_conga",
    "percu_full",
}


def build_3(name):
    mods = []
    params = GeneratorParams(density=0.48)

    match name:
        case "afro_house_kick":
            gen = AfroHouseGenerator(
                params=params,
                variant="deep",
                percussion_density=0.45,
            )
            mods.append(VelocityScalingModifier(scale=0.75))

        case "afro_house_kick_hats":
            gen = AfroHouseGenerator(
                params=params,
                variant="deep",
                percussion_density=0.65,
            )
            mods.append(VelocityScalingModifier(scale=0.88))

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.35,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "bass_808_slide":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="drill_sliding",
                slide_type="chromatic",
                slide_probability=0.60,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "marimba_low":
            gen = AfroHouseGenerator(
                params=GeneratorParams(density=0.35),
                variant="spiritual",
                percussion_density=0.35,
            )
            mods.append(VelocityScalingModifier(scale=0.52))

        case "marimba_pulse":
            gen = AfroHouseGenerator(
                params=GeneratorParams(density=0.55),
                variant="deep",
                percussion_density=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.62))

        case "marimba_busy":
            gen = AfroHouseGenerator(
                params=GeneratorParams(density=0.65),
                variant="spiritual",
                percussion_density=0.65,
            )
            mods.append(VelocityScalingModifier(scale=0.65))

        case "marimba_solo":
            gen = AfroHouseGenerator(
                params=GeneratorParams(density=0.70),
                variant="organic",
                percussion_density=0.50,
            )
            mods.append(VelocityScalingModifier(scale=0.58))

        case "pad_sub":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.18),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.12,
                register="low",
                overlap=0.5,
            )

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.20),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.14,
                register="mid",
                overlap=0.45,
            )

        case "elec_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.16,
                register="mid",
                overlap=0.40,
            )

        case "strings_sub":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.15),
                mode="tritone_drone",
                chord_dur=4.0,
                velocity_level=0.10,
                register="mid",
                overlap=0.5,
            )

        case "chants":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.30),
                processing="pitch_shift",
                density=0.35,
                chop_pattern="syncopated",
                source_pitch=60,
            )
            mods.append(VelocityScalingModifier(scale=0.35))

        case "percu_conga":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.40),
                ensemble="cuban_afro",
                density=0.45,
                include_pitched=False,
                call_response=True,
                swing=0.53,
            )
            mods.append(VelocityScalingModifier(scale=0.50))

        case "percu_full":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.55),
                ensemble="cuban_afro",
                density=0.60,
                include_pitched=True,
                call_response=True,
                swing=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.58))

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
                params=GeneratorParams(density=0.25),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=10,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 4 — Drill Djembe (Afro Drill / Burna Boy)
# D Phrygian | 130 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_4 = Scale(root=2, mode=Mode.PHRYGIAN)  # D Phrygian

SECTIONS_4 = [
    ("Intro", 4, ["djembe_intro", "pad_tense", "afro_hat_soft"]),
    ("V1", 8, ["afro_drill_drums", "bass_808_drill", "djembe_full", "pad", "hihat"]),
    ("Pre", 4, ["pad", "afro_perc_djembe", "hihat_rapid_drill", "riser"]),
    (
        "Hook",
        8,
        [
            "afro_drill_drums",
            "bass_808_slide",
            "djembe_full",
            "pad",
            "hihat_rapid_drill",
            "lead_melodic",
            "snare_ghost",
        ],
    ),
    ("Break", 4, ["afro_perc_balafon_call", "pad"]),
    (
        "V2",
        8,
        ["afro_drill_drums", "bass_808_drill", "djembe_full", "pad", "hihat", "lead_melodic"],
    ),
    (
        "Hook 2",
        8,
        [
            "afro_drill_drums",
            "bass_808_slide",
            "djembe_full",
            "pad",
            "hihat_rapid_drill",
            "lead_melodic",
            "snare_ghost",
            "riser",
        ],
    ),
    ("Outro", 4, ["djembe_intro", "pad_tense", "impact_drill"]),
]

INSTRUMENTS_4 = {
    "afro_drill_drums": 0,
    "bass_808_drill": 38,
    "bass_808_slide": 38,
    "djembe_intro": 0,
    "djembe_full": 0,
    "afro_hat_soft": 0,
    "hihat": 0,
    "hihat_rapid_drill": 0,
    "pad_tense": 92,
    "pad": 92,
    "afro_perc_djembe": 0,
    "afro_perc_balafon_call": 0,
    "lead_melodic": 81,
    "snare_ghost": 0,
    "riser": 97,
    "impact_drill": 103,
}

PERC_4 = {
    "afro_drill_drums",
    "bass_808_drill",
    "djembe_intro",
    "djembe_full",
    "afro_hat_soft",
    "hihat",
    "hihat_rapid_drill",
    "snare_ghost",
    "afro_perc_djembe",
    "afro_perc_balafon_call",
}


def build_4(name):
    mods = []
    params = GeneratorParams(density=0.55)

    match name:
        case "afro_drill_drums":
            gen = AfroDrillGenerator(
                params=params,
                variant="burna",
                slide_amount=7,
                melody_density=0.5,
            )
            mods.append(VelocityScalingModifier(scale=0.80))

        case "bass_808_drill":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="drill_basic",
                slide_type="octave_jump",
                slide_probability=0.50,
                slide_curve="octave_whip",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.88))

        case "bass_808_slide":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="drill_sliding",
                slide_type="chromatic",
                slide_probability=0.65,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "djembe_intro":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.28),
                ensemble="west_african",
                density=0.32,
                include_pitched=False,
                call_response=False,
                swing=0.52,
            )
            mods.append(VelocityScalingModifier(scale=0.48))

        case "djembe_full":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.55),
                ensemble="west_african",
                density=0.60,
                include_pitched=True,
                call_response=True,
                swing=0.58,
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "afro_hat_soft":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.25),
                pattern="trap_eighth",
                roll_density=0.20,
                open_hat_probability=0.05,
                pan_mode="alternate",
                scale_snap_rolls=False,
                stutter_lengths=[3],
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "hihat":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.35,
                open_hat_probability=0.10,
                pan_mode="alternate",
                scale_snap_rolls=True,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.57, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "hihat_rapid_drill":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="drill_stutter",
                roll_density=0.60,
                open_hat_probability=0.08,
                pan_mode="sweep_lr",
                scale_snap_rolls=True,
                stutter_lengths=[5, 7],
            )
            mods.append(SwingController(swing_ratio=0.58, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.60))

        case "pad_tense":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.18),
                mode="phrygian_pad",
                chord_dur=4.0,
                velocity_level=0.12,
                register="mid",
                overlap=0.5,
            )

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.20),
                mode="phrygian_pad",
                chord_dur=4.0,
                velocity_level=0.14,
                register="mid",
                overlap=0.45,
            )

        case "afro_perc_djembe":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.50),
                ensemble="west_african",
                density=0.55,
                include_pitched=False,
                call_response=True,
                swing=0.57,
            )
            mods.append(VelocityScalingModifier(scale=0.58))

        case "afro_perc_balafon_call":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.35),
                ensemble="east_african",
                density=0.40,
                include_pitched=True,
                call_response=True,
                swing=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.48))

        case "lead_melodic":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.50),
                style="supersaw",
                portamento=0.30,
                note_length="staccato",
            )
            mods += [
                LimitNoteRangeModifier(low=58, high=80),
                HumanizeModifier(timing_std=0.025, velocity_std=4),
                VelocityScalingModifier(scale=0.62),
            ]

        case "snare_ghost":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.25),
                target="snare",
                pattern="hiphop",
                ghost_velocity=25,
                ghost_density=0.30,
                placement="sixteenth",
            )

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.40),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=95,
            )

        case "impact_drill":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.25),
                impact_type="boom",
                tail_length=4.0,
                pitch_drop=18,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 5 — Coco Bounce (Candomblé / Afro-Samba / Samba-Afro)
# A minor | 110 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_5 = Scale(root=9, mode=Mode.NATURAL_MINOR)  # A minor

SECTIONS_5 = [
    ("Intro", 4, ["samba_perc_intro", "guitar_open"]),
    ("V1", 8, ["afro_samba_drums", "bass_walk", "guitar_samba", "pad", "shaker"]),
    ("Pre", 4, ["pad", "samba_perc_busy", "shaker", "riser"]),
    (
        "Hook",
        8,
        ["afro_samba_drums", "bass_808", "guitar_samba", "pad", "lead", "chops", "samba_perc_full"],
    ),
    ("Break", 4, ["samba_perc_open", "guitar_open"]),
    ("V2", 8, ["afro_samba_drums", "bass_walk", "guitar_samba", "pad", "chops"]),
    (
        "Hook 2",
        8,
        [
            "afro_samba_drums_hard",
            "bass_808",
            "guitar_hook_samba",
            "pad",
            "lead",
            "chops",
            "samba_perc_full",
            "riser",
        ],
    ),
    ("Outro", 4, ["samba_perc_calm", "guitar_open", "impact"]),
]

INSTRUMENTS_5 = {
    "afro_samba_drums": 0,
    "afro_samba_drums_hard": 0,
    "bass_walk": 38,
    "bass_808": 38,
    "samba_perc_intro": 0,
    "samba_perc_busy": 0,
    "samba_perc_full": 0,
    "samba_perc_open": 0,
    "samba_perc_calm": 0,
    "guitar_open": 25,
    "guitar_samba": 25,
    "guitar_hook_samba": 25,
    "pad": 92,
    "lead": 81,
    "chops": 54,
    "shaker": 0,
    "riser": 97,
    "impact": 103,
}

PERC_5 = {
    "afro_samba_drums",
    "afro_samba_drums_hard",
    "samba_perc_intro",
    "samba_perc_busy",
    "samba_perc_full",
    "samba_perc_open",
    "samba_perc_calm",
    "shaker",
}


def build_5(name):
    mods = []
    params = GeneratorParams(density=0.50)

    match name:
        case "afro_samba_drums":
            gen = AfroSambaGenerator(
                params=params,
                variant="samba_afro",
            )
            mods.append(VelocityScalingModifier(scale=0.78))

        case "afro_samba_drums_hard":
            gen = AfroSambaGenerator(
                params=GeneratorParams(density=0.62),
                variant="samba_afro",
            )
            mods.append(VelocityScalingModifier(scale=0.88))

        case "bass_walk":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.35,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.78))

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.30,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.72))

        case "samba_perc_intro":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.30),
                ensemble="south_african",
                density=0.35,
                include_pitched=True,
                call_response=False,
                swing=0.52,
            )
            mods.append(VelocityScalingModifier(scale=0.45))

        case "samba_perc_busy":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.55),
                ensemble="west_african",
                density=0.60,
                include_pitched=True,
                call_response=True,
                swing=0.56,
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "samba_perc_full":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.60),
                ensemble="west_african",
                density=0.65,
                include_pitched=True,
                call_response=True,
                swing=0.58,
            )
            mods.append(VelocityScalingModifier(scale=0.62))

        case "samba_perc_open":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.40),
                ensemble="cuban_afro",
                density=0.45,
                include_pitched=True,
                call_response=True,
                swing=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.52))

        case "samba_perc_calm":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.25),
                ensemble="east_african",
                density=0.30,
                include_pitched=False,
                call_response=False,
                swing=0.52,
            )
            mods.append(VelocityScalingModifier(scale=0.40))

        case "guitar_open":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.30),
                variant="palm_wine",
                riff_density=0.35,
                palm_mute_ratio=0.10,
                octave_doubling=False,
                interlocking=False,
                pentatonic_bias=0.80,
            )
            mods += [
                VelocityScalingModifier(scale=0.42),
                HumanizeModifier(timing_std=0.03, velocity_std=3),
            ]

        case "guitar_samba":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.55),
                variant="highlife",
                riff_density=0.60,
                palm_mute_ratio=0.35,
                octave_doubling=True,
                interlocking=True,
                pentatonic_bias=0.70,
            )
            mods += [
                HumanizeModifier(timing_std=0.02, velocity_std=4),
                VelocityScalingModifier(scale=0.55),
            ]

        case "guitar_hook_samba":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.65),
                variant="juju",
                riff_density=0.70,
                palm_mute_ratio=0.20,
                octave_doubling=True,
                interlocking=True,
                pentatonic_bias=0.65,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=4),
                VelocityScalingModifier(scale=0.62),
            ]

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.15,
                register="mid",
                overlap=0.45,
            )

        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.40),
                style="retro",
                portamento=0.18,
                note_length="mixed",
            )
            mods += [
                LimitNoteRangeModifier(low=62, high=80),
                HumanizeModifier(timing_std=0.02, velocity_std=4),
                VelocityScalingModifier(scale=0.55),
            ]

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.40),
                processing="pitch_shift",
                density=0.45,
                chop_pattern="syncopated",
                source_pitch=62,
            )
            mods += [
                VelocityScalingModifier(scale=0.40),
                HumanizeModifier(timing_std=0.03, velocity_std=3),
            ]

        case "shaker":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.25),
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.45,
                percussion_layer=True,
            )
            mods.append(VelocityScalingModifier(scale=0.38))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.35),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=92,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.28),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=15,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 6 — Soukous Sunset (Soukous / Highlife Guitar / Afro-Pop Fusion)
# Bb Mixolydian | 118 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_6 = Scale(root=10, mode=Mode.MIXOLYDIAN)  # Bb Mixolydian

SECTIONS_6 = [
    ("Intro", 4, ["guitar_intro_souk", "pad_sunset"]),
    ("V1", 8, ["soukous_guitar", "bass_soukous", "afro_drums_lite", "shaker", "pad"]),
    ("Pre", 4, ["guitar_intro_souk", "pad", "shaker", "riser"]),
    (
        "Hook",
        8,
        [
            "soukous_guitar_hook",
            "bass_soukous",
            "afro_drums",
            "lead_souk",
            "chops_souk",
            "shaker_dense",
            "afro_perc_wak",
        ],
    ),
    ("Break", 4, ["guitar_intro_souk", "afro_perc_wak"]),
    (
        "V2",
        8,
        [
            "soukous_guitar",
            "bass_soukous",
            "afro_drums_lite",
            "guitar_highlife",
            "pad",
            "shaker",
            "chops_souk",
        ],
    ),
    (
        "Hook 2",
        8,
        [
            "soukous_guitar_hook",
            "bass_soukous",
            "afro_drums",
            "lead_souk",
            "chops_souk",
            "shaker_dense",
            "afro_perc_wak",
            "riser",
        ],
    ),
    ("Outro", 4, ["guitar_intro_souk", "pad_sunset", "impact_smooth"]),
]

INSTRUMENTS_6 = {
    "soukous_guitar": 25,
    "soukous_guitar_hook": 28,
    "guitar_highlife": 29,
    "guitar_intro_souk": 25,
    "bass_soukous": 38,
    "afro_drums": 0,
    "afro_drums_lite": 0,
    "shaker": 0,
    "shaker_dense": 0,
    "pad_sunset": 92,
    "pad": 92,
    "lead_souk": 81,
    "chops_souk": 54,
    "afro_perc_wak": 0,
    "riser": 97,
    "impact_smooth": 103,
}

PERC_6 = {"afro_drums", "afro_drums_lite", "shaker", "shaker_dense", "afro_perc_wak"}


def build_6(name):
    mods = []
    params = GeneratorParams(density=0.50)

    match name:
        case "soukous_guitar":
            gen = HighlifeGuitarGenerator(
                params=params,
                variant="highlife",
                riff_density=0.65,
                palm_mute_ratio=0.30,
                octave_doubling=True,
                interlocking=False,
                pentatonic_bias=0.60,
            )
            mods += [
                HumanizeModifier(timing_std=0.02, velocity_std=5),
                VelocityScalingModifier(scale=0.55),
            ]

        case "soukous_guitar_hook":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.70),
                variant="highlife",
                riff_density=0.80,
                palm_mute_ratio=0.20,
                octave_doubling=True,
                interlocking=True,
                pentatonic_bias=0.55,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=4),
                VelocityScalingModifier(scale=0.62),
            ]

        case "guitar_highlife":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.60),
                variant="juju",
                riff_density=0.65,
                palm_mute_ratio=0.25,
                octave_doubling=True,
                interlocking=True,
                pentatonic_bias=0.65,
            )
            mods += [
                HumanizeModifier(timing_std=0.02, velocity_std=4),
                VelocityScalingModifier(scale=0.58),
            ]

        case "guitar_intro_souk":
            gen = HighlifeGuitarGenerator(
                params=GeneratorParams(density=0.35),
                variant="palm_wine",
                riff_density=0.40,
                palm_mute_ratio=0.10,
                octave_doubling=False,
                interlocking=False,
                pentatonic_bias=0.85,
            )
            mods += [
                VelocityScalingModifier(scale=0.48),
                HumanizeModifier(timing_std=0.03, velocity_std=3),
            ]

        case "bass_soukous":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.40,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.82))

        case "afro_drums":
            gen = AfrobeatsGenerator(
                params=params,
                variant="afrobeats",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.50,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.78))

        case "afro_drums_lite":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.40),
                variant="afrobeats",
                log_drum_density=0.0,
                shaker_pattern="eighth",
                include_piano=False,
                bounce_amount=0.48,
                percussion_layer=False,
            )
            mods.append(VelocityScalingModifier(scale=0.68))

        case "shaker":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.28),
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.45,
                percussion_layer=True,
            )
            mods.append(VelocityScalingModifier(scale=0.35))

        case "shaker_dense":
            gen = AfrobeatsGenerator(
                params=GeneratorParams(density=0.40),
                variant="amapiano",
                log_drum_density=0.0,
                shaker_pattern="sixteenth",
                include_piano=False,
                bounce_amount=0.50,
                percussion_layer=True,
            )
            mods.append(VelocityScalingModifier(scale=0.45))

        case "pad_sunset":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.14,
                register="mid",
                overlap=0.5,
            )

        case "pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.16,
                register="mid",
                overlap=0.45,
            )

        case "lead_souk":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.42),
                style="retro",
                portamento=0.20,
                note_length="mixed",
            )
            mods += [
                LimitNoteRangeModifier(low=60, high=78),
                HumanizeModifier(timing_std=0.02, velocity_std=4),
                VelocityScalingModifier(scale=0.55),
            ]

        case "chops_souk":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.40),
                processing="pitch_shift",
                density=0.45,
                chop_pattern="syncopated",
                source_pitch=62,
            )
            mods += [
                VelocityScalingModifier(scale=0.42),
                HumanizeModifier(timing_std=0.025, velocity_std=3),
            ]

        case "afro_perc_wak":
            gen = AfroPercussionGenerator(
                params=GeneratorParams(density=0.45),
                ensemble="west_african",
                density=0.50,
                include_pitched=True,
                call_response=True,
                swing=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.32),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=92,
            )

        case "impact_smooth":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.28),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=14,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# Album Production
# ═══════════════════════════════════════════════════════════════════════════════

TRACKS = [
    {
        "title": "01_Lagos_Run",
        "scale": SCALE_1,
        "sections": SECTIONS_1,
        "build": build_1,
        "instruments": INSTRUMENTS_1,
        "bpm": 112,
        "mood": Mood.AGGRESSIVE,
        "perc": PERC_1,
        "key_label": "Fm",
    },
    {
        "title": "02_Amapiano_Rave",
        "scale": SCALE_2,
        "sections": SECTIONS_2,
        "build": build_2,
        "instruments": INSTRUMENTS_2,
        "bpm": 122,
        "mood": Mood.CINEMATIC,
        "perc": PERC_2,
        "key_label": "C",
    },
    {
        "title": "03_Deep_Abyss",
        "scale": SCALE_3,
        "sections": SECTIONS_3,
        "build": build_3,
        "instruments": INSTRUMENTS_3,
        "bpm": 124,
        "mood": Mood.INTIMATE,
        "perc": PERC_3,
        "key_label": "Gm",
    },
    {
        "title": "04_Drill_Djembe",
        "scale": SCALE_4,
        "sections": SECTIONS_4,
        "build": build_4,
        "instruments": INSTRUMENTS_4,
        "bpm": 130,
        "mood": Mood.AGGRESSIVE,
        "perc": PERC_4,
        "key_label": "Dm",
    },
    {
        "title": "05_Coco_Bounce",
        "scale": SCALE_5,
        "sections": SECTIONS_5,
        "build": build_5,
        "instruments": INSTRUMENTS_5,
        "bpm": 110,
        "mood": Mood.CINEMATIC,
        "perc": PERC_5,
        "key_label": "Am",
    },
    {
        "title": "06_Soukous_Sunset",
        "scale": SCALE_6,
        "sections": SECTIONS_6,
        "build": build_6,
        "instruments": INSTRUMENTS_6,
        "bpm": 118,
        "mood": Mood.INTIMATE,
        "perc": PERC_6,
        "key_label": "Bb",
    },
]


def main():
    album_dir = Path("output/album_afrobeat")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   AFRO PULSE — World-Afro Fusion Album")
    print("   6 Cuts | Afrobeats · Amapiano · Afro House · Afro Drill · Samba-Afro · Soukous")
    print("=" * 60 + "\n")

    for t in TRACKS:
        title = t["title"]
        bpm = t["bpm"]
        bars = sum(s[1] for s in t["sections"])
        mins = (bars * 4) / bpm
        print(f"{'─' * 50}")
        print(f"  {title.replace('_', ' ')}")
        print(f"  {mins:.1f} min ({bars} bars @ {bpm} BPM)\n")

        raw, cc, total_beats = generate_track(t["scale"], t["sections"], t["build"])
        out_path = album_dir / f"{title}.mid"

        produce_track(
            tracks=raw,
            bpm=bpm,
            instruments=t["instruments"],
            path=str(out_path),
            mood=t["mood"],
            key=t["scale"],
            cc_events=cc,
            verbose=False,
        )

        total_notes = sum(len(n) for n in raw.values())
        print(f"  -> {out_path.name} ({total_notes} notes)\n")

    print("=" * 60)
    print("   PRODUCTION COMPLETE: AFRO PULSE")
    print(f"   Location: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
