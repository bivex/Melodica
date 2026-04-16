
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
ug_phonk.py — Underground phonk with dramatic arc and HMM3.

8-act arc:
  Dirt -> Smoke -> Teeth -> Grind -> Heat -> Warp -> Ash -> Void

Underground phonk DNA:
  - Cowbell-driven Memphis patterns (drift & classic)
  - Sliding 808 sub-bass
  - Trap drums with hat rolls
  - Dark pads (phrygian, tritone drone)
  - Vocal chops (Memphis pitched)
  - FX risers/impacts at transitions
  - Lead synth for hook lines

Scale choices:
  Phrygian dominant, Hungarian minor, natural minor — dark, Eastern color.
  Key changes pivot through shared chord tones.
"""

import sys
import random
import warnings
import argparse
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    MarkovMelodyGenerator,
    ArpeggiatorGenerator,
    ChordGenerator,
    RiffGenerator,
    CountermelodyGenerator,
    GeneratorParams,
)
from melodica.generators.phonk import PhonkGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.vocal_chops import VocalChopsGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    LimitNoteRangeModifier,
    SwingController,
    ModifierContext,
)
from melodica.composer import NonChordToneGenerator, ArticulationEngine
from melodica.midi import export_multitrack_midi, GM_INSTRUMENTS
from melodica.render_context import RenderContext


SCALES = {
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "phrygian_dom": Scale(root=0, mode=Mode.BYZANTINE),  # Phrygian dominant
    "hungarian": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "dorian": Scale(root=0, mode=Mode.DORIAN),
}


@dataclass
class Section:
    name: str
    bars: int
    scale_name: str
    key_root: int
    mood: str
    density: float
    tracks: list[str]


def build_sections(total_bars: int) -> list[Section]:
    template = [
        # Act 1: intro — sparse, foggy, cowbell whispers
        (
            "Dirt",
            0.08,
            "phrygian",
            0,
            "dirt",
            0.15,
            ["dark_pad", "bass_808", "vocal_chops", "cowbell_spare"],
        ),
        # Act 2: groove emerges — Memphis chops, sliding 808
        (
            "Smoke",
            0.10,
            "phrygian_dom",
            0,
            "smoke",
            0.30,
            ["phonk", "bass_808", "dark_pad", "vocal_chops", "hihat", "lead"],
        ),
        # Act 3: energy rise — full trap drums, cowbell heavy
        (
            "Teeth",
            0.14,
            "hungarian",
            0,
            "teeth",
            0.50,
            ["phonk", "bass_808", "trap_drums", "hihat", "dark_pad", "lead", "vocal_chops"],
        ),
        # Act 4: peak 1 — aggressive, dense, drift phonk mode
        (
            "Grind",
            0.16,
            "harmonic_minor",
            3,
            "grind",
            0.70,
            [
                "phonk_drift",
                "bass_808_slide",
                "trap_drums",
                "hihat_rapid",
                "lead",
                "riff",
                "dark_pad",
                "vocal_chops",
            ],
        ),
        # Act 5: breakdown — strip back, atmospheric
        (
            "Heat",
            0.10,
            "dorian",
            5,
            "heat",
            0.25,
            ["dark_pad", "bass_808_half", "vocal_chops", "cowbell_spare", "lead"],
        ),
        # Act 6: rebuild — riser into second peak, warped
        (
            "Warp",
            0.14,
            "phrygian_dom",
            0,
            "warp",
            0.55,
            [
                "phonk",
                "bass_808",
                "trap_drums",
                "hihat",
                "lead",
                "dark_pad",
                "fx_riser",
            ],
        ),
        # Act 7: groove dissolves — sparse, drifting
        (
            "Ash",
            0.14,
            "natural_minor",
            7,
            "ash",
            0.25,
            ["bass_808_half", "dark_pad", "vocal_chops", "cowbell_spare"],
        ),
        # Act 8: outro — fade to void
        (
            "Void",
            0.14,
            "phrygian",
            0,
            "void",
            0.08,
            ["dark_pad", "fx_impact"],
        ),
    ]

    raw = [max(1, round(total_bars * r)) for _, r, *_ in template]
    raw[-1] += total_bars - sum(raw)
    raw[-1] = max(1, raw[-1])
    return [
        Section(n, raw[i], sn, kr, m, d, t)
        for i, (n, _, sn, kr, m, d, t) in enumerate(template)
    ]


def make_pipeline(track: str, mood: str, density: float, scale: Scale):
    params = GeneratorParams(density=density)
    mods: list = []

    match track:
        case "phonk":
            gen = PhonkGenerator(
                params=params,
                variant="classic_phonk",
                cowbell_density=0.7,
                bass_slide_amount=5,
                memphis_chops=True,
                aggression=0.6,
            )
            mods.append(VelocityScalingModifier(scale=0.85))

        case "phonk_drift":
            gen = PhonkGenerator(
                params=params,
                variant="drift_phonk",
                cowbell_density=0.9,
                bass_slide_amount=7,
                memphis_chops=True,
                aggression=0.8,
            )
            mods.append(VelocityScalingModifier(scale=0.90))
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))

        case "cowbell_spare":
            gen = PhonkGenerator(
                params=params,
                variant="lofi_phonk",
                cowbell_density=0.35,
                bass_slide_amount=0,
                memphis_chops=False,
                aggression=0.2,
            )
            mods.append(VelocityScalingModifier(scale=0.40))
            mods.append(CrescendoModifier(
                start_vel=70 if mood == "dirt" else 50,
                end_vel=30 if mood == "dirt" else 20,
            ))

        case "bass_808":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="trap_basic",
                slide_type="overlap",
                slide_probability=0.5,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "bass_808_slide":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="drill_sliding",
                slide_type="chromatic",
                slide_probability=0.7,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.95))

        case "bass_808_half":
            gen = Bass808SlidingGenerator(
                params=params,
                pattern="half_time",
                slide_type="overlap",
                slide_probability=0.3,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))
            mods.append(VelocityScalingModifier(scale=0.70))
            if mood in ("heat", "void"):
                mods.append(CrescendoModifier(start_vel=80, end_vel=35))

        case "trap_drums":
            variant = "standard" if mood in ("teeth", "ash") else "drill"
            gen = TrapDrumsGenerator(
                params=params,
                variant=variant,
                hat_roll_density=0.6 if mood == "grind" else 0.4,
                kick_pattern="syncopated" if mood == "warp" else "standard",
            )

        case "hihat":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="trap_eighth",
                roll_density=0.35,
                open_hat_probability=0.12,
            )
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))

        case "hihat_rapid":
            gen = HiHatStutterGenerator(
                params=params,
                pattern="drill_stutter",
                roll_density=0.6,
                open_hat_probability=0.08,
                stutter_lengths=[3, 5, 7],
            )
            mods.append(SwingController(swing_ratio=0.58, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "dark_pad":
            mode = "tritone_drone" if mood in ("grind", "warp") else "phrygian_pad"
            gen = DarkPadGenerator(
                params=params,
                mode=mode,
                chord_dur=8.0,
                velocity_level=0.15,
                register="low",
                overlap=0.5,
            )
            if mood in ("void", "dirt"):
                mods.append(CrescendoModifier(start_vel=50, end_vel=20))

        case "vocal_chops":
            gen = VocalChopsGenerator(
                params=params,
                processing="pitch_shift" if mood in ("smoke", "heat") else "stutter",
                density=0.4 if mood in ("dirt", "void") else 0.6,
                chop_pattern="syncopated",
                source_pitch=62,
            )
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5))
            mods.append(VelocityScalingModifier(scale=0.55))

        case "lead":
            gen = LeadSynthGenerator(
                params=params,
                style="retro" if mood in ("smoke", "heat") else "supersaw",
                note_length="mixed",
            )
            mods.append(LimitNoteRangeModifier(low=55, high=80))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=6))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "riff":
            gen = RiffGenerator(
                params=params,
                scale_type="blues",
                riff_pattern="gallop",
                palm_mute_prob=0.4,
                power_chord=True,
            )
            mods.append(VelocityScalingModifier(scale=0.70))
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))

        case "fx_riser":
            gen = FXRiserGenerator(
                params=params,
                riser_type="sub_drop",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=120,
            )

        case "fx_impact":
            gen = FXImpactGenerator(
                params=params,
                impact_type="boom",
                tail_length=3.0,
                pitch_drop=18,
            )

        case _:
            gen = DarkPadGenerator(params=params)

    return gen, None, mods


def pick_harmonizer(mood: str):
    match mood:
        case "dirt" | "void":
            return HMM3Harmonizer(
                beam_width=3,
                melody_weight=0.25,
                cadence_weight=0.08,
                repetition_penalty=0.02,
                secondary_dom_weight=0.03,
            )
        case "smoke":
            return HMM3Harmonizer(
                beam_width=4,
                melody_weight=0.25,
                secondary_dom_weight=0.08,
                extension_weight=0.05,
                repetition_penalty=0.06,
                cadence_weight=0.10,
            )
        case "teeth" | "ash":
            return HMM3Harmonizer(
                beam_width=5,
                melody_weight=0.22,
                secondary_dom_weight=0.12,
                extension_weight=0.07,
                repetition_penalty=0.08,
                cadence_weight=0.12,
            )
        case "grind" | "warp":
            return HMM3Harmonizer(
                beam_width=6,
                melody_weight=0.20,
                secondary_dom_weight=0.15,
                extension_weight=0.10,
                repetition_penalty=0.10,
                cadence_weight=0.14,
            )
        case "heat":
            return HMM3Harmonizer(
                beam_width=4,
                melody_weight=0.30,
                cadence_weight=0.15,
                repetition_penalty=0.05,
            )
        case _:
            return HMM3Harmonizer(beam_width=5, cadence_weight=0.12)


def _build_melody_contour(scale, bars, beats_per_bar, density):
    degs = scale.degrees()
    if not degs:
        return [NoteInfo(pitch=52, start=0.0, duration=4.0, velocity=60)]

    notes = []
    n = len(degs)

    for bar in range(bars):
        pos = bar % 4
        # Phonk tends to sit on roots and fifths with occasional color tones
        if pos == 0:
            pc = int(degs[0])
        elif pos == 1:
            pc = int(degs[min(2, n - 1)])
        elif pos == 2:
            pc = int(degs[min(4, n - 1)] if n > 4 else degs[0])
        else:
            pc = int(degs[0]) if random.random() < 0.5 else int(degs[min(3, n - 1)])

        pitch = max(36, min(68, 44 + pc))
        dur = max(0.5, beats_per_bar - 0.1)
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(bar * beats_per_bar, 6),
                duration=round(dur, 6),
                velocity=55,
            )
        )

    return notes


PHONK_INSTRUMENTS = {
    "phonk": 0,           # Channel 10 drums
    "phonk_drift": 0,     # Channel 10 drums
    "cowbell_spare": 0,   # Channel 10 drums
    "bass_808": 38,       # Synth Bass 1
    "bass_808_slide": 38, # Synth Bass 1
    "bass_808_half": 38,  # Synth Bass 1
    "trap_drums": 0,      # Channel 10 drums
    "hihat": 0,           # Channel 10 drums
    "hihat_rapid": 0,     # Channel 10 drums
    "dark_pad": 92,       # Halo Pad
    "vocal_chops": 54,    # Synth Voice
    "lead": 81,           # Sawtooth Lead
    "riff": 30,           # Overdriven Guitar
    "fx_riser": 97,       # FX 1 Rain
    "fx_impact": 103,     # FX 4 Atmosphere
}

# Tracks that use percussion channel (GM channel 10)
PERC_TRACKS = {"phonk", "phonk_drift", "cowbell_spare", "trap_drums", "hihat", "hihat_rapid"}


def generate(duration_minutes, tempo, key_root, seed):
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    total_beats = duration_minutes * 60 * (tempo / 60)
    total_bars = max(8, int(round(total_beats / beats_per_bar)))
    sections = build_sections(total_bars)

    tracks: dict[str, list[NoteInfo]] = {}
    all_chords: list[ChordLabel] = []
    beat_offset = 0.0

    nct = NonChordToneGenerator(passing_prob=0.08, neighbor_prob=0.04)
    art_engine = ArticulationEngine()
    track_contexts = {}
    prev_scale = None
    prev_last_chord = None

    for si, sec in enumerate(sections):
        s_beats = sec.bars * beats_per_bar
        base = SCALES[sec.scale_name]
        scale = Scale(root=(sec.key_root + key_root) % 12, mode=base.mode)

        if prev_scale is not None and scale != prev_scale:
            rn = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
            print(
                f"  ♩ {rn[prev_scale.root]} {prev_scale.mode.name} → {rn[scale.root]} {scale.mode.name}  [{sec.name}]"
            )
        prev_scale = scale

        harmonizer = pick_harmonizer(sec.mood)
        contour = _build_melody_contour(scale, sec.bars, beats_per_bar, sec.density)
        if prev_last_chord is not None:
            pivot = NoteInfo(pitch=prev_last_chord.root + 44, start=-2.0, duration=2.0, velocity=40)
            contour = [pivot] + contour

        local_chords = harmonizer.harmonize(contour, scale, s_beats)
        local_chords = [c for c in local_chords if c.start >= 0]

        while len(local_chords) < sec.bars:
            local_chords.append(
                local_chords[-1]
                if local_chords
                else ChordLabel(
                    root=int(scale.degrees()[0]) if scale.degrees() else 0,
                    quality=Quality.MINOR,
                    start=len(local_chords) * beats_per_bar,
                    duration=beats_per_bar,
                )
            )

        for c in local_chords:
            all_chords.append(
                ChordLabel(
                    root=c.root,
                    quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration,
                    degree=c.degree,
                )
            )

        if local_chords:
            prev_last_chord = local_chords[-1]

        phrase_pos = si / max(1, len(sections) - 1)

        for track_name in sec.tracks:
            gen, _, mods = make_pipeline(track_name, sec.mood, sec.density, scale)

            prev_ctx = track_contexts.get(track_name)
            ctx = RenderContext(
                prev_pitch=prev_ctx.prev_pitch if prev_ctx else None,
                prev_velocity=prev_ctx.prev_velocity if prev_ctx else None,
                prev_chord=prev_ctx.prev_chord if prev_ctx else None,
                prev_pitches=list(prev_ctx.prev_pitches) if prev_ctx else [],
                phrase_position=phrase_pos,
                current_scale=scale,
            )

            notes = gen.render(local_chords, scale, s_beats, ctx)
            if hasattr(gen, "_last_context") and gen._last_context is not None:
                track_contexts[track_name] = gen._last_context

            mctx = ModifierContext(
                duration_beats=s_beats, chords=local_chords, timeline=None, scale=scale
            )
            for m in mods:
                try:
                    notes = m.modify(notes, mctx)
                except Exception:
                    warnings.warn(f"Modifier error: {e}", stacklevel=2)  # noqa: S110

            if track_name in ("lead", "riff", "vocal_chops"):
                try:
                    notes = nct.add_non_chord_tones(notes, local_chords, scale)
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

    for k in tracks:
        tracks[k] = sorted(tracks[k], key=lambda n: n.start)

    pedal_cc = {}
    for tn in list(tracks.keys()):
        inst = PHONK_INSTRUMENTS.get(tn, 89)
        tracks[tn] = art_engine.apply(tracks[tn], tn, beat_offset)
        # Skip sustain pedal for percussion tracks
        if tn not in PERC_TRACKS:
            raw = art_engine.add_sustain_pedal_events(tracks[tn], beat_offset)
            if raw:
                pedal_cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, pedal_cc


def main():
    p = argparse.ArgumentParser(description="UG Phonk — underground phonk arc")
    p.add_argument("--duration", type=float, default=4.0)
    p.add_argument("--tempo", type=int, default=75)
    p.add_argument("--key", type=int, default=2)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="ug_phonk.mid")
    args = p.parse_args()

    duration = max(1.0, min(20.0, args.duration))
    bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual = bars * 4 / args.tempo * 60
    rn = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_name = rn[args.key]

    print(f"UG Phonk — underground phonk arc")
    print(f"  {duration:.1f} min -> {actual / 60:.1f} min actual ({bars} bars @ {args.tempo} BPM)")
    print(f"  Key: {key_name}m")
    print()

    tracks, pedal_cc = generate(duration, args.tempo, args.key, args.seed)

    total = sum(len(n) for n in tracks.values())
    print(f"  Tracks: {len(tracks)}, Notes: {total}")
    for name, notes in sorted(tracks.items()):
        print(f"    {name:20s}: {len(notes):5d} notes")

    export_multitrack_midi(
        tracks,
        args.output,
        bpm=args.tempo,
        key=f"{key_name}m",
        cc_events=pedal_cc,
        instruments=PHONK_INSTRUMENTS,
    )
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
