
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
album_velvet_nights.py — "Velvet Nights" R&B Beats Album.

5 cuts across R&B sub-genres, each with pro arrangement:

  1. Midnight Velvet    — Slow Jam / Neo-Soul    | Eb Dorian | 75 BPM
  2. Silk & Smoke       — New Jack Swing          | Gb Major  | 92 BPM
  3. Drip               — Modern Trap-Soul        | Bb Dorian | 100 BPM
  4. Golden Hour         — Gospel-Soul / Warm     | Db Lydian | 78 BPM
  5. After Hours         — Bedroom R&B / Lo-Fi   | F Minor   | 70 BPM

Uses produce_track() pipeline for auto-mix, psychoacoustic, mastering.
"""

import sys
import random
import warnings
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
from melodica.generators.backbeat import BackbeatGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.strings_ensemble import StringsEnsembleGenerator
from melodica.generators.guitar_strumming import GuitarStrummingGenerator
from melodica.generators.markov import MarkovMelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.vocal_melisma import VocalMelismaGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.vocal_adlibs import VocalAdlibsGenerator
from melodica.generators.vocal_melody_auto import VocalMelodyAutoGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.brass_section import BrassSectionGenerator
from melodica.generators.beat_repeat import BeatRepeatGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.generators.choir_ahhs import ChoirAahsGenerator
from melodica.generators.strings_legato import StringsLegatoGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.lofi_hiphop import LoFiHipHopGenerator
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
        melody_weight=0.22,
        secondary_dom_weight=0.12,
        extension_weight=0.10,
        repetition_penalty=0.06,
        cadence_weight=0.10,
    )
    degs = scale.degrees()
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
    chords = harmonizer.harmonize(contour, scale, bars * bpb)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(root=int(degs[0]), quality=Quality.MINOR,
                            start=len(chords) * bpb, duration=bpb)
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

    grooved_sections: dict[tuple[str, str], tuple[any, list[NoteInfo]]] = {}

    for name, bars, trks in sections:
        s_beats = bars * bpb
        chords = harmonize(scale, bars, bpb)
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

            mc = ModifierContext(duration_beats=s_beats, chords=chords, timeline=None, scale=scale)
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
    for tn in list(tracks):
        tracks[tn] = art.apply(tracks[tn], tn, beat_offset)
        tracks[tn] = [n for n in tracks[tn] if n.duration > 0.001]
        raw = art.add_sustain_pedal_events(tracks[tn], beat_offset)
        if raw:
            cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

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
            print(f"    • {tn:15s} | Groove: {gt_name:10s} | {bar} | {accuracy_pct:5.1f}% ({matched}/{total} notes matched)")
        print()

    return tracks, cc, beat_offset


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 1 — Midnight Velvet (Neo-Soul Slow Jam)
# Eb Dorian | 75 BPM | 44 bars
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_1 = Scale(root=3, mode=Mode.DORIAN)

SECTIONS_1 = [
    ("Intro",      4, ["arp_sparp", "pad_ambient", "organ_soft"]),
    ("V1",         8, ["keys_comp", "bass", "groove", "melody"]),
    ("Pre",        4, ["keys_busy", "organ", "bass_slap", "groove_full", "melody_pre", "riser"]),
    ("Hook",       8, ["keys_hook", "bass_slap_hook", "groove_full", "melody_hook",
                       "counter", "arp_converge", "vocal_melisma", "brass_stab", "chops"]),
    ("Breakdown",  4, ["keys_solo", "strings_pad"]),
    ("Hook 2",     8, ["keys_hook", "bass_slap_hook", "groove_full", "melody_hook",
                       "counter", "arp_converge", "chops", "riser", "filter_sweep"]),
    ("Outro",      4, ["pad_ambient", "organ_soft", "bass_walk"]),
]

INSTRUMENTS_1 = {
    "arp_sparp": 88, "arp_converge": 88,
    "pad_ambient": 98,
    "organ_soft": 16, "organ": 16,
    "keys_comp": 4, "keys_busy": 4, "keys_hook": 4, "keys_solo": 4,
    "bass": 33, "bass_walk": 33, "bass_slap": 33, "bass_slap_hook": 33,
    "groove": 0, "groove_full": 0,
    "melody": 56, "melody_hook": 56, "melody_pre": 56,
    "counter": 52,
    "vocal_melisma": 85,
    "brass_stab": 62,
    "chops": 54,
    "strings_pad": 48,
    "riser": 97, "filter_sweep": 95,
}

PERC_1 = {"groove", "groove_full"}


def build_1(name):
    mods = []
    match name:
        case "arp_sparp":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.12), pattern="up",
                note_duration=0.75, voicing="open", octaves=2,
            )
            mods += [VelocityScalingModifier(scale=0.25), HumanizeModifier(timing_std=0.03, velocity_std=3)]

        case "arp_converge":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.35), pattern="converge",
                note_duration=0.25, voicing="open", octaves=2,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "pad_ambient":
            gen = AmbientPadGenerator(
                params=GeneratorParams(density=0.08), voicing="spread",
                note_range_low=36, note_range_high=60,
            )
            mods += [VelocityScalingModifier(scale=0.25), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "organ_soft":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.12), registration="ballad",
                leslie_speed="slow", percussion=False, vibrato=True, sustain_bars=1.5,
            )
            mods.append(VelocityScalingModifier(scale=0.22))

        case "organ":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.22), registration="gospel",
                leslie_speed="slow", percussion=True, vibrato=False, sustain_bars=1.0,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "keys_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.38), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.65,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "keys_busy":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.48), extension="min7",
                stab_pattern="dense", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.44), extension="maj9",
                stab_pattern="syncopated", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.52),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "keys_solo":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.42), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.70,
            )
            mods += [LimitNoteRangeModifier(low=46, high=79), VelocityScalingModifier(scale=0.50),
                     HumanizeModifier(timing_std=0.025, velocity_std=6),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "bass":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.45), approach_style="mixed",
                connect_roots=True, add_chromatic_passing=True, swing_eighth_ratio=0.65,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "bass_walk":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.30), approach_style="diatonic",
                connect_roots=True, add_chromatic_passing=False, swing_eighth_ratio=0.60,
            )
            mods += [LimitNoteRangeModifier(low=28, high=48), VelocityScalingModifier(scale=0.30),
                     CrescendoModifier(start_vel=55, end_vel=25)]

        case "bass_slap":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.50), slap_pattern="funky",
                ghost_note_prob=0.35, pop_probability=0.40, octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.82),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "bass_slap_hook":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.55), slap_pattern="slap_pop",
                ghost_note_prob=0.40, pop_probability=0.50, octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.85),
                     HumanizeModifier(timing_std=0.01, velocity_std=4)]

        case "groove":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.45), groove_pattern="soul",
                ghost_note_vel=30, accent_vel=105,
            )
            mods.append(HumanizeModifier(timing_std=0.01, velocity_std=6))

        case "groove_full":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.55), groove_pattern="funk_1",
                ghost_note_vel=32, accent_vel=110,
            )
            mods += [HumanizeModifier(timing_std=0.01, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.35), harmony_note_probability=0.70,
                note_range_low=58, note_range_high=79, note_repetition_probability=0.14,
                steps_probability=0.90, random_movement=0.78, first_note="any_chord",
                last_note="last_chord_root", after_leap="step_opposite", climax="first_plus_maj3",
                syncopation=0.35, rhythm_variety=0.5, phrase_length=8.0,
                drama_shape="crescendo", drama_peak=0.55,
                groove_template=SWING_60, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=58, high=79), VelocityScalingModifier(scale=0.72),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "melody_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45), harmony_note_probability=0.72,
                note_range_low=60, note_range_high=82, note_repetition_probability=0.08,
                steps_probability=0.88, random_movement=0.72, first_note="chord_root",
                last_note="last_chord_root", after_leap="step_opposite", climax="up_5th",
                penultimate_step_above=True, syncopation=0.4, rhythm_variety=0.55,
                phrase_length=8.0, drama_shape="dramatic", drama_peak=0.65,
                motif_probability=0.6, groove_template=SWING_60,
                beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=60, high=82), VelocityScalingModifier(scale=0.80),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "melody_pre":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.40), harmony_note_probability=0.65,
                note_range_low=58, note_range_high=80, note_repetition_probability=0.10,
                steps_probability=0.90, random_movement=0.70, first_note="scale",
                last_note="any", after_leap="step_any", climax="up_octave",
                syncopation=0.45, phrase_length=4.0, drama_shape="crescendo", drama_peak=0.7,
                groove_template=SWING_60, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=58, high=80), VelocityScalingModifier(scale=0.70),
                     CrescendoModifier(start_vel=40, end_vel=80),
                     HumanizeModifier(timing_std=0.02, velocity_std=5)]

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.30), motion_preference="mixed",
                dissonance_on_weak=True, interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=65, high=84), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "vocal_melisma":
            gen = VocalMelismaGenerator(
                params=GeneratorParams(density=0.30), style="rnb",
                run_length=4, ornament_prob=0.4, vibrato_depth=0.3, register_center=65,
            )
            mods += [LimitNoteRangeModifier(low=58, high=77), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "brass_stab":
            gen = BrassSectionGenerator(
                params=GeneratorParams(density=0.15), articulation="hit",
                voicing="closed", intensity=0.9, divisi_count=3,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.01, velocity_std=3)]

        case "strings_pad":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.10), section_size="chamber",
                articulation="sustained", divisi=2, dynamic_curve="flat",
            )
            mods.append(VelocityScalingModifier(scale=0.35))

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.35), processing="pitch_shift",
                density=0.40, chop_pattern="syncopated", source_pitch=65,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.25), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=48,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case "filter_sweep":
            gen = FilterSweepGenerator(
                params=GeneratorParams(density=0.20), sweep_type="lowpass_open",
                resonance=0.5, duration=4.0, curve="exponential",
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 2 — Silk & Smoke (New Jack Swing)
# Gb Major | 92 BPM | 44 bars
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_2 = Scale(root=6, mode=Mode.MAJOR)

SECTIONS_2 = [
    ("Intro",      4, ["keys_warmup", "synth_bass_hint", "hihat_sparp"]),
    ("V1",         8, ["keys_comp", "synth_bass", "groove", "melody"]),
    ("Hook",       8, ["keys_hook", "bass_slap", "drums", "melody_hook",
                       "brass_stab", "chops"]),
    ("Break A",    2, ["keys_solo", "strings_pad"]),
    ("Break B",    2, ["keys_soft", "strings_pad", "bass_walk_back"]),
    ("V2",         8, ["keys_comp", "synth_bass", "drums", "guitar_funk", "melody"]),
    ("Hook 2",     8, ["keys_hook", "bass_slap", "drums", "melody_hook",
                       "brass_stab", "chops", "riser", "counter"]),
    ("Outro",      4, ["keys_soft", "strings_pad", "bass_walk"]),
]

INSTRUMENTS_2 = {
    "keys_warmup": 4, "keys_comp": 4, "keys_hook": 4, "keys_soft": 4, "keys_solo": 4,
    "synth_bass_hint": 38, "synth_bass": 38, "bass_slap": 33,
    "bass_walk": 33, "bass_walk_back": 33,
    "groove": 0, "drums": 0,
    "hihat_sparp": 0,
    "guitar_funk": 27,
    "melody": 56, "melody_hook": 56,
    "brass_stab": 62,
    "chops": 54, "counter": 52,
    "strings_pad": 48,
    "riser": 97,
}

PERC_2 = {"groove", "drums", "hihat_sparp"}


def build_2(name):
    mods = []
    match name:
        case "keys_warmup":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15), comp_style="pop",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.35,
            )
            mods += [VelocityScalingModifier(scale=0.22), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "keys_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.35), comp_style="pop",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.60,
            )
            mods += [LimitNoteRangeModifier(low=50, high=74), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.42), extension="maj7",
                stab_pattern="syncopated", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=50, high=74), VelocityScalingModifier(scale=0.52),
                     HumanizeModifier(timing_std=0.02, velocity_std=4),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "keys_soft":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.18), comp_style="pop",
                voicing_type="shell", accent_pattern="2_4", chord_density=0.32,
            )
            mods += [LimitNoteRangeModifier(low=50, high=72), VelocityScalingModifier(scale=0.25),
                     CrescendoModifier(start_vel=45, end_vel=22)]

        case "keys_solo":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.40), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.68,
            )
            mods += [LimitNoteRangeModifier(low=48, high=77), VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.025, velocity_std=5)]

        case "synth_bass_hint":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.15), waveform="sine",
                pattern="plucked", slide_probability=0.1, octave_variation=0.05,
            )
            mods += [LimitNoteRangeModifier(low=28, high=48), VelocityScalingModifier(scale=0.30)]

        case "synth_bass":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.42), waveform="saw",
                pattern="plucked", slide_probability=0.25, octave_variation=0.12,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.80),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "bass_slap":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.50), slap_pattern="funky",
                ghost_note_prob=0.38, pop_probability=0.42, octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.85),
                     HumanizeModifier(timing_std=0.015, velocity_std=5),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "bass_walk":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.30), approach_style="diatonic",
                connect_roots=True, add_chromatic_passing=False, swing_eighth_ratio=0.58,
            )
            mods += [LimitNoteRangeModifier(low=28, high=48), VelocityScalingModifier(scale=0.35),
                     CrescendoModifier(start_vel=42, end_vel=22)]

        case "bass_walk_back":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.30), approach_style="mixed",
                connect_roots=True, add_chromatic_passing=True, swing_eighth_ratio=0.60,
            )
            mods += [LimitNoteRangeModifier(low=28, high=48), VelocityScalingModifier(scale=0.55),
                     CrescendoModifier(start_vel=30, end_vel=65),
                     HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "groove":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.45), groove_pattern="soul",
                ghost_note_vel=30, accent_vel=105,
            )
            mods.append(HumanizeModifier(timing_std=0.01, velocity_std=6))

        case "drums":
            gen = ElectronicDrumsGenerator(
                params=GeneratorParams(density=0.48), kit="linn",
                pattern="breakbeat", sidechain=True,
            )
            mods += [HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "hihat_sparp":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.18), pattern="sparse",
                roll_density=0.15, open_hat_probability=0.08, instrument="shaker",
            )
            mods += [VelocityScalingModifier(scale=0.30), HumanizeModifier(timing_std=0.025, velocity_std=3)]

        case "guitar_funk":
            gen = GuitarStrummingGenerator(
                params=GeneratorParams(density=0.45), strum_pattern="funk",
                palm_mute_ratio=0.35, accent_velocity=1.15, dead_strums=True,
                strum_delay=0.012, string_count=6,
            )
            mods += [LimitNoteRangeModifier(low=40, high=67), VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.015, velocity_std=5),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.35), harmony_note_probability=0.72,
                note_range_low=60, note_range_high=79, steps_probability=0.90,
                random_movement=0.80, first_note="any_chord", last_note="last_chord_root",
                after_leap="step_opposite", syncopation=0.35, phrase_length=8.0,
                drama_shape="crescendo", drama_peak=0.50,
                groove_template=LAID_BACK, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=60, high=79), VelocityScalingModifier(scale=0.70),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "melody_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45), harmony_note_probability=0.74,
                note_range_low=62, note_range_high=81, steps_probability=0.88,
                random_movement=0.75, first_note="chord_root", last_note="last_chord_root",
                after_leap="step_opposite", climax="up_5th", penultimate_step_above=True,
                syncopation=0.40, phrase_length=8.0, motif_probability=0.55,
                groove_template=LAID_BACK, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=62, high=81), VelocityScalingModifier(scale=0.82),
                     HumanizeModifier(timing_std=0.02, velocity_std=4),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "brass_stab":
            gen = BrassSectionGenerator(
                params=GeneratorParams(density=0.15), articulation="hit",
                voicing="closed", intensity=0.85, divisi_count=3,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.01, velocity_std=3)]

        case "strings_pad":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.10), section_size="chamber",
                articulation="sustained", divisi=2, dynamic_curve="flat",
            )
            mods.append(VelocityScalingModifier(scale=0.30))

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.35), processing="pitch_shift",
                density=0.40, chop_pattern="syncopated", source_pitch=65,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.03, velocity_std=3),
                     SwingController(swing_ratio=0.61, grid=0.5)]

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.28), motion_preference="mixed",
                dissonance_on_weak=True, interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=65, high=84), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.22), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=48,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 3 — Drip (Trap-Soul / Drop)
# Bb Dorian | 100 BPM | 52 bars
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_3 = Scale(root=10, mode=Mode.DORIAN)

SECTIONS_3 = [
    ("Intro",      4, ["keys_warmup", "bass808_hint", "trap_hint"]),
    ("Hook",       8, ["keys_hook", "bass808_hook", "trap", "melody_hook", "chops"]),
    ("V1",         8, ["keys_comp", "bass808", "trap", "melody"]),
    ("Pre",        4, ["keys_busy", "bass808_hook", "trap_up", "melody_pre", "riser", "filter_close"]),
    ("Hook 2",     8, ["keys_hook", "bass808_hook", "trap", "melody_hook",
                       "counter", "chops", "beat_repeat"]),
    ("V2",         8, ["keys_comp", "bass808", "trap", "melody", "vocal_adlibs"]),
    ("Hook 3",     8, ["keys_hook", "bass808_hook", "trap", "melody_hook",
                       "counter", "chops", "brass_stab", "riser", "filter_open"]),
    ("Outro",      4, ["keys_soft", "bass808_hint", "impact"]),
]

INSTRUMENTS_3 = {
    "keys_warmup": 4, "keys_comp": 4, "keys_busy": 4, "keys_hook": 4, "keys_soft": 4,
    "bass808_hint": 0, "bass808": 0, "bass808_hook": 0,
    "trap_hint": 0, "trap": 0, "trap_up": 0,
    "melody": 82, "melody_hook": 82, "melody_pre": 82,
    "counter": 52, "chops": 54,
    "vocal_adlibs": 85,
    "brass_stab": 62,
    "beat_repeat": 0,
    "riser": 97, "impact": 103,
    "filter_close": 95, "filter_open": 95,
}

PERC_3 = {"bass808_hint", "bass808", "bass808_hook", "trap_hint", "trap", "trap_up", "beat_repeat"}


def build_3(name):
    mods = []
    match name:
        case "keys_warmup":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15), comp_style="pop",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.35,
            )
            mods += [VelocityScalingModifier(scale=0.22), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "keys_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.38), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.60,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "keys_busy":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.52), extension="min7",
                stab_pattern="dense", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.012, velocity_std=4)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.45), extension="maj9",
                stab_pattern="syncopated", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.50),
                     HumanizeModifier(timing_std=0.012, velocity_std=4)]

        case "keys_soft":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15), comp_style="pop",
                voicing_type="shell", accent_pattern="2_4", chord_density=0.30,
            )
            mods += [LimitNoteRangeModifier(low=48, high=72), VelocityScalingModifier(scale=0.22),
                     CrescendoModifier(start_vel=42, end_vel=20)]

        case "bass808_hint":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.15), pattern="trap_basic",
                slide_probability=0.20, octave_range=1, accent_velocity=0.8,
            )
            mods += [LimitNoteRangeModifier(low=24, high=48), VelocityScalingModifier(scale=0.35)]

        case "bass808":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.45), pattern="trap_syncopated",
                slide_probability=0.40, octave_range=2, accent_velocity=1.05,
            )
            mods += [LimitNoteRangeModifier(low=24, high=52), VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.01, velocity_std=4)]

        case "bass808_hook":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.50), pattern="drill_sliding",
                slide_probability=0.45, octave_range=2, accent_velocity=1.12,
            )
            mods += [LimitNoteRangeModifier(low=24, high=52), VelocityScalingModifier(scale=0.85),
                     HumanizeModifier(timing_std=0.008, velocity_std=3)]

        case "trap_hint":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.18), variant="minimal",
                hat_roll_density=0.15, kick_pattern="sparse", open_hat_probability=0.08,
            )
            mods.append(VelocityScalingModifier(scale=0.30))

        case "trap":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.45), variant="drill",
                hat_roll_density=0.55, kick_pattern="syncopated", open_hat_probability=0.22,
            )
            mods.append(HumanizeModifier(timing_std=0.008, velocity_std=4))

        case "trap_up":
            gen = TrapDrumsGenerator(
                params=GeneratorParams(density=0.52), variant="drill",
                hat_roll_density=0.65, kick_pattern="syncopated", open_hat_probability=0.28,
            )
            mods.append(HumanizeModifier(timing_std=0.008, velocity_std=4))

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.40), harmony_note_probability=0.68,
                note_range_low=58, note_range_high=79, steps_probability=0.85,
                random_movement=0.72, first_note="any_chord", last_note="last_chord_root",
                after_leap="step_any", syncopation=0.50, rhythm_variety=0.6,
                phrase_length=8.0, motif_probability=0.4,
                drama_shape="dramatic", drama_peak=0.60,
                groove_template=HIP_HOP, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=58, high=79), VelocityScalingModifier(scale=0.75),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "melody_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.50), harmony_note_probability=0.72,
                note_range_low=60, note_range_high=82, steps_probability=0.86,
                random_movement=0.68, first_note="chord_root", last_note="last_chord_root",
                after_leap="step_opposite", climax="up_5th", penultimate_step_above=True,
                syncopation=0.55, rhythm_variety=0.65, phrase_length=8.0,
                motif_probability=0.6, drama_shape="dramatic", drama_peak=0.72,
                groove_template=HIP_HOP, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=60, high=82), VelocityScalingModifier(scale=0.82),
                     HumanizeModifier(timing_std=0.012, velocity_std=4)]

        case "melody_pre":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45), harmony_note_probability=0.65,
                note_range_low=58, note_range_high=80, steps_probability=0.88,
                random_movement=0.68, first_note="scale", last_note="any",
                after_leap="step_any", syncopation=0.55, phrase_length=4.0,
                drama_shape="crescendo", drama_peak=0.75,
                groove_template=HIP_HOP, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=58, high=80), VelocityScalingModifier(scale=0.72),
                     CrescendoModifier(start_vel=35, end_vel=80),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.32), motion_preference="mixed",
                dissonance_on_weak=True, interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=65, high=84), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.38), processing="pitch_shift",
                density=0.42, chop_pattern="syncopated", source_pitch=65,
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "vocal_adlibs":
            gen = VocalAdlibsGenerator(
                params=GeneratorParams(density=0.25), density_adlib=0.3,
                register="mid", style="adlib", phrase_variety=0.5,
            )
            mods += [LimitNoteRangeModifier(low=55, high=75), VelocityScalingModifier(scale=0.40),
                     HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "brass_stab":
            gen = BrassSectionGenerator(
                params=GeneratorParams(density=0.15), articulation="hit",
                voicing="closed", intensity=0.9, divisi_count=3,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.01, velocity_std=3)]

        case "beat_repeat":
            gen = BeatRepeatGenerator(
                params=GeneratorParams(density=0.20), repeat_type="glitch",
                stutter_length=2.0, min_subdivision=0.0625,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case "filter_close":
            gen = FilterSweepGenerator(
                params=GeneratorParams(density=0.20), sweep_type="lowpass_close",
                resonance=0.6, duration=4.0, curve="exponential",
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case "filter_open":
            gen = FilterSweepGenerator(
                params=GeneratorParams(density=0.20), sweep_type="lowpass_open",
                resonance=0.6, duration=4.0, curve="exponential",
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.28), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=48,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case "impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.28), impact_type="boom",
                tail_length=3.5, pitch_drop=14,
            )
            mods += [VelocityScalingModifier(scale=0.35)]

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 4 — Golden Hour (Gospel-Soul)
# Db Lydian | 78 BPM | 40 bars
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_4 = Scale(root=1, mode=Mode.LYDIAN)

SECTIONS_4 = [
    ("Intro",      4, ["piano_warmup", "organ_soft", "strings_pad", "choir_hum"]),
    ("V1",         8, ["piano_comp", "organ", "bass", "groove", "melody", "strings_swell"]),
    ("Hook",       8, ["piano_hook", "organ_full", "bass_slap_hook", "groove_full",
                       "melody_hook", "counter", "strings_full", "choir_aah"]),
    ("Bridge",     4, ["piano_soft", "organ_soft", "bass_walk", "choir_hum"]),
    ("Hook 2",     8, ["piano_hook", "organ_full", "bass_slap_hook", "groove_full",
                       "melody_hook", "counter", "strings_full", "choir_aah",
                       "riser", "brass_stab"]),
    ("Outro",      4, ["organ_soft", "strings_pad", "choir_hum"]),
]

INSTRUMENTS_4 = {
    "piano_warmup": 1, "piano_comp": 1, "piano_hook": 1, "piano_soft": 1,
    "organ": 16, "organ_soft": 16, "organ_full": 16,
    "bass": 33, "bass_walk": 33, "bass_slap_hook": 33,
    "groove": 0, "groove_full": 0,
    "melody": 56, "melody_hook": 56,
    "counter": 49,
    "strings_pad": 48, "strings_swell": 48, "strings_full": 48,
    "choir_hum": 53, "choir_aah": 52,
    "brass_stab": 62,
    "riser": 97,
}

PERC_4 = {"groove", "groove_full"}


def build_4(name):
    mods = []
    match name:
        case "piano_warmup":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15), comp_style="pop",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.35,
            )
            mods += [VelocityScalingModifier(scale=0.22), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "piano_comp":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.38), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.62,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "piano_hook":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.44), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.70,
            )
            mods += [LimitNoteRangeModifier(low=48, high=76), VelocityScalingModifier(scale=0.55),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "piano_soft":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15), comp_style="pop",
                voicing_type="shell", accent_pattern="2_4", chord_density=0.30,
            )
            mods += [LimitNoteRangeModifier(low=48, high=72), VelocityScalingModifier(scale=0.25),
                     CrescendoModifier(start_vel=42, end_vel=22)]

        case "organ":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.22), registration="gospel",
                leslie_speed="slow", percussion=True, vibrato=False, sustain_bars=1.0,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "organ_soft":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.12), registration="ballad",
                leslie_speed="slow", percussion=False, vibrato=True, sustain_bars=1.5,
            )
            mods.append(VelocityScalingModifier(scale=0.25))

        case "organ_full":
            gen = OrganDrawbarsGenerator(
                params=GeneratorParams(density=0.30), registration="gospel",
                leslie_speed="fast", percussion=True, vibrato=False, sustain_bars=0.8,
            )
            mods.append(VelocityScalingModifier(scale=0.65))

        case "bass":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.42), approach_style="mixed",
                connect_roots=True, add_chromatic_passing=True, swing_eighth_ratio=0.62,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.015, velocity_std=5)]

        case "bass_walk":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.30), approach_style="diatonic",
                connect_roots=True, add_chromatic_passing=False, swing_eighth_ratio=0.58,
            )
            mods += [LimitNoteRangeModifier(low=28, high=48), VelocityScalingModifier(scale=0.45),
                     CrescendoModifier(start_vel=48, end_vel=25)]

        case "bass_slap_hook":
            gen = BassSlapGenerator(
                params=GeneratorParams(density=0.55), slap_pattern="funky",
                ghost_note_prob=0.38, pop_probability=0.45, octave_range=2,
            )
            mods += [LimitNoteRangeModifier(low=28, high=52), VelocityScalingModifier(scale=0.85),
                     HumanizeModifier(timing_std=0.015, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "groove":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.45), groove_pattern="soul",
                ghost_note_vel=30, accent_vel=105,
            )
            mods.append(HumanizeModifier(timing_std=0.01, velocity_std=6))

        case "groove_full":
            gen = GrooveGenerator(
                params=GeneratorParams(density=0.55), groove_pattern="funk_2",
                ghost_note_vel=32, accent_vel=110,
            )
            mods += [HumanizeModifier(timing_std=0.01, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.35), harmony_note_probability=0.74,
                note_range_low=58, note_range_high=79, steps_probability=0.92,
                random_movement=0.80, first_note="any_chord", last_note="last_chord_root",
                after_leap="step_opposite", syncopation=0.30, phrase_length=8.0,
                drama_shape="crescendo", drama_peak=0.55, motif_probability=0.5,
                groove_template=SHUFFLE, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=58, high=79), VelocityScalingModifier(scale=0.75),
                     HumanizeModifier(timing_std=0.02, velocity_std=5),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "melody_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45), harmony_note_probability=0.76,
                note_range_low=60, note_range_high=82, steps_probability=0.90,
                random_movement=0.75, first_note="chord_root", last_note="last_chord_root",
                after_leap="step_opposite", climax="up_5th", penultimate_step_above=True,
                syncopation=0.35, phrase_length=8.0, motif_probability=0.65,
                drama_shape="dramatic", drama_peak=0.65,
                groove_template=SHUFFLE, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=60, high=82), VelocityScalingModifier(scale=0.82),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "counter":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.28), motion_preference="mixed",
                dissonance_on_weak=True, interval_limit=7,
            )
            mods += [LimitNoteRangeModifier(low=65, high=84), VelocityScalingModifier(scale=0.42),
                     HumanizeModifier(timing_std=0.025, velocity_std=4),
                     SwingController(swing_ratio=0.58, grid=0.5)]

        case "strings_pad":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.10), section_size="chamber",
                articulation="sustained", divisi=2, dynamic_curve="flat",
            )
            mods.append(VelocityScalingModifier(scale=0.30))

        case "strings_swell":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.15), section_size="chamber",
                articulation="sustained", divisi=3, dynamic_curve="swell",
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.02, velocity_std=3)]

        case "strings_full":
            gen = StringsEnsembleGenerator(
                params=GeneratorParams(density=0.20), section_size="full",
                articulation="sustained", divisi=4, dynamic_curve="crescendo",
            )
            mods += [VelocityScalingModifier(scale=0.42), HumanizeModifier(timing_std=0.015, velocity_std=3)]

        case "choir_hum":
            gen = ChoirAahsGenerator(
                params=GeneratorParams(density=0.08), voice_count=4,
                dynamics="pp", vibrato=0.2, syllable="mm",
            )
            mods.append(VelocityScalingModifier(scale=0.30))

        case "choir_aah":
            gen = ChoirAahsGenerator(
                params=GeneratorParams(density=0.18), voice_count=6,
                dynamics="mf", vibrato=0.3, syllable="aah",
            )
            mods += [VelocityScalingModifier(scale=0.45), HumanizeModifier(timing_std=0.02, velocity_std=4)]

        case "brass_stab":
            gen = BrassSectionGenerator(
                params=GeneratorParams(density=0.15), articulation="hit",
                voicing="closed", intensity=0.9, divisi_count=3,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.01, velocity_std=3)]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.22), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=48,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# TRACK 5 — After Hours (Bedroom R&B / Lo-Fi)
# F Minor | 70 BPM | 36 bars
# ═══════════════════════════════════════════════════════════════════════════════

SCALE_5 = Scale(root=5, mode=Mode.NATURAL_MINOR)

SECTIONS_5 = [
    ("Intro",      4, ["pad_ambient", "keys_warmup", "synth_bass_hint"]),
    ("V1",         8, ["keys_comp", "synth_bass", "lofi_drums", "melody"]),
    ("Hook",       8, ["keys_hook", "synth_bass", "lofi_drums", "melody_hook",
                       "vocal_oohs", "arp_quiet"]),
    ("Break",      4, ["keys_solo"]),
    ("Hook 2",     8, ["keys_hook", "synth_bass", "lofi_drums", "melody_hook",
                       "vocal_oohs", "arp_quiet", "riser"]),
    ("Outro",      4, ["pad_ambient", "bass_walk", "vocal_oohs_soft"]),
]

INSTRUMENTS_5 = {
    "pad_ambient": 98,
    "keys_warmup": 4, "keys_comp": 4, "keys_hook": 4, "keys_solo": 4,
    "synth_bass_hint": 38, "synth_bass": 38,
    "bass_walk": 33,
    "lofi_drums": 0,
    "melody": 82, "melody_hook": 82,
    "vocal_oohs": 54, "vocal_oohs_soft": 54,
    "arp_quiet": 88,
    "riser": 97,
}

PERC_5 = {"lofi_drums"}


def build_5(name):
    mods = []
    match name:
        case "pad_ambient":
            gen = AmbientPadGenerator(
                params=GeneratorParams(density=0.06), voicing="spread",
                note_range_low=36, note_range_high=60,
            )
            mods += [VelocityScalingModifier(scale=0.25), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "keys_warmup":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.15), comp_style="pop",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.35,
            )
            mods += [VelocityScalingModifier(scale=0.22), HumanizeModifier(timing_std=0.04, velocity_std=3)]

        case "keys_comp":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.40), extension="min9",
                stab_pattern="syncopated", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=50, high=74), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.02, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.25)]

        case "keys_hook":
            gen = ModernChordPatternGenerator(
                params=GeneratorParams(density=0.48), extension="min9",
                stab_pattern="syncopated", voicing="open",
            )
            mods += [LimitNoteRangeModifier(low=50, high=76), VelocityScalingModifier(scale=0.52),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.25)]

        case "keys_solo":
            gen = PianoCompGenerator(
                params=GeneratorParams(density=0.45), comp_style="jazz",
                voicing_type="rootless", accent_pattern="syncopated", chord_density=0.72,
            )
            mods += [LimitNoteRangeModifier(low=46, high=79), VelocityScalingModifier(scale=0.48),
                     HumanizeModifier(timing_std=0.025, velocity_std=6),
                     SwingController(swing_ratio=0.55, grid=0.5)]

        case "synth_bass_hint":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.15), waveform="sine",
                pattern="plucked", slide_probability=0.05, octave_variation=0.0,
            )
            mods += [LimitNoteRangeModifier(low=28, high=46), VelocityScalingModifier(scale=0.30)]

        case "synth_bass":
            gen = SynthBassGenerator(
                params=GeneratorParams(density=0.45), waveform="square",
                pattern="plucked", slide_probability=0.15, octave_variation=0.08,
            )
            mods += [LimitNoteRangeModifier(low=28, high=48), VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.015, velocity_std=5),
                     SwingController(swing_ratio=0.55, grid=0.25)]

        case "bass_walk":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.25), approach_style="diatonic",
                connect_roots=True, add_chromatic_passing=False, swing_eighth_ratio=0.55,
            )
            mods += [LimitNoteRangeModifier(low=28, high=46), VelocityScalingModifier(scale=0.35),
                     CrescendoModifier(start_vel=45, end_vel=22)]

        case "lofi_drums":
            gen = LoFiHipHopGenerator(
                params=GeneratorParams(density=0.50), variant="chill",
                swing_ratio=0.55, chord_voicing="ninth",
                include_drums=True, include_bass=False,
                vinyl_noise=0.3, tape_stop=0.1,
            )
            mods += [HumanizeModifier(timing_std=0.015, velocity_std=4)]

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.35), harmony_note_probability=0.72,
                note_range_low=60, note_range_high=78, steps_probability=0.92,
                random_movement=0.82, first_note="any_chord", last_note="last_chord_root",
                after_leap="step_opposite", syncopation=0.32, phrase_length=8.0,
                drama_shape="crescendo", drama_peak=0.55, motif_probability=0.55,
                groove_template=PUSH, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=60, high=78), VelocityScalingModifier(scale=0.68),
                     HumanizeModifier(timing_std=0.02, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.25)]

        case "melody_hook":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45), harmony_note_probability=0.75,
                note_range_low=62, note_range_high=80, steps_probability=0.90,
                random_movement=0.76, first_note="chord_root", last_note="last_chord_root",
                after_leap="step_opposite", climax="up_5th", penultimate_step_above=True,
                syncopation=0.38, phrase_length=8.0, motif_probability=0.65,
                drama_shape="crescendo", drama_peak=0.65,
                groove_template=PUSH, beats_per_bar=4, denominator=4,
            )
            mods += [LimitNoteRangeModifier(low=62, high=80), VelocityScalingModifier(scale=0.78),
                     HumanizeModifier(timing_std=0.015, velocity_std=4),
                     SwingController(swing_ratio=0.55, grid=0.25)]

        case "vocal_oohs":
            gen = VocalOohsGenerator(
                params=GeneratorParams(density=0.15), syllable="ooh",
                harmony_count=3, vibrato=0.4, breath_phasing=True,
            )
            mods += [LimitNoteRangeModifier(low=55, high=72), VelocityScalingModifier(scale=0.45),
                     HumanizeModifier(timing_std=0.03, velocity_std=3)]

        case "vocal_oohs_soft":
            gen = VocalOohsGenerator(
                params=GeneratorParams(density=0.10), syllable="ooh",
                harmony_count=3, vibrato=0.35, breath_phasing=True,
            )
            mods += [LimitNoteRangeModifier(low=55, high=72), VelocityScalingModifier(scale=0.30),
                     CrescendoModifier(start_vel=42, end_vel=20)]

        case "arp_quiet":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.20), pattern="up_down",
                note_duration=0.35, voicing="open", octaves=2,
            )
            mods += [VelocityScalingModifier(scale=0.35), HumanizeModifier(timing_std=0.025, velocity_std=3),
                     SwingController(swing_ratio=0.55, grid=0.25)]

        case "riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.22), riser_type="synth",
                length_beats=4.0, pitch_curve="exponential", peak_velocity=48,
            )
            mods += [VelocityScalingModifier(scale=0.30)]

        case _:
            return None

    return gen, mods


# ═══════════════════════════════════════════════════════════════════════════════
# Album Production
# ═══════════════════════════════════════════════════════════════════════════════

TRACKS = [
    {
        "title": "01_Midnight_Velvet",
        "scale": SCALE_1, "sections": SECTIONS_1, "build": build_1,
        "instruments": INSTRUMENTS_1, "bpm": 75, "mood": Mood.INTIMATE,
        "perc": PERC_1, "key_label": "Ebm",
    },
    {
        "title": "02_Silk_And_Smoke",
        "scale": SCALE_2, "sections": SECTIONS_2, "build": build_2,
        "instruments": INSTRUMENTS_2, "bpm": 92, "mood": Mood.CINEMATIC,
        "perc": PERC_2, "key_label": "Gb",
    },
    {
        "title": "03_Drip",
        "scale": SCALE_3, "sections": SECTIONS_3, "build": build_3,
        "instruments": INSTRUMENTS_3, "bpm": 100, "mood": Mood.CINEMATIC,
        "perc": PERC_3, "key_label": "Bbm",
    },
    {
        "title": "04_Golden_Hour",
        "scale": SCALE_4, "sections": SECTIONS_4, "build": build_4,
        "instruments": INSTRUMENTS_4, "bpm": 78, "mood": Mood.INTIMATE,
        "perc": PERC_4, "key_label": "Db",
    },
    {
        "title": "05_After_Hours",
        "scale": SCALE_5, "sections": SECTIONS_5, "build": build_5,
        "instruments": INSTRUMENTS_5, "bpm": 70, "mood": Mood.AMBIENT,
        "perc": PERC_5, "key_label": "Fm",
    },
]


def main():
    album_dir = Path("output/album_velvet_nights")
    album_dir.mkdir(exist_ok=True, parents=True)

    print("\n" + "=" * 60)
    print("   VELVET NIGHTS — R&B Beats Album")
    print("   5 Cuts | Neo-Soul · New Jack Swing · Trap-Soul · Gospel-Soul · Lo-Fi")
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
    print("   PRODUCTION COMPLETE: VELVET NIGHTS")
    print(f"   Location: {album_dir}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
