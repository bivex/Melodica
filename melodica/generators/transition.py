"""
generators/transition.py — Drop / Breakdown / Build transition generator.

Creates the note patterns and energy curves for EDM/pop structural
transitions. Unlike FX generators (risers/impacts), this produces
actual musical note content with rhythmic energy shifts.

Types:
    "build"     — increasing energy, rising pitch, faster rhythm
    "drop"      — sudden energy release, strong downbeat, wide range
    "breakdown" — reduced energy, sparse notes, often higher register
    "fill"      — drum fill or melodic run leading to next section
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class TransitionGenerator(PhraseGenerator):
    """
    Drop / Breakdown / Build transition generator.

    transition_type:
        "build", "drop", "breakdown", "fill".
    length_beats:
        Duration of the transition in beats.
    octave_range:
        How many octaves to span during the transition.
    rhythm_acceleration:
        For "build": how much the rhythm speeds up (1.0 = linear).
    pitch_strategy:
        "chord_tone", "scale_tone", "chromatic".
    """

    name: str = "Transition Generator"
    transition_type: str = "build"
    length_beats: float = 8.0
    octave_range: int = 2
    rhythm_acceleration: float = 1.0
    pitch_strategy: str = "chord_tone"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        transition_type: str = "build",
        length_beats: float = 8.0,
        octave_range: int = 2,
        rhythm_acceleration: float = 1.0,
        pitch_strategy: str = "chord_tone",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if transition_type not in ("build", "drop", "breakdown", "fill"):
            raise ValueError(f"Unknown transition_type: {transition_type!r}")
        self.transition_type = transition_type
        self.length_beats = max(1.0, min(32.0, length_beats))
        self.octave_range = max(1, min(4, octave_range))
        self.rhythm_acceleration = max(0.1, min(3.0, rhythm_acceleration))
        self.pitch_strategy = pitch_strategy
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
        dur = min(self.length_beats, duration_beats)
        t = 0.0

        if self.transition_type == "build":
            notes = self._build_transition(chords, key, dur)
        elif self.transition_type == "drop":
            notes = self._drop_transition(chords, key, dur)
        elif self.transition_type == "breakdown":
            notes = self._breakdown_transition(chords, key, dur)
        elif self.transition_type == "fill":
            notes = self._fill_transition(chords, key, dur)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _build_transition(self, chords, key, dur):
        """Rising energy, accelerating rhythm."""
        notes = []
        t = 0.0
        base_octave = 4
        while t < dur:
            progress = t / max(0.1, dur)
            # Accelerate: note duration decreases
            note_dur = max(0.125, 1.0 / (1.0 + progress * self.rhythm_acceleration * 6))
            # Rise in pitch
            oct_shift = int(progress * self.octave_range)
            chord = chord_at(chords, t)
            pcs = chord.pitch_classes()
            if pcs:
                pc = pcs[int(progress * len(pcs)) % len(pcs)]
                pitch = nearest_pitch(pc, 60 + (base_octave + oct_shift - 4) * 12)
                pitch = max(0, min(127, pitch))
                # Crescendo
                vel = max(1, min(127, int(40 + progress * 80)))
                notes.append(
                    NoteInfo(pitch=pitch, start=round(t, 6), duration=note_dur, velocity=vel)
                )
            t += note_dur
        return notes

    def _drop_transition(self, chords, key, dur):
        """Sudden energy release on downbeat."""
        notes = []
        chord = chord_at(chords, 0)
        pcs = chord.pitch_classes()
        if not pcs:
            return notes
        # Strong downbeat chord
        for i, pc in enumerate(pcs[:4]):
            pitch = nearest_pitch(pc, 60)
            pitch = max(0, min(127, pitch))
            notes.append(NoteInfo(pitch=pitch, start=0.0, duration=min(dur, 4.0), velocity=110))
        # Sustained note with gradual decay
        t = 4.0
        while t < dur:
            decay = 1.0 - (t / dur)
            vel = max(20, int(110 * decay))
            pitch = nearest_pitch(pcs[0], 48)
            notes.append(NoteInfo(pitch=pitch, start=round(t, 6), duration=1.0, velocity=vel))
            t += 1.0
        return notes

    def _breakdown_transition(self, chords, key, dur):
        """Sparse notes, higher register, reduced energy."""
        notes = []
        t = 0.0
        while t < dur:
            progress = t / max(0.1, dur)
            # Increasing sparseness
            gap = 1.0 + progress * 3.0
            chord = chord_at(chords, t)
            pcs = chord.pitch_classes()
            if pcs:
                pc = random.choice(pcs)
                pitch = nearest_pitch(pc, 72)
                pitch = max(0, min(127, pitch))
                vel = max(15, int(80 - progress * 50))
                notes.append(
                    NoteInfo(
                        pitch=pitch, start=round(t, 6), duration=min(gap, dur - t), velocity=vel
                    )
                )
            t += gap
        return notes

    def _fill_transition(self, chords, key, dur):
        """Melodic or rhythmic fill leading to next section."""
        notes = []
        chord = chord_at(chords, 0)
        pcs = chord.pitch_classes()
        if not pcs:
            return notes
        # Descending fill from high to root
        n_notes = max(4, int(dur * 2))
        top_pitch = nearest_pitch(pcs[-1], 72)
        root_pitch = nearest_pitch(pcs[0], 48)
        step_dur = dur / n_notes
        for i in range(n_notes):
            progress = i / max(1, n_notes - 1)
            pitch = int(top_pitch - progress * (top_pitch - root_pitch))
            pitch = max(0, min(127, pitch))
            vel = max(1, min(127, int(100 - progress * 40)))
            notes.append(
                NoteInfo(
                    pitch=pitch, start=round(i * step_dur, 6), duration=step_dur * 0.8, velocity=vel
                )
            )
        return notes
