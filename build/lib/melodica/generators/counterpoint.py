"""
generators/counterpoint.py — Strict species counterpoint generator.

Layer: Application / Domain
Style: Renaissance, Baroque, classical composition pedagogy.

Implements the five species of counterpoint as described in Fux's
"Gradus ad Parnassum". Generates a counter-melody against a
cantus firmus derived from chord tones.

Species:
    1 — whole notes (1:1 ratio)
    2 — half notes (2:1 ratio)
    3 — quarter notes (4:1 ratio)
    4 — syncopated (2:1 with ties)
    5 — florid (mixed note values)

Dissonance rules restrict which intervals may sound against the
cantus firmus on strong beats.
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
class CounterpointGenerator(PhraseGenerator):
    """
    Strict species counterpoint generator.

    species:
        Counterpoint species (1–5).
    voices:
        Number of voices (2 = cantus + one counter).
    cantus_position:
        Whether the cantus firmus is "below" or "above".
    dissonance_rules:
        If True, enforce consonance on strong beats.
    """

    name: str = "Counterpoint Generator"
    species: int = 1
    voices: int = 2
    cantus_position: str = "below"
    dissonance_rules: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    _CONSONANT_INTERVALS: frozenset[int] = frozenset({0, 3, 4, 5, 7, 8, 9})

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        species: int = 1,
        voices: int = 2,
        cantus_position: str = "below",
        dissonance_rules: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.species = max(1, min(5, species))
        self.voices = max(2, min(4, voices))
        if cantus_position not in ("below", "above"):
            raise ValueError(f"cantus_position must be 'below' or 'above'; got {cantus_position!r}")
        self.cantus_position = cantus_position
        self.dissonance_rules = dissonance_rules
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

        cantus_anchor = anchor - 12 if self.cantus_position == "below" else anchor + 12
        counter_anchor = anchor if self.cantus_position == "below" else anchor - 6

        prev_counter = (
            context.prev_pitch if context and context.prev_pitch is not None else counter_anchor
        )
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pcs = chord.pitch_classes()
            if not pcs:
                continue

            cantus_pc = int(pcs[0])
            cantus_pitch = nearest_pitch(cantus_pc, cantus_anchor)
            cantus_pitch = max(low, min(high, cantus_pitch))

            counter_pitch = self._pick_counter_pitch(
                cantus_pitch, pcs, prev_counter, low, high, event.onset
            )

            if self.cantus_position == "below":
                notes.append(
                    NoteInfo(
                        pitch=cantus_pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity(True))),
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=counter_pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity(False))),
                    )
                )
            else:
                notes.append(
                    NoteInfo(
                        pitch=counter_pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity(False))),
                    )
                )
                notes.append(
                    NoteInfo(
                        pitch=cantus_pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity(True))),
                    )
                )
            prev_counter = counter_pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_counter_pitch(
        self,
        cantus: int,
        pcs: list[int],
        prev: int,
        low: int,
        high: int,
        onset: float,
    ) -> int:
        beat_pos = onset % 1.0
        is_strong = beat_pos < 0.01

        valid_pcs = list(pcs)
        if self.dissonance_rules and is_strong:
            valid_pcs = [
                int(pc) for pc in pcs if abs((int(pc) - cantus) % 12) in self._CONSONANT_INTERVALS
            ]
            if not valid_pcs:
                valid_pcs = [int(pcs[0])]

        best_pitch = nearest_pitch(int(valid_pcs[0]), prev)
        best_dist = abs(best_pitch - prev)

        for pc in valid_pcs:
            p = nearest_pitch(int(pc), prev)
            p = max(low, min(high, p))
            dist = abs(p - prev)
            if dist < best_dist:
                best_dist = dist
                best_pitch = p

        return max(low, min(high, best_pitch))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.species == 1:
            step = 4.0
        elif self.species == 2:
            step = 2.0
        elif self.species == 3:
            step = 1.0
        elif self.species == 4:
            step = 2.0
        else:
            step = 2.0

        t, events = 0.0, []
        note_idx = 0

        # Species 4: syncopated — first note starts on the weak beat (beat 2),
        # then every note is tied across the barline, creating suspension figures.
        syncopation_offset = step * 0.5 if self.species == 4 else 0.0
        # For species 4, extend duration by half a step to cross the barline.
        species4_dur = step * 1.5

        while t < duration_beats:
            onset = t + syncopation_offset
            if onset >= duration_beats:
                break

            if self.species == 5:
                dur = random.choice([1.0, 2.0, 2.0, 4.0])
            elif self.species == 4:
                dur = species4_dur
            else:
                dur = step

            dur = min(dur, duration_beats - onset)
            if dur <= 0:
                break
            events.append(RhythmEvent(onset=round(onset, 6), duration=round(dur * 0.98, 6)))
            t += step
            note_idx += 1
        return events

    def _velocity(self, is_cantus: bool) -> int:
        if is_cantus:
            return int(55 + self.params.density * 25)
        return int(50 + self.params.density * 30)
