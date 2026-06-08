"""Two-feeling bass generator.

Half-note bass lines (beats 1 and 3) used in ballads, slow swing,
and the first chorus of many jazz standards before switching to
walking bass. Based on WalkingBassGenerator architecture.

Players: Ray Brown, Paul Chambers, Ron Carter (ballad work).
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch

# Blues scale for passing tones
_BLUES_SCALE = [0, 3, 5, 6, 7, 10]


@dataclass
class TwoFeelingGenerator(PhraseGenerator):
    """Generate two-feeling bass lines (half notes on beats 1 and 3).

    Parameters
    ----------
    approach_style : str
        How beat 3 approaches the next chord root:
        "chord_tone" — 3rd, 5th, or 7th (default, traditional)
        "chromatic" — half-step approach to next root
        "diatonic" — scale-step approach
        "mixed" — context-dependent
    transition_to_walking : float
        Probability per bar of switching from half notes to quarter notes
        (0 = always two-feel, 1 = immediately walking). Default 0.
    include_approach_tone : bool
        Add a passing tone between beats 1 and 3 on beat 2 or 4.
    velocity_diff : int
        Velocity difference between beat 1 (strong) and beat 3.
    """

    name: str = field(default="two_feeling", init=False)
    approach_style: str = "chord_tone"
    transition_to_walking: float = 0.0
    include_approach_tone: bool = False
    velocity_diff: int = 10
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid = ("chord_tone", "chromatic", "diatonic", "mixed")
        if self.approach_style not in valid:
            raise ValueError(f"approach_style must be one of {valid}, got {self.approach_style!r}")

    def _beat1_pitch(self, chord: ChordLabel, key: Scale, prev_pitch: int | None) -> int:
        """Beat 1: always chord root."""
        root_pc = chord.root
        anchor = prev_pitch if prev_pitch else self.params.key_range_low + 12
        return nearest_pitch(root_pc, anchor)

    def _beat3_pitch(self, chord: ChordLabel, next_chord: ChordLabel | None, key: Scale, prev_pitch: int) -> int:
        """Beat 3: approach next chord root."""
        if next_chord is None:
            # Last chord — just play the 5th
            fifth_pc = (chord.root + 7) % 12
            return nearest_pitch(fifth_pc, prev_pitch)

        next_root = next_chord.root
        approach = self.approach_style

        if approach == "mixed":
            approach = random.choice(["chord_tone", "chromatic", "diatonic"])

        if approach == "chromatic":
            # Half-step below or above next root
            direction = 1 if random.random() < 0.6 else -1
            approach_pc = (next_root - direction) % 12
            return nearest_pitch(approach_pc, prev_pitch)

        if approach == "diatonic":
            # Scale step above next root
            degs = key.degrees()
            for i, d in enumerate(degs):
                if abs(int(d) - next_root) < 0.5:
                    # One degree above
                    above_deg = degs[(i - 1) % len(degs)]
                    return nearest_pitch(int(above_deg) % 12, prev_pitch)
            return nearest_pitch(next_root, prev_pitch)

        # chord_tone: 3rd, 5th, or 7th
        pcs = chord.pitch_classes()
        root_pc = chord.root
        chord_tones = [pc for pc in pcs if (pc - root_pc) % 12 in (4, 3, 7, 10, 11)]
        if not chord_tones:
            chord_tones = pcs
        # Pick closest to prev_pitch
        best = min(chord_tones, key=lambda pc: abs(nearest_pitch(pc, prev_pitch) - prev_pitch))
        return nearest_pitch(best, prev_pitch)

    def _approach_tone(self, beat3_pitch: int, next_root_pc: int, prev_pitch: int) -> int | None:
        """Optional passing tone on beat 2 or 4."""
        if not self.include_approach_tone:
            return None
        # Chromatic or scale step between prev and beat3
        direction = 1 if beat3_pitch > prev_pitch else -1
        passing = prev_pitch + direction * random.choice([1, 2])
        if self.params.key_range_low <= passing <= self.params.key_range_high:
            return passing
        return None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        base_vel = self.base_velocity()
        notes: list[NoteInfo] = []
        prev_pitch: int | None = None
        bar = 0

        t = 0.0
        while t < duration_beats:
            chord = chords[0]
            # Find the current chord from the list
            for c in chords:
                c_start = getattr(c, 'start', 0.0)
                if c_start <= t + 0.01:
                    chord = c

            # Find next chord
            next_chord = None
            for c in chords:
                c_start = getattr(c, 'start', 0.0)
                if c_start > t + 0.01:
                    next_chord = c
                    break

            # Decide: two-feel or walking?
            is_walking = random.random() < self.transition_to_walking

            # Beat 1: root
            p1 = self._beat1_pitch(chord, key, prev_pitch)
            p1 = max(self.params.key_range_low, min(self.params.key_range_high, p1))
            v1 = min(127, base_vel + self.velocity_diff)
            notes.append(NoteInfo(
                pitch=p1,
                start=round(t, 4),
                duration=1.8 if not is_walking else 0.85,
                velocity=v1,
            ))
            prev_pitch = p1

            if not is_walking:
                # Optional approach tone on beat 2
                at = self._approach_tone(
                    self._beat3_pitch(chord, next_chord, key, p1),
                    next_chord.root if next_chord else chord.root,
                    p1,
                )
                if at is not None:
                    notes.append(NoteInfo(
                        pitch=at,
                        start=round(t + 1.0, 4),
                        duration=0.8,
                        velocity=max(1, base_vel - 5),
                    ))

                # Beat 3: chord tone / approach
                p3 = self._beat3_pitch(chord, next_chord, key, p1)
                p3 = max(self.params.key_range_low, min(self.params.key_range_high, p3))
                v3 = max(1, base_vel - self.velocity_diff // 2)
                notes.append(NoteInfo(
                    pitch=p3,
                    start=round(t + 2.0, 4),
                    duration=1.8,
                    velocity=v3,
                ))
                prev_pitch = p3

            else:
                # Walking 4 notes
                p3 = max(self.params.key_range_low, min(self.params.key_range_high,
                    self._beat3_pitch(chord, next_chord, key, p1)))
                notes.append(NoteInfo(
                    pitch=p3,
                    start=round(t + 1.0, 4),
                    duration=0.85,
                    velocity=max(1, base_vel - 3),
                ))
                # Beat 3
                pc3 = (chord.root + 5) % 12  # 4th or 5th
                p4 = max(self.params.key_range_low, min(self.params.key_range_high,
                    nearest_pitch(pc3, p3)))
                notes.append(NoteInfo(
                    pitch=p4,
                    start=round(t + 2.0, 4),
                    duration=0.85,
                    velocity=base_vel,
                ))
                # Beat 4: approach to next
                if next_chord:
                    approach_pc = (next_chord.root + 1) % 12  # chromatic below
                    p5 = max(self.params.key_range_low, min(self.params.key_range_high,
                        nearest_pitch(approach_pc, p4)))
                else:
                    p5 = max(self.params.key_range_low, min(self.params.key_range_high,
                        nearest_pitch(chord.root, p4)))
                notes.append(NoteInfo(
                    pitch=p5,
                    start=round(t + 3.0, 4),
                    duration=0.85,
                    velocity=max(1, base_vel - 5),
                ))
                prev_pitch = p5

            t += 4.0
            bar += 1

        return notes
