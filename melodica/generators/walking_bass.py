# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/walking_bass.py — Dedicated jazz walking bass generator.

Layer: Application / Domain
Style: Bebop / swing era walking bass lines.

A walking bass line plays one note per beat, chromatically or diatonically
connecting chord roots with approach notes and passing tones. This is a
first-class generator (not a mode of BassGenerator) because walking bass
has fundamentally different voice-leading rules.

Approach strategies:
    chromatic  — half-step below or above next chord root
    diatonic   — scale step approaching next root
    enclosure  — chromatic approach from both sides (complexity > 0.7)

Beat roles:
    beat 1    — chord root (always)
    beat 3    — chord tone (3rd, 5th, or 7th)
    beat 2,4  — passing tone or approach note targeting next root
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, HarmonicFunction, NoteInfo, Quality, Scale
from melodica.utils import nearest_pitch, nearest_pitch_above, chord_at


# Blues scale intervals (minor pentatonic + b5)
BLUES_INTERVALS = [0, 3, 5, 6, 7, 10]


@dataclass
class WalkingBassGenerator(PhraseGenerator):
    """
    Jazz walking bass: one note per beat connecting chord changes.

    approach_style:
        "chromatic" — half-step approach to next root
        "diatonic"  — scale-step approach
        "mixed"     — choose per beat based on context
    connect_roots:
        When True, the last beat of each chord targets the next chord's root.
    add_chromatic_passing:
        Insert chromatic passing tones between distant chord tones.
    swing_eighth_ratio:
        For eighth-note subdivisions: ratio of long to short (1.0 = straight).
        Default 0.67 for triplet swing feel.
    """

    name: str = "Walking Bass Generator"
    approach_style: str = "mixed"
    connect_roots: bool = True
    add_chromatic_passing: bool = True
    swing_eighth_ratio: float = 0.67
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        approach_style: str = "mixed",
        connect_roots: bool = True,
        add_chromatic_passing: bool = True,
        swing_eighth_ratio: float = 0.67,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if approach_style not in ("chromatic", "diatonic", "mixed"):
            raise ValueError(
                f"approach_style must be 'chromatic', 'diatonic', or 'mixed'; got {approach_style!r}"
            )
        self.approach_style = approach_style
        self.connect_roots = connect_roots
        self.add_chromatic_passing = add_chromatic_passing
        self.swing_eighth_ratio = max(0.5, min(1.0, swing_eighth_ratio))
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
        low = max(24, self.params.key_range_low)

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else low
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Find next chord
            next_chord: ChordLabel | None = None
            for c in chords:
                if c.start > event.onset + 0.01:
                    next_chord = c
                    break

            beat_in_chord = int(round(event.onset - chord.start))
            total_beats_in_chord = max(1, int(round(chord.duration)))

            pitch = self._pick_pitch(
                chord, next_chord, beat_in_chord, total_beats_in_chord, prev_pitch, key
            )
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            # Velocity: downbeat emphasis
            vel = self._velocity(beat_in_chord)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, int(vel * event.velocity_factor))),
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

    # ------------------------------------------------------------------
    # Pitch selection
    # ------------------------------------------------------------------

    def _pick_pitch(
        self,
        chord: ChordLabel,
        next_chord: ChordLabel | None,
        beat_in_chord: int,
        total_beats: int,
        prev_pitch: int,
        key: Scale,
    ) -> int:
        root_pc = chord.root
        pcs = chord.pitch_classes()

        # Beat 1: always root
        if beat_in_chord % total_beats == 0:
            return nearest_pitch(root_pc, prev_pitch)

        # Last beat before chord change: approach next root
        is_last_beat = (beat_in_chord + 1) >= total_beats
        if is_last_beat and next_chord is not None and self.connect_roots:
            return self._approach_note(chord, next_chord, prev_pitch, key)

        # Beat 3 (in 4/4): chord tone (3rd, 5th, or 7th)
        if beat_in_chord % 4 == 2 and len(pcs) > 1:
            # Prefer 3rd or 7th for color
            third_pc = pcs[1] if len(pcs) > 1 else pcs[0]
            seventh_pc = pcs[3] if len(pcs) > 3 else pcs[-1]
            candidates = [
                nearest_pitch(third_pc, prev_pitch),
                nearest_pitch(seventh_pc, prev_pitch),
            ]
            if len(pcs) > 2:
                candidates.append(nearest_pitch(pcs[2], prev_pitch))  # 5th
            return min(candidates, key=lambda p: abs(p - prev_pitch))

        # Other beats: chord tone or passing tone
        if random.random() < 0.6:
            # Chord tone
            pc = random.choice(pcs)
            return nearest_pitch(pc, prev_pitch)
        else:
            # Passing tone (scale or chromatic)
            return self._passing_tone(chord, prev_pitch, key)

    def _approach_note(
        self,
        chord: ChordLabel,
        next_chord: ChordLabel,
        prev_pitch: int,
        key: Scale,
    ) -> int:
        next_root_pc = next_chord.root
        next_root_pitch = nearest_pitch(next_root_pc, prev_pitch)

        if self.approach_style == "chromatic" or (
            self.approach_style == "mixed" and random.random() < 0.6
        ):
            # Chromatic approach: half-step below or above
            if prev_pitch > next_root_pitch:
                return max(self.params.key_range_low, next_root_pitch - 1)
            else:
                return min(self.params.key_range_high, next_root_pitch + 1)
        else:
            # Diatonic approach: nearest scale step to next root
            degs = key.degrees()
            best_pc = min(
                degs, key=lambda d: abs(nearest_pitch(int(d), next_root_pitch) - next_root_pitch)
            )
            approach = nearest_pitch(int(best_pc), next_root_pitch)
            # Make sure it's not the same as the target
            if approach == next_root_pitch:
                approach += 1 if prev_pitch < next_root_pitch else -1
            return max(self.params.key_range_low, min(self.params.key_range_high, approach))

    def _passing_tone(self, chord: ChordLabel, prev_pitch: int, key: Scale) -> int:
        """Generate a passing tone between chord tones."""
        degs = key.degrees()
        if not degs:
            return prev_pitch

        # Choose a scale tone near prev_pitch
        candidates = [nearest_pitch(int(d), prev_pitch) for d in degs]
        # Filter to those within a step of prev_pitch
        step_candidates = [p for p in candidates if 1 <= abs(p - prev_pitch) <= 2]
        if step_candidates:
            return random.choice(step_candidates)

        # Chromatic passing
        direction = random.choice([-1, 1])
        return max(
            self.params.key_range_low,
            min(self.params.key_range_high, prev_pitch + direction),
        )

    # ------------------------------------------------------------------
    # Rhythm & velocity
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Walking bass: one note per beat, slightly swung
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.9))
            t += 1.0
        return events

    def _velocity(self, beat_in_chord: int) -> int:
        base = int(65 + self.params.density * 30)
        if beat_in_chord % 4 == 0:
            return min(127, int(base * 1.15))
        return base
