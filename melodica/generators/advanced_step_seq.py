"""
generators/advanced_step_seq.py — Advanced step sequencer with velocity layers.

Layer: Application / Domain
Style: All electronic genres.

A modern grid-based step sequencer with per-step control:
  - Per-step velocity, probability, ratchet, micro-timing
  - Multiple lanes (kick, snare, hat, etc.)
  - Pattern presets for common genres
  - Humanization

Patterns:
    "four_on_floor" — classic 4/4 kick pattern
    "breakbeat"     — breakbeat pattern
    "trap"          — trap drum pattern
    "techno"        — techno pattern
    "dnb"           — drum & bass pattern
    "custom"        — user-defined grid
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import chord_at


KICK = 36
SNARE = 38
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
RIM = 37
TOM_LOW = 41
CRASH = 49


@dataclass
class StepLane:
    """A single lane in the step sequencer."""

    pitch: int
    steps: list[float]  # 0.0 = off, 1.0 = max velocity
    velocity_layers: list[int] = field(default_factory=list)  # per-step velocity overrides
    probability: list[float] = field(default_factory=list)  # per-step probability
    ratchet: list[int] = field(default_factory=list)  # per-step ratchet count
    micro_timing: list[float] = field(default_factory=list)  # per-step micro-timing offset in beats


# Pre-built pattern grids (16 steps, values = velocity factor 0.0-1.0)
PATTERN_GRIDS: dict[str, dict[str, list[float]]] = {
    "four_on_floor": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hh_closed": [0.6, 0, 0.5, 0, 0.6, 0, 0.5, 0, 0.6, 0, 0.5, 0, 0.6, 0, 0.5, 0],
        "hh_open": [0, 0, 0, 0, 0, 0, 0, 0.7, 0, 0, 0, 0, 0, 0, 0, 0.7],
    },
    "breakbeat": {
        "kick": [1, 0, 0, 0.5, 0, 0, 1, 0, 0.7, 0, 0, 0, 1, 0, 0.5, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0.5, 0, 0, 0.7, 0, 1, 0, 0, 0],
        "hh_closed": [
            0.6,
            0.4,
            0.5,
            0.4,
            0.6,
            0.4,
            0.5,
            0.4,
            0.6,
            0.4,
            0.5,
            0.4,
            0.6,
            0.4,
            0.5,
            0.4,
        ],
    },
    "trap": {
        "kick": [1, 0, 0, 0, 0, 0, 0.7, 0, 0, 0, 1, 0, 0, 0, 0, 0.5],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hh_closed": [
            0.7,
            0.4,
            0.6,
            0.4,
            0.7,
            0.4,
            0.6,
            0.4,
            0.7,
            0.4,
            0.6,
            0.4,
            0.7,
            0.4,
            0.6,
            0.4,
        ],
        "hh_open": [0, 0, 0, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 0, 0, 0, 0.5],
    },
    "techno": {
        "kick": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
        "hh_closed": [
            0.5,
            0.3,
            0.5,
            0.3,
            0.5,
            0.3,
            0.5,
            0.3,
            0.5,
            0.3,
            0.5,
            0.3,
            0.5,
            0.3,
            0.5,
            0.3,
        ],
        "clap": [0, 0, 0, 0, 0.8, 0, 0, 0, 0, 0, 0, 0, 0.8, 0, 0, 0],
        "rim": [0, 0, 0.4, 0, 0, 0, 0.4, 0, 0, 0, 0.4, 0, 0, 0, 0.4, 0.5],
    },
    "dnb": {
        "kick": [1, 0, 0, 0, 0, 0, 0.7, 0, 0.8, 0, 0, 0, 0, 0, 0.7, 0],
        "snare": [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
        "hh_closed": [
            0.6,
            0.5,
            0.6,
            0.5,
            0.6,
            0.5,
            0.6,
            0.5,
            0.6,
            0.5,
            0.6,
            0.5,
            0.6,
            0.5,
            0.6,
            0.5,
        ],
    },
}

PITCH_MAP: dict[str, int] = {
    "kick": KICK,
    "snare": SNARE,
    "hh_closed": HH_CLOSED,
    "hh_open": HH_OPEN,
    "clap": CLAP,
    "rim": RIM,
    "tom_low": TOM_LOW,
    "crash": CRASH,
}


@dataclass
class AdvancedStepSequencer(PhraseGenerator):
    """
    Advanced step sequencer with velocity layers, probability, ratchets, micro-timing.

    pattern:
        "four_on_floor", "breakbeat", "trap", "techno", "dnb", "custom"
    steps:
        Total number of steps (16, 32, etc).
    humanize_timing:
        Random micro-timing offset per step (0.0-0.1 beats).
    humanize_velocity:
        Random velocity variation per step (0-30).
    swing:
        Swing ratio (0.5 = straight, 0.67 = triplet feel).
    lanes:
        Custom lanes when pattern="custom". Each lane defines a pitch and step grid.
    """

    name: str = "Advanced Step Sequencer"
    pattern: str = "four_on_floor"
    steps: int = 16
    humanize_timing: float = 0.02
    humanize_velocity: int = 8
    swing: float = 0.5
    lanes: list[StepLane] | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "four_on_floor",
        steps: int = 16,
        humanize_timing: float = 0.02,
        humanize_velocity: int = 8,
        swing: float = 0.5,
        lanes: list[StepLane] | None = None,
    ) -> None:
        super().__init__(params)
        self.pattern = pattern
        self.steps = max(4, min(64, steps))
        self.humanize_timing = max(0.0, min(0.1, humanize_timing))
        self.humanize_velocity = max(0, min(30, humanize_velocity))
        self.swing = max(0.5, min(0.75, swing))
        self.lanes = lanes

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        last_chord = chords[-1] if chords else None

        if self.lanes is not None:
            # Custom lanes
            lanes_to_use = self.lanes
        else:
            lanes_to_use = self._build_lanes_from_pattern()

        step_duration = 4.0 / self.steps  # Assuming 4/4 time

        bar_start = 0.0
        while bar_start < duration_beats:
            for lane in lanes_to_use:
                grid_steps = len(lane.steps)
                for i in range(min(self.steps, grid_steps)):
                    vel_factor = lane.steps[i]
                    if vel_factor <= 0:
                        continue

                    # Probability check
                    prob = 1.0
                    if i < len(lane.probability):
                        prob = lane.probability[i]
                    if random.random() > prob:
                        continue

                    # Calculate onset with swing
                    base_onset = bar_start + i * step_duration
                    if i % 2 == 1:
                        base_onset += (self.swing - 0.5) * step_duration

                    # Micro-timing
                    micro = 0.0
                    if i < len(lane.micro_timing):
                        micro = lane.micro_timing[i]
                    micro += random.gauss(0, self.humanize_timing)
                    onset = base_onset + micro

                    if onset >= duration_beats:
                        continue

                    # Velocity
                    vel = int(vel_factor * 100)
                    if i < len(lane.velocity_layers) and lane.velocity_layers[i] > 0:
                        vel = lane.velocity_layers[i]
                    vel += random.randint(-self.humanize_velocity, self.humanize_velocity)
                    vel = max(1, min(MIDI_MAX, vel))

                    # Ratchet
                    ratchet = 1
                    if i < len(lane.ratchet):
                        ratchet = max(1, lane.ratchet[i])

                    if ratchet > 1:
                        ratchet_dur = step_duration / ratchet
                        for r in range(ratchet):
                            r_onset = onset + r * ratchet_dur
                            if r_onset < duration_beats:
                                r_vel = max(1, vel - r * 5)
                                notes.append(
                                    NoteInfo(
                                        pitch=lane.pitch,
                                        start=round(r_onset, 6),
                                        duration=ratchet_dur * 0.6,
                                        velocity=r_vel,
                                    )
                                )
                    else:
                        notes.append(
                            NoteInfo(
                                pitch=lane.pitch,
                                start=round(onset, 6),
                                duration=step_duration * 0.8,
                                velocity=vel,
                            )
                        )

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_lanes_from_pattern(self) -> list[StepLane]:
        grid = PATTERN_GRIDS.get(self.pattern, PATTERN_GRIDS["four_on_floor"])
        lanes = []
        for name, steps in grid.items():
            pitch = PITCH_MAP.get(name, KICK)
            # Pad or truncate to match step count
            padded = (steps + [0.0] * self.steps)[: self.steps]
            lanes.append(
                StepLane(
                    pitch=pitch,
                    steps=padded,
                )
            )
        return lanes
