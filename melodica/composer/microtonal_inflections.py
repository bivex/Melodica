"""composer/microtonal_inflections.py — Expressive microtonal inflections for strings.

Applies quarter-tone and smaller pitch-bend inflections to string voices,
scaled by a TensionCurve.  High tension = wider, more frequent inflections.
Low tension = minimal or no inflection (clean intonation).

Based on expressive string intonation practice:
  - Leading tones raised ~25–50 cents approaching resolution
  - Colour tones (3rd, 7th) inflected for expressivity
  - Sustained notes get gentle vibrato-like pitch drift
  - Dissonant intervals (semitones, tritones) inflected upward under tension

pitch_bend range: MIDI pitch bend is ±8192 semitones*100.
  We store normalised values in expression["pitch_bend"] as semitone fractions,
  e.g. 0.25 = +25 cents (quarter tone up).
  The MIDI renderer converts: bend_int = int(value / 2.0 * 8192) clamped ±8191.

String programs (GM): Violin=40, Viola=41, Cello=42, Contrabass=43,
  String Ensemble 1=48, String Ensemble 2=49, Slow Strings=50,
  Synth Strings 1=50, Synth Strings 2=51.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from melodica.types_pkg._notes import NoteInfo

if TYPE_CHECKING:
    from melodica.composer.tension_curve import TensionCurve

# GM programs considered "strings" for inflection eligibility
STRING_PROGRAMS: frozenset[int] = frozenset({40, 41, 42, 43, 48, 49, 50, 51})

# Pitch classes that are leading tones or colour tones in diatonic context
# (inflection is most natural here)
_LEADING_TONE_PCS: frozenset[int] = frozenset({11, 4, 7})  # B, E, G (common leading contexts)
_COLOUR_PCS: frozenset[int] = frozenset({3, 6, 10})        # Eb, F#, Bb (chromatic colour)


def _tension_at(curve: "TensionCurve | None", beat: float) -> float:
    if curve is None:
        return 0.3
    return float(curve.tension_at(beat))


def inflect_note(
    note: NoteInfo,
    *,
    cents: float,
    start_fraction: float = 0.0,
    end_fraction: float = 1.0,
) -> NoteInfo:
    """Apply a static pitch-bend inflection to a single note.

    Parameters
    ----------
    note : NoteInfo
        The note to inflect (not mutated; a copy is returned).
    cents : float
        Inflection amount in cents (100 cents = 1 semitone).
        Positive = sharp, negative = flat.
    start_fraction : float
        When within the note's duration the inflection begins (0.0–1.0).
    end_fraction : float
        When within the note's duration the inflection ends (0.0–1.0).

    Returns
    -------
    NoteInfo
        Copy of the note with pitch_bend set in expression dict.
    """
    semitones = cents / 100.0
    expr = dict(note.expression)

    if start_fraction <= 0.0 and end_fraction >= 1.0:
        # Static bend: store as int-scaled cents (×100) to match expression type
        expr["pitch_bend"] = int(round(semitones * 100))  # type: ignore[assignment]
    else:
        # Timed automation: list of (beat_offset, semitone_value×100 as int)
        t0 = note.start + note.duration * start_fraction
        t1 = note.start + note.duration * end_fraction
        expr["pitch_bend"] = [  # type: ignore[assignment]
            (round(t0, 6), int(round(semitones * 100))),
            (round(t1, 6), 0),
        ]

    return NoteInfo(
        pitch=note.pitch,
        start=note.start,
        duration=note.duration,
        velocity=note.velocity,
        absolute=note.absolute,
        articulation=note.articulation,
        expression=expr,
    )


def apply_string_inflections(
    notes: list[NoteInfo],
    *,
    tension_curve: "TensionCurve | None" = None,
    program: int | None = None,
    max_cents: float = 50.0,
    leading_tone_cents: float = 30.0,
    sustained_drift_cents: float = 15.0,
    min_duration_for_drift: float = 1.5,
    seed: int | None = None,
) -> list[NoteInfo]:
    """Apply expressive microtonal inflections to a string voice.

    Inflection amount scales with tension: at tension=0 → ~10% of max_cents,
    at tension=1 → 100% of max_cents.

    Three inflection types applied:
    1. Leading-tone sharpening — notes with PC in _LEADING_TONE_PCS get
       a +cents inflection in the last 30% of their duration.
    2. Colour-tone colouring — chromatic colour PCs get subtle flat/sharp
       depending on approach direction.
    3. Sustained drift — long notes (>= min_duration_for_drift) get a gentle
       upward drift in the middle third, returning to 0 (simulates vibrato
       centroid drift under expressive pressure).

    Parameters
    ----------
    notes : list[NoteInfo]
        Notes from a string generator.
    tension_curve : TensionCurve | None
        Tension source. None = moderate constant tension (0.3).
    program : int | None
        GM program number. If not in STRING_PROGRAMS, returns notes unchanged.
    max_cents : float
        Maximum inflection magnitude in cents (default 50 = quarter tone).
    leading_tone_cents : float
        Cents applied to leading tones (default 30).
    sustained_drift_cents : float
        Peak drift cents for sustained notes (default 15).
    min_duration_for_drift : float
        Minimum note duration for sustained drift (default 1.5 beats).
    seed : int | None
        Random seed for stochastic inflection selection.

    Returns
    -------
    list[NoteInfo]
        Notes with pitch_bend inflections applied.
    """
    import random
    rng = random.Random(seed)

    if program is not None and program not in STRING_PROGRAMS:
        return list(notes)

    result: list[NoteInfo] = []

    for note in notes:
        tau = _tension_at(tension_curve, note.start)
        # Scale factor: 0.1 at rest, 1.0 at full tension
        scale = 0.1 + 0.9 * tau

        pc = note.pitch % 12
        inflected = note

        # 1. Leading tone sharpening
        if pc in _LEADING_TONE_PCS and scale > 0.2:
            cents = leading_tone_cents * scale
            # Only if probability gate passes (more likely at high tension)
            if rng.random() < scale:
                inflected = inflect_note(
                    inflected,
                    cents=cents,
                    start_fraction=0.65,
                    end_fraction=1.0,
                )

        # 2. Colour tone colouring (chromatic PCs get subtle flat)
        elif pc in _COLOUR_PCS and scale > 0.35:
            cents = -max_cents * scale * 0.4  # slight flat for colour tones
            if rng.random() < scale * 0.6:
                inflected = inflect_note(
                    inflected,
                    cents=cents,
                    start_fraction=0.0,
                    end_fraction=0.5,
                )

        # 3. Sustained drift for long notes
        if note.duration >= min_duration_for_drift and scale > 0.15:
            drift = sustained_drift_cents * scale
            if rng.random() < 0.7:
                # Drift up in middle third, return to 0
                t_mid_start = note.start + note.duration * 0.25
                t_mid_peak  = note.start + note.duration * 0.55
                t_mid_end   = note.start + note.duration * 0.85
                existing = inflected.expression.get("pitch_bend")
                expr = dict(inflected.expression)
                if existing is None:
                    expr["pitch_bend"] = [  # type: ignore[assignment]
                        (round(note.start, 6), 0),
                        (round(t_mid_start, 6), 0),
                        (round(t_mid_peak, 6), int(round(drift))),
                        (round(t_mid_end, 6), 0),
                    ]
                    inflected = NoteInfo(
                        pitch=inflected.pitch,
                        start=inflected.start,
                        duration=inflected.duration,
                        velocity=inflected.velocity,
                        absolute=inflected.absolute,
                        articulation=inflected.articulation,
                        expression=expr,
                    )

        result.append(inflected)

    return result


def tension_scaled_inflections(
    notes: list[NoteInfo],
    tension_curve: "TensionCurve | None",
    *,
    program: int | None = None,
    quarter_tone_threshold: float = 0.6,
    seed: int | None = None,
) -> list[NoteInfo]:
    """High-level wrapper: apply inflections with quarter-tone at high tension.

    Below threshold: subtle colour drift only (<=15 cents).
    At/above threshold: full expressive inflection (up to 50 cents).

    Parameters
    ----------
    quarter_tone_threshold : float
        Tension level above which quarter-tone inflection (50 cents) activates.
    """
    # Determine peak tension to choose inflection range
    if tension_curve is not None:
        sample_beats = [i * 0.5 for i in range(int(notes[-1].start / 0.5) + 2)] if notes else [0.0]
        peak_tau = max(_tension_at(tension_curve, b) for b in sample_beats)
    else:
        peak_tau = 0.3

    if peak_tau >= quarter_tone_threshold:
        max_c = 50.0
        lead_c = 35.0
        drift_c = 20.0
    else:
        max_c = 20.0
        lead_c = 15.0
        drift_c = 8.0

    return apply_string_inflections(
        notes,
        tension_curve=tension_curve,
        program=program,
        max_cents=max_c,
        leading_tone_cents=lead_c,
        sustained_drift_cents=drift_c,
        seed=seed,
    )
