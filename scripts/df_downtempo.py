#!/usr/bin/env python3
"""
df_downtempo.py — Downtempo arrangement with groove and HMM3.

7-act arc: Fog -> Pulse -> Flow -> Depth -> Glow -> Fade -> Sleep

- HMM3 harmonizer per section with tuned params
- Walking bass, swing, groove patterns
- Melody + counter in every section
- Section transitions via shared-chord pivot
"""

import sys
import random
import argparse
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators import (
    MelodyGenerator,
    MarkovMelodyGenerator,
    ArpeggiatorGenerator,
    BassGenerator,
    ChordGenerator,
    OstinatoGenerator,
    FingerpickingGenerator,
    AmbientPadGenerator,
    DyadGenerator,
    CountermelodyGenerator,
    ChoraleGenerator,
    CallResponseGenerator,
    PianoRunGenerator,
    PercussionGenerator,
    GrooveGenerator,
    RiffGenerator,
    WalkingBassGenerator,
    GeneratorParams,
)
from melodica.generators.dark_pad import DarkPadGenerator
from melodica.generators.dark_bass import DarkBassGenerator
from melodica.generators.swing import SwingGenerator
from melodica.generators.downbeat_rest import DownbeatRestGenerator
from melodica.harmonize import HMM3Harmonizer
from melodica.modifiers import (
    HumanizeModifier,
    VelocityScalingModifier,
    CrescendoModifier,
    StaccatoLegatoModifier,
    LimitNoteRangeModifier,
    SwingController,
    ModifierContext,
)
from melodica.composer import NonChordToneGenerator, ArticulationEngine
from melodica.rhythm import BassRhythmGenerator, SmoothRhythmGenerator
from melodica.midi import export_multitrack_midi, STYLE_INSTRUMENTS
from melodica.render_context import RenderContext


SCALES = {
    "dorian": Scale(root=0, mode=Mode.DORIAN),
    "natural_minor": Scale(root=0, mode=Mode.NATURAL_MINOR),
    "phrygian": Scale(root=0, mode=Mode.PHRYGIAN),
    "harmonic_minor": Scale(root=0, mode=Mode.HARMONIC_MINOR),
    "hungarian_minor": Scale(root=0, mode=Mode.HUNGARIAN_MINOR),
    "suspense": Scale(root=0, mode=Mode.SUSPENSE),
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
        (
            "Fog",
            0.10,
            "natural_minor",
            0,
            "fog",
            0.12,
            ["melody", "counter", "dark_pad", "dark_bass", "ambient"],
        ),
        (
            "Pulse",
            0.12,
            "dorian",
            0,
            "pulse",
            0.25,
            ["melody", "counter", "walking_bass", "groove", "chords", "fingerpicking"],
        ),
        (
            "Flow",
            0.18,
            "phrygian",
            0,
            "flow",
            0.40,
            ["melody", "counter", "arp", "walking_bass", "chords", "dyads", "groove", "ambient"],
        ),
        (
            "Depth",
            0.15,
            "harmonic_minor",
            0,
            "depth",
            0.45,
            ["melody", "counter", "dark_bass", "dark_pad", "ostinato", "call_response"],
        ),
        (
            "Glow",
            0.20,
            "dorian",
            5,
            "glow",
            0.55,
            [
                "melody",
                "melody2",
                "counter",
                "walking_bass",
                "chords",
                "arp",
                "percussion",
                "dyads",
                "groove",
            ],
        ),
        (
            "Fade",
            0.13,
            "natural_minor",
            9,
            "fade",
            0.30,
            ["melody", "counter", "ambient", "walking_bass", "chords", "fingerpicking"],
        ),
        (
            "Sleep",
            0.12,
            "natural_minor",
            0,
            "sleep",
            0.10,
            ["melody", "counter", "dark_pad", "ambient", "dark_bass"],
        ),
    ]

    raw = [max(1, round(total_bars * r)) for _, r, *_ in template]
    raw[-1] += total_bars - sum(raw)
    raw[-1] = max(1, raw[-1])
    return [
        Section(n, raw[i], sn, kr, m, d, t) for i, (n, _, sn, kr, m, d, t) in enumerate(template)
    ]


def make_pipeline(track: str, mood: str, density: float, scale: Scale):
    params = GeneratorParams(density=density)
    mods: list = []

    match track:
        case "melody":
            gen = MelodyGenerator(
                params=params,
                harmony_note_probability=0.75,
                note_range_low=60,
                note_range_high=78,
                note_repetition_probability=0.15,
                steps_probability=0.90,
            )
            mods.append(HumanizeModifier(timing_std=0.04, velocity_std=6))
            if mood == "fade":
                mods.append(CrescendoModifier(start_vel=60, end_vel=30))
            elif mood == "sleep":
                mods.append(CrescendoModifier(start_vel=45, end_vel=20))

        case "melody2":
            gen = MarkovMelodyGenerator(
                params=params,
                harmony_note_probability=0.65,
                note_range_low=60,
                note_range_high=76,
                note_repetition_probability=0.10,
            )
            mods.append(VelocityScalingModifier(scale=0.55))
            mods.append(HumanizeModifier(timing_std=0.03, velocity_std=4))

        case "counter":
            gen = CountermelodyGenerator(
                params=params,
                motion_preference="contrary",
                dissonance_on_weak=True,
                interval_limit=9,
            )
            mods.append(LimitNoteRangeModifier(low=65, high=84))
            mods.append(VelocityScalingModifier(scale=0.25))
            mods.append(HumanizeModifier(timing_std=0.06, velocity_std=2))

        case "bass":
            gen = BassGenerator(
                params=params,
                allowed_notes=["root", "fourth"],
                note_movement="alternating",
                transpose_octaves=-1,
            )
            rhythm = BassRhythmGenerator(pattern_name="syncopated")
            mods.append(LimitNoteRangeModifier(low=28, high=52))
            mods.append(VelocityScalingModifier(scale=0.85))

        case "walking_bass":
            gen = WalkingBassGenerator(
                params=params,
                approach_style="mixed",
                connect_roots=True,
                add_chromatic_passing=True,
            )
            mods.append(LimitNoteRangeModifier(low=28, high=55))
            mods.append(VelocityScalingModifier(scale=0.80))

        case "dark_bass":
            gen = DarkBassGenerator(
                params=params,
                mode="dub" if mood in ("fog", "sleep") else "trip_hop",
                octave=2,
                note_duration=8.0,
                velocity_level=0.55,
                movement="root_only",
            )
            mods.append(LimitNoteRangeModifier(low=24, high=48))

        case "dark_pad":
            gen = DarkPadGenerator(
                params=params,
                mode="minor_pad" if mood == "depth" else "phrygian_pad",
                chord_dur=8.0,
                velocity_level=0.12,
                register="low",
                overlap=0.5,
            )

        case "chords":
            gen = ChordGenerator(params=params, voicing="open")
            rhythm = SmoothRhythmGenerator(
                pattern_name="whole_legato" if mood in ("fog", "sleep") else "half_legato",
                overlap=0.3,
            )
            mods.append(VelocityScalingModifier(scale=0.55))

        case "arp":
            gen = ArpeggiatorGenerator(
                params=params,
                pattern="converge" if mood in ("flow", "depth") else "up_down",
                note_duration=0.5,
                octaves=1,
                voicing="spread",
            )
            mods.append(VelocityScalingModifier(scale=0.55))
            mods.append(SwingController(swing_ratio=0.55, grid=0.5))

        case "ostinato":
            pat = {"depth": "5-1-4-1-3-1-2-1", "glow": "1-3-5-6"}.get(mood, "1-3-5-3")
            gen = OstinatoGenerator(params=params, pattern=pat, repeat_notes=1)
            mods.append(VelocityScalingModifier(scale=0.60))

        case "ambient":
            gen = AmbientPadGenerator(params=params, voicing="spread", overlap=0.7)
            mods.append(VelocityScalingModifier(scale=0.25))
            mods.append(HumanizeModifier(timing_std=0.04, velocity_std=2))

        case "dyads":
            gen = DyadGenerator(
                params=params,
                interval_pref=[5, 7, 12],
                motion_mode="contrary",
            )
            mods.append(StaccatoLegatoModifier(amount=0.9))
            mods.append(VelocityScalingModifier(scale=0.50))

        case "fingerpicking":
            gen = FingerpickingGenerator(
                params=params,
                pattern=[0, 2, 1, 3],
                notes_to_use=[0, 1, 2, 3],
                sustain_notes="bottom_note",
            )

        case "percussion":
            gen = PercussionGenerator(
                params=params,
                pattern_name="bossa" if mood in ("pulse", "flow") else "rock",
                velocity_humanize=12,
            )

        case "groove":
            gen = GrooveGenerator(
                params=params,
                groove_pattern="funk_1" if mood in ("glow", "flow") else "funk_2",
                ghost_note_vel=22,
                accent_vel=100,
            )
            mods.append(SwingController(swing_ratio=0.58, grid=0.5))

        case "swing":
            gen = SwingGenerator(
                params=params,
                swing_ratio=0.60,
                subdivision=0.5,
                pitch_strategy="chord_tone",
                accent_pattern="backbeat",
            )

        case "call_response":
            gen = CallResponseGenerator(
                params=params,
                call_length=4.0,
                response_length=4.0,
                call_direction="down",
                response_direction="up",
            )

        case _:
            gen = AmbientPadGenerator(params=params)

    return gen, None, mods


def pick_harmonizer(mood: str):
    match mood:
        case "fog" | "sleep":
            return HMM3Harmonizer(
                beam_width=4,
                melody_weight=0.30,
                cadence_weight=0.10,
                repetition_penalty=0.03,
                secondary_dom_weight=0.05,
            )
        case "pulse":
            return HMM3Harmonizer(
                beam_width=5,
                melody_weight=0.25,
                secondary_dom_weight=0.10,
                extension_weight=0.06,
                repetition_penalty=0.08,
                cadence_weight=0.12,
            )
        case "flow" | "glow":
            return HMM3Harmonizer(
                beam_width=6,
                melody_weight=0.25,
                secondary_dom_weight=0.12,
                extension_weight=0.08,
                repetition_penalty=0.10,
                cadence_weight=0.12,
            )
        case "depth":
            return HMM3Harmonizer(
                beam_width=5,
                secondary_dom_weight=0.08,
                repetition_penalty=0.05,
                cadence_weight=0.15,
            )
        case "fade":
            return HMM3Harmonizer(
                beam_width=4,
                melody_weight=0.30,
                cadence_weight=0.18,
                repetition_penalty=0.03,
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
        if pos == 0:
            pc = int(random.choice(degs[: min(3, n)]))
        elif pos == 1:
            pc = int(degs[random.choice([1, 3]) if n > 3 else [0, 2]])
        elif pos == 2:
            pc = int(degs[random.choice([4, 6]) if n > 4 else [0, 2, 4]])
        else:
            pc = int(degs[0]) if random.random() < 0.6 else int(random.choice(degs[: min(3, n)]))

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

    nct = NonChordToneGenerator(passing_prob=0.10, neighbor_prob=0.05)
    art_engine = ArticulationEngine()
    track_contexts = {}
    prev_scale = None
    prev_last_chord = None

    INST = {
        "melody": "harp",
        "melody2": "harp",
        "counter": "harp",
        "bass": "cello",
        "walking_bass": "cello",
        "dark_bass": "cello",
        "chords": "strings_pad",
        "dark_pad": "strings_pad",
        "ambient": "strings_pad",
        "arp": "harp",
        "ostinato": "strings_staccato",
        "dyads": "harp",
        "fingerpicking": "harp",
        "percussion": "percussion",
        "groove": "harp",
        "swing": "harp",
        "call_response": "harp",
    }

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
                    pass

            if track_name in ("melody", "arp", "fingerpicking", "counter"):
                try:
                    notes = nct.add_non_chord_tones(notes, local_chords, scale)
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
        inst = INST.get(tn, "strings_pad")
        tracks[tn] = art_engine.apply(tracks[tn], inst, beat_offset)
        raw = art_engine.add_sustain_pedal_events(tracks[tn], beat_offset)
        if raw:
            pedal_cc[tn] = [(e["time"], 64, e["value"]) for e in raw]

    return tracks, pedal_cc


def main():
    p = argparse.ArgumentParser(description="DF Downtempo — groove + HMM3")
    p.add_argument("--duration", type=float, default=5.0)
    p.add_argument("--tempo", type=int, default=68)
    p.add_argument("--key", type=int, default=2)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--output", type=str, default="df_downtempo.mid")
    args = p.parse_args()

    duration = max(1.0, min(30.0, args.duration))
    bars = int(round(duration * 60 * (args.tempo / 60) / 4))
    actual = bars * 4 / args.tempo * 60
    rn = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    key_name = rn[args.key]

    print(f"DF Downtempo — groove + HMM3")
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
        instruments=STYLE_INSTRUMENTS["downtempo"],
    )
    print(f"\n  -> {args.output} ({Path(args.output).stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
