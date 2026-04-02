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
generators/markov.py — MarkovMelodyGenerator.

Layer: Application / Domain

Melodica-matching additions (all with defaults):
  note_repetition_probability 0.14  — hold the previous pitch
  harmony_note_probability    0.64  — chord-tone attraction (downbeat & random)
  note_range_low / high       None  — narrower note range (overrides params)
  direction_bias              0.0   — gentle up/down tendency
  allowed_up_intervals        None  — frozenset of permitted up-intervals (semitones)
  allowed_down_intervals      None  — frozenset of permitted down-intervals
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


DEFAULT_UP_INTERVALS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 7, 9, 12})
DEFAULT_DOWN_INTERVALS: frozenset[int] = frozenset({1, 2, 3, 4, 5, 7, 9, 12})

_DEFAULT_TRANSITIONS: dict[int, dict[int, float]] = {
    0:  {0: 0.20, 1: 0.30, -1: 0.30, 2: 0.10, -2: 0.10},
    1:  {1: 0.35, 0: 0.25, 2: 0.20, -1: 0.15, 3: 0.05},
    -1: {-1: 0.35, 0: 0.25, -2: 0.20, 1: 0.15, -3: 0.05},
    2:  {2: 0.30, 1: 0.25, 0: 0.20, 3: 0.10, -1: 0.10, -2: 0.05},
    -2: {-2: 0.30, -1: 0.25, 0: 0.20, -3: 0.10, 1: 0.10, 2: 0.05},
    3:  {1: 0.30, 2: 0.25, 0: 0.20, -1: 0.15, 3: 0.10},
    -3: {-1: 0.30, -2: 0.25, 0: 0.20, 1: 0.15, -3: 0.10},
    4:  {1: 0.30, -1: 0.25, 0: 0.20, 2: 0.15, -2: 0.10},
    -4: {-1: 0.30, 1: 0.25, 0: 0.20, -2: 0.15, 2: 0.10},
}


@dataclass
class MarkovMelodyGenerator(PhraseGenerator):
    """
    Generates melodies using a first-order Markov Chain for intervals.
    Transitions are defined as semitone offsets.

    The Markov chain proposes the interval; downstream filters apply
    note repetition, chord-tone attraction, interval allow-lists, and
    a phrase-arch velocity contour.
    """

    name: str = "Markov Melody"
    transitions: dict[int, dict[int, float]] = field(
        default_factory=lambda: dict(_DEFAULT_TRANSITIONS)
    )
    rhythm: RhythmGenerator | None = None
    note_repetition_probability: float = 0.14
    harmony_note_probability: float = 0.64
    note_range_low: int | None = None
    note_range_high: int | None = None
    direction_bias: float = 0.0
    allowed_up_intervals: frozenset[int] | None = None
    allowed_down_intervals: frozenset[int] | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        transitions: dict[int, dict[int, float]] | None = None,
        rhythm: RhythmGenerator | None = None,
        note_repetition_probability: float = 0.14,
        harmony_note_probability: float = 0.64,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
        direction_bias: float = 0.0,
        allowed_up_intervals: frozenset[int] | None = None,
        allowed_down_intervals: frozenset[int] | None = None,
    ) -> None:
        super().__init__(params)
        self.transitions = transitions if transitions is not None else dict(_DEFAULT_TRANSITIONS)
        self.rhythm = rhythm
        self.note_repetition_probability = max(0.0, min(1.0, note_repetition_probability))
        self.harmony_note_probability = max(0.0, min(1.0, harmony_note_probability))
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self.direction_bias = direction_bias
        self.allowed_up_intervals = allowed_up_intervals
        self.allowed_down_intervals = allowed_down_intervals
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = self.note_range_high if self.note_range_high is not None else self.params.key_range_high

        current_chord = chords[0]
        last_chord = current_chord
        if context is not None and context.prev_pitch is not None:
            last_pitch = context.prev_pitch
        else:
            last_pitch = nearest_pitch(current_chord.root, (low + high) // 2)
        last_interval = 0

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is not None:
                last_chord = chord
                current_chord = chord

            # --- Note repetition ---
            if notes and random.random() < self.note_repetition_probability:
                target_pitch = last_pitch
                next_interval = 0
            else:
                # 1. Markov proposes an interval
                proposed = self._get_next_interval(last_interval)

                # 2. direction_bias: nudge zero-move toward preferred direction
                if proposed == 0 and self.direction_bias != 0.0:
                    if random.random() < abs(self.direction_bias):
                        proposed = 1 if self.direction_bias > 0 else -1

                # 3. Snap to nearest allowed interval (preserves direction)
                next_interval = self._filter_interval(proposed)
                target_pitch = last_pitch + next_interval

            # 4. Range bounce
            if target_pitch < low:
                target_pitch += 12
            elif target_pitch > high:
                target_pitch -= 12

            # 5. Key snap
            active_key = key.get_key_at(event.onset) if hasattr(key, "get_key_at") else key
            if not active_key.contains(target_pitch % 12):
                found = False
                for offset in [1, -1, 2, -2]:
                    if active_key.contains((target_pitch + offset) % 12):
                        target_pitch += offset
                        found = True
                        break
                if not found:
                    target_pitch = nearest_pitch(current_chord.root, target_pitch)

            # 6. Chord-tone attraction on downbeats and with harmony_note_probability
            is_downbeat = event.onset % 1.0 < 0.1
            if chord is not None and (is_downbeat or random.random() < self.harmony_note_probability):
                chord_pcs = chord.pitch_classes()
                if chord_pcs and (target_pitch % 12) not in chord_pcs:
                    nearest_ct = min(
                        (nearest_pitch(pc, target_pitch) for pc in chord_pcs),
                        key=lambda p: abs(p - target_pitch),
                    )
                    # Only snap if within 2 semitones — avoid unexpected leaps
                    if abs(nearest_ct - target_pitch) <= 2:
                        target_pitch = nearest_ct

            # Final clamp
            target_pitch = max(low, min(high, target_pitch))

            base_vel = self._velocity()
            vel = int(base_vel * event.velocity_factor)
            notes.append(NoteInfo(
                pitch=target_pitch,
                start=round(event.onset, 6),
                duration=event.duration,
                velocity=max(1, min(127, vel)),
            ))

            # Clamp interval so Markov state stays within the transition table range.
            # Without clamping, range-bounce (+/-12) or chord-snap can push last_interval
            # to states far outside the table, breaking the chain via the fallback lookup.
            last_interval = max(-12, min(12, target_pitch - last_pitch))
            last_pitch = target_pitch

        # Passing tones between large leaps
        notes = self._fill_leaps(notes, key, low, high)

        # Phrase arch velocity contour
        notes = self._apply_phrase_arch(
            notes, duration_beats,
            context.phrase_position if context else 0.0,
        )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    @classmethod
    def train_from_notes(
        cls,
        notes: list[NoteInfo],
        *,
        params: GeneratorParams | None = None,
        **kwargs,
    ) -> "MarkovMelodyGenerator":
        """
        Build a MarkovMelodyGenerator whose transition table is learned from
        the intervals present in *notes* (sorted by start time).

        Smoothing: each observed transition gets a count of 1; unseen states
        fall back to _DEFAULT_TRANSITIONS at weight 0.1 so generation never
        gets stuck.
        """
        sorted_notes = sorted(notes, key=lambda n: n.start)
        counts: dict[int, dict[int, int]] = {}
        for i in range(len(sorted_notes) - 1):
            interval = sorted_notes[i + 1].pitch - sorted_notes[i].pitch
            # Clamp interval to a reasonable range (±12 semitones)
            interval = max(-12, min(12, interval))
            prev_interval = (
                sorted_notes[i].pitch - sorted_notes[i - 1].pitch if i > 0 else 0
            )
            prev_interval = max(-12, min(12, prev_interval))
            counts.setdefault(prev_interval, {}).setdefault(interval, 0)
            counts[prev_interval][interval] += 1

        # Normalise to probabilities
        transitions: dict[int, dict[int, float]] = {}
        for state, successors in counts.items():
            total = sum(successors.values())
            transitions[state] = {iv: c / total for iv, c in successors.items()}

        # Fill in any state from the default table that's missing (smoothing)
        for state, defaults in _DEFAULT_TRANSITIONS.items():
            if state not in transitions:
                transitions[state] = {iv: w * 0.1 for iv, w in defaults.items()}

        return cls(params=params, transitions=transitions, **kwargs)

    # ------------------------------------------------------------------
    # Markov chain
    # ------------------------------------------------------------------

    def _get_next_interval(self, current: int) -> int:
        if current in self.transitions:
            state = current
        else:
            state = min(self.transitions.keys(), key=lambda k: abs(k - current))
        choices = self.transitions[state]
        return random.choices(list(choices.keys()), weights=list(choices.values()), k=1)[0]

    def _filter_interval(self, proposed: int) -> int:
        """Snap proposed interval to the nearest value in the allowed set."""
        if proposed == 0:
            return 0
        up_ivls = self.allowed_up_intervals if self.allowed_up_intervals is not None else DEFAULT_UP_INTERVALS
        dn_ivls = self.allowed_down_intervals if self.allowed_down_intervals is not None else DEFAULT_DOWN_INTERVALS

        if proposed > 0:
            if proposed in up_ivls:
                return proposed
            best = min(up_ivls, key=lambda iv: abs(iv - proposed), default=None)
            return best if best is not None else proposed
        else:
            abs_iv = abs(proposed)
            if abs_iv in dn_ivls:
                return proposed
            best = min(dn_ivls, key=lambda iv: abs(iv - abs_iv), default=None)
            return -best if best is not None else proposed

    # ------------------------------------------------------------------
    # Rhythm / events
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.45))
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)

    # ------------------------------------------------------------------
    # Post-processing
    # ------------------------------------------------------------------

    def _fill_leaps(
        self,
        notes: list[NoteInfo],
        key: Scale,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        """Insert a passing tone between any two notes > 5 semitones apart."""
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
                if not active_key.contains(pass_pitch % 12):
                    for offset in [1, -1, 2, -2]:
                        if active_key.contains((pass_pitch + offset) % 12):
                            pass_pitch += offset
                            break
                pass_pitch = max(low, min(high, pass_pitch))
                pass_dur = min(notes[i - 1].duration, 0.25)
                result.append(NoteInfo(
                    pitch=pass_pitch,
                    start=round(pass_start, 6),
                    duration=pass_dur,
                    velocity=max(1, min(127, int(notes[i].velocity * 0.7))),
                ))
            result.append(notes[i])
        return result

    def _apply_phrase_arch(
        self,
        notes: list[NoteInfo],
        duration_beats: float,
        phrase_position: float = 0.0,
    ) -> list[NoteInfo]:
        """Sin-curve velocity arch: soft start → peak at ~70% → gentle resolution."""
        if not notes or duration_beats <= 0:
            return notes
        arch_height = 0.3 + 0.2 * phrase_position
        for note in notes:
            progress = note.start / duration_beats
            arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
            note.velocity = max(1, min(127, int(note.velocity * arch)))
        return notes
