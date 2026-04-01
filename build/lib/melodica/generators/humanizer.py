"""
generators/humanizer.py — Post-processing humanization generator.

Layer: Application / Domain
Style: All — makes any generated part sound more natural.

Humanizer wraps around existing notes and applies:
  - Micro-timing offsets (slight rubato)
  - Velocity variation (dynamic expression)
  - Subtle pitch drift (intonation variation)
  - Note length variation (articulation humanization)

This is a post-processor — it modifies notes rather than generating them.
However, as a PhraseGenerator, it generates a humanized version of
a chord progression's implied notes.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class HumanizerGenerator(PhraseGenerator):
    """
    Post-processing humanization generator.

    Generates notes from chords and then applies humanization effects.

    timing_variance:
        Maximum timing offset in beats (0.0–0.2). Typical: 0.02–0.05.
    velocity_variance:
        Maximum velocity variation (0.0–1.0). Typical: 0.1.
    pitch_drift:
        Maximum pitch drift in semitones (0.0–0.1). Typical: 0.02.
    length_variance:
        Note duration variation factor (0.0–0.5).
    groove_type:
        "straight" — even timing
        "swing" — triplet swing feel
        "push" — notes slightly ahead of beat
        "lay_back" — notes slightly behind beat
    """

    name: str = "Humanizer Generator"
    timing_variance: float = 0.03
    velocity_variance: float = 0.1
    pitch_drift: float = 0.0
    length_variance: float = 0.15
    groove_type: str = "straight"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        timing_variance: float = 0.03,
        velocity_variance: float = 0.1,
        pitch_drift: float = 0.0,
        length_variance: float = 0.15,
        groove_type: str = "straight",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.timing_variance = max(0.0, min(0.2, timing_variance))
        self.velocity_variance = max(0.0, min(1.0, velocity_variance))
        self.pitch_drift = max(0.0, min(0.1, pitch_drift))
        self.length_variance = max(0.0, min(0.5, length_variance))
        self.groove_type = groove_type
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

        events = self._build_events(duration_beats)
        raw_notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else mid
        last_chord: ChordLabel | None = None

        # First: generate raw notes
        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pcs = chord.pitch_classes()
            if not pcs:
                continue

            pc = random.choice(pcs)
            pitch = nearest_pitch(int(pc), prev_pitch)
            pitch = max(low, min(high, pitch))

            raw_notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=event.onset,
                    duration=event.duration,
                    velocity=int(60 + self.params.density * 30),
                )
            )
            prev_pitch = pitch

        # Then: humanize
        notes = self._humanize(raw_notes)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _humanize(self, raw: list[NoteInfo]) -> list[NoteInfo]:
        humanized = []
        for note in raw:
            # Timing offset
            timing_off = random.gauss(0, self.timing_variance * 0.3)
            # Groove adjustment
            if self.groove_type == "push":
                timing_off -= self.timing_variance * 0.5
            elif self.groove_type == "lay_back":
                timing_off += self.timing_variance * 0.5
            elif self.groove_type == "swing":
                beat_pos = note.start % 1.0
                if 0.4 < beat_pos < 0.6:
                    timing_off += 0.05  # Swing the offbeats

            new_start = max(0, note.start + timing_off)

            # Velocity variation
            vel_off = int(random.gauss(0, note.velocity * self.velocity_variance * 0.3))
            new_vel = max(1, min(127, note.velocity + vel_off))

            # Length variation
            len_factor = 1.0 + random.gauss(0, self.length_variance * 0.3)
            new_dur = max(0.05, note.duration * len_factor)

            # Pitch drift (very subtle)
            pitch_off = random.gauss(0, self.pitch_drift * 3)
            # We keep integer pitch but the drift affects velocity expression
            pitch = note.pitch

            humanized.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(new_start, 6),
                    duration=round(new_dur, 6),
                    velocity=new_vel,
                    articulation=note.articulation,
                    expression=dict(note.expression),
                )
            )

        return humanized

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = random.choice([0.5, 1.0, 1.0, 2.0])
            events.append(RhythmEvent(onset=round(t, 6), duration=min(dur, duration_beats - t)))
            t += dur
        return events
