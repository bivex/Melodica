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

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        degrees = self._resolve_pattern()
        if not degrees:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        prev_chord: ChordLabel | None = None
        prev_pitch: int | None = None
        last_chord: ChordLabel | None = None

        pat_idx = 0
        note_count = 0
        pattern_start_beat = 0.0

        for event in events:
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

            # Determine current degree from pattern
            deg = degrees[pat_idx % len(degrees)]

            # Insert root every N notes
            if (
                self.insert_root_every > 0
                and note_count > 0
                and note_count % self.insert_root_every == 0
            ):
                deg = 1

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

            # Voice-lead on chord change
            if chord != prev_chord and prev_chord is not None and prev_pitch is not None:
                pitch = self._voice_lead_pitch(pitch, prev_pitch)

            base_vel = self._velocity()
            accent = self.accent_pattern[pat_idx % len(self.accent_pattern)]
            vel = int(base_vel * accent)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(0, min(127, vel)),
                )
            )

            prev_pitch = pitch
            prev_chord = chord
            last_chord = chord
            note_count += 1

            # Advance pattern index every repeat_notes steps
            if note_count % self.repeat_notes == 0:
                pat_idx += 1

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

    def _resolve_pattern(self) -> list[int]:
        """Convert pattern param to a list of scale degrees (1-based)."""
        if isinstance(self.pattern, str):
            if self.pattern in NAMED_PATTERNS:
                return list(NAMED_PATTERNS[self.pattern])
            # Try parsing custom "1-3-5-7" string
            try:
                return [int(x) for x in self.pattern.split("-")]
            except ValueError:
                return [1, 3, 5, 3]
        elif isinstance(self.pattern, list):
            if self.use_scale_degrees:
                return list(self.pattern)
            else:
                # Legacy: chord tone indices → keep as 1-based for uniform handling
                # (render() will call _chord_index_to_pitch with deg-1)
                return [d + 1 for d in self.pattern]
        return [1, 3, 5, 3]

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

        # Base octave from anchor or range
        anchor = (
            prev_pitch
            if prev_pitch is not None
            else (self.params.key_range_low + self.params.key_range_high) // 2
        )
        # Snap anchor to root pitch class of the scale
        root_pc = degs[0]
        base_octave = anchor // 12
        anchor_pc = anchor % 12
        if anchor_pc > root_pc:
            base_octave += 1

        pitch = (base_octave + octave_shift) * 12 + pc

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
        return int(60 + self.params.density * 30)
