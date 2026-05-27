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
album_eight_o_eight.py — "808 Showcase" Modern Beats Album.

4 premium high-energy cuts showcasing the commercial BeatStars-grade engines:

  1. Sub-Bass Infinity   — UK/NY Drill / heavy glides     | G Minor     | 140 BPM
  2. Phonk District      — Aggressive Phonk / cowbells    | D Phrygian  | 130 BPM
  3. Melodic Gravity     — Melodic Plugg/Trap / sweeps    | E Minor     | 120 BPM
  4. Dystopian Drop      — Minimalist Trap / mutes & cuts | A Minor     | 150 BPM

Uses produce_track() pipeline for auto-mix, psychoacoustic, mastering.
"""

import sys
import random
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, KeyLabel, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.modern_chord import ModernChordPatternGenerator
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
# Arrangement generator — shared engine
# ═══════════════════════════════════════════════════════════════════════════════

def map_section_type(name: str) -> str:
    n = name.lower()
    if "intro" in n: return "intro"
    if "pre" in n: return "pre_chorus"
    if "hook" in n or "chorus" in n: return "chorus"
    if "outro" in n: return "outro"
    if "break" in n or "bridge" in n: return "bridge"
    return "verse"


def generate_track(scale, sections, build_fn, bpb=4):
    tracks: dict[str, list[NoteInfo]] = {}
    contexts: dict[str, RenderContext] = {}
    art = ArticulationEngine()
    beat_offset = 0.0

    # Track groove templates and notes generated for accuracy validation
    grooved_sections: dict[tuple[str, str], tuple[any, list[NoteInfo]]] = {}

    for name, bars, trks in sections:
        s_beats = bars * bpb
        chords = harmonize(scale, bars, bpb)
        
        # shift chords to absolute position
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

            # Build per-section timeline for modifiers
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

            # Store the notes for this section if a groove template is active on the generator
            if hasattr(gen, "groove_template") and gen.groove_template is not None:
                key = (tn, gen.groove_template.name)
                if key not in grooved_sections:
                    grooved_sections[key] = (gen.groove_template, [])
                grooved_sections[key][1].extend(section_notes)

        beat_offset += s_beats

    for k in tracks:
        tracks[k].sort(key=lambda n: n.start)

    cc = {}
    for tn in list(tracks):
        tracks[tn] = art.apply(tracks[tn], tn, beat_offset)
        tracks[tn] = [n for n in tracks[tn] if n.duration > 0.001]
        raw = art.add_sustain_pedal_events(tracks[tn], beat_offset)
        if raw:
            cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    # Console reporting of groove template validation
    if grooved_sections:
        print("\n  [Groove Accuracy Validation]")
        for (tn, gt_name), (template, notes) in sorted(grooved_sections.items()):
            res = template.verify_accuracy(notes)
            accuracy_pct = res["accuracy"] * 100
            matched = res["matched_notes"]
            total = res["total_notes"]
            
            # Print a neat progress-bar style status
            bar_len = 20
            filled_len = int(round(bar_len * res["accuracy"]))
            bar = "█" * filled_len + "░" * (bar_len - filled_len)
            
            print(f"    • {tn:15s} | Groove: {gt_name:10s} | {bar} | {accuracy_pct:5.1f}% ({matched}/{total} notes matched)")
        print()

    return tracks, cc, beat_offset


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 1 — Sub-Bass Infinity (UK/NY Drill)
# G Minor | 140 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_1 = Scale(root=7, mode=Mode.NATURAL_MINOR)

SECTIONS_1 = [
    ("Intro",    4, ["dark_pad", "vocals_hint"]),
    ("Verse 1",  8, ["bass_808", "trap_drums", "hihat", "dark_pad"]),
    ("Pre",      4, ["dark_pad", "hihat_rapid", "vocals", "riser"]),
    ("Chorus",   8, ["bass_808_slide", "trap_drums_drill", "hihat_rapid", "dark_pad", "vocals", "ghost_snare"]),
    ("Verse 2",  8, ["bass_808", "trap_drums", "hihat", "dark_pad", "vocals", "ghost_snare"]),
    ("Chorus 2", 8, ["bass_808_slide", "trap_drums_drill", "hihat_rapid", "dark_pad", "vocals", "ghost_snare", "riser"]),
    ("Outro",    4, ["dark_pad", "bass_808_soft", "impact"]),
]

INSTRUMENTS_1 = {
    "bass_808": 38,
    "bass_808_slide": 38,
    "bass_808_soft": 38,
    "trap_drums": 0,
    "trap_drums_drill": 0,
    "hihat": 0,
    "hihat_rapid": 0,
    "ghost_snare": 0,
    "dark_pad": 92,
    "vocals_hint": 54,
    "vocals": 54,
    "riser": 97,
    "impact": 103,
}

PERC_1 = {"trap_drums", "trap_drums_drill", "hihat", "hihat_rapid", "ghost_snare"}


def build_1(name):
    mods = []
    params = GeneratorParams(density=0.5)

    match name:
        case "bass_808":
            # Gated warm 808
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.40,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "bass_808_slide":
            # Drill sliding 808 with rapid pitch adjustments
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="drill_sliding",
                slide_type="chromatic",
                slide_probability=0.75,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.95))

        case "bass_808_soft":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.20,
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "trap_drums":
            gen = TrapDrumsGenerator(
                params=params,
                variant="standard",
                hat_roll_density=0.35,
                kick_pattern="standard",
                mute_boundaries=True,
                kick_less_verse=False,
            )
            mods.append(VelocityScalingModifier(scale=0.85))

        case "trap_drums_drill":
            gen = TrapDrumsGenerator(
                params=params,
                variant="drill",
                hat_roll_density=0.65,
                kick_pattern="syncopated",
                mute_boundaries=True,
                kick_less_verse=True,
            )
            mods.append(VelocityScalingModifier(scale=0.90))

        case "hihat":
            # Advanced hi-hats with swing and alternate panning
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.35,
                open_hat_probability=0.12,
                pan_mode="alternate",
                scale_snap_rolls=True,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "hihat_rapid":
            # Drill rapid fire stutters with sweep panning
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
            mods.append(VelocityScalingModifier(scale=0.70))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.35),
                target="snare",
                pattern="hiphop",
                ghost_velocity=32,
                ghost_density=0.45,
                placement="sixteenth",
            )

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.25),
                mode="phrygian_pad",
                chord_dur=4.0,
                velocity_level=0.15,
                register="mid",
            )

        case "vocals_hint":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.25),
                processing="pitch_shift",
                density=0.30,
                chop_pattern="syncopated",
                source_pitch=62,
            )
            mods.append(VelocityScalingModifier(scale=0.40))

        case "vocals":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.50),
                processing="pitch_shift",
                density=0.55,
                chop_pattern="syncopated",
                source_pitch=62,
            )
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))
            mods.append(VelocityScalingModifier(scale=0.50))

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
# TRACK 2 — Phonk District (Aggressive Phonk)
# D Phrygian | 130 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_2 = Scale(root=2, mode=Mode.PHRYGIAN)

SECTIONS_2 = [
    ("Intro",    4, ["dark_pad", "cowbell_spare"]),
    ("Verse 1",  8, ["bass_808", "trap_drums", "hihat", "dark_pad", "cowbell_spare"]),
    ("Pre",      4, ["dark_pad", "hihat_rapid", "cowbell_spare", "riser"]),
    ("Chorus",   8, ["bass_808_slide_exp", "trap_drums_hard", "hihat_rapid", "cowbell_full", "dark_pad", "lead", "ghost_snare"]),
    ("Verse 2",  8, ["bass_808", "trap_drums", "hihat", "dark_pad", "cowbell_spare", "lead_soft"]),
    ("Chorus 2", 8, ["bass_808_slide_exp", "trap_drums_hard", "hihat_rapid", "cowbell_full", "dark_pad", "lead", "ghost_snare", "riser"]),
    ("Outro",    4, ["dark_pad", "bass_808_soft", "impact"]),
]

INSTRUMENTS_2 = {
    "bass_808": 38,
    "bass_808_slide_exp": 38,
    "bass_808_soft": 38,
    "trap_drums": 0,
    "trap_drums_hard": 0,
    "hihat": 0,
    "hihat_rapid": 0,
    "cowbell_spare": 0,
    "cowbell_full": 0,
    "ghost_snare": 0,
    "dark_pad": 92,
    "lead": 81,
    "lead_soft": 81,
    "riser": 97,
    "impact": 103,
}

PERC_2 = {"trap_drums", "trap_drums_hard", "hihat", "hihat_rapid", "cowbell_spare", "cowbell_full", "ghost_snare"}


def build_2(name):
    mods = []
    params = GeneratorParams(density=0.5)

    match name:
        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.45,
                slide_curve="exponential",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "bass_808_slide_exp":
            # Aggressive octave jumps with exponential sweeps
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="rolling",
                slide_type="octave_jump",
                slide_probability=0.70,
                slide_curve="octave_whip",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.98))

        case "bass_808_soft":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.20,
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "trap_drums":
            gen = TrapDrumsGenerator(
                params=params,
                variant="standard",
                hat_roll_density=0.30,
                kick_pattern="standard",
                mute_boundaries=True,
            )
            mods.append(VelocityScalingModifier(scale=0.85))

        case "trap_drums_hard":
            gen = TrapDrumsGenerator(
                params=params,
                variant="standard",
                hat_roll_density=0.50,
                kick_pattern="syncopated",
                mute_boundaries=True,
                kick_less_verse=False,
            )
            mods.append(VelocityScalingModifier(scale=0.92))

        case "hihat":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.30,
                open_hat_probability=0.10,
                pan_mode="alternate",
                scale_snap_rolls=True,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.75))

        case "hihat_rapid":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="drill_stutter",
                roll_density=0.55,
                open_hat_probability=0.06,
                pan_mode="sweep_rl",
                scale_snap_rolls=True,
                stutter_lengths=[5, 7],
            )
            mods.append(SwingController(swing_ratio=0.57, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "cowbell_spare":
            gen = PhonkGenerator(
                params=GeneratorParams(density=0.20),
                variant="lofi_phonk",
                cowbell_density=0.35,
                bass_slide_amount=0,
                memphis_chops=False,
                aggression=0.20,
            )
            mods.append(VelocityScalingModifier(scale=0.45))

        case "cowbell_full":
            gen = PhonkGenerator(
                params=GeneratorParams(density=0.65),
                variant="classic_phonk",
                cowbell_density=0.75,
                bass_slide_amount=4,
                memphis_chops=True,
                aggression=0.60,
            )
            mods.append(VelocityScalingModifier(scale=0.70))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.30),
                mode="phrygian_pad",
                chord_dur=4.0,
                velocity_level=0.18,
                register="mid",
            )

        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.50),
                style="supersaw",
                portamento=0.25,
                note_length="mixed",
            )
            mods.append(LimitNoteRangeModifier(low=58, high=80))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "lead_soft":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.25),
                style="retro",
                portamento=0.15,
                note_length="legato",
            )
            mods.append(LimitNoteRangeModifier(low=60, high=76))
            mods.append(VelocityScalingModifier(scale=0.40))
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=3))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.30),
                target="snare",
                pattern="hiphop",
                ghost_velocity=30,
                ghost_density=0.40,
                placement="sixteenth",
            )

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
                params=GeneratorParams(density=0.30),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=15,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 3 — Melodic Gravity (Melodic Plugg/Trap)
# E Minor | 120 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_3 = Scale(root=4, mode=Mode.NATURAL_MINOR)

SECTIONS_3 = [
    ("Intro",    4, ["dark_pad", "keys_comp", "hihat"]),
    ("Verse 1",  8, ["bass_808", "trap_drums", "hihat", "dark_pad", "keys_comp"]),
    ("Pre",      4, ["dark_pad", "keys_busy", "hihat_rapid", "riser"]),
    ("Chorus",   8, ["bass_808_slide_log", "trap_drums_melodic", "hihat_rapid", "dark_pad", "keys_hook", "vocal_chops", "ghost_snare"]),
    ("Verse 2",  8, ["bass_808", "trap_drums", "hihat", "dark_pad", "keys_comp", "vocal_chops"]),
    ("Chorus 2", 8, ["bass_808_slide_log", "trap_drums_melodic", "hihat_rapid", "dark_pad", "keys_hook", "vocal_chops", "ghost_snare", "riser"]),
    ("Outro",    4, ["dark_pad", "bass_808_soft", "impact"]),
]

INSTRUMENTS_3 = {
    "bass_808": 38,
    "bass_808_slide_log": 38,
    "bass_808_soft": 38,
    "trap_drums": 0,
    "trap_drums_melodic": 0,
    "hihat": 0,
    "hihat_rapid": 0,
    "ghost_snare": 0,
    "dark_pad": 92,
    "keys_comp": 4,
    "keys_busy": 4,
    "keys_hook": 4,
    "vocal_chops": 54,
    "riser": 97,
    "impact": 103,
}

PERC_3 = {"trap_drums", "trap_drums_melodic", "hihat", "hihat_rapid", "ghost_snare"}


def build_3(name):
    mods = []
    params = GeneratorParams(density=0.5)

    match name:
        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.35,
                slide_curve="linear",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "bass_808_slide_log":
            # Melodic plugg logarithmic slide curves
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="overlap",
                slide_probability=0.60,
                slide_curve="logarithmic",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.92))

        case "bass_808_soft":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.15,
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.60))

        case "trap_drums":
            gen = TrapDrumsGenerator(
                params=params,
                variant="standard",
                hat_roll_density=0.30,
                kick_pattern="standard",
                mute_boundaries=True,
            )
            mods.append(VelocityScalingModifier(scale=0.82))

        case "trap_drums_melodic":
            gen = TrapDrumsGenerator(
                params=params,
                variant="melodic",
                hat_roll_density=0.55,
                kick_pattern="syncopated",
                mute_boundaries=True,
                kick_less_verse=True,
            )
            mods.append(VelocityScalingModifier(scale=0.85))

        case "hihat":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.35,
                open_hat_probability=0.15,
                pan_mode="sweep_rl",
                scale_snap_rolls=True,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.75))

        case "hihat_rapid":
            # Pentatonic scale snapped sweeps
            gen = HiHatStutterGenerator(
                params=params,
                pattern="drill_stutter",
                roll_density=0.50,
                open_hat_probability=0.10,
                pan_mode="sweep_lr",
                scale_snap_rolls=True,
                stutter_lengths=[5, 7],
            )
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.68))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.25),
                mode="minor_pad",
                chord_dur=4.0,
                velocity_level=0.14,
                register="mid",
            )

        case "keys_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.35),
                comp_style="jazz",
                voicing_type="rootless",
                accent_pattern="syncopated",
                chord_density=0.55,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.38),
                     HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "keys_busy":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.48),
                extension="min7",
                stab_pattern="dense",
                voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.35),
                     HumanizeModifier(timing_std=0.012, velocity_std=4)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.45),
                extension="maj9",
                stab_pattern="syncopated",
                voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "vocal_chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.45),
                processing="pitch_shift",
                density=0.50,
                chop_pattern="syncopated",
                source_pitch=64,
            )
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))
            mods.append(VelocityScalingModifier(scale=0.45))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.25),
                target="snare",
                pattern="hiphop",
                ghost_velocity=28,
                ghost_density=0.35,
                placement="sixteenth",
            )

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
# TRACK 4 — Dystopian Drop (Minimalist Trap)
# A Minor | 150 BPM
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_4 = Scale(root=9, mode=Mode.NATURAL_MINOR)

SECTIONS_4 = [
    ("Intro",    4, ["dark_pad", "ghost_snare"]),
    ("Verse 1",  8, ["bass_808_whip", "trap_drums_minimal", "hihat", "dark_pad"]),
    ("Pre",      4, ["dark_pad", "hihat_rapid", "riser"]),
    ("Chorus",   8, ["bass_808_whip", "trap_drums_minimal_hard", "hihat_rapid", "dark_pad", "lead", "ghost_snare"]),
    ("Verse 2",  8, ["bass_808_whip", "trap_drums_minimal", "hihat", "dark_pad", "ghost_snare"]),
    ("Chorus 2", 8, ["bass_808_whip", "trap_drums_minimal_hard", "hihat_rapid", "dark_pad", "lead", "ghost_snare", "riser"]),
    ("Outro",    4, ["dark_pad", "bass_808_soft", "impact"]),
]

INSTRUMENTS_4 = {
    "bass_808_whip": 38,
    "bass_808_soft": 38,
    "trap_drums_minimal": 0,
    "trap_drums_minimal_hard": 0,
    "hihat": 0,
    "hihat_rapid": 0,
    "ghost_snare": 0,
    "dark_pad": 92,
    "lead": 81,
    "riser": 97,
    "impact": 103,
}

PERC_4 = {"trap_drums_minimal", "trap_drums_minimal_hard", "hihat", "hihat_rapid", "ghost_snare"}


def build_4(name):
    mods = []
    params = GeneratorParams(density=0.5)

    match name:
        case "bass_808_whip":
            # Octave whip curves with extreme gated ducking
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_syncopated",
                slide_type="octave_jump",
                slide_probability=0.70,
                slide_curve="octave_whip",
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.96))

        case "bass_808_soft":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.10,
                transient_ducking=True,
                envelope_gating=True,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.60))

        case "trap_drums_minimal":
            # Highly dramatic mute boundaries & kick-less verse entries
            gen = TrapDrumsGenerator(
                params=params,
                variant="minimal",
                hat_roll_density=0.25,
                kick_pattern="sparse",
                mute_boundaries=True,
                kick_less_verse=True,
            )
            mods.append(VelocityScalingModifier(scale=0.82))

        case "trap_drums_minimal_hard":
            gen = TrapDrumsGenerator(
                params=params,
                variant="minimal",
                hat_roll_density=0.45,
                kick_pattern="standard",
                mute_boundaries=True,
                kick_less_verse=False,
            )
            mods.append(VelocityScalingModifier(scale=0.88))

        case "hihat":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.25,
                open_hat_probability=0.08,
                pan_mode="alternate",
                scale_snap_rolls=True,
                stutter_lengths=[3, 5],
            )
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.72))

        case "hihat_rapid":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="drill_stutter",
                roll_density=0.50,
                open_hat_probability=0.05,
                pan_mode="sweep_lr",
                scale_snap_rolls=True,
                stutter_lengths=[5, 7],
            )
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.62))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.20),
                mode="phrygian_pad",
                chord_dur=4.0,
                velocity_level=0.12,
                register="mid",
            )

        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.40),
                style="retro",
                portamento=0.20,
                note_length="mixed",
            )
            mods.append(LimitNoteRangeModifier(low=57, high=76))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))
            mods.append(VelocityScalingModifier(scale=0.60))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.20),
                target="snare",
                pattern="hiphop",
                ghost_velocity=25,
                ghost_density=0.30,
                placement="sixteenth",
            )

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.25),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=85,
            )

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.20),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=12,
            )

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# Album Production
# ═══════════════════════════════════════════════════════════════════════════════

TRACKS = [
    {
        "title": "01_Sub-Bass_Infinity",
        "scale": SCALE_1, "sections": SECTIONS_1, "build": build_1,
        "instruments": INSTRUMENTS_1, "bpm": 140, "mood": Mood.AGGRESSIVE,
        "perc": PERC_1, "key_label": "Gm",
    },
    {
        "title": "02_Phonk_District",
        "scale": SCALE_2, "sections": SECTIONS_2, "build": build_2,
        "instruments": INSTRUMENTS_2, "bpm": 130, "mood": Mood.AGGRESSIVE,
        "perc": PERC_2, "key_label": "Dm",
    },
    {
        "title": "03_Melodic_Gravity",
        "scale": SCALE_3, "sections": SECTIONS_3, "build": build_3,
        "instruments": INSTRUMENTS_3, "bpm": 120, "mood": Mood.CINEMATIC,
        "perc": PERC_3, "key_label": "Em",
    },
    {
        "title": "04_Dystopian_Drop",
        "scale": SCALE_4, "sections": SECTIONS_4, "build": build_4,
        "instruments": INSTRUMENTS_4, "bpm": 150, "mood": Mood.AGGRESSIVE,
        "perc": PERC_4, "key_label": "Am",
    },
]


def main():
    album_dir = Path("output/album_eight_o_eight")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   808 SHOWCASE — Modern BeatStars-Grade Bass & Beats Album")
    print("   4 Cuts | Heavy UK/NY Drill · Aggressive Phonk · Plugg · Minimalist Trap")
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
    print("   PRODUCTION COMPLETE: 808 SHOWCASE")
    print(f"   Location: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
