"""
generators/power_chord.py — Power chord riff generator.

Layer: Application / Domain
Style: Rock, metal, punk, grunge.

Power chords (root + fifth, optionally + octave) are the backbone of
distorted guitar music. This generator creates rhythmic power chord
patterns with techniques like palm muting, galloping, and chugging.

Patterns:
    "chug"       — steady eighth-note palm-muted chugs
    "gallop"     — galloping rhythm (short-short-long)
    "offbeat"    — emphasis on upbeats
    "staccato"   — short stabs on downbeats
    "sustained"  — long sustained power chords
    "syncopated" — syncopated hits
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


GALLOP_RHYTHM = [0.15, 0.15, 0.3, 0.4]  # short-short-long pattern


@dataclass
class PowerChordGenerator(PhraseGenerator):
    """
    Power chord riff generator.

    pattern:
        Chugging pattern type.
    include_octave:
        Add the octave above the fifth (full power chord = R-5-8).
    palm_mute_ratio:
        Fraction of notes that are palm-muted (0–1).
    gallop_speed:
        For "gallop" pattern: subdivision speed in beats.
    dead_notes:
        Include dead/muted percussive hits.
    """

    name: str = "Power Chord Generator"
    pattern: str = "chug"
    include_octave: bool = True
    palm_mute_ratio: float = 0.6
    gallop_speed: float = 0.15
    dead_notes: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "chug",
        include_octave: bool = True,
        palm_mute_ratio: float = 0.6,
        gallop_speed: float = 0.15,
        dead_notes: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.include_octave = include_octave
        self.palm_mute_ratio = max(0.0, min(1.0, palm_mute_ratio))
        self.gallop_speed = max(0.08, min(0.3, gallop_speed))
        self.dead_notes = dead_notes
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
        low = max(28, self.params.key_range_low)
        mid = (self.params.key_range_low + self.params.key_range_high) // 2

        prev_root = low + 12
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            root = nearest_pitch(chord.root, prev_root)
            root = max(low, min(mid - 5, root))
            fifth = root + 7
            prev_root = root

            is_muted = random.random() < self.palm_mute_ratio

            if self.pattern == "gallop":
                notes.extend(
                    self._gallop(root, fifth, event.onset, event.duration, is_muted, low, mid)
                )
            elif self.pattern == "chug":
                notes.extend(
                    self._chug(root, fifth, event.onset, event.duration, is_muted, low, mid)
                )
            elif self.pattern == "offbeat":
                notes.extend(
                    self._offbeat(root, fifth, event.onset, event.duration, is_muted, low, mid)
                )
            elif self.pattern == "staccato":
                notes.extend(self._staccato(root, fifth, event.onset, event.duration, low, mid))
            elif self.pattern == "sustained":
                notes.extend(self._sustained(root, fifth, event.onset, event.duration, low, mid))
            else:  # syncopated
                notes.extend(
                    self._syncopated(root, fifth, event.onset, event.duration, is_muted, low, mid)
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _power_chord_pitches(self, root: int, low: int, mid: int) -> list[int]:
        pitches = [max(low, min(mid, root)), max(low, min(mid + 12, root + 7))]
        if self.include_octave:
            pitches.append(max(low, min(mid + 12, root + 12)))
        return pitches

    def _chug(
        self, root: int, fifth: int, onset: float, dur: float, muted: bool, low: int, mid: int
    ) -> list[NoteInfo]:
        pitches = self._power_chord_pitches(root, low, mid)
        vel = self._velocity(muted)
        notes = []
        t = onset
        step = 0.5
        while t < onset + dur:
            n_dur = min(step * 0.7, onset + dur - t)
            for p in pitches:
                notes.append(NoteInfo(pitch=p, start=round(t, 6), duration=n_dur, velocity=vel))
            t += step
        return notes

    def _gallop(
        self, root: int, fifth: int, onset: float, dur: float, muted: bool, low: int, mid: int
    ) -> list[NoteInfo]:
        pitches = self._power_chord_pitches(root, low, mid)
        vel = self._velocity(muted)
        notes = []
        t = onset
        gs = self.gallop_speed
        while t < onset + dur:
            for i, frac in enumerate(GALLOP_RHYTHM):
                if t >= onset + dur:
                    break
                n_dur = min(gs * 0.8, onset + dur - t)
                for p in pitches:
                    v = int(vel * 1.1) if i == 2 else int(vel * 0.8)
                    notes.append(
                        NoteInfo(pitch=p, start=round(t, 6), duration=n_dur, velocity=max(1, v))
                    )
                t += gs
        return notes

    def _offbeat(
        self, root: int, fifth: int, onset: float, dur: float, muted: bool, low: int, mid: int
    ) -> list[NoteInfo]:
        pitches = self._power_chord_pitches(root, low, mid)
        vel = self._velocity(muted)
        notes = []
        t = onset
        while t < onset + dur:
            # Play on & of each beat
            t += 0.5
            if t >= onset + dur:
                break
            n_dur = min(0.35, onset + dur - t)
            for p in pitches:
                notes.append(NoteInfo(pitch=p, start=round(t, 6), duration=n_dur, velocity=vel))
            t += 0.5
        return notes

    def _staccato(
        self, root: int, fifth: int, onset: float, dur: float, low: int, mid: int
    ) -> list[NoteInfo]:
        pitches = self._power_chord_pitches(root, low, mid)
        vel = self._velocity(False)
        notes = []
        t = onset
        while t < onset + dur:
            for p in pitches:
                notes.append(NoteInfo(pitch=p, start=round(t, 6), duration=0.2, velocity=vel))
            t += 1.0
        return notes

    def _sustained(
        self, root: int, fifth: int, onset: float, dur: float, low: int, mid: int
    ) -> list[NoteInfo]:
        pitches = self._power_chord_pitches(root, low, mid)
        vel = self._velocity(False)
        return [
            NoteInfo(pitch=p, start=round(onset, 6), duration=dur, velocity=vel) for p in pitches
        ]

    def _syncopated(
        self, root: int, fifth: int, onset: float, dur: float, muted: bool, low: int, mid: int
    ) -> list[NoteInfo]:
        pitches = self._power_chord_pitches(root, low, mid)
        vel = self._velocity(muted)
        hits = [0.0, 0.75, 1.5, 2.5, 3.0]
        notes = []
        for h in hits:
            t = onset + h
            if t >= onset + dur:
                break
            n_dur = min(0.35, onset + dur - t)
            for p in pitches:
                notes.append(NoteInfo(pitch=p, start=round(t, 6), duration=n_dur, velocity=vel))
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=min(4.0, duration_beats - t)))
            t += 4.0
        return events

    def _velocity(self, muted: bool) -> int:
        base = int(65 + self.params.density * 35)
        return int(base * 0.6) if muted else base
