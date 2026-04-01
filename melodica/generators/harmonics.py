"""
generators/harmonics.py — Guitar/bass harmonics generator.

Layer: Application / Domain
Style: Classical guitar, ambient, metal, bass.

Produces natural and artificial harmonics:
  - Natural harmonics: at frets 12, 7, 5, 4, 3 (node points)
  - Artificial harmonics: fretted note + touch 12th fret above

Types:
    "natural"    — natural harmonics at open-string nodes
    "artificial" — fretted harmonics (touch + fret)
    "tap"        — tapped harmonics
    "harp"       — harp harmonics (alternating fretted and harmonic)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# Natural harmonic nodes (semitones above open string)
NATURAL_NODES = [12, 7, 5, 4, 3]  # octave, fifth, fourth, major third, minor third


@dataclass
class HarmonicsGenerator(PhraseGenerator):
    """
    Guitar harmonics generator.

    harmonic_type:
        "natural", "artificial", "tap", "harp"
    use_chord_tones:
        If True, harmonics outline chord tones.
    duration_per_note:
        Duration of each harmonic note in beats.
    velocity_pp:
        Harmonics are typically very soft.
    """

    name: str = "Harmonics Generator"
    harmonic_type: str = "natural"
    use_chord_tones: bool = True
    duration_per_note: float = 2.0
    velocity_pp: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        harmonic_type: str = "natural",
        use_chord_tones: bool = True,
        duration_per_note: float = 2.0,
        velocity_pp: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.harmonic_type = harmonic_type
        self.use_chord_tones = use_chord_tones
        self.duration_per_note = max(0.25, min(8.0, duration_per_note))
        self.velocity_pp = velocity_pp
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
        mid = (low + high) // 2

        prev_pitch = mid
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitch = self._pick_harmonic(chord, key, prev_pitch, low, high)
            vel = self._velocity()

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

    def _pick_harmonic(self, chord: ChordLabel, key: Scale, prev: int, low: int, high: int) -> int:
        # Find chord tone or scale tone
        if self.use_chord_tones:
            pcs = chord.pitch_classes()
        else:
            pcs = [int(d) for d in key.degrees()]

        if not pcs:
            pcs = [chord.root]

        pc = random.choice(pcs)
        base_pitch = nearest_pitch(pc, prev)

        # Natural harmonics: snap to harmonic node
        if self.harmonic_type == "natural":
            # Harmonics sound 12, 7, 5 semitones above the open string
            # We simulate by picking a pitch and mapping to nearest node
            node = random.choice([12, 7, 5, 4])
            # The sounding pitch is the open string + node
            harmonic_pitch = base_pitch + node - 12
            return max(low, min(high, harmonic_pitch))

        return max(low, min(high, base_pitch))

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(self.duration_per_note, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += self.duration_per_note + random.uniform(0.5, 2.0)
        return events

    def _velocity(self) -> int:
        if self.velocity_pp:
            return int(30 + self.params.density * 15)
        return int(50 + self.params.density * 25)
