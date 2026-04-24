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
generators/bass.py — Specialized phrase generator for basslines.

Layer: Application / Domain

Allowed notes (style):
    "root"          – B (bass root)
    "fourth"        – B+IV (root + perfect 4th, +5 semitones)
    "sixth"         – B+VI (root + major 6th, +9 semitones)
    "lower_octave"  – B+loct (root one octave lower)

Global movement: "up", "down", "up_down", "none"
Note movement:   "none", "alternating"
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica import types
from melodica.types import ChordLabel, HarmonicFunction, NoteInfo, Scale
from melodica.utils import (
    nearest_pitch_above,
    nearest_pitch_below,
    nearest_pitch,
    pitch_class,
    chord_at,
)


STYLES = {"root_only", "root_fifth", "root_fifth_octave", "walking"}
ALLOWED_NOTE_TYPES = {"root", "fourth", "sixth", "lower_octave"}
GLOBAL_MOVEMENTS = {"up", "down", "up_down", "none"}
NOTE_MOVEMENTS = {"none", "alternating"}


@dataclass
class BassGenerator(PhraseGenerator):
    """
    Generates basslines.

    Style (legacy):
        'root_only', 'root_fifth', 'root_fifth_octave', or 'walking'

    Melodica-style params (override style when set):
        allowed_notes:        which notes are available (root, fourth, sixth, lower_octave)
        global_movement:      overall direction (up, down, up_down, none)
        note_movement:        per-note movement (none, alternating)
        transpose_octaves:    octave shift (-2..+2)
    """

    name: str = "Bass Generator"
    style: str = "root_only"
    allowed_notes: list[str] = field(default_factory=lambda: ["root"])
    global_movement: str = "none"
    note_movement: str = "alternating"
    transpose_octaves: int = 0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        style: str = "root_only",
        allowed_notes: list[str] | None = None,
        global_movement: str = "none",
        note_movement: str = "alternating",
        transpose_octaves: int = 0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if style not in STYLES:
            raise ValueError(f"style must be one of {sorted(STYLES)}; got {style}")
        self.style = style
        self.allowed_notes = allowed_notes if allowed_notes is not None else ["root"]
        for note in self.allowed_notes:
            if note not in ALLOWED_NOTE_TYPES:
                raise ValueError(
                    f"allowed note must be one of {sorted(ALLOWED_NOTE_TYPES)}; got {note!r}"
                )
        if global_movement not in GLOBAL_MOVEMENTS:
            raise ValueError(
                f"global_movement must be one of {sorted(GLOBAL_MOVEMENTS)}; got {global_movement!r}"
            )
        self.global_movement = global_movement
        if note_movement not in NOTE_MOVEMENTS:
            raise ValueError(
                f"note_movement must be one of {sorted(NOTE_MOVEMENTS)}; got {note_movement!r}"
            )
        self.note_movement = note_movement
        self.transpose_octaves = max(-2, min(2, transpose_octaves))
        self.rhythm = rhythm

    def render(
        self,
        chords: list[types.ChordLabel],
        key: types.Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[types.NoteInfo]:
        if not chords:
            return []

        if self.style == "walking" and self.allowed_notes == ["root"]:
            return self._render_walking(chords, key, duration_beats, context)

        # Use legacy path when style is non-default and allowed_notes is still default
        _use_legacy = self.allowed_notes == ["root"] and self.style != "root_only"

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        seq_idx = 0

        anchor_pitch = (
            context.prev_pitch
            if context and context.prev_pitch is not None
            else max(24, self.params.key_range_low)
        )

        prev_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue

            if _use_legacy:
                pitch = self._get_pitch_for_event(chord, seq_idx, anchor_pitch)
            else:
                # Build pitch pool from allowed notes
                pool = self._build_pool(chord, anchor_pitch)

                if not pool:
                    continue

                # Apply note movement
                if self.note_movement == "alternating":
                    pitch = pool[seq_idx % len(pool)]
                else:
                    pitch = pool[0]

                # Apply global movement (shift pitch by direction tendency)
                pitch = self._apply_global_movement(pitch, anchor_pitch, seq_idx)

                # Apply transpose
                pitch += self.transpose_octaves * types.OCTAVE

                # Update anchor for next event (new code path only)
                anchor_pitch = pitch

            # Clamp to range
            pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

            vel = int(self._velocity() * event.velocity_factor)

            notes.append(
                types.NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(0, min(types.MIDI_MAX, vel)),
                )
            )

            prev_chord = chord
            seq_idx += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )
        else:
            self._last_context = (context or RenderContext()).with_end_state(
                duration_beats=duration_beats,
                total_duration=duration_beats,
            )
        return notes

    # ------------------------------------------------------------------
    # Pool building
    # ------------------------------------------------------------------
    # Pool building
    # ------------------------------------------------------------------

    def _build_pool(self, chord: ChordLabel, anchor: int) -> list[int]:
        """Build sorted pitch pool from allowed_notes for the given chord."""
        root_pc = chord.bass if chord.bass is not None else chord.root
        low, high = self.params.key_range_low, self.params.key_range_high
        pool = []

        for note_type in self.allowed_notes:
            if note_type == "root":
                pool.append(self._nearest_in_range(root_pc, anchor))
            elif note_type == "fourth":
                fourth_pc = (root_pc + 5) % types.OCTAVE
                pool.append(self._nearest_in_range(fourth_pc, anchor))
            elif note_type == "sixth":
                sixth_pc = (root_pc + 9) % types.OCTAVE
                pool.append(self._nearest_in_range(sixth_pc, anchor))
            elif note_type == "lower_octave":
                root_pitch = self._nearest_in_range(root_pc, anchor)
                low_pitch = root_pitch - types.OCTAVE
                if low_pitch >= low:
                    pool.append(low_pitch)

        pool = sorted(set(p for p in pool if p is not None and low <= p <= high))

        # Apply global movement ordering
        if self.global_movement == "up":
            pool = sorted(pool)
        elif self.global_movement == "down":
            pool = sorted(pool, reverse=True)
        elif self.global_movement == "up_down":
            up = sorted(pool)
            pool = up + up[-2:0:-1]
        # "none" — keep insertion order (root first)

        return pool if pool else [nearest_pitch(root_pc, anchor)]

    def _apply_global_movement(self, pitch: int, anchor: int, seq_idx: int) -> int:
        """Apply global movement tendency (gradual shift up or down)."""
        if self.global_movement == "none":
            return pitch
        if self.global_movement == "up":
            # Slight upward nudge every few notes
            if seq_idx > 0 and seq_idx % 4 == 0:
                pitch += 1
        elif self.global_movement == "down":
            if seq_idx > 0 and seq_idx % 4 == 0:
                pitch -= 1
        return pitch

    def _nearest_in_range(self, pc: int, anchor: int) -> int:
        """Find nearest pitch with given pitch class that is within key range."""
        low, high = self.params.key_range_low, self.params.key_range_high
        p = nearest_pitch(pc, anchor)
        if low <= p <= high:
            return p
        # Try above
        p_up = nearest_pitch_above(pc, low)
        if p_up <= high:
            return p_up
        # Try below
        p_down = nearest_pitch_below(pc, high)
        if p_down >= low:
            return p_down
        return p

    # ------------------------------------------------------------------
    # Legacy pitch logic
    # ------------------------------------------------------------------

    def _get_pitch_for_event(
        self, chord: types.ChordLabel, seq_idx: int, anchor_pitch: int | None = None
    ) -> int:
        pool_pcs = self._get_pool_pcs(chord)
        target_pc = pool_pcs[seq_idx % len(pool_pcs)]

        if anchor_pitch is None:
            anchor_pitch = max(24, self.params.key_range_low)
        pitch = nearest_pitch(target_pc, anchor_pitch)

        if self.style == "root_fifth_octave" and (seq_idx % len(pool_pcs)) == 2:
            pitch += types.OCTAVE
        low, high = self.params.key_range_low, self.params.key_range_high
        if pitch < low:
            snap_up = nearest_pitch_above(target_pc, low)
            if snap_up <= high:
                pitch = snap_up
            else:
                snap_down = nearest_pitch_below(target_pc, high)
                pitch = snap_down if snap_down >= low else snap_up
        elif pitch > high:
            snap_down = nearest_pitch_below(target_pc, high)
            if snap_down >= low:
                pitch = snap_down
            else:
                snap_up = nearest_pitch_above(target_pc, low)
                pitch = snap_up if snap_up <= high else snap_down
        return pitch

    def _get_pool_pcs(self, chord: types.ChordLabel) -> list[int]:
        bass_pc = chord.bass if chord.bass is not None else chord.root
        pool = [bass_pc]

        if self.style in ("root_fifth", "root_fifth_octave"):
            is_dim = chord.quality in (
                types.Quality.DIMINISHED,
                types.Quality.HALF_DIM7,
                types.Quality.FULL_DIM7,
            )
            fifth_pc = (chord.root + (6 if is_dim else 7)) % types.OCTAVE
            pool.append(fifth_pc)

        if self.style == "root_fifth_octave":
            pool.append(bass_pc)
        return pool

    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default fallback: straight quarter notes
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.9))
            t += 1.0
        return events

    def _velocity(self) -> int:
        return int(70 + self.params.density * 30)

    # ------------------------------------------------------------------
    # Walking bass
    # ------------------------------------------------------------------

    def _walking_pitch(
        self,
        chord: ChordLabel,
        next_chord: ChordLabel | None,
        beat_in_chord: int,
        beats_in_chord: int,
        prev_pitch: int,
        key: Scale,
    ) -> int:
        """Choose a pitch for walking bass style."""
        root_pc = chord.root
        pcs = chord.pitch_classes()

        if beat_in_chord == 0:
            return nearest_pitch(root_pc, max(24, self.params.key_range_low))

        if next_chord is not None and beat_in_chord >= beats_in_chord - 1:
            next_root = nearest_pitch(next_chord.root, prev_pitch)
            if chord.function == HarmonicFunction.DOMINANT or (
                chord.degree is not None and chord.degree == 5
            ):
                if next_chord.degree is not None and next_chord.degree == 1:
                    resolution = next_root - 1
                    return max(24, min(self.params.key_range_high, resolution))
            if prev_pitch > next_root:
                approach = next_root - 1
            else:
                approach = next_root + 1
            return max(24, min(self.params.key_range_high, approach))

        if self.params.complexity > 0.5 and random.random() < 0.4:
            direction = 1 if root_pc > prev_pitch % 12 else -1
            pass_pc = (prev_pitch + direction) % 12
            if not key.contains(pass_pc):
                for offset in [direction, -direction]:
                    if key.contains((prev_pitch + offset) % 12):
                        pass_pc = (prev_pitch + offset) % 12
                        break
            return nearest_pitch(pass_pc, prev_pitch)

        if pcs:
            return min(
                (nearest_pitch(pc, prev_pitch) for pc in pcs),
                key=lambda p: abs(p - prev_pitch),
            )
        return nearest_pitch(root_pc, max(24, self.params.key_range_low))

    def _render_walking(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        if not chords:
            return []
        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        prev_pitch = (
            context.prev_pitch
            if context and context.prev_pitch is not None
            else max(24, self.params.key_range_low)
        )
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            next_chord: ChordLabel | None = None
            for c in chords:
                if c.start > event.onset:
                    next_chord = c
                    break

            beats_in_chord = int(chord.duration)
            beat_in_chord = int(event.onset - chord.start)

            pitch = self._walking_pitch(
                chord,
                next_chord,
                beat_in_chord,
                beats_in_chord,
                prev_pitch,
                key,
            )
            pitch += self.transpose_octaves * types.OCTAVE
            pitch = max(24, min(self.params.key_range_high, pitch))

            base_vel = int(70 + self.params.density * 30)
            if event.onset % 4.0 < 0.1:
                base_vel = min(127, int(base_vel * 1.15))

            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(event.onset, 6),
                    duration=event.duration,
                    velocity=max(1, min(127, int(base_vel * event.velocity_factor))),
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
