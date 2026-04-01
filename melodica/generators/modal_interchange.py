"""
generators/modal_interchange.py — Modal interchange / borrowed chord generator.

Layer: Application / Domain
Style: Jazz, neo-soul, pop, film scoring.

Modal interchange (borrowed chords) uses chords from parallel modes
to add color and emotional depth. For example, borrowing bVI and bVII
from the parallel minor into a major key.

Source modes:
    "minor"       — borrow from parallel natural minor (bVI, bVII, iv, ii°)
    "lydian"      — borrow from parallel Lydian (#IV, II)
    "mixolydian"  — borrow from parallel Mixolydian (bVII, v)
    "dorian"      — borrow from parallel Dorian (iv, VII)
    "phrygian"    — borrow from parallel Phrygian (bII, bvii)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, chord_pitches_closed, chord_at


# Borrowed chord intervals (semitones from tonic root) and qualities, by source mode.
# All offsets produce pitches from the *parallel* mode, not the diatonic major scale.
# Example in C major: "minor" bVI = Ab = 8 semitones above C.
BORROWED_OFFSETS: dict[str, list[tuple[int, Quality]]] = {
    "minor": [
        (5, Quality.MINOR),       # iv  — P4 (F minor in C major)
        (8, Quality.MAJOR),       # bVI — m6 (Ab major in C major)
        (10, Quality.MAJOR),      # bVII — m7 (Bb major in C major)
        (2, Quality.DIMINISHED),  # ii° — M2 (D dim in C major)
    ],
    "lydian": [
        (6, Quality.MAJOR),       # #IV — tritone (F# major in C major)
        (2, Quality.MAJOR),       # II  — M2 (D major in C major)
    ],
    "mixolydian": [
        (7, Quality.MINOR),       # v   — P5 minor (G minor in C major)
        (10, Quality.MAJOR),      # bVII — m7 (Bb major in C major)
    ],
    "dorian": [
        (5, Quality.MINOR),       # iv  — P4 (F minor in C major)
        (10, Quality.MAJOR),      # bVII — m7 (Bb major in C major)
    ],
    "phrygian": [
        (1, Quality.MAJOR),       # bII — m2 (Db major in C major)
        (10, Quality.MINOR),      # bvii — m7 minor (Bb minor in C major)
    ],
}


@dataclass
class ModalInterchangeGenerator(PhraseGenerator):
    """
    Modal interchange / borrowed chord generator.

    source_mode:
        Mode to borrow chords from.
    frequency:
        How often to insert borrowed chords (0.0–1.0).
    voice_leading:
        Smooth voice leading for borrowed chords.
    target_degree:
        Which scale degree to target for substitution (0 = random).
    """

    name: str = "Modal Interchange Generator"
    source_mode: str = "minor"
    frequency: float = 0.3
    voice_leading: bool = True
    target_degree: int = 0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        source_mode: str = "minor",
        frequency: float = 0.3,
        voice_leading: bool = True,
        target_degree: int = 0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.source_mode = source_mode
        self.frequency = max(0.0, min(1.0, frequency))
        self.voice_leading = voice_leading
        self.target_degree = max(0, min(7, target_degree))
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

        borrowed = BORROWED_OFFSETS.get(self.source_mode, BORROWED_OFFSETS["minor"])
        tonic_root = key.root  # pitch class 0–11

        for chord in chords:
            should_borrow = random.random() < self.frequency

            if should_borrow:
                # Compute borrowed root from tonic using semitone offset
                offset, quality = random.choice(borrowed)
                borrowed_root = (tonic_root + offset) % 12
                sub_chord = ChordLabel(
                    root=borrowed_root,
                    quality=quality,
                    start=chord.start,
                    duration=chord.duration,
                )
            else:
                sub_chord = chord

            last_chord = sub_chord
            voicing = chord_pitches_closed(sub_chord, mid)

            if self.voice_leading and prev_voicing is not None:
                voicing = self._voice_lead(voicing, prev_voicing)
            prev_voicing = voicing

            vel = int(55 + self.params.density * 30)
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
