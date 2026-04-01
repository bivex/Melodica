"""
generators/strum.py -- StrumPatternGenerator.

Layer: Application / Domain
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import (
    chord_pitches_closed,
    chord_pitches_open,
    chord_pitches_spread,
    chord_at,
    build_guitar_voicing,
)


# Built-in meter-aware strum patterns (list of directions per subdivision).
# 1 = downstrum, -1 = upstrum, 0 = skip/no-strum
STRUM_PATTERNS: dict[str, list[int]] = {
    # 4/4 patterns (8 subdivisions = 8th note grid)
    "folk_4_4": [1, -1, 1, -1, 1, -1, 1, -1],
    "rock_4_4": [1, 0, -1, 0, 1, 0, -1, 0],
    "ballad_4_4": [1, 0, 0, 0, -1, 0, 0, 0],
    "punk_4_4": [1, 1, 1, 1, 1, 1, 1, 1],
    "reggae_4_4": [0, -1, 0, 1, 0, -1, 0, 1],
    # 3/4 patterns (6 subdivisions)
    "waltz_3_4": [1, 0, 0, -1, 0, 0],
    # 6/8 patterns (6 subdivisions)
    "compound_6_8": [1, 0, -1, 1, 0, -1],
}


# Maps density to fraction of strings to include per strum
DENSITY_MAP: dict[str, float] = {
    "low": 0.3,
    "low_medium": 0.45,
    "medium": 0.6,
    "medium_high": 0.75,
    "high": 1.0,
}


@dataclass
class StrumPatternGenerator(PhraseGenerator):
    """
    Generates chords with a built-in strum delay (arpeggiation of block chords).

    Supports named meter-aware patterns that reset at bar lines.
    direction_pattern: 1 = downstrum (low to high), -1 = upstrum (high to low).
    pattern_name: one of STRUM_PATTERNS keys (overrides direction_pattern).
    beats_per_bar: meter top number (resets pattern at each bar).

    options:
        polyphony: number of strings/voices to include (max 9).
        density:   "low" | "low_medium" | "medium" | "medium_high" | "high"
                   Controls how many strings participate in each strum.
    """

    name: str = "Strum Pattern"
    strum_delay: float = 0.02
    voicing: str = "guitar"
    direction_pattern: list[int] = field(default_factory=lambda: [1, -1, 1, -1])
    pattern_name: str | None = None
    beats_per_bar: int = 4
    subdivisions_per_bar: int = 8
    polyphony: int = 6
    density_strum: str = "medium"
    rhythm: RhythmGenerator | None = None
    note_range_low: int | None = None
    note_range_high: int | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        strum_delay: float = 0.02,
        voicing: str = "guitar",
        direction_pattern: list[int] | None = None,
        pattern_name: str | None = None,
        beats_per_bar: int = 4,
        subdivisions_per_bar: int = 8,
        polyphony: int = 6,
        density: str = "medium",
        rhythm: RhythmGenerator | None = None,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
    ) -> None:
        super().__init__(params)
        self.strum_delay = max(0.0, strum_delay)
        valid_voicings = {"closed", "open", "spread", "guitar"}
        if voicing not in valid_voicings:
            raise ValueError(f"voicing must be in {valid_voicings}")
        self.voicing = voicing
        self.pattern_name = pattern_name
        self.beats_per_bar = max(1, beats_per_bar)
        self.subdivisions_per_bar = max(1, subdivisions_per_bar)
        self.polyphony = max(1, min(9, polyphony))
        if density not in DENSITY_MAP:
            raise ValueError(f"density must be one of {sorted(DENSITY_MAP)}; got {density!r}")
        self.density_strum = density
        self.rhythm = rhythm
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high

        if pattern_name and pattern_name in STRUM_PATTERNS:
            self.direction_pattern = STRUM_PATTERNS[pattern_name]
        else:
            self.direction_pattern = direction_pattern if direction_pattern else [1, -1, 1, -1]
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
        last_chord = chords[0]
        last_strum_pitches: list[int] = []

        seq_idx = 0
        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Reset pattern index at each bar line
            bar_start = (event.onset % self.beats_per_bar) < 0.01
            if bar_start:
                seq_idx = 0

            direction = self.direction_pattern[seq_idx % len(self.direction_pattern)]
            seq_idx += 1

            # Skip no-strum beats
            if direction == 0:
                continue

            pitches = self._get_voicing(chord)
            if not pitches:
                continue

            sorted_pitches = sorted(pitches)
            if direction < 0:
                sorted_pitches = list(reversed(sorted_pitches))
            last_strum_pitches = sorted_pitches

            base_vel = self._velocity()
            # Beat strength is already encoded in event.velocity_factor;
            # no separate accent multiplier needed here.
            vel = int(base_vel * event.velocity_factor)

            for i, pitch in enumerate(sorted_pitches):
                delay = i * self.strum_delay
                clamped_delay = min(delay, max(0.0, event.duration - 0.01))
                string_vel = vel if i == 0 else int(vel * 0.85)

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset + clamped_delay, 6),
                        duration=max(0.05, event.duration - clamped_delay),
                        velocity=max(1, min(127, string_vel)),
                    )
                )

        notes = self._apply_phrase_arch(notes, duration_beats, context.phrase_position if context else 0.0)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=last_strum_pitches,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        slot_duration = self.beats_per_bar / self.subdivisions_per_bar
        half_bar = self.subdivisions_per_bar // 2
        t, events = 0.0, []
        while t < duration_beats:
            bar_pos = t % self.beats_per_bar
            # Round to nearest subdivision index to avoid float drift
            subdiv_in_bar = round(bar_pos / slot_duration) % self.subdivisions_per_bar
            # Velocity contour that reflects actual beat strength:
            #   beat 1 (subdiv 0)         → strong downbeat   1.00
            #   beat 3 / half-bar         → medium strong     0.90
            #   on-beat subdivisions      → medium             0.85
            #   off-beat (upstrum) slots  → weak               0.75
            if subdiv_in_bar == 0:
                vel_factor = 1.0
            elif subdiv_in_bar == half_bar:
                vel_factor = 0.9
            elif subdiv_in_bar % 2 == 0:
                vel_factor = 0.85
            else:
                vel_factor = 0.75
            events.append(
                RhythmEvent(
                    onset=round(t, 6),
                    duration=round(slot_duration * 0.9, 6),
                    velocity_factor=vel_factor,
                )
            )
            t += slot_duration
        return events

    def _velocity(self) -> int:
        return int(65 + self.params.density * 35)

    def _get_voicing(self, chord: ChordLabel) -> list[int]:
        if self.voicing == "closed":
            base = chord_pitches_closed(chord, self.params.key_range_low)
        elif self.voicing == "open":
            base = chord_pitches_open(chord, self.params.key_range_low)
        elif self.voicing == "spread":
            base = chord_pitches_spread(chord, self.params.key_range_low)
        else:
            base = build_guitar_voicing(
                chord, anchor=max(40, self.params.key_range_low), min_voices=5
            )

        # Filter by note range BEFORE applying polyphony limit
        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        base = [p for p in base if low <= p <= high]

        # Apply polyphony limit
        base = base[: self.polyphony]

        # Apply density — include only a fraction of strings
        frac = DENSITY_MAP.get(self.density_strum, 0.6)
        count = max(1, int(len(base) * frac))
        return base[:count]

    def _apply_phrase_arch(self, notes, duration_beats, phrase_position=0.0):
        if not notes or duration_beats <= 0:
            return notes
        arch_height = 0.3 + 0.2 * phrase_position
        for note in notes:
            progress = note.start / duration_beats
            arch = 1.0 - arch_height + arch_height * math.sin(progress * math.pi * 0.7)
            note.velocity = max(1, min(127, int(note.velocity * arch)))
        return notes
