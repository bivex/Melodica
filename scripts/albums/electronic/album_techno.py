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
album_techno.py — "Steel Pulse" Techno Album.

3 cuts proving the upgraded ElectronicDrumsGenerator + 808 post-processing:

  1. Obsidian Floor  — Deep melodic techno (Bodzin / Mockasin) | A minor | 127 BPM
  2. Acid Sector    — Acid techno / TB-303 squelch        | F Phrygian  | 132 BPM
  3. Iron Foundry    — Industrial / hard techno             | D Dorian    | 140 BPM

All three tracks use TR-909 (`kit="909"`), 808 transient-ducking,
pan_mode sweeps on hi-hats, and swing timing from GrooveTemplate.
"""

import sys
import random
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, KeyLabel, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
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


# ═══════════════════════════════════════════════════════════════════════════════
# Harmony engine
# ═══════════════════════════════════════════════════════════════════════════════


def harmonize(scale, bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.20,
        secondary_dom_weight=0.10,
        extension_weight=0.06,
        repetition_penalty=0.10,
        cadence_weight=0.12,
    )
    degs = scale.degrees()
    contour = []
    for bar in range(bars):
        pos = bar % 8
        if pos < 2:
            pc = int(degs[0])
        elif pos < 4:
            pc = int(degs[min(2, len(degs) - 1)])
        elif pos < 6:
            pc = int(degs[min(4, len(degs) - 1)])
        else:
            pc = int(degs[0]) if random.random() < 0.7 else int(degs[min(5, len(degs) - 1)])
        contour.append(NoteInfo(pitch=44 + pc, start=bar * bpb, duration=bpb - 0.05, velocity=52))
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
# Arrangement engine
# ═══════════════════════════════════════════════════════════════════════════════


def map_section_type(name: str) -> str:
    n = name.lower()
    if "intro" in n:
        return "intro"
    if "pre" in n or "buildup" in n:
        return "pre_chorus"
    if "hook" in n or "drop" in n:
        return "chorus"
    if "outro" in n:
        return "outro"
    if "break" in n:
        return "bridge"
    return "verse"


def setup_groove(groove_template, params, swing=0.57, grid=0.25):
    rg = RhythmGenerator()
    rg.default_pocket = (swing - 0.5) * 2.0 * grid
    return groove_template


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
            ctx_args = {}
            if prev:
                ctx_args = dict(
                    prev_pitch=prev.prev_pitch,
                    prev_velocity=prev.prev_velocity,
                    prev_chord=prev.prev_chord,
                    prev_pitches=list(prev.prev_pitches),
                )
            ctx = RenderContext(current_scale=scale, **ctx_args)
            ctx.section_type = map_section_type(name)
            ctx.auto_fills = True

            notes = gen.render(chords, scale, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                contexts[tn] = gen._last_context

            section_timeline = MusicTimeline(
                chords=abs_chords,
                keys=[],
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

            if hasattr(gen, "groove_template") and gen.groove_template is not None:
                key = (tn, gen.groove_template.name)
                if key not in grooved_sections:
                    grooved_sections[key] = (gen.groove_template, [])
                grooved_sections[key][1].extend(tracks[tn])

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
# TRACK 1 — Obsidian Floor (Deep melodic techno, Bodzin / Stephan Bodzin vibes)
# A minor | 127 BPM
# Uses: TR-909, mute_boundaries, transient_ducking, pan sweeps, ghost snare
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_1 = Scale(root=9, mode=Mode.NATURAL_MINOR)  # A minor

SECTIONS_1 = [
    ("Intro", 4, ["dark_pad", "euro_drums_hint"]),
    ("Verse 1", 8, ["909_drums", "bass_808_floor", "dark_pad", "arp_line"]),
    ("Buildup", 4, ["dark_pad", "arp_build", "909_hats_only", "riser"]),
    ("Drop", 8, ["909_drums_hard", "bass_808_slide", "slash_pad", "arp_line", "ghost_snare"]),
    ("Break", 4, ["dark_pad", "acid_bass_solo"]),
    ("Verse 2", 8, ["909_drums", "bass_808_floor", "dark_pad", "arp_line"]),
    (
        "Drop 2",
        8,
        ["909_drums_hard", "bass_808_slide", "slash_pad", "arp_line", "ghost_snare", "riser"],
    ),
    ("Outro", 4, ["dark_pad", "euro_drums_out", "impact"]),
]

INSTRUMENTS_1 = {
    "909_drums": 0,
    "909_drums_hard": 0,
    "909_hats_only": 0,
    "euro_drums_hint": 0,
    "euro_drums_out": 0,
    "bass_808_floor": 38,
    "bass_808_slide": 38,
    "dark_pad": 92,
    "slash_pad": 92,
    "arp_line": 0,
    "arp_build": 0,
    "acid_bass_solo": 38,
    "ghost_snare": 0,
    "riser": 97,
    "impact": 103,
}

PERC_1 = {
    "909_drums",
    "909_drums_hard",
    "909_hats_only",
    "euro_drums_hint",
    "euro_drums_out",
    "ghost_snare",
}


def build_1(name):
    mods = []
    params = GeneratorParams(density=0.50)

    match name:
        case "909_drums":
            gen = ElectronicDrumsGenerator(
                params=params,
                kit="909",
                pattern="four_on_floor",
                sidechain=True,
                sidechain_depth=0.40,
                snare_delay=0.012,
                groove_swing=0.57,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.20,
                section_type="verse",
                auto_fills=True,
                groove_template=None,
                transient_ducking=True,
                ducking_duration=0.020,
                envelope_gating=True,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="sweep_lr",
                pan_alternation_rate=0.5,
                flam_probability=0.04,
                drag_probability=0.02,
            )
            mods.append(VelocityScalingModifier(scale=0.78))
            mods.append(HumanizeModifier(timing_std=0.012, velocity_std=3))

        case "909_drums_hard":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.62),
                kit="909",
                pattern="four_on_floor",
                sidechain=True,
                sidechain_depth=0.50,
                snare_delay=0.015,
                groove_swing=0.57,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.30,
                section_type="chorus",
                auto_fills=True,
                groove_template=None,
                transient_ducking=True,
                ducking_duration=0.020,
                envelope_gating=True,
                mute_boundaries=True,
                kick_less_verse=False,
                pan_mode="sweep_lr",
                flam_probability=0.06,
                drag_probability=0.03,
            )
            mods.append(VelocityScalingModifier(scale=0.88))

        case "909_hats_only":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.35),
                pattern="trap_eighth",
                roll_density=0.30,
                open_hat_probability=0.10,
                pan_mode="sweep_lr",
                scale_snap_rolls=False,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.57, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "euro_drums_hint":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.35),
                kit="909",
                pattern="breakbeat",
                sidechain=True,
                sidechain_depth=0.30,
                groove_swing=0.50,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.00,
                section_type="intro",
                auto_fills=False,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="alternate",
            )
            mods.append(VelocityScalingModifier(scale=0.58))

        case "euro_drums_out":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.30),
                kit="909",
                pattern="breakbeat",
                sidechain=False,
                groove_swing=0.50,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.00,
                section_type="outro",
                auto_fills=False,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="alternate",
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "bass_808_floor":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.30,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
                ducking_duration=0.020,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "bass_808_slide":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.65),
                pattern="rolling",
                slide_type="chromatic",
                slide_probability=0.55,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
                ducking_duration=0.020,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.20),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.14,
                register="mid",
                overlap=0.5,
            )

        case "slash_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="tritone_drone",
                chord_dur=4.0,
                velocity_level=0.18,
                register="mid",
                overlap=0.45,
            )

        case "arp_line":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.55),
                pattern="up",
                note_duration=0.25,
            )
            mods += [
                HumanizeModifier(timing_std=0.008, velocity_std=2),
                VelocityScalingModifier(scale=0.60),
                LimitNoteRangeModifier(low=60, high=84),
            ]

        case "arp_build":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.70),
                pattern="up_down",
                note_duration=0.20,
            )
            mods += [
                HumanizeModifier(timing_std=0.008, velocity_std=2),
                VelocityScalingModifier(scale=0.65),
                LimitNoteRangeModifier(low=62, high=84),
            ]

        case "acid_bass_solo":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.55),
                waveform="acid",
                pattern="acid_line",
                slide_probability=0.20,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=5),
                VelocityScalingModifier(scale=0.70),
                LimitNoteRangeModifier(low=32, high=55),
            ]

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.25),
                target="snare",
                pattern="hiphop",
                ghost_velocity=20,
                ghost_density=0.35,
                placement="sixteenth",
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.40),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=100,
            )

        case "impact":
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
# TRACK 2 — Acid Sector (Acid techno, TB-303 squelch)
# F Phrygian | 132 BPM
# Uses: TR-909 with drag_electronic, acid bass, reverb-pad
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_2 = Scale(root=5, mode=Mode.PHRYGIAN)  # F Phrygian

SECTIONS_2 = [
    ("Intro", 4, ["acid_intro_hint", "pad_tense"]),
    ("Verse 1", 8, ["909_drums", "bass_303", "acid_pad", "hats_electro"]),
    ("Buildup", 4, ["pad_tense", "arp_acid_build", "909_hats_roll", "riser"]),
    (
        "Drop",
        8,
        ["909_drums_hard", "bass_303_wild", "acid_pad", "hats_electro_roll", "arp_acid_line"],
    ),
    ("Break", 4, ["acid_bass_solo_only", "pad_tense"]),
    ("Verse 2", 8, ["909_drums", "bass_303", "acid_pad", "hats_electro"]),
    (
        "Drop 2",
        8,
        [
            "909_drums_hard",
            "bass_303_wild",
            "acid_pad",
            "hats_electro_roll",
            "arp_acid_line",
            "riser",
        ],
    ),
    ("Outro", 4, ["acid_pad", "acid_bass_out", "impact_303"]),
]

INSTRUMENTS_2 = {
    "909_drums": 0,
    "909_drums_hard": 0,
    "909_hats_roll": 0,
    "acid_intro_hint": 0,
    "bass_303": 38,
    "bass_303_wild": 38,
    "acid_pad": 92,
    "pad_tense": 92,
    "hats_electro": 0,
    "hats_electro_roll": 0,
    "arp_acid_build": 0,
    "arp_acid_line": 0,
    "acid_bass_solo_only": 38,
    "acid_bass_out": 38,
    "riser": 97,
    "impact_303": 103,
}

PERC_2 = {
    "909_drums",
    "909_drums_hard",
    "909_hats_roll",
    "acid_intro_hint",
    "hats_electro",
    "hats_electro_roll",
}


def build_2(name):
    mods = []
    params = GeneratorParams(density=0.52)

    match name:
        case "909_drums":
            gen = ElectronicDrumsGenerator(
                params=params,
                kit="909",
                pattern="techno",
                sidechain=True,
                sidechain_depth=0.55,
                snare_delay=0.010,
                groove_swing=0.505,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.15,
                section_type="verse",
                auto_fills=True,
                groove_template=None,
                transient_ducking=True,
                ducking_duration=0.020,
                envelope_gating=True,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="sweep_lr",
                pan_alternation_rate=0.4,
                flam_probability=0.03,
                drag_probability=0.02,
            )
            mods.append(VelocityScalingModifier(scale=0.80))
            mods.append(HumanizeModifier(timing_std=0.010, velocity_std=3))

        case "909_drums_hard":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.62),
                kit="909",
                pattern="techno",
                sidechain=True,
                sidechain_depth=0.60,
                snare_delay=0.012,
                groove_swing=0.505,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.20,
                section_type="chorus",
                auto_fills=True,
                groove_template=None,
                transient_ducking=True,
                ducking_duration=0.020,
                envelope_gating=True,
                mute_boundaries=True,
                kick_less_verse=False,
                pan_mode="sweep_lr",
                flam_probability=0.05,
                drag_probability=0.03,
            )
            mods.append(VelocityScalingModifier(scale=0.88))

        case "909_hats_roll":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.50),
                pattern="drill_stutter" if random.random() < 0.5 else "trap_eighth",
                roll_density=0.65,
                open_hat_probability=0.12,
                pan_mode="sweep_lr",
                scale_snap_rolls=True,
                stutter_lengths=[4, 4],
            )
            mods.append(SwingController(swing_ratio=0.51, grid=0.25))
            mods.append(VelocityScalingModifier(scale=0.58))

        case "acid_intro_hint":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.30),
                kit="909",
                pattern="minimal",
                sidechain=False,
                groove_swing=0.50,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.00,
                section_type="intro",
                auto_fills=False,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="off",
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "bass_303":
            gen = SynthBassGenerator(
                params=params,
                waveform="acid",
                pattern="acid_line",
                slide_probability=0.30,
            )
            mods += [
                LimitNoteRangeModifier(low=36, high=55),
                VelocityScalingModifier(scale=0.80),
                HumanizeModifier(timing_std=0.012, velocity_std=4),
            ]

        case "bass_303_wild":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.65),
                waveform="acid",
                pattern="acid_line",
                slide_probability=0.50,
            )
            mods += [
                LimitNoteRangeModifier(low=34, high=58),
                VelocityScalingModifier(scale=0.85),
                HumanizeModifier(timing_std=0.010, velocity_std=5),
            ]

        case "acid_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.22),
                mode="phrygian_pad",
                chord_dur=4.0,
                velocity_level=0.16,
                register="mid",
                overlap=0.40,
            )

        case "pad_tense":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.18),
                mode="dim_cluster",
                chord_dur=4.0,
                velocity_level=0.12,
                register="mid",
                overlap=0.5,
            )

        case "hats_electro":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.35,
                open_hat_probability=0.12,
                pan_mode="alternate",
                scale_snap_rolls=True,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.51, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.62))

        case "hats_electro_roll":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.58),
                pattern="drill_stutter",
                roll_density=0.70,
                open_hat_probability=0.10,
                pan_mode="sweep_rl",
                scale_snap_rolls=True,
                stutter_lengths=[5, 7],
            )
            mods.append(SwingController(swing_ratio=0.51, grid=0.25))
            mods.append(VelocityScalingModifier(scale=0.58))

        case "arp_acid_build":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.65),
                pattern="up_down",
                note_duration=0.22,
            )
            mods += [
                VelocityScalingModifier(scale=0.65),
                LimitNoteRangeModifier(low=60, high=83),
                CrescendoModifier(start_vel=55, end_vel=82),
            ]

        case "arp_acid_line":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.58),
                pattern="up",
                note_duration=0.22,
            )
            mods += [
                HumanizeModifier(timing_std=0.008, velocity_std=2),
                VelocityScalingModifier(scale=0.65),
                LimitNoteRangeModifier(low=60, high=84),
            ]

        case "acid_bass_solo_only":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.60),
                waveform="acid",
                pattern="acid_line",
                slide_probability=0.20,
            )
            mods += [
                HumanizeModifier(timing_std=0.015, velocity_std=6),
                VelocityScalingModifier(scale=0.75),
                LimitNoteRangeModifier(low=32, high=55),
            ]

        case "acid_bass_out":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.40),
                waveform="acid",
                pattern="acid_line",
                slide_probability=0.50,
            )
            mods += [
                VelocityScalingModifier(scale=0.60),
                LimitNoteRangeModifier(low=34, high=58),
            ]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.35),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=100,
            )

        case "impact_303":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.28),
                impact_type="boom",
                tail_length=4.5,
                pitch_drop=20,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 3 — Iron Foundry (Industrial hard techno, Regis / Surgeon)
# D Dorian | 140 BPM
# Uses: TR-909 hard, breakbeat, reverb-pad, arp staccato
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_3 = Scale(root=2, mode=Mode.DORIAN)  # D Dorian (Dm → fourth degree = G minor feel)

SECTIONS_3 = [
    ("Intro", 4, ["pad_industrial", "909_hint_industrial"]),
    ("Verse 1", 8, ["909_industrial", "bass_hard", "pad_industrial", "arp_staccato"]),
    ("Buildup", 4, ["pad_industrial", "arp_bulldozer", "909_hats_militant", "riser_hard"]),
    (
        "Drop",
        8,
        ["909_industrial_hard", "bass_hard_slide", "pad_industrial", "arp_staccato", "ghost_snare"],
    ),
    ("Break", 4, ["pad_industrial", "bass_hard_solo"]),
    ("Verse 2", 8, ["909_industrial", "bass_hard", "pad_industrial", "arp_staccato"]),
    (
        "Drop 2",
        8,
        [
            "909_industrial_hard",
            "bass_hard_slide",
            "pad_industrial",
            "arp_staccato",
            "ghost_snare",
            "riser_hard",
        ],
    ),
    ("Outro", 4, ["pad_industrial", "909_hint_industrial", "impact_iron"]),
]

INSTRUMENTS_3 = {
    "909_industrial": 0,
    "909_industrial_hard": 0,
    "909_hint_industrial": 0,
    "909_hats_militant": 0,
    "bass_hard": 38,
    "bass_hard_slide": 38,
    "bass_hard_solo": 38,
    "pad_industrial": 92,
    "arp_staccato": 0,
    "arp_bulldozer": 0,
    "ghost_snare": 0,
    "riser_hard": 97,
    "impact_iron": 103,
}

PERC_3 = {
    "909_industrial",
    "909_industrial_hard",
    "909_hint_industrial",
    "909_hats_militant",
    "ghost_snare",
}


def build_3(name):
    mods = []
    params = GeneratorParams(density=0.52)

    match name:
        case "909_industrial":
            gen = ElectronicDrumsGenerator(
                params=params,
                kit="909",
                pattern="breakbeat",
                sidechain=True,
                sidechain_depth=0.50,
                snare_delay=0.020,
                hihat_delay=0.008,
                groove_swing=0.55,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.25,
                section_type="verse",
                auto_fills=True,
                groove_template=None,
                transient_ducking=True,
                
                envelope_gating=True,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="sweep_lr",
                pan_alternation_rate=0.5,
                flam_probability=0.06,
                drag_probability=0.04,
            )
            mods.append(VelocityScalingModifier(scale=0.82))
            mods.append(HumanizeModifier(timing_std=0.014, velocity_std=5))

        case "909_industrial_hard":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.65),
                kit="909",
                pattern="breakbeat",
                sidechain=True,
                sidechain_depth=0.60,
                snare_delay=0.025,
                hihat_delay=0.010,
                groove_swing=0.55,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.30,
                section_type="chorus",
                auto_fills=True,
                groove_template=None,
                transient_ducking=True,
                
                envelope_gating=True,
                mute_boundaries=True,
                kick_less_verse=False,
                pan_mode="sweep_lr",
                flam_probability=0.08,
                drag_probability=0.05,
            )
            mods.append(VelocityScalingModifier(scale=0.90))

        case "909_hint_industrial":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.30),
                kit="909",
                pattern="breakbeat",
                sidechain=False,
                groove_swing=0.50,
                swing_grid=0.25,
                choke_hats=True,
                ghost_snare_prob=0.00,
                section_type="intro",
                auto_fills=False,
                mute_boundaries=False,
                kick_less_verse=False,
                pan_mode="off",
            )
            mods.append(VelocityScalingModifier(scale=0.60))

        case "909_hats_militant":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.42),
                pattern="techno_straight",
                roll_density=0.40,
                open_hat_probability=0.08,
                pan_mode="sweep_rl",
                scale_snap_rolls=False,
                stutter_lengths=[3],
            )
            mods.append(SwingController(swing_ratio=0.52, grid=0.25))
            mods.append(VelocityScalingModifier(scale=0.68))

        case "bass_hard":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.25,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
                
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "bass_hard_slide":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.60),
                pattern="drill_sliding",
                slide_type="octave_jump",
                slide_probability=0.65,
                slide_curve="octave_whip",
                transient_ducking=True,
                envelope_gating=True,
                
            )
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "bass_hard_solo":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.55),
                waveform="saw",
                pattern="plucked",
                slide_probability=0.30,
            )
            mods += [
                LimitNoteRangeModifier(low=30, high=54),
                VelocityScalingModifier(scale=0.80),
                HumanizeModifier(timing_std=0.018, velocity_std=6),
            ]

        case "pad_industrial":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.18),
                mode="chromatic_pad",
                chord_dur=4.0,
                velocity_level=0.12,
                register="low",
                overlap=0.5,
            )

        case "arp_staccato":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.60),
                pattern="up_down",
                note_duration=0.18,
            )
            mods += [
                VelocityScalingModifier(scale=0.65),
                LimitNoteRangeModifier(low=62, high=82),
                HumanizeModifier(timing_std=0.010, velocity_std=3),
            ]

        case "arp_bulldozer":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.75),
                pattern="down",
                note_duration=0.15,
            )
            mods += [
                VelocityScalingModifier(scale=0.70),
                LimitNoteRangeModifier(low=58, high=80),
                CrescendoModifier(start_vel=60, end_vel=90),
            ]

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.30),
                target="snare",
                pattern="hiphop",
                ghost_velocity=22,
                ghost_density=0.40,
                placement="sixteenth",
            )
            mods.append(VelocityScalingModifier(scale=0.62))

        case "riser_hard":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.45),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=105,
            )

        case "impact_iron":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.25),
                impact_type="boom",
                tail_length=5.0,
                pitch_drop=22,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# Album Production
# ═══════════════════════════════════════════════════════════════════════════════

TRACKS = [
    {
        "title": "01_Obsidian_Floor",
        "scale": SCALE_1,
        "sections": SECTIONS_1,
        "build": build_1,
        "instruments": INSTRUMENTS_1,
        "bpm": 127,
        "mood": Mood.INTIMATE,
        "perc": PERC_1,
        "key_label": "Am",
    },
    {
        "title": "02_Acid_Sector",
        "scale": SCALE_2,
        "sections": SECTIONS_2,
        "build": build_2,
        "instruments": INSTRUMENTS_2,
        "bpm": 132,
        "mood": Mood.EXPERIMENTAL,
        "perc": PERC_2,
        "key_label": "Fm",
    },
    {
        "title": "03_Iron_Foundry",
        "scale": SCALE_3,
        "sections": SECTIONS_3,
        "build": build_3,
        "instruments": INSTRUMENTS_3,
        "bpm": 140,
        "mood": Mood.AGGRESSIVE,
        "perc": PERC_3,
        "key_label": "Dm",
    },
]


def main():
    album_dir = Path("output/album_techno")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   STEEL PULSE — Techno Album")
    print("   3 Cuts | Deep · Acid · Industrial")
    print("=" * 60 + "\n")

    totals = []
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
        totals.append((title, total_notes))
        print(f"  -> {out_path.name} ({total_notes} notes)\n")

    print("=" * 60)
    print("   PRODUCTION COMPLETE: STEEL PULSE")
    print(f"   Location: {album_dir}")
    for title, n in totals:
        print(f"   • {title}: {n} notes")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
