"""Side-slipping generator.

Side-slipping (or side-stepping) is a jazz technique where the player
shifts an idea up or down by a half-step, creating momentary tension,
then resolves back to the original key. Used extensively by:
  - John Coltrane (sheets of sound)
  - Michael Brecker
  - Woody Shaw
  - Kenny Werner

The generator plays a short motif, transposes it by a semitone,
then resolves back — creating an "out" and "in" effect.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch, snap_to_scale


@dataclass
class SideSlippingGenerator(PhraseGenerator):
    """Generate side-slipping patterns (half-step out and back).

    Parameters
    ----------
    slip_direction : str
        "up" — slip up a half-step.
        "down" — slip down a half-step.
        "both" — random direction per phrase.
    phrase_length : int
        Notes per phrase segment (before slip and after).
    slip_duration : int
        Number of notes in the "slipped" (outside) segment.
    resolution_style : str
        "direct" — snap back to nearest chord tone.
        "chromatic" — walk back by half-steps.
        "scale" — resolve through scale steps.
    pattern_source : str
        "arpeggio" — base pattern from chord arpeggio.
        "scale" — base pattern from scale run.
        "mixed" — varied patterns.
    """

    name: str = field(default="side_slipping", init=False)
    slip_direction: str = "both"
    phrase_length: int = 4
    slip_duration: int = 3
    resolution_style: str = "chromatic"
    pattern_source: str = "arpeggio"
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid_dir = ("up", "down", "both")
        if self.slip_direction not in valid_dir:
            raise ValueError(f"slip_direction must be one of {valid_dir}")

    def _build_in_pattern(self, chord: ChordLabel, key: Scale, anchor: int) -> list[int]:
        """Build the 'inside' (in-key) phrase."""
        low = self.params.key_range_low
        high = self.params.key_range_high
        pcs = chord.pitch_classes()
        degs = key.degrees()

        pitches: list[int] = []
        current = anchor

        for _ in range(self.phrase_length):
            if self.pattern_source == "arpeggio" and pcs:
                pc = int(random.choice(pcs))
            elif self.pattern_source == "scale" and degs:
                pc = int(random.choice(degs)) % 12
            else:
                pc = int(random.choice(pcs)) if pcs else chord.root

            p = nearest_pitch(pc, current)
            p = max(low, min(high, p))
            pitches.append(p)
            current = p

        return pitches

    def _apply_slip(self, pitches: list[int], direction: int) -> list[int]:
        """Transpose pitches by a half-step."""
        return [max(0, min(127, p + direction)) for p in pitches]

    def _resolve(
        self, last_slip_pitch: int, chord: ChordLabel, key: Scale
    ) -> list[int]:
        """Build resolution notes back to the chord."""
        low = self.params.key_range_low
        high = self.params.key_range_high
        pcs = chord.pitch_classes()

        # Target: nearest chord tone
        targets = [nearest_pitch(int(pc), last_slip_pitch) for pc in pcs]
        target = min(targets, key=lambda t: abs(t - last_slip_pitch))
        target = max(low, min(high, target))

        if self.resolution_style == "direct":
            return [target]

        if self.resolution_style == "chromatic":
            notes = []
            current = last_slip_pitch
            direction = 1 if target > current else -1
            while current != target and len(notes) < 4:
                current += direction
                current = max(low, min(high, current))
                notes.append(current)
            return notes

        # scale: step through scale degrees
        notes = []
        current = last_slip_pitch
        for _ in range(3):
            direction = 1 if target > current else -1
            step = snap_to_scale(current + direction * 2, key)
            step = max(low, min(high, step))
            notes.append(step)
            current = step
            if current == target:
                break
        return notes

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
        anchor = (low + high) // 2

        beat_dur = 0.5  # eighth notes
        t = 0.0

        for chord in chords:
            chord_start = chord.start
            chord_dur = chord.duration

            # Build pattern: in → slip → resolve → in
            in_pitches = self._build_in_pattern(chord, key, anchor)

            direction = 1
            if self.slip_direction == "down":
                direction = -1
            elif self.slip_direction == "both":
                direction = random.choice([-1, 1])

            slip_pitches = self._apply_slip(
                in_pitches[:self.slip_duration], direction
            )
            resolve_pitches = self._resolve(
                slip_pitches[-1] if slip_pitches else anchor, chord, key
            )

            # Time allocation
            total_notes = len(in_pitches) + len(slip_pitches) + len(resolve_pitches)
            if total_notes == 0:
                continue

            segment_dur = chord_dur / total_notes
            onset = chord_start

            # "In" phrase
            for p in in_pitches:
                if onset >= chord_start + chord_dur or onset >= duration_beats:
                    break
                notes.append(NoteInfo(
                    pitch=max(low, min(high, p)),
                    start=round(onset, 4),
                    duration=segment_dur * 0.85,
                    velocity=base_vel,
                ))
                onset += segment_dur

            # "Slip" phrase (slightly louder for tension)
            for p in slip_pitches:
                if onset >= chord_start + chord_dur or onset >= duration_beats:
                    break
                notes.append(NoteInfo(
                    pitch=max(low, min(high, p)),
                    start=round(onset, 4),
                    duration=segment_dur * 0.85,
                    velocity=min(127, base_vel + 5),
                ))
                onset += segment_dur

            # Resolution (slightly softer — landing)
            for p in resolve_pitches:
                if onset >= chord_start + chord_dur or onset >= duration_beats:
                    break
                notes.append(NoteInfo(
                    pitch=max(low, min(high, p)),
                    start=round(onset, 4),
                    duration=segment_dur * 0.9,
                    velocity=max(1, base_vel - 3),
                ))
                onset += segment_dur

            anchor = in_pitches[-1] if in_pitches else anchor

        return notes
