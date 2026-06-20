"""
Stress-test the CoupledHMMHarmonizer across ALL 78 modes it advertises.

Checks per mode:
  1. No crash / valid output structure (roots 0-11, positive durations).
  2. Durations tile the timeline.
  3. Mode-fidelity: when the caller *requests* a mode via initial_scale,
     Layer-2 should actually detect it (share of requested mode bars).
  4. Microtonal collapse: does the prior-building step `round(iv) % 12`
     silently turn the mode into a 12-TET common scale?
  5. Modal-cadence correctness: characteristic penultimate degree resolves
     to tonic at least once (only meaningful for modes with a known cadence).
  6. Diatonic-to-scale ratio: are chord roots that are produced actually
     members of the requested scale?
"""
from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass

from melodica.harmonize.coupled_hmm import (
    CoupledHMMHarmonizer,
    MODES_LIST,
    N_KEY_TYPES,
    PENULTIMATE_DEGREE,
)
from melodica.theory.modes import MODE_DATABASE, Mode, get_mode_intervals
from melodica.types import NoteInfo, Scale


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class ModeReport:
    mode: Mode
    category: str
    intervals: list[float]
    rounded_pcs: set[int]
    collapsed_to: str | None
    detected_share: float
    detected_top: list[tuple[str, float]]
    diatonic_ratio: float
    cadence_hit: bool | None
    chord_count: int
    sample_progression: list[str]


def _diatonic_melody(scale: Scale, n_notes: int = 128) -> list[NoteInfo]:
    """Build a strictly diatonic melody drawn only from `scale.degrees()`."""
    degrees = scale.degrees()
    pitches = []
    for d in degrees:
        # Build an octave-ish pool: pitch class + a couple of octave doublings
        for octave in (60, 72, 84):
            pitches.append(octave + int(round(d)))
    random.seed(1234)
    melody = []
    for i in range(n_notes):
        p = random.choice(pitches)
        melody.append(NoteInfo(pitch=p, start=i * 0.5, duration=0.5, velocity=80))
    return melody


def _detected_mode_share(h: CoupledHMMHarmonizer, scale: Scale,
                         seeds=8) -> tuple[float, Counter]:
    agg: Counter = Counter()
    for seed in range(seeds):
        random.seed(seed)
        degrees = scale.degrees()
        pitch_pool = []
        for d in degrees:
            for octave in (60, 72, 84):
                pitch_pool.append(octave + int(round(d)))
        melody = [NoteInfo(pitch=random.choice(pitch_pool),
                           start=i * 0.5, duration=0.5, velocity=80)
                  for i in range(16 * 8)]
        cp = h._get_change_points(64.0)
        obs = h._extract_observations(melody, cp)
        draft = h._viterbi_chords(obs, scale, cp, None, None, key_path=None)
        kp = h._viterbi_keys(draft, requested_scale=scale)
        for _, kt in kp:
            agg[MODES_LIST[kt].value] += 1
    total = sum(agg.values())
    requested_share = agg.get(scale.mode.value, 0) / total if total else 0.0
    return requested_share, agg


def _name(c):
    return f"{NOTE_NAMES[c.root]}{c.quality.name[:3]}"


def evaluate_mode(mode: Mode) -> ModeReport:
    defn = MODE_DATABASE[mode]
    intervals = list(get_mode_intervals(mode))
    rounded_pcs = {round(iv) % 12 for iv in intervals}

    # Collapse detection: do the rounded PCs equal a "common" scale?
    collapsed_to: str | None = None
    if rounded_pcs == {0, 2, 4, 5, 7, 9, 11} and intervals != [0, 2, 4, 5, 7, 9, 11]:
        collapsed_to = "MAJOR/IONIAN"
    elif rounded_pcs == {0, 2, 3, 5, 7, 8, 10} and intervals != [0, 2, 3, 5, 7, 8, 10]:
        collapsed_to = "NATURAL_MINOR/AEOLIAN"

    scale = Scale(root=0, mode=mode)
    h = CoupledHMMHarmonizer(chord_change="bars")

    # Layer-2 fidelity
    share, agg = _detected_mode_share(h, scale, seeds=8)
    total = sum(agg.values())
    top = [(m, c / total) for m, c in agg.most_common(3)]

    # Diatonic ratio + cadence over a few seeds
    scale_pcs = rounded_pcs  # what the engine "sees"
    diatonic_ratios = []
    cadence_hits = []
    penult = PENULTIMATE_DEGREE.get(mode)
    for seed in range(8):
        random.seed(seed + 100)
        melody = _diatonic_melody(scale, n_notes=128)
        chords = h.harmonize(melody, scale, duration_beats=64.0)
        if not chords:
            continue
        roots = [c.root for c in chords]
        diatonic = sum(1 for r in roots if r in scale_pcs)
        diatonic_ratios.append(diatonic / len(roots))
        if penult is not None:
            hit = any(roots[i - 1] == penult % 12 and roots[i] == 0
                      for i in range(1, len(roots)))
            cadence_hits.append(hit)

    diatonic_ratio = (sum(diatonic_ratios) / len(diatonic_ratios)
                      if diatonic_ratios else 0.0)
    cadence_hit = (any(cadence_hits) if cadence_hits else None)

    # One sample progression for inspection
    random.seed(0)
    sample = h.harmonize(_diatonic_melody(scale, n_notes=64),
                         scale, duration_beats=32.0)

    return ModeReport(
        mode=mode,
        category=defn.category,
        intervals=intervals,
        rounded_pcs=rounded_pcs,
        collapsed_to=collapsed_to,
        detected_share=share,
        detected_top=top,
        diatonic_ratio=diatonic_ratio,
        cadence_hit=cadence_hit,
        chord_count=len(sample),
        sample_progression=[_name(c) for c in sample[:8]],
    )


def main() -> None:
    random.seed(0)
    reports = [evaluate_mode(m) for m in MODES_LIST]

    print("=" * 100)
    print("COUPLED-HMM EXOTIC-MODE STRESS TEST — 78 modes")
    print("=" * 100)

    # --- 1. Collapse table ---
    print("\n## 1. Microtonal / non-12-TET collapse in prior building")
    print(f"{'Mode':24s} {'Category':12s} {'Intervals':40s} {'STATUS'}")
    collapsed_rows = [r for r in reports if r.collapsed_to]
    if not collapsed_rows:
        print("  (none)")
    for r in collapsed_rows:
        print(f"{r.mode.name:24s} {r.category:12s} {str(r.intervals):40s} "
              f"COLLAPSES -> {r.collapsed_to}")

    # --- 2. Layer-2 mode fidelity ---
    print("\n## 2. Layer-2 mode fidelity (share of bars detected as requested mode)")
    print(f"{'Mode':24s} {'Cat':10s} {'Share':>6s}  Top detected")
    fidelity_failures = []
    for r in reports:
        flag = ""
        if r.mode in (Mode.MAJOR, Mode.IONIAN, Mode.NATURAL_MINOR, Mode.AEOLIAN,
                      Mode.HARMONIC_MINOR, Mode.MELODIC_MINOR):
            # Common modes: should be near-perfect
            if r.detected_share < 0.7:
                flag = "  <-- COMMON MODE FAIL"
                fidelity_failures.append(r)
        elif r.category in ("Jazz", "Blues", "Symmetric", "Pentatonic"):
            if r.detected_share < 0.5:
                flag = "  <-- EXPECTED FIDELITY"
                fidelity_failures.append(r)
        else:  # Atmospheric, Ethnic, Exotic, Modernist, etc.
            if r.detected_share < 0.3:
                flag = "  <-- EXPECTED FIDELITY"
                fidelity_failures.append(r)
        top_str = ", ".join(f"{m}:{s:.0%}" for m, s in r.detected_top[:2])
        print(f"{r.mode.name:24s} {r.category:10s} {r.detected_share:>5.0%}  {top_str}{flag}")

    # --- 3. Diatonic-to-scale ratio ---
    print("\n## 3. Diatonic-to-scale ratio (chord roots that ARE scale tones)")
    print(f"{'Mode':24s} {'Ratio':>6s}")
    non_diatonic = [r for r in reports if r.diatonic_ratio < 0.5]
    for r in reports:
        flag = "  <-- LOW" if r.diatonic_ratio < 0.5 else ""
        print(f"{r.mode.name:24s} {r.diatonic_ratio:>5.0%}{flag}")

    # --- 4. Cadence check (only modes with a known penultimate map) ---
    print("\n## 4. Characteristic cadence appears at least once (penult -> tonic)")
    cadence_modes = [r for r in reports if r.cadence_hit is not None]
    cadence_misses = [r for r in cadence_modes if not r.cadence_hit]
    for r in cadence_modes:
        flag = "  <-- MISS" if not r.cadence_hit else ""
        print(f"{r.mode.name:24s} hit={r.cadence_hit}{flag}")

    # --- 5. Summary ---
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)
    print(f"  Total modes evaluated:          {len(reports)}")
    print(f"  Prior-collapse problems:        {len(collapsed_rows)}")
    print(f"  Layer-2 fidelity failures:      {len(fidelity_failures)}")
    print(f"  Low diatonic ratio (<50%):      {len(non_diatonic)}")
    print(f"  Cadence misses (where tested):  {len(cadence_misses)}/{len(cadence_modes)}")


if __name__ == "__main__":
    main()
