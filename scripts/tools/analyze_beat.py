# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
scripts/analyze_beat.py — Beat Arrangement Monotony Analyzer

Analyzes generated notes for uniformity problems that make output sound flat.
Produces a per-track report with scores and specific issues.

Usage:
    python3 scripts/analyze_beat.py                    # analyze beat arrangement
    python3 scripts/analyze_beat.py --script pro       # analyze demo_pro_structure
"""

import argparse
import math
import sys
from collections import Counter
from dataclasses import dataclass


def shannon_entropy(counter: Counter) -> float:
    total = sum(counter.values())
    if total == 0:
        return 0.0
    return -sum((c / total) * math.log2(c / total) for c in counter.values() if c > 0)


def normalized_entropy(counter: Counter, max_items: int | None = None) -> float:
    if max_items is None:
        max_items = len(counter)
    if max_items <= 1:
        return 1.0
    h = shannon_entropy(counter)
    h_max = math.log2(max_items)
    return h / h_max if h_max > 0 else 0.0


@dataclass
class TrackReport:
    name: str
    n_notes: int
    duration_beats: float
    pitch_entropy_norm: float
    rhythm_entropy_norm: float
    velocity_entropy_norm: float
    interval_entropy_norm: float
    pitch_range: int
    velocity_range: int
    unique_pitches: int
    unique_durations: int
    avg_notes_per_bar: float
    density_variance: float
    ngr4_repetition_ratio: float
    issues: list[str]

    @property
    def overall_score(self) -> float:
        return (
            self.pitch_entropy_norm * 0.25
            + self.rhythm_entropy_norm * 0.20
            + self.velocity_entropy_norm * 0.20
            + self.interval_entropy_norm * 0.15
            + (1.0 - self.ngr4_repetition_ratio) * 0.20
        )


def analyze_track(name: str, notes: list, beats_per_bar: float = 4.0) -> TrackReport:
    issues: list[str] = []

    if not notes:
        return TrackReport(
            name=name, n_notes=0, duration_beats=0.0,
            pitch_entropy_norm=0.0, rhythm_entropy_norm=0.0,
            velocity_entropy_norm=0.0, interval_entropy_norm=0.0,
            pitch_range=0, velocity_range=0,
            unique_pitches=0, unique_durations=0,
            avg_notes_per_bar=0.0, density_variance=0.0,
            ngr4_repetition_ratio=0.0,
            issues=["EMPTY TRACK — no notes generated"],
        )

    pitches = [n.pitch for n in notes]
    durations = [round(n.duration, 3) for n in notes]
    velocities = [n.velocity for n in notes]

    total_beats = max(n.start + n.duration for n in notes)

    # --- Pitch variety ---
    pitch_counter = Counter(pitches)
    pitch_entropy = normalized_entropy(pitch_counter, max_items=min(len(pitch_counter), 88))
    unique_pitches = len(pitch_counter)
    pitch_range = max(pitches) - min(pitches)

    if unique_pitches <= 3 and len(notes) > 8:
        issues.append(f"LOW PITCH VARIETY — only {unique_pitches} unique pitches")
    if pitch_entropy < 0.25:
        issues.append(f"LOW PITCH ENTROPY ({pitch_entropy:.2f}) — same notes repeating")
    if pitch_range < 5 and len(notes) > 10:
        issues.append(f"LOW PITCH RANGE ({pitch_range} semitones) — no melodic contour")

    # --- Rhythm variety ---
    dur_counter = Counter(durations)
    rhythm_entropy = normalized_entropy(dur_counter, max_items=len(dur_counter))
    unique_durations = len(dur_counter)

    if unique_durations == 1 and len(notes) > 4:
        issues.append(f"MONORHYTHM — all notes same duration ({durations[0]})")
    if rhythm_entropy < 0.2:
        issues.append(f"LOW RHYTHM ENTROPY ({rhythm_entropy:.2f}) — robotic rhythm")

    # --- Velocity dynamics ---
    vel_counter = Counter(velocities)
    vel_entropy = normalized_entropy(vel_counter, max_items=len(vel_counter))
    vel_range = max(velocities) - min(velocities)

    if vel_range < 10 and len(notes) > 8:
        issues.append(f"FLAT VELOCITY — range only {vel_range} (no dynamics)")
    if vel_entropy < 0.15:
        issues.append(f"LOW VELOCITY ENTROPY ({vel_entropy:.2f}) — no accent variation")

    # --- Interval variety ---
    intervals = [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]
    if intervals:
        intv_counter = Counter(intervals)
        interval_entropy = normalized_entropy(intv_counter, max_items=len(intv_counter))
        most_common_intv = intv_counter.most_common(1)[0]
        if most_common_intv[1] > len(intervals) * 0.6:
            issues.append(f"DOMINANT INTERVAL — {most_common_intv[0]:+d} semitones in {most_common_intv[1]}/{len(intervals)} steps")
    else:
        interval_entropy = 0.0

    # --- Density variance across bars ---
    n_bars = max(1, int(total_beats / beats_per_bar))
    bars = [0] * n_bars
    for n in notes:
        bar = min(int(n.start / beats_per_bar), n_bars - 1)
        bars[bar] += 1
    avg_density = sum(bars) / len(bars) if bars else 0
    density_var = (sum((b - avg_density) ** 2 for b in bars) / len(bars)) ** 0.5 if bars else 0

    if density_var < 0.5 and n_bars > 4:
        issues.append(f"FLAT DENSITY — variance {density_var:.1f} across {n_bars} bars (no phrasing)")

    # --- N-gram repetition (4-note sequences) ---
    if len(pitches) >= 8:
        ngrams = [tuple(pitches[i:i+4]) for i in range(len(pitches) - 3)]
        ngr_counter = Counter(ngrams)
        repeated = sum(c - 1 for c in ngr_counter.values() if c > 1)
        ngr4_rep = repeated / len(ngrams) if ngrams else 0.0

        if ngr4_rep > 0.4:
            issues.append(f"HIGH REPETITION — {ngr4_rep*100:.0f}% of 4-note sequences repeat")
    else:
        ngr4_rep = 0.0

    return TrackReport(
        name=name, n_notes=len(notes), duration_beats=total_beats,
        pitch_entropy_norm=round(pitch_entropy, 3),
        rhythm_entropy_norm=round(rhythm_entropy, 3),
        velocity_entropy_norm=round(vel_entropy, 3),
        interval_entropy_norm=round(interval_entropy, 3),
        pitch_range=pitch_range,
        velocity_range=vel_range,
        unique_pitches=unique_pitches,
        unique_durations=unique_durations,
        avg_notes_per_bar=round(avg_density, 1),
        density_variance=round(density_var, 1),
        ngr4_repetition_ratio=round(ngr4_rep, 3),
        issues=issues,
    )


def score_bar(score: float, width: int = 20) -> str:
    filled = int(score * width)
    empty = width - filled
    color = "\033[92m" if score >= 0.5 else "\033[93m" if score >= 0.3 else "\033[91m"
    reset = "\033[0m"
    return f"{color}{'█' * filled}{'░' * empty}{reset} {score:.2f}"


def print_report(reports: list[TrackReport]):
    print()
    print("=" * 80)
    print("  M I D I   M O N O T O N Y   A N A L Y S I S")
    print("=" * 80)

    for r in reports:
        print()
        print(f"  ┌─ {r.name} ({r.n_notes} notes, {r.duration_beats:.0f} beats) ─────────────────")
        print(f"  │ Pitch variety:    {score_bar(r.pitch_entropy_norm)}")
        print(f"  │ Rhythm variety:   {score_bar(r.rhythm_entropy_norm)}")
        print(f"  │ Velocity variety: {score_bar(r.velocity_entropy_norm)}")
        print(f"  │ Interval variety: {score_bar(r.interval_entropy_norm)}")
        print(f"  │ Repetition:       {score_bar(1.0 - r.ngr4_repetition_ratio)}")
        print(f"  │ OVERALL:          {score_bar(r.overall_score)}")
        print(f"  │")
        print(f"  │ Pitches: {r.unique_pitches} unique, range {r.pitch_range} semitones")
        print(f"  │ Duration types: {r.unique_durations} unique")
        print(f"  │ Velocity range: {r.velocity_range}")
        print(f"  │ Density: {r.avg_notes_per_bar:.1f} notes/bar, variance {r.density_variance:.1f}")

        if r.issues:
            print(f"  │")
            for issue in r.issues:
                print(f"  │ ⚠  {issue}")

        print(f"  └{'─' * 60}")

    scores = [r.overall_score for r in reports if r.n_notes > 0]
    if scores:
        avg = sum(scores) / len(scores)
        worst = min(reports, key=lambda r: r.overall_score)
        best = max(reports, key=lambda r: r.overall_score)

        print()
        print(f"  SUMMARY: Average variety score = {avg:.2f}")
        print(f"  Best:  {best.name} ({best.overall_score:.2f})")
        print(f"  Worst: {worst.name} ({worst.overall_score:.2f})")

        all_issues = [i for r in reports for i in r.issues]
        if all_issues:
            print()
            print(f"  TOTAL ISSUES: {len(all_issues)}")
            issue_counts = Counter(all_issues)
            for issue, count in issue_counts.most_common():
                print(f"    [{count}x] {issue}")

    print()
    print("=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Analyze MIDI output for monotony")
    parser.add_argument("--script", choices=["beat", "pro"], default="beat",
                        help="Which demo script to analyze (default: beat)")
    parser.add_argument("--midi", type=str, default=None,
                        help="Path to existing MIDI file to analyze instead")
    args = parser.parse_args()

    print("  Generating notes for analysis...")

    if args.midi:
        print(f"  MIDI file analysis not yet implemented. Use --script instead.")
        sys.exit(1)

    if args.script == "beat":
        from scripts.demo_beat_arrangement import generate_notes
        notes_dict, tracks, parts, scale = generate_notes()

    elif args.script == "pro":
        from scripts.demo_pro_structure import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart, structure_to_schedule
        from melodica.generators import (
            MelodyGenerator, BassGenerator, StringsEnsembleGenerator,
            AmbientPadGenerator, FluteGenerator, ChoirAahsGenerator,
        )
        from melodica.types import Scale, Mode

        scale = Scale(2, Mode.DORIAN)

        tracks = [
            TrackConfig(name="Cinematic_Pad", generator=AmbientPadGenerator(voicing="spread"), instrument="dark_pad", density=0.5, octave_shift=-1),
            TrackConfig(name="Deep_Bass", generator=BassGenerator(style="root_only"), instrument="contrabass", density=0.6, octave_shift=-2),
            TrackConfig(name="Orchestral_Strings", generator=StringsEnsembleGenerator(section_size="full", articulation="legato", divisi=2), instrument="strings", density=0.7),
            TrackConfig(name="Lead_Melody", generator=MelodyGenerator(motif_probability=0.8), instrument="violin", density=0.6, octave_shift=1),
            TrackConfig(name="Woodwind_Counter", generator=FluteGenerator(), instrument="flute", density=0.5, octave_shift=1),
            TrackConfig(name="Epic_Choir", generator=ChoirAahsGenerator(voice_count=6, dynamics="f"), instrument="choir", density=0.6, octave_shift=1),
        ]

        parts = [
            IdeaPart(name="Intro", bars=8, scale=scale, tempo=75, progression_type="coupled_hmm",
                     track_phrase_schedules={
                         "Cinematic_Pad": structure_to_schedule("A", 8), "Deep_Bass": structure_to_schedule("A", 8),
                         "Lead_Melody": structure_to_schedule("R", 8), "Woodwind_Counter": structure_to_schedule("A R", 4),
                         "Orchestral_Strings": structure_to_schedule("R", 8), "Epic_Choir": structure_to_schedule("R", 8),
                     }),
            IdeaPart(name="Verse", bars=8, scale=scale, tempo=80, progression_type="coupled_hmm",
                     track_phrase_schedules={
                         "Cinematic_Pad": structure_to_schedule("A", 8), "Deep_Bass": structure_to_schedule("A", 8),
                         "Orchestral_Strings": structure_to_schedule("A", 8), "Lead_Melody": structure_to_schedule("A R", 4),
                         "Woodwind_Counter": structure_to_schedule("R A:var", 4), "Epic_Choir": structure_to_schedule("R", 8),
                     }),
            IdeaPart(name="Chorus", bars=12, scale=scale, tempo=95, progression_type="coupled_hmm",
                     track_phrase_schedules={
                         "Cinematic_Pad": structure_to_schedule("A", 12), "Deep_Bass": structure_to_schedule("A", 12),
                         "Orchestral_Strings": structure_to_schedule("A", 12), "Epic_Choir": structure_to_schedule("A", 12),
                         "Lead_Melody": structure_to_schedule("B R", 8, loop=False),
                         "Woodwind_Counter": structure_to_schedule("R B R", 4, loop=False),
                     }),
            IdeaPart(name="Climax", bars=8, scale=scale, tempo=110, progression_type="coupled_hmm",
                     track_phrase_schedules={
                         "Cinematic_Pad": structure_to_schedule("A", 8), "Deep_Bass": structure_to_schedule("A", 8),
                         "Orchestral_Strings": structure_to_schedule("A", 8), "Epic_Choir": structure_to_schedule("A", 8),
                         "Lead_Melody": structure_to_schedule("B:var", 8), "Woodwind_Counter": structure_to_schedule("B:retro", 8),
                     }),
            IdeaPart(name="Outro", bars=8, scale=scale, tempo=75, progression_type="coupled_hmm",
                     track_phrase_schedules={
                         "Cinematic_Pad": structure_to_schedule("A R", 4), "Deep_Bass": structure_to_schedule("A R", 4),
                         "Orchestral_Strings": structure_to_schedule("R", 8), "Epic_Choir": structure_to_schedule("R", 8),
                         "Lead_Melody": structure_to_schedule("R", 8), "Woodwind_Counter": structure_to_schedule("A R", 4),
                     }),
        ]

        config = IdeaToolConfig(style="cinematic_hybrid", parts=parts, tracks=tracks,
                                use_voice_leading=True, use_harmonic_verifier=True)
        notes_dict = IdeaTool(config).generate()

    reports: list[TrackReport] = []
    for name, notes in notes_dict.items():
        if name.startswith("_") or not isinstance(notes, list):
            continue
        reports.append(analyze_track(name, notes))

    reports.sort(key=lambda r: r.overall_score)
    print_report(reports)


if __name__ == "__main__":
    main()
