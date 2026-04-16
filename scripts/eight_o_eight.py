
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
eight_o_eight.py — Tight 808 beat with arrangement.

Structure:
  Intro (4 bars) -> Verse 1 (8) -> Hook (8) -> Verse 2 (8) -> Hook 2 (8) -> Outro (4)

Core: sliding 808 + trap drums + hat rolls + cowbell + dark pad + lead.
Sections layer/unlayer tracks for arrangement dynamics.
"""

import sys
import random
import warnings
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    GeneratorParams,
)
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
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    LimitNoteRangeModifier,
    SwingController,
    ModifierContext,
)
from melodica.composer import ArticulationEngine
from melodica.midi import export_multitrack_midi
from melodica.render_context import RenderContext


# -- sections: name, bars, active tracks -----------------------------------------

INTRO = [
    (4, ["dark_pad", "cowbell_spare"]),
]

VERSE_1 = [
    (8, ["bass_808", "trap_drums", "hihat", "dark_pad", "lead_spare"]),
]

HOOK = [
    (8, ["bass_808_slide", "trap_drums_hard", "hihat_rapid", "cowbell_full", "dark_pad", "lead", "ghost_snare"]),
]

VERSE_2 = [
    (8, ["bass_808", "trap_drums", "hihat", "dark_pad", "vocal_chops", "ghost_snare"]),
]

HOOK_2 = [
    (8, ["bass_808_slide", "trap_drums_hard", "hihat_rapid", "cowbell_full", "dark_pad", "lead", "ghost_snare", "fx_riser"]),
]

OUTRO = [
    (4, ["dark_pad", "bass_808_half", "fx_impact"]),
]


# -- scale / harmony --------------------------------------------------------------

SCALE = Scale(root=2, mode=Mode.PHRYGIAN)  # D Phrygian


def harmonize_section(bars, beats_per_bar=4):
    harmonizer = HMM3Harmonizer(
        beam_width=5,
        melody_weight=0.25,
        secondary_dom_weight=0.10,
        extension_weight=0.06,
        repetition_penalty=0.08,
        cadence_weight=0.12,
    )
    degs = SCALE.degrees()
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
        contour.append(
            NoteInfo(pitch=44 + pc, start=bar * beats_per_bar, duration=beats_per_bar - 0.1, velocity=55)
        )
    s_beats = bars * beats_per_bar
    chords = harmonizer.harmonize(contour, SCALE, s_beats)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(root=int(degs[0]), quality=Quality.MINOR, start=len(chords) * beats_per_bar, duration=beats_per_bar)
        )
    return chords


# -- track builders ---------------------------------------------------------------

def build_track(name, density=0.5):
    params = GeneratorParams(density=density)
    mods = []

    match name:
        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.45,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "bass_808_slide":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="drill_sliding",
                slide_type="chromatic",
                slide_probability=0.65,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.95))

        case "bass_808_half":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.25,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "trap_drums":
            gen = TrapDrumsGenerator(
                params=params,
                variant="standard",
                hat_roll_density=0.4,
                kick_pattern="standard",
            )

        case "trap_drums_hard":
            gen = TrapDrumsGenerator(
                params=params,
                variant="drill",
                hat_roll_density=0.6,
                kick_pattern="syncopated",
            )

        case "hihat":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.30,
                open_hat_probability=0.10,
            )
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))

        case "hihat_rapid":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="drill_stutter",
                roll_density=0.55,
                open_hat_probability=0.06,
            )
            mods.append(SwingController(swing_ratio=0.57, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "cowbell_spare":
            gen = PhonkGenerator(
                params=GeneratorParams(density=0.15),
                variant="lofi_phonk",
                cowbell_density=0.30,
                bass_slide_amount=0,
                memphis_chops=False,
                aggression=0.15,
            )
            mods.append(VelocityScalingModifier(scale=0.35))

        case "cowbell_full":
            gen = PhonkGenerator(
                params=GeneratorParams(density=0.6),
                variant="classic_phonk",
                cowbell_density=0.75,
                bass_slide_amount=4,
                memphis_chops=True,
                aggression=0.55,
            )
            mods.append(VelocityScalingModifier(scale=0.75))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.3),
                mode="phrygian_pad",
                chord_dur=8.0,
                velocity_level=0.12,
                register="low",
                overlap=0.5,
            )

        case "lead":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.5),
                style="supersaw",
                portamento=0.20,
                note_length="mixed",
            )
            mods.append(LimitNoteRangeModifier(low=57, high=79))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=5))
            mods.append(VelocityScalingModifier(scale=0.60))

        case "lead_spare":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.25),
                style="retro",
                portamento=0.10,
                note_length="legato",
            )
            mods.append(LimitNoteRangeModifier(low=60, high=76))
            mods.append(VelocityScalingModifier(scale=0.35))
            mods.append(HumanizeModifier(timing_std=0.04, velocity_std=3))

        case "vocal_chops":
            gen = VocalChopsGenerator(
                params=GeneratorParams(density=0.5),
                processing="pitch_shift",
                density=0.55,
                chop_pattern="syncopated",
                source_pitch=62,
            )
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5))
            mods.append(VelocityScalingModifier(scale=0.50))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.3),
                target="snare",
                pattern="hiphop",
                ghost_velocity=32,
                ghost_density=0.50,
                placement="sixteenth",
            )

        case "fx_riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.4),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=105,
            )

        case "fx_impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.3),
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=15,
            )

        case _:
            return None, []

    return gen, mods


# -- instruments ------------------------------------------------------------------

INSTRUMENTS = {
    "bass_808": 38,         # Synth Bass 1
    "bass_808_slide": 38,   # Synth Bass 1
    "bass_808_half": 38,    # Synth Bass 1
    "trap_drums": 0,
    "trap_drums_hard": 0,
    "hihat": 0,
    "hihat_rapid": 0,
    "cowbell_spare": 0,
    "cowbell_full": 0,
    "dark_pad": 92,         # Halo Pad
    "lead": 81,             # Sawtooth Lead
    "lead_spare": 81,
    "vocal_chops": 54,      # Synth Voice
    "ghost_snare": 0,
    "fx_riser": 97,         # FX 1 Rain
    "fx_impact": 103,       # FX 4 Atmosphere
}

PERC_TRACKS = {
    "trap_drums", "trap_drums_hard", "hihat", "hihat_rapid",
    "cowbell_spare", "cowbell_full", "ghost_snare",
}


# -- generate ---------------------------------------------------------------------

def generate(tempo, seed):
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    song = INTRO + VERSE_1 + HOOK + VERSE_2 + HOOK_2 + OUTRO

    tracks: dict[str, list[NoteInfo]] = {}
    beat_offset = 0.0
    track_contexts: dict[str, RenderContext] = {}
    art_engine = ArticulationEngine()

    section_names = ["Intro", "Verse 1", "Hook", "Verse 2", "Hook 2", "Outro"]
    sec_idx = 0

    for sec_bars, sec_tracks in song:
        sec_name = section_names[sec_idx] if sec_idx < len(section_names) else "?"
        s_beats = sec_bars * beats_per_bar
        chords = harmonize_section(sec_bars, beats_per_bar)

        # shift chords to absolute position
        abs_chords = [
            ChordLabel(root=c.root, quality=c.quality, start=round(c.start + beat_offset, 6),
                       duration=c.duration, degree=c.degree)
            for c in chords
        ]

        print(f"  [{sec_name:9s}] {sec_bars} bars, tracks: {', '.join(sec_tracks)}")

        for track_name in sec_tracks:
            gen, mods = build_track(track_name)
            if gen is None:
                continue

            prev_ctx = track_contexts.get(track_name)
            ctx = RenderContext(
                prev_pitch=prev_ctx.prev_pitch if prev_ctx else None,
                prev_velocity=prev_ctx.prev_velocity if prev_ctx else None,
                prev_chord=prev_ctx.prev_chord if prev_ctx else None,
                prev_pitches=list(prev_ctx.prev_pitches) if prev_ctx else [],
                current_scale=SCALE,
            )

            notes = gen.render(chords, SCALE, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                track_contexts[track_name] = gen._last_context

            mctx = ModifierContext(duration_beats=s_beats, chords=chords, timeline=None, scale=SCALE)
            for m in mods:
                try:
                    notes = m.modify(notes, mctx)
                except Exception:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)  # noqa: S110

            if track_name not in tracks:
                tracks[track_name] = []
            for n in notes:
                tracks[track_name].append(
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
        sec_idx += 1

    for k in tracks:
        tracks[k] = sorted(tracks[k], key=lambda n: n.start)

    pedal_cc = {}
    for tn in list(tracks.keys()):
        if tn not in PERC_TRACKS:
            tracks[tn] = art_engine.apply(tracks[tn], tn, beat_offset)
            raw = art_engine.add_sustain_pedal_events(tracks[tn], beat_offset)
            if raw:
                pedal_cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, pedal_cc


def main():
    p = argparse.ArgumentParser(description="808 beat — tight arrangement")
    p.add_argument("--tempo", type=int, default=75)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="eight_o_eight.mid")
    args = p.parse_args()

    total_bars = 4 + 8 + 8 + 8 + 8 + 4  # 40 bars
    actual_min = total_bars * 4 / args.tempo * 60

    print(f"808 Beat")
    print(f"  {actual_min:.1f} min ({total_bars} bars @ {args.tempo} BPM)")
    print(f"  D Phrygian")
    print()

    tracks, pedal_cc = generate(args.tempo, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"\n  Tracks: {len(tracks)}, Notes: {total}")
    for name, notes in sorted(tracks.items()):
        print(f"    {name:20s}: {len(notes):5d} notes")

    export_multitrack_midi(
        tracks,
        args.output,
        bpm=args.tempo,
        key="Dm",
        cc_events=pedal_cc,
        instruments=INSTRUMENTS,
    )
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
