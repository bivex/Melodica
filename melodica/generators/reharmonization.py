# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-06-08
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/reharmonization.py — Reharmonization / chord substitution generator.

Layer: Application / Domain
Style: Jazz, neo-soul, pop, film scoring.

Reharmonization replaces chords in a progression with harmonic
equivalents while preserving the overall key and function.

Strategies:
    "tritone"           — tritone substitution (bII7 for V7)
    "diatonic_swap"     — replace with diatonic function equivalent
    "secondary_dom"     — add secondary dominants
    "chromatic_mediant" — chromatic mediant substitution
    "backdoor"          — backdoor ii-V substitution
    "ii_v_insertion"    — insert ii-V before target chords
    "pedal_point"       — hold bass note while harmonies change above
    "negative"          — negative harmony (Steve Coleman / Jacob Collier)
    "mixed"             — combine multiple strategies
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, HarmonicFunction, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_pitches_closed, chord_at

_NEGATIVE_QUALITY_MAP: dict[Quality, Quality] = {
    Quality.MAJOR: Quality.MINOR,
    Quality.MINOR: Quality.MAJOR,
    Quality.DOMINANT7: Quality.HALF_DIM7,
    Quality.HALF_DIM7: Quality.DOMINANT7,
    Quality.MAJOR7: Quality.MINOR7,
    Quality.MINOR7: Quality.MAJOR7,
    Quality.DIMINISHED: Quality.AUGMENTED,
    Quality.AUGMENTED: Quality.DIMINISHED,
}

# Diatonic chord substitutions by scale degree
_DIATONIC_SUBS: dict[int, list[tuple[int, Quality]]] = {
    0: [(2, Quality.MINOR), (5, Quality.MINOR)],     # I → iii or vi
    2: [(0, Quality.MAJOR7), (4, Quality.DOMINANT7)],  # iii → I or V7
    4: [(2, Quality.MINOR7), (0, Quality.MAJOR7)],     # V → iii-7 or I
    5: [(0, Quality.MAJOR7), (3, Quality.MINOR7)],     # vi → I or IV-7
    1: [(4, Quality.DOMINANT7)],                         # ii → V7
}


@dataclass
class ReharmonizationGenerator(PhraseGenerator):
    """
    Chord reharmonization / substitution generator.

    Takes an existing chord progression and produces reharmonized voicings.

    strategy:
        Substitution strategy (see module docstring).
    preservation:
        What to preserve: "bass" (keep bass note), "melody" (keep top note), "none"
    substitution_frequency:
        How often to substitute (0.0 = never, 1.0 = always).
    voice_leading:
        Apply smooth voice leading to result.
    pedal_note:
        Pitch class for pedal_point strategy (None = use first chord root).
    intensity:
        How radical the substitutions get (0.0 = safe, 1.0 = adventurous).
    """

    name: str = "Reharmonization Generator"
    strategy: str = "tritone"
    preservation: str = "melody"
    substitution_frequency: float = 0.5
    voice_leading: bool = True
    pedal_note: int | None = None
    intensity: float = 0.5
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
        pedal_note: int | None = None,
        intensity: float = 0.5,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        valid = {
            "tritone", "diatonic_swap", "secondary_dom", "chromatic_mediant",
            "backdoor", "ii_v_insertion", "pedal_point", "negative", "mixed",
        }
        if strategy not in valid:
            raise ValueError(f"strategy must be one of {sorted(valid)}, got {strategy!r}")
        self.strategy = strategy
        self.preservation = preservation
        self.substitution_frequency = max(0.0, min(1.0, substitution_frequency))
        self.voice_leading = voice_leading
        self.pedal_note = pedal_note
        self.intensity = max(0.0, min(1.0, intensity))
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

        # Build reharmonized chord list
        sub_chords = self._reharmonize_progression(chords, key)

        for chord in sub_chords:
            last_chord = chord
            voicing = chord_pitches_closed(chord, mid)

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

    def reharmonize(self, chords: list[ChordLabel], key: Scale) -> list[ChordLabel]:
        """Return reharmonized chord list (for integration with other generators)."""
        return self._reharmonize_progression(chords, key)

    def _reharmonize_progression(self, chords: list[ChordLabel], key: Scale) -> list[ChordLabel]:
        result: list[ChordLabel] = []

        for i, chord in enumerate(chords):
            if random.random() < self.substitution_frequency:
                sub = self._substitute(chord, key, chords, i)
                if self.strategy == "ii_v_insertion":
                    result.extend(sub)  # returns list
                    continue
                result.append(sub)
            else:
                result.append(chord)

        # Apply pedal point over entire progression
        if self.strategy == "pedal_point":
            pedal_pc = self.pedal_note if self.pedal_note is not None else chords[0].root
            for c in result:
                c.bass = pedal_pc

        return result

    def _substitute(
        self, chord: ChordLabel, key: Scale, all_chords: list[ChordLabel], idx: int
    ) -> ChordLabel | list[ChordLabel]:
        root = chord.root
        strategy = self.strategy

        if strategy == "mixed":
            strategy = random.choice([
                "tritone", "diatonic_swap", "secondary_dom",
                "chromatic_mediant", "backdoor",
            ])

        if strategy == "tritone":
            if chord.quality in (Quality.DOMINANT7, Quality.MAJOR):
                sub_root = (root + 6) % 12
                return ChordLabel(
                    root=sub_root, quality=Quality.DOMINANT7,
                    start=chord.start, duration=chord.duration,
                )

        elif strategy == "diatonic_swap":
            degs = key.degrees()
            root_pc = root % 12
            for deg_idx, deg in enumerate(degs):
                if abs(int(deg) - root_pc) % 12 == 0:
                    subs = _DIATONIC_SUBS.get(deg_idx)
                    if subs and random.random() < self.intensity:
                        sub_deg, sub_qual = random.choice(subs)
                        if sub_deg < len(degs):
                            new_root = int(degs[sub_deg]) % 12
                            return ChordLabel(
                                root=new_root, quality=sub_qual,
                                start=chord.start, duration=chord.duration,
                            )
            return ChordLabel(
                root=int(degs[2]) % 12 if len(degs) > 2 else root,
                quality=Quality.MINOR,
                start=chord.start, duration=chord.duration,
            )

        elif strategy == "secondary_dom":
            dom_root = (root + 7) % 12
            return ChordLabel(
                root=dom_root, quality=Quality.DOMINANT7,
                start=chord.start, duration=chord.duration,
            )

        elif strategy == "chromatic_mediant":
            offset = random.choice([3, 4, 8, 9])
            new_root = (root + offset) % 12
            new_qual = Quality.MINOR if chord.quality == Quality.MAJOR else Quality.MAJOR
            return ChordLabel(
                root=new_root, quality=new_qual,
                start=chord.start, duration=chord.duration,
            )

        elif strategy == "backdoor":
            bVII = (root + 10) % 12
            return ChordLabel(
                root=bVII, quality=Quality.DOMINANT7,
                start=chord.start, duration=chord.duration,
            )

        elif strategy == "ii_v_insertion":
            # Insert ii-V before the target chord
            if random.random() > self.intensity:
                return [chord]
            ii_root = (root + 9) % 12  # Up a 4th = ii
            v_root = (root + 7) % 12   # Down a 5th = V
            half_dur = chord.duration / 2.0
            return [
                ChordLabel(root=ii_root, quality=Quality.MINOR7,
                           start=chord.start, duration=half_dur),
                ChordLabel(root=v_root, quality=Quality.DOMINANT7,
                           start=chord.start + half_dur, duration=half_dur),
            ]

        elif strategy == "negative":
            # Negative harmony: mirror around tritone
            mirror_root = (6 - root) % 12
            neg_qual = _NEGATIVE_QUALITY_MAP.get(chord.quality, Quality.MINOR)
            return ChordLabel(
                root=mirror_root, quality=neg_qual,
                start=chord.start, duration=chord.duration,
            )

        elif strategy == "pedal_point":
            # Chord stays same, pedal applied in _reharmonize_progression
            return chord

        return chord

    def _voice_lead(self, new_voicing: list[int], prev_voicing: list[int]) -> list[int]:
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
