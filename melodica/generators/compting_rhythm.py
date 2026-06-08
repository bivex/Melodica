"""Compting rhythm generator — syncopated jazz accompaniment patterns.

Generates the rhythmic skeleton of jazz comping:
  - Charleston pattern (dotted quarter + eighth)
  - Syncopated hits (anticipations, kicks)
  - Guide-tone rhythms (3-3-2 grouping)
  - Freddie Green style (4-to-the-bar)

These rhythms drive when chords are attacked, not what pitches are played.
Pair with PianoCompGenerator or GuitarCompGenerator for full comping.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale

# ---------------------------------------------------------------------------
# Rhythmic patterns (offsets within a 4-beat bar, as fractions)
# ---------------------------------------------------------------------------

_PATTERNS: dict[str, list[list[float]]] = {
    # Charleston: the most essential jazz rhythm
    "charleston": [
        [1.0, 3.5],  # Basic: beat 2 + "and" of 4
        [0.0, 1.5],  # Displaced: beat 1 + "and" of 2
        [1.0, 2.5],  # Close-position
        [0.0, 3.5],  # Spread
    ],
    # Freddie Green: quarter-note pulse (Count Basie style)
    "freddie_green": [
        [0.0, 1.0, 2.0, 3.0],
    ],
    # Syncopated hits: offbeat accents
    "syncopated": [
        [0.5, 2.0, 3.5],  # Offbeat emphasis
        [1.0, 2.5, 3.5],  # Kicks on 2, "and" of 3, "and" of 4
        [0.5, 1.5, 3.0],  # Repeated offbeat
        [1.0, 3.0, 3.5],  # Two hits + anticipation
    ],
    # 3-3-2 grouping (Afro-Cuban rooted, common in modern jazz)
    "tresillo": [
        [0.0, 1.5, 3.0],
        [0.5, 2.0, 3.5],  # Displaced
    ],
    # Ballad comping: sparse, rubato-like
    "ballad": [
        [0.0],
        [1.0, 3.0],
        [0.0, 3.5],
        [1.5],
    ],
    # Bossa nova comping pattern
    "bossa": [
        [0.0, 1.0, 2.5, 3.5],
        [0.0, 1.5, 2.0, 3.5],
    ],
    # Post-bop: McCoy Tyner / Herbie Hancock style
    "post_bop": [
        [0.0, 0.5, 2.0, 3.5],  # Double-hit on 1
        [1.0, 1.5, 3.0, 3.5],  # Double-hit on "and" of 1 and 3
        [0.5, 2.0, 2.5, 3.5],  # Clustered
    ],
    # Walking on "and" (creates forward motion)
    "and_walk": [
        [0.5, 1.5, 2.5, 3.5],  # All offbeats
        [0.5, 2.5],  # Offbeats 1 and 3
    ],
}

# Duration patterns for each hit
_DURATIONS: dict[str, float] = {
    "charleston": 0.75,
    "freddie_green": 0.85,
    "syncopated": 0.45,
    "tresillo": 0.75,
    "ballad": 1.5,
    "bossa": 0.5,
    "post_bop": 0.4,
    "and_walk": 0.4,
}


@dataclass
class ComptingRhythmGenerator(PhraseGenerator):
    """Generate syncopated jazz comping rhythms.

    Output is a list of NoteInfo events where each note represents a comp attack.
    Pitch is set to the chord root (or can be ignored — consumers use timing only).

    Parameters
    ----------
    pattern_family : str
        Rhythmic style: "charleston", "freddie_green", "syncopated",
        "tresillo", "ballad", "bossa", "post_bop", "and_walk".
    variation : float
        How much to deviate from fixed patterns (0 = strict, 1 = free).
    density : float
        Override from params.density — controls how many hits per bar.
    accent_profile : str
        "2_and_4" (bebop), "1_and_3" (trad), "all_equal", "random".
    anticipate : float
        Probability of anticipating beat 1 (playing on 4.5 of prev bar).
    stop_time : bool
        Insert stop-time gaps (rest on specific bars for dramatic effect).
    """

    name: str = field(default="compting_rhythm", init=False)
    pattern_family: str = "charleston"
    variation: float = 0.3
    density: float = 0.6
    accent_profile: str = "2_and_4"
    anticipate: float = 0.2
    stop_time: bool = False
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid_families = set(_PATTERNS.keys())
        if self.pattern_family not in valid_families:
            raise ValueError(f"pattern_family must be one of {valid_families}, got {self.pattern_family!r}")
        valid_accents = ("2_and_4", "1_and_3", "all_equal", "random")
        if self.accent_profile not in valid_accents:
            raise ValueError(f"accent_profile must be one of {valid_accents}, got {self.accent_profile!r}")

    def _velocity_for_beat(self, beat: float) -> int:
        base = self.base_velocity()
        if self.accent_profile == "all_equal":
            return base
        if self.accent_profile == "random":
            return base + random.randint(-10, 15)
        # Accent specific beats
        is_strong = (beat % 4) in (1.0, 3.0) if self.accent_profile == "2_and_4" else (beat % 4) in (0.0, 2.0)
        return min(127, base + 15) if is_strong else max(1, base - 10)

    def _pick_pattern(self) -> list[float]:
        patterns = _PATTERNS[self.pattern_family]
        return random.choice(patterns)

    def _vary_pattern(self, pattern: list[float]) -> list[float]:
        """Apply controlled variation to a pattern."""
        if self.variation <= 0:
            return pattern

        result = list(pattern)

        # Possibly drop a hit
        if len(result) > 1 and random.random() < self.variation * 0.3:
            idx = random.randint(0, len(result) - 1)
            result.pop(idx)

        # Possibly displace a hit by a small amount
        for i in range(len(result)):
            if random.random() < self.variation * 0.4:
                shift = random.choice([-0.5, 0.5])
                new_val = result[i] + shift
                if 0.0 <= new_val < 4.0:
                    result[i] = new_val

        # Possibly add a hit
        if random.random() < self.variation * 0.25 * self.density:
            new_beat = random.choice([0.5, 1.5, 2.5, 3.5])
            if new_beat not in result:
                result.append(new_beat)
                result.sort()

        return result

    def _should_stop_time(self, bar: int) -> bool:
        """Stop-time: silence every N bars for dramatic effect."""
        if not self.stop_time:
            return False
        # Stop on bars 4, 12, 20, ... (every 8 bars, offset by 4)
        return bar % 8 == 4

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        beats_per_bar = 4
        num_bars = int(duration_beats / beats_per_bar)
        dur = _DURATIONS.get(self.pattern_family, 0.5)

        # Scale duration by density
        effective_dur = dur * (0.5 + self.density * 0.5)

        # Pick a base chord for pitch reference
        chord = chords[0] if chords else key.diatonic_chord(1, seventh=True)
        root_pc = chord.root

        bar = 0
        while bar < num_bars:
            bar_start = bar * beats_per_bar

            # Stop-time: skip this bar
            if self._should_stop_time(bar):
                # Add one quiet hit on beat 1
                notes.append(NoteInfo(
                    pitch=min(root_pc + 60, 127),
                    start=float(bar_start),
                    duration=0.3,
                    velocity=40,
                    articulation="staccato",
                ))
                bar += 1
                continue

            # Pick and vary pattern
            pattern = self._pick_pattern()
            pattern = self._vary_pattern(pattern)

            # Density filter: drop hits probabilistically
            if self.density < 0.5:
                pattern = [p for p in pattern if random.random() < self.density * 2]

            for offset in pattern:
                beat_time = bar_start + offset

                # Anticipation of next bar's beat 1
                if offset >= 3.5 and random.random() < self.anticipate:
                    # Place it slightly early
                    beat_time = bar_start + 3.5 + random.uniform(0.0, 0.1)
                    effective_dur = 0.5  # Short anticipation

                if beat_time >= duration_beats:
                    continue

                vel = self._velocity_for_beat(offset)

                # Humanize timing
                if self.params.intel.time_humanization > 0:
                    t_jitter = random.gauss(0, self.params.intel.time_humanization * 0.08)
                else:
                    t_jitter = 0.0

                # Humanize velocity
                if self.params.intel.velocity_humanization > 0:
                    v_jitter = int(random.gauss(0, self.params.intel.velocity_humanization * 10))
                else:
                    v_jitter = 0

                notes.append(NoteInfo(
                    pitch=min(root_pc + 60, 127),
                    start=round(max(0.0, beat_time + t_jitter), 4),
                    duration=round(effective_dur, 4),
                    velocity=max(1, min(127, vel + v_jitter)),
                ))

            bar += 1

        return notes
