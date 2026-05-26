#!/usr/bin/env python3
"""Debug script: show beam search + TIV tension + surprise scoring for a track."""

import math
import numpy as np
from melodica.harmonize.functional_hmm import (
    FunctionalHMMHarmonizer, _QUALITY_TO_NAME, _TYPE_NAME_TO_IDX,
)
from melodica.harmonize.tension_tiv import (
    tension_curve_for_progression, tension_similarity, surprise_contour,
)
from melodica.harmonize.coupled_hmm import PCHANGE
from melodica.types import Scale, Mode, NoteInfo, BarGrid
from melodica.composer.tension_curve import TensionCurve

PC = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
Q_SHORT = {0:'Maj',1:'Min',2:'Dim',3:'Aug',4:'s2',5:'s4',
           6:'Maj7',7:'Min7',8:'Dom7',9:'Maj9',10:'Min9',11:'Add9'}


def chord_name(c):
    return f"{PC[c.root]}{Q_SHORT.get(c.quality.value, '?')}"


def analyze(title, scale, melody, duration, bpm, grid=None, curve_type='classical'):
    print(f"\n{'='*72}")
    print(f"  {title}  (scale={PC[scale.root]} {scale.mode.value}, bpm={bpm})")
    print(f"{'='*72}")

    tension = TensionCurve(total_beats=duration, curve_type=curve_type)
    harmonizer = FunctionalHMMHarmonizer(beam_width=6, bar_grid=grid, n_candidates=4)

    change_points = harmonizer._get_change_points(duration)
    observations = harmonizer._extract_observations(melody, change_points)
    T = len(change_points)

    print(f"\n  {T} change points, {len(melody)} melody notes")
    print(f"  Target tension curve ({curve_type}):")
    for i, cp in enumerate(change_points):
        tau = tension.tension_at(cp)
        bar = int(cp // (grid.numerator if grid else 4)) + 1
        phase = tension.phase_at(cp).value
        filled = int(tau * 20)
        print(f"    bar {bar:2d} (beat {cp:5.1f}): tau={tau:.2f} {'█'*filled}{'░'*(20-filled)} [{phase}]")

    # Run harmonizer normally
    result = harmonizer.harmonize(melody, scale, duration, tension_curve=tension)

    # Now compute TIV tension curve for the result
    progression = [(c.root, _QUALITY_TO_NAME.get(c.quality, "major")) for c in result]
    key_root = scale.root if scale.root is not None else 0
    is_major = scale.mode in (Mode.MAJOR, Mode.IONIAN, Mode.LYDIAN, Mode.MIXOLYDIAN)
    candidate_tensions = tension_curve_for_progression(progression, key_root, is_major)

    target_tensions = [tension.tension_at(cp) for cp in change_points[:len(result)]]
    sim = tension_similarity(candidate_tensions, target_tensions)

    # Surprise contour
    surprises = surprise_contour(progression, PCHANGE, _TYPE_NAME_TO_IDX)

    # Score breakdown
    score = harmonizer._score_progression(result, observations,
        [0], scale, tension, change_points)

    print(f"\n  Chord progression:")
    for i, c in enumerate(result):
        fn = c.function.name if c.function else 'NONE'
        tiv_t = candidate_tensions[i] if i < len(candidate_tensions) else 0
        tgt_t = target_tensions[i] if i < len(target_tensions) else 0
        print(f"    bar {i+1:2d}: {chord_name(c):8s}  deg={c.degree} fn={fn:12s}  "
              f"tiv_tension={tiv_t:6.2f}  target={tgt_t:.2f}")

    if surprises:
        print(f"\n  Surprise contour (-log p(chord_t|chord_t-1)):")
        for i, s in enumerate(surprises):
            bar_from = i + 1
            bar_to = i + 2
            filled = min(int(s * 3), 30)
            label = "low" if s < 2 else "med" if s < 4 else "HIGH"
            print(f"    bar {bar_from:2d}→{bar_to:2d}: surprise={s:5.2f} {'█'*filled}{'░'*(30-filled)} [{label}]")
        mean_s = sum(surprises) / len(surprises)
        print(f"    mean surprise: {mean_s:.2f}  (optimal ~2.5)")

    print(f"\n  Scores:")
    print(f"    TIV tension similarity (Pearson): {sim:.4f}")
    print(f"    Total progression score:          {score:.2f}")
    print(f"    Beam width used:                  {harmonizer.beam_width}")
    print(f"    Function plans tried:             {max(2, harmonizer.n_candidates // harmonizer.beam_width)}")


def main():
    # --- Track 1: Hirojoshi Garden "Mist" ---
    melody = []
    pitches = [62, 63, 67, 68, 70, 67, 63, 62, 60, 62, 63, 67, 68, 70, 68, 63]
    for i, p in enumerate(pitches):
        melody.append(NoteInfo(pitch=p, start=float(i*4), duration=4.0))

    analyze("Hirojoshi Garden — 1 Mist",
            Scale(2, Mode.HIROJOSHI), melody, 64.0, 48,
            BarGrid(4, 4), 'classical')

    # --- Track: Dark Souls style, minor ---
    melody2 = []
    pitches2 = [55, 58, 60, 63, 62, 60, 58, 55, 53, 55, 58, 62, 60, 58, 55, 53]
    for i, p in enumerate(pitches2):
        melody2.append(NoteInfo(pitch=p, start=float(i*4), duration=4.0))

    analyze("Shadows of Lordran — style",
            Scale(3, Mode.HARMONIC_MINOR), melody2, 64.0, 72,
            BarGrid(4, 4), 'build_release')

    # --- Track: Sikah Nights style ---
    melody3 = []
    pitches3 = [62, 65, 66, 69, 68, 66, 65, 62, 61, 62, 65, 69, 68, 66, 65, 61]
    for i, p in enumerate(pitches3):
        melody3.append(NoteInfo(pitch=p, start=float(i*4), duration=4.0))

    analyze("Sikah Nights — style",
            Scale(2, Mode.SIKAH), melody3, 64.0, 55,
            BarGrid(4, 4), 'classical')


if __name__ == "__main__":
    main()
