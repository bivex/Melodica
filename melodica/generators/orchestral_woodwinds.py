# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_woodwinds.py -- Individual orchestral woodwind generators.

Flute, Oboe, Clarinet (Bb), Bassoon -- each with real instrument range,
register-aware voicing, multiple articulations, breath phrasing,
and dynamic curve support.

Layer: Application / Domain
Style: Classical, cinematic, film scoring, orchestral.
"""

from __future__ import annotations

import random
from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, snap_to_scale


# ---------------------------------------------------------------------------
# Instrument range definitions (MIDI pitches)
# ---------------------------------------------------------------------------

WOODWIND_RANGES = {
    "flute":    {"low": 60, "high": 96},   # C4--C7, bright, agile
    "oboe":     {"low": 58, "high": 91},   # Bb3--C6, reedy, expressive
    "clarinet": {"low": 50, "high": 91},   # D3--C6 (Bb clarinet), warm-dark to bright
    "bassoon":  {"low": 34, "high": 72},   # Bb1--C5, dark, reedy bass
}

BASS_CLARINET_RANGE = {"low": 38, "high": 79}   # D2--G4 (sounding)
COR_ANGLAIS_RANGE = {"low": 52, "high": 84}     # Eb3--C6 (sounding)

ARTICULATIONS = {
    "sustained":       {"dur_factor": 0.92, "vel_mod": 0,  "short": False},
    "legato":          {"dur_factor": 1.0,  "vel_mod": -5, "short": False},
    "staccato":        {"dur_factor": 0.25, "vel_mod": 10, "short": True},
    "flutter_tongue":  {"dur_factor": 0.92, "vel_mod": 3,  "short": False, "grain": 0.0625, "grain_dur": 0.05},
    "trill":           {"dur_factor": 0.92, "vel_mod": 5,  "short": False, "grain": 0.0625, "grain_dur": 0.05},
    "breath":          {"dur_factor": 0.5,  "vel_mod": 8,  "short": True},
}

_REGISTER_VEL_OFFSET = {
    1: -8,   # low: darker, softer
    2: 0,    # middle: standard
    3: 8,    # high: brighter, louder
}

# Dynamic curve shapes
_CURVE_FLAT = "flat"
_CURVE_CRESC = "crescendo"
_CURVE_DECRESC = "decrescendo"
_CURVE_SWELL = "swell"
_CURVE_DIM = "diminuendo"


def _apply_dynamic_curve(vel: int, progress: float, curve: str, base: int) -> int:
    if curve == _CURVE_CRESC:
        vel = int(base + progress * 30)
    elif curve == _CURVE_DECRESC:
        vel = int(base + (1.0 - progress) * 30)
    elif curve == _CURVE_SWELL:
        vel = int(base + 20 * (1.0 - abs(2.0 * progress - 1.0)))
    elif curve == _CURVE_DIM:
        vel = int(base + 15 * max(0, 1.0 - progress * 1.5))
    return max(1, min(127, vel))


def _breath_gap_interval(density: float) -> int:
    """Return how many beats between breath pauses, based on density."""
    if density < 0.3:
        return 8
    elif density < 0.6:
        return 6
    return 4


# ---------------------------------------------------------------------------
# Base class for orchestral woodwinds
# ---------------------------------------------------------------------------

class _OrchestralWoodwindBase(PhraseGenerator):
    """Base class shared by all orchestral woodwind generators."""

    def _setup_range(self) -> None:
        self._range = WOODWIND_RANGES.get(self.instrument, WOODWIND_RANGES["flute"])
        low = self._range["low"]
        high = self._range["high"]
        self.params.key_range_low = max(self.params.key_range_low, low)
        self.params.key_range_high = min(self.params.key_range_high, high)

    def _anchor(self) -> int:
        """Center of the instrument's comfortable range, adjusted by register."""
        mid = (self._range["low"] + self._range["high"]) // 2
        return mid + (self.register - 2) * 4

    def _velocity(self, progress: float) -> int:
        if self.params.velocity_range:
            base = (self.params.velocity_range[0] + self.params.velocity_range[1]) // 2
        else:
            base = int(60 + self.params.density * 30)

        base += _REGISTER_VEL_OFFSET.get(self.register, 0)
        return _apply_dynamic_curve(base, progress, self.dynamic_curve, base)

    def _resolve_pitch(self, pc: int, anchor: int, key: Scale) -> int:
        pitch = nearest_pitch(int(pc), anchor)
        pitch = snap_to_scale(pitch, key)
        return max(self._range["low"], min(self._range["high"], pitch))

    def _next_breath_boundary(self, breath_interval: int) -> float:
        if not hasattr(self, "_breath_clock"):
            self._breath_clock = 0.0
        return self._breath_clock + breath_interval


# ---------------------------------------------------------------------------
# Flute Generator
# ---------------------------------------------------------------------------

class FluteGenerator(_OrchestralWoodwindBase):
    """
    Solo flute -- C4--C7 range, bright and agile.

    articulation: sustained, legato, staccato, flutter_tongue, trill, breath
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    vibrato: true by default (flute has natural vibrato)
    register: 1-3 (low/middle/high)
    breath_phrase: automatically insert breath pauses
    """

    name: str = "Flute"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = True,
        register: int = 2,
        breath_phrase: bool = True,
    ) -> None:
        super().__init__(params)
        self.instrument = "flute"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.register = max(1, min(3, register))
        self.breath_phrase = breath_phrase
        self._last_context = None
        self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self._last_context = context
        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor
        breath_interval = _breath_gap_interval(self.params.density)
        self._breath_clock = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                self._breath_clock += chord.duration
                continue

            # Breath pause: skip this chord slot to create a short gap
            if self.breath_phrase and self._breath_clock >= breath_interval:
                self._breath_clock = 0.0
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"]

            # 70% chord tone, 30% scale tone
            if random.random() < 0.7 + self.params.complexity * 0.15:
                pc = random.choice(pcs)
            else:
                scale_pcs = [int(d) % 12 for d in key.degrees()]
                pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            # Stepwise smoothing -- avoid large jumps
            if abs(pitch - prev_pitch) > 7 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 3)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            onset = chord.start + random.uniform(0.0, 0.012)
            note_dur = chord.duration * art["dur_factor"]

            vel_final = vel + random.randint(-3, 3) if self.vibrato else vel
            vel_final = max(1, min(127, vel_final))

            if art.get("grain"):
                # Flutter tongue or trill -- subdivide into rapid notes
                gt = onset
                if self.articulation == "trill":
                    # Alternate between main pitch and upper neighbor
                    scale_pcs = [int(d) % 12 for d in key.degrees()]
                    upper_pc = (int(pitch) + 2) % 12
                    # Find nearest scale step above
                    for sp in scale_pcs:
                        if (sp % 12) > (int(pitch) % 12):
                            upper_pc = sp % 12
                            break
                    upper_pitch = nearest_pitch(upper_pc, pitch + 2)
                    upper_pitch = snap_to_scale(upper_pitch, key)
                    toggle = False
                    while gt < onset + note_dur:
                        t_pitch = upper_pitch if toggle else pitch
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=t_pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
                        toggle = not toggle
                else:
                    while gt < onset + note_dur:
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
            else:
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=max(0.05, note_dur),
                    velocity=vel_final,
                ))

            prev_pitch = pitch
            elapsed += chord.duration
            self._breath_clock += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Oboe Generator
# ---------------------------------------------------------------------------

class OboeGenerator(_OrchestralWoodwindBase):
    """
    Solo oboe -- Bb3--C6 range, reedy and expressive.

    articulation: sustained, legato, staccato, flutter_tongue, trill, breath
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    vibrato: true by default (oboe has expressive vibrato)
    register: 1-3 (low/middle/high)
    cor_anglais: switch to English horn range (Eb3--C6)
    """

    name: str = "Oboe"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = True,
        register: int = 2,
        breath_phrase: bool = True,
        cor_anglais: bool = False,
    ) -> None:
        super().__init__(params)
        self.instrument = "oboe"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.register = max(1, min(3, register))
        self.breath_phrase = breath_phrase
        self.cor_anglais = cor_anglais
        self._last_context = None
        if cor_anglais:
            self._range = COR_ANGLAIS_RANGE.copy()
            low = self._range["low"]
            high = self._range["high"]
            self.params.key_range_low = max(self.params.key_range_low, low)
            self.params.key_range_high = min(self.params.key_range_high, high)
        else:
            self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self._last_context = context
        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor
        breath_interval = _breath_gap_interval(self.params.density)
        self._breath_clock = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                self._breath_clock += chord.duration
                continue

            if self.breath_phrase and self._breath_clock >= breath_interval:
                self._breath_clock = 0.0
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"]

            # Oboe: slightly higher chord-tone bias (expressive melodic lines)
            if random.random() < 0.72 + self.params.complexity * 0.15:
                pc = random.choice(pcs)
            else:
                scale_pcs = [int(d) % 12 for d in key.degrees()]
                pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            if abs(pitch - prev_pitch) > 7 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 3)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            onset = chord.start + random.uniform(0.0, 0.012)
            note_dur = chord.duration * art["dur_factor"]

            # Oboe vibrato is more pronounced
            vel_final = vel + random.randint(-4, 4) if self.vibrato else vel
            vel_final = max(1, min(127, vel_final))

            if art.get("grain"):
                gt = onset
                if self.articulation == "trill":
                    scale_pcs = [int(d) % 12 for d in key.degrees()]
                    upper_pc = (int(pitch) + 2) % 12
                    for sp in scale_pcs:
                        if (sp % 12) > (int(pitch) % 12):
                            upper_pc = sp % 12
                            break
                    upper_pitch = nearest_pitch(upper_pc, pitch + 2)
                    upper_pitch = snap_to_scale(upper_pitch, key)
                    toggle = False
                    while gt < onset + note_dur:
                        t_pitch = upper_pitch if toggle else pitch
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=t_pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
                        toggle = not toggle
                else:
                    while gt < onset + note_dur:
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
            else:
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=max(0.05, note_dur),
                    velocity=vel_final,
                ))

            prev_pitch = pitch
            elapsed += chord.duration
            self._breath_clock += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Clarinet Generator
# ---------------------------------------------------------------------------

class ClarinetGenerator(_OrchestralWoodwindBase):
    """
    Solo Bb clarinet -- D3--C6 range, warm-dark to bright.

    articulation: sustained, legato, staccato, flutter_tongue, trill, breath
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    vibrato: false by default (clarinet typically plays without vibrato)
    register: 1-3 (low/chalumeau, middle, high/clarino)
    bass_voice: switch to bass clarinet range (D2--G4)
    """

    name: str = "Clarinet"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = False,
        register: int = 2,
        breath_phrase: bool = True,
        bass_voice: bool = False,
    ) -> None:
        super().__init__(params)
        self.instrument = "clarinet"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.register = max(1, min(3, register))
        self.breath_phrase = breath_phrase
        self.bass_voice = bass_voice
        self._last_context = None
        if bass_voice:
            self._range = BASS_CLARINET_RANGE.copy()
            low = self._range["low"]
            high = self._range["high"]
            self.params.key_range_low = max(self.params.key_range_low, low)
            self.params.key_range_high = min(self.params.key_range_high, high)
        else:
            self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self._last_context = context
        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor
        breath_interval = _breath_gap_interval(self.params.density)
        self._breath_clock = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                self._breath_clock += chord.duration
                continue

            if self.breath_phrase and self._breath_clock >= breath_interval:
                self._breath_clock = 0.0
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"]

            # Bass voice: prefer root, then fifth
            if self.bass_voice and pcs:
                pc = pcs[0]
                if random.random() < 0.3 and len(pcs) > 2:
                    pc = pcs[2] % 12
            elif random.random() < 0.7 + self.params.complexity * 0.15:
                pc = random.choice(pcs)
            else:
                scale_pcs = [int(d) % 12 for d in key.degrees()]
                pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            if abs(pitch - prev_pitch) > 7 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 3)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            onset = chord.start + random.uniform(0.0, 0.012)
            note_dur = chord.duration * art["dur_factor"]

            # Clarinet typically no vibrato, but slight velocity variation
            vel_final = vel + random.randint(-2, 2) if self.vibrato else vel
            vel_final = max(1, min(127, vel_final))

            if art.get("grain"):
                gt = onset
                if self.articulation == "trill":
                    scale_pcs = [int(d) % 12 for d in key.degrees()]
                    upper_pc = (int(pitch) + 2) % 12
                    for sp in scale_pcs:
                        if (sp % 12) > (int(pitch) % 12):
                            upper_pc = sp % 12
                            break
                    upper_pitch = nearest_pitch(upper_pc, pitch + 2)
                    upper_pitch = snap_to_scale(upper_pitch, key)
                    toggle = False
                    while gt < onset + note_dur:
                        t_pitch = upper_pitch if toggle else pitch
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=t_pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
                        toggle = not toggle
                else:
                    while gt < onset + note_dur:
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
            else:
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=max(0.05, note_dur),
                    velocity=vel_final,
                ))

            prev_pitch = pitch
            elapsed += chord.duration
            self._breath_clock += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Bassoon Generator
# ---------------------------------------------------------------------------

class BassoonGenerator(_OrchestralWoodwindBase):
    """
    Solo bassoon -- Bb1--C5 range, dark and reedy bass voice.

    articulation: sustained, legato, staccato, flutter_tongue, trill, breath
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    vibrato: false by default (bassoon vibrato is subtle)
    register: 1-3 (low/bass, middle/tenor, high)
    """

    name: str = "Bassoon"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = False,
        register: int = 1,
        breath_phrase: bool = True,
    ) -> None:
        super().__init__(params)
        self.instrument = "bassoon"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.register = max(1, min(3, register))
        self.breath_phrase = breath_phrase
        self._last_context = None
        self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self._last_context = context
        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor
        breath_interval = _breath_gap_interval(self.params.density)
        self._breath_clock = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                self._breath_clock += chord.duration
                continue

            if self.breath_phrase and self._breath_clock >= breath_interval:
                self._breath_clock = 0.0
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"]

            # Bassoon as bass voice: strongly prefer root/fifth
            if self.register == 1 and pcs:
                if random.random() < 0.65:
                    pc = pcs[0]
                elif len(pcs) > 2 and random.random() < 0.5:
                    pc = pcs[2] % 12
                else:
                    scale_pcs = [int(d) % 12 for d in key.degrees()]
                    pc = random.choice(scale_pcs)
            elif random.random() < 0.7 + self.params.complexity * 0.15:
                pc = random.choice(pcs)
            else:
                scale_pcs = [int(d) % 12 for d in key.degrees()]
                pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            if abs(pitch - prev_pitch) > 7 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 4)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            onset = chord.start + random.uniform(0.0, 0.012)
            note_dur = chord.duration * art["dur_factor"]

            vel_final = vel + random.randint(-2, 2) if self.vibrato else vel
            vel_final = max(1, min(127, vel_final))

            if art.get("grain"):
                gt = onset
                if self.articulation == "trill":
                    scale_pcs = [int(d) % 12 for d in key.degrees()]
                    upper_pc = (int(pitch) + 2) % 12
                    for sp in scale_pcs:
                        if (sp % 12) > (int(pitch) % 12):
                            upper_pc = sp % 12
                            break
                    upper_pitch = nearest_pitch(upper_pc, pitch + 2)
                    upper_pitch = snap_to_scale(upper_pitch, key)
                    toggle = False
                    while gt < onset + note_dur:
                        t_pitch = upper_pitch if toggle else pitch
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=t_pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
                        toggle = not toggle
                else:
                    while gt < onset + note_dur:
                        g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                        notes.append(NoteInfo(
                            pitch=pitch,
                            start=round(gt, 6),
                            duration=art.get("grain_dur", art["grain"] * 0.75),
                            velocity=g_vel,
                        ))
                        gt += art["grain"]
            else:
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=max(0.05, note_dur),
                    velocity=vel_final,
                ))

            prev_pitch = pitch
            elapsed += chord.duration
            self._breath_clock += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes
