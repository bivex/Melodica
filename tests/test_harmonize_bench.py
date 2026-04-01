"""
tests/test_harmonize_bench.py — Benchmark all harmonization algorithms.

Compares quality, speed, and musicality of:
1. FunctionalHarmonizer
2. RuleBasedHarmonizer
3. HMMHarmonizer
4. GraphSearchHarmonizer
"""

import time
import statistics
from melodica.types import NoteInfo, Scale, Mode, Quality
from melodica.harmonize import (
    FunctionalHarmonizer,
    RuleBasedHarmonizer,
    HMMHarmonizer,
    HMM2Harmonizer,
    HMM3Harmonizer,
    GraphSearchHarmonizer,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _make_melody(notes_per_bar: int = 4, bars: int = 4) -> list[NoteInfo]:
    """Generate a realistic C major melody."""
    # Scale tones: C D E F G A B
    scale_pitches = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79]
    melody = []
    for bar in range(bars):
        for beat in range(notes_per_bar):
            idx = (bar * notes_per_bar + beat) % len(scale_pitches)
            melody.append(
                NoteInfo(
                    pitch=scale_pitches[idx],
                    start=round(bar * 4.0 + beat * (4.0 / notes_per_bar), 6),
                    duration=round(4.0 / notes_per_bar * 0.9, 6),
                    velocity=80,
                )
            )
    return melody


def _melody_chord_fit(melody: list, chords: list) -> float:
    """Score: how many melody notes fit their chord (0-1)."""
    if not chords or not melody:
        return 0.0
    total = 0
    fit = 0
    for chord in chords:
        chord_pcs = set(chord.pitch_classes())
        notes_in_span = [n for n in melody if chord.start <= n.start < chord.start + chord.duration]
        for n in notes_in_span:
            total += 1
            if n.pitch % 12 in chord_pcs:
                fit += 1
    return fit / max(1, total)


def _voice_leading_score(chords: list) -> float:
    """Score: how smooth the voice leading is (0-1, higher = smoother)."""
    if len(chords) < 2:
        return 1.0
    total_dist = 0.0
    for i in range(len(chords) - 1):
        a = chords[i].pitch_classes()
        b = chords[i + 1].pitch_classes()
        if a and b:
            # Min semitone movement between chord roots
            dist = min(abs(a[0] - b[0]) % 12, 12 - abs(a[0] - b[0]) % 12)
            total_dist += dist
    avg_dist = total_dist / (len(chords) - 1)
    # Normalize: 0 semitones = 1.0, 6 semitones = 0.0
    return max(0.0, 1.0 - avg_dist / 6.0)


def _chord_variety(chords: list) -> float:
    """Score: how many different chord degrees are used (0-1)."""
    if not chords:
        return 0.0
    degrees = set(c.degree for c in chords)
    return len(degrees) / 7.0


def _functional_progression_score(chords: list) -> float:
    """Score: how well the progression follows functional rules (0-1)."""
    if len(chords) < 2:
        return 1.0
    good_transitions = {(1, 4), (1, 5), (4, 5), (5, 1), (5, 6), (6, 2), (2, 5), (6, 4), (3, 6)}
    total = 0
    good = 0
    for i in range(len(chords) - 1):
        pair = (chords[i].degree, chords[i + 1].degree)
        total += 1
        if pair in good_transitions:
            good += 1
    return good / max(1, total)


def _benchmark(harmonizer, melody, scale, duration, runs=20):
    """Run harmonizer and collect metrics."""
    times = []
    all_chords = []
    for _ in range(runs):
        t0 = time.perf_counter()
        chords = harmonizer.harmonize(melody, scale, duration)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        all_chords.append(chords)

    # Use first run for quality metrics
    chords = all_chords[0]
    return {
        "name": type(harmonizer).__name__,
        "avg_time_ms": statistics.mean(times) * 1000,
        "chords_count": len(chords) if chords else 0,
        "melody_fit": _melody_chord_fit(melody, chords),
        "voice_leading": _voice_leading_score(chords),
        "chord_variety": _chord_variety(chords),
        "functional_score": _functional_progression_score(chords),
        "degrees": [c.degree for c in chords] if chords else [],
    }


def test_benchmark_all_algorithms():
    """Compare all 4 harmonization algorithms."""
    melody = _make_melody(notes_per_bar=4, bars=4)
    duration = 16.0

    algorithms = [
        ("Functional", FunctionalHarmonizer()),
        ("Rule-Based", RuleBasedHarmonizer(expectedness="expected")),
        ("HMM 1.0", HMMHarmonizer()),
        ("HMM 2.0", HMM2Harmonizer()),
        ("HMM 3.0", HMM3Harmonizer()),
        ("Graph Search", GraphSearchHarmonizer()),
    ]

    print("\n" + "=" * 80)
    print("HARMONIZATION ALGORITHM BENCHMARK")
    print("=" * 80)
    print(f"Melody: {len(melody)} notes over {duration} beats, C major")
    print("-" * 80)

    results = []
    for name, algo in algorithms:
        r = _benchmark(algo, melody, C_MAJOR, duration, runs=20)
        results.append(r)

    # Print results table
    print(
        f"{'Algorithm':<18} {'Time(ms)':>10} {'Chords':>8} {'Melody%':>8} {'Voice%':>8} {'Variety%':>9} {'Func%':>7}"
    )
    print("-" * 80)
    for r in results:
        print(
            f"{r['name']:<18} "
            f"{r['avg_time_ms']:>10.2f} "
            f"{r['chords_count']:>8} "
            f"{r['melody_fit'] * 100:>7.1f}% "
            f"{r['voice_leading'] * 100:>7.1f}% "
            f"{r['chord_variety'] * 100:>8.1f}% "
            f"{r['functional_score'] * 100:>6.1f}%"
        )

    # Composite score: weighted average of all quality metrics
    print("-" * 80)
    print(
        f"{'Algorithm':<18} {'Melody':>8} {'Voice':>8} {'Variety':>8} {'Func':>8} {'Speed':>8} {'TOTAL':>8}"
    )
    print("-" * 80)

    best_name = ""
    best_total = -1
    for r in results:
        speed_score = 1.0 - min(r["avg_time_ms"] / 100.0, 1.0)  # faster = better
        total = (
            r["melody_fit"] * 0.35
            + r["voice_leading"] * 0.25
            + r["chord_variety"] * 0.15
            + r["functional_score"] * 0.15
            + speed_score * 0.10
        )
        print(
            f"{r['name']:<18} "
            f"{r['melody_fit']:>8.3f} "
            f"{r['voice_leading']:>8.3f} "
            f"{r['chord_variety']:>8.3f} "
            f"{r['functional_score']:>8.3f} "
            f"{speed_score:>8.3f} "
            f"{total:>8.3f}"
        )
        if total > best_total:
            best_total = total
            best_name = r["name"]

    print("=" * 80)
    print(f"BEST DEFAULT: {best_name} (score={best_total:.3f})")
    print("=" * 80)

    # Print chord progressions
    print("\nChord progressions (degrees):")
    for r in results:
        print(f"  {r['name']:<18}: {' → '.join(str(d) for d in r['degrees'])}")

    # Assertions
    assert all(r["melody_fit"] > 0.3 for r in results), (
        "All algorithms should fit >30% melody notes"
    )
    assert all(r["chords_count"] > 0 for r in results), "All algorithms should produce chords"


def test_benchmark_different_melodies():
    """Test algorithms on different melody densities."""
    print("\n" + "=" * 80)
    print("DENSITY COMPARISON")
    print("=" * 80)

    algorithms = [
        ("Functional", FunctionalHarmonizer()),
        ("Rule-Based", RuleBasedHarmonizer()),
        ("HMM 1.0", HMMHarmonizer()),
        ("HMM 2.0", HMM2Harmonizer()),
        ("HMM 3.0", HMM3Harmonizer()),
        ("Graph", GraphSearchHarmonizer()),
    ]

    for density in [2, 4, 8]:
        melody = _make_melody(notes_per_bar=density, bars=4)
        print(f"\n--- {density} notes/bar, {len(melody)} total notes ---")
        for name, algo in algorithms:
            r = _benchmark(algo, melody, C_MAJOR, 16.0, runs=10)
            print(
                f"  {name:<14}: "
                f"fit={r['melody_fit']:.2f} "
                f"voice={r['voice_leading']:.2f} "
                f"variety={r['chord_variety']:.2f} "
                f"time={r['avg_time_ms']:.1f}ms"
            )


def test_benchmark_8_bar_phrase():
    """Test on longer phrase (8 bars = 32 beats)."""
    melody = _make_melody(notes_per_bar=4, bars=8)
    duration = 32.0

    algorithms = [
        ("Functional", FunctionalHarmonizer()),
        ("Rule-Based", RuleBasedHarmonizer()),
        ("HMM 1.0", HMMHarmonizer()),
        ("HMM 2.0", HMM2Harmonizer()),
        ("HMM 3.0", HMM3Harmonizer()),
        ("Graph Search", GraphSearchHarmonizer()),
    ]

    print(f"\n{'=' * 60}")
    print(f"8-BAR PHRASE BENCHMARK ({len(melody)} notes, {duration} beats)")
    print(f"{'=' * 60}")

    for name, algo in algorithms:
        t0 = time.perf_counter()
        chords = algo.harmonize(melody, C_MAJOR, duration)
        elapsed = (time.perf_counter() - t0) * 1000
        fit = _melody_chord_fit(melody, chords)
        vl = _voice_leading_score(chords)
        print(f"  {name:<14}: {len(chords)} chords, fit={fit:.2f}, voice={vl:.2f}, {elapsed:.1f}ms")


if __name__ == "__main__":
    test_benchmark_all_algorithms()
    test_benchmark_different_melodies()
    test_benchmark_8_bar_phras
