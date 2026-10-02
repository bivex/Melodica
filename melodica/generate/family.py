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
from melodica.utils import chord_pitches_closed, nearest_pitch, snap_to_scale


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


@dataclass(frozen=True)
class _PluckedRenderContext:
    """Parameter object encapsulating rendering context per chord slice for plucked instruments."""
    chord: ChordLabel
    pcs: tuple[int, ...]
    key: Scale
    low: int
    high: int
    mid: int
    prev_pitch: int


class PluckedFamily(FamilyGenerator):
    """
    Universal plucked and percussive solo instrument family generator.
    Serves Grand/Bright/Electric Pianos, Harpsichord, Clavinet, Acoustic/Electric Guitars,
    Sitar, Koto, and Kalimba.
    """

    name: str = "Plucked Family Generator"

    def __init__(
        self,
        profile: InstrumentProfile | str = "grand_piano",
        params: GeneratorParams | None = None,
        *,
        style: str | None = None,
        pedal: bool | None = None,
        acoustic_type: str | None = None,
        pop_intensity: float | None = None,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(profile, params, note_density=note_density)
        self.style = style or self.profile.default_pattern or "fingerpicking"
        self.pedal = self.profile.sustain_pedal if pedal is None else pedal
        self.acoustic_type = acoustic_type or self.profile.id
        self.pop_intensity = (
            max(0.0, min(1.0, pop_intensity))
            if pop_intensity is not None
            else float(self.profile.features.get("pop_intensity", 0.5))
        )

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
        prev_pitch = mid

        notes: list[NoteInfo] = []
        is_keyboard = self.profile.gm_program <= 7
        is_guitar = 24 <= self.profile.gm_program <= 31

        for chord in filtered_chords:
            pcs = tuple(chord.pitch_classes())
            if not pcs:
                continue
            ctx = _PluckedRenderContext(chord, pcs, key, low, high, mid, prev_pitch)
            if is_keyboard:
                prev_pitch = self._render_keyboard_slice(ctx, notes)
            elif is_guitar:
                prev_pitch = self._render_guitar_slice(ctx, notes)
            else:
                prev_pitch = self._render_ethnic_slice(ctx, notes)

        return sorted(notes, key=lambda x: x.start)

    def _get_keyboard_dur_mult(self, inst: str) -> float:
        mult_map: dict[str, float] = {
            "harpsichord": 0.4,
            "clavinet": 0.6,
            "bright_piano": 1.5 if self.pedal else 0.85,
            "electric_grand": 1.3 if self.pedal else 0.8,
            "honky_tonk": 1.6 if self.pedal else 0.9,
            "electric_piano_2": 2.0 if self.pedal else 1.1,
            "electric_piano_1": 1.8 if self.pedal else 0.95,
            "electric_piano": 1.8 if self.pedal else 0.95,
        }
        return mult_map.get(inst, 1.8 if self.pedal else 0.9)

    def _render_keyboard_slice(self, ctx: _PluckedRenderContext, notes: list[NoteInfo]) -> int:
        pc = random.choice(ctx.pcs) if random.random() < 0.8 else random.choice([int(d) % 12 for d in ctx.key.degrees()])
        pitch = nearest_pitch(pc, ctx.prev_pitch)
        pitch = snap_to_scale(pitch, ctx.key)
        pitch = max(ctx.low, min(ctx.high, pitch))

        inst = self.profile.id
        vel = self._velocity(self.profile.base_velocity)
        dur_mult = self._get_keyboard_dur_mult(inst)
        duration = max(0.1, ctx.chord.duration * dur_mult)

        expression: dict[int, list[tuple[float, int]]] = {}
        if inst in ("harpsichord", "clavinet"):
            duration = min(duration, 0.4 if inst == "harpsichord" else 0.6)
        elif inst in ("electric_piano", "electric_piano_1"):
            expression[11] = [(0.0, 70), (duration * 0.5, 95), (duration, 60)]
        elif inst == "electric_piano_2":
            expression[93] = [(0.0, 105), (duration, 105)]
            expression[11] = [(0.0, 80), (duration * 0.25, 95), (duration * 0.5, 80), (duration * 0.75, 95), (duration, 80)]
        elif inst == "electric_grand":
            expression[93] = [(0.0, 80), (duration, 80)]
            expression[11] = [(0.0, 75), (duration * 0.5, 90), (duration, 70)]
        elif inst == "honky_tonk":
            expression[93] = [(0.0, 95), (duration, 95)]

        note = NoteInfo(
            pitch=pitch,
            start=round(ctx.chord.start, 6),
            duration=round(duration, 6),
            velocity=vel,
        )
        if expression:
            note.expression = expression
        notes.append(note)

        if inst == "honky_tonk":
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(ctx.chord.start + random.uniform(0.01, 0.025), 6),
                duration=round(duration * 0.8, 6),
                velocity=max(1, int(vel * 0.75)),
            ))

        if random.random() < 0.5:
            bass_pitch = max(36, nearest_pitch(ctx.pcs[0], ctx.mid - 12))
            notes.append(NoteInfo(
                pitch=bass_pitch,
                start=round(ctx.chord.start, 6),
                duration=round(duration * 0.7, 6),
                velocity=max(1, vel - 15),
            ))

        return pitch

    def _render_guitar_slice(self, ctx: _PluckedRenderContext, notes: list[NoteInfo]) -> int:
        ac_type = self.acoustic_type or self.profile.id
        is_rock = ac_type in ("overdriven", "distortion", "overdriven_guitar", "distortion_guitar")
        is_harmonics = ac_type in ("harmonics", "guitar_harmonics")

        if self.style == "fingerpicking" and not is_rock and not is_harmonics and len(ctx.pcs) >= 3:
            return self._render_guitar_fingerpicking(ctx, notes)
        return self._render_guitar_lead(ctx, notes)

    def _render_guitar_fingerpicking(self, ctx: _PluckedRenderContext, notes: list[NoteInfo]) -> int:
        vel = self._velocity(75)
        notes.append(NoteInfo(
            pitch=max(40, nearest_pitch(ctx.pcs[0], ctx.mid - 8)),
            start=round(ctx.chord.start, 6),
            duration=round(ctx.chord.duration * 0.95, 6),
            velocity=vel,
        ))
        sub_dur = ctx.chord.duration / 3.0
        p_high = ctx.prev_pitch
        for s in range(1, 3):
            p_idx = s % len(ctx.pcs)
            p_high = max(52, nearest_pitch(ctx.pcs[p_idx], ctx.mid + 6))
            notes.append(NoteInfo(
                pitch=p_high,
                start=round(ctx.chord.start + s * sub_dur, 6),
                duration=round(sub_dur * 0.9, 6),
                velocity=max(1, vel - 8),
            ))
        return p_high

    def _render_guitar_lead(self, ctx: _PluckedRenderContext, notes: list[NoteInfo]) -> int:
        ac_type = self.acoustic_type or self.profile.id
        vel = self._velocity(self.profile.base_velocity)
        pc = random.choice(ctx.pcs)
        pitch = nearest_pitch(pc, ctx.prev_pitch)
        pitch = snap_to_scale(pitch, ctx.key)
        pitch = max(ctx.low, min(ctx.high, pitch))

        if "harmonics" in ac_type:
            pitch = max(ctx.low, min(ctx.high, pitch + 12))
            dur = ctx.chord.duration * 0.35
        elif "muted" in ac_type:
            dur = ctx.chord.duration * 0.15
        else:
            dur = ctx.chord.duration * 0.85

        expr = self._build_guitar_expression(ac_type, dur)
        note = NoteInfo(
            pitch=pitch,
            start=round(ctx.chord.start, 6),
            duration=round(dur, 6),
            velocity=vel,
        )
        if expr:
            note.expression = expr
        notes.append(note)

        if ("overdriven" in ac_type or "distortion" in ac_type) and ctx.pcs:
            self._add_power_chords(ctx, note, notes)

        return pitch

    def _build_guitar_expression(self, ac_type: str, dur: float) -> dict[int, list[tuple[float, int]]]:
        expr: dict[int, list[tuple[float, int]]] = {}
        if "overdriven" in ac_type or "distortion" in ac_type:
            expr[1] = [(0.0, 70), (dur * 0.5, 95), (dur, 75)]
            if "distortion" in ac_type:
                expr[93] = [(0.0, 85), (dur, 85)]
        return expr

    def _add_power_chords(
        self,
        ctx: _PluckedRenderContext,
        root_note: NoteInfo,
        notes: list[NoteInfo],
    ) -> None:
        p5 = max(ctx.low, min(ctx.high, root_note.pitch + 7))
        p8 = max(ctx.low, min(ctx.high, root_note.pitch + 12))
        for p in (p5, p8):
            n = NoteInfo(
                pitch=p,
                start=round(ctx.chord.start, 6),
                duration=root_note.duration,
                velocity=max(1, root_note.velocity - 10),
            )
            if root_note.expression:
                n.expression = dict(root_note.expression)
            notes.append(n)

    def _render_ethnic_slice(self, ctx: _PluckedRenderContext, notes: list[NoteInfo]) -> int:
        pc = random.choice(ctx.pcs)
        pitch = nearest_pitch(pc, ctx.prev_pitch)
        pitch = snap_to_scale(pitch, ctx.key)
        pitch = max(ctx.low, min(ctx.high, pitch))

        inst = self.profile.id
        vel = self._velocity(self.profile.base_velocity)
        dur = ctx.chord.duration * self.profile.sustain_factor

        expression: dict[int, list[tuple[float, int]]] = {}
        if "sitar" in inst:
            expression[12] = [(0.0, 64), (dur * 0.3, 90), (dur * 0.7, 50), (dur, 64)]
        elif "koto" in inst:
            notes.append(NoteInfo(
                pitch=pitch,
                start=round(ctx.chord.start + 0.08, 6),
                duration=round(dur * 0.4, 6),
                velocity=max(1, vel - 12),
            ))
            dur = dur * 0.3
        elif "kalimba" in inst:
            dur = min(ctx.chord.duration * 0.7, 0.22)
            if self.pop_intensity > 0 and random.random() < 0.7:
                harmonic = random.choice([12, 19])
                pop_pitch = pitch + harmonic
                if pop_pitch <= ctx.high:
                    notes.append(NoteInfo(
                        pitch=pop_pitch,
                        start=round(ctx.chord.start + 0.002, 6),
                        duration=0.06,
                        velocity=max(5, int(vel * self.pop_intensity * 0.5)),
                    ))

        note = NoteInfo(
            pitch=pitch,
            start=round(ctx.chord.start, 6),
            duration=round(dur, 6),
            velocity=vel,
        )
        if expression:
            note.expression = expression
        notes.append(note)

        return pitch


@dataclass(frozen=True)
class _WindBrassRenderContext:
    """Parameter object encapsulating rendering context per chord slice for winds & brass."""
    chord: ChordLabel
    pcs: tuple[int, ...]
    key: Scale
    low: int
    high: int
    mid: int
    prev_pitch: int


class WindBrassFamily(FamilyGenerator):
    """
    Universal solo wind and brass family generator.
    Serves Muted Trumpet, Synth Brass 1 & 2, Woodwinds (Piccolo, Recorder, Pan Flute,
    Blown Bottle, Shakuhachi, Whistle, Ocarina), Flugelhorn, English Horn, Bass Clarinet,
    Euphonium, and Alto Flute.
    """

    name: str = "Wind & Brass Family Generator"

    def __init__(
        self,
        profile: InstrumentProfile | str = "muted_trumpet",
        params: GeneratorParams | None = None,
        *,
        brass_type: str | None = None,
        instrument: str | None = None,
        plunger_wah: bool = True,
        breath_vibrato: bool = True,
        vibrato: bool = True,
        harmony_count: int = 3,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(profile, params, note_density=note_density)
        self.brass_type = brass_type or self.profile.id
        self.instrument = instrument or self.profile.id
        self.plunger_wah = plunger_wah
        self.breath_vibrato = breath_vibrato
        self.vibrato = vibrato
        self.harmony_count = max(2, min(4, harmony_count))

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
        prev_pitch = mid

        notes: list[NoteInfo] = []
        inst_id = self.profile.id

        for chord in filtered_chords:
            pcs = tuple(chord.pitch_classes())
            if not pcs:
                continue
            ctx = _WindBrassRenderContext(chord, pcs, key, low, high, mid, prev_pitch)
            if "synth_brass" in inst_id or self.brass_type in ("synth_brass_1", "synth_brass_2"):
                prev_pitch = self._render_synth_brass_slice(ctx, notes)
            elif "muted_trumpet" in inst_id:
                prev_pitch = self._render_muted_trumpet_slice(ctx, notes)
            elif inst_id in ("piccolo", "recorder", "pan_flute", "blown_bottle", "shakuhachi", "whistle", "ocarina"):
                prev_pitch = self._render_woodwind_slice(ctx, notes)
            else:
                prev_pitch = self._render_lyrical_slice(ctx, notes)

        return sorted(notes, key=lambda x: x.start)

    def _render_synth_brass_slice(self, ctx: _WindBrassRenderContext, notes: list[NoteInfo]) -> int:
        voicing = chord_pitches_closed(ctx.chord, ctx.mid)[: self.harmony_count]
        dur = ctx.chord.duration * self.profile.sustain_factor
        expression: dict[int, list[tuple[float, int]]] = {}
        if self.brass_type == "synth_brass_1" or self.profile.id == "synth_brass_1":
            expression[74] = [(0.0, 110), (dur * 0.15, 60), (dur * 0.6, 75), (dur, 50)]
            vel = self._velocity(self.profile.base_velocity)
        else:
            expression[74] = [(0.0, 75), (dur * 0.3, 90), (dur, 65)]
            expression[93] = [(0.0, 100), (dur, 100)]
            vel = self._velocity(self.profile.base_velocity)

        last_pitch = ctx.prev_pitch
        for p in voicing:
            p = max(ctx.low, min(ctx.high, p))
            p = snap_to_scale(p, ctx.key)
            last_pitch = p
            note = NoteInfo(
                pitch=p,
                start=round(ctx.chord.start, 6),
                duration=round(dur, 6),
                velocity=vel,
            )
            if expression:
                note.expression = expression
            notes.append(note)
        return last_pitch

    def _render_muted_trumpet_slice(self, ctx: _WindBrassRenderContext, notes: list[NoteInfo]) -> int:
        pc = random.choice(ctx.pcs)
        pitch = nearest_pitch(pc, ctx.prev_pitch)
        pitch = snap_to_scale(pitch, ctx.key)
        pitch = max(ctx.low, min(ctx.high, pitch))

        vel = self._velocity(self.profile.base_velocity)
        dur = ctx.chord.duration * self.profile.sustain_factor
        expression: dict[int, list[tuple[float, int]]] = {}
        if self.plunger_wah:
            expression[74] = [(0.0, 40), (dur * 0.25, 95), (dur * 0.5, 55), (dur * 0.75, 95), (dur, 60)]
            expression[11] = [(0.0, 60), (dur * 0.3, 90), (dur * 0.7, 75), (dur, 50)]

        note = NoteInfo(
            pitch=pitch,
            start=round(ctx.chord.start, 6),
            duration=round(dur, 6),
            velocity=vel,
        )
        if expression:
            note.expression = expression
        notes.append(note)
        return pitch

    def _render_woodwind_slice(self, ctx: _WindBrassRenderContext, notes: list[NoteInfo]) -> int:
        pc = random.choice(ctx.pcs)
        pitch = nearest_pitch(pc, ctx.prev_pitch)
        pitch = snap_to_scale(pitch, ctx.key)
        pitch = max(ctx.low, min(ctx.high, pitch))

        inst = self.instrument or self.profile.id
        vel = self._velocity(self.profile.base_velocity)
        dur = ctx.chord.duration * self.profile.sustain_factor

        expression: dict[int, list[tuple[float, int]]] = {}
        if self.breath_vibrato:
            depth = 18 if inst == "shakuhachi" else 8
            speed = 4.5 if inst == "shakuhachi" else 6.0
            expression[11] = generate_lfo_cc(dur, speed, base=80, depth=depth, step=0.05)

        note = NoteInfo(
            pitch=pitch,
            start=round(ctx.chord.start, 6),
            duration=round(dur, 6),
            velocity=vel,
        )
        if expression:
            note.expression = expression
        notes.append(note)

        if inst in ("whistle", "piccolo") and random.random() < 0.4:
            grace_pitch = max(ctx.low, min(ctx.high, pitch + 2))
            notes.append(NoteInfo(
                pitch=snap_to_scale(grace_pitch, ctx.key),
                start=round(ctx.chord.start, 6),
                duration=0.08,
                velocity=max(1, vel - 15),
            ))
        elif inst == "pan_flute" and random.random() < 0.5:
            puff_pitch = max(ctx.low, min(ctx.high, pitch + 12))
            notes.append(NoteInfo(
                pitch=snap_to_scale(puff_pitch, ctx.key),
                start=round(ctx.chord.start, 6),
                duration=0.05,
                velocity=max(1, vel + 15),
            ))

        return pitch

    def _render_lyrical_slice(self, ctx: _WindBrassRenderContext, notes: list[NoteInfo]) -> int:
        pc = random.choice(ctx.pcs)
        pitch = nearest_pitch(pc, ctx.prev_pitch)
        pitch = snap_to_scale(pitch, ctx.key)
        pitch = max(ctx.low, min(ctx.high, pitch))

        inst = self.profile.id
        vel = self._velocity(self.profile.base_velocity)
        dur = ctx.chord.duration * self.profile.sustain_factor

        expression: dict[int, list[tuple[float, int]]] = {}
        if inst == "flugelhorn" and self.breath_vibrato:
            expression[11] = generate_lfo_cc(dur, 5.0, base=82, depth=8, step=0.06)
        elif inst == "english_horn" and self.vibrato:
            expression[1] = generate_lfo_cc(dur, 4.5, base=40, depth=20, step=0.08)
        elif inst == "alto_flute" and self.breath_vibrato:
            expression[11] = generate_lfo_cc(dur, 5.5, base=80, depth=8, step=0.06)
        elif inst == "bass_clarinet":
            expression[11] = [(0.0, 50), (dur * 0.2, 85), (dur * 0.8, 80), (dur, 30)]
        elif inst == "euphonium":
            expression[11] = [(0.0, 40), (dur * 0.25, 95), (dur * 0.8, 80), (dur, 40)]

        note = NoteInfo(
            pitch=pitch,
            start=round(ctx.chord.start, 6),
            duration=round(dur, 6),
            velocity=vel,
        )
        if expression:
            note.expression = expression
        notes.append(note)
        return pitch
