"""
generators/amapiano_logdrum.py — Dedicated Amapiano Log Drum generator.

Layer: Application / Domain
Style: Amapiano, Afropiano, South African house.

Amapiano's signature element — pitched log drums with complex
syncopated rhythms. This is a DEDICATED generator for the
log drum pattern, separate from the general Afrobeats generator.

Patterns:
    "classic"    — classic Kabza De Small style
    "kabza"      — Kabza-style (rolling, complex)
    "dj_maphorisa" — Dj Maphorisa style (bouncy)
    "mellow"     — mellow/minimal log drums
    "percussive" — heavy percussive log drums
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


LOG_DRUM_LOW = 60
LOG_DRUM_HIGH = 84

# Characteristic Amapiano log drum rhythm offsets per bar
CLASSIC_OFFSETS = [0.0, 0.5, 1.0, 1.75, 2.0, 2.5, 3.0, 3.5, 3.75]
KABZA_OFFSETS = [0.0, 0.25, 0.75, 1.0, 1.5, 2.0, 2.25, 2.75, 3.0, 3.25, 3.5]
MELLOW_OFFSETS = [0.0, 1.0, 2.0, 3.0]
PERCUSSIVE_OFFSETS = [
    0.0,
    0.25,
    0.5,
    0.75,
    1.0,
    1.25,
    1.5,
    2.0,
    2.25,
    2.5,
    2.75,
    3.0,
    3.25,
    3.5,
    3.75,
]


@dataclass
class AmapianoLogDrumGenerator(PhraseGenerator):
    """
    Dedicated Amapiano Log Drum generator.

    pattern:
        "classic", "kabza", "dj_maphorisa", "mellow", "percussive"
    pitch_variation:
        How much pitch varies between hits (0.0-1.0).
        0 = same pitch, 1 = wide range.
    velocity_humanize:
        Velocity humanization amount (0.0-1.0).
    ghost_probability:
        Probability of ghost notes (quiet, subtle hits).
    swing:
        Swing amount (0.5=straight, 0.67=heavy).
    note_length_variation:
        How much note lengths vary (0.0-1.0).
    """

    name: str = "Amapiano Log Drum Generator"
    pattern: str = "classic"
    pitch_variation: float = 0.4
    velocity_humanize: float = 0.3
    ghost_probability: float = 0.2
    swing: float = 0.55
    note_length_variation: float = 0.3
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "classic",
        pitch_variation: float = 0.4,
        velocity_humanize: float = 0.3,
        ghost_probability: float = 0.2,
        swing: float = 0.55,
        note_length_variation: float = 0.3,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.pitch_variation = max(0.0, min(1.0, pitch_variation))
        self.velocity_humanize = max(0.0, min(1.0, velocity_humanize))
        self.ghost_probability = max(0.0, min(1.0, ghost_probability))
        self.swing = max(0.5, min(0.75, swing))
        self.note_length_variation = max(0.0, min(1.0, note_length_variation))

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
        last_chord = chords[-1]
        bar_start = 0.0

        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            offsets = self._get_offsets()
            root_pc = chord.root
            third_pc = (root_pc + 3) % 12
            fifth_pc = (root_pc + 7) % 12
            seventh_pc = (root_pc + 10) % 12
            scale_pcs = [root_pc, third_pc, fifth_pc, seventh_pc]

            prev_pitch = nearest_pitch(root_pc, LOG_DRUM_LOW + 6)

            for i, off in enumerate(offsets):
                # Apply swing to offbeat positions
                actual_off = off
                if int(off * 2) % 2 == 1:
                    actual_off += (self.swing - 0.5) * 0.25

                onset = bar_start + actual_off
                if onset >= duration_beats:
                    continue

                # Pitch selection
                if random.random() < self.pitch_variation:
                    pc = random.choice(scale_pcs)
                else:
                    pc = root_pc
                pitch = nearest_pitch(pc, prev_pitch)
                pitch = max(LOG_DRUM_LOW, min(LOG_DRUM_HIGH, pitch))

                # Velocity
                base_vel = 80 if i % 2 == 0 else 65
                vel_noise = int(random.gauss(0, self.velocity_humanize * 15))
                vel = max(30, min(MIDI_MAX, base_vel + vel_noise))

                # Duration
                base_dur = 0.4
                if self.note_length_variation > 0:
                    dur_noise = (
                        random.uniform(-self.note_length_variation, self.note_length_variation)
                        * 0.3
                    )
                    base_dur = max(0.1, base_dur + dur_noise)

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=base_dur,
                        velocity=vel,
                    )
                )

                # Ghost note
                if random.random() < self.ghost_probability:
                    ghost_onset = onset + 0.125
                    if ghost_onset < duration_beats:
                        ghost_pc = random.choice(scale_pcs)
                        ghost_pitch = max(
                            LOG_DRUM_LOW, min(LOG_DRUM_HIGH, nearest_pitch(ghost_pc, pitch))
                        )
                        notes.append(
                            NoteInfo(
                                pitch=ghost_pitch,
                                start=round(ghost_onset, 6),
                                duration=0.15,
                                velocity=max(20, vel - 30),
                            )
                        )

                prev_pitch = pitch

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_offsets(self) -> list[float]:
        return {
            "classic": CLASSIC_OFFSETS,
            "kabza": KABZA_OFFSETS,
            "dj_maphorisa": CLASSIC_OFFSETS,
            "mellow": MELLOW_OFFSETS,
            "percussive": PERCUSSIVE_OFFSETS,
        }.get(self.pattern, CLASSIC_OFFSETS)
