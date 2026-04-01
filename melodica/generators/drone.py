"""
generators/drone.py — Drone / Pedal tone generator.

Layer: Application / Domain
Style: Cinematic, metal, folk, Indian classical, ambient.

A drone holds a sustained pitch (or interval) across chord changes,
creating harmonic tension and release through the static bass against
moving harmony. Pedal tones (pedal bass) are a subset: they sustain
a single pitch (usually the tonic or dominant) through changing chords.

Variants:
    "tonic"       — sustain the key's tonic throughout
    "dominant"    — sustain the key's dominant (5th) throughout
    "root"        — sustain each chord's root (changes with harmony)
    "fifth"       — sustain each chord's fifth
    "octave"      — tonic + octave doubled
    "power"       — tonic + fifth (power chord drone)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


VARIANT_PITCH_COUNTS = {
    "tonic": 1,
    "dominant": 1,
    "root": 1,
    "fifth": 1,
    "octave": 2,
    "power": 2,
}


@dataclass
class DroneGenerator(PhraseGenerator):
    """
    Sustained drone / pedal tone generator.

    variant:
        Which pitch to sustain. "tonic" and "dominant" are fixed across
        the entire phrase; "root" and "fifth" follow chord changes.
        "octave" doubles the tonic; "power" plays tonic + fifth.
    fade_in:
        Beats to fade in at the start of each sustained note.
    fade_out:
        Beats to fade out before the end of each sustained note.
    retrigger_on_chord:
        When True with "root"/"fifth" variant, retrigger on each chord change.
    """

    name: str = "Drone Generator"
    variant: str = "tonic"
    fade_in: float = 0.0
    fade_out: float = 0.0
    retrigger_on_chord: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "tonic",
        fade_in: float = 0.0,
        fade_out: float = 0.0,
        retrigger_on_chord: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if variant not in VARIANT_PITCH_COUNTS:
            raise ValueError(
                f"variant must be one of {sorted(VARIANT_PITCH_COUNTS)}; got {variant!r}"
            )
        self.variant = variant
        self.fade_in = max(0.0, fade_in)
        self.fade_out = max(0.0, fade_out)
        self.retrigger_on_chord = retrigger_on_chord
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

        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        # Compute the drone pitch(es)
        if self.variant in ("tonic", "octave", "power"):
            tonic_pc = key.root
            tonic_pitch = nearest_pitch(tonic_pc, anchor)
            tonic_pitch = max(low, min(high, tonic_pitch))

        notes: list[NoteInfo] = []

        if self.rhythm is not None:
            # Rhythm-driven: sustain for each event
            events = self._build_events(duration_beats)
            for event in events:
                chord = chord_at(chords, event.onset)
                if chord is None:
                    continue
                pitches = self._drone_pitches(chord, key, anchor, low, high)
                for p in pitches:
                    vel = self._velocity_with_fade(event.onset, event.duration, duration_beats)
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=event.duration,
                            velocity=max(1, min(127, vel)),
                        )
                    )
        elif self.variant in ("root", "fifth") and self.retrigger_on_chord:
            # One sustained note per chord
            for chord in chords:
                pitches = self._drone_pitches(chord, key, anchor, low, high)
                dur = chord.duration
                for p in pitches:
                    vel = self._velocity_with_fade(chord.start, dur, duration_beats)
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=chord.start,
                            duration=dur,
                            velocity=max(1, min(127, vel)),
                        )
                    )
        else:
            # Single sustained note for the entire phrase
            pitches = self._drone_pitches(chords[0], key, anchor, low, high)
            for p in pitches:
                vel = self._velocity_with_fade(0.0, duration_beats, duration_beats)
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=0.0,
                        duration=duration_beats,
                        velocity=max(1, min(127, vel)),
                    )
                )

        if notes:
            last_chord = chord_at(chords, notes[-1].start)
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=[n.pitch for n in notes[-VARIANT_PITCH_COUNTS.get(self.variant, 1) :]],
            )
        return notes

    # ------------------------------------------------------------------
    # Drone pitch computation
    # ------------------------------------------------------------------

    def _drone_pitches(
        self, chord: ChordLabel, key: Scale, anchor: int, low: int, high: int
    ) -> list[int]:
        if self.variant == "tonic":
            return [self._clamp(nearest_pitch(key.root, anchor), low, high)]
        elif self.variant == "dominant":
            dom_pc = (key.root + 7) % 12
            return [self._clamp(nearest_pitch(dom_pc, anchor), low, high)]
        elif self.variant == "root":
            return [self._clamp(nearest_pitch(chord.root, anchor), low, high)]
        elif self.variant == "fifth":
            fifth_pc = (chord.root + 7) % 12
            return [self._clamp(nearest_pitch(fifth_pc, anchor), low, high)]
        elif self.variant == "octave":
            t = self._clamp(nearest_pitch(key.root, anchor), low, high)
            upper = self._clamp(t + 12, low, high)
            return [t, upper]
        elif self.variant == "power":
            t = self._clamp(nearest_pitch(key.root, anchor), low, high)
            fifth = self._clamp(nearest_pitch((key.root + 7) % 12, anchor), low, high)
            return sorted({t, fifth})
        return [self._clamp(nearest_pitch(key.root, anchor), low, high)]

    @staticmethod
    def _clamp(pitch: int, low: int, high: int) -> int:
        return max(low, min(high, pitch))

    # ------------------------------------------------------------------
    # Velocity with fade
    # ------------------------------------------------------------------

    def _velocity_with_fade(self, onset: float, duration: float, total_duration: float) -> int:
        base = int(40 + self.params.density * 30)
        # Fade in
        if self.fade_in > 0 and onset < self.fade_in:
            factor = onset / self.fade_in
            base = int(base * factor)
        # Fade out
        end = onset + duration
        if self.fade_out > 0 and (total_duration - end) < self.fade_out:
            factor = (total_duration - end) / self.fade_out
            base = int(base * max(0.1, factor))
        return max(1, base)

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default: one long event spanning the full duration
        return [RhythmEvent(onset=0.0, duration=duration_beats)]
