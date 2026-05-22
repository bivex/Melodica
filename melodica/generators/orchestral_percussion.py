# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_percussion.py -- Timpani and mallet percussion generators.

Timpani: pitched orchestral bass drums (kettle drums), 2-5 drums.
Mallet: marimba, xylophone, vibraphone, glockenspiel.

Layer: Application / Domain
Style: Classical, cinematic, film scoring, orchestral.
"""

from __future__ import annotations

import random
import math

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_at


# ---------------------------------------------------------------------------
# Instrument ranges (MIDI pitches)
# ---------------------------------------------------------------------------

TIMPANI_LOW = 36   # C2
TIMPANI_HIGH = 60  # C4

MALLET_RANGES = {
    "marimba":      {"low": 45, "high": 84, "vel_base": 65, "vel_spread": 15},
    "xylophone":    {"low": 65, "high": 96, "vel_base": 85, "vel_spread": 15},
    "vibraphone":   {"low": 53, "high": 89, "vel_base": 72, "vel_spread": 13},
    "glockenspiel": {"low": 72, "high": 108, "vel_base": 72, "vel_spread": 18},
}

TYPICAL_PRIMARY = [0, 7, 2, 5, 10]  # common timpani tuning PCs relative to root


# ---------------------------------------------------------------------------
# Timpani Generator
# ---------------------------------------------------------------------------

class TimpaniGenerator(PhraseGenerator):
    """
    Orchestral timpani (kettle drums) -- pitched bass percussion.

    stroke_pattern:
        "single"   -- one hit per chord change, root on strong beats
        "roll"     -- sustained tremolo on root
        "fanfare"  -- alternating root and fifth (boom-bah-boom-bah)
        "accented" -- hits on beat 1 of each bar, occasional offbeat accents

    drum_count:   2-5 drums available
    tuning_follows: if True, re-tune drums to match chord roots
    roll_speed:   beats per subdivision for rolls (default 0.125 = 32nd notes)
    """

    name: str = "Timpani"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        stroke_pattern: str = "single",
        drum_count: int = 4,
        tuning_follows: bool = True,
        roll_speed: float = 0.125,
    ) -> None:
        super().__init__(params)
        self.stroke_pattern = stroke_pattern
        self.drum_count = max(2, min(5, drum_count))
        self.tuning_follows = tuning_follows
        self.roll_speed = max(0.03125, roll_speed)
        self.params.key_range_low = max(self.params.key_range_low, TIMPANI_LOW)
        self.params.key_range_high = min(self.params.key_range_high, TIMPANI_HIGH)
        self._last_context: RenderContext | None = None
        self._drum_pitches: list[int] = self._initial_tuning()

    def _initial_tuning(self) -> list[int]:
        anchor = (TIMPANI_LOW + TIMPANI_HIGH) // 2
        pitches: list[int] = []
        for i in range(self.drum_count):
            offset = TYPICAL_PRIMARY[i] if i < len(TYPICAL_PRIMARY) else i * 3
            p = nearest_pitch(offset, anchor - (self.drum_count // 2 - i) * 5)
            p = max(TIMPANI_LOW, min(TIMPANI_HIGH, p))
            pitches.append(p)
        return sorted(pitches)

    def _retune(self, chord: ChordLabel, key: Scale) -> list[int]:
        pcs = chord.pitch_classes()
        if not pcs:
            return list(self._drum_pitches)

        root_pc = pcs[0]
        fifth_pc = (root_pc + 7) % 12
        core = [root_pc, fifth_pc]
        extra_pcs = [pc for pc in pcs if pc not in core]
        needed = core + extra_pcs[: self.drum_count - len(core)]

        anchor_low = TIMPANI_LOW + 2
        result: list[int] = []
        for i, pc in enumerate(needed[: self.drum_count]):
            p = nearest_pitch(pc, anchor_low + i * 5)
            p = snap_to_scale(p, key)
            p = max(TIMPANI_LOW, min(TIMPANI_HIGH, p))
            result.append(p)

        while len(result) < self.drum_count:
            pc = pcs[i % len(pcs)] if pcs else 0
            p = nearest_pitch(pc, anchor_low + len(result) * 5)
            p = max(TIMPANI_LOW, min(TIMPANI_HIGH, p))
            result.append(p)

        self._drum_pitches = sorted(result)
        return list(self._drum_pitches)

    def _pick_drum(self, target_pc: int, drums: list[int]) -> int:
        best = drums[0]
        best_dist = abs(best % 12 - target_pc % 12)
        best_dist = min(best_dist, 12 - best_dist)
        for d in drums[1:]:
            dist = abs(d % 12 - target_pc % 12)
            dist = min(dist, 12 - dist)
            if dist < best_dist:
                best = d
                best_dist = dist
        return best

    def _velocity(self, progress: float, accent: bool = False) -> int:
        if self.params.velocity_range:
            base = (self.params.velocity_range[0] + self.params.velocity_range[1]) // 2
        else:
            base = int(70 + self.params.density * 25)
        if accent:
            base = min(127, base + 15)
        return max(1, min(127, base + random.randint(-3, 3)))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        dispatch = {
            "single": self._render_single,
            "roll": self._render_roll,
            "fanfare": self._render_fanfare,
            "accented": self._render_accented,
        }
        render_fn = dispatch.get(self.stroke_pattern, self._render_single)
        notes = render_fn(chords, key, duration_beats)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )

        return notes

    def _render_single(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            drums = self._retune(chord, key) if self.tuning_follows else self._drum_pitches
            progress = elapsed / max(duration_beats, 1.0)

            root_pc = pcs[0]
            pitch = self._pick_drum(root_pc, drums)

            is_strong_beat = (int(chord.start) % 4 == 0)
            vel = self._velocity(progress, accent=is_strong_beat)

            if is_strong_beat and len(pcs) > 1:
                fifth_pc = pcs[min(2, len(pcs) - 1)]
                fifth_pitch = self._pick_drum(fifth_pc, drums)
                notes.append(NoteInfo(
                    pitch=fifth_pitch,
                    start=round(chord.start + chord.duration * 0.5, 6),
                    duration=max(0.1, chord.duration * 0.4),
                    velocity=max(1, vel - 8),
                ))

            notes.append(NoteInfo(
                pitch=pitch,
                start=round(chord.start, 6),
                duration=max(0.1, chord.duration * 0.85),
                velocity=vel,
            ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_roll(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            drums = self._retune(chord, key) if self.tuning_follows else self._drum_pitches
            root_pc = pcs[0]
            pitch = self._pick_drum(root_pc, drums)

            t = chord.start
            grain_idx = 0
            while t < chord.start + chord.duration:
                progress = elapsed / max(duration_beats, 1.0)
                frac = (t - chord.start) / max(chord.duration, 0.01)
                dynamic = math.sin(frac * math.pi) * 20
                vel = self._velocity(progress)
                vel = max(1, min(127, int(vel + dynamic + random.randint(-4, 4))))

                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=self.roll_speed * 0.8,
                    velocity=vel,
                ))
                t += self.roll_speed
                grain_idx += 1

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_fanfare(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            drums = self._retune(chord, key) if self.tuning_follows else self._drum_pitches
            progress = elapsed / max(duration_beats, 1.0)

            root_pc = pcs[0]
            fifth_pc = (root_pc + 7) % 12
            root_pitch = self._pick_drum(root_pc, drums)
            fifth_pitch = self._pick_drum(fifth_pc, drums)

            half = chord.duration / 2.0
            vel_root = self._velocity(progress, accent=True)
            vel_fifth = self._velocity(progress)

            notes.append(NoteInfo(
                pitch=root_pitch,
                start=round(chord.start, 6),
                duration=max(0.1, half * 0.85),
                velocity=vel_root,
            ))
            notes.append(NoteInfo(
                pitch=fifth_pitch,
                start=round(chord.start + half, 6),
                duration=max(0.1, half * 0.7),
                velocity=vel_fifth,
            ))

            if chord.duration >= 3.0:
                notes.append(NoteInfo(
                    pitch=root_pitch,
                    start=round(chord.start + half * 1.5, 6),
                    duration=max(0.1, half * 0.35),
                    velocity=max(1, vel_root - 5),
                ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_accented(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            drums = self._retune(chord, key) if self.tuning_follows else self._drum_pitches
            progress = elapsed / max(duration_beats, 1.0)

            root_pc = pcs[0]
            root_pitch = self._pick_drum(root_pc, drums)

            beat_1_onset = chord.start
            notes.append(NoteInfo(
                pitch=root_pitch,
                start=round(beat_1_onset, 6),
                duration=max(0.1, min(1.0, chord.duration * 0.5)),
                velocity=self._velocity(progress, accent=True),
            ))

            bar_start = int(chord.start) - int(chord.start) % 4
            if chord.duration >= 4.0:
                offbeat_positions = [bar_start + 2.5, bar_start + 3.0]
                for pos in offbeat_positions:
                    if chord.start <= pos < chord.start + chord.duration:
                        if random.random() < 0.4:
                            fifth_pc = pcs[min(2, len(pcs) - 1)]
                            fifth_pitch = self._pick_drum(fifth_pc, drums)
                            notes.append(NoteInfo(
                                pitch=fifth_pitch,
                                start=round(pos, 6),
                                duration=0.2,
                                velocity=self._velocity(progress),
                            ))
            elif chord.duration >= 2.0 and random.random() < 0.3:
                offbeat = chord.start + 1.0 + random.choice([0.0, 0.5])
                if offbeat < chord.start + chord.duration:
                    notes.append(NoteInfo(
                        pitch=root_pitch,
                        start=round(offbeat, 6),
                        duration=0.2,
                        velocity=self._velocity(progress),
                    ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Mallet Percussion Generator
# ---------------------------------------------------------------------------

class MalletPercussionGenerator(PhraseGenerator):
    """
    Orchestral mallet percussion: marimba, xylophone, vibraphone, glockenspiel.

    instrument: "marimba", "xylophone", "vibraphone", "glockenspiel"
    pattern:    "arpeggio", "run", "sustained", "tremolo", "glissando"
    mallet_count: 2-4 mallets (affects chord capacity)
    """

    name: str = "Mallet Percussion"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        instrument: str = "marimba",
        pattern: str = "arpeggio",
        mallet_count: int = 2,
    ) -> None:
        super().__init__(params)
        self.instrument = instrument
        self.pattern = pattern
        self.mallet_count = max(2, min(4, mallet_count))
        self._range = MALLET_RANGES.get(instrument, MALLET_RANGES["marimba"])
        self.params.key_range_low = max(self.params.key_range_low, self._range["low"])
        self.params.key_range_high = min(self.params.key_range_high, self._range["high"])
        self._last_context: RenderContext | None = None

    def _anchor(self) -> int:
        return (self._range["low"] + self._range["high"]) // 2

    def _base_velocity(self) -> int:
        r = self._range
        if self.params.velocity_range:
            return (self.params.velocity_range[0] + self.params.velocity_range[1]) // 2
        return r["vel_base"]

    def _velocity_jitter(self, vel: int) -> int:
        spread = self._range["vel_spread"]
        return max(1, min(127, vel + random.randint(-spread // 3, spread // 3)))

    def _resolve_pitch(self, pc: int, anchor: int, key: Scale) -> int:
        pitch = nearest_pitch(int(pc), anchor)
        pitch = snap_to_scale(pitch, key)
        return max(self._range["low"], min(self._range["high"], pitch))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        dispatch = {
            "arpeggio": self._render_arpeggio,
            "run": self._render_run,
            "sustained": self._render_sustained,
            "tremolo": self._render_tremolo,
            "glissando": self._render_glissando,
        }
        render_fn = dispatch.get(self.pattern, self._render_arpeggio)
        notes = render_fn(chords, key, duration_beats)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1],
            )

        return notes

    def _render_arpeggio(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        anchor = self._anchor()
        elapsed = 0.0
        vel = self._base_velocity()

        speed = max(0.125, 1.0 - self.params.density * 0.75)

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            usable = pcs[: self.mallet_count]
            t = chord.start
            idx = 0
            while t < chord.start + chord.duration:
                pc = usable[idx % len(usable)]
                octave_offset = (idx // len(usable)) * 12
                pitch = self._resolve_pitch(pc, anchor + octave_offset, key)

                note_vel = self._velocity_jitter(vel)
                note_dur = max(0.05, speed * 0.75)
                if self.instrument == "vibraphone":
                    note_dur = max(note_dur, speed * 1.5)

                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=note_dur,
                    velocity=note_vel,
                ))
                t += speed
                idx += 1

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_run(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        anchor = self._anchor()
        elapsed = 0.0
        vel = self._base_velocity()

        scale_pcs = [int(d) % 12 for d in key.degrees()]
        speed = max(0.125, 0.5 - self.params.density * 0.35)

        prev_pitch = anchor
        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            target_root = self._resolve_pitch(pcs[0], anchor, key)

            current = prev_pitch
            direction = 1 if target_root >= current else -1

            step_count = max(1, int(chord.duration / speed))
            actual_step = (target_root - current) / max(step_count, 1)

            t = chord.start
            for i in range(step_count):
                if direction > 0 and current >= target_root:
                    break
                if direction < 0 and current <= target_root:
                    break

                pc_approx = int(round(current)) % 12
                nearest_scale = min(scale_pcs, key=lambda s: abs(s - pc_approx))
                pitch = nearest_pitch(nearest_scale, int(round(current)))
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=max(0.05, speed * 0.6),
                    velocity=self._velocity_jitter(vel),
                ))
                current += direction if abs(actual_step) < 1 else actual_step
                t += speed

            prev_pitch = target_root
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_sustained(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        anchor = self._anchor()
        elapsed = 0.0
        vel = self._base_velocity()

        if self.instrument != "vibraphone":
            vel = max(1, vel - 10)

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            usable = pcs[: self.mallet_count]
            for pc in usable:
                pitch = self._resolve_pitch(pc, anchor, key)

                note_dur = chord.duration * 0.9 if self.instrument == "vibraphone" else max(0.1, chord.duration * 0.3)
                note_vel = self._velocity_jitter(vel)

                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(chord.start, 6),
                    duration=max(0.05, note_dur),
                    velocity=note_vel,
                ))

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_tremolo(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        anchor = self._anchor()
        elapsed = 0.0
        vel = self._base_velocity()

        grain = 0.125
        speed_mod = 0.8 if self.instrument == "vibraphone" else 1.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            target_pc = pcs[0]
            pitch = self._resolve_pitch(target_pc, anchor, key)

            t = chord.start
            while t < chord.start + chord.duration:
                frac = (t - chord.start) / max(chord.duration, 0.01)
                dynamic = math.sin(frac * math.pi) * 10
                note_vel = max(1, min(127, int(vel + dynamic + random.randint(-4, 4))))

                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=grain * speed_mod,
                    velocity=note_vel,
                ))
                t += grain

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes

    def _render_glissando(
        self, chords: list[ChordLabel], key: Scale, duration_beats: float,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        elapsed = 0.0
        vel = self._base_velocity()

        scale_pcs = [int(d) % 12 for d in key.degrees()]
        scale_set = set(scale_pcs)

        prev_root_pitch = self._range["low"] + 12

        for i, chord in enumerate(chords):
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            target_pitch = self._resolve_pitch(pcs[0], self._anchor(), key)

            start_pitch = prev_root_pitch if i > 0 else self._range["low"] + 12
            start_pitch = max(self._range["low"], start_pitch)

            if start_pitch == target_pitch:
                elapsed += chord.duration
                prev_root_pitch = target_pitch
                continue

            direction = 1 if target_pitch > start_pitch else -1

            sweep: list[int] = []
            p = start_pitch
            while (direction > 0 and p <= target_pitch) or (direction < 0 and p >= target_pitch):
                if p % 12 in scale_set:
                    sweep.append(p)
                p += direction
            if target_pitch not in sweep:
                sweep.append(target_pitch)
            sweep.sort(reverse=(direction < 0))

            if not sweep:
                elapsed += chord.duration
                prev_root_pitch = target_pitch
                continue

            step = chord.duration / max(len(sweep), 1)

            for j, pitch in enumerate(sweep):
                t = j / max(len(sweep) - 1, 1)
                dynamic = math.sin(t * math.pi) * 8
                note_vel = max(1, min(127, int(vel + dynamic + random.randint(-3, 3))))

                onset = chord.start + j * step
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=max(0.04, step * 0.9),
                    velocity=note_vel,
                ))

            prev_root_pitch = target_pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes
