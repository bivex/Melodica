"""
generators/reharmonization.py — Reharmonization / chord substitution generator.

Layer: Application / Domain
Style: Jazz, neo-soul, pop, film scoring.

Reharmonization replaces chords in a progression with harmonic
equivalents while preserving the overall key and function.

Strategies:
    "tritone"         — tritone substitution (bII7 for V7)
    "diatonic_swap"   — replace with diatonic function equivalent
    "secondary_dom"   — add secondary dominants
    "chromatic_mediant" — chromatic mediant substitution
    "backdoor"        — backdoor ii-V substitution
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, HarmonicFunction, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_pitches_closed, chord_at


@dataclass
class ReharmonizationGenerator(PhraseGenerator):
    """
    Chord reharmonization / substitution generator.

    Takes an existing chord progression and produces reharmonized voicings.

    strategy:
        Substitution strategy (see above).
    preservation:
        What to preserve: "bass" (keep bass note), "melody" (keep top note), "none"
    substitution_frequency:
        How often to substitute (0.0 = never, 1.0 = always).
    voice_leading:
        Apply smooth voice leading to result.
    """

    name: str = "Reharmonization Generator"
    strategy: str = "tritone"
    preservation: str = "melody"
    substitution_frequency: float = 0.5
    voice_leading: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        strategy: str = "tritone",
        preservation: str = "melody",
        substitution_frequency: float = 0.5,
        voice_leading: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.strategy = strategy
        self.preservation = preservation
        self.substitution_frequency = max(0.0, min(1.0, substitution_frequency))
        self.voice_leading = voice_leading
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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None
        prev_voicing: list[int] | None = None

        for chord in chords:
            # Decide whether to substitute
            if random.random() < self.substitution_frequency:
                sub_chord = self._substitute(chord, key, chords)
            else:
                sub_chord = chord

            last_chord = sub_chord
            voicing = chord_pitches_closed(sub_chord, mid)

            # Voice lead
            if self.voice_leading and prev_voicing is not None:
                voicing = self._voice_lead(voicing, prev_voicing)
            prev_voicing = voicing

            vel = int(60 + self.params.density * 25)
            for p in voicing:
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=chord.start,
                        duration=chord.duration * 0.9,
                        velocity=max(1, min(127, vel)),
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _substitute(
        self, chord: ChordLabel, key: Scale, all_chords: list[ChordLabel]
    ) -> ChordLabel:
        root = chord.root

        if self.strategy == "tritone":
            # Tritone substitution: bII7 for V7
            if chord.quality in (Quality.DOMINANT7, Quality.MAJOR):
                sub_root = (root + 6) % 12
                return ChordLabel(
                    root=sub_root,
                    quality=Quality.DOMINANT7,
                    start=chord.start,
                    duration=chord.duration,
                )

        elif self.strategy == "diatonic_swap":
            # Replace with functionally equivalent chord
            degs = key.degrees()
            if len(degs) > 4:
                # Swap tonic ↔ mediant, dominant ↔ leading tone
                if abs(root - int(degs[0])) % 12 == 0:
                    return ChordLabel(
                        root=int(degs[2]),
                        quality=Quality.MINOR,
                        start=chord.start,
                        duration=chord.duration,
                    )
                elif abs(root - int(degs[4])) % 12 == 0:
                    return ChordLabel(
                        root=int(degs[6]) if len(degs) > 6 else (root + 2) % 12,
                        quality=Quality.DIMINISHED,
                        start=chord.start,
                        duration=chord.duration,
                    )

        elif self.strategy == "secondary_dom":
            # Add a secondary dominant before the chord
            dom_root = (root + 7) % 12
            return ChordLabel(
                root=dom_root, quality=Quality.DOMINANT7, start=chord.start, duration=chord.duration
            )

        elif self.strategy == "chromatic_mediant":
            # Chromatic mediant: root +/- major/minor third
            offset = random.choice([3, 4, 8, 9])
            new_root = (root + offset) % 12
            new_qual = Quality.MINOR if chord.quality == Quality.MAJOR else Quality.MAJOR
            return ChordLabel(
                root=new_root, quality=new_qual, start=chord.start, duration=chord.duration
            )

        elif self.strategy == "backdoor":
            # bVII7 instead of V7
            bVII = (root + 10) % 12
            return ChordLabel(
                root=bVII, quality=Quality.DOMINANT7, start=chord.start, duration=chord.duration
            )

        return chord

    def _voice_lead(self, new_voicing: list[int], prev_voicing: list[int]) -> list[int]:
        """Shift new voicing octaves to minimize distance from previous."""
        if not prev_voicing or not new_voicing:
            return new_voicing
        result = []
        for nv in new_voicing:
            best = min(prev_voicing, key=lambda pv: abs(nv - pv))
            while nv - best > 6:
                nv -= 12
            while best - nv > 6:
                nv += 12
            result.append(nv)
        return sorted(result)
