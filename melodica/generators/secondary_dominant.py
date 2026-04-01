"""
generators/secondary_dominant.py — Secondary dominant / tritone substitution generator.

Generates secondary dominant chords (V/V, V/vi, V/ii, etc.) and
tritone substitutions as passing chords between diatonic chords.

Strategies:
    "secondary"      — insert secondary dominants before target chords
    "tritone"        — replace dominants with tritone subs
    "both"           — mix secondary dominants and tritone subs
    "chain"          — chain of dominants (circle of fifths)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, Quality
from melodica.utils import nearest_pitch, chord_at


def _secondary_dominant_root(target_root_pc: int) -> int:
    """Root of the V/x chord for target degree."""
    return (target_root_pc - 7) % 12  # a fifth above target = V of target


def _tritone_sub_root(target_root_pc: int) -> int:
    """Root of tritone substitution (bII7)."""
    return (target_root_pc - 6) % 12  # tritone above target root


@dataclass
class SecondaryDominantGenerator(PhraseGenerator):
    """
    Secondary dominant / tritone substitution generator.

    strategy:
        "secondary" — insert V/x before target chords
        "tritone" — use bII7 as passing chords
        "both" — randomly choose per chord change
        "chain" — circle-of-fifths dominant chain
    target_degrees:
        Which scale degrees get secondary dominants (0-indexed).
        Default: [1, 2, 4, 5] (ii, iii, V, vi in major).
    voicing:
        "root_position", "drop2", "shell".
    octave:
        Base octave for chord voicing.
    """

    name: str = "Secondary Dominant Generator"
    strategy: str = "secondary"
    target_degrees: tuple[int, ...] = (1, 2, 4, 5)
    voicing: str = "root_position"
    octave: int = 4
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        strategy: str = "secondary",
        target_degrees: tuple[int, ...] = (1, 2, 4, 5),
        voicing: str = "root_position",
        octave: int = 4,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if strategy not in ("secondary", "tritone", "both", "chain"):
            raise ValueError(f"Unknown strategy: {strategy!r}")
        self.strategy = strategy
        self.target_degrees = target_degrees
        self.voicing = voicing
        self.octave = max(1, min(7, octave))
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
        degrees = key.degrees()
        if not degrees:
            return []

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            chord_root_pc = chord.root % 12

            # Find which scale degree this chord root is
            degree_idx = None
            for i, d in enumerate(degrees):
                if abs((d % 12) - chord_root_pc) < 0.5:
                    degree_idx = i
                    break

            use_sec = False
            use_trit = False

            if degree_idx is not None and degree_idx in self.target_degrees and t > 0:
                if self.strategy == "secondary":
                    use_sec = True
                elif self.strategy == "tritone":
                    use_trit = True
                elif self.strategy == "both":
                    if random.random() < 0.5:
                        use_sec = True
                    else:
                        use_trit = True

            if use_sec:
                sec_root = _secondary_dominant_root(chord_root_pc)
                sec_dur = min(1.0, chord.end - t if hasattr(chord, "end") else 1.0)
                sec_pitches = self._voicing(sec_root)
                for p in sec_pitches:
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, p)),
                            start=round(t, 6),
                            duration=sec_dur,
                            velocity=self._vel(t, duration_beats),
                        )
                    )
                t += sec_dur
            elif use_trit:
                trit_root = _tritone_sub_root(chord_root_pc)
                trit_dur = min(1.0, chord.end - t if hasattr(chord, "end") else 1.0)
                trit_pitches = self._voicing(trit_root)
                for p in trit_pitches:
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, p)),
                            start=round(t, 6),
                            duration=trit_dur,
                            velocity=self._vel(t, duration_beats),
                        )
                    )
                t += trit_dur
            else:
                # Regular chord tone
                pcs = chord.pitch_classes()
                if pcs:
                    pitches = self._voicing(pcs[0])
                else:
                    pitches = [chord_root_pc + self.octave * 12]
                chord_dur = (
                    min(chord.end - t, duration_beats - t)
                    if hasattr(chord, "end")
                    else min(4.0, duration_beats - t)
                )
                for p in pitches:
                    notes.append(
                        NoteInfo(
                            pitch=max(0, min(127, p)),
                            start=round(t, 6),
                            duration=chord_dur,
                            velocity=self._vel(t, duration_beats),
                        )
                    )
                t += chord_dur

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _voicing(self, root_pc: int) -> list[int]:
        base = root_pc + self.octave * 12
        if self.voicing == "shell":
            return [base, base + 4, base + 10]  # 3rd and 7th
        if self.voicing == "drop2":
            return sorted([base, base + 4, base + 7, base + 3])  # drop2 shape
        return [base, base + 4, base + 7, base + 10]  # root position V7

    def _vel(self, t: float, dur: float) -> int:
        base = int(self.params.density * 100)
        return max(1, min(127, int(base * 0.9)))
