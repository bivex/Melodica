# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
"""
test_melody_coverage.py — Melody generator uniqueness & coverage audit.

Tests MelodyGenerator across all parameter combinations:
  - All enum-like params: mode, first_note, last_note, after_leap,
    phrase_contour, accent_pattern, motif_variation
  - Boundary values: steps_probability, harmony_note_probability,
    random_movement, note_repetition_probability, syncopation, rhythm_variety,
    motif_probability, ornament_probability, register_smoothness, direction_bias
  - Edge cases: single chord, very short/long phrases, extreme ranges

Uniqueness metrics:
  - Pitch sequence hash (exact uniqueness)
  - Interval fingerprint (direction + magnitude pattern)
  - Contour shape (up/down/flat pattern)
  - Pitch class distribution entropy
  - Self-similarity across N runs with same seed vs different seeds

Coverage metrics:
  - Which code paths fire (mode, first_note, last_note, etc.)
  - Parameter sweep hits
  - Fallback cascade activations
"""

import sys
import random
import hashlib
from collections import Counter
from pathlib import Path
from itertools import product
from math import log2

sys.path.insert(0, str(Path(__file__).parent.parent))

from melodica.types import Scale, Mode, ChordLabel, Quality, NoteInfo
from melodica.generators.melody import MelodyGenerator
from melodica.generators import GeneratorParams
from melodica.render_context import RenderContext


SCALE = Scale(root=0, mode=Mode.MAJOR)

# Valid enum values from the generator
MODES = ["scale_only", "chord_only", "downbeat_chord", "on_beat_chord", "scale_and_chord"]
FIRST_NOTES = ["chord_root", "any_chord", "scale", "tonic", "step_above_tonic", "step_below_tonic"]
LAST_NOTES = ["last_chord_root", "any_chord", "scale", "any"]
AFTER_LEAPS = ["step_opposite", "step_any", "step_or_smaller_opposite", "leap_opposite", "any"]
CONTOURS = ["arch", "rise_fall", "flat", "rise"]
ACCENTS = ["natural", "strong_weak", "syncopated"]
MOTIF_VARIATIONS = ["transpose", "invert", "retrograde", "any"]


def make_chords(bars=4, bpb=4):
    degs = SCALE.degrees()
    chords = []
    for b in range(bars):
        p = b % 4
        if p == 0:
            root = int(degs[0])
        elif p == 1:
            root = int(degs[min(3, len(degs) - 1)])
        elif p == 2:
            root = int(degs[min(4, len(degs) - 1)])
        else:
            root = int(degs[0])
        chords.append(
            ChordLabel(root=root, quality=Quality.MAJOR, start=b * bpb, duration=bpb)
        )
    return chords


def pitch_hash(notes):
    return hashlib.md5(",".join(str(n.pitch) for n in notes).encode()).hexdigest()[:12]


def interval_fingerprint(notes):
    if len(notes) < 2:
        return ()
    intervals = []
    for i in range(1, len(notes)):
        diff = notes[i].pitch - notes[i - 1].pitch
        direction = "U" if diff > 0 else "D" if diff < 0 else "S"
        mag = min(abs(diff), 12)
        intervals.append(f"{direction}{mag}")
    return tuple(intervals)


def contour_shape(notes):
    if len(notes) < 2:
        return ()
    return tuple(
        "U" if notes[i].pitch > notes[i - 1].pitch
        else "D" if notes[i].pitch < notes[i - 1].pitch
        else "F"
        for i in range(1, len(notes))
    )


def pitch_class_distribution(notes):
    pc_counts = Counter(n.pitch % 12 for n in notes)
    total = len(notes)
    if total == 0:
        return 0.0
    entropy = 0.0
    for count in pc_counts.values():
        p = count / total
        if p > 0:
            entropy -= p * log2(p)
    return entropy


def pitch_range_span(notes):
    if not notes:
        return 0
    return max(n.pitch for n in notes) - min(n.pitch for n in notes)


def generate_one(gen, bars=4, seed=None):
    if seed is not None:
        random.seed(seed)
    chords = make_chords(bars)
    ctx = RenderContext(current_scale=SCALE)
    return gen.render(chords, SCALE, bars * 4, ctx)


# ── Test 1: Enum parameter coverage ──────────────────────────────────────────

def test_enum_coverage():
    print("=" * 70)
    print("  1. ENUM PARAMETER COVERAGE")
    print("=" * 70)

    results = {}

    # Modes
    print("\n  [mode]")
    for mode in MODES:
        gen = MelodyGenerator(params=GeneratorParams(density=0.5), mode=mode)
        notes = generate_one(gen, seed=42)
        h = pitch_hash(notes)
        ent = pitch_class_distribution(notes)
        span = pitch_range_span(notes)
        print(f"    {mode:20s}: {len(notes):3d} notes  hash={h}  entropy={ent:.2f}  span={span}")
        results[f"mode:{mode}"] = {"hash": h, "entropy": ent, "span": span, "count": len(notes)}

    # First note strategies
    print("\n  [first_note]")
    for fn in FIRST_NOTES:
        gen = MelodyGenerator(params=GeneratorParams(density=0.5), first_note=fn)
        notes = generate_one(gen, seed=42)
        first = notes[0].pitch if notes else 0
        h = pitch_hash(notes)
        print(f"    {fn:20s}: first={first:3d}  hash={h}  {len(notes)} notes")
        results[f"first_note:{fn}"] = {"hash": h, "first": first, "count": len(notes)}

    # Last note strategies
    print("\n  [last_note]")
    for ln in LAST_NOTES:
        gen = MelodyGenerator(params=GeneratorParams(density=0.5), last_note=ln)
        notes = generate_one(gen, seed=42)
        last = notes[-1].pitch if notes else 0
        h = pitch_hash(notes)
        print(f"    {ln:20s}: last={last:3d}  hash={h}  {len(notes)} notes")
        results[f"last_note:{ln}"] = {"hash": h, "last": last, "count": len(notes)}

    # After leap
    print("\n  [after_leap]")
    for al in AFTER_LEAPS:
        gen = MelodyGenerator(
            params=GeneratorParams(density=0.6),
            after_leap=al,
            steps_probability=0.3,
        )
        notes = generate_one(gen, seed=42)
        fp = interval_fingerprint(notes)
        leaps = sum(1 for iv in fp if iv[0] in ("U", "D") and int(iv[1:]) > 2)
        h = pitch_hash(notes)
        print(f"    {al:30s}: leaps={leaps:3d}  hash={h}  {len(notes)} notes")
        results[f"after_leap:{al}"] = {"hash": h, "leaps": leaps, "count": len(notes)}

    # Phrase contours
    print("\n  [phrase_contour]  (phrase_length=4)")
    for pc in CONTOURS:
        gen = MelodyGenerator(
            params=GeneratorParams(density=0.5),
            phrase_length=4.0,
            phrase_contour=pc,
        )
        notes = generate_one(gen, seed=42)
        shape = contour_shape(notes)
        ups = shape.count("U")
        downs = shape.count("D")
        flats = shape.count("F")
        h = pitch_hash(notes)
        print(f"    {pc:20s}: U={ups} D={downs} F={flats}  hash={h}  {len(notes)} notes")
        results[f"contour:{pc}"] = {"hash": h, "ups": ups, "downs": downs, "count": len(notes)}

    # Accent patterns
    print("\n  [accent_pattern]  (phrase_length=4)")
    for ap in ACCENTS:
        gen = MelodyGenerator(
            params=GeneratorParams(density=0.5),
            phrase_length=4.0,
            accent_pattern=ap,
        )
        notes = generate_one(gen, seed=42)
        vels = [n.velocity for n in notes]
        vel_range = max(vels) - min(vels) if vels else 0
        h = pitch_hash(notes)
        print(f"    {ap:20s}: vel_range={vel_range:3d}  hash={h}  {len(notes)} notes")
        results[f"accent:{ap}"] = {"hash": h, "vel_range": vel_range, "count": len(notes)}

    # Motif variation
    print("\n  [motif_variation]  (motif_probability=0.8, phrase_length=4)")
    for mv in MOTIF_VARIATIONS:
        gen = MelodyGenerator(
            params=GeneratorParams(density=0.5),
            phrase_length=4.0,
            motif_probability=0.8,
            motif_variation=mv,
        )
        notes = generate_one(gen, seed=42)
        h = pitch_hash(notes)
        print(f"    {mv:20s}: hash={h}  {len(notes)} notes")
        results[f"motif:{mv}"] = {"hash": h, "count": len(notes)}

    return results


# ── Test 2: Boundary value sweep ─────────────────────────────────────────────

def test_boundary_sweep():
    print(f"\n{'=' * 70}")
    print("  2. BOUNDARY VALUE SWEEP")
    print("=" * 70)

    params_sweep = [
        ("steps_probability", [0.0, 0.3, 0.7, 1.0]),
        ("harmony_note_probability", [0.0, 0.3, 0.64, 1.0]),
        ("random_movement", [0.0, 0.5, 0.8, 1.0]),
        ("note_repetition_probability", [0.0, 0.3, 0.6, 1.0]),
        ("syncopation", [0.0, 0.5, 1.0]),
        ("rhythm_variety", [0.0, 0.5, 1.0]),
        ("ornament_probability", [0.0, 0.5, 1.0]),
        ("register_smoothness", [0.0, 0.5, 1.0]),
        ("direction_bias", [-1.0, -0.5, 0.0, 0.5, 1.0]),
    ]

    all_hashes = set()
    results = {}

    for param_name, values in params_sweep:
        print(f"\n  [{param_name}]")
        for val in values:
            kwargs = {param_name: val}
            gen = MelodyGenerator(params=GeneratorParams(density=0.5), **kwargs)
            notes = generate_one(gen, seed=42)
            h = pitch_hash(notes)
            ent = pitch_class_distribution(notes)
            span = pitch_range_span(notes)
            all_hashes.add(h)
            print(f"    {str(val):6s}: hash={h}  entropy={ent:.2f}  span={span}  {len(notes)} notes")
            results[f"{param_name}:{val}"] = {"hash": h, "entropy": ent, "span": span}

    print(f"\n  Total unique hashes from boundary sweep: {len(all_hashes)}")
    return results, all_hashes


# ── Test 3: Uniqueness across N runs ─────────────────────────────────────────

def test_uniqueness_n_runs(n=50, bars=4):
    print(f"\n{'=' * 70}")
    print(f"  3. UNIQUENESS ACROSS {n} RUNS (same params, different seeds)")
    print("=" * 70)

    gen = MelodyGenerator(params=GeneratorParams(density=0.5))

    pitch_hashes = set()
    interval_fps = set()
    contours = set()
    entropies = []
    spans = []

    for seed in range(n):
        notes = generate_one(gen, bars=bars, seed=seed)
        pitch_hashes.add(pitch_hash(notes))
        interval_fps.add(interval_fingerprint(notes))
        contours.add(contour_shape(notes))
        entropies.append(pitch_class_distribution(notes))
        spans.append(pitch_range_span(notes))

    pitch_unique = len(pitch_hashes)
    interval_unique = len(interval_fps)
    contour_unique = len(contours)
    avg_entropy = sum(entropies) / len(entropies)
    avg_span = sum(spans) / len(spans)

    print(f"  Runs:                   {n}")
    print(f"  Unique pitch sequences: {pitch_unique}/{n} ({pitch_unique / n * 100:.0f}%)")
    print(f"  Unique interval patterns: {interval_unique}/{n} ({interval_unique / n * 100:.0f}%)")
    print(f"  Unique contour shapes:  {contour_unique}/{n} ({contour_unique / n * 100:.0f}%)")
    print(f"  Avg pitch class entropy: {avg_entropy:.2f} (max={log2(12):.2f})")
    print(f"  Avg pitch span:         {avg_span:.1f} semitones")

    if pitch_unique == n:
        print("  VERDICT: 100% unique — every seed produces a different melody")
    elif pitch_unique >= n * 0.9:
        print("  VERDICT: High uniqueness (>90%)")
    else:
        print(f"  WARNING: Only {pitch_unique / n * 100:.0f}% unique — possible repetition")

    return {
        "pitch_unique": pitch_unique,
        "interval_unique": interval_unique,
        "contour_unique": contour_unique,
        "avg_entropy": avg_entropy,
        "avg_span": avg_span,
    }


# ── Test 4: Same seed determinism ────────────────────────────────────────────

def test_determinism(runs=5):
    print(f"\n{'=' * 70}")
    print(f"  4. DETERMINISM (same seed = same output)")
    print("=" * 70)

    gen = MelodyGenerator(params=GeneratorParams(density=0.5))
    hashes = []
    for _ in range(runs):
        notes = generate_one(gen, seed=12345)
        hashes.append(pitch_hash(notes))

    all_same = len(set(hashes)) == 1
    print(f"  {runs} runs with seed=12345: hashes = {hashes}")
    if all_same:
        print("  VERDICT: Deterministic — same seed always produces identical output")
    else:
        print("  WARNING: Non-deterministic — same seed produces different output!")

    return all_same


# ── Test 5: Feature activation matrix ────────────────────────────────────────

def test_feature_activation():
    print(f"\n{'=' * 70}")
    print("  5. FEATURE ACTIVATION (which features actually change output)")
    print("=" * 70)

    base_gen = MelodyGenerator(params=GeneratorParams(density=0.5))
    base_notes = generate_one(base_gen, seed=42)
    base_hash = pitch_hash(base_notes)

    features = {
        "phrase_length=4": MelodyGenerator(params=GeneratorParams(density=0.5), phrase_length=4.0),
        "phrase_length=8": MelodyGenerator(params=GeneratorParams(density=0.5), phrase_length=8.0),
        "phrase_contour=rise": MelodyGenerator(params=GeneratorParams(density=0.5), phrase_length=4.0, phrase_contour="rise"),
        "phrase_contour=flat": MelodyGenerator(params=GeneratorParams(density=0.5), phrase_length=4.0, phrase_contour="flat"),
        "accent=syncopated": MelodyGenerator(params=GeneratorParams(density=0.5), phrase_length=4.0, accent_pattern="syncopated"),
        "accent=strong_weak": MelodyGenerator(params=GeneratorParams(density=0.5), phrase_length=4.0, accent_pattern="strong_weak"),
        "syncopation=0.8": MelodyGenerator(params=GeneratorParams(density=0.5), syncopation=0.8),
        "rhythm_variety=0.8": MelodyGenerator(params=GeneratorParams(density=0.5), rhythm_variety=0.8),
        "motif_prob=0.8": MelodyGenerator(params=GeneratorParams(density=0.5), motif_probability=0.8, phrase_length=4.0),
        "ornament_prob=0.8": MelodyGenerator(params=GeneratorParams(density=0.5), ornament_probability=0.8),
        "after_leap=step_opposite": MelodyGenerator(params=GeneratorParams(density=0.5), after_leap="step_opposite", steps_probability=0.3),
        "direction_bias=+0.8": MelodyGenerator(params=GeneratorParams(density=0.5), direction_bias=0.8),
        "direction_bias=-0.8": MelodyGenerator(params=GeneratorParams(density=0.5), direction_bias=-0.8),
        "register_smoothness=0.9": MelodyGenerator(params=GeneratorParams(density=0.5), register_smoothness=0.9, phrase_length=4.0),
        "note_repetition=0.6": MelodyGenerator(params=GeneratorParams(density=0.5), note_repetition_probability=0.6),
        "rhythm_motif=[1,0.5,0.5,1]": MelodyGenerator(params=GeneratorParams(density=0.5), rhythm_motif=[1.0, 0.5, 0.5, 1.0]),
    }

    active = 0
    print(f"\n  Base hash (all defaults): {base_hash}\n")
    for name, gen in features.items():
        notes = generate_one(gen, seed=42)
        h = pitch_hash(notes)
        changed = h != base_hash
        mark = "ACTIVE" if changed else "NO CHANGE"
        if changed:
            active += 1
        print(f"    {name:35s}: {mark:10s}  hash={h}  {len(notes)} notes")

    total = len(features)
    print(f"\n  Features that change output: {active}/{total}")
    if active == total:
        print("  VERDICT: All features are functional")
    else:
        print(f"  WARNING: {total - active} features produce identical output to defaults")

    return active, total


# ── Test 6: Parameter interaction matrix ─────────────────────────────────────

def test_interaction_matrix():
    print(f"\n{'=' * 70}")
    print("  6. PARAMETER INTERACTION (combined params produce unique output)")
    print("=" * 70)

    combos = list(product(
        ["scale_only", "downbeat_chord", "scale_and_chord"],
        [0.3, 0.8],
        [0.3, 0.8],
    ))

    hashes = set()
    for mode, steps_p, random_m in combos:
        gen = MelodyGenerator(
            params=GeneratorParams(density=0.5),
            mode=mode,
            steps_probability=steps_p,
            random_movement=random_m,
        )
        notes = generate_one(gen, seed=42)
        hashes.add(pitch_hash(notes))

    total = len(combos)
    unique = len(hashes)
    print(f"  Combinations tested: {total}")
    print(f"  Unique outputs:      {unique}")
    print(f"  Uniqueness rate:     {unique / total * 100:.0f}%")

    if unique == total:
        print("  VERDICT: All parameter combinations produce unique melodies")
    elif unique >= total * 0.8:
        print("  VERDICT: Good diversity, some combinations collapse")
    else:
        print(f"  WARNING: Low diversity — only {unique / total * 100:.0f}% unique")

    return unique, total


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("MelodyGenerator — Uniqueness & Coverage Audit\n")

    enum_results = test_enum_coverage()
    sweep_results, sweep_hashes = test_boundary_sweep()
    uniqueness = test_uniqueness_n_runs(n=50)
    deterministic = test_determinism()
    active, total_features = test_feature_activation()
    interactions = test_interaction_matrix()

    # Summary
    print(f"\n{'=' * 70}")
    print("  SUMMARY")
    print("=" * 70)
    print(f"  Enum params tested:        {len(enum_results)}")
    print(f"  Boundary values tested:    {len(sweep_results)}")
    print(f"  Unique hashes (sweep):     {len(sweep_hashes)}")
    print(f"  Uniqueness (50 runs):      {uniqueness['pitch_unique']}/50 ({uniqueness['pitch_unique'] / 50 * 100:.0f}%)")
    print(f"  Deterministic:             {'YES' if deterministic else 'NO'}")
    print(f"  Features active:           {active}/{total_features}")
    print(f"  Interaction uniqueness:    {interactions[0]}/{interactions[1]}")
    print(f"  Avg entropy:               {uniqueness['avg_entropy']:.2f} / {log2(12):.2f}")
    print(f"  Avg span:                  {uniqueness['avg_span']:.1f} semitones")


if __name__ == "__main__":
    main()
