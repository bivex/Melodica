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
gravity_pull.py — Downtempo beat that drags you down, with a luminous middle.

Feel: heavy, gravitational, low-register density. The "pulling down" comes from
descending bass lines, slow swing, sparse highs, and Phrygian darkness.
Section 4 "Levitation" shifts to Dorian — a brief float before the sink resumes.

Structure (48 bars, ~4.6 min @ 62 BPM):
  Descent (6) -> Gravity (8) -> Abyss (6) -> Levitation (8) -> Sinking (8) -> Freefall (8) -> Settle (4)
"""

import sys
import random
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.walking_bass import WalkingBassGenerator
from melodica.generators.boom_bap import BoomBapGenerator
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.melody import MelodyGenerator
from melodica.generators.countermelody import CountermelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator
from melodica.generators.ghost_notes import GhostNotesGenerator
from melodica.generators.vocal_oohs import VocalOohsGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
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


# -- sections: (bars, track_names) ------------------------------------------------

DESCENT = [
    (6, ["dark_pad", "sub_drone", "fx_impact"]),
]

GRAVITY = [
    (8, ["dark_bass", "boom_bap", "dark_pad", "hihat_spare", "lead_whisper"]),
]

ABYSS = [
    (6, ["dark_bass_slide", "boom_bap_hard", "dark_pad", "hihat_mid", "lead_descent", "ghost_snare"]),
]

LEVITATION = [
    (8, ["walking_bass", "boom_bap_soft", "ambient_pad", "arp", "melody", "vocal_oohs", "countermelody"]),
]

SINKING = [
    (8, ["dark_bass_slide", "boom_bap_hard", "dark_pad", "hihat_rapid", "lead_dark", "ghost_snare", "fx_riser"]),
]

FREEFALL = [
    (8, ["dark_bass_slide", "boom_bap_hard", "dark_pad", "hihat_rapid", "lead_full", "ghost_snare", "arp_dark", "fx_riser"]),
]

SETTLE = [
    (4, ["dark_pad", "sub_drone", "fx_impact"]),
]


# -- scales -----------------------------------------------------------------------

SCALE_MAIN = Scale(root=1, mode=Mode.PHRYGIAN)   # C# Phrygian — dark, flat-2 pull
SCALE_LIFT = Scale(root=1, mode=Mode.DORIAN)      # C# Dorian — brighter, the "float"


# -- harmonization ----------------------------------------------------------------

def pick_harmonizer(mood: str) -> HMM3Harmonizer:
    params = {
        "sparse":   dict(beam_width=3, melody_weight=0.20, secondary_dom_weight=0.04,
                         extension_weight=0.03, repetition_penalty=0.12, cadence_weight=0.08),
        "heavy":    dict(beam_width=5, melody_weight=0.30, secondary_dom_weight=0.08,
                         extension_weight=0.05, repetition_penalty=0.06, cadence_weight=0.10),
        "tense":    dict(beam_width=5, melody_weight=0.25, secondary_dom_weight=0.10,
                         extension_weight=0.08, repetition_penalty=0.05, cadence_weight=0.06),
        "ethereal": dict(beam_width=4, melody_weight=0.15, secondary_dom_weight=0.03,
                         extension_weight=0.10, repetition_penalty=0.04, cadence_weight=0.15),
        "intense":  dict(beam_width=6, melody_weight=0.35, secondary_dom_weight=0.12,
                         extension_weight=0.07, repetition_penalty=0.04, cadence_weight=0.08),
    }
    return HMM3Harmonizer(**params.get(mood, params["heavy"]))


def harmonize_section(bars, scale, mood, beats_per_bar=4):
    harmonizer = pick_harmonizer(mood)
    degs = scale.degrees()
    contour = []
    for bar in range(bars):
        pos = bar % 4
        if pos == 0:
            pc = int(degs[0])
        elif pos == 1:
            pc = int(degs[min(3, len(degs) - 1)])
        elif pos == 2:
            pc = int(degs[min(4, len(degs) - 1)] if len(degs) > 4 else degs[0])
        else:
            pc = int(degs[0]) if random.random() < 0.55 else int(degs[min(2, len(degs) - 1)])
        # descending contour — start higher, resolve lower each phrase
        descent_offset = max(0, 3 - (bar % 4))
        contour.append(
            NoteInfo(
                pitch=44 + pc - descent_offset,
                start=bar * beats_per_bar,
                duration=beats_per_bar - 0.1,
                velocity=50,
            )
        )
    s_beats = bars * beats_per_bar
    chords = harmonizer.harmonize(contour, scale, s_beats)
    while len(chords) < bars:
        chords.append(
            chords[-1]
            if chords
            else ChordLabel(
                root=int(degs[0]), quality=Quality.MINOR,
                start=len(chords) * beats_per_bar, duration=beats_per_bar,
            )
        )
    return chords


# -- track builder ----------------------------------------------------------------

def build_track(name):
    mods = []

    match name:
        case "dark_bass":
            gen = DarkBassGenerator(
                params=GeneratorParams(density=0.45),
                mode="trip_hop",
                octave=2,
                note_duration=3.5,
                velocity_level=0.75,
                movement="root_fifth",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=43))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "dark_bass_slide":
            gen = Bass808SlidingGenerator(
                params=GeneratorParams(density=0.55),
                pattern="drill_sliding",
                slide_type="chromatic",
                slide_probability=0.55,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=43))
            mods.append(VelocityScalingModifier(scale=0.90))

        case "walking_bass":
            gen = WalkingBassGenerator(
                params=GeneratorParams(density=0.5),
                approach_style="chromatic",
                add_chromatic_passing=True,
                connect_roots=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=48))
            mods.append(VelocityScalingModifier(scale=0.70))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))

        case "boom_bap":
            gen = BoomBapGenerator(
                params=GeneratorParams(density=0.4),
                variant="dusty",
                swing_ratio=0.58,
                chop_density=0.25,
                ghost_snares=True,
                dusty_velocities=True,
            )

        case "boom_bap_hard":
            gen = BoomBapGenerator(
                params=GeneratorParams(density=0.6),
                variant="golden_age",
                swing_ratio=0.56,
                chop_density=0.35,
                ghost_snares=True,
                dusty_velocities=True,
            )

        case "boom_bap_soft":
            gen = BoomBapGenerator(
                params=GeneratorParams(density=0.3),
                variant="jazz_hop",
                swing_ratio=0.62,
                chop_density=0.15,
                ghost_snares=False,
                dusty_velocities=True,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=GeneratorParams(density=0.3),
                mode="phrygian_pad",
                chord_dur=6.0,
                velocity_level=0.15,
                register="low",
                overlap=0.6,
            )

        case "ambient_pad":
            gen = AmbientPadGenerator(
                params=GeneratorParams(density=0.25),
                voicing="spread",
                overlap=0.3,
            )
            mods.append(LimitNoteRangeModifier(low=48, high=67))
            mods.append(VelocityScalingModifier(scale=0.40))

        case "hihat_spare":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.2),
                pattern="trap_eighth",
                roll_density=0.15,
                open_hat_probability=0.06,
            )
            mods.append(SwingController(swing_ratio=0.58, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.45))

        case "hihat_mid":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.35),
                pattern="trap_eighth",
                roll_density=0.30,
                open_hat_probability=0.08,
            )
            mods.append(SwingController(swing_ratio=0.57, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.55))

        case "hihat_rapid":
            gen = HiHatStutterGenerator(
                params=GeneratorParams(density=0.5),
                pattern="drill_stutter",
                roll_density=0.50,
                open_hat_probability=0.05,
            )
            mods.append(SwingController(swing_ratio=0.56, grid=0.5))
            mods.append(VelocityScalingModifier(scale=0.65))

        case "lead_whisper":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.15),
                style="retro",
                portamento=0.15,
                note_length="legato",
            )
            mods.append(LimitNoteRangeModifier(low=55, high=72))
            mods.append(VelocityScalingModifier(scale=0.25))
            mods.append(HumanizeModifier(timing_std=0.04, velocity_std=3))

        case "lead_descent":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.35, leap_probability=0.15),
                harmony_note_probability=0.55,
                steps_probability=0.75,
                note_repetition_probability=0.08,
            )
            mods.append(LimitNoteRangeModifier(low=55, high=74))
            mods.append(VelocityScalingModifier(scale=0.40))
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5))

        case "lead_dark":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.45),
                style="supersaw",
                portamento=0.25,
                note_length="mixed",
            )
            mods.append(LimitNoteRangeModifier(low=52, high=72))
            mods.append(VelocityScalingModifier(scale=0.50))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))

        case "lead_full":
            gen = LeadSynthGenerator(
                params=GeneratorParams(density=0.55),
                style="supersaw",
                portamento=0.20,
                note_length="mixed",
            )
            mods.append(LimitNoteRangeModifier(low=52, high=76))
            mods.append(VelocityScalingModifier(scale=0.60))
            mods.append(HumanizeModifier(timing_std=0.02, velocity_std=4))

        case "melody":
            gen = MelodyGenerator(
                params=GeneratorParams(density=0.45, leap_probability=0.20),
                harmony_note_probability=0.60,
                steps_probability=0.65,
                note_repetition_probability=0.10,
            )
            mods.append(LimitNoteRangeModifier(low=57, high=76))
            mods.append(VelocityScalingModifier(scale=0.50))
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=5))

        case "countermelody":
            gen = CountermelodyGenerator(
                params=GeneratorParams(density=0.35, leap_probability=0.15),
                motion_preference="contrary",
                dissonance_on_weak=True,
                interval_limit=7,
            )
            mods.append(LimitNoteRangeModifier(low=60, high=79))
            mods.append(VelocityScalingModifier(scale=0.35))
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=4))

        case "arp":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.4),
                pattern="up_down",
            )
            mods.append(LimitNoteRangeModifier(low=55, high=79))
            mods.append(VelocityScalingModifier(scale=0.35))
            mods.append(HumanizeModifier(timing_std=0.01, velocity_std=3))

        case "arp_dark":
            gen = ArpeggiatorGenerator(
                params=GeneratorParams(density=0.5),
                pattern="down_up",
            )
            mods.append(LimitNoteRangeModifier(low=48, high=72))
            mods.append(VelocityScalingModifier(scale=0.40))

        case "ghost_snare":
            gen = GhostNotesGenerator(
                params=GeneratorParams(density=0.3),
                target="snare",
                pattern="hiphop",
                ghost_velocity=28,
                ghost_density=0.45,
                placement="sixteenth",
            )

        case "vocal_oohs":
            gen = VocalOohsGenerator(
                params=GeneratorParams(density=0.25),
                syllable="ooh",
                harmony_count=3,
                vibrato=0.35,
                breath_phasing=True,
            )
            mods.append(LimitNoteRangeModifier(low=55, high=72))
            mods.append(VelocityScalingModifier(scale=0.30))

        case "sub_drone":
            gen = DroneGenerator(
                params=GeneratorParams(density=0.2),
                variant="power",
                fade_in=4.0,
                fade_out=3.0,
                retrigger_on_chord=False,
            )
            mods.append(LimitNoteRangeModifier(low=24, high=36))
            mods.append(VelocityScalingModifier(scale=0.55))

        case "fx_riser":
            gen = FXRiserGenerator(
                params=GeneratorParams(density=0.3),
                riser_type="synth",
                length_beats=4.0,
                pitch_curve="exponential",
                peak_velocity=100,
            )

        case "fx_impact":
            gen = FXImpactGenerator(
                params=GeneratorParams(density=0.25),
                impact_type="boom",
                tail_length=4.0,
                pitch_drop=18,
            )

        case _:
            return None, []

    return gen, mods


# -- instruments ------------------------------------------------------------------

INSTRUMENTS = {
    "dark_bass": 38,        # Synth Bass 1
    "dark_bass_slide": 38,
    "walking_bass": 32,     # Acoustic Bass
    "boom_bap": 0,
    "boom_bap_hard": 0,
    "boom_bap_soft": 0,
    "dark_pad": 92,         # Halo Pad
    "ambient_pad": 89,      # Warm Pad
    "hihat_spare": 0,
    "hihat_mid": 0,
    "hihat_rapid": 0,
    "lead_whisper": 81,     # Sawtooth Lead
    "lead_descent": 81,
    "lead_dark": 81,
    "lead_full": 81,
    "melody": 88,           # New Age Pad
    "countermelody": 89,    # Warm Pad
    "arp": 46,              # Harp
    "arp_dark": 46,
    "ghost_snare": 0,
    "vocal_oohs": 53,       # Choir Aahs
    "sub_drone": 38,        # Synth Bass 1
    "fx_riser": 97,         # FX 1 Rain
    "fx_impact": 103,       # FX 4 Atmosphere
}

PERC_TRACKS = {
    "boom_bap", "boom_bap_hard", "boom_bap_soft",
    "hihat_spare", "hihat_mid", "hihat_rapid",
    "ghost_snare",
}


# -- section config ---------------------------------------------------------------

SECTIONS = [
    ("Descent",    DESCENT,    SCALE_MAIN, "sparse"),
    ("Gravity",    GRAVITY,    SCALE_MAIN, "heavy"),
    ("Abyss",      ABYSS,      SCALE_MAIN, "tense"),
    ("Levitation", LEVITATION, SCALE_LIFT, "ethereal"),
    ("Sinking",    SINKING,    SCALE_MAIN, "tense"),
    ("Freefall",   FREEFALL,   SCALE_MAIN, "intense"),
    ("Settle",     SETTLE,     SCALE_MAIN, "sparse"),
]


# -- generate ---------------------------------------------------------------------

def generate(tempo, seed):
    if seed is not None:
        random.seed(seed)

    beats_per_bar = 4
    tracks: dict[str, list[NoteInfo]] = {}
    beat_offset = 0.0
    track_contexts: dict[str, RenderContext] = {}
    art_engine = ArticulationEngine()

    for sec_name, sec_data, scale, mood in SECTIONS:
        for sec_bars, sec_tracks in sec_data:
            s_beats = sec_bars * beats_per_bar
            chords = harmonize_section(sec_bars, scale, mood, beats_per_bar)

            abs_chords = [
                ChordLabel(
                    root=c.root, quality=c.quality,
                    start=round(c.start + beat_offset, 6),
                    duration=c.duration, degree=c.degree,
                )
                for c in chords
            ]

            print(f"  [{sec_name:11s}] {sec_bars} bars | {scale.mode.name:8s} | {mood:8s} | {', '.join(sec_tracks)}")

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
                    current_scale=scale,
                )

                notes = gen.render(chords, scale, s_beats, ctx)
                if hasattr(gen, "_last_context") and gen._last_context is not None:
                    track_contexts[track_name] = gen._last_context

                mctx = ModifierContext(duration_beats=s_beats, chords=chords, timeline=None, scale=scale)
                for m in mods:
                    try:
                        notes = m.modify(notes, mctx)
                    except Exception:
                        pass

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
        if tn not in PERC_TRACKS:
            tracks[tn] = art_engine.apply(tracks[tn], tn, beat_offset)
            raw = art_engine.add_sustain_pedal_events(tracks[tn], beat_offset)
            if raw:
                pedal_cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, pedal_cc


def main():
    p = argparse.ArgumentParser(description="Gravity Pull — downtempo beat that drags you down")
    p.add_argument("--tempo", type=int, default=62)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="gravity_pull.mid")
    args = p.parse_args()

    total_bars = 6 + 8 + 6 + 8 + 8 + 8 + 4  # 48
    actual_min = total_bars * 4 / args.tempo * 60

    print("Gravity Pull — Downtempo")
    print(f"  {actual_min:.1f} min ({total_bars} bars @ {args.tempo} BPM)")
    print(f"  C# Phrygian / Dorian")
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
        key="C#m",
        cc_events=pedal_cc,
        instruments=INSTRUMENTS,
    )
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
