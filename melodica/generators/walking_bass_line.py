"""Walking bass line construction generator.

Builds walking bass lines through chord changes with emphasis on
voice leading and line construction — distinct from WalkingBassGenerator
which focuses on beat-by-beat approach notes. This generator emphasizes:

  - Smooth voice leading between chord tones
  - Target-note arrival (planning ahead to land on specific degrees)
  - Contour shapes (ascending, descending, scalar, arpeggiated)
  - Phrase-level logic vs. beat-level logic

Used in:
  - Jazz bass walking lines
  - Piano left-hand walking
  - Organ bass lines (Jimmy Smith, Larry Young)

Players: Ray Brown, Paul Chambers, Ron Carter, Sam Jones.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch, nearest_pitch_above, snap_to_scale


@dataclass
class WalkingBassLineGenerator(PhraseGenerator):
    """Generate phrase-level walking bass lines through chord changes.

    Parameters
    ----------
    contour : str
        "ascending" — line generally rises through changes.
        "descending" — line generally falls.
        "scalar" — follows scale degrees stepwise.
        "arpeggiated" — outlines chord shapes.
        "mixed" — varies contour per phrase.
    target_note : str
        "root" — always land on root of each chord.
        "guide_tones" — land on 3rds and 7ths.
        "fifths" — emphasize 5ths for movement.
        "mixed" — vary target notes.
    passing_tones : str
        "chromatic" — half-step passing tones.
        "diatonic" — scale-step passing tones.
        "enclosure" — chromatic enclosure before targets.
        "mixed" — combine approaches.
    phrase_length : int
        Bars per phrase segment before resetting contour.
    swing_feel : float
        Swing ratio for eighth-note subdivision (0.5 = straight, 0.67 = swing).
    """

    name: str = field(default="walking_bass_line", init=False)
    contour: str = "mixed"
    target_note: str = "root"
    passing_tones: str = "mixed"
    phrase_length: int = 4
    swing_feel: float = 0.67
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid_contours = ("ascending", "descending", "scalar", "arpeggiated", "mixed")
        if self.contour not in valid_contours:
            raise ValueError(f"contour must be one of {valid_contours}")
        valid_targets = ("root", "guide_tones", "fifths", "mixed")
        if self.target_note not in valid_targets:
            raise ValueError(f"target_note must be one of {valid_targets}")

    def _chord_target(self, chord: ChordLabel) -> int:
        """Get target pitch class for a chord based on target_note setting."""
        root = chord.root
        pcs = chord.pitch_classes()

        if self.target_note == "root":
            return root
        if self.target_note == "guide_tones":
            # 3rd or 7th — pick alternately
            if len(pcs) > 3:
                return int(pcs[3])  # 7th
            if len(pcs) > 1:
                return int(pcs[1])  # 3rd
            return root
        if self.target_note == "fifths":
            if len(pcs) > 2:
                return int(pcs[2])
            return (root + 7) % 12
        # mixed
        choices = [root]
        if len(pcs) > 1:
            choices.append(int(pcs[1]))
        if len(pcs) > 2:
            choices.append(int(pcs[2]))
        return random.choice(choices)

    def _build_beat_notes(
        self,
        target_pc: int,
        prev_pitch: int,
        beats: int,
        chord: ChordLabel,
        key: Scale,
        low: int,
        high: int,
    ) -> list[int]:
        """Build a sequence of pitches for `beats` beats targeting `target_pc`."""
        target = nearest_pitch(target_pc, prev_pitch)
        target = max(low, min(high, target))

        contour = self.contour
        if contour == "mixed":
            contour = random.choice(["ascending", "descending", "scalar", "arpeggiated"])

        pitches: list[int] = []

        if contour == "ascending" and prev_pitch < target:
            step = max(1, (target - prev_pitch) // max(1, beats))
            current = prev_pitch
            for _ in range(beats - 1):
                current = min(target, current + step)
                current = max(low, min(high, current))
                pitches.append(current)
            pitches.append(target)

        elif contour == "descending" and prev_pitch > target:
            step = max(1, (prev_pitch - target) // max(1, beats))
            current = prev_pitch
            for _ in range(beats - 1):
                current = max(target, current - step)
                current = max(low, min(high, current))
                pitches.append(current)
            pitches.append(target)

        elif contour == "arpeggiated":
            pcs = chord.pitch_classes()
            current = prev_pitch
            for _ in range(beats - 1):
                if pcs:
                    pc = int(random.choice(pcs))
                    p = nearest_pitch(pc, current)
                    p = max(low, min(high, p))
                    pitches.append(p)
                    current = p
                else:
                    step = random.choice([-2, -1, 1, 2])
                    p = max(low, min(high, current + step))
                    pitches.append(p)
                    current = p
            pitches.append(target)

        else:
            # scalar or fallback
            current = prev_pitch
            for _ in range(beats - 1):
                direction = 1 if target > current else -1
                p = snap_to_scale(current + direction * 2, key)
                p = max(low, min(high, p))
                pitches.append(p)
                current = p
            pitches.append(target)

        # Ensure correct length
        while len(pitches) < beats:
            pitches.append(pitches[-1] if pitches else target)
        return pitches[:beats]

    def _add_passing_tone(
        self, prev: int, target: int, key: Scale, low: int, high: int
    ) -> int:
        style = self.passing_tones
        if style == "mixed":
            style = random.choice(["chromatic", "diatonic", "enclosure"])

        if style == "chromatic":
            direction = 1 if target > prev else -1
            return max(low, min(high, prev + direction))

        if style == "diatonic":
            direction = 1 if target > prev else -1
            return max(low, min(high, snap_to_scale(prev + direction * 2, key)))

        # enclosure — half-step below target
        return max(low, min(high, target - 1))

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
        low = self.params.key_range_low
        high = self.params.key_range_high

        prev_pitch = (low + high) // 2
        if context and context.prev_pitch is not None:
            prev_pitch = context.prev_pitch

        t = 0.0
        phrase_bar = 0

        for chord in chords:
            chord_start = chord.start
            chord_dur = min(chord.duration, duration_beats - chord_start) if chord_start < duration_beats else chord.duration

            if chord_start >= duration_beats:
                break

            target_pc = self._chord_target(chord)
            n_beats = max(1, int(chord_dur))

            beat_pitches = self._build_beat_notes(
                target_pc, prev_pitch, n_beats, chord, key, low, high,
            )

            for bi, pitch in enumerate(beat_pitches):
                onset = chord_start + bi
                if onset >= chord_start + chord_dur or onset >= duration_beats:
                    break

                # Beat 1 and 3 stronger
                vel = base_vel
                if bi == 0:
                    vel = min(127, base_vel + 5)
                elif bi == 2:
                    vel = min(127, base_vel + 2)

                vel = max(1, min(127, vel + random.randint(-3, 3)))

                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(onset, 4),
                    duration=0.85,
                    velocity=vel,
                ))

            if beat_pitches:
                prev_pitch = beat_pitches[-1]

            phrase_bar += 1
            if phrase_bar >= self.phrase_length:
                phrase_bar = 0

        return notes
