"""
generators/sax_solo.py — Saxophone solo improvisation generator.

Layer: Application / Domain
Style: Jazz, smooth jazz, R&B, fusion.

Simulates saxophone solo phrasing with bebop vocabulary, blues notes,
vibrato, and characteristic articulations.

Styles:
    "ballad"    — slow, lyrical, lots of sustained notes
    "bebop"     — fast, chromatic, complex bebop lines
    "fusion"    — jazz-rock fusion (wider intervals, odd groupings)
    "smooth"    — smooth jazz (pentatonic, accessible)
    "free"      — free improvisation
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
class SaxSoloGenerator(PhraseGenerator):
    """
    Saxophone solo improvisation generator.

    style:
        "ballad", "bebop", "fusion", "smooth", "free"
    vibrato_depth:
        0.0–1.0, velocity variation for vibrato simulation.
    breath_noise:
        Probability of a rest to simulate breath (0–1).
    blues_notes:
        Include blue notes (b3, b5, b7) in the vocabulary.
    chromaticism:
        How chromatic the lines are (0.0–1.0).
    """

    name: str = "Sax Solo Generator"
    style: str = "bebop"
    vibrato_depth: float = 0.3
    breath_noise: float = 0.1
    blues_notes: bool = True
    chromaticism: float = 0.5
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "bebop",
        vibrato_depth: float = 0.3,
        breath_noise: float = 0.1,
        blues_notes: bool = True,
        chromaticism: float = 0.5,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.style = style
        self.vibrato_depth = max(0.0, min(1.0, vibrato_depth))
        self.breath_noise = max(0.0, min(0.5, breath_noise))
        self.blues_notes = blues_notes
        self.chromaticism = max(0.0, min(1.0, chromaticism))
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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        sax_range_low = max(self.params.key_range_low, mid - 5)
        sax_range_high = min(self.params.key_range_high, mid + 19)

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else mid
        last_chord: ChordLabel | None = None
        phrase_count = 0

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Breath pause between phrases
            if phrase_count >= random.randint(4, 8):
                if random.random() < self.breath_noise:
                    phrase_count = 0
                    continue

            pitch = self._pick_pitch(chord, key, prev_pitch, sax_range_low, sax_range_high)

            # Vibrato
            vel = self._velocity()
            vibrato_var = int(self.vibrato_depth * 8)
            vel += random.randint(-vibrato_var, vibrato_var)
            vel = max(1, min(127, vel))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=vel,
                )
            )
            prev_pitch = pitch
            phrase_count += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, key: Scale, prev: int, low: int, high: int) -> int:
        pcs = chord.pitch_classes()
        degs = key.degrees()

        # Build note pool
        pool: list[int] = []
        for pc in pcs:
            pool.append(int(pc))
        if self.blues_notes:
            for ivl in [3, 6, 10]:  # b3, b5, b7
                pool.append((chord.root + ivl) % 12)

        if not pool:
            pool = [chord.root]

        if self.style == "bebop":
            # Chromatic approach
            if random.random() < self.chromaticism:
                return max(low, min(high, prev + random.choice([-1, 1])))
            # Chord tone with occasional leap
            if random.random() < 0.3:
                target = nearest_pitch(random.choice(pool), prev + random.choice([-7, -5, 5, 7]))
            else:
                target = nearest_pitch(random.choice(pool), prev)
            return max(low, min(high, target))

        elif self.style == "ballad":
            # Mostly stepwise, long notes
            if random.random() < 0.7:
                return max(low, min(high, prev + random.choice([-1, -1, 0, 1, 1])))
            pc = random.choice(pool)
            return max(low, min(high, nearest_pitch(pc, prev)))

        elif self.style == "fusion":
            # Wider intervals
            if random.random() < 0.4:
                return max(low, min(high, prev + random.choice([-5, -4, 4, 5, 7])))
            pc = random.choice(pool)
            return max(low, min(high, nearest_pitch(pc, prev)))

        elif self.style == "smooth":
            # Pentatonic, stepwise
            penta = [int(d) for d in degs[:5]] if len(degs) >= 5 else [chord.root]
            pc = random.choice(penta)
            target = nearest_pitch(pc, prev)
            # Keep in smooth range
            target = max(low, min(high, target))
            if abs(target - prev) > 4:
                target = prev + (2 if target > prev else -2)
            return max(low, min(high, target))

        else:  # free
            return max(low, min(high, prev + random.choice([-3, -2, -1, 0, 1, 2, 3])))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.style == "ballad":
            t, events = 0.0, []
            while t < duration_beats:
                dur = random.choice([1.0, 1.5, 2.0, 3.0])
                events.append(RhythmEvent(onset=round(t, 6), duration=min(dur, duration_beats - t)))
                t += dur
            return events

        elif self.style == "bebop":
            t, events = 0.0, []
            while t < duration_beats:
                dur = random.choice([0.25, 0.25, 0.5, 0.5, 0.75])
                events.append(RhythmEvent(onset=round(t, 6), duration=min(dur, duration_beats - t)))
                t += dur
            return events

        else:
            t, events = 0.0, []
            while t < duration_beats:
                dur = random.choice([0.25, 0.5, 0.5, 1.0])
                events.append(RhythmEvent(onset=round(t, 6), duration=min(dur, duration_beats - t)))
                t += dur
            return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
