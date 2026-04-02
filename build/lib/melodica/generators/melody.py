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
generators/melody.py — MelodyGenerator.

Layer: Application / Domain

Melodica-matching parameters (all with defaults):
  steps_probability        0.86  — fraction of moves that are steps (≤2 semitones)
  note_repetition_probability 0.14 — probability of repeating the last pitch
  random_movement          0.80  — fraction of selections made randomly (vs. closest)
  harmony_note_probability 0.64  — fraction from chord tones (vs. scale tones)
  note_range_low/high      54/76 — E3/E5 override (beats params.key_range)
  first_note               "chord_root"      — strategy for the very first pitch
  last_note                "last_chord_root" — strategy for the very last pitch
  after_leap               "any"             — constraint on move following a leap
  allowed_up_intervals     None (= all)      — frozenset of semitone distances allowed up
  allowed_down_intervals   None (= all)      — frozenset of semitone distances allowed down
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica import types
from melodica.render_context import RenderContext
from melodica.utils import nearest_pitch, nearest_pitch_above, pitch_class, chord_at
from melodica.generators._melody_pitch import (
    MelodyPitchSelector,
    STEP_SEMITONES,
    LEAP_SEMITONES,
    ALL_INTERVALS,
    DEFAULT_UP_INTERVALS,
    DEFAULT_DOWN_INTERVALS,
    _all_pitches_in_range,
    _all_pitches_in_range_pc_list,
)


# Interval constants and utility helpers re-exported from _melody_pitch
# (kept here so existing imports from this module continue to work)

FIRST_NOTE_OPTIONS = frozenset(
    {
        "chord_root",  # root of the first chord (default)
        "any_chord",  # random tone of the first chord
        "scale",  # random scale tone near middle
        "tonic",  # scale root
        "step_above_tonic",
        "step_below_tonic",
    }
)
LAST_NOTE_OPTIONS = frozenset(
    {
        "last_chord_root",  # root of the last chord (default)
        "any_chord",
        "scale",
        "any",  # no constraint
    }
)
AFTER_LEAP_OPTIONS = frozenset(
    {
        "step_opposite",  # step in the opposite direction
        "step_any",  # any step
        "step_or_smaller_opposite",  # step or smaller leap, opposite direction
        "leap_opposite",  # leap in the opposite direction
        "any",  # no constraint (default)
    }
)


# ---------------------------------------------------------------------------
# MelodyGenerator
# ---------------------------------------------------------------------------


@dataclass
class MelodyGenerator(PhraseGenerator):
    """
    Generates a stepwise/leaping melodic line over a chord sequence.

    harmony_note_probability / prefer_chord_tones:
        Probability [0–1] that a pitch is drawn from chord tones (vs. scale tones).
         default: 0.64.  `prefer_chord_tones` is a legacy alias.
    steps_probability:
        Probability [0–1] that a non-repeated move is a step (≤2 semitones).
         default: 0.86.  Overrides params.leap_probability when set.
    note_repetition_probability:
        Probability [0–1] of repeating the previous pitch.  default: 0.14.
    random_movement:
        Probability [0–1] of choosing randomly among valid candidates (vs. closest).
         default: 0.80.
    first_note / last_note:
        Strategy for the opening and closing pitch.
    after_leap:
        Constraint applied on the note immediately following a leap.
    allowed_up_intervals / allowed_down_intervals:
        frozenset of semitone distances permitted when moving up / down.
        None = use DEFAULT_UP/DOWN_INTERVALS.
    """

    name: str = "Melody Generator"
    rhythm: RhythmGenerator | None = None

    # Mode: how chord/scale tones are used
    mode: str = "downbeat_chord"  # "downbeat_chord", "scale_only", "on_beat_chord", "chord_only", "scale_and_chord"

    # Pitch-pool control (harmony vs. scale tones)
    harmony_note_probability: float = 0.64
    prefer_chord_tones: float = 0.64  # legacy alias

    # Step / leap / repetition balance
    steps_probability: float | None = None  # None → use 1 − params.leap_probability
    note_repetition_probability: float = 0.14

    # Random vs. directed selection
    random_movement: float = 0.80

    # Note-range override (default: G2-F4)
    note_range_low: int | None = None
    note_range_high: int | None = None

    # Direction tendency (kept for backward compat; still nudges targets)
    direction_bias: float = 0.0

    # Phrase-boundary strategies
    first_note: str = "chord_root"
    last_note: str = "last_chord_root"

    # Post-leap constraint
    after_leap: str = "any"

    # Climax
    climax: str = "first_plus_maj3"  # "first_plus_maj3", "none", "up_3rd", "up_5th", "up_octave"

    # Penultimate note is a step above tonic
    penultimate_step_above: bool = True

    # Allow 2nd/7th as melody notes even in chord-only mode
    allow_2nd: bool = True
    allow_7th: bool = True

    # Interval filters (None = use defaults)
    allowed_up_intervals: frozenset[int] | None = None
    allowed_down_intervals: frozenset[int] | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        rhythm: RhythmGenerator | None = None,
        mode: str = "downbeat_chord",
        # Backward-compat alias first
        prefer_chord_tones: float | None = None,
        harmony_note_probability: float = 0.64,
        steps_probability: float | None = None,
        note_repetition_probability: float = 0.14,
        random_movement: float = 0.80,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
        direction_bias: float = 0.0,
        first_note: str = "chord_root",
        last_note: str = "last_chord_root",
        after_leap: str = "any",
        climax: str = "first_plus_maj3",
        penultimate_step_above: bool = True,
        allow_2nd: bool = True,
        allow_7th: bool = True,
        allowed_up_intervals: frozenset[int] | None = None,
        allowed_down_intervals: frozenset[int] | None = None,
    ) -> None:
        super().__init__(params)
        self.rhythm = rhythm

        # prefer_chord_tones → harmony_note_probability (legacy alias)
        if prefer_chord_tones is not None:
            self.harmony_note_probability = prefer_chord_tones
            self.prefer_chord_tones = prefer_chord_tones
        else:
            self.harmony_note_probability = harmony_note_probability
            self.prefer_chord_tones = harmony_note_probability

        self.steps_probability = steps_probability  # None handled at render time
        self.note_repetition_probability = max(0.0, min(1.0, note_repetition_probability))
        self.random_movement = max(0.0, min(1.0, random_movement))
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self.direction_bias = direction_bias

        if first_note not in FIRST_NOTE_OPTIONS:
            raise ValueError(
                f"first_note must be one of {sorted(FIRST_NOTE_OPTIONS)}; got {first_note!r}"
            )
        if last_note not in LAST_NOTE_OPTIONS:
            raise ValueError(
                f"last_note must be one of {sorted(LAST_NOTE_OPTIONS)}; got {last_note!r}"
            )
        if after_leap not in AFTER_LEAP_OPTIONS:
            raise ValueError(
                f"after_leap must be one of {sorted(AFTER_LEAP_OPTIONS)}; got {after_leap!r}"
            )
        self.first_note = first_note
        self.last_note = last_note
        self.after_leap = after_leap
        self.mode = mode
        self.climax = climax
        self.penultimate_step_above = penultimate_step_above
        self.allow_2nd = allow_2nd
        self.allow_7th = allow_7th
        self.allowed_up_intervals = allowed_up_intervals
        self.allowed_down_intervals = allowed_down_intervals
        self._last_context: RenderContext | None = None
        self._pitch_selector: MelodyPitchSelector = MelodyPitchSelector(self)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def render(
        self,
        chords: list[types.ChordLabel],
        key: types.Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[types.NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[types.NoteInfo] = []

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        # Effective steps probability: explicit > 1 − leap_probability
        steps_prob = (
            self.steps_probability
            if self.steps_probability is not None
            else 1.0 - self.params.leap_probability
        )

        # Initialise prev_pitch via first_note strategy
        prev_pitch = self._first_pitch(chords[0], key, low, high, context)

        last_interval = 0  # signed semitones of the most recent move
        last_chord: types.ChordLabel | None = None

        for i, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            last_chord = chord
            is_last = i == len(events) - 1

            # Beat position for mode
            is_downbeat = event.onset % 1.0 < 0.1
            is_on_beat = event.onset % 0.5 < 0.1

            # Penultimate note: step above tonic
            is_penultimate = i == len(events) - 2 and self.penultimate_step_above and not is_last

            # ---- Note repetition ----
            if notes and random.random() < self.note_repetition_probability:
                pitch = prev_pitch
            elif is_last and self.last_note != "any":
                # ---- Last-note strategy ----
                pitch = self._last_pitch(last_chord, key, prev_pitch, low, high)
            else:
                # ---- Normal selection ----
                active_key = key.get_key_at(event.onset) if hasattr(key, "get_key_at") else key
                pitch = self._pick_pitch(
                    chord,
                    active_key,
                    prev_pitch,
                    low,
                    high,
                    last_interval,
                    steps_prob,
                    is_downbeat,
                    is_on_beat,
                    is_penultimate,
                )

            # Clamp to range
            pitch = max(low, min(high, pitch))

            base_vel = _velocity_from_density(self.params.density)
            vel = int(base_vel * event.velocity_factor)

            notes.append(
                types.NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(0, min(types.MIDI_MAX, vel)),
                )
            )
            last_interval = pitch - prev_pitch
            prev_pitch = pitch

        # Leap-after-fill: insert passing tones between large leaps.
        # Skipped in strict chord-tone mode (harmony_note_probability == 1.0)
        # because passing tones would be scale tones, violating the constraint.
        # Use after_leap="step_opposite" to tame leaps without passing tones.
        if self.harmony_note_probability < 1.0:
            notes = self._fill_leaps(notes, key)

        # Phrase arch velocity contour
        from melodica.generators._postprocess import apply_phrase_arch

        notes = apply_phrase_arch(
            notes,
            duration_beats,
            context.phrase_position if context else 0.0,
        )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        else:
            self._last_context = None

        return notes

    # ------------------------------------------------------------------
    # Pitch selection
    # ------------------------------------------------------------------

    def _pick_pitch(
        self,
        chord: types.ChordLabel | None,
        key: types.Scale,
        prev_pitch: int,
        low: int,
        high: int,
        last_interval: int,
        steps_prob: float,
        is_downbeat: bool = False,
        is_on_beat: bool = False,
        is_penultimate: bool = False,
    ) -> int:
        return self._pitch_selector.pick_pitch(
            chord,
            key,
            prev_pitch,
            low,
            high,
            last_interval,
            steps_prob,
            is_downbeat,
            is_on_beat,
            is_penultimate,
        )

    def _build_candidates(
        self,
        pool: list[int],
        prev_pitch: int,
        low: int,
        high: int,
        interval_set: frozenset[int],
        required_direction: int,  # +1=up, -1=down, 0=either
    ) -> list[int]:
        return self._pitch_selector.build_candidates(
            pool,
            prev_pitch,
            low,
            high,
            interval_set,
            required_direction,
        )

    def _get_pitch_pool(
        self,
        chord: types.ChordLabel | None,
        key: types.Scale,
        is_downbeat: bool = False,
        is_on_beat: bool = False,
    ) -> list[int]:
        return self._pitch_selector.get_pitch_pool(chord, key, is_downbeat, is_on_beat)

    # ------------------------------------------------------------------
    # First / last note strategies
    # ------------------------------------------------------------------

    def _first_pitch(
        self,
        first_chord: types.ChordLabel,
        key: types.Scale,
        low: int,
        high: int,
        context: RenderContext | None,
    ) -> int:
        return self._pitch_selector.first_pitch(first_chord, key, low, high, context)

    def _last_pitch(
        self,
        last_chord: types.ChordLabel | None,
        key: types.Scale,
        prev_pitch: int,
        low: int,
        high: int,
    ) -> int:
        return self._pitch_selector.last_pitch(last_chord, key, prev_pitch, low, high)

    # ------------------------------------------------------------------
    # Rhythm / events
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        step = max(0.25, (1.0 - self.params.density) * 2.0)
        t, events = 0.0, []
        while t < duration_beats:
            dur = max(0.125, step - 0.01)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur, velocity_factor=1.0))
            t += step
        return events

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    def _fill_leaps(self, notes: list[types.NoteInfo], key) -> list[types.NoteInfo]:
        """Insert a passing tone between any two consecutive notes > 5 semitones apart."""
        if len(notes) < 2:
            return notes
        result = [notes[0]]
        for i in range(1, len(notes)):
            gap = notes[i].pitch - notes[i - 1].pitch
            if abs(gap) > 5:
                direction = 1 if gap > 0 else -1
                pass_pitch = notes[i - 1].pitch + direction * min(abs(gap) // 2, 3)
                pass_start = (notes[i - 1].start + notes[i].start) / 2
                active_key = key.get_key_at(pass_start) if hasattr(key, "get_key_at") else key
                if hasattr(active_key, "contains") and not active_key.contains(pass_pitch % 12):
                    for offset in [1, -1, 2, -2]:
                        if active_key.contains((pass_pitch + offset) % 12):
                            pass_pitch += offset
                            break
                low = (
                    self.note_range_low
                    if self.note_range_low is not None
                    else self.params.key_range_low
                )
                high = (
                    self.note_range_high
                    if self.note_range_high is not None
                    else self.params.key_range_high
                )
                pass_pitch = max(low, min(high, pass_pitch))
                pass_dur = min(notes[i - 1].duration, 0.25)
                result.append(
                    types.NoteInfo(
                        pitch=pass_pitch,
                        start=round(pass_start, 6),
                        duration=pass_dur,
                        velocity=max(1, min(127, int(notes[i].velocity * 0.7))),
                    )
                )
            result.append(notes[i])
        return result


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


def _velocity_from_density(density: float) -> int:
    return int(50 + density * 50)
