"""
generators/pluck_sequence.py — Offbeat pluck sequence generator.

Layer: Application / Domain
Style: Deep house, tech house, tropical house, techno.

Pluck sequences are short, decaying synth notes placed on offbeats,
creating the characteristic rhythmic pulse of modern electronic music.

Patterns:
    "offbeat"    — pluck on & of every beat
    "syncopated" — varied syncopation (3+3+2, etc.)
    "arpeggiated" — pluck arpeggio across chord tones
    "random"     — random pluck placement within bar
    "driving"    — eighth-note driving pluck
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


SYNCOPATION_PATTERNS: dict[str, list[float]] = {
    "offbeat": [0.5, 1.5, 2.5, 3.5],
    "syncopated": [0.0, 0.75, 1.5, 2.0, 2.75, 3.5],
    "driving": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    "arpeggiated": [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5],
    "random": [],
}


@dataclass
class PluckSequenceGenerator(PhraseGenerator):
    """
    Offbeat pluck sequence generator.

    pattern:
        Rhythm pattern for pluck placement.
    decay_time:
        How quickly each pluck fades (in beats). Shorter = more percussive.
    pitch_randomization:
        Probability of slight pitch variation (0–1).
    pitch_range:
        How many scale tones the plucks span (1–7).
    """

    name: str = "Pluck Sequence Generator"
    pattern: str = "offbeat"
    decay_time: float = 0.3
    pitch_randomization: float = 0.0
    pitch_range: int = 3
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "offbeat",
        decay_time: float = 0.3,
        pitch_randomization: float = 0.0,
        pitch_range: int = 3,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.decay_time = max(0.05, min(1.0, decay_time))
        self.pitch_randomization = max(0.0, min(1.0, pitch_randomization))
        self.pitch_range = max(1, min(7, pitch_range))
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

        offsets = SYNCOPATION_PATTERNS.get(self.pattern, SYNCOPATION_PATTERNS["offbeat"])
        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        anchor = mid

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None
        pat_idx = 0

        bar_start = 0.0
        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue
            last_chord = chord

            degs = key.degrees()

            if self.pattern == "random":
                num_plucks = random.randint(2, 6)
                bar_offsets = sorted([round(random.uniform(0, 3.9), 2) for _ in range(num_plucks)])
            elif self.pattern == "arpeggiated":
                bar_offsets = offsets
            else:
                bar_offsets = offsets

            for off in bar_offsets:
                onset = bar_start + off
                if onset >= duration_beats:
                    break

                # Pick pitch from chord tones within range
                if self.pattern == "arpeggiated":
                    pcs = chord.pitch_classes()
                    pc = pcs[pat_idx % len(pcs)] if pcs else chord.root
                    pitch = nearest_pitch(int(pc), anchor)
                    # Move up through range
                    pitch += (pat_idx // max(len(pcs), 1)) * 12
                else:
                    pcs = chord.pitch_classes()
                    pc = random.choice(pcs) if pcs else chord.root
                    pitch = nearest_pitch(int(pc), prev_pitch)

                # Pitch randomization
                if random.random() < self.pitch_randomization:
                    pitch += random.choice([-1, 0, 1])

                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                vel = self._velocity()
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=self.decay_time,
                        velocity=max(1, min(127, vel)),
                    )
                )
                prev_pitch = pitch
                pat_idx += 1

            bar_start += 4.0

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _velocity(self) -> int:
        return int(55 + self.params.density * 30)
