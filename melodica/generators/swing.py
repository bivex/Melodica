"""
generators/swing.py — Swing / Shuffle rhythm generator.

Applies swing feel to any rhythmic pattern by delaying off-beat notes.
Unlike the groove template or humanizer, this generates notes with
explicit swing timing from scratch.

Swing ratios:
    50% = straight (no swing)
    60% = light swing (jazz, pop)
    67% = medium swing (standard jazz)
    75% = hard swing (shuffle, blues)
    80% = very hard swing (triplet feel)
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
class SwingGenerator(PhraseGenerator):
    """
    Swing / Shuffle rhythm generator.

    swing_ratio:
        Percentage of the beat for the first note in a pair.
        50 = straight, 67 = medium swing, 75 = hard swing.
    subdivision:
        Base subdivision: 1.0 = quarter notes, 0.5 = eighths.
    pitch_strategy:
        "chord_tone", "scale_tone", "root_fifth", "melody".
    accent_pattern:
        "downbeat" — accent beats 1 and 3
        "backbeat" — accent beats 2 and 4
        "every_note" — all notes same velocity
    velocity_accent:
        Velocity multiplier for accented notes.
    """

    name: str = "Swing Generator"
    swing_ratio: float = 0.67
    subdivision: float = 0.5
    pitch_strategy: str = "chord_tone"
    accent_pattern: str = "downbeat"
    velocity_accent: float = 1.1
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        swing_ratio: float = 0.67,
        subdivision: float = 0.5,
        pitch_strategy: str = "chord_tone",
        accent_pattern: str = "downbeat",
        velocity_accent: float = 1.1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.swing_ratio = max(0.5, min(0.85, swing_ratio))
        self.subdivision = max(0.25, min(1.0, subdivision))
        self.pitch_strategy = pitch_strategy
        self.accent_pattern = accent_pattern
        self.velocity_accent = max(0.5, min(1.5, velocity_accent))
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
        t = 0.0
        pair_idx = 0  # even = on-beat, odd = swung

        while t < duration_beats:
            chord = chord_at(chords, t)
            beat_in_bar = t % 4.0

            if pair_idx % 2 == 0:
                # On-beat note (straight)
                onset = t
                note_dur = self.subdivision * self.swing_ratio
            else:
                # Off-beat note (swung/delayed)
                onset = t + self.subdivision * (self.swing_ratio - 0.5)
                note_dur = self.subdivision * (1.0 - self.swing_ratio)

            if onset >= duration_beats:
                break

            pitch = self._pick_pitch(chord, key, pair_idx)
            vel = self._vel(beat_in_bar)
            notes.append(
                NoteInfo(
                    pitch=pitch, start=round(onset, 6), duration=max(0.05, note_dur), velocity=vel
                )
            )

            t += self.subdivision
            pair_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _pick_pitch(self, chord: ChordLabel, key: Scale, idx: int) -> int:
        pcs = chord.pitch_classes()
        if not pcs:
            return key.root * 12 + 60
        if self.pitch_strategy == "root":
            return nearest_pitch(pcs[0], 60)
        if self.pitch_strategy == "root_fifth":
            pc = pcs[0] if idx % 2 == 0 else (pcs[0] + 7) % 12
            return nearest_pitch(pc, 60)
        if self.pitch_strategy == "scale_tone":
            degrees = key.degrees()
            if degrees:
                return nearest_pitch(int(degrees[idx % len(degrees)]) % 12, 60)
        return nearest_pitch(random.choice(pcs), 60)

    def _vel(self, beat_in_bar: float) -> int:
        base = int(self.params.density * 100)
        is_strong = False
        if self.accent_pattern == "downbeat":
            is_strong = abs(beat_in_bar) < 0.01 or abs(beat_in_bar - 2.0) < 0.01
        elif self.accent_pattern == "backbeat":
            is_strong = abs(beat_in_bar - 1.0) < 0.01 or abs(beat_in_bar - 3.0) < 0.01
        else:
            is_strong = True
        factor = self.velocity_accent if is_strong else 0.85
        return max(1, min(127, int(base * factor)))
