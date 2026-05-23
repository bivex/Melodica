# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_strings.py — Individual orchestral string generators.

Violin, Viola, Cello, Contrabass — each with real instrument range,
register-aware voicing, multiple articulations, and position-based pitch logic.

Layer: Application / Domain
Style: Classical, cinematic, film scoring, orchestral.
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field
from typing import List

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


# ---------------------------------------------------------------------------
# Instrument range definitions (MIDI pitches)
# ---------------------------------------------------------------------------

STRING_RANGES = {
    "violin":     {"low": 55, "high": 96, "open": [55, 62, 69, 76]},   # G3–C7, open G-D-A-E
    "viola":      {"low": 48, "high": 84, "open": [48, 55, 62, 69]},   # C3–C6, open C-G-D-A
    "cello":      {"low": 36, "high": 72, "open": [36, 43, 50, 57]},   # C2–C5, open C-G-D-A
    "contrabass": {"low": 28, "high": 55, "open": [28, 33, 38, 43]},   # E1–G3, open E-A-D-G
}

ARTICULATIONS = {
    "sustained":  {"dur_factor": 0.92, "vel_mod": 0,   "short": False},
    "legato":     {"dur_factor": 1.0,  "vel_mod": -5,  "short": False},
    "staccato":   {"dur_factor": 0.2,  "vel_mod": 10,  "short": True},
    "spiccato":   {"dur_factor": 0.15, "vel_mod": 12,  "short": True},
    "pizzicato":  {"dur_factor": 0.12, "vel_mod": 8,   "short": True},
    "tremolo":    {"dur_factor": 0.92, "vel_mod": 3,   "short": False, "grain": 0.125},
    "col_legno":  {"dur_factor": 0.1,  "vel_mod": 5,   "short": True},
    "harmonic":   {"dur_factor": 0.85, "vel_mod": -10, "short": False},
}

# Dynamic curve shapes
_CURVE_FLAT = "flat"
_CURVE_CRESC = "crescendo"
_CURSE_DECRESC = "decrescendo"
_CURVE_SWELL = "swell"
_CURVE_DIM = "diminuendo"


def _apply_dynamic_curve(vel: int, progress: float, curve: str, base: int) -> int:
    if curve == _CURVE_CRESC:
        vel = int(base + progress * 30)
    elif curve == _CURSE_DECRESC:
        vel = int(base + (1.0 - progress) * 30)
    elif curve == _CURVE_SWELL:
        vel = int(base + 20 * (1.0 - abs(2.0 * progress - 1.0)))
    elif curve == _CURVE_DIM:
        vel = int(base + 15 * max(0, 1.0 - progress * 1.5))
    return max(1, min(127, vel))


def _prefer_open_string_pitch(target_pc: int, anchor: int, open_strings: list[int]) -> int:
    """If an open string matches the target pitch class near the anchor, prefer it."""
    best = anchor
    best_dist = abs(anchor - target_pc)
    for os_pitch in open_strings:
        candidate = os_pitch
        while candidate < anchor - 12:
            candidate += 12
        while candidate > anchor + 12:
            candidate -= 12
        dist = abs(candidate - anchor)
        pc_match = (candidate % 12) == (target_pc % 12)
        if pc_match and dist < best_dist + 3:
            best = candidate
            best_dist = dist
    return best


def _harmonic_pitch(base_pitch: int, harmonic_number: int = 2) -> int:
    """Natural harmonic: 2=octave, 3=fifth, 4=2octaves, 5=maj3rd."""
    if harmonic_number == 2:
        return base_pitch + 12
    elif harmonic_number == 3:
        return base_pitch + 19
    elif harmonic_number == 4:
        return base_pitch + 24
    elif harmonic_number == 5:
        return base_pitch + 28
    return base_pitch + 12


# ---------------------------------------------------------------------------
# Base class for orchestral strings
# ---------------------------------------------------------------------------

class _OrchestralStringBase(PhraseGenerator):
    """Base class shared by all orchestral string generators."""
    note_density: float = 1.0

    def _apply_note_density(self, chords: list[ChordLabel]) -> list[ChordLabel]:
        note_density = getattr(self, "note_density", 1.0)
        if not chords or note_density == 1.0:
            return chords
        
        if note_density <= 0.0:
            return []
        
        if note_density < 1.0:
            new_chords = []
            for i, chord in enumerate(chords):
                prev_val = int((i - 1) * note_density) if i > 0 else -1
                curr_val = int(i * note_density)
                if curr_val > prev_val:
                    new_chords.append(chord)
            return new_chords
        
        subdivisions = max(1, round(note_density))
        if subdivisions <= 1:
            return chords
            
        import dataclasses
        new_chords = []
        for chord in chords:
            sub_dur = chord.duration / subdivisions
            for s in range(subdivisions):
                new_chord = dataclasses.replace(
                    chord,
                    start=chord.start + s * sub_dur,
                    duration=sub_dur
                )
                new_chords.append(new_chord)
        return new_chords

    def _setup_range(self) -> None:
        self._range = STRING_RANGES.get(self.instrument, STRING_RANGES["violin"])
        low = self._range["low"]
        high = self._range["high"]
        self.params.key_range_low = max(self.params.key_range_low, low)
        self.params.key_range_high = min(self.params.key_range_high, high)

    def _anchor(self) -> int:
        """Center of the instrument's comfortable range, adjusted by position."""
        mid = (self._range["low"] + self._range["high"]) // 2
        return mid + (self.position - 1) * 2

    def _velocity(self, progress: float) -> int:
        if self.params.velocity_range:
            base = (self.params.velocity_range[0] + self.params.velocity_range[1]) // 2
        else:
            base = int(60 + self.params.density * 30)

        if self.con_sordino:
            base = int(base * 0.7)

        return _apply_dynamic_curve(base, progress, self.dynamic_curve, base)

    def _resolve_pitch(self, pc: int, anchor: int, key: Scale) -> int:
        pitch = nearest_pitch(int(pc), anchor)
        pitch = snap_to_scale(pitch, key)
        return max(self._range["low"], min(self._range["high"], pitch))


# ---------------------------------------------------------------------------
# Violin Generator
# ---------------------------------------------------------------------------

class ViolinGenerator(_OrchestralStringBase):
    """
    Solo violin with proper range (G3–C7), string-aware pitch selection,
    and full articulation support.

    articulation: sustained, legato, staccato, spiccato, pizzicato,
                  tremolo, col_legno, harmonic
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    position: 1–7 (higher position = higher register preference)
    """

    name: str = "Violin"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = True,
        con_sordino: bool = False,
        double_stops: bool = False,
        position: int = 1,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = "violin"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.con_sordino = con_sordino
        self.double_stops = double_stops
        self.position = max(1, min(7, position))
        self.note_density = note_density
        self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0

        prev_pitch = anchor
        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress)
            vel += art["vel_mod"]

            # Pick a pitch — chord-tone biased, with stepwise motion
            if random.random() < 0.7 + self.params.complexity * 0.2:
                pc = random.choice(pcs)
            else:
                scale_pcs = [int(d) % 12 for d in key.degrees()]
                pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            # Stepwise smoothing — avoid huge jumps
            if abs(pitch - prev_pitch) > 7 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 3)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            # Natural harmonic — shift pitch to harmonic node
            if self.articulation == "harmonic":
                harm_pitch = _harmonic_pitch(pitch, random.choice([2, 3, 4]))
                if self._range["low"] <= harm_pitch <= self._range["high"]:
                    pitch = harm_pitch

            onset = chord.start + random.uniform(0.0, 0.015)
            note_dur = chord.duration * art["dur_factor"]

            # Vibrato velocity shimmer
            vel_final = vel + random.randint(-3, 3) if self.vibrato else vel
            vel_final = max(1, min(127, vel_final))

            if art.get("grain"):
                # Tremolo
                gt = onset
                while gt < onset + note_dur:
                    g_vel = max(1, min(127, vel_final + random.randint(-4, 4)))
                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(gt, 6),
                        duration=art["grain"] * 0.8,
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

            # Double stops — add a second voice at consonant interval
            if self.double_stops and len(pcs) > 1:
                second_pc = pcs[1] if pcs[0] == pc else pcs[0]
                second_pitch = self._resolve_pitch(second_pc, pitch - 5, key)
                if abs(second_pitch - pitch) >= 2:
                    notes.append(NoteInfo(
                        pitch=second_pitch,
                        start=round(onset, 6),
                        duration=max(0.05, note_dur),
                        velocity=max(1, vel_final - 8),
                    ))

            prev_pitch = pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Viola Generator
# ---------------------------------------------------------------------------

class ViolaGenerator(_OrchestralStringBase):
    """
    Solo viola — C3–C6 range, darker tone, alto voice in the section.

    Same articulations as violin. Defaults to slightly lower velocity
    to reflect the alto blend role.
    """

    name: str = "Viola"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = True,
        con_sordino: bool = False,
        double_stops: bool = False,
        position: int = 1,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = "viola"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.con_sordino = con_sordino
        self.double_stops = double_stops
        self.position = max(1, min(5, position))
        self.note_density = note_density
        self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"] - 3  # slightly softer blend

            pc = random.choice(pcs)
            pitch = self._resolve_pitch(pc, prev_pitch, key)

            if abs(pitch - prev_pitch) > 9 and self.params.leap_probability < 0.4:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 3)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            if self.articulation == "harmonic":
                harm_pitch = _harmonic_pitch(pitch, random.choice([2, 3]))
                if self._range["low"] <= harm_pitch <= self._range["high"]:
                    pitch = harm_pitch

            onset = chord.start + random.uniform(0.0, 0.015)
            note_dur = chord.duration * art["dur_factor"]
            vel_final = max(1, min(127, vel + (random.randint(-2, 2) if self.vibrato else 0)))

            if art.get("grain"):
                gt = onset
                while gt < onset + note_dur:
                    g_vel = max(1, min(127, vel_final + random.randint(-3, 3)))
                    notes.append(NoteInfo(pitch=pitch, start=round(gt, 6),
                                         duration=art["grain"] * 0.8, velocity=g_vel))
                    gt += art["grain"]
            else:
                notes.append(NoteInfo(pitch=pitch, start=round(onset, 6),
                                      duration=max(0.05, note_dur), velocity=vel_final))

            if self.double_stops and len(pcs) > 1:
                second_pc = pcs[1] if pcs[0] == pc else pcs[0]
                second_pitch = self._resolve_pitch(second_pc, pitch - 5, key)
                if abs(second_pitch - pitch) >= 2:
                    notes.append(NoteInfo(pitch=second_pitch, start=round(onset, 6),
                                          duration=max(0.05, note_dur),
                                          velocity=max(1, vel_final - 6)))

            prev_pitch = pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Cello Generator
# ---------------------------------------------------------------------------

class CelloGenerator(_OrchestralStringBase):
    """
    Solo cello — C2–C5 range. Tenor/bass voice, lyrical solos,
    bass line support, and rich sustained tone.

    Bass-aware: when used as bass voice, prefers root/fifth of chord.
    """

    name: str = "Cello"
    bass_voice: bool = False

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = True,
        con_sordino: bool = False,
        double_stops: bool = False,
        position: int = 1,
        bass_voice: bool = False,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = "cello"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.con_sordino = con_sordino
        self.double_stops = double_stops
        self.position = max(1, min(5, position))
        self.bass_voice = bass_voice
        self.note_density = note_density
        self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"]

            # Bass voice: strongly prefer root, then fifth
            if self.bass_voice and pcs:
                pc = pcs[0]  # root
                if random.random() < 0.3 and len(pcs) > 2:
                    pc = pcs[2] % 12  # fifth approximation
            else:
                if random.random() < 0.65 + self.params.complexity * 0.2:
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

            if self.articulation == "harmonic":
                harm_pitch = _harmonic_pitch(pitch, random.choice([2, 3]))
                if self._range["low"] <= harm_pitch <= self._range["high"]:
                    pitch = harm_pitch

            onset = chord.start + random.uniform(0.0, 0.015)
            note_dur = chord.duration * art["dur_factor"]
            vel_final = max(1, min(127, vel + (random.randint(-2, 2) if self.vibrato else 0)))

            if art.get("grain"):
                gt = onset
                while gt < onset + note_dur:
                    g_vel = max(1, min(127, vel_final + random.randint(-3, 3)))
                    notes.append(NoteInfo(pitch=pitch, start=round(gt, 6),
                                         duration=art["grain"] * 0.8, velocity=g_vel))
                    gt += art["grain"]
            else:
                notes.append(NoteInfo(pitch=pitch, start=round(onset, 6),
                                      duration=max(0.05, note_dur), velocity=vel_final))

            if self.double_stops and len(pcs) > 1:
                second_pc = pcs[-1]  # lowest chord tone for bass pairing
                second_pitch = self._resolve_pitch(second_pc, pitch - 7, key)
                if abs(second_pitch - pitch) >= 3:
                    notes.append(NoteInfo(pitch=second_pitch, start=round(onset, 6),
                                          duration=max(0.05, note_dur),
                                          velocity=max(1, vel_final - 5)))

            prev_pitch = pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes


# ---------------------------------------------------------------------------
# Contrabass Generator
# ---------------------------------------------------------------------------

class ContrabassGenerator(_OrchestralStringBase):
    """
    Double bass / contrabass — E1–G3 range (written pitch, sounds octave lower).

    Primarily bass line function. Supports:
    - sustained, pizzicato (most common), staccato, legato
    - bass_voice mode (always locked to root/fifth)
    - walking bass patterns when density > 0.5
    """

    name: str = "Contrabass"
    bass_voice: bool = True

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        vibrato: bool = False,
        con_sordino: bool = False,
        position: int = 1,
        bass_voice: bool = True,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = "contrabass"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.vibrato = vibrato
        self.con_sordino = con_sordino
        self.double_stops = False
        self.position = max(1, min(4, position))
        self.bass_voice = bass_voice
        self.note_density = note_density
        self._setup_range()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        notes: list[NoteInfo] = []
        art = ARTICULATIONS.get(self.articulation, ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        prev_pitch = anchor

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress) + art["vel_mod"]

            # Walking bass: subdivide chord duration into beat-level movement
            if self.params.density > 0.5 and chord.duration >= 2.0:
                beats_in_chord = int(chord.duration)
                for beat_idx in range(beats_in_chord):
                    if beat_idx == 0:
                        pc = pcs[0]  # root on beat 1
                    elif beat_idx == 2 and len(pcs) > 2:
                        pc = pcs[2] % 12  # fifth on beat 3
                    elif beat_idx % 2 == 1:
                        # Passing tone on weak beats
                        scale_pcs = [int(d) % 12 for d in key.degrees()]
                        pc = random.choice(scale_pcs)
                    else:
                        pc = random.choice(pcs)

                    pitch = self._resolve_pitch(pc, prev_pitch, key)
                    onset = chord.start + beat_idx
                    beat_vel = max(1, min(127, vel + (5 if beat_idx % 2 == 0 else -3)))

                    notes.append(NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=max(0.05, 0.9 * art["dur_factor"]),
                        velocity=beat_vel,
                    ))
                    prev_pitch = pitch
            else:
                # Simple: one note per chord, root or fifth
                if self.bass_voice:
                    pc = pcs[0]
                    if random.random() < 0.25 and len(pcs) > 2:
                        pc = pcs[2] % 12
                else:
                    pc = random.choice(pcs)

                pitch = self._resolve_pitch(pc, prev_pitch, key)
                onset = chord.start + random.uniform(0.0, 0.01)
                note_dur = chord.duration * art["dur_factor"]
                vel_final = max(1, min(127, vel))

                if art.get("grain"):
                    gt = onset
                    while gt < onset + note_dur:
                        g_vel = max(1, min(127, vel_final + random.randint(-2, 2)))
                        notes.append(NoteInfo(pitch=pitch, start=round(gt, 6),
                                             duration=art["grain"] * 0.8, velocity=g_vel))
                        gt += art["grain"]
                else:
                    notes.append(NoteInfo(pitch=pitch, start=round(onset, 6),
                                         duration=max(0.05, note_dur), velocity=vel_final))

                prev_pitch = pitch

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)
        return notes
