"""
generators/fingerpicking.py — Specialized generator for guitar fingerpicking.

Layer: Application / Domain

options:
    notes_to_use:      indices of chord tones to include (#1=0, #2=1, ...)
    retrigger:         retrigger pattern every N beats (0 = never)
    sustain_notes:     "no", "yes", "bottom_note", "bottom_two"
    dedicated_bass:    "none", or bass string index
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import semitones_up, chord_at, build_guitar_voicing

SUSTAIN_OPTIONS = {"no", "yes", "bottom_note", "bottom_two"}


@dataclass
class FingerpickingGenerator(PhraseGenerator):
    """
    Simulates guitar strings being plucked sequentially.

    pattern:          e.g. [0, 2, 1, 3] points to the strings (0 is lowest/bass).
    notes_to_use:     which chord tones to include (indices, 0-based).
                      [0,1,2,3,4] = use 5 notes from voicing.
    retrigger:        retrigger pattern every N beats (0 = never).
    sustain_notes:    "no" | "yes" | "bottom_note" | "bottom_two"
    strum_delay:      if > 0, introduces delay between simultaneous notes.
    """

    name: str = "Fingerpicking Generator"
    pattern: list[int] = field(default_factory=lambda: [0, 2, 1, 3])
    notes_to_use: list[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    retrigger: float = 0.0
    sustain_notes: str = "no"
    strum_delay: float = 0.0
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: list[int] | None = None,
        notes_to_use: list[int] | None = None,
        retrigger: float = 0.0,
        sustain_notes: str = "no",
        strum_delay: float = 0.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern if pattern is not None else [0, 2, 1, 3]
        self.notes_to_use = notes_to_use if notes_to_use is not None else [0, 1, 2, 3, 4]
        self.retrigger = max(0.0, retrigger)
        if sustain_notes not in SUSTAIN_OPTIONS:
            raise ValueError(
                f"sustain_notes must be one of {sorted(SUSTAIN_OPTIONS)}; got {sustain_notes!r}"
            )
        self.sustain_notes = sustain_notes
        self.strum_delay = max(0.0, strum_delay)
        self.rhythm = rhythm
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

        seq_idx = 0
        pattern_start_beat = 0.0
        last_chord = chords[0]

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Retrigger pattern
            if self.retrigger > 0 and (event.onset - pattern_start_beat) >= self.retrigger:
                seq_idx = 0
                pattern_start_beat = event.onset

            guitar_voicing = build_guitar_voicing(chord, anchor=max(40, self.params.key_range_low))

            if not guitar_voicing:
                continue

            # Filter voicing by notes_to_use
            filtered = [guitar_voicing[i] for i in self.notes_to_use if i < len(guitar_voicing)]
            if not filtered:
                filtered = guitar_voicing

            # Figure out which 'string' to pluck
            string_idx = self.pattern[seq_idx % len(self.pattern)]
            string_idx = min(string_idx, len(filtered) - 1)

            pitch = filtered[string_idx]

            # Sustain logic
            is_bottom = string_idx == 0
            is_bottom_two = string_idx <= 1
            if self.sustain_notes == "yes":
                duration = event.duration * 2.0  # sustained
            elif self.sustain_notes == "bottom_note" and is_bottom:
                duration = event.duration * 2.0
            elif self.sustain_notes == "bottom_two" and is_bottom_two:
                duration = event.duration * 2.0
            else:
                duration = event.duration

            base_vel = self._velocity()
            vel = int(base_vel * event.velocity_factor)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(duration, 6),
                    velocity=max(0, min(127, vel)),
                )
            )

            seq_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=[notes[-1].pitch],
            )

        return notes

    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default fallback: 8th notes
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.45))
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
