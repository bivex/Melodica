"""rhythm/euclidean.py — Euclidean rhythm generator with tension-adaptive density.

The Euclidean algorithm distributes k pulses as evenly as possible over n steps
(Toussaint, 2005).  This produces rhythms found across world music traditions:
  E(3,8) = tresillo (Cuban), E(5,8) = cinquillo, E(2,3) = basic hemiola,
  E(4,9) = aksak, E(5,12) = south African, E(7,12) = West African standard.

Tension-adaptive density:
  At low tension → sparse Euclidean rhythm (few pulses in many steps).
  At high tension → dense rhythm (many pulses, shorter steps).
  The generator interpolates between a sparse and dense preset based on
  TensionCurve value at the current beat.

Classes
-------
EuclideanRhythm       — static Euclidean pattern
EuclideanGenerator    — RhythmGenerator subclass, loops the pattern
TensionEuclidean      — adapts density to TensionCurve across a phrase
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from melodica.rhythm import RhythmEvent, RhythmGenerator

if TYPE_CHECKING:
    from melodica.composer.tension_curve import TensionCurve


# ---------------------------------------------------------------------------
# Core algorithm
# ---------------------------------------------------------------------------

def euclidean_pattern(pulses: int, steps: int, rotation: int = 0) -> list[bool]:
    """Compute a Euclidean rhythm pattern.

    Distributes `pulses` onsets as evenly as possible across `steps` slots,
    starting from position 0.

    Examples
    --------
    euclidean_pattern(3, 8)  → X..X..X.  (tresillo)
    euclidean_pattern(5, 8)  → X.X.XX.X  (cinquillo)
    euclidean_pattern(7,12)  → X.XX.X.XX.X.  (bembé)
    """
    if pulses <= 0:
        return [False] * steps
    if pulses >= steps:
        return [True] * steps

    # Place each onset at floor(k * steps / pulses) for k = 0..pulses-1
    flat = [False] * steps
    for k in range(pulses):
        flat[k * steps // pulses] = True

    if rotation:
        r = rotation % steps
        flat = flat[r:] + flat[:r]

    return flat


def pattern_to_events(
    pattern: list[bool],
    step_duration: float,
    *,
    velocity_accent: float = 1.0,
    downbeat_accent: float = 1.15,
) -> list[RhythmEvent]:
    """Convert a boolean pattern to RhythmEvent list.

    Parameters
    ----------
    pattern : list[bool]
        Euclidean pattern from euclidean_pattern().
    step_duration : float
        Duration of each step in beats.
    velocity_accent : float
        Base velocity factor for all onsets.
    downbeat_accent : float
        Extra accent on the first onset (index 0).

    Returns
    -------
    list[RhythmEvent]
        Events with onset positions and durations set to the gap
        until the next onset (or end of pattern).
    """
    events: list[RhythmEvent] = []
    onset_indices = [i for i, v in enumerate(pattern) if v]

    for j, idx in enumerate(onset_indices):
        onset = idx * step_duration
        # Duration = gap to next onset (or end of pattern)
        if j + 1 < len(onset_indices):
            dur = (onset_indices[j + 1] - idx) * step_duration
        else:
            dur = (len(pattern) - idx) * step_duration
        vf = downbeat_accent * velocity_accent if idx == 0 else velocity_accent
        vf = min(1.0, vf)
        events.append(RhythmEvent(onset=round(onset, 6), duration=round(dur, 6), velocity_factor=vf))

    return events


# ---------------------------------------------------------------------------
# EuclideanRhythm — named preset container
# ---------------------------------------------------------------------------

# Classic named patterns (pulses, steps, rotation)
NAMED_PATTERNS: dict[str, tuple[int, int, int]] = {
    "tresillo":       (3, 8, 2),
    "cinquillo":      (5, 8, 4),
    "hemiola":        (3, 6, 0),
    "aksak":          (4, 9, 0),
    "bembé":          (7, 12, 10),
    "south_african":  (5, 12, 0),
    "west_african":   (7, 16, 0),
    "cuban_6_8":      (4, 6, 0),
    "bolero":         (3, 4, 0),
    "fume_fume":      (5, 8, 1),
    "shiko":          (4, 8, 0),
    "soukous":        (6, 8, 0),
    "gahu":           (3, 8, 1),
    "clave_3_2":      (5, 8, 2),
    "quintillo":      (5, 9, 0),
    "sixteen_beat":   (4, 16, 0),
}


@dataclass
class EuclideanRhythm:
    """A named or custom Euclidean rhythm pattern.

    Parameters
    ----------
    pulses : int
        Number of onsets.
    steps : int
        Total slots in the pattern.
    rotation : int
        Pattern rotation offset.
    step_duration : float
        Duration of each step in beats (default 0.5 = eighth note in 4/4).
    name : str
        Optional human-readable name.
    """
    pulses: int
    steps: int
    rotation: int = 0
    step_duration: float = 0.5
    name: str = ""

    @classmethod
    def from_name(cls, name: str, step_duration: float = 0.5) -> "EuclideanRhythm":
        """Create from a named preset."""
        if name not in NAMED_PATTERNS:
            raise ValueError(
                f"Unknown pattern {name!r}. Available: {sorted(NAMED_PATTERNS)}"
            )
        p, s, r = NAMED_PATTERNS[name]
        return cls(pulses=p, steps=s, rotation=r, step_duration=step_duration, name=name)

    @property
    def pattern(self) -> list[bool]:
        return euclidean_pattern(self.pulses, self.steps, self.rotation)

    @property
    def cycle_beats(self) -> float:
        return self.steps * self.step_duration

    def events(self, *, velocity_accent: float = 1.0) -> list[RhythmEvent]:
        return pattern_to_events(self.pattern, self.step_duration, velocity_accent=velocity_accent)

    def __str__(self) -> str:
        pat = "".join("X" if v else "." for v in self.pattern)
        label = self.name or f"E({self.pulses},{self.steps})"
        return f"{label}: [{pat}]"


# ---------------------------------------------------------------------------
# EuclideanGenerator — RhythmGenerator subclass
# ---------------------------------------------------------------------------

@dataclass
class EuclideanGenerator(RhythmGenerator):
    """RhythmGenerator that loops a Euclidean pattern.

    Parameters
    ----------
    pulses : int
        Onsets per cycle.
    steps : int
        Steps per cycle.
    rotation : int
        Pattern rotation.
    step_duration : float
        Duration of each step in beats.
    preset : str | None
        Named preset from NAMED_PATTERNS (overrides pulses/steps/rotation).
    """
    pulses: int = 4
    steps: int = 8
    rotation: int = 0
    step_duration: float = 0.5
    preset: str | None = None

    def __init__(
        self,
        pulses: int = 4,
        steps: int = 8,
        rotation: int = 0,
        step_duration: float = 0.5,
        preset: str | None = None,
        *,
        hits_per_bar: int | None = None,
        slots_per_beat: int | None = None,
        offset: int | None = None,
        gate: float = 0.9,
    ) -> None:
        if hits_per_bar is not None:
            pulses = hits_per_bar
        if slots_per_beat is not None:
            steps = 4 * slots_per_beat
            step_duration = 1.0 / slots_per_beat
        if offset is not None:
            rotation = -offset

        self.pulses = pulses
        self.steps = steps
        self.rotation = rotation
        self.step_duration = step_duration
        self.preset = preset
        if self.preset and self.preset in NAMED_PATTERNS:
            p, s, r = NAMED_PATTERNS[self.preset]
            self.pulses = p
            self.steps = s
            self.rotation = r

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        rhythm = EuclideanRhythm(
            pulses=self.pulses,
            steps=self.steps,
            rotation=self.rotation,
            step_duration=self.step_duration,
        )
        cycle_beats = rhythm.cycle_beats
        base_events = rhythm.events()

        result: list[RhythmEvent] = []
        t = 0.0
        while t < duration_beats:
            for e in base_events:
                onset = t + e.onset
                if onset >= duration_beats:
                    break
                dur = min(e.duration, duration_beats - onset)
                result.append(RhythmEvent(onset=round(onset, 6), duration=round(dur, 6),
                                          velocity_factor=e.velocity_factor))
            t += cycle_beats

        return result


# ---------------------------------------------------------------------------
# TensionEuclidean — density adapts to TensionCurve
# ---------------------------------------------------------------------------

@dataclass
class TensionEuclidean(RhythmGenerator):
    """Euclidean rhythm that adapts density to a TensionCurve.

    At low tension → sparse preset (few pulses = open, breathing rhythm).
    At high tension → dense preset (many pulses = driving, urgent rhythm).

    Interpolation is per-cycle: each Euclidean cycle snaps to one of two
    presets based on the tension value at the cycle's start beat.

    Parameters
    ----------
    sparse : EuclideanRhythm
        Rhythm used at low tension.
    dense : EuclideanRhythm
        Rhythm used at high tension.
    tension_curve : TensionCurve | None
        Tension source.  None = constant medium density.
    threshold : float
        Tension value above which the dense preset activates (default 0.55).
    step_duration : float
        Step duration shared by both presets (overrides their own).
    """
    sparse: EuclideanRhythm = field(
        default_factory=lambda: EuclideanRhythm(pulses=3, steps=8, step_duration=0.5, name="sparse")
    )
    dense: EuclideanRhythm = field(
        default_factory=lambda: EuclideanRhythm(pulses=7, steps=8, step_duration=0.5, name="dense")
    )
    tension_curve: "TensionCurve | None" = field(default=None, repr=False)
    threshold: float = 0.55
    step_duration: float = 0.5

    def _tension_at(self, beat: float) -> float:
        if self.tension_curve is None:
            return 0.4
        return float(self.tension_curve.tension_at(beat))

    def generate(self, duration_beats: float) -> list[RhythmEvent]:
        # Use sparse cycle_beats as the base loop unit (both presets share step_duration)
        sparse = EuclideanRhythm(
            self.sparse.pulses, self.sparse.steps, self.sparse.rotation,
            self.step_duration
        )
        dense = EuclideanRhythm(
            self.dense.pulses, self.dense.steps, self.dense.rotation,
            self.step_duration
        )
        sparse_events = sparse.events()
        dense_events  = dense.events()
        cycle_beats = sparse.cycle_beats  # both same steps × step_duration

        result: list[RhythmEvent] = []
        t = 0.0
        while t < duration_beats:
            tau = self._tension_at(t)
            events = dense_events if tau >= self.threshold else sparse_events
            vel_boost = 1.0 + 0.15 * max(0.0, tau - self.threshold)

            for e in events:
                onset = t + e.onset
                if onset >= duration_beats:
                    break
                dur = min(e.duration, duration_beats - onset)
                vf = min(1.0, e.velocity_factor * vel_boost)
                result.append(RhythmEvent(onset=round(onset, 6), duration=round(dur, 6),
                                          velocity_factor=round(vf, 3)))
            t += cycle_beats

        return result

    @classmethod
    def from_presets(
        cls,
        sparse_name: str = "tresillo",
        dense_name: str = "bembé",
        tension_curve: "TensionCurve | None" = None,
        step_duration: float = 0.5,
        threshold: float = 0.55,
    ) -> "TensionEuclidean":
        """Convenience constructor using named presets."""
        return cls(
            sparse=EuclideanRhythm.from_name(sparse_name, step_duration),
            dense=EuclideanRhythm.from_name(dense_name, step_duration),
            tension_curve=tension_curve,
            threshold=threshold,
            step_duration=step_duration,
        )


# Backward-compatible alias expected by rhythm/__init__.py
EuclideanRhythmGenerator = EuclideanGenerator
