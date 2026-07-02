# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
tonality_scale_showcase.py — Демонстрация Tonality по всем Scale/Mode.

Для каждого из 80 режимов генерирует прогрессию через CoupledHMM используя
ХАРАКТЕРНЫЕ ТОНЫ самого режима (берём 1, 3, 5, 7 ступени из Scale.intervals()),
прогоняет verify_progression и выводит сводную таблицу.

Run:  .venv_dd/bin/python scripts/tonality_scale_showcase.py
"""

from __future__ import annotations

import warnings
import math
from typing import Optional

from melodica.engines.coupled_hmm_engine import CoupledHMMEngine
from melodica.harmonize.coupled_hmm import HMMConfig
from melodica.theory import name_chord_label, verify_progression
from melodica.types import HarmonizationRequest, Mode, Note, Scale

CHORD_RHYTHM = 4.0
DEFAULT_ROOT = 0  # C


def _scale_melody(key: Scale, root: int) -> list[Note]:
    """Build a 4-note melody from the 1st, 3rd, 5th, 7th scale degrees.
    Falls back to 1,2,3,4 if the scale has fewer than 7 tones.
    Rounds microtonal intervals to nearest semitone for MIDI.
    """
    ivs = key.intervals()
    # pick indices: I, III, V, VII (0-indexed: 0,2,4,6) — or wrap
    picks = [0, 2, 4, 6] if len(ivs) >= 7 else list(range(min(4, len(ivs))))
    picks = picks[:4]
    # pad to 4 if fewer
    while len(picks) < 4:
        picks.append(picks[-1])

    notes = []
    for i, deg in enumerate(picks):
        interval = ivs[deg % len(ivs)]
        pitch = root + int(round(float(interval)))
        # keep in MIDI range 48-84
        while pitch < 48:
            pitch += 12
        while pitch > 84:
            pitch -= 12
        notes.append(Note(pitch, i * CHORD_RHYTHM, CHORD_RHYTHM))
    return notes


def _chord_name(c) -> str:
    NOTE = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
    QUAL = {
        'maj': '', 'min': 'm', 'dim': 'dim', 'aug': 'aug',
        'sus2': 'sus2', 'sus4': 'sus4',
        'maj7': 'M7', 'min7': 'm7', 'dom7': '7',
        'maj9': 'M9', 'min9': 'm9', 'add9': 'add9',
        'maj6': 'M6', 'min6': 'm6',
    }
    nm = name_chord_label(c)
    if nm and nm.chosen:
        ri = nm.chosen.interpretation
        root_name = NOTE[int(ri.root_pc) % 12]
        qual = QUAL.get(ri.quality, ri.quality)
        return f"{root_name}{qual}"
    return "?"


def probe_mode(mode: Mode, root: int = DEFAULT_ROOT):
    key   = Scale(root=root, mode=mode)
    notes = _scale_melody(key, root)
    n     = len(notes)

    microtonal = False
    error: Optional[str] = None
    chord_names: list[str] = []
    parseable = ambiguous = vl = 0

    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            engine = CoupledHMMEngine(config=HMMConfig(key_coupling_weight=2.0))
            chords = engine.harmonize(
                HarmonizationRequest(notes, key, chord_rhythm=CHORD_RHYTHM)
            )
            for w in caught:
                if "microtonal" in str(w.message).lower():
                    microtonal = True

        rep       = verify_progression(chords)
        parseable = rep["parseable"]
        ambiguous = rep["ambiguous"]
        vl        = rep["total_voice_leading"]
        chord_names = [_chord_name(c) for c in chords]

    except Exception as e:
        error = str(e)[:70]
        chord_names = ["ERR"] * n

    return dict(
        mode=mode, root=root,
        chord_names=chord_names,
        parseable=parseable, n=n,
        ambiguous=ambiguous, vl=vl,
        microtonal=microtonal,
        error=error,
    )


def main() -> None:
    NOTE = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

    print("\n" + "=" * 82)
    print("  TONALITY SCALE SHOWCASE — CoupledHMM harmonization across all modes")
    print("  Melody built from scale's own I-III-V-VII degrees, key_coupling=2.0")
    print("=" * 82)
    print(f"  {'MODE':<32} {'CHORDS (I III V VII)':<28} {'PARSE':>5} {'AMB':>4} {'VL':>4}  FLAGS")
    print("  " + "-" * 78)

    results = []
    clean = partial = exotic = nerrors = 0

    for mode in Mode:
        r = probe_mode(mode, DEFAULT_ROOT)
        results.append(r)

        chords_str = " ".join(f"{c:>6}" for c in r["chord_names"][:4])
        parse_str  = f"{r['parseable']}/{r['n']}"
        flags = []
        if r["microtonal"]:
            flags.append("microtonal")
        if r["error"]:
            flags.append(f"ERR:{r['error'][:40]}")
        elif r["parseable"] == 0:
            flags.append("degenerate")
        elif r["ambiguous"] == r["n"]:
            flags.append("all-ambiguous")

        flag_str = ", ".join(flags)
        vl_str   = str(r["vl"]) if r["vl"] else "-"

        print(f"  {mode.value:<32} {chords_str:<28} "
              f"{parse_str:>5} {r['ambiguous']:>4} {vl_str:>4}  {flag_str}")

        if r["error"]:
            nerrors += 1
        elif r["parseable"] == r["n"] and r["ambiguous"] == 0:
            clean += 1
        elif r["parseable"] == 0 or r["ambiguous"] == r["n"]:
            exotic += 1
        else:
            partial += 1

    total = len(results)
    print("\n" + "=" * 82)
    print(f"  SUMMARY  ({total} modes)")
    print(f"  CLEAN   parse=n, amb=0   : {clean:>3}  ({100*clean//total}%)")
    print(f"  PARTIAL parse<n or amb>0 : {partial:>3}  ({100*partial//total}%)")
    print(f"  EXOTIC  0 parsed/all-amb : {exotic:>3}  ({100*exotic//total}%)")
    if nerrors:
        print(f"  ERRORS                   : {nerrors:>3}")
    print("=" * 82)

    print("\n  CLEAN (full Tonality coverage):")
    for r in results:
        if not r["error"] and r["parseable"] == r["n"] and r["ambiguous"] == 0:
            mt = "  [microtonal]" if r["microtonal"] else ""
            prog = " → ".join(r["chord_names"])
            print(f"    {r['mode'].value:<32} {prog}{mt}")

    partial_list = [r for r in results
                    if not r["error"] and 0 < r["parseable"] < r["n"] or
                    (not r["error"] and r["parseable"] == r["n"] and r["ambiguous"] > 0)]
    if partial_list:
        print(f"\n  PARTIAL ({len(partial_list)} modes — some ambiguous or unparseable):")
        for r in partial_list:
            mt = "  [microtonal]" if r["microtonal"] else ""
            prog = " → ".join(r["chord_names"])
            print(f"    {r['mode'].value:<32} {prog}  amb={r['ambiguous']}{mt}")

    exotic_list = [r for r in results
                   if not r["error"] and (r["parseable"] == 0 or r["ambiguous"] == r["n"])]
    if exotic_list:
        print(f"\n  EXOTIC/DEGENERATE ({len(exotic_list)} modes):")
        for r in exotic_list:
            print(f"    {r['mode'].value}")

    err_list = [r for r in results if r["error"]]
    if err_list:
        print(f"\n  ERRORS ({len(err_list)}):")
        for r in err_list:
            print(f"    {r['mode'].value:<32} {r['error']}")

    print()


if __name__ == "__main__":
    main()
