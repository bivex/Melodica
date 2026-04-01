"""
generators/hocket.py — Hocket / interlocking pattern generator.

Layer: Application / Domain
Style: Minimalism, African polyphony, contemporary classical, electronic.

Hocket (from French "hoquet") divides a melody between two or more voices,
with each voice playing only some of the notes and resting while the other
sounds. This creates an interlocking texture where the combined output
forms a single coherent line.

This generator produces one voice of a hocket pair. To create the full
hocket effect, use two instances with complementary rhythm patterns.

Pattern types:
    "alternating" — strict alternation: A-B-A-B
    "syncopated"  — offbeat emphasis: rest-onbeat, play-offbeat
    "euclidean"   — Euclidean rhythm distribution
    "random"      — random selection per event
    "long_short"  — long note then short rest pattern
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class HocketGenerator(PhraseGenerator):
    """
    Hocket / interlocking pattern generator.

    This generator produces a voice that plays on a subset of events,
    creating the hocket effect when combined with its complement.

    hocket_pattern:
        "alternating" — play on even events, rest on odd (or vice versa)
        "syncopated"  — play on offbeats
        "euclidean"   — distribute notes using Euclidean rhythm
        "random"      — random play/skip per event
        "long_short"  — play long note, skip next event
    voice_index:
        0 or 1 — which voice of the hocket pair (affects which events are played)
    euclidean_pulses:
        For "euclidean" pattern: number of pulses.
    euclidean_steps:
        For "euclidean" pattern: total steps.
    """

    name: str = "Hocket Generator"
    hocket_pattern: str = "alternating"
    voice_index: int = 0
    euclidean_pulses: int = 3
    euclidean_steps: int = 4
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        hocket_pattern: str = "alternating",
        voice_index: int = 0,
        euclidean_pulses: int = 3,
        euclidean_steps: int = 4,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if hocket_pattern not in ("alternating", "syncopated", "euclidean", "random", "long_short"):
            raise ValueError(
                f"hocket_pattern must be one of 'alternating', 'syncopated', "
                f"'euclidean', 'random', 'long_short'; got {hocket_pattern!r}"
            )
        self.hocket_pattern = hocket_pattern
        self.voice_index = 0 if voice_index == 0 else 1
        self.euclidean_pulses = max(1, euclidean_pulses)
        self.euclidean_steps = max(2, euclidean_steps)
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
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        # Pre-compute hocket mask
        mask = self._hocket_mask(len(events))

        for i, event in enumerate(events):
            if i >= len(mask) or not mask[i]:
                continue  # this event belongs to the other voice

            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            pitch = self._pick_pitch(chord, prev_pitch, key, low, high)

            vel = int(self._velocity() * event.velocity_factor)

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, vel)),
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
    # Hocket mask
    # ------------------------------------------------------------------

    def _hocket_mask(self, count: int) -> list[bool]:
        """Generate a boolean mask: True = this voice plays, False = rest."""
        if count <= 0:
            return []

        if self.hocket_pattern == "alternating":
            return [(i % 2) == self.voice_index for i in range(count)]

        elif self.hocket_pattern == "syncopated":
            # Voice 0 plays on beats, voice 1 plays on offbeats
            if self.voice_index == 0:
                return [(i % 2) == 0 for i in range(count)]
            else:
                return [(i % 2) == 1 for i in range(count)]

        elif self.hocket_pattern == "euclidean":
            # Generate Euclidean rhythm.
            # bjorklund returns 0/1: voice 0 plays on pulses (1), voice 1 on rests (0).
            pattern = self._bjorklund(self.euclidean_pulses, self.euclidean_steps)
            mask = []
            for i in range(count):
                idx = i % len(pattern)
                mask.append(pattern[idx] == (1 - self.voice_index))
            return mask

        elif self.hocket_pattern == "random":
            return [random.random() > 0.5 for _ in range(count)]

        elif self.hocket_pattern == "long_short":
            # Voice 0: play on groups of 2 (first note), rest on second
            # Voice 1: opposite
            if self.voice_index == 0:
                return [(i % 2) == 0 for i in range(count)]
            else:
                return [(i % 2) == 1 for i in range(count)]

        return [True] * count

    @staticmethod
    def _bjorklund(pulses: int, steps: int) -> list[int]:
        """Euclidean rhythm via Bjorklund's algorithm."""
        if pulses <= 0:
            return [0] * steps
        if pulses >= steps:
            return [1] * steps

        groups = [[1] if i < pulses else [0] for i in range(steps)]

        while True:
            # Find smallest and largest groups
            min_len = min(len(g) for g in groups)
            # Count groups by length
            by_len: dict[int, list[int]] = {}
            for i, g in enumerate(groups):
                l = len(g)
                by_len.setdefault(l, []).append(i)

            if len(by_len) <= 1:
                break

            # Merge shortest groups with longest
            sorted_lengths = sorted(by_len.keys())
            short_idx = by_len[sorted_lengths[0]]
            long_idx = by_len[sorted_lengths[-1]]

            if not short_idx or not long_idx:
                break

            new_groups = []
            used_short = set()
            used_long = set()

            for i in range(min(len(short_idx), len(long_idx))):
                si, li = short_idx[i], long_idx[i]
                new_groups.append(groups[si] + groups[li])
                used_short.add(si)
                used_long.add(li)

            for i, g in enumerate(groups):
                if i not in used_short and i not in used_long:
                    new_groups.append(g)

            groups = new_groups

        result = []
        for g in groups:
            result.extend(g)
        return result[:steps]

    # ------------------------------------------------------------------
    # Pitch selection
    # ------------------------------------------------------------------

    def _pick_pitch(
        self, chord: ChordLabel, prev_pitch: int, key: Scale, low: int, high: int
    ) -> int:
        # Prefer chord tones for clarity (hocket needs strong pitch identity)
        pcs = chord.pitch_classes()
        if random.random() < 0.75:
            pc = random.choice(pcs)
        else:
            degs = key.degrees()
            pc = int(random.choice(degs)) if degs else chord.root

        pitch = nearest_pitch(pc, prev_pitch)

        # Occasional octave displacement for interest
        if random.random() < 0.2:
            pitch += random.choice([-12, 12])

        return max(low, min(high, pitch))

    # ------------------------------------------------------------------
    # Rhythm & velocity
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default: steady eighth notes
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.4))
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 30)
