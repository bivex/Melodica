# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

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


_CONSONANT_INTERVALS: frozenset[int] = frozenset({0, 3, 4, 5, 7, 8, 9, 12})

_INTERVAL_PREF: dict[str, frozenset[int]] = {
    "thirds_sixths": frozenset({3, 4, 8, 9}),   # m3, M3, m6, M6
    "sixths":        frozenset({8, 9}),           # m6, M6
    "unison":        frozenset({0, 12}),          # unison, octave
    "mixed":         frozenset(),                 # no restriction
}
_MOTION_OPTIONS: frozenset[str] = frozenset(
    {"contrary", "parallel", "oblique", "similar", "free"}
)


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
    interval_preference:
        Preferred harmonic interval type between cantus and counter voice.
        ``"thirds_sixths"`` — prefer consonant 3rds and 6ths (warm, full).
        ``"sixths"``        — prefer 6ths only (open, airy).
        ``"unison"``        — prefer unisons and octaves (austere, ancient).
        ``"mixed"``         — no preference (default Fux behaviour).
    motion:
        Melodic motion strategy of the counter voice.
        ``"contrary"``  — move opposite to cantus (classical ideal).
        ``"parallel"``  — move in the same direction (harmony, warmth).
        ``"oblique"``   — one voice stays, other moves (sustained pedal effect).
        ``"similar"``   — move in same direction but by different interval.
        ``"free"``      — no constraint (default).
    voice_crossing:
        If False (default), prevent the counter voice from crossing below
        the cantus firmus (avoids muddy, unnatural lines).
    """

    name: str = "Counterpoint Generator"
    species: int = 1
    voices: int = 2
    cantus_position: str = "below"
    dissonance_rules: bool = True
    interval_preference: str = "mixed"
    motion: str = "free"
    voice_crossing: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)


    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        species: int = 1,
        voices: int = 2,
        cantus_position: str = "below",
        dissonance_rules: bool = True,
        interval_preference: str = "mixed",
        motion: str = "free",
        voice_crossing: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.species = max(1, min(5, species))
        self.voices = max(2, min(4, voices))
        if cantus_position not in ("below", "above"):
            raise ValueError(f"cantus_position must be 'below' or 'above'; got {cantus_position!r}")
        self.cantus_position = cantus_position
        self.dissonance_rules = dissonance_rules
        if interval_preference not in _INTERVAL_PREF:
            raise ValueError(
                f"interval_preference must be one of "
                f"{sorted(_INTERVAL_PREF)}; got {interval_preference!r}"
            )
        self.interval_preference = interval_preference
        if motion not in _MOTION_OPTIONS:
            raise ValueError(
                f"motion must be one of {sorted(_MOTION_OPTIONS)}; got {motion!r}"
            )
        self.motion = motion
        self.voice_crossing = voice_crossing
        self.rhythm = rhythm
        self._prev_cantus_pitch: int | None = None  # tracks cantus direction for motion logic

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
        num_counters = self.voices - 1  # voices - 1 = counter voices
        counter_offsets = [0, -5, 7] if num_counters >= 3 else (
            [0, -5] if num_counters >= 2 else [0]
        )
        counter_anchors = []
        for i in range(num_counters):
            offset = counter_offsets[i % len(counter_offsets)]
            if self.cantus_position == "below":
                counter_anchors.append(anchor + offset)
            else:
                counter_anchors.append(anchor - 12 + offset)

        prev_counters = [
            context.prev_pitch - 12 * (i + 1) if context and context.prev_pitch is not None
            else ca
            for i, ca in enumerate(counter_anchors)
        ]
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

            # Emit cantus firmus
            cantus_vel = max(1, min(127, self._velocity(True)))
            cantus_note = NoteInfo(
                pitch=cantus_pitch,
                start=round(event.onset, 6),
                duration=event.duration,
                velocity=cantus_vel,
            )

            # Generate each counter voice
            counter_pitches = []
            for ci in range(num_counters):
                cp = self._pick_counter_pitch(
                    [cantus_pitch] + counter_pitches, pcs, prev_counters[ci],
                    low, high, event.onset, counter_anchors[ci],
                    cantus_pitch=cantus_pitch,
                )
                counter_pitches.append(cp)
                prev_counters[ci] = cp
            self._prev_cantus_pitch = cantus_pitch

            # Order: cantus below counters or above
            if self.cantus_position == "below":
                notes.append(cantus_note)
                for ci, cp in enumerate(counter_pitches):
                    notes.append(NoteInfo(
                        pitch=cp,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity(False, ci))),
                    ))
            else:
                for ci, cp in enumerate(counter_pitches):
                    notes.append(NoteInfo(
                        pitch=cp,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, self._velocity(False, ci))),
                    ))
                notes.append(cantus_note)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )
        else:
            self._last_context = (context or RenderContext()).with_end_state(
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )
        return notes

    def _pick_counter_pitch(
        self,
        other_active_pitches: list[int],
        pcs: list[int],
        prev: int,
        low: int,
        high: int,
        onset: float,
        anchor: int | None = None,
        cantus_pitch: int | None = None,
    ) -> int:
        beat_pos = onset % 1.0
        is_strong = beat_pos < 0.01

        search_anchor = anchor if anchor is not None else prev

        # Build candidate pitches from chord tones
        candidates = []
        for pc in pcs:
            p = nearest_pitch(int(pc), search_anchor)
            p = max(low, min(high, p))

            # voice_crossing guard: counter must stay above cantus (when cantus is below)
            if not self.voice_crossing and cantus_pitch is not None:
                if self.cantus_position == "below" and p <= cantus_pitch:
                    p = nearest_pitch(int(pc), cantus_pitch + 3)
                    p = max(cantus_pitch + 1, min(high, p))
                elif self.cantus_position == "above" and p >= cantus_pitch:
                    p = nearest_pitch(int(pc), cantus_pitch - 3)
                    p = max(low, min(cantus_pitch - 1, p))

            is_valid = True
            if self.dissonance_rules and is_strong:
                for active_p in other_active_pitches:
                    interval = abs(p - active_p) % 12
                    if interval not in _CONSONANT_INTERVALS:
                        is_valid = False
                        break
            if is_valid:
                candidates.append(p)

        if not candidates:
            p = nearest_pitch(int(pcs[0]), search_anchor)
            candidates = [max(low, min(high, p))]

        # interval_preference filter: prefer candidates whose interval with cantus matches
        pref_intervals = _INTERVAL_PREF.get(self.interval_preference, frozenset())
        if pref_intervals and cantus_pitch is not None:
            preferred = [
                c for c in candidates
                if abs(c - cantus_pitch) % 12 in pref_intervals
            ]
            if preferred:
                candidates = preferred

        # motion filter: bias candidate selection by desired motion type
        if cantus_pitch is not None and self._prev_cantus_pitch is not None:
            cantus_dir = cantus_pitch - self._prev_cantus_pitch  # + up, - down, 0 same
            if self.motion == "contrary":
                # prefer pitches moving opposite to cantus
                if cantus_dir > 0:
                    candidates = sorted(candidates, key=lambda c: prev - c)  # prefer down
                elif cantus_dir < 0:
                    candidates = sorted(candidates, key=lambda c: c - prev)  # prefer up
            elif self.motion == "parallel":
                # prefer pitches moving in same direction as cantus
                if cantus_dir > 0:
                    candidates = sorted(candidates, key=lambda c: c - prev, reverse=True)
                elif cantus_dir < 0:
                    candidates = sorted(candidates, key=lambda c: prev - c, reverse=True)
            elif self.motion == "oblique":
                # prefer staying on the same pitch class
                candidates = sorted(candidates, key=lambda c: abs(c - prev))
            # "similar" and "free" — no directional sorting; fall through to min-movement

        # Final pick: smallest voice-leading distance (stays musical in all cases)
        best_pitch = min(candidates, key=lambda p: abs(p - prev))
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

    def _velocity(self, is_cantus: bool, counter_idx: int = 0) -> int:
        if is_cantus:
            return int(55 + self.params.density * 25)
        decay = counter_idx * 5
        return int(50 + self.params.density * 30 - decay)
