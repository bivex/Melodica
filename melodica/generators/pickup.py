"""
generators/pickup.py — Pickup notes / anacrusis generator.

Layer: Application / Domain
Style: All genres.

Generates a short anacrusis (pickup) phrase leading into the downbeat
of the next section. Pickup notes create momentum and natural phrasing.

Types:
    "scale_up"      — ascending scale fragment into the target note
    "scale_down"    — descending scale fragment
    "chromatic_up"  — chromatic approach from below
    "chromatic_down" — chromatic approach from above
    "arpeggio"      — chord arpeggio leading to root
    "rhythmic"      — repeated note with accelerating rhythm
    "blues_pickup"  — blues scale approach with b3 bend
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
class PickupGenerator(PhraseGenerator):
    """
    Pickup / anacrusis generator.

    Produces a short phrase (typically 1-2 beats) that leads into
    the downbeat of the next chord section.

    pickup_type:
        Type of pickup phrase.
    pickup_length:
        Duration in beats (typically 0.5, 1.0, or 2.0).
    target_on_downbeat:
        If True, the last note lands on the next chord's root.
        If False, the phrase is placed freely.
    """

    name: str = "Pickup Generator"
    pickup_type: str = "scale_down"
    pickup_length: float = 1.0
    target_on_downbeat: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pickup_type: str = "scale_down",
        pickup_length: float = 1.0,
        target_on_downbeat: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if pickup_type not in (
            "scale_up",
            "scale_down",
            "chromatic_up",
            "chromatic_down",
            "arpeggio",
            "rhythmic",
            "blues_pickup",
        ):
            raise ValueError(f"Unknown pickup_type: {pickup_type!r}")
        self.pickup_type = pickup_type
        self.pickup_length = max(0.25, min(4.0, pickup_length))
        self.target_on_downbeat = target_on_downbeat
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

        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        # Place pickups before each new chord region
        for i, chord in enumerate(chords):
            if i == 0:
                # No pickup before the very first chord
                continue

            # The pickup leads INTO this chord's start
            pickup_start = chord.start - self.pickup_length
            if pickup_start < 0:
                continue

            # Target pitch: root of the chord we're leading into
            target = nearest_pitch(chord.root, prev_pitch)
            target = max(low, min(high, target))

            pickup_notes = self._build_pickup(
                target, chord, key, pickup_start, self.pickup_length, prev_pitch, low, high
            )
            notes.extend(pickup_notes)
            if pickup_notes:
                prev_pitch = pickup_notes[-1].pitch
            last_chord = chord

        # Also handle regions longer than 4 bars — add internal pickups
        events = self._build_events(duration_beats) if self.rhythm else []
        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            target = nearest_pitch(chord.root, prev_pitch)
            target = max(low, min(high, target))
            pickup_start = event.onset
            pickup_dur = min(self.pickup_length, duration_beats - pickup_start)
            if pickup_dur <= 0:
                continue
            pickup_notes = self._build_pickup(
                target, chord, key, pickup_start, pickup_dur, prev_pitch, low, high
            )
            notes.extend(pickup_notes)
            if pickup_notes:
                prev_pitch = pickup_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------

    def _build_pickup(
        self,
        target: int,
        chord: ChordLabel,
        key: Scale,
        onset: float,
        dur: float,
        prev: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        vel = self._velocity()

        if self.pickup_type == "scale_down":
            return self._scale_pickup(target, key, onset, dur, low, high, vel, ascending=False)
        elif self.pickup_type == "scale_up":
            return self._scale_pickup(target, key, onset, dur, low, high, vel, ascending=True)
        elif self.pickup_type == "chromatic_down":
            return self._chromatic_pickup(target, onset, dur, low, high, vel, -1)
        elif self.pickup_type == "chromatic_up":
            return self._chromatic_pickup(target, onset, dur, low, high, vel, 1)
        elif self.pickup_type == "arpeggio":
            return self._arpeggio_pickup(target, chord, onset, dur, low, high, vel)
        elif self.pickup_type == "rhythmic":
            return self._rhythmic_pickup(target, onset, dur, vel)
        else:  # blues_pickup
            return self._blues_pickup(target, chord, onset, dur, low, high, vel)

    def _scale_pickup(
        self,
        target: int,
        key: Scale,
        onset: float,
        dur: float,
        low: int,
        high: int,
        vel: int,
        ascending: bool,
    ) -> list[NoteInfo]:
        degs = sorted(key.degrees())
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / steps

        # Build scale fragment leading to target
        target_pc = target % 12
        try:
            target_idx = degs.index(target_pc)
        except ValueError:
            target_idx = 0

        for i in range(steps):
            if ascending:
                idx = target_idx - steps + i
            else:
                idx = target_idx + steps - i
            pc = int(degs[idx % len(degs)])
            octave_shift = (idx // len(degs)) * 12
            pitch = nearest_pitch(pc, target) + octave_shift
            pitch = max(low, min(high, pitch))
            notes.append(
                NoteInfo(pitch=pitch, start=round(t, 6), duration=step_dur * 0.85, velocity=vel)
            )
            t += step_dur

        # Last note is the target
        if notes:
            notes[-1] = NoteInfo(
                pitch=target, start=notes[-1].start, duration=notes[-1].duration, velocity=vel
            )
        return notes

    def _chromatic_pickup(
        self,
        target: int,
        onset: float,
        dur: float,
        low: int,
        high: int,
        vel: int,
        direction: int,
    ) -> list[NoteInfo]:
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / steps
        for i in range(steps):
            p = target + direction * (steps - i)
            p = max(low, min(high, p))
            notes.append(
                NoteInfo(pitch=p, start=round(t, 6), duration=step_dur * 0.85, velocity=vel)
            )
            t += step_dur
        if notes:
            notes[-1] = NoteInfo(
                pitch=target, start=notes[-1].start, duration=notes[-1].duration, velocity=vel
            )
        return notes

    def _arpeggio_pickup(
        self,
        target: int,
        chord: ChordLabel,
        onset: float,
        dur: float,
        low: int,
        high: int,
        vel: int,
    ) -> list[NoteInfo]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [NoteInfo(pitch=target, start=round(onset, 6), duration=dur, velocity=vel)]
        pitches = [nearest_pitch(int(pc), target) for pc in pcs]
        pitches = sorted(set(max(low, min(high, p)) for p in pitches))
        notes = []
        t = onset
        step_dur = dur / max(len(pitches), 1)
        for p in pitches:
            notes.append(
                NoteInfo(pitch=p, start=round(t, 6), duration=step_dur * 0.85, velocity=vel)
            )
            t += step_dur
        if notes:
            notes[-1] = NoteInfo(
                pitch=target, start=notes[-1].start, duration=notes[-1].duration, velocity=vel
            )
        return notes

    def _rhythmic_pickup(self, target: int, onset: float, dur: float, vel: int) -> list[NoteInfo]:
        # Accelerating repetitions of the target note
        subdivisions = [0.5, 0.25, 0.25, 0.125]
        notes = []
        t = onset
        for sd in subdivisions:
            if t >= onset + dur:
                break
            rem = min(sd, onset + dur - t)
            notes.append(
                NoteInfo(pitch=target, start=round(t, 6), duration=rem * 0.8, velocity=vel)
            )
            t += sd
        return notes

    def _blues_pickup(
        self,
        target: int,
        chord: ChordLabel,
        onset: float,
        dur: float,
        low: int,
        high: int,
        vel: int,
    ) -> list[NoteInfo]:
        root = chord.root
        pool = [(root + ivl) % 12 for ivl in [0, 3, 5, 6, 7, 10]]
        steps = max(2, int(dur / 0.25))
        notes = []
        t = onset
        step_dur = dur / steps
        pitch = target + steps * 2
        for i in range(steps):
            pc = random.choice(pool)
            pitch = nearest_pitch(pc, pitch - 1)
            pitch = max(low, min(high, pitch))
            notes.append(
                NoteInfo(pitch=pitch, start=round(t, 6), duration=step_dur * 0.85, velocity=vel)
            )
            t += step_dur
        if notes:
            notes[-1] = NoteInfo(
                pitch=target, start=notes[-1].start, duration=notes[-1].duration, velocity=vel
            )
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        return []

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
