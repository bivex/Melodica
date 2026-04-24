# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-24
# Last Updated: 2026-04-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
composer/diagnostics.py — Auto-diagnostic report for MIDI generation.

Enabled via ``export_multitrack_midi(diagnose=True)`` or by calling
``diagnose_tracks()`` directly.

Prints a compact report with:
  - Per-track stats (note count, register, velocity range)
  - Psychoacoustic issue counts (masking, fusion, blur)
  - Top clashing track pairs
  - Actionable fix suggestions ranked by impact
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from melodica.types import NoteInfo
from melodica.composer.psychoacoustic import (
    detect_frequency_masking,
    detect_temporal_masking,
    detect_fusion,
    detect_blur,
    detect_register_masking,
    detect_brightness_overload,
)
from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig


@dataclass
class DiagnosticReport:
    total_notes: int = 0
    track_count: int = 0
    tracks: dict = field(default_factory=dict)
    psychoacoustic: dict = field(default_factory=dict)
    psychoacoustic_total: int = 0
    clashes: int = 0
    clash_pairs: dict = field(default_factory=dict)
    suggestions: list[str] = field(default_factory=list)


_REGISTER_NAMES = {
    (0, 24): "sub",
    (24, 36): "sub-bass",
    (36, 48): "low",
    (48, 60): "mid-low",
    (60, 72): "mid",
    (72, 84): "mid-high",
    (84, 96): "high",
    (96, 108): "very high",
    (108, 127): "top",
}


def _register_name(lo: int, hi: int) -> str:
    center = (lo + hi) // 2
    for (rlo, rhi), name in _REGISTER_NAMES.items():
        if rlo <= center < rhi:
            return name
    return f"{lo}-{hi}"


def diagnose_tracks(
    tracks: dict[str, list[NoteInfo]],
    bpm: float = 120.0,
    label: str | None = None,
) -> DiagnosticReport:
    """Run diagnostics on track data and return a report.

    The report is also printed to stdout with actionable fix suggestions.
    """
    report = DiagnosticReport()

    # ── 1. Track stats ──────────────────────────────────────────────────
    for name, notes in sorted(tracks.items()):
        if not notes:
            continue
        pitches = [n.pitch for n in notes]
        vels = [n.velocity for n in notes]
        durs = [n.duration for n in notes]
        report.tracks[name] = {
            "count": len(notes),
            "pitch_lo": min(pitches),
            "pitch_hi": max(pitches),
            "vel_lo": min(vels),
            "vel_hi": max(vels),
            "dur_min": round(min(durs), 4),
            "dur_max": round(max(durs), 4),
        }
        report.total_notes += len(notes)
    report.track_count = len(report.tracks)

    # ── 2. Psychoacoustic ──────────────────────────────────────────────
    psycho_checks = {
        "freq_mask": detect_frequency_masking(tracks),
        "temporal_mask": detect_temporal_masking(tracks),
        "fusion": detect_fusion(tracks),
        "blur": detect_blur(tracks),
        "reg_mask": detect_register_masking(tracks),
        "brightness": detect_brightness_overload(tracks),
    }
    report.psychoacoustic = {k: len(v) for k, v in psycho_checks.items()}
    report.psychoacoustic_total = sum(report.psychoacoustic.values())

    # ── 3. Harmonic clashes ─────────────────────────────────────────────
    clashes = detect_clashes(tracks, VerifierConfig(dissonance_tolerance=0.5))
    by_pair: Counter = Counter()
    for c in clashes:
        by_pair[f"{c.track_a}↔{c.track_b}"] += 1
    report.clashes = len(clashes)
    report.clash_pairs = dict(by_pair.most_common(10))

    # ── 4. Fix suggestions ──────────────────────────────────────────────
    report.suggestions = _suggestions(report.tracks, psycho_checks, by_pair)

    # ── 5. Print ────────────────────────────────────────────────────────
    _print(report, bpm, label)

    return report


# ---------------------------------------------------------------------------
# Suggestion engine
# ---------------------------------------------------------------------------

def _suggestions(
    track_stats: dict,
    psycho_checks: dict[str, list],
    clash_pairs: Counter,
) -> list[str]:
    suggestions: list[str] = []

    # Velocity problems
    for name, st in track_stats.items():
        if st["vel_hi"] < 60:
            suggestions.append(
                f"  {name}: max velocity {st['vel_hi']} too low — raise VelocityScalingModifier"
            )
        if st["vel_lo"] < 12 and st["count"] > 20:
            suggestions.append(
                f"  {name}: min velocity {st['vel_lo']} — floor too low, notes inaudible"
            )

    # Register overlap
    regs = {n: (s["pitch_lo"], s["pitch_hi"]) for n, s in track_stats.items()}
    names = list(regs.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            alo, ahi = regs[a]
            blo, bhi = regs[b]
            overlap = min(ahi, bhi) - max(alo, blo)
            if overlap <= 0:
                continue
            min_span = min(ahi - alo, bhi - blo) or 1
            pct = overlap / min_span * 100
            if pct > 60:
                suggestions.append(
                    f"  {a}↔{b}: register overlap {pct:.0f}% — add LimitNoteRangeModifier"
                )

    # Harmonic clashes
    for pair, count in list(clash_pairs.items())[:5]:
        if count > 50:
            suggestions.append(
                f"  {pair}: {count} harmonic clashes — separate registers or reduce density"
            )

    # Psychoacoustic hot spots
    for check, events in psycho_checks.items():
        n = len(events)
        if check == "freq_mask" and n > 200:
            suggestions.append(
                f"  Frequency masking: {n} events — spread register bands apart"
            )
        elif check == "reg_mask" and n > 200:
            suggestions.append(
                f"  Register masking: {n} events — bass/melody competing below C4"
            )
        elif check == "brightness" and n > 200:
            suggestions.append(
                f"  Brightness overload: {n} events — thin out notes above C6"
            )

    # Dense tracks
    for name, st in track_stats.items():
        if st["count"] > 800:
            suggestions.append(
                f"  {name}: {st['count']} notes — reduce generator density to avoid clutter"
            )

    # Blurry notes by track
    blur_events = psycho_checks.get("blur", [])
    if len(blur_events) > 100:
        blur_by_track: Counter = Counter()
        for e in blur_events:
            blur_by_track[e.track_a] += 1
        for name, count in blur_by_track.most_common(3):
            suggestions.append(
                f"  {name}: {count} blurry notes (<30ms) — increase note duration"
            )

    return suggestions


# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

_PSYCHO_LABELS = {
    "freq_mask": "Freq masking",
    "temporal_mask": "Temporal mask",
    "fusion": "Fusion",
    "blur": "Blur",
    "reg_mask": "Register mask",
    "brightness": "Brightness",
}


def _print(report: DiagnosticReport, bpm: float, label: str | None) -> None:
    w = 60
    print(f"\n{'─' * w}")
    hdr = f"DIAGNOSTICS{'  (' + label + ')' if label else ''}"
    print(f"  {hdr}")
    print(f"  {report.track_count} tracks | {report.total_notes} notes | {bpm:.0f} BPM")
    print(f"{'─' * w}")

    # Track table
    print(f"\n  {'Track':18s} {'Notes':>6s} {'Register':>12s} {'Velocity':>10s} {'Band':>10s}")
    print(f"  {'─' * 18} {'─' * 6} {'─' * 12} {'─' * 10} {'─' * 10}")
    for name, st in report.tracks.items():
        reg = f"{st['pitch_lo']}-{st['pitch_hi']}"
        vel = f"{st['vel_lo']}-{st['vel_hi']}"
        band = _register_name(st["pitch_lo"], st["pitch_hi"])
        print(f"  {name:18s} {st['count']:6d} {reg:>12s} {vel:>10s} {band:>10s}")

    # Psycho
    psycho = report.psychoacoustic
    total = report.psychoacoustic_total
    print(f"\n  Psychoacoustic: {total} issues")
    for key, label in _PSYCHO_LABELS.items():
        count = psycho.get(key, 0)
        if count > 0:
            bar = "█" * min(count // 10, 25)
            print(f"    {label:16s}: {count:5d}  {bar}")

    # Harmonic
    print(f"\n  Harmonic clashes: {report.clashes}")
    for pair, count in report.clash_pairs.items():
        if count > 20:
            print(f"    {pair:30s}: {count:5d}")

    # Suggestions
    if report.suggestions:
        print(f"\n  FIX SUGGESTIONS:")
        for s in report.suggestions:
            print(s)
    else:
        print(f"\n  No major issues detected.")

    print(f"{'─' * w}\n")
