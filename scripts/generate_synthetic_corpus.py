# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
Generate synthetic .ntc corpus for all 78 modes in MODE_DATABASE.
Each mode gets ~8 songs with diatonic progressions, producing ~600 songs total.
Output goes to tymoczko_code/Code/First step/synth_data/ in .ntc format.
"""

import random
from pathlib import Path
from melodica.theory.modes import MODE_DATABASE, get_mode_intervals, Mode

# 6 chord types for the expanded model
# Lookup by (third_offset, fifth_offset) from root
TRIAD_TYPES = {
    (4, 7): 0,   # Major
    (3, 7): 1,   # Minor
    (3, 6): 2,   # Diminished
    (4, 8): 3,   # Augmented
    (2, 7): 4,   # sus2
    (5, 7): 5,   # sus4
}

def classify_triad(intervals):
    """Classify (root, third, fifth) into one of 6 triad types."""
    root, third, fifth = intervals
    rel = ((third - root) % 12, (fifth - root) % 12)
    if rel in TRIAD_TYPES:
        return TRIAD_TYPES[rel]
    # Find nearest by interval distance
    best_type, best_dist = 0, 999
    for triad_key, t_idx in TRIAD_TYPES.items():
        dist = abs(rel[0] - triad_key[0]) + abs(rel[1] - triad_key[1])
        if dist < best_dist:
            best_dist = dist
            best_type = t_idx
    return best_type


def build_mode_triads(mode_intervals):
    """Build diatonic triads on each degree of a mode. Returns [(root_pc, type_idx)]."""
    n = len(mode_intervals)
    triads = []
    scale_pcs = [round(iv) % 12 for iv in mode_intervals]

    for i in range(n):
        root = scale_pcs[i]
        third = scale_pcs[(i + 2) % n]
        fifth = scale_pcs[(i + 4) % n]

        # For microtonal modes, round to nearest semitone
        root_iv = mode_intervals[i]
        third_iv = mode_intervals[(i + 2) % n]
        fifth_iv = mode_intervals[(i + 4) % n]

        # Use actual pitch classes
        root_pc = round(root_iv) % 12
        third_pc = round(third_iv) % 12
        fifth_pc = round(fifth_iv) % 12

        rel_third = (third_pc - root_pc) % 12
        rel_fifth = (fifth_pc - root_pc) % 12

        t_idx = classify_triad((0, rel_third, rel_fifth))
        triads.append((root_pc, t_idx))

    return triads


# Functional progression patterns (degree indices)
# Each tuple = (tonic, subdominant, dominant) degree indices
PROGRESSION_PATTERNS = [
    # Standard T-S-D-T
    [0, 3, 4, 0],
    [0, 3, 4, 0, 3, 4, 4, 0],
    # T-D-T-S
    [0, 4, 0, 3],
    # Minor i-VI-III-VII
    [0, 5, 2, 6],
    [0, 5, 2, 6, 0, 3, 4, 0],
    # Modal: i-iv-V-i
    [0, 3, 4, 0, 1, 3, 4, 0],
    # Long: i-VII-VI-V-i-iv-VII-V-i
    [0, 6, 5, 4, 0, 3, 6, 4, 0],
    # Pentatonic (5 degrees)
    [0, 2, 3, 4, 0],
    [0, 3, 4, 0, 2, 3, 4, 0],
    # Phrygian flavor: i-bII-VII-i
    [0, 1, 6, 0],
    # Expanded: i-iv-VII-III-VI-II-V-i
    [0, 3, 6, 2, 5, 1, 4, 0],
]


def generate_notes_for_chord(root_pc, type_idx, scale_pcs, n_notes=4):
    """Generate pitch classes for a chord beat, including passing tones from scale."""
    # Chord tones based on type
    chord_intervals = {
        0: [0, 4, 7],       # Major
        1: [0, 3, 7],       # Minor
        2: [0, 3, 6],       # Dim
        3: [0, 4, 8],       # Aug
        4: [0, 2, 7],       # sus2
        5: [0, 5, 7],       # sus4
    }
    intervals = chord_intervals.get(type_idx, [0, 4, 7])
    chord_pcs = [(root_pc + iv) % 12 for iv in intervals]

    notes = list(chord_pcs)

    # Add passing tones from scale (not chord tones)
    scale_passing = [pc for pc in scale_pcs if pc not in chord_pcs]
    if scale_passing and n_notes > len(notes):
        extra = random.sample(scale_passing, min(n_notes - len(notes), len(scale_passing)))
        notes.extend(extra)

    return sorted(set(notes))


def generate_song(mode_intervals, triads, bars=8, beats_per_bar=4):
    """Generate a synthetic song in .ntc format."""
    n_degrees = len(mode_intervals)
    scale_pcs = [round(iv) % 12 for iv in mode_intervals]

    # Pick a progression pattern that fits the scale
    valid_patterns = [p for p in PROGRESSION_PATTERNS if max(p) < n_degrees]
    if not valid_patterns:
        valid_patterns = [[0] * 4]

    pattern = random.choice(valid_patterns)

    lines = []
    beat = 0.0
    total_beats = bars * beats_per_bar

    while beat < total_beats:
        # Map pattern position to degree
        pat_idx = int(beat / beats_per_bar) % len(pattern)
        deg_idx = pattern[pat_idx] % len(triads)
        root_pc, type_idx = triads[deg_idx]

        # Generate notes
        n_notes = random.choice([3, 4, 4, 5])
        notes = generate_notes_for_chord(root_pc, type_idx, scale_pcs, n_notes)

        lines.append(f"{beat:.1f} [{', '.join(str(n) for n in notes)}]")

        # Sometimes add a half-beat passing chord
        if random.random() < 0.3 and beat + 0.5 < total_beats:
            # Neighbor chord
            neighbor_deg = (deg_idx + random.choice([-1, 1])) % len(triads)
            nr, nt = triads[neighbor_deg]
            nn = generate_notes_for_chord(nr, nt, scale_pcs, 3)
            lines.append(f"{beat + 0.5:.1f} [{', '.join(str(n) for n in nn)}]")

        beat += beats_per_bar

    return lines


def main():
    out_dir = Path("tymoczko_code/Code/First step/synth_data")
    out_dir.mkdir(exist_ok=True, parents=True)

    songlist = []
    total_songs = 0

    for mode_idx, (mode, definition) in enumerate(MODE_DATABASE.items()):
        intervals = definition.intervals
        triads = build_mode_triads(intervals)
        scale_pcs = [round(iv) % 12 for iv in intervals]

        # Generate 30 songs per mode
        n_songs = 30
        for song_i in range(n_songs):
            name = f"synth_{mode.value}_{song_i:03d}"
            bars = random.choice([8, 12, 16])
            bpb = 4 if len(intervals) != 5 else random.choice([4, 3])

            lines = generate_song(intervals, triads, bars=bars, beats_per_bar=bpb)

            filepath = out_dir / f"{name}.ntc"
            with open(filepath, "w") as f:
                f.write("\n".join(lines) + "\n")

            songlist.append(name)
            total_songs += 1

        # Summary for this mode
        triad_types = set(t for _, t in triads)
        type_names = {0: "Maj", 1: "Min", 2: "Dim", 3: "Aug", 4: "sus2", 5: "sus4"}
        types_str = ", ".join(type_names.get(t, "?") for t in sorted(triad_types))
        print(f"  {mode.value:30s} intervals={intervals}  triads=[{types_str}]")

    # Write songlist
    songlist_path = out_dir / "songlist.txt"
    songlist_path.write_text("\n".join(songlist) + "\n")

    print(f"\n  Generated {total_songs} synthetic songs for {len(MODE_DATABASE)} modes")
    print(f"  Songlist: {songlist_path}")


if __name__ == "__main__":
    random.seed(42)
    main()
