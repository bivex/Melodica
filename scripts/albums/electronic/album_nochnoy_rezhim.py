"""
НОЧНОЙ РЕЖИМ (Night Mode) — Trap Album
8 tracks. Dark trap with 808s, bells, hi-hats, dark pads, piano.
Uses section-based arrangement + produce_track() pipeline.
"""

import sys
import random
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo, KeyLabel, MusicTimeline
from melodica.generators import GeneratorParams
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    LimitNoteRangeModifier,
    SwingController,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.composer.album_pipeline import produce_track, Mood
from melodica.render_context import RenderContext

# ═══════════════════════════════════════════════════════════════════
# Harmony engine
# ═══════════════════════════════════════════════════════════════════

def harmonize(scale, bars, bpb=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5, melody_weight=0.25,
        secondary_dom_weight=0.10, extension_weight=0.06,
        repetition_penalty=0.08, cadence_weight=0.12,
    )
    degs = scale.degrees()
    contour = []
    for bar in range(bars):
        pos = bar % 4
        if pos == 0:    pc = int(degs[0])
        elif pos == 1:  pc = int(degs[min(2, len(degs) - 1)])
        elif pos == 2:  pc = int(degs[min(4, len(degs) - 1)] if len(degs) > 4 else degs[0])
        else:           pc = int(degs[0]) if random.random() < 0.6 else int(degs[min(3, len(degs) - 1)])
        contour.append(NoteInfo(pitch=44 + pc, start=bar * bpb, duration=bpb - 0.1, velocity=55))
    s_beats = bars * bpb
    chords = harmonizer.harmonize(contour, scale, s_beats)
    while len(chords) < bars:
        chords.append(
            chords[-1] if chords
            else ChordLabel(root=int(degs[0]), quality=Quality.MINOR, start=len(chords) * bpb, duration=bpb)
        )
    return chords


# ═══════════════════════════════════════════════════════════════════
# Arrangement engine
# ═══════════════════════════════════════════════════════════════════

def _map_section(name):
    n = name.lower()
    if "intro" in n: return "intro"
    if "pre" in n:   return "pre_chorus"
    if "hook" in n or "chorus" in n: return "chorus"
    if "outro" in n: return "outro"
    if "break" in n or "bridge" in n: return "bridge"
    if "double" in n: return "chorus"
    return "verse"


def generate_track(scale, sections, build_fn, bpb=4):
    tracks: dict[str, list[NoteInfo]] = {}
    contexts: dict[str, RenderContext] = {}
    art = ArticulationEngine()
    beat_offset = 0.0

    for name, bars, trks in sections:
        s_beats = bars * bpb
        chords = harmonize(scale, bars, bpb)

        abs_chords = [
            ChordLabel(root=c.root, quality=c.quality,
                       start=round(c.start + beat_offset, 6),
                       duration=c.duration, degree=c.degree)
            for c in chords
        ]

        print(f"    [{name:10s}] {bars:2d} bars | {', '.join(trks)}")

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
            ctx.section_type = _map_section(name)
            ctx.auto_fills = True

            notes = gen.render(chords, scale, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                contexts[tn] = gen._last_context

            section_timeline = MusicTimeline(
                chords=abs_chords,
                keys=[KeyLabel(scale=scale, start=0, duration=s_beats)],
            )
            mc = ModifierContext(duration_beats=s_beats, chords=abs_chords, timeline=section_timeline, scale=scale)
            for m in mods:
                try:
                    notes = m.modify(notes, mc)
                except Exception as e:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)

            if tn not in tracks:
                tracks[tn] = []

            for n in notes:
                dur = n.duration if n.duration > 0.001 else 0.1
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
        tracks[tn] = art.apply(tracks[tn], tn, beat_offset)
        tracks[tn] = [n for n in tracks[tn] if n.duration > 0.001]
        raw = art.add_sustain_pedal_events(tracks[tn], beat_offset)
        if raw:
            cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, cc, beat_offset


# ═══════════════════════════════════════════════════════════════════
# TRACK 1 — ЗАГРУЗКА (Intro)
# F#m | 130 BPM | Dark ambient, reverse pads
# ═══════════════════════════════════════════════════════════════════

SCALE_1 = Scale(root=6, mode=Mode.NATURAL_MINOR)

SECTIONS_1 = [
    ("Intro",  4, ["dark_pad", "arp_sweep"]),
    ("Verse",  4, ["dark_pad", "bass_808_soft", "trap_drums_soft", "arp_sweep"]),
    ("Outro",  2, ["dark_pad", "impact"]),
]

INSTRUMENTS_1 = {
    "dark_pad": 92, "arp_sweep": 98, "bass_808_soft": 38,
    "trap_drums_soft": 0, "impact": 103,
}


def build_1(name):
    mods = []
    match name:
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.18, key_range_low=36, key_range_high=60),
                mode="minor_pad", chord_dur=8.0, velocity_level=0.30, register="low",
            )
        case "arp_sweep":
            gen = ArpeggiatorGenerator(
                GeneratorParams(density=0.30, key_range_low=60, key_range_high=84),
                pattern="up", note_duration=0.5,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.01, velocity_std=3)]
        case "bass_808_soft":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.35, key_range_low=24, key_range_high=40),
                pattern="trap_basic", slide_probability=0.20, slide_curve="logarithmic",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=40))
        case "trap_drums_soft":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.05),
                variant="standard", kick_pattern="sparse", open_hat_probability=0.05,
                clap_on_two=True, section_type="intro", auto_fills=False,
                ghost_snare_prob=0.10, kick_less_verse=True,
            )
        case "impact":
            gen = FXImpactGenerator(
                GeneratorParams(density=0.15), impact_type="boom", tail_length=4.0, pitch_drop=18,
            )
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 2 — ДЫМ И НЕОН
# F#m | 140 BPM | Aggressive modern trap, 808 glide, bell, fast hats
# ═══════════════════════════════════════════════════════════════════

SCALE_2 = Scale(root=6, mode=Mode.NATURAL_MINOR)

SECTIONS_2 = [
    ("Hook",       4, ["trap_drums", "bass_808_glide", "bell_lead", "fast_hats", "dark_pad"]),
    ("Verse",      4, ["trap_drums", "bass_808_glide", "bell_lead", "fast_hats", "ghost_snare"]),
    ("Hook 2",     4, ["trap_drums", "bass_808_glide", "bell_lead", "fast_hats", "dark_pad"]),
    ("Verse 2",    4, ["trap_drums", "bass_808_glide", "bell_lead", "fast_hats", "ghost_snare"]),
    ("Hook 3",     4, ["trap_drums", "bass_808_glide", "bell_lead", "fast_hats", "dark_pad", "riser"]),
]

INSTRUMENTS_2 = {
    "trap_drums": 0, "bass_808_glide": 38, "bell_lead": 14,
    "fast_hats": 0, "dark_pad": 92, "ghost_snare": 0, "riser": 97,
}


def build_2(name):
    mods = []
    match name:
        case "trap_drums":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.10),
                variant="standard", hat_roll_density=0.6, kick_pattern="standard",
                open_hat_probability=0.15, clap_on_two=True, section_type="verse",
                auto_fills=True, ghost_snare_prob=0.25, kick_less_verse=False,
            )
            mods.append(HumanizeModifier(timing_std=0.008, velocity_std=4))
        case "bass_808_glide":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.55, key_range_low=24, key_range_high=40),
                pattern="trap_basic", slide_type="overlap", slide_probability=0.50,
                slide_curve="exponential",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=40))
        case "bell_lead":
            gen = LeadSynthGenerator(
                GeneratorParams(density=0.50, key_range_low=60, key_range_high=84),
                style="trance", portamento=0.20, vibrato_depth=0.15, note_length="staccato",
            )
            mods += [VelocityScalingModifier(scale=0.65), LimitNoteRangeModifier(low=60, high=84)]
        case "fast_hats":
            gen = HiHatStutterGenerator(
                GeneratorParams(density=0.50),
                pattern="trap_eighth", roll_density=0.45, open_hat_probability=0.10,
                pan_mode="alternate",
            )
            mods += [VelocityScalingModifier(scale=0.55), HumanizeModifier(timing_std=0.006, velocity_std=3)]
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.15, key_range_low=36, key_range_high=60),
                mode="minor_pad", chord_dur=4.0, velocity_level=0.20, register="low",
            )
            mods.append(VelocityScalingModifier(scale=0.35))
        case "ghost_snare":
            gen = GhostNotesGenerator(
                GeneratorParams(density=0.15),
                pattern="hiphop", target="snare", ghost_velocity=28, ghost_density=0.4,
            )
        case "riser":
            gen = FXRiserGenerator(
                GeneratorParams(density=0.40), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=105,
            )
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 3 — ХОЛОДНЫЙ ВЗГЛЯД
# Am | 145 BPM | Melancholic trap, piano, dark pad, deep 808
# ═══════════════════════════════════════════════════════════════════

SCALE_3 = Scale(root=9, mode=Mode.NATURAL_MINOR)

SECTIONS_3 = [
    ("Intro",    4, ["dark_pad", "piano"]),
    ("Hook",     4, ["trap_drums", "bass_808_deep", "dark_pad", "piano", "fast_hats"]),
    ("Verse",    4, ["trap_drums", "bass_808_deep", "dark_pad", "piano", "ghost_snare"]),
    ("Hook 2",   4, ["trap_drums", "bass_808_deep", "dark_pad", "piano", "fast_hats"]),
    ("Verse 2",  4, ["trap_drums", "bass_808_deep", "dark_pad", "piano", "ghost_snare"]),
    ("Outro",    2, ["dark_pad", "piano"]),
]

INSTRUMENTS_3 = {
    "trap_drums": 0, "bass_808_deep": 38, "dark_pad": 92,
    "piano": 0, "fast_hats": 0, "ghost_snare": 0,
}


def build_3(name):
    mods = []
    match name:
        case "trap_drums":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.10),
                variant="standard", hat_roll_density=0.5, kick_pattern="standard",
                open_hat_probability=0.12, clap_on_two=True, section_type="verse",
                auto_fills=True, ghost_snare_prob=0.20,
            )
        case "bass_808_deep":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.45, key_range_low=20, key_range_high=36),
                pattern="trap_basic", slide_type="overlap", slide_probability=0.35,
                slide_curve="exponential",
            )
            mods.append(LimitNoteRangeModifier(low=20, high=36))
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.15, key_range_low=36, key_range_high=60),
                mode="phrygian_pad", chord_dur=4.0, velocity_level=0.25, register="mid",
            )
            mods.append(VelocityScalingModifier(scale=0.40))
        case "piano":
            gen = PianoCompGenerator(
                GeneratorParams(density=0.40, key_range_low=48, key_range_high=72),
                comp_style="pop", voicing_type="close", accent_pattern="syncopated",
                chord_density=0.6,
            )
            mods.append(HumanizeModifier(timing_std=0.012, velocity_std=4))
        case "fast_hats":
            gen = HiHatStutterGenerator(
                GeneratorParams(density=0.45),
                pattern="trap_eighth", roll_density=0.35, open_hat_probability=0.10,
                pan_mode="sweep_lr",
            )
            mods.append(VelocityScalingModifier(scale=0.50))
        case "ghost_snare":
            gen = GhostNotesGenerator(
                GeneratorParams(density=0.12),
                pattern="hiphop", target="snare", ghost_velocity=25, ghost_density=0.35,
            )
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 4 — ПОД ПРИЦЕЛОМ
# Em | 150 BPM | Hard street trap, brass, distorted 808
# ═══════════════════════════════════════════════════════════════════

SCALE_4 = Scale(root=4, mode=Mode.NATURAL_MINOR)

SECTIONS_4 = [
    ("Hook",     4, ["trap_drums_hard", "bass_808_dist", "brass_lead", "fast_hats", "dark_pad"]),
    ("Verse",    4, ["trap_drums_hard", "bass_808_dist", "brass_lead", "fast_hats", "ghost_snare"]),
    ("Bridge",   2, ["dark_pad", "bass_808_soft", "riser"]),
    ("Hook 2",   4, ["trap_drums_hard", "bass_808_dist", "brass_lead", "fast_hats", "dark_pad", "impact"]),
    ("Outro",    2, ["dark_pad", "impact"]),
]

INSTRUMENTS_4 = {
    "trap_drums_hard": 0, "bass_808_dist": 38, "brass_lead": 62,
    "fast_hats": 0, "dark_pad": 92, "ghost_snare": 0,
    "riser": 97, "impact": 103, "bass_808_soft": 38,
}


def build_4(name):
    mods = []
    match name:
        case "trap_drums_hard":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.12),
                variant="standard", hat_roll_density=0.7, kick_pattern="standard",
                open_hat_probability=0.20, clap_on_two=True, section_type="chorus",
                auto_fills=True, ghost_snare_prob=0.30, kick_less_verse=False,
                sidechain_depth=0.7,
            )
            mods.append(HumanizeModifier(timing_std=0.006, velocity_std=5))
        case "bass_808_dist":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.60, key_range_low=24, key_range_high=40),
                pattern="trap_basic", slide_type="overlap", slide_probability=0.55,
                slide_curve="exponential",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=40))
        case "bass_808_soft":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.30, key_range_low=24, key_range_high=40),
                pattern="trap_basic", slide_probability=0.15,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=40))
        case "brass_lead":
            gen = LeadSynthGenerator(
                GeneratorParams(density=0.55, key_range_low=48, key_range_high=72),
                style="trance", portamento=0.10, vibrato_depth=0.25, note_length="staccato",
            )
            mods += [VelocityScalingModifier(scale=0.70), LimitNoteRangeModifier(low=48, high=72)]
        case "fast_hats":
            gen = HiHatStutterGenerator(
                GeneratorParams(density=0.55),
                pattern="drill_stutter", roll_density=0.55, open_hat_probability=0.12,
                pan_mode="alternate",
            )
            mods += [VelocityScalingModifier(scale=0.55), HumanizeModifier(timing_std=0.005, velocity_std=3)]
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.12, key_range_low=36, key_range_high=60),
                mode="dim_cluster", chord_dur=4.0, velocity_level=0.20, register="low",
            )
            mods.append(VelocityScalingModifier(scale=0.35))
        case "ghost_snare":
            gen = GhostNotesGenerator(
                GeneratorParams(density=0.18),
                pattern="hiphop", target="snare", ghost_velocity=30, ghost_density=0.45,
            )
        case "riser":
            gen = FXRiserGenerator(
                GeneratorParams(density=0.45), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=110,
            )
        case "impact":
            gen = FXImpactGenerator(
                GeneratorParams(density=0.20), impact_type="boom", tail_length=3.0, pitch_drop=24,
            )
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 5 — ПОЛНОЧЬ
# Cm | 138 BPM | Night ride, synth keys, smooth 808
# ═══════════════════════════════════════════════════════════════════

SCALE_5 = Scale(root=0, mode=Mode.NATURAL_MINOR)

SECTIONS_5 = [
    ("Intro",    4, ["dark_pad", "synth_keys", "arp"]),
    ("Verse",    4, ["trap_drums", "bass_808_smooth", "dark_pad", "synth_keys", "hihat"]),
    ("Hook",     4, ["trap_drums", "bass_808_smooth", "dark_pad", "synth_keys", "hihat", "arp"]),
    ("Verse 2",  4, ["trap_drums", "bass_808_smooth", "dark_pad", "synth_keys", "hihat"]),
    ("Hook 2",   4, ["trap_drums", "bass_808_smooth", "dark_pad", "synth_keys", "hihat", "arp"]),
]

INSTRUMENTS_5 = {
    "trap_drums": 0, "bass_808_smooth": 38, "dark_pad": 92,
    "synth_keys": 4, "hihat": 0, "arp": 98,
}


def build_5(name):
    mods = []
    match name:
        case "trap_drums":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.09),
                variant="standard", hat_roll_density=0.4, kick_pattern="standard",
                open_hat_probability=0.10, clap_on_two=True, section_type="verse",
                auto_fills=True, ghost_snare_prob=0.15, kick_less_verse=True,
            )
        case "bass_808_smooth":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.40, key_range_low=24, key_range_high=40),
                pattern="trap_basic", slide_type="overlap", slide_probability=0.25,
                slide_curve="logarithmic",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=40))
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.15, key_range_low=36, key_range_high=60),
                mode="minor_pad", chord_dur=4.0, velocity_level=0.25, register="low",
            )
            mods.append(VelocityScalingModifier(scale=0.40))
        case "synth_keys":
            gen = PianoCompGenerator(
                GeneratorParams(density=0.35, key_range_low=48, key_range_high=72),
                comp_style="pop", voicing_type="close", accent_pattern="syncopated",
                chord_density=0.5,
            )
            mods += [VelocityScalingModifier(scale=0.60), HumanizeModifier(timing_std=0.015, velocity_std=4)]
        case "hihat":
            gen = HiHatStutterGenerator(
                GeneratorParams(density=0.35),
                pattern="trap_eighth", roll_density=0.25, open_hat_probability=0.08,
                pan_mode="sweep_lr",
            )
            mods.append(VelocityScalingModifier(scale=0.45))
        case "arp":
            gen = ArpeggiatorGenerator(
                GeneratorParams(density=0.35, key_range_low=60, key_range_high=84),
                pattern="up", note_duration=0.375,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.01, velocity_std=3)]
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 6 — БЕЗ ТОРМОЗОВ
# Bbm | 155 BPM | Max energy, hard 808, synth lead, open hats
# ═══════════════════════════════════════════════════════════════════

SCALE_6 = Scale(root=10, mode=Mode.NATURAL_MINOR)

SECTIONS_6 = [
    ("Hook",        4, ["trap_drums_hard", "bass_808_hard", "synth_lead", "open_hats", "dark_pad"]),
    ("Verse",       4, ["trap_drums_hard", "bass_808_hard", "synth_lead", "open_hats", "ghost_snare"]),
    ("Hook 2",      4, ["trap_drums_hard", "bass_808_hard", "synth_lead", "open_hats", "dark_pad"]),
    ("Verse 2",     4, ["trap_drums_hard", "bass_808_hard", "synth_lead", "open_hats", "ghost_snare"]),
    ("Double Hook", 4, ["trap_drums_hard", "bass_808_hard", "synth_lead", "open_hats", "dark_pad", "riser"]),
]

INSTRUMENTS_6 = {
    "trap_drums_hard": 0, "bass_808_hard": 38, "synth_lead": 81,
    "open_hats": 0, "dark_pad": 92, "ghost_snare": 0, "riser": 97,
}


def build_6(name):
    mods = []
    match name:
        case "trap_drums_hard":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.12),
                variant="standard", hat_roll_density=0.75, kick_pattern="standard",
                open_hat_probability=0.25, clap_on_two=True, section_type="chorus",
                auto_fills=True, ghost_snare_prob=0.35, kick_less_verse=False,
                sidechain_depth=0.7, transient_ducking=True,
            )
            mods.append(HumanizeModifier(timing_std=0.005, velocity_std=5))
        case "bass_808_hard":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.65, key_range_low=24, key_range_high=40),
                pattern="trap_basic", slide_type="overlap", slide_probability=0.60,
                slide_curve="exponential",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=40))
        case "synth_lead":
            gen = LeadSynthGenerator(
                GeneratorParams(density=0.55, key_range_low=55, key_range_high=80),
                style="trance", portamento=0.15, vibrato_depth=0.30, note_length="legato",
            )
            mods += [VelocityScalingModifier(scale=0.70), LimitNoteRangeModifier(low=55, high=80)]
        case "open_hats":
            gen = HiHatStutterGenerator(
                GeneratorParams(density=0.55),
                pattern="drill_stutter", roll_density=0.60, open_hat_probability=0.20,
                pan_mode="alternate",
            )
            mods += [VelocityScalingModifier(scale=0.55), HumanizeModifier(timing_std=0.005, velocity_std=4)]
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.12, key_range_low=36, key_range_high=60),
                mode="chromatic_pad", chord_dur=4.0, velocity_level=0.18, register="low",
            )
            mods.append(VelocityScalingModifier(scale=0.30))
        case "ghost_snare":
            gen = GhostNotesGenerator(
                GeneratorParams(density=0.20),
                pattern="hiphop", target="snare", ghost_velocity=30, ghost_density=0.50,
            )
        case "riser":
            gen = FXRiserGenerator(
                GeneratorParams(density=0.45), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=115,
            )
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 7 — ТЕНИ
# Gm | 135 BPM | Dark cinematic trap, choir, piano, sub bass
# ═══════════════════════════════════════════════════════════════════

SCALE_7 = Scale(root=7, mode=Mode.NATURAL_MINOR)

SECTIONS_7 = [
    ("Intro",    4, ["choir_pad", "piano"]),
    ("Verse",    4, ["trap_drums", "sub_bass", "choir_pad", "piano", "hihat"]),
    ("Hook",     4, ["trap_drums", "sub_bass", "choir_pad", "piano", "hihat", "dark_pad"]),
    ("Verse 2",  4, ["trap_drums", "sub_bass", "choir_pad", "piano", "hihat", "ghost_snare"]),
    ("Hook 2",   4, ["trap_drums", "sub_bass", "choir_pad", "piano", "hihat", "dark_pad"]),
    ("Outro",    2, ["choir_pad", "piano"]),
]

INSTRUMENTS_7 = {
    "trap_drums": 0, "sub_bass": 38, "choir_pad": 52,
    "piano": 0, "hihat": 0, "dark_pad": 92, "ghost_snare": 0,
}


def build_7(name):
    mods = []
    match name:
        case "trap_drums":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.09),
                variant="standard", hat_roll_density=0.4, kick_pattern="standard",
                open_hat_probability=0.10, clap_on_two=True, section_type="verse",
                auto_fills=True, ghost_snare_prob=0.15, kick_less_verse=True,
            )
        case "sub_bass":
            gen = Bass808SlidingGenerator(
                GeneratorParams(density=0.40, key_range_low=20, key_range_high=36),
                pattern="trap_basic", slide_type="overlap", slide_probability=0.30,
                slide_curve="exponential",
            )
            mods.append(LimitNoteRangeModifier(low=20, high=36))
        case "choir_pad":
            gen = ChoirAahsGenerator(
                GeneratorParams(density=0.20, key_range_low=43, key_range_high=60),
                voice_count=4, dynamics="mp", vibrato=0.4, syllable="aah",
            )
            mods.append(VelocityScalingModifier(scale=0.45))
        case "piano":
            gen = PianoCompGenerator(
                GeneratorParams(density=0.38, key_range_low=48, key_range_high=72),
                comp_style="pop", voicing_type="close", accent_pattern="syncopated",
                chord_density=0.5,
            )
            mods += [VelocityScalingModifier(scale=0.65), HumanizeModifier(timing_std=0.012, velocity_std=4)]
        case "hihat":
            gen = HiHatStutterGenerator(
                GeneratorParams(density=0.30),
                pattern="trap_eighth", roll_density=0.25, open_hat_probability=0.08,
                pan_mode="sweep_lr",
            )
            mods.append(VelocityScalingModifier(scale=0.45))
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.10, key_range_low=36, key_range_high=55),
                mode="minor_pad", chord_dur=4.0, velocity_level=0.18, register="low",
            )
            mods.append(VelocityScalingModifier(scale=0.30))
        case "ghost_snare":
            gen = GhostNotesGenerator(
                GeneratorParams(density=0.12),
                pattern="hiphop", target="snare", ghost_velocity=25, ghost_density=0.35,
            )
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# TRACK 8 — РАССВЕТ (Outro)
# Dm | 125 BPM | Calm resolution, ambient piano, strings, soft bass
# ═══════════════════════════════════════════════════════════════════

SCALE_8 = Scale(root=2, mode=Mode.NATURAL_MINOR)

SECTIONS_8 = [
    ("Intro",    4, ["dark_pad", "piano", "arp"]),
    ("Verse",    4, ["dark_pad", "piano", "arp", "soft_bass", "soft_drums"]),
    ("Outro",    4, ["dark_pad", "piano", "arp"]),
]

INSTRUMENTS_8 = {
    "dark_pad": 92, "piano": 0, "arp": 98,
    "soft_bass": 35, "soft_drums": 0,
}


def build_8(name):
    mods = []
    match name:
        case "dark_pad":
            gen = DarkPadGenerator(
                GeneratorParams(density=0.12, key_range_low=36, key_range_high=60),
                mode="minor_pad", chord_dur=8.0, velocity_level=0.20, register="low",
            )
            mods.append(VelocityScalingModifier(scale=0.35))
        case "piano":
            gen = PianoCompGenerator(
                GeneratorParams(density=0.35, key_range_low=48, key_range_high=72),
                comp_style="pop", voicing_type="close", accent_pattern="syncopated",
                chord_density=0.4,
            )
            mods += [VelocityScalingModifier(scale=0.65), HumanizeModifier(timing_std=0.015, velocity_std=3)]
        case "arp":
            gen = ArpeggiatorGenerator(
                GeneratorParams(density=0.25, key_range_low=60, key_range_high=84),
                pattern="up", note_duration=0.5,
            )
            mods += [VelocityScalingModifier(scale=0.40), HumanizeModifier(timing_std=0.01, velocity_std=3)]
        case "soft_bass":
            gen = SynthBassGenerator(
                GeneratorParams(density=0.30, key_range_low=28, key_range_high=44),
                waveform="sine", pattern="plucked", slide_probability=0.10,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=44))
        case "soft_drums":
            gen = TrapDrumsGenerator(
                GeneratorParams(density=0.04),
                variant="standard", kick_pattern="sparse", open_hat_probability=0.03,
                clap_on_two=False, section_type="outro", auto_fills=False,
                ghost_snare_prob=0.05, kick_less_verse=True,
            )
            mods.append(VelocityScalingModifier(scale=0.45))
        case _:
            return None
    return gen, mods


# ═══════════════════════════════════════════════════════════════════
# Track Registry
# ═══════════════════════════════════════════════════════════════════

TRACKS = [
    {
        "title": "01_Zagruzka",
        "scale": SCALE_1, "sections": SECTIONS_1,
        "build": build_1, "instruments": INSTRUMENTS_1,
        "bpm": 130, "mood": Mood.AMBIENT, "key_label": "F#m",
    },
    {
        "title": "02_Dym_I_Neon",
        "scale": SCALE_2, "sections": SECTIONS_2,
        "build": build_2, "instruments": INSTRUMENTS_2,
        "bpm": 140, "mood": Mood.AGGRESSIVE, "key_label": "F#m",
    },
    {
        "title": "03_Holodnyj_Vzglyad",
        "scale": SCALE_3, "sections": SECTIONS_3,
        "build": build_3, "instruments": INSTRUMENTS_3,
        "bpm": 145, "mood": Mood.INTIMATE, "key_label": "Am",
    },
    {
        "title": "04_Dop_Prizeplom",
        "scale": SCALE_4, "sections": SECTIONS_4,
        "build": build_4, "instruments": INSTRUMENTS_4,
        "bpm": 150, "mood": Mood.AGGRESSIVE, "key_label": "Em",
    },
    {
        "title": "05_Polnoch",
        "scale": SCALE_5, "sections": SECTIONS_5,
        "build": build_5, "instruments": INSTRUMENTS_5,
        "bpm": 138, "mood": Mood.INTIMATE, "key_label": "Cm",
    },
    {
        "title": "06_Bez_Tormozov",
        "scale": SCALE_6, "sections": SECTIONS_6,
        "build": build_6, "instruments": INSTRUMENTS_6,
        "bpm": 155, "mood": Mood.AGGRESSIVE, "key_label": "Bbm",
    },
    {
        "title": "07_Teni",
        "scale": SCALE_7, "sections": SECTIONS_7,
        "build": build_7, "instruments": INSTRUMENTS_7,
        "bpm": 135, "mood": Mood.CINEMATIC, "key_label": "Gm",
    },
    {
        "title": "08_Rassvet",
        "scale": SCALE_8, "sections": SECTIONS_8,
        "build": build_8, "instruments": INSTRUMENTS_8,
        "bpm": 125, "mood": Mood.AMBIENT, "key_label": "Dm",
    },
]


# ═══════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════

def main():
    album_dir = Path(__file__).resolve().parent.parent.parent.parent / "output" / "nochnoy_rezhim"
    album_dir.mkdir(exist_ok=True, parents=True)

    print("НОЧНОЙ РЕЖИМ — Trap Album")
    print("=" * 50)

    for t in TRACKS:
        print(f"\n  {t['title']} ({t['key_label']}, {t['bpm']} BPM, {t['mood'].value})")
        raw, cc, total_beats = generate_track(t["scale"], t["sections"], t["build"])
        out_path = album_dir / f"{t['title']}.mid"
        produce_track(
            tracks=raw, bpm=t["bpm"], instruments=t["instruments"],
            path=str(out_path), mood=t["mood"], key=t["scale"],
            cc_events=cc, verbose=False, genre="trap",
        )
        print(f"    -> {out_path}")

    print(f"\nDone. {len(TRACKS)} tracks in {album_dir}")


if __name__ == "__main__":
    main()
