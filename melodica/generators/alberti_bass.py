"""
generators/alberti_bass.py — Alberti bass pattern generator.

Layer: Application / Domain
Style: Classical / romantic piano accompaniment.

Alberti bass is an accompaniment pattern that plays chord tones in the order
root – fifth – third – fifth (or variations). Named after Domenico Alberti,
it became the standard left-hand pattern in Classical-era keyboard music.

Pattern variants:
    "1-5-3-5"  — root-fifth-third-fifth (standard Alberti)
    "1-5-3-7"  — adds seventh on beat 4
    "1-3-5-3"  — root-third-fifth-third (Mozart variant)
    "1-5-6-5"  — root-fifth-sixth-fifth
    "1-4-3-5"  — root-fourth-third-fifth
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, nearest_pitch_above, chord_at


NAMED_PATTERNS: dict[str, list[int]] = {
    "1-5-3-5": [1, 5, 3, 5],
    "1-5-3-7": [1, 5, 3, 7],
    "1-3-5-3": [1, 3, 5, 3],
    "1-5-6-5": [1, 5, 6, 5],
    "1-4-3-5": [1, 4, 3, 5],
}


@dataclass
class AlbertiBassGenerator(PhraseGenerator):
    """
    Alberti bass: broken chord accompaniment pattern.

    pattern:
        Named pattern string or custom "1-5-3-5" string.
        Values are chord tone positions:
          1=root, 2=2nd, 3=3rd, 4=4th, 5=5th, 6=6th, 7=7th
    subdivision:
        Beat subdivision: 0.5 = eighth notes, 0.25 = sixteenth notes.
    voice_lead:
        When True, shift pitches by octaves for smooth voice leading.
    """

    name: str = "Alberti Bass Generator"
    pattern: str = "1-5-3-5"
    subdivision: float = 0.5
    voice_lead: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "1-5-3-5",
        subdivision: float = 0.5,
        voice_lead: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.subdivision = max(0.125, min(1.0, subdivision))
        self.voice_lead = voice_lead
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
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []

        prev_chord: ChordLabel | None = None
        prev_pitch: int | None = (
            context.prev_pitch if context and context.prev_pitch is not None else None
        )
        last_chord: ChordLabel | None = None
        pat_idx = 0

        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = prev_pitch if prev_pitch is not None else (low + high) // 2

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            deg = degrees[pat_idx % len(degrees)]
            pitch = self._degree_to_pitch(deg, chord, anchor)

            # Voice lead on chord change
            if self.voice_lead and chord != prev_chord and prev_pitch is not None:
                pitch = self._smooth_voice_lead(pitch, prev_pitch)

            pitch = max(low, min(high, pitch))

            vel = int(self._velocity() * event.velocity_factor)
            # Slight accent on root (first pattern position)
            if pat_idx % len(degrees) == 0:
                vel = min(127, int(vel * 1.1))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )

            prev_pitch = pitch
            prev_chord = chord
            pat_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Pitch computation
    # ------------------------------------------------------------------

    def _degree_to_pitch(self, degree: int, chord: ChordLabel, anchor: int) -> int:
        """
        Map a chord-tone degree (1=root, 3=third, 5=fifth, etc.) to a MIDI pitch.

        Uses chord.pitch_classes() for the actual intervals.
        """
        pcs = chord.pitch_classes()
        if not pcs:
            return anchor

        # degree 1 -> pcs[0], degree 3 -> pcs[1], degree 5 -> pcs[2], etc.
        # Map: 1->0, 2->?, 3->1, 4->?, 5->2, 6->?, 7->3
        degree_to_idx = {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 2, 7: 3}
        idx = degree_to_idx.get(degree, (degree - 1) % len(pcs))

        # For degrees beyond chord tones, use scale-based approach
        if idx < len(pcs):
            target_pc = pcs[idx]
        else:
            # Degree maps to an extension: compute from root
            target_pc = (chord.root + degree - 1) % 12

        pitch = nearest_pitch(target_pc, anchor)

        # Handle octave displacement for patterns spanning wide range
        if degree == 5 and len(pcs) > 1:
            # Fifth should be above third
            third_pc = pcs[1]
            third_pitch = nearest_pitch(third_pc, anchor)
            if pitch <= third_pitch:
                pitch += 12

        return pitch

    def _smooth_voice_lead(self, new_pitch: int, prev_pitch: int) -> int:
        """Shift new_pitch by octaves to minimize distance from prev_pitch."""
        while new_pitch - prev_pitch > 6:
            new_pitch -= 12
        while prev_pitch - new_pitch > 6:
            new_pitch += 12
        return max(0, min(127, new_pitch))

    # ------------------------------------------------------------------
    # Pattern & rhythm
    # ------------------------------------------------------------------

    def _resolve_pattern(self) -> list[int]:
        if self.pattern in NAMED_PATTERNS:
            return list(NAMED_PATTERNS[self.pattern])
        try:
            return [int(x) for x in self.pattern.split("-")]
        except ValueError:
            return [1, 5, 3, 5]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        dur = max(0.1, self.subdivision * 0.9)
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += self.subdivision
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 25)
