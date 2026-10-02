# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.generate.family — Parameterized family generators.

Layer 2 of the architecture: a single family generator class services an entire instrument family
(e.g. MalletFamily handles Celesta, Glockenspiel, Vibraphone, Marimba, Xylophone, Music Box, Dulcimer),
parameterized by an InstrumentProfile (Layer 1 data) and powered by kernel functions.
"""

from __future__ import annotations

import math
import random
from abc import ABC
from dataclasses import dataclass
from typing import Callable, Sequence

from melodica.generate.kernel import (
    apply_note_density,
    generate_lfo_cc,
    resolve_bounded_pitch,
)
from melodica.generate.profile import InstrumentProfile, get_profile
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


@dataclass(frozen=True)
class _MalletRenderContext:
    """Parameter object encapsulating rendering context per chord slice."""
    chord: ChordLabel
    pcs: tuple[int, ...]
    key: Scale
    low: int
    high: int
    mid: int
    dur_mult: float


class FamilyGenerator(PhraseGenerator, ABC):
    """
    Abstract base for instrument family generators.
    Bound to an InstrumentProfile and uses shared kernel logic.
    """

    profile: InstrumentProfile
    note_density: float = 1.0

    def __init__(
        self,
        profile: InstrumentProfile | str,
        params: GeneratorParams | None = None,
        *,
        note_density: float = 1.0,
    ) -> None:
        if isinstance(profile, str):
            profile = get_profile(profile)
        super().__init__(params)
        self.profile = profile
        self.note_density = note_density

        # Clamp generator range to instrument physical profile boundaries
        self.params.key_range_low = max(self.params.key_range_low, self.profile.range_low)
        self.params.key_range_high = min(self.params.key_range_high, self.profile.range_high)

    def _apply_note_density(self, chords: Sequence[ChordLabel]) -> list[ChordLabel]:
        return apply_note_density(chords, self.note_density)

    def _resolve_pitch(self, pc: int, anchor: int, key: Scale, low: int, high: int) -> int:
        return resolve_bounded_pitch(pc, anchor, key, low, high)

    def _velocity(self, base_val: int, jitter: int | None = None) -> int:
        if self.params.velocity_range:
            v_min, v_max = self.params.velocity_range
            return random.randint(v_min, v_max)
        jit = jitter if jitter is not None else self.profile.velocity_jitter
        return max(1, min(127, base_val + random.randint(-jit, jit)))


class MalletFamily(FamilyGenerator):
    """
    Universal chromatic and mallet percussion family generator.
    Serves Celesta, Glockenspiel, Music Box, Vibraphone, Marimba, Xylophone, and Dulcimer.
    """

    name: str = "Mallet Family Generator"

    def __init__(
        self,
        profile: InstrumentProfile | str = "vibraphone",
        params: GeneratorParams | None = None,
        *,
        pattern: str | None = None,
        pedal: bool | None = None,
        motor_speed_hz: float | None = None,
        mallets: int | None = None,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(profile, params, note_density=note_density)
        self.pattern = pattern or self.profile.default_pattern
        self.pedal = self.profile.sustain_pedal if pedal is None else pedal
        self.motor_speed_hz = motor_speed_hz or float(
            self.profile.features.get("motor_vibrato", {}).get("speed_hz", 6.0)
        )
        self.mallets = mallets or int(self.profile.defaults.get("mallets", self.profile.max_polyphony))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        filtered_chords = self._apply_note_density(chords)
        if not filtered_chords:
            return []

        low = max(self.profile.range_low, self.params.key_range_low)
        high = min(self.profile.range_high, self.params.key_range_high)
        mid = (low + high) // 2
        dur_mult = 1.6 if self.pedal else 0.8

        handler = self._get_pattern_handler(self.pattern)
        notes: list[NoteInfo] = []
        for chord in filtered_chords:
            pcs = tuple(chord.pitch_classes())
            if not pcs:
                continue
            ctx = _MalletRenderContext(chord, pcs, key, low, high, mid, dur_mult)
            handler(ctx, notes)

        return sorted(notes, key=lambda x: x.start)

    def _get_pattern_handler(self, pattern: str) -> Callable[[_MalletRenderContext, list[NoteInfo]], None]:
        handlers: dict[str, Callable[[_MalletRenderContext, list[NoteInfo]], None]] = {
            "dreamy_arpeggio": self._render_dreamy_arpeggio,
            "sparkling_chords": self._render_sparkling_chords,
            "melodic_accent": self._render_melodic_accent,
            "sparkling_run": self._render_sparkling_run,
            "clockwork_ostinato": self._render_clockwork_ostinato,
            "gentle_melody": self._render_gentle_melody,
            "warm_chords": self._render_warm_chords,
            "motor_arpeggio": self._render_motor_arpeggio,
            "rolling_tremolo": self._render_rolling_tremolo,
            "woody_arpeggio": self._render_woody_arpeggio,
            "dry_staccato_run": self._render_dry_staccato_run,
            "skeletal_accents": self._render_skeletal_accents,
            "hammered_roll": self._render_hammered_roll,
            "rapid_arpeggio": self._render_rapid_arpeggio,
        }
        return handlers.get(pattern, self._render_default_arpeggio)

    def _render_dreamy_arpeggio(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        if len(ctx.pcs) < 2:
            self._render_default_arpeggio(ctx, notes)
            return
        sub_dur = ctx.chord.duration / len(ctx.pcs)
        for i, pc in enumerate(ctx.pcs):
            pitch = self._resolve_pitch(pc, ctx.mid + (i - len(ctx.pcs) // 2) * 4, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + i * sub_dur, 6),
                    duration=round(max(0.1, sub_dur * ctx.dur_mult), 6),
                    velocity=self._velocity(self.profile.base_velocity),
                )
            )

    def _render_sparkling_chords(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        for pc in ctx.pcs[: min(3, self.profile.max_polyphony)]:
            pitch = self._resolve_pitch(pc, ctx.mid + 12, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start, 6),
                    duration=round(max(0.1, ctx.chord.duration * ctx.dur_mult), 6),
                    velocity=self._velocity(self.profile.base_velocity + 3),
                )
            )

    def _render_melodic_accent(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        pitch = self._resolve_pitch(ctx.pcs[0], ctx.mid + 12, ctx.key, ctx.low, ctx.high)
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(ctx.chord.start, 6),
                duration=0.6,
                velocity=self._velocity(self.profile.base_velocity),
            )
        )

    def _render_sparkling_run(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        sub_dur = ctx.chord.duration / 4.0
        for s in range(4):
            pc = ctx.pcs[s % len(ctx.pcs)]
            pitch = self._resolve_pitch(pc, ctx.mid + 12 + s * 2, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * sub_dur, 6),
                    duration=0.3,
                    velocity=self._velocity(self.profile.base_velocity - 6),
                )
            )

    def _render_clockwork_ostinato(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        sub_dur = 0.5
        steps = max(1, int(ctx.chord.duration / sub_dur))
        for s in range(steps):
            pc = ctx.pcs[s % len(ctx.pcs)]
            octave = (s // len(ctx.pcs)) * 12
            pitch = self._resolve_pitch(pc, ctx.mid + octave, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * sub_dur, 6),
                    duration=0.35,
                    velocity=self._velocity(self.profile.base_velocity),
                )
            )

    def _render_gentle_melody(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        pc = random.choice(ctx.pcs)
        pitch = self._resolve_pitch(pc, ctx.mid + 6, ctx.key, ctx.low, ctx.high)
        notes.append(
            NoteInfo(
                pitch=pitch,
                start=round(ctx.chord.start, 6),
                duration=0.4,
                velocity=self._velocity(self.profile.base_velocity),
            )
        )

    def _render_warm_chords(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        chord_dur = ctx.chord.duration * self.profile.sustain_factor
        for pc in ctx.pcs[: self.profile.max_polyphony]:
            pitch = self._resolve_pitch(pc, ctx.mid, ctx.key, ctx.low, ctx.high)
            expression: dict[int, list[tuple[float, int]]] = {}
            if self.motor_speed_hz:
                expression[11] = generate_lfo_cc(
                    chord_dur,
                    self.motor_speed_hz,
                    base=85,
                    depth=15,
                    step=0.05,
                )
            if self.pedal:
                expression[64] = [(0.0, 0), (0.04, 127)]
            note = NoteInfo(
                pitch=pitch,
                start=round(ctx.chord.start, 6),
                duration=round(chord_dur, 6),
                velocity=self._velocity(self.profile.base_velocity),
            )
            if expression:
                note.expression = expression
            notes.append(note)

    def _render_motor_arpeggio(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        sub_dur = ctx.chord.duration / 3.0
        for s in range(3):
            pc = ctx.pcs[s % len(ctx.pcs)]
            pitch = self._resolve_pitch(pc, ctx.mid, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * sub_dur, 6),
                    duration=round(sub_dur * 1.5, 6),
                    velocity=self._velocity(self.profile.base_velocity + 4),
                )
            )

    def _render_rolling_tremolo(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        roll_speed = 0.125
        steps = max(1, int(ctx.chord.duration / roll_speed))
        for s in range(steps):
            pc = ctx.pcs[s % min(len(ctx.pcs), 2)]
            pitch = self._resolve_pitch(pc, ctx.mid, ctx.key, ctx.low, ctx.high)
            t_frac = s / max(1, steps - 1)
            swell = int(math.sin(t_frac * math.pi) * 12)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * roll_speed, 6),
                    duration=roll_speed * 0.95,
                    velocity=max(1, min(127, self._velocity(self.profile.base_velocity - 8) + swell)),
                )
            )

    def _render_woody_arpeggio(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        num_mallets = max(2, min(4, self.mallets))
        sub_dur = ctx.chord.duration / num_mallets
        for s in range(num_mallets):
            pc = ctx.pcs[s % len(ctx.pcs)]
            pitch = self._resolve_pitch(pc, ctx.mid - 6 + s * 4, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * sub_dur, 6),
                    duration=0.22,
                    velocity=self._velocity(self.profile.base_velocity),
                )
            )

    def _render_dry_staccato_run(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        sub_dur = 0.25
        steps = max(1, int(ctx.chord.duration / sub_dur))
        for s in range(steps):
            pc = ctx.pcs[s % len(ctx.pcs)]
            pitch = self._resolve_pitch(pc, ctx.mid + (s % 3) * 3, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * sub_dur, 6),
                    duration=0.12,
                    velocity=self._velocity(self.profile.base_velocity),
                )
            )

    def _render_skeletal_accents(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        for i, pc in enumerate(ctx.pcs[:2]):
            pitch = self._resolve_pitch(pc, ctx.mid + i * 7, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start, 6),
                    duration=0.15,
                    velocity=self._velocity(self.profile.base_velocity + 6),
                )
            )

    def _render_hammered_roll(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        bounce_speed = 0.125
        steps = max(1, int(ctx.chord.duration / bounce_speed))
        for s in range(steps):
            pc = ctx.pcs[s % len(ctx.pcs)]
            pitch = self._resolve_pitch(pc, ctx.mid, ctx.key, ctx.low, ctx.high)
            vel_mod = 12 if s % 2 == 0 else -12
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * bounce_speed, 6),
                    duration=0.25,
                    velocity=max(1, min(127, self._velocity(self.profile.base_velocity - 4) + vel_mod)),
                )
            )

    def _render_rapid_arpeggio(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        sub_dur = ctx.chord.duration / 3.0
        for s in range(3):
            pc = ctx.pcs[s % len(ctx.pcs)]
            pitch = self._resolve_pitch(pc, ctx.mid + 6, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + s * sub_dur, 6),
                    duration=round(sub_dur * 1.6, 6),
                    velocity=self._velocity(self.profile.base_velocity),
                )
            )

    def _render_default_arpeggio(self, ctx: _MalletRenderContext, notes: list[NoteInfo]) -> None:
        sub_dur = ctx.chord.duration / max(1, len(ctx.pcs))
        for i, pc in enumerate(ctx.pcs):
            pitch = self._resolve_pitch(pc, ctx.mid, ctx.key, ctx.low, ctx.high)
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(ctx.chord.start + i * sub_dur, 6),
                    duration=round(sub_dur * 0.9, 6),
                    velocity=self._velocity(self.profile.base_velocity),
                )
            )
