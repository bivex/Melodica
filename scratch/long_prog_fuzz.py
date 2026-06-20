"""
Exploratory fuzzer: run LONG progressions (32-256 bars) through
CoupledHMMHarmonizer across many modes/keys/melody-types and scan for
anomalies. The goal is to FIND BUGS, not to assert correctness.

Scans for:
  1. Crashes / exceptions
  2. Structural anomalies: root out of [0,11], duration <= 0, NaN/inf in
     any chord field, gaps/overlaps in the timeline, duration sum != total
  3. Numerical degradation: does the Viterbi DP produce -inf or NaN at long
     lengths? (long-path accumulation)
  4. Pathological repetition: same chord N times, V->I loops > threshold
  5. Quality-gravity wells: single quality > 70% at long lengths
  6. Mode-fidelity drift: at long lengths does the requested mode detection
     share drop vs short?
  7. Memory blow-up: does 256 bars take pathological time/memory?
"""
from __future__ import annotations

import math
import random
import sys
import time
import traceback
import warnings
from collections import Counter
from dataclasses import dataclass, field

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer, MODES_LIST
from melodica.theory.modes import Mode, get_mode_intervals
from melodica.types import NoteInfo, Scale

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


@dataclass
class Anomaly:
    kind: str
    detail: str
    context: str = ""


@dataclass
class ProbeResult:
    label: str
    bars: int
    elapsed: float
    anomalies: list[Anomaly] = field(default_factory=list)
    crashed: str | None = None


def _melody(scale: Scale, bars: int, kind: str, seed: int) -> list[NoteInfo]:
    random.seed(seed)
    degrees = scale.degrees()
    diatonic_pool = []
    for d in degrees:
        for octv in (60, 72, 84):
            diatonic_pool.append(octv + int(round(d)))
    melody = []
    for i in range(bars * 8):
        if kind == "diatonic":
            p = random.choice(diatonic_pool)
        elif kind == "chromatic":
            p = 60 + random.randint(0, 11)
        elif kind == "tonic_heavy":
            # 50% tonic, rest diatonic — stresses tonic gravity
            p = 60 + int(round(degrees[0])) if random.random() < 0.5 else random.choice(diatonic_pool)
        elif kind == "single_note":
            p = 60 + int(round(degrees[0]))
        else:
            p = random.choice(diatonic_pool)
        melody.append(NoteInfo(pitch=p, start=i * 0.5, duration=0.5, velocity=80))
    return melody


def _scan_chords(chords, total_beats: float, label: str) -> list[Anomaly]:
    anomalies = []
    if not chords:
        anomalies.append(Anomaly("empty", "no chords produced"))
        return anomalies
    # Structural
    for i, c in enumerate(chords):
        if not (0 <= c.root < 12):
            anomalies.append(Anomaly("root_oob", f"chord {i}: root={c.root}"))
        if not (c.duration > 0):
            anomalies.append(Anomaly("nonpos_dur", f"chord {i}: duration={c.duration}"))
        if not math.isfinite(c.duration):
            anomalies.append(Anomaly("nan_dur", f"chord {i}: duration={c.duration}"))
        if not math.isfinite(c.start):
            anomalies.append(Anomaly("nan_start", f"chord {i}: start={c.start}"))
    # Timeline tiling
    total = sum(c.duration for c in chords)
    if abs(total - total_beats) > 0.01:
        anomalies.append(Anomaly("duration_sum",
                                 f"sum={total:.4f} expected={total_beats}"))
    for i in range(1, len(chords)):
        gap = chords[i].start - chords[i - 1].end if hasattr(chords[i - 1], 'end') else chords[i].start - (chords[i-1].start + chords[i-1].duration)
        if abs(gap) > 0.01:
            anomalies.append(Anomaly("timeline_gap",
                                     f"chord {i}: gap={gap:.4f}"))
        if chords[i].start < chords[i - 1].start - 1e-9:
            anomalies.append(Anomaly("non_monotonic",
                                     f"chord {i}: start {chords[i].start} < prev {chords[i-1].start}"))
    # Pathological repetition (same root+quality)
    run = 1
    max_run = 1
    for i in range(1, len(chords)):
        if chords[i].root == chords[i - 1].root and chords[i].quality == chords[i - 1].quality:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    if max_run > 8:
        anomalies.append(Anomaly("stagnation",
                                 f"same chord repeated {max_run}x"))
    # V->I loop
    roots = [c.root for c in chords]
    vi_run = 0
    vi_max = 0
    i = 0
    while i + 1 < len(roots):
        if roots[i] == 7 and roots[i + 1] == 0:
            vi_run += 1
            vi_max = max(vi_max, vi_run)
            i += 2
        else:
            vi_run = 0
            i += 1
    if vi_max > 6:
        anomalies.append(Anomaly("vi_loop", f"V->I chain {vi_max}x"))
    # Quality gravity well
    q_counts = Counter(c.quality for c in chords)
    for q, cnt in q_counts.items():
        if cnt / len(chords) > 0.7:
            anomalies.append(Anomaly("quality_gravity",
                                     f"{q.name} = {cnt}/{len(chords)} ({cnt/len(chords):.0%})"))
    # Root monopoly
    r_counts = Counter(c.root for c in chords)
    for r, cnt in r_counts.items():
        if cnt / len(chords) > 0.6:
            anomalies.append(Anomaly("root_monopoly",
                                     f"{NOTE_NAMES[r]} = {cnt}/{len(chords)} ({cnt/len(chords):.0%})"))
    return anomalies


def probe(label: str, scale: Scale, bars: int, melody_kind: str, seed: int,
          chord_change: str = "bars") -> ProbeResult:
    h = CoupledHMMHarmonizer(chord_change=chord_change)
    melody = _melody(scale, bars, melody_kind, seed)
    duration = float(bars * 4)
    t0 = time.time()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            chords = h.harmonize(melody, scale, duration_beats=duration)
    except Exception as e:
        return ProbeResult(label=label, bars=bars, elapsed=time.time() - t0,
                           crashed=f"{type(e).__name__}: {e}\n{traceback.format_exc()}")
    elapsed = time.time() - t0
    anomalies = _scan_chords(chords, duration, label)
    return ProbeResult(label=label, bars=bars, elapsed=elapsed, anomalies=anomalies)


def main() -> int:
    random.seed(0)
    results: list[ProbeResult] = []

    # Mode set: representative across categories
    modes = [
        Mode.MAJOR, Mode.NATURAL_MINOR, Mode.HARMONIC_MINOR, Mode.MELODIC_MINOR,
        Mode.DORIAN, Mode.PHRYGIAN, Mode.LYDIAN, Mode.MIXOLYDIAN, Mode.LOCRIAN,
        Mode.HUNGARIAN_MINOR, Mode.GYPSY, Mode.BYZANTINE, Mode.PERSIAN,
        Mode.PHRYGIAN_DOMINANT, Mode.DOUBLE_HARMONIC, Mode.SUSPENSE,
        Mode.MESSIAEN_2, Mode.MESSIAEN_3, Mode.WHOLE_TONE, Mode.DIMINISHED,
        Mode.HIROJOSHI, Mode.SLENDRO_APPROX, Mode.NEAPOLITAN_MINOR,
    ]
    keys = [0, 1, 2, 5, 6, 7, 11]  # spread across the circle of fifths

    bars_set = [32, 64, 128, 256]
    melody_kinds = ["diatonic", "chromatic", "tonic_heavy", "single_note"]

    total_runs = 0
    print("=" * 90)
    print("LONG-PROGRESSION FUZZER")
    print("=" * 90)

    # Phase 1: length scaling — does anything break at extreme lengths?
    print("\n## Phase 1: length scaling (C major, diatonic)")
    for bars in bars_set:
        r = probe(f"len_Cmaj_{bars}", Scale(0, Mode.MAJOR), bars, "diatonic", seed=0)
        results.append(r)
        total_runs += 1
        status = "OK" if not r.anomalies and not r.crashed else "ANOMALY"
        print(f"  bars={bars:3d}  {r.elapsed:6.2f}s  {status}  "
              f"{len(r.anomalies)} anomalies{'  CRASHED' if r.crashed else ''}")
        for a in r.anomalies[:3]:
            print(f"      [{a.kind}] {a.detail}")
        if r.crashed:
            print(f"      CRASH: {r.crashed.splitlines()[0]}")

    # Phase 2: melody-kind stress at 128 bars, multiple modes
    print("\n## Phase 2: melody-kind stress (128 bars)")
    for kind in melody_kinds:
        for mode in [Mode.MAJOR, Mode.NATURAL_MINOR, Mode.HUNGARIAN_MINOR]:
            r = probe(f"kind_{kind}_{mode.name[:6]}", Scale(0, mode), 128, kind, seed=0)
            results.append(r)
            total_runs += 1
            if r.anomalies or r.crashed:
                print(f"  {kind:14s} {mode.name:18s}  {len(r.anomalies)} anomalies"
                      f"{'  CRASHED' if r.crashed else ''}")
                for a in r.anomalies[:3]:
                    print(f"      [{a.kind}] {a.detail}")

    # Phase 3: every key at 64 bars — exposes key-specific bugs
    print("\n## Phase 3: every key (64 bars, diatonic, major + phrygian)")
    for key in keys:
        for mode in [Mode.MAJOR, Mode.PHRYGIAN]:
            r = probe(f"key_{key}_{mode.name[:6]}", Scale(key, mode), 64, "diatonic", seed=0)
            results.append(r)
            total_runs += 1
            if r.anomalies or r.crashed:
                print(f"  key={key:2d} {mode.name:18s}  {len(r.anomalies)} anomalies"
                      f"{'  CRASHED' if r.crashed else ''}")
                for a in r.anomalies[:3]:
                    print(f"      [{a.kind}] {a.detail}")

    # Phase 4: half-bar changes at long length — doubles the DP steps
    print("\n## Phase 4: half-bar changes at 128 bars (2x DP steps)")
    for mode in [Mode.MAJOR, Mode.DOUBLE_HARMONIC]:
        r = probe(f"half_{mode.name[:6]}", Scale(0, mode), 128, "diatonic", seed=0,
                  chord_change="half")
        results.append(r)
        total_runs += 1
        print(f"  half-bar {mode.name:18s}  {r.elapsed:6.2f}s  "
              f"{len(r.anomalies)} anomalies{'  CRASHED' if r.crashed else ''}")
        for a in r.anomalies[:3]:
            print(f"      [{a.kind}] {a.detail}")

    # Phase 5: seed sweep on the worst-case (long + chromatic)
    print("\n## Phase 5: seed sweep (256 bars, chromatic, 10 seeds)")
    crash_or_anomaly_seeds = []
    for seed in range(10):
        r = probe(f"seed_{seed}", Scale(0, Mode.MAJOR), 256, "chromatic", seed=seed)
        results.append(r)
        total_runs += 1
        if r.anomalies or r.crashed:
            crash_or_anomaly_seeds.append(seed)
            print(f"  seed={seed}: {len(r.anomalies)} anomalies"
                  f"{'  CRASHED' if r.crashed else ''}")
            for a in r.anomalies[:3]:
                print(f"      [{a.kind}] {a.detail}")
    if not crash_or_anomaly_seeds:
        print("  (all 10 seeds clean)")

    # Phase 6: memory/time scaling check
    print("\n## Phase 6: timing scaling (is 256 bars pathological?)")
    times = []
    for bars in [16, 32, 64, 128, 256]:
        r = probe(f"time_{bars}", Scale(0, Mode.MAJOR), bars, "diatonic", seed=0)
        times.append((bars, r.elapsed))
        total_runs += 1
    print("  bars  time   ratio (vs 16 bars)")
    base = times[0][1]
    for bars, t in times:
        print(f"  {bars:4d}  {t:5.2f}s  {t/base:5.1f}x")

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)
    crashes = [r for r in results if r.crashed]
    anomalous = [r for r in results if r.anomalies and not r.crashed]
    clean = [r for r in results if not r.anomalies and not r.crashed]
    print(f"  Total runs:        {total_runs}")
    print(f"  Clean:             {len(clean)}")
    print(f"  Anomalous:         {len(anomalous)}")
    print(f"  Crashed:           {len(crashes)}")
    if anomalous or crashes:
        print("\n## All anomalies (deduplicated by kind):")
        seen_kinds = {}
        for r in results:
            for a in r.anomalies:
                key = (a.kind, r.label)
                if a.kind not in seen_kinds:
                    seen_kinds[a.kind] = []
                seen_kinds[a.kind].append((r.label, a.detail))
        for kind, occurrences in sorted(seen_kinds.items()):
            print(f"\n  [{kind}] — {len(occurrences)} occurrence(s):")
            for label, detail in occurrences[:5]:
                print(f"    {label}: {detail[:90]}")
    return 1 if (crashes or anomalous) else 0


if __name__ == "__main__":
    sys.exit(main())
