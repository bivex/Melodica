"""
generators/modern_chord.py — ModernChordPatternGenerator.

Extended chord voicings with rhythmic patterns.
add9, sus2, sus4, maj7, min7 — played as rhythmic stabs or swells.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, Quality
from melodica.utils import chord_pitches_closed, chord_pitches_open, chord_at


# Rhythm patterns (beat offsets within a bar)
STAB_PATTERNS: dict[str, list[float]] = {
    "syncopated": [0.0, 0.75, 1.5, 2.0, 2.75, 3.5],
    "straight": [0.0, 1.0, 2.0, 3.0],
    "offbeat": [0.5, 1.5, 2.5, 3.5],
    "sparse": [0.0, 2.0],
    "dense": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
}

# Extension offsets (semitones from root)
EXTENSIONS = {
    "add9": [0, 4, 7, 14],  # root, 3rd, 5th, 9th
    "sus2": [0, 2, 7],  # root, 2nd, 5th
    "sus4": [0, 5, 7],  # root, 4th, 5th
    "maj7": [0, 4, 7, 11],  # root, 3rd, 5th, 7th
    "min7": [0, 3, 7, 10],  # root, b3, 5th, b7
    "dom7": [0, 4, 7, 10],  # root, 3rd, 5th, b7
    "maj9": [0, 4, 7, 11, 14],  # root, 3rd, 5th, 7th, 9th
}


@dataclass
class ModernChordPatternGenerator(PhraseGenerator):
    """
    Modern chord patterns with extended voicings and rhythmic stabs.

    extension:   which chord extension to use
    stab_pattern: rhythm pattern name
    voicing:     "closed" | "open"
    """

    name: str = "Modern Chord Pattern"
    extension: str = "add9"
    stab_pattern: str = "syncopated"
    voicing: str = "closed"
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        extension: str = "add9",
        stab_pattern: str = "syncopated",
        voicing: str = "closed",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.extension = extension
        self.stab_pattern = stab_pattern
        self.voicing = voicing
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
        last_chord = chords[0]

        low = self.params.key_range_low

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Build extended voicing
            ext_offsets = EXTENSIONS.get(self.extension, [0, 4, 7])
            pitches = []
            for offset in ext_offsets:
                pc = (chord.root + offset) % 12
                octave = offset // 12
                pitch = (low // 12 + octave) * 12 + pc
                while pitch < low:
                    pitch += 12
                pitches.append(pitch)

            # Clamp to range
            pitches = [
                p for p in pitches if self.params.key_range_low <= p <= self.params.key_range_high
            ]

            if not pitches:
                continue

            # Staccato duration
            dur = min(event.duration * 0.3, 0.3)

            # Velocity pattern: accented on downbeats
            is_downbeat = (event.onset % 2.0) < 0.1
            base_vel = int(70 + self.params.density * 30)
            vel = int(base_vel * (1.15 if is_downbeat else 0.85) * event.velocity_factor)

            for p in pitches:
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(event.onset, 6),
                        duration=round(dur, 6),
                        velocity=max(1, min(127, vel)),
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )

        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        pattern = STAB_PATTERNS.get(self.stab_pattern, STAB_PATTERNS["syncopated"])
        t, events, idx = 0.0, [], 0
        while t < duration_beats:
            offset = pattern[idx % len(pattern)]
            onset = t + offset
            if onset < duration_beats:
                events.append(RhythmEvent(onset=round(onset, 6), duration=0.25))
            idx += 1
            if idx % len(pattern) == 0:
                t += 4.0  # next bar
        return events

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)
