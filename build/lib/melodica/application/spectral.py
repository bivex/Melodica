# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
spectral.py — Spectral / frequency analysis for orchestral arrangements.

Detects:
  - Notes outside an instrument's physical range or sweet spot
  - Frequency zone crowding (too many instruments competing in the same band)
  - Frequency clashes (instruments within ±2 semitones playing simultaneously)
  - Articulation-based HF spectral load estimate per track
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import combinations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from melodica.types import Arrangement, Track


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def midi_to_hz(note: int) -> float:
    """MIDI note → frequency in Hz  (A4=69=440Hz)."""
    return 440.0 * (2.0 ** ((note - 69) / 12.0))


# Named spectral zones with Hz boundaries
_ZONES: list[tuple[str, float, float]] = [
    ("Sub-bass",  0.0,   80.0),
    ("Bass",      80.0,  250.0),
    ("Low-mid",   250.0, 800.0),
    ("Mid",       800.0, 2500.0),
    ("High-mid",  2500.0, 5000.0),
    ("High",      5000.0, 22000.0),
]


def _zone_name(hz: float) -> str:
    for name, lo, hi in _ZONES:
        if lo <= hz < hi:
            return name
    return "High"


# ---------------------------------------------------------------------------
# Report data classes
# ---------------------------------------------------------------------------

@dataclass
class RangeIssue:
    track_name: str
    count: int            # number of affected notes
    total: int            # total notes in track
    detail: str           # human-readable reason


@dataclass
class ClashWarning:
    track_a: str
    track_b: str
    zone: str
    clash_beats: list[float]  # beat positions where clash was detected


@dataclass
class SpectralReport:
    range_issues:  list[RangeIssue]   = field(default_factory=list)
    clash_warnings: list[ClashWarning] = field(default_factory=list)
    zone_load:     dict[str, list[str]] = field(default_factory=dict)
    # track_name → average articulation brightness factor (0.0=dark, 1.0=bright)
    hf_load:       dict[str, float]   = field(default_factory=dict)

    def print_report(self) -> None:
        W = 68
        print("\n" + "═" * W)
        print("  SPECTRAL ANALYSIS REPORT")
        print("═" * W)

        # --- Range issues ---
        if self.range_issues:
            print(f"\n  RANGE / REGISTER ISSUES  ({len(self.range_issues)}):")
            for issue in self.range_issues:
                pct = 100 * issue.count // issue.total
                print(f"    [{issue.track_name:<14}]  {issue.count}/{issue.total} notes ({pct}%)  — {issue.detail}")
        else:
            print("\n  ✓ All notes within instrument ranges.")

        # --- Zone occupation ---
        if self.zone_load:
            print("\n  SPECTRAL ZONE OCCUPATION:")
            for zone, tracks in self.zone_load.items():
                crowd = "  ⚠ CROWDED" if len(tracks) > 3 else ""
                print(f"    {zone:<12}  {', '.join(tracks)}{crowd}")

        # --- Frequency clashes ---
        if self.clash_warnings:
            print(f"\n  FREQUENCY CLASHES  ({len(self.clash_warnings)}):")
            for w in self.clash_warnings:
                beats_str = ", ".join(f"{b:.0f}" for b in w.clash_beats[:4])
                suffix = "..." if len(w.clash_beats) > 4 else ""
                print(f"    {w.track_a} ↔ {w.track_b}  [{w.zone}]  beats: {beats_str}{suffix}")
        else:
            print("\n  ✓ No frequency clashes detected.")

        # --- HF load ---
        if self.hf_load:
            print("\n  HF SPECTRAL LOAD BY TRACK  (articulation brightness, 0=dark → 1=bright):")
            for name, load in sorted(self.hf_load.items(), key=lambda x: -x[1]):
                filled = round(load * 24)
                bar = "█" * filled + "░" * (24 - filled)
                print(f"    {name:<14}  {bar}  {load:.2f}")

        print("═" * W)


# ---------------------------------------------------------------------------
# Analyser
# ---------------------------------------------------------------------------

# Articulation brightness factor (0.0=dark, 1.0=bright) — mirrors ARTICULATION_BRIGHTNESS CC74
_ART_BRIGHT_FACTOR: dict[str, float] = {
    "legato":    0.43,
    "staccato":  0.79,
    "marcato":   0.90,
    "sustain":   0.31,
    "pizzicato": 0.71,
    "tremolo":   0.61,
    "spiccato":  0.75,
}


class SpectralAnalyzer:
    """
    Analyses an Arrangement for spectral conflicts and register issues.

    Usage:
        report = SpectralAnalyzer.analyze(arrangement)
        report.print_report()
    """

    # fraction of notes outside sweet spot that triggers a warning
    SWEET_SPOT_THRESHOLD = 0.15

    @classmethod
    def analyze(cls, arrangement: "Arrangement") -> SpectralReport:
        from melodica.application.orchestration import ORCHESTRAL_PROFILES

        report = SpectralReport()
        profiled = [t for t in arrangement.tracks if t.name in ORCHESTRAL_PROFILES]

        # ── 1. Range / sweet spot validation ─────────────────────────────────
        for track in profiled:
            p = ORCHESTRAL_PROFILES[track.name]
            total = len(track.notes)
            if total == 0:
                continue

            out_of_range = [n for n in track.notes
                            if n.pitch < p.min_pitch or n.pitch > p.max_pitch]
            if out_of_range:
                report.range_issues.append(RangeIssue(
                    track.name, len(out_of_range), total,
                    f"outside physical range [{p.min_pitch}–{p.max_pitch}]"
                ))
                continue  # skip sweet-spot check if already out of range

            outside_sweet = [n for n in track.notes
                             if n.pitch < p.sweet_spot[0] or n.pitch > p.sweet_spot[1]]
            if len(outside_sweet) / total > cls.SWEET_SPOT_THRESHOLD:
                report.range_issues.append(RangeIssue(
                    track.name, len(outside_sweet), total,
                    f"outside sweet spot [{p.sweet_spot[0]}–{p.sweet_spot[1]}] "
                    f"(timbre may be thin/harsh)"
                ))

        # ── 2. Zone occupation ────────────────────────────────────────────────
        zone_map: dict[str, list[str]] = {}
        for track in profiled:
            z = _zone_name(ORCHESTRAL_PROFILES[track.name].spectral_centroid)
            zone_map.setdefault(z, []).append(track.name)
        report.zone_load = {z: t for z, t in zone_map.items() if t}

        # ── 3. Frequency clash detection (sampled every 4 beats) ─────────────
        sample_step = 4
        sample_beats = list(range(0, max(1, int(arrangement.total_beats)), sample_step))

        # Build pitch-sets per track per sampled beat
        active: dict[str, dict[int, set[int]]] = {}
        for track in profiled:
            by_beat: dict[int, set[int]] = {}
            for beat in sample_beats:
                pitches = {
                    n.pitch for n in track.notes
                    if n.start <= beat < n.start + n.duration
                }
                if pitches:
                    by_beat[beat] = pitches
            active[track.name] = by_beat

        for ta, tb in combinations(profiled, 2):
            pa = ORCHESTRAL_PROFILES[ta.name]
            pb = ORCHESTRAL_PROFILES[tb.name]
            # Only flag clashes within the same spectral zone
            if _zone_name(pa.spectral_centroid) != _zone_name(pb.spectral_centroid):
                continue

            clash_beats: list[float] = []
            for beat in sample_beats:
                pitches_a = active[ta.name].get(beat, set())
                pitches_b = active[tb.name].get(beat, set())
                if any(abs(pa - pb) <= 2 for pa in pitches_a for pb in pitches_b):
                    clash_beats.append(float(beat))

            # Only report if clashes occur in at least 3 sample points
            if len(clash_beats) >= 3:
                report.clash_warnings.append(ClashWarning(
                    track_a=ta.name,
                    track_b=tb.name,
                    zone=_zone_name(pa.spectral_centroid),
                    clash_beats=clash_beats,
                ))

        # ── 4. HF load per track ──────────────────────────────────────────────
        for track in arrangement.tracks:
            if not track.notes:
                continue
            factors = [
                _ART_BRIGHT_FACTOR.get(n.articulation or "", 0.50)
                for n in track.notes
            ]
            report.hf_load[track.name] = round(sum(factors) / len(factors), 3)

        return report
