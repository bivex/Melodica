"""
generators/bass_slap.py — Slap bass technique generator.

Layer: Application / Domain

Produces slap bass patterns with thumb slaps (hard),
finger pops (medium), and ghost notes (soft).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, OCTAVE, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


SLAP_PATTERNS = {"funky", "pop", "slap_pop", "octave"}

# Pattern: S=slap, P=pop, G=ghost, -=rest
_PATTERN_SEQ: dict[str, list[str]] = {
    "funky": ["S", "G", "P", "G", "S", "P", "G", "S"],
    "pop": ["S", "P", "S", "P", "S", "P", "S", "P"],
    "slap_pop": ["S", "-", "P", "-", "S", "G", "P", "-"],
    "octave": ["S", "-", "P", "-", "S", "-", "P", "G"],
}

# Velocity base per technique
_VEL_SLAP = 110
_VEL_POP = 90
_VEL_GHOST = 45


@dataclass
class BassSlapGenerator(PhraseGenerator):
    """
    Slap bass technique: thumb slap, finger pop, ghost notes.

    slap_pattern: "funky" | "pop" | "slap_pop" | "octave"
    ghost_note_prob: 0.0–1.0 probability of inserting ghost notes
    pop_probability: 0.0–1.0 ratio of pops vs slaps
    """

    name: str = "Bass Slap"
    slap_pattern: str = "funky"
    ghost_note_prob: float = 0.3
    pop_probability: float = 0.4
    octave_range: int = 1
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        slap_pattern: str = "funky",
        ghost_note_prob: float = 0.3,
        pop_probability: float = 0.4,
        octave_range: int = 1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if slap_pattern not in SLAP_PATTERNS:
            raise ValueError(f"slap_pattern must be one of {SLAP_PATTERNS}; got {slap_pattern!r}")
        self.slap_pattern = slap_pattern
        self.ghost_note_prob = max(0.0, min(1.0, ghost_note_prob))
        self.pop_probability = max(0.0, min(1.0, pop_probability))
        self.octave_range = max(1, min(3, octave_range))
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
        last_chord: ChordLabel | None = None
        pat_seq = _PATTERN_SEQ.get(self.slap_pattern, _PATTERN_SEQ["funky"])
        prev_pitch: int = self.params.key_range_low + 12

        for idx, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            technique = pat_seq[idx % len(pat_seq)]

            if technique == "-":
                continue

            root_pc = chord.bass if chord.bass is not None else chord.root
            pcs = chord.pitch_classes()

            if technique == "S":
                # Thumb slap: root or fifth, hard velocity
                slap_pc = int(root_pc)
                pitch = nearest_pitch(slap_pc, prev_pitch)
                vel = int(_VEL_SLAP * event.velocity_factor)
                dur = event.duration * 0.6
            elif technique == "P":
                # Finger pop: third or octave, medium velocity
                pop_candidates = [
                    int(pc) for pc in pcs if (int(pc) - int(root_pc)) % 12 in (3, 4, 7)
                ]
                if not pop_candidates:
                    pop_candidates = [int(pcs[0])] if pcs else [int(root_pc)]
                pop_pc = random.choice(pop_candidates)
                pitch = nearest_pitch(pop_pc, prev_pitch + 7)
                vel = int(_VEL_POP * event.velocity_factor)
                dur = event.duration * 0.5
            else:
                # Ghost note: muted percussive, soft velocity
                if random.random() > self.ghost_note_prob:
                    continue
                ghost_pc = int(root_pc)
                pitch = nearest_pitch(ghost_pc, prev_pitch)
                vel = int(_VEL_GHOST * event.velocity_factor)
                dur = event.duration * 0.2

            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=round(max(0.05, dur), 6),
                    velocity=max(0, min(MIDI_MAX, vel)),
                    articulation="staccato" if technique == "G" else None,
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

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # 16th note grid
        t, events = 0.0, []
        while t < duration_beats:
            is_downbeat = (t % 1.0) < 0.01
            vel = 1.0 if is_downbeat else 0.85
            events.append(RhythmEvent(onset=round(t, 6), duration=0.2, velocity_factor=vel))
            t += 0.25
        return events

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)
