#!/usr/bin/env python3
# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
harmonize_big_progression.py — stress-test CoupledHMMHarmonizer.

Builds ONE large, harmonically rich chord progression (~150 bars: maj/min
diatonic, ii-V-I in all 12 keys, secondary dominants, tritone subs, chromatic
mediants, Neapolitan, quality tour, chromatic descents/climbs), spells each
chord as a chord-tone contour, and harmonizes the SAME contour under 5 profiles
(pop, jazz, neo_soul, funk, blues). Reports how each profile renders it:
exact-match %, root-match %, average tone overlap, and a full bar-by-bar
TARGET -> OUTPUT dump for the most retentive profile.

No MIDI exported — this is a harmonizer diagnostic.

Run:  .venv_dd/bin/python scripts/harmonize_big_progression.py
"""
from __future__ import annotations

import random
import sys
import warnings
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]  # scripts/<file> -> repo root
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

warnings.filterwarnings("ignore")
random.seed(7)

from melodica.harmonize.coupled_hmm import CoupledHMMHarmonizer
from melodica.harmonize import harmonizer_profile
from melodica.theory import name_chord_label
from melodica.types import NoteInfo, Scale, Mode

KEY = Scale(root=0, mode=Mode.MAJOR)  # C major reference; the contour forces the actual chords
BARS_PER_CHORD = 4.0
NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

# quality -> relative pitch classes (root = 0)
QPCS = {
    "maj": [0, 4, 7], "min": [0, 3, 7], "dim": [0, 3, 6], "aug": [0, 4, 8],
    "sus4": [0, 5, 7], "sus2": [0, 2, 7],
    "maj7": [0, 4, 7, 11], "min7": [0, 3, 7, 10], "7": [0, 4, 7, 10],
    "maj9": [0, 4, 7, 11, 2], "min9": [0, 3, 7, 10, 2], "9": [0, 4, 7, 10, 2],
    "m7b5": [0, 3, 6, 10], "dim7": [0, 3, 6, 9],
    "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9], "add9": [0, 4, 7, 2],
}

# Build the big progression: list of (section, root_pc, quality).
PROG: list[tuple[str, int, str]] = []


def add(section, chords):
    for r, q in chords:
        PROG.append((section, r, q))


# A. C major diatonic 7ths
add("A maj-diatonic", [(0, "maj7"), (2, "min7"), (4, "min7"), (5, "maj7"),
                        (7, "7"), (9, "min7"), (11, "m7b5")])
# B. C minor diatonic 7ths
add("B min-diatonic", [(0, "min7"), (2, "m7b5"), (3, "maj7"), (5, "min7"),
                        (7, "min7"), (8, "maj7"), (10, "7")])
# C. ii-V-I major, 7 keys (circle of 5ths up)
progC = []
for k in [0, 7, 2, 9, 4, 11, 6]:
    progC += [((k + 2) % 12, "min7"), ((k + 7) % 12, "7"), (k, "maj7")]
add("C ii-V-I maj", progC)
# D. ii-V-i minor, 5 keys
progD = []
for k in [0, 7, 2, 9, 4]:
    progD += [((k + 2) % 12, "m7b5"), ((k + 7) % 12, "7"), (k, "min7")]
add("D ii-V-i min", progD)
# E. Secondary dominants in C (V7/x -> x)
pairsE = [(9, 2, "min7"), (11, 4, "min7"), (0, 5, "maj7"), (2, 7, "7"), (4, 9, "min7")]
progE = []
for vr, tr, tq in pairsE:
    progE += [(vr, "7"), (tr, tq)]
add("E secondary-dom", progE)
# F. Tritone-sub ii-bII7-I (4 keys)
progF = []
for k in [0, 7, 2, 9]:
    progF += [((k + 2) % 12, "min7"), ((k + 1) % 12, "7"), (k, "maj7")]
add("F tritone-sub", progF)
# G. Chromatic mediant + Neapolitan + dim passing
add("G chromatic-color", [(0, "maj7"), (8, "maj7"), (0, "maj7"), (4, "maj7"),
                           (1, "maj7"), (0, "maj7"), (11, "dim7"), (2, "min7")])
# H. Quality tour on C
add("H quality-tour", [(0, "maj"), (0, "min"), (0, "7"), (0, "min7"), (0, "maj7"),
                        (0, "dim7"), (0, "aug"), (0, "sus4"), (0, "6"), (0, "m7b5")])
# I. Chromatic maj7 descent (12 semitones)
add("I chromatic-maj7-desc", [((0 - i) % 12, "maj7") for i in range(12)])
# J. Circle-of-fifths maj7 climb (12)
add("J circle5ths-climb", [((7 * i) % 12, "maj7") for i in range(12)])
# K. ii-V-I in ALL 12 keys
progK = []
for k in range(12):
    progK += [((k + 2) % 12, "min7"), ((k + 7) % 12, "7"), (k, "maj7")]
add("K ii-V-I all-12-keys", progK)

N_BARS = len(PROG)
DUR = float(N_BARS * BARS_PER_CHORD)


def build_contour():
    contour = []
    for i, (_, r, q) in enumerate(PROG):
        pcs = QPCS[q]
        step = BARS_PER_CHORD / len(pcs)  # fit all chord tones within the bar
        for j, pc in enumerate(pcs):
            contour.append(NoteInfo(
                pitch=48 + ((r + pc) % 12),  # base 48 (mult of 12) preserves pitch classes
                start=i * BARS_PER_CHORD + j * step,
                duration=step * 0.9, velocity=58,
            ))
    return contour


_QNORM = {
    "maj7": "maj7", "major7": "maj7", "mj7": "maj7", "maj": "maj", "major": "maj",
    "min7": "min7", "m7": "min7", "minor7": "min7", "min": "min", "m": "min", "minor": "min",
    "7": "7", "dom7": "7", "dominant7": "7", "9": "9", "13": "13",
    "dim": "dim", "diminished": "dim", "dim7": "dim7",
    "aug": "aug", "augmented": "aug", "+": "aug",
    "sus": "sus", "sus4": "sus", "sus2": "sus",
    "6": "6", "m6": "m6", "add9": "add9", "m7b5": "m7b5",
}


def norm_q(q):
    return _QNORM.get(str(q).lower().strip(), str(q).lower().strip())


def chord_label(c):
    nm = name_chord_label(c, key=KEY)
    if nm and nm.chosen:
        ri = nm.chosen.interpretation
        return ri.root_pc, ri.quality, norm_q(ri.quality)
    return c.root, c.quality, norm_q(c.quality)


def harmonize(pname, contour):
    if pname == "boost_exotic":
        # jazz's uniform 5 on common types, but ×15 on the rare types so their
        # completion_bonus can overcome the emission gap from tiny real-music priors.
        cfg = harmonizer_profile("jazz", completion_bonus={
            0: 5.0, 1: 5.0, 6: 5.0, 7: 5.0, 8: 5.0,                 # maj/min/maj7/m7/dom7 keep ×5
            2: 15.0, 3: 15.0, 5: 15.0, 9: 15.0, 10: 15.0, 11: 15.0,  # dim/aug/sus4/halfdim/fulldim/add9 ×15
        })
    else:
        cfg = harmonizer_profile(pname)
    h = CoupledHMMHarmonizer(beam_width=14, chord_change="bars", config=cfg)
    return h.harmonize(contour, KEY, DUR)


def analyze(pname, chords):
    qctr = Counter()
    exact = root_match = 0
    overlaps = []
    rows = []  # (target_r, target_q, out_r, out_q, overlap_frac, ok)
    for i, (_, tr, tq) in enumerate(PROG):
        c = chords[i] if i < len(chords) else None
        tpcs = set((tr + pc) % 12 for pc in QPCS[tq])  # root the quality pcs before comparing
        if c is None:
            rows.append((tr, tq, None, None, 0.0, False))
            continue
        out_r, out_q_raw, out_q = chord_label(c)
        opcs = set(c.pitch_classes())
        overlap = len(tpcs & opcs) / len(tpcs)
        overlaps.append(overlap)
        qctr[out_q] += 1
        rm = (out_r % 12) == (tr % 12)
        em = rm and (out_q == norm_q(tq))
        root_match += int(rm)
        exact += int(em)
        rows.append((tr, tq, out_r, out_q_raw, overlap, em))
    n = len(PROG)
    return {
        "profile": pname, "n_chords": len(chords), "qdist": qctr,
        "exact_pct": 100.0 * exact / n, "root_pct": 100.0 * root_match / n,
        "avg_overlap": sum(overlaps) / len(overlaps) if overlaps else 0.0,
        "rows": rows,
    }


def dump_target():
    print(f"=== TARGET PROGRESSION ({N_BARS} bars, {len({s for s,_,_ in PROG})} sections) ===")
    cur = None
    line = []
    for i, (sec, r, q) in enumerate(PROG):
        if sec != cur:
            if line:
                print("  " + " ".join(line))
            cur, line = sec, []
        line.append(f"{NAMES[r]}:{q}")
    if line:
        print("  " + " ".join(line))


def dump_render(result):
    pname = result["profile"]
    print(f"\n=== HARMONIZED under '{pname}' "
          f"(exact {result['exact_pct']:.0f}% | root {result['root_pct']:.0f}% | "
          f"tone-overlap {result['avg_overlap']:.2f}) ===")
    cur = None
    for i, (sec, tr, tq) in enumerate(PROG):
        if sec != cur:
            print(f"  [{sec}]")
            cur = sec
        out_r, out_q_raw, ov, ok = result["rows"][i][2], result["rows"][i][3], result["rows"][i][4], result["rows"][i][5]
        mark = "✓" if ok else "·"
        out_s = f"{NAMES[out_r]}:{out_q_raw}" if out_r is not None else "—"
        print(f"    {i:>3} {NAMES[tr]:>2}:{tq:<5} -> {out_s:<8} {mark}  tones {ov:.2f}")


def main():
    contour = build_contour()
    print(f"Contour: {len(contour)} notes across {N_BARS} bars "
          f"({N_BARS * BARS_PER_CHORD:.0f} beats). KEY={NAMES[0]} major reference.\n")
    dump_target()

    results = {p: analyze(p, harmonize(p, contour))
               for p in ["pop", "jazz", "neo_soul", "funk", "blues", "boost_exotic"]}

    # Full bar-by-bar dump for the most 7th-retentive profile (jazz).
    dump_render(results["jazz"])

    print("\n=== STATS — same contour, 5 profiles ===")
    print(f"{'profile':<10} {'chords':>6} {'exact%':>7} {'root%':>7} {'overlap':>8}  top qualities")
    for p in ["pop", "jazz", "neo_soul", "funk", "blues", "boost_exotic"]:
        r = results[p]
        top = ", ".join(f"{q}:{n}" for q, n in r["qdist"].most_common(5))
        print(f"{p:<12} {r['n_chords']:>6} {r['exact_pct']:>6.0f}% {r['root_pct']:>6.0f}% "
              f"{r['avg_overlap']:>8.2f}  {top}")

    # Focused: do heavily-boosted rare types now survive where jazz dropped them?
    exotic = {"m7b5", "dim7", "dim", "aug", "sus4", "sus2", "6", "m6",
              "maj9", "min9", "9", "add9"}
    print("\n=== EXOTIC-TYPE RETENTION: jazz (uniform ×5) vs boost_exotic (rare types ×15) ===")
    print(f"{'bar':>4} {'target':<10} {'jazz':<14} {'boost_exotic':<16}")
    for i, (_, tr, tq) in enumerate(PROG):
        if tq in exotic:
            j, b = results["jazz"]["rows"][i], results["boost_exotic"]["rows"][i]
            js = f"{NAMES[j[2]]}:{j[3]} {'✓' if j[5] else '·'}" if j[2] is not None else "—"
            bs = f"{NAMES[b[2]]}:{b[3]} {'✓' if b[5] else '·'}" if b[2] is not None else "—"
            print(f"{i:>4} {NAMES[tr] + ':' + tq:<10} {js:<14} {bs:<16}")


if __name__ == "__main__":
    main()
