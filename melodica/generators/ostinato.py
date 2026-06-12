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
generators/ostinato.py — Ostinato/Pattern generator.

Layer: Application / Domain

Patterns use scale degrees 1-7 where:
  1 = root, 2 = second, 3 = third, 4 = fourth,
  5 = fifth, 6 = sixth, 7 = seventh.

"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import chord_pitches_closed, chord_at


# Scale degree patterns from UI (1-based degrees)
NAMED_PATTERNS: dict[str, list[int]] = {
    "1-3-5": [1, 3, 5],
    "5-3-1": [5, 3, 1],
    "5-1-3-1": [5, 1, 3, 1],
    "1-3-1-5": [1, 3, 1, 5],
    "1-3-5-3-1-5-3-1-3-5": [1, 3, 5, 3, 1, 5, 3, 1, 3, 5],
    "1-2-1-3-1-4-1-5": [1, 2, 1, 3, 1, 4, 1, 5],
    "1-3-4-5-4-3-1-3": [1, 3, 4, 5, 4, 3, 1, 3],
    "1-3-5-3": [1, 3, 5, 3],
    "5-3-5-1": [5, 3, 5, 1],
    "3-1": [3, 1],
    "5-1-4-1-3-1-2-1": [5, 1, 4, 1, 3, 1, 2, 1],
    "5-1-4-1": [5, 1, 4, 1],
    "5-3-1-3": [5, 3, 1, 3],
    "1-5-3-5": [1, 5, 3, 5],
    "1-3-5-1-5-3-1-5": [1, 3, 5, 1, 5, 3, 1, 5],
    "3-1-1-1": [3, 1, 1, 1],
    "1-3-5-6": [1, 3, 5, 6],
    "1-3-4-5-4-3": [1, 3, 4, 5, 4, 3],
    "5-1-5-1": [5, 1, 5, 1],
}

# All possible intervals (default: all allowed)
DEFAULT_INTERVALS = frozenset({-7, -6, -5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 7})


@dataclass
class OstinatoGenerator(PhraseGenerator):
    """
    Plays a fixed repeating pattern of scale degrees over chord changes.

    pattern:
        str — named pattern ("1-3-5", "5-1-4-1", etc.) or custom "1-3-5-7"
        list[int] — explicit scale degrees (legacy: chord tone indices if use_scale_degrees=False)
    use_scale_degrees:
        True (default) — pattern values are 1-based scale degrees (style)
        False — legacy mode, pattern values are chord tone indices
    repeat_notes:
        How many times to repeat each pattern note (Melodica: "Repeat Notes: 1x" or "4X")
    pattern_length:
        Number of beats after which to retrigger the pattern (Melodica: "Pattern Length (Retrigger)")
        None = never retrigger (pattern cycles continuously)
    insert_root_every:
        Insert chord root note every N pattern steps (Melodica: "Insert Chord Root Note Every")
        0 or None = never insert root
    changed_notes_count:
        After this many notes, stop applying variation (Melodica: "Changed Notes Count")
        0 = no variation limit
    possible_intervals:
        Allowed scale step intervals from root (Melodica: "Possible Intervals")
        e.g. {1, 3, 5} means only degrees 1, 3, 5 can appear in variation
    """

    name: str = "Ostinato Generator"
    pattern: str | list[int] = "1-3-5-3"
    use_scale_degrees: bool = True
    repeat_notes: int = 1
    pattern_length: float | None = None
    insert_root_every: int = 0
    changed_notes_count: int = 0
    possible_intervals: frozenset[int] = field(default_factory=lambda: DEFAULT_INTERVALS)
    accent_pattern: list[float] = field(default_factory=lambda: [1.2, 0.8, 1.0, 0.9])
    rhythm: RhythmGenerator | None = None

    # Humanization
    timing_jitter: float = 0.0
    velocity_jitter: int = 0
    duration_jitter: float = 0.0
    seed: int | None = None
    random_seed: int | None = None

    # Phrase Generator
    phrase_length: float | None = None
    phrase_ending: str = "none"  # "none", "root", "fifth", "silence", "hold"

    # Pattern Morphing
    patterns: list[str | list[int]] | None = None
    change_pattern_every: float | None = None
    pattern_transition_mode: str = "sequential"  # "sequential", "random"

    # Variation Engine
    variation_probability: float = 0.0
    variation_types: list[str] = field(default_factory=lambda: ["repeat", "skip", "neighbor", "octave"])

    # Legacy support
    shape: list[int] | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str | list[int] | None = None,
        shape: list[int] | None = None,
        use_scale_degrees: bool = True,
        repeat_notes: int = 1,
        pattern_length: float | None = None,
        insert_root_every: int = 0,
        changed_notes_count: int = 0,
        possible_intervals: frozenset[int] | None = None,
        accent_pattern: list[float] | None = None,
        rhythm: RhythmGenerator | None = None,
        timing_jitter: float = 0.0,
        velocity_jitter: int = 0,
        duration_jitter: float = 0.0,
        seed: int | None = None,
        random_seed: int | None = None,
        phrase_length: float | None = None,
        phrase_ending: str = "none",
        patterns: list[str | list[int]] | None = None,
        change_pattern_every: float | None = None,
        pattern_transition_mode: str = "sequential",
        variation_probability: float = 0.0,
        variation_types: list[str] | None = None,
    ) -> None:
        super().__init__(params)

        # Resolve pattern: pattern param > shape param > default
        if pattern is not None:
            self.pattern = pattern
            self.use_scale_degrees = use_scale_degrees
        elif shape is not None:
            self.pattern = shape
            self.use_scale_degrees = False  # Legacy: chord tone indices
        else:
            self.pattern = "1-3-5-3"
            self.use_scale_degrees = use_scale_degrees
        self.repeat_notes = max(1, repeat_notes)
        self.pattern_length = pattern_length
        self.insert_root_every = insert_root_every if insert_root_every > 0 else 0
        self.changed_notes_count = changed_notes_count if changed_notes_count > 0 else 0
        self.possible_intervals = (
            possible_intervals if possible_intervals is not None else DEFAULT_INTERVALS
        )
        self.accent_pattern = accent_pattern if accent_pattern is not None else [1.2, 0.8, 1.0, 0.9]
        self.rhythm = rhythm

        self.timing_jitter = timing_jitter
        self.velocity_jitter = velocity_jitter
        self.duration_jitter = duration_jitter
        self.seed = seed if seed is not None else random_seed
        self.random_seed = self.seed
        self.phrase_length = phrase_length
        self.phrase_ending = phrase_ending
        self.patterns = patterns
        self.change_pattern_every = change_pattern_every
        self.pattern_transition_mode = pattern_transition_mode
        self.variation_probability = variation_probability
        self.variation_types = variation_types if variation_types is not None else ["repeat", "skip", "neighbor", "octave"]

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        # Localized RNG to guarantee determinism
        rng = random.Random(self.seed)

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        prev_chord: ChordLabel | None = None
        prev_pitch: int | None = None
        last_chord: ChordLabel | None = None
        prev_deg: int | None = None

        pat_idx = 0
        note_count = 0
        pattern_start_beat = 0.0
        skip_until = 0.0
        last_pattern_idx = -1

        for event_idx, event in enumerate(events):
            if event.onset < skip_until:
                continue

            chord = chord_at(chords, event.onset)
            if chord is None:
                continue

            # Retrigger pattern if pattern_length is set
            if (
                self.pattern_length is not None
                and (event.onset - pattern_start_beat) >= self.pattern_length
            ):
                pat_idx = 0
                pattern_start_beat = event.onset

            # Get active pattern degrees for the current time (supports Pattern Morphing)
            degrees, active_pat_idx = self._get_pattern_for_time(event.onset)
            if not degrees:
                continue

            # Reset pattern index at morph boundaries for better phrasing
            if self.change_pattern_every is not None and self.patterns and len(self.patterns) > 1:
                if active_pat_idx != last_pattern_idx:
                    pat_idx = 0
                    last_pattern_idx = active_pat_idx

            # Determine current degree from pattern
            deg = degrees[pat_idx % len(degrees)]

            # Apply Variation Engine
            apply_octave_shift = 0
            if self.variation_probability > 0.0 and rng.random() < self.variation_probability and self.variation_types:
                v_type = rng.choice(self.variation_types)
                if v_type == "skip":
                    note_count += 1
                    if note_count % self.repeat_notes == 0:
                        pat_idx += 1
                    continue
                elif v_type == "repeat":
                    if prev_deg is not None:
                        deg = prev_deg
                elif v_type == "neighbor":
                    deg = max(1, deg + rng.choice([-1, 1]))
                elif v_type == "octave":
                    apply_octave_shift = rng.choice([12, -12])

            # Insert root every N notes
            if (
                self.insert_root_every > 0
                and note_count > 0
                and note_count % self.insert_root_every == 0
            ):
                deg = 1

            # Phrase Generator logic
            if self.phrase_length is not None:
                phrase_beat = event.onset % self.phrase_length
                
                # Determine if this is the last event in the current phrase
                is_last_in_phrase = False
                current_phrase_idx = int(event.onset // self.phrase_length)
                if event_idx + 1 == len(events):
                    is_last_in_phrase = True
                else:
                    next_phrase_idx = int(events[event_idx + 1].onset // self.phrase_length)
                    if next_phrase_idx > current_phrase_idx:
                        is_last_in_phrase = True

                if self.phrase_ending == "silence":
                    # Silence the ending window
                    if self.phrase_length - phrase_beat <= 1.0 or is_last_in_phrase:
                        continue
                    note_duration = event.duration
                elif self.phrase_ending == "root" and is_last_in_phrase:
                    deg = 1
                    note_duration = event.duration
                elif self.phrase_ending == "fifth" and is_last_in_phrase:
                    deg = 5
                    note_duration = event.duration
                elif self.phrase_ending == "hold" and (self.phrase_length - phrase_beat <= 1.0 or is_last_in_phrase):
                    # Hold note until phrase end and skip the rest of the phrase
                    phrase_end = (current_phrase_idx + 1) * self.phrase_length
                    note_duration = max(0.1, phrase_end - event.onset)
                    skip_until = phrase_end
                else:
                    note_duration = event.duration
            else:
                note_duration = event.duration

            if self.use_scale_degrees:
                # Apply possible_intervals constraint (only in scale degree mode)
                interval_from_root = deg - 1
                if (
                    interval_from_root not in self.possible_intervals
                    and -interval_from_root not in self.possible_intervals
                ):
                    deg = self._snap_to_allowed_interval(deg)

                # Get pitch from scale degree
                pitch = self._degree_to_pitch(deg, chord, key, prev_pitch)
            else:
                # Legacy mode: use chord tone indices directly
                pitch = self._chord_index_to_pitch(deg - 1, chord)

            # Apply octave shift from variation engine
            if apply_octave_shift != 0:
                pitch = max(0, min(127, pitch + apply_octave_shift))

            # Voice-lead on chord change
            if chord != prev_chord and prev_chord is not None and prev_pitch is not None:
                pitch = self._voice_lead_pitch(pitch, prev_pitch)

            # Velocity calculations with accent tied to beat position in bar
            base_vel = self._velocity()
            # accent_pattern indexed by beat position, not pattern index
            # e.g. 4/4: beat 0=strong, 1=weak, 2=medium, 3=weak
            beat_in_bar = int(event.onset) % len(self.accent_pattern)
            accent = self.accent_pattern[beat_in_bar]
            vel = int(base_vel * accent)
            if self.velocity_jitter > 0:
                vel += rng.randint(-self.velocity_jitter, self.velocity_jitter)
            vel = max(1, min(127, vel))

            # Apply Humanization (timing and duration jitter)
            final_onset = event.onset
            if self.timing_jitter > 0.0:
                final_onset += rng.uniform(-self.timing_jitter, self.timing_jitter)
            final_onset = max(0.0, round(final_onset, 6))

            final_duration = note_duration
            if self.duration_jitter > 0.0 and self.phrase_ending != "hold":
                final_duration += rng.uniform(-self.duration_jitter, self.duration_jitter)
            final_duration = max(0.01, round(final_duration, 6))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=final_onset,
                    duration=final_duration,
                    velocity=vel,
                )
            )

            prev_pitch = pitch
            prev_chord = chord
            last_chord = chord
            prev_deg = deg
            note_count += 1

            # Advance pattern index every repeat_notes steps
            if note_count % self.repeat_notes == 0:
                pat_idx += 1

        # Make sure notes are strictly sorted by start time after timing humanization
        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    # ------------------------------------------------------------------
    # Pattern resolution
    # ------------------------------------------------------------------

    def _resolve_pattern_value(self, pat: str | list[int]) -> list[int]:
        """Convert a pattern value to a list of scale degrees (1-based)."""
        if isinstance(pat, str):
            if pat in NAMED_PATTERNS:
                return list(NAMED_PATTERNS[pat])
            try:
                return [int(x) for x in pat.split("-")]
            except ValueError:
                return [1, 3, 5, 3]
        elif isinstance(pat, list):
            if self.use_scale_degrees:
                return list(pat)
            else:
                return [d + 1 for d in pat]
        return [1, 3, 5, 3]

    def _get_pattern_for_time(self, onset: float) -> tuple[list[int], int]:
        """Supports pattern morphing by returning (resolved_pattern, active_pattern_index)."""
        if self.patterns and self.change_pattern_every:
            idx = int(onset // self.change_pattern_every)
            if self.pattern_transition_mode == "random":
                # Seeding local Random block deterministically for this transition point
                state_rng = random.Random((self.seed or 0) + idx + 12345)
                active_idx = state_rng.randint(0, len(self.patterns) - 1)
            else:
                active_idx = idx % len(self.patterns)
            pat = self.patterns[active_idx]
            return self._resolve_pattern_value(pat), active_idx
        return self._resolve_pattern_value(self.pattern), -1

    def _resolve_pattern(self) -> list[int]:
        """Convert pattern param to a list of scale degrees (1-based)."""
        return self._resolve_pattern_value(self.pattern)


    # ------------------------------------------------------------------
    # Pitch computation
    # ------------------------------------------------------------------

    def _degree_to_pitch(
        self,
        degree: int,
        chord: ChordLabel,
        key: Scale,
        prev_pitch: int | None,
    ) -> int:
        """Convert a scale degree (1-7) to a MIDI pitch."""
        # Get pitch class from scale degree
        degs = key.degrees()
        if not degs:
            return self.params.key_range_low

        # 1-based degree → 0-based index into scale degrees
        deg_idx = (degree - 1) % len(degs)
        pc = degs[deg_idx]

        # Octave shift for degrees outside 1-7
        octave_shift = (degree - 1) // len(degs)

        # Base octave from range center
        range_center = (self.params.key_range_low + self.params.key_range_high) // 2
        base_octave = range_center // 12

        pitch = (base_octave + octave_shift) * 12 + pc

        # If we have a previous note, voice lead to it
        if prev_pitch is not None:
            pitch = self._voice_lead_pitch(pitch, prev_pitch)

        # Clamp to range
        pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

        return int(pitch)

    def _chord_index_to_pitch(self, index: int, chord: ChordLabel) -> int:
        """Legacy mode: convert chord tone index to MIDI pitch."""
        tones = chord_pitches_closed(chord, self.params.key_range_low)
        if not tones:
            return self.params.key_range_low
        octave = index // len(tones)
        base_idx = index % len(tones)
        pitch = tones[base_idx] + 12 * octave
        return max(0, min(127, pitch))

    def _snap_to_allowed_interval(self, degree: int) -> int:
        """Snap a degree to the nearest allowed interval."""
        interval = degree - 1
        if not self.possible_intervals:
            return degree

        # Find closest allowed interval
        best = min(self.possible_intervals, key=lambda x: abs(x - interval))
        return best + 1

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default fallback: 16th notes
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.20))
            t += 0.25
        return events

    def _voice_lead_pitch(self, new_pitch: int, prev_pitch: int) -> int:
        """Shift new_pitch by octaves to be closest to prev_pitch."""
        while new_pitch - prev_pitch > 6:
            new_pitch -= 12
        while prev_pitch - new_pitch > 6:
            new_pitch += 12
        return max(0, min(127, new_pitch))

    def _velocity(self) -> int:
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            return (v_min + v_max) // 2
        return int(60 + self.params.density * 30)
