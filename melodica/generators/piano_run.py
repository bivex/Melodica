"""
generators/piano_run.py — PianoRunGenerator.

Layer: Application / Domain

Techniques:
    straddle               – alternate above/below center note
    straddle_without_middle – straddle without repeating center
    2-1_breakup            – 2 up, 1 back (rock/pop)
    3-1_breakup            – 3 up, 1 back (flowing)
    waterfall              – descending cascade
    waterfall_inversions   – waterfall via chord inversions

Motion:
    up_down – bidirectional from anchor
    up      – ascending only from anchor
"""

from __future__ import annotations

from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import chord_pitches_closed, chord_at


TECHNIQUES = frozenset(
    {
        "straddle",
        "straddle_without_middle",
        "2-1_breakup",
        "3-1_breakup",
        "waterfall",
        "waterfall_inversions",
    }
)

MOTIONS = frozenset({"up_down", "up"})


@dataclass
class PianoRunGenerator(PhraseGenerator):
    """
    Generates fast melodic runs or sweeps (arpeggios/scales) within an event duration.
    Instead of 1 note per rhythm event, it packs `notes_per_run` notes into the duration.

    technique:
        None                     – use direction/scale_steps (legacy)
        "straddle"               – alternate above/below center note
        "straddle_without_middle" – straddle, skip center note
        "2-1_breakup"            – 2 notes up, 1 back
        "3-1_breakup"            – 3 notes up, 1 back
        "waterfall"              – descending cascade
        "waterfall_inversions"   – waterfall through chord inversions

    motion:
        "up_down" – bidirectional from anchor
        "up"      – ascending only

    up_motion_range:   max semitones upward from starting pitch (default 28 = ~2 octaves)
    down_motion_range: max semitones downward from starting pitch (default 18 = ~1.5 octaves)
    """

    name: str = "Piano Run"
    direction: str = "up"  # legacy: 'up', 'down', 'up_down'
    scale_steps: bool = False  # legacy: True = scale tones, False = chord tones
    technique: str | None = None
    motion: str = "up_down"
    up_motion_range: int = 28
    down_motion_range: int = 18
    notes_per_run: int = 4
    rhythm: RhythmGenerator | None = None
    note_range_low: int | None = None
    note_range_high: int | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        direction: str = "up",
        scale_steps: bool = False,
        technique: str | None = None,
        motion: str = "up_down",
        up_motion_range: int = 28,
        down_motion_range: int = 18,
        notes_per_run: int = 4,
        rhythm: RhythmGenerator | None = None,
        note_range_low: int | None = None,
        note_range_high: int | None = None,
    ) -> None:
        super().__init__(params)
        valid_dirs = {"up", "down", "up_down"}
        if direction not in valid_dirs:
            raise ValueError(f"direction must be in {valid_dirs}")
        if technique is not None and technique not in TECHNIQUES:
            raise ValueError(f"technique must be one of {sorted(TECHNIQUES)}; got {technique!r}")
        if motion not in MOTIONS:
            raise ValueError(f"motion must be one of {sorted(MOTIONS)}; got {motion!r}")
        self.direction = direction
        self.scale_steps = scale_steps
        self.technique = technique
        self.motion = motion
        self.up_motion_range = max(1, up_motion_range)
        self.down_motion_range = max(1, down_motion_range)
        self.notes_per_run = max(2, notes_per_run)
        self.rhythm = rhythm
        self.note_range_low = note_range_low
        self.note_range_high = note_range_high
        self._last_context: RenderContext | None = None

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        low = self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )

        # Anchor start pitch from previous phrase if available; otherwise use
        # the middle of the range so runs don't always start in the lowest register.
        if context is not None and context.prev_pitch is not None:
            anchor_pitch = context.prev_pitch
        else:
            anchor_pitch = (low + high) // 2

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue

            # Build the pitch pool
            if self.technique is not None:
                pool = self._build_pool_v2(chord, key, anchor=anchor_pitch)
            elif self.scale_steps:
                pool = self._build_scale_pool(chord, key, anchor=anchor_pitch)
            else:
                pool = self._build_chord_pool(chord, anchor=anchor_pitch)

            if not pool:
                continue

            # Build the sequence
            if self.technique is not None:
                seq = self._build_technique_sequence(pool)
            else:
                seq = self._build_sequence(pool)

            if not seq:
                continue

            # Fit `notes_per_run` notes across `event.duration`
            step_duration = event.duration / self.notes_per_run
            base_vel = self._velocity()
            vel = int(base_vel * event.velocity_factor)

            for i in range(self.notes_per_run):
                pitch = seq[i % len(seq)]
                onset = event.onset + (i * step_duration)

                # Accent the first and last notes slightly
                accent = 1.1 if i == 0 or i == self.notes_per_run - 1 else 0.9

                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=round(step_duration * 0.95, 6),
                        velocity=max(1, min(127, int(vel * accent))),
                    )
                )

            # Update anchor so next event continues from this register
            if notes:
                anchor_pitch = notes[-1].pitch

        from melodica.generators._postprocess import apply_phrase_arch

        notes = apply_phrase_arch(
            notes, duration_beats, context.phrase_position if context else 0.0
        )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, notes[-1].start),
                last_pitches=[n.pitch for n in notes[-4:]]
                if len(notes) >= 4
                else [n.pitch for n in notes],
            )

        return notes

    # ------------------------------------------------------------------
    # Pool builders
    # ------------------------------------------------------------------

    def _build_chord_pool(self, chord: ChordLabel, anchor: int | None = None) -> list[int]:
        range_low = (
            self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        )
        range_high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )
        bass = anchor if anchor is not None else range_low
        bass = max(range_low, min(range_high, bass))
        base = chord_pitches_closed(chord, bass)
        pool = list(base)
        for i in range(1, 4):
            pool.extend([p + 12 * i for p in base])
        return sorted(list(set(pool)))

    def _build_scale_pool(
        self, chord: ChordLabel, key: Scale, anchor: int | None = None
    ) -> list[int]:
        range_low = (
            self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        )
        range_high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )
        root_pc = chord.root
        start_pitch = anchor if anchor is not None else range_low
        while (start_pitch % 12) != root_pc:
            start_pitch += 1
            if start_pitch > range_high:
                start_pitch -= 24

        pool = []
        cur = start_pitch
        while cur < start_pitch + 36:
            if key.contains(cur % 12):
                pool.append(cur)
            cur += 1
        return pool

    def _build_pool_v2(self, chord: ChordLabel, key: Scale, anchor: int | None = None) -> list[int]:
        """Build pool using motion range limits (technique-aware)."""
        range_low = (
            self.note_range_low if self.note_range_low is not None else self.params.key_range_low
        )
        range_high = (
            self.note_range_high if self.note_range_high is not None else self.params.key_range_high
        )
        center = anchor if anchor is not None else range_low
        center = max(range_low, min(range_high, center))

        if self.scale_steps:
            base_pool = self._build_scale_pool(chord, key, anchor=center)
        else:
            base_pool = self._build_chord_pool(chord, anchor=center)

        # Filter by motion ranges
        lo = max(range_low, center - self.down_motion_range)
        hi = min(range_high, center + self.up_motion_range)
        pool = [p for p in base_pool if lo <= p <= hi]

        if self.motion == "up":
            pool = [p for p in pool if p >= center]

        return sorted(pool)

    # ------------------------------------------------------------------
    # Sequence builders
    # ------------------------------------------------------------------

    def _build_sequence(self, pool: list[int]) -> list[int]:
        """Legacy sequence builder (direction + scale_steps mode)."""
        sliced = pool[: self.notes_per_run]
        if self.direction == "up":
            return sliced
        elif self.direction == "down":
            return list(reversed(sliced))
        else:  # up_down
            half = max(1, self.notes_per_run // 2)
            up = sliced[:half]
            down = list(reversed(sliced[:half]))
            return up + down

    def _build_technique_sequence(self, pool: list[int]) -> list[int]:
        """Dispatch to technique-specific sequence builder."""
        if not pool:
            return []
        match self.technique:
            case "straddle":
                return self._straddle(pool)
            case "straddle_without_middle":
                return self._straddle_without_middle(pool)
            case "2-1_breakup":
                return self._breakup_2_1(pool)
            case "3-1_breakup":
                return self._breakup_3_1(pool)
            case "waterfall":
                return self._waterfall(pool)
            case "waterfall_inversions":
                return self._waterfall_inversions(pool)
            case _:
                return sorted(pool)

    def _straddle(self, pool: list[int]) -> list[int]:
        """
        Straddle: alternate above/below a center note.
        Center, +1, Center, -1, Center, +2, Center, -2, ...
        [48, 52, 55, 60, 64, 67] → [60, 64, 60, 55, 60, 67, 60, 52]
        """
        center_idx = len(pool) // 2
        result = [pool[center_idx]]
        for offset in range(1, center_idx + 1):
            if center_idx + offset < len(pool):
                result.append(pool[center_idx + offset])
            result.append(pool[center_idx])
            if center_idx - offset >= 0:
                result.append(pool[center_idx - offset])
            if center_idx + offset < len(pool) or center_idx - offset >= 0:
                result.append(pool[center_idx])
        return result

    def _straddle_without_middle(self, pool: list[int]) -> list[int]:
        """
        Straddle without repeating center note.
        +1, -1, +2, -2, +3, -3, ...
        [48, 52, 55, 60, 64, 67] → [64, 55, 67, 52]
        """
        center_idx = len(pool) // 2
        result = []
        for offset in range(1, center_idx + 1):
            if center_idx + offset < len(pool):
                result.append(pool[center_idx + offset])
            if center_idx - offset >= 0:
                result.append(pool[center_idx - offset])
        return result

    def _breakup_2_1(self, pool: list[int]) -> list[int]:
        """
        2-1 Breakup: 2 notes up, 1 back (rock/pop pattern).
        [0,1,2,3,4] → [0,1,2, 1,2,3, 2,3,4, 3,4,3]
        Each triplet: n, n+1, n (step back).
        """
        up = sorted(pool)
        n = len(up)
        result = []
        i = 0
        while i < n and len(result) < self.notes_per_run * 2:
            if i + 1 < n:
                result.extend([up[i], up[i + 1], up[i]])
                i += 1
            else:
                result.append(up[i])
                i += 1
        return result

    def _breakup_3_1(self, pool: list[int]) -> list[int]:
        """
        3-1 Breakup: 3 notes up, 1 back (flowing pattern).
        [0,1,2,3,4,5] → [0,1,2,3, 1,2,3,4, 2,3,4,5]
        Each group of 4: n, n+1, n+2, n+1 (step back from peak).
        """
        up = sorted(pool)
        n = len(up)
        result = []
        i = 0
        while i < n and len(result) < self.notes_per_run * 2:
            if i + 2 < n:
                result.extend([up[i], up[i + 1], up[i + 2], up[i + 1]])
                i += 1
            elif i + 1 < n:
                result.extend([up[i], up[i + 1]])
                i += 1
            else:
                result.append(up[i])
                i += 1
        return result

    def _waterfall(self, pool: list[int]) -> list[int]:
        """
        Waterfall: descending cascade from top of pool.
        [48,52,55,60,64,67] → [67,64,60,55,52,48]
        """
        return sorted(pool, reverse=True)

    def _waterfall_inversions(self, pool: list[int]) -> list[int]:
        """
        Waterfall using inversions: descend by pitch, dropping the top
        note down an octave at each step (inversion waterfall).
        [48,52,55,60] → [60,55,52,48, 60+12=72,55,52,48, ...]
        Actually: for each step, take top note, drop it an octave,
        then re-sort. Creates smooth descent through inversions.
        [48,52,55,60] → [60,55,52,48,  48,52,55,36] ... simplification:
        Just cycle inversions: each successive chord drops top note an octave.
        """
        up = sorted(pool)
        n = len(up)
        if n < 2:
            return up
        result = []
        # Generate several inversions by dropping top note each time
        current = list(up)
        for _ in range(max(1, self.notes_per_run // n + 1)):
            result.extend(sorted(current, reverse=True))
            # Drop the highest note down an octave
            current.sort()
            current[-1] -= 12
            current = sorted(current)
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default: fire a run once per measure
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=3.8))
            t += 4.0
        return events

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)
