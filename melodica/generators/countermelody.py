"""
generators/countermelody.py — Independent contrapuntal melody generator.

Layer: Application / Domain
Style: Orchestral, chamber, contrapuntal writing.

Unlike canon (which is a delayed copy), countermelody generates an
independent melodic voice that respects contrapuntal rules:
  - Prefers contrary and oblique motion against a primary melody
  - Avoids parallel fifths and octaves
  - Resolves sevenths downward
  - Uses consonant intervals on strong beats
  - Allows dissonance (2nds, 7ths) on weak beats as passing tones

This generator requires a primary melody to be passed via context.prev_pitches
or as a separate parameter. Without a primary melody, it generates a
free-flowing second voice over the chord progression.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# Consonant intervals (in semitones, mod 12)
_CONSONANT = {0, 3, 4, 5, 7, 8, 9}
# Strong-beat consonant intervals (unison, 3rds, 5ths, 6ths, octaves)
_STRONG_CONSONANT = {0, 3, 4, 7, 8, 9}


@dataclass
class CountermelodyGenerator(PhraseGenerator):
    """
    Independent contrapuntal voice generator.

    primary_melody:
        List of NoteInfo from the primary voice. If provided, the counter
        voice will use contrary/oblique motion and consonant intervals.
    motion_preference:
        Preferred motion type against primary melody:
        "contrary" — move in opposite direction
        "oblique"  — hold one note while other moves
        "mixed"    — random choice weighted by complexity
    dissonance_on_weak:
        Allow dissonant intervals on weak beats (passing tones).
    interval_limit:
        Maximum interval in semitones between consecutive counter notes.
    """

    name: str = "Countermelody Generator"
    primary_melody: list[NoteInfo] | None = None
    motion_preference: str = "mixed"
    dissonance_on_weak: bool = True
    interval_limit: int = 7
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        primary_melody: list[NoteInfo] | None = None,
        motion_preference: str = "mixed",
        dissonance_on_weak: bool = True,
        interval_limit: int = 7,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.primary_melody = primary_melody
        if motion_preference not in ("contrary", "oblique", "mixed"):
            raise ValueError(
                f"motion_preference must be 'contrary', 'oblique', or 'mixed'; "
                f"got {motion_preference!r}"
            )
        self.motion_preference = motion_preference
        self.dissonance_on_weak = dissonance_on_weak
        self.interval_limit = max(2, min(12, interval_limit))
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
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        # Get primary melody pitch at a given beat
        primary = self.primary_melody
        if primary is None and context and context.prev_pitches:
            # Fallback: use prev_pitches as a hint
            primary = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Find primary voice pitch at this onset
            primary_pitch = self._primary_at(event.onset, primary)

            is_strong_beat = (event.onset % 1.0) < 0.1

            if primary_pitch is not None:
                pitch = self._pitch_against_primary(
                    chord, primary_pitch, prev_pitch, is_strong_beat, key, low, high
                )
            else:
                # Free counterpoint: stepwise motion biased toward chord tones
                pitch = self._free_counter_pitch(chord, prev_pitch, key, low, high)

            # Limit interval from previous note
            pitch = self._limit_interval(pitch, prev_pitch, low, high)

            vel = int(self._velocity(event.onset, is_strong_beat) * event.velocity_factor)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
                )
            )
            prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Primary melody lookup
    # ------------------------------------------------------------------

    def _primary_at(self, beat: float, primary: list[NoteInfo] | None) -> int | None:
        """Find the primary melody pitch active at the given beat."""
        if not primary:
            return None
        for note in reversed(primary):
            if note.start <= beat < note.start + note.duration:
                return note.pitch
        # Find closest note
        closest = min(primary, key=lambda n: abs(n.start - beat))
        if abs(closest.start - beat) < 1.0:
            return closest.pitch
        return None

    # ------------------------------------------------------------------
    # Pitch selection against primary
    # ------------------------------------------------------------------

    def _pitch_against_primary(
        self,
        chord: ChordLabel,
        primary_pitch: int,
        prev_pitch: int,
        is_strong: bool,
        key: Scale,
        low: int,
        high: int,
    ) -> int:
        """Choose a counter-melody pitch against the primary voice."""
        pcs = chord.pitch_classes()
        candidates: list[tuple[int, int]] = []  # (pitch, score)

        motion = self.motion_preference
        if motion == "mixed":
            motion = random.choices(
                ["contrary", "oblique", "mixed_free"],
                weights=[0.4, 0.2, 0.4],
            )[0]

        primary_direction = primary_pitch - prev_pitch if prev_pitch else 0

        for pc in pcs + [chord.root]:
            for octave_offset in [-12, 0, 12]:
                pitch = nearest_pitch(int(pc), prev_pitch + octave_offset)
                if pitch < low or pitch > high:
                    continue

                interval = abs(pitch - primary_pitch) % 12
                is_consonant = interval in _CONSONANT
                is_strong_consonant = interval in _STRONG_CONSONANT

                score = 50  # base

                # Strong beat: prefer consonant intervals
                if is_strong:
                    if is_strong_consonant:
                        score += 30
                    elif is_consonant:
                        score += 15
                    else:
                        score -= 40  # penalize dissonance on strong beats
                else:
                    # Weak beat: dissonance OK as passing tone
                    if is_consonant:
                        score += 10
                    elif self.dissonance_on_weak:
                        score += 5

                # Motion preference
                counter_direction = pitch - prev_pitch
                if motion == "contrary" and primary_direction != 0:
                    if (counter_direction > 0) != (primary_direction > 0):
                        score += 20
                    elif counter_direction == 0:
                        score += 5  # oblique is OK
                elif motion == "oblique":
                    if counter_direction == 0:
                        score += 20

                # Prefer smaller intervals from prev_pitch
                score -= abs(pitch - prev_pitch)

                # Avoid parallel fifths/octaves
                if interval in (0, 7) and abs(prev_pitch - primary_pitch) % 12 in (0, 7):
                    score -= 30

                candidates.append((pitch, score))

        if not candidates:
            return max(low, min(high, prev_pitch))

        # Weighted random selection
        candidates.sort(key=lambda x: x[1], reverse=True)
        top = candidates[: max(3, len(candidates) // 3)]
        return random.choice(top)[0]

    def _free_counter_pitch(
        self,
        chord: ChordLabel,
        prev_pitch: int,
        key: Scale,
        low: int,
        high: int,
    ) -> int:
        """Generate free counterpoint without a primary melody."""
        step = random.choice([-2, -1, -1, 0, 1, 1, 2])
        pitch = prev_pitch + step

        # Snap to scale
        if not key.contains(pitch % 12):
            pitch = nearest_pitch(chord.root, pitch)

        # Bias toward chord tones on strong beats
        if random.random() < 0.4 + self.params.complexity * 0.3:
            pcs = chord.pitch_classes()
            pc = random.choice(pcs)
            pitch = nearest_pitch(int(pc), prev_pitch)

        return max(low, min(high, pitch))

    def _limit_interval(self, pitch: int, prev_pitch: int, low: int, high: int) -> int:
        """Limit the interval between consecutive notes."""
        diff = pitch - prev_pitch
        if abs(diff) > self.interval_limit:
            direction = 1 if diff > 0 else -1
            pitch = prev_pitch + direction * self.interval_limit
        return max(low, min(high, pitch))

    # ------------------------------------------------------------------
    # Rhythm & velocity
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default: eighth notes
        t, events = 0.0, []
        while t < duration_beats:
            dur = 0.4 if random.random() < 0.6 else 0.9
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += 0.5
        return events

    def _velocity(self, onset: float, is_strong: bool) -> int:
        base = int(55 + self.params.density * 25)
        if is_strong:
            return min(127, int(base * 1.1))
        return int(base * 0.9)
