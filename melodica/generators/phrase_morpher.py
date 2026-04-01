"""
generators/phrase_morpher.py — PhraseMorpher.

Intelligently connects 2 phrases by generating a smooth transition
from source to target using interpolation.
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class PhraseMorpher(PhraseGenerator):
    """
    Creates a smooth transition between a source and target phrase.

    source_notes: the starting phrase notes
    target_notes: the ending phrase notes
    steps:        number of interpolation steps (more = smoother)
    vertical_snap: "scale" | "semitone" | "none"
    """

    name: str = "Phrase Morpher"
    source_notes: list[NoteInfo] | None = None
    target_notes: list[NoteInfo] | None = None
    steps: int = 8
    vertical_snap: str = "scale"
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        source_notes: list[NoteInfo] | None = None,
        target_notes: list[NoteInfo] | None = None,
        steps: int = 8,
        vertical_snap: str = "scale",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.source_notes = source_notes
        self.target_notes = target_notes
        self.steps = max(2, steps)
        self.vertical_snap = vertical_snap
        self.rhythm = rhythm
        self._last_context: RenderContext | None = None

    def morph(
        self,
        source: list[NoteInfo],
        target: list[NoteInfo],
        key: Scale,
        duration_beats: float,
    ) -> list[NoteInfo]:
        """Generate interpolated notes between source and target."""
        if not source or not target:
            return []

        notes: list[NoteInfo] = []
        step_dur = duration_beats / self.steps

        for i in range(self.steps):
            t = i * step_dur
            frac = i / max(1, self.steps - 1)  # 0.0 → 1.0

            # Interpolate between source and target note sets
            src_idx = int(frac * (len(source) - 1))
            tgt_idx = int(frac * (len(target) - 1))
            src_note = source[min(src_idx, len(source) - 1)]
            tgt_note = target[min(tgt_idx, len(target) - 1)]

            # Interpolate pitch
            pitch = int(src_note.pitch + (tgt_note.pitch - src_note.pitch) * frac)

            # Snap to scale/semitone
            if self.vertical_snap == "scale" and not key.contains(pitch % 12):
                pitch = nearest_pitch(src_note.pitch % 12, pitch)
                if not key.contains(pitch % 12):
                    pitch = nearest_pitch(tgt_note.pitch % 12, pitch)
            elif self.vertical_snap == "semitone":
                pitch = round(pitch)

            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            # Interpolate velocity
            vel = int(src_note.velocity + (tgt_note.velocity - src_note.velocity) * frac)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=round(step_dur * 0.9, 6),
                    velocity=max(1, min(127, vel)),
                )
            )

        return notes

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        source = self.source_notes
        target = self.target_notes

        # Fallback: derive source/target from the first and last chords
        if not source or not target:
            if not chords:
                return []
            source = self._notes_from_chord(chords[0], key, duration_beats, ascending=True)
            target = self._notes_from_chord(chords[-1], key, duration_beats, ascending=False)

        return self.morph(source, target, key, duration_beats)

    def _notes_from_chord(
        self,
        chord: ChordLabel,
        key: Scale,
        duration_beats: float,
        ascending: bool,
    ) -> list[NoteInfo]:
        """Generate a simple arpeggio phrase from a chord for use as morph source/target."""
        pcs = chord.pitch_classes()
        if not pcs:
            return []
        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2
        step = duration_beats / max(len(pcs), 1)
        pitches = sorted(
            [nearest_pitch(int(pc), mid) for pc in pcs],
            key=lambda p: p,
        )
        if not ascending:
            pitches = list(reversed(pitches))
        return [
            NoteInfo(
                pitch=max(low, min(high, p)),
                start=round(i * step, 6),
                duration=round(step * 0.85, 6),
                velocity=80,
            )
            for i, p in enumerate(pitches)
        ]
