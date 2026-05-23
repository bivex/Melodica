# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/orchestral_brass.py — Individual orchestral brass generators.

Trumpet, Trombone, French Horn — each with real instrument range,
register-aware voicing, multiple articulations, and brass-specific features
including fanfare mode, rip passages, con sordino, and breath pauses.

Layer: Application / Domain
Style: Classical, cinematic, film scoring, orchestral.
"""

from __future__ import annotations

import random
from typing import List

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


# ---------------------------------------------------------------------------
# Instrument range definitions (MIDI pitches)
# ---------------------------------------------------------------------------

BRASS_RANGES = {
    "trumpet":     {"low": 55, "high": 82},   # A3–Bb5
    "trombone":    {"low": 40, "high": 70},   # E2–Bb4
    "bass_trombone": {"low": 36, "high": 66}, # C2–F#4 (4 semitones lower)
    "french_horn": {"low": 34, "high": 70},   # Bb1–Bb4
}

BRASS_ARTICULATIONS = {
    "sustained":  {"dur_factor": 0.90, "vel_mod": 0,   "short": False},
    "staccato":   {"dur_factor": 0.2,  "vel_mod": 10,  "short": True},
    "legato":     {"dur_factor": 1.0,  "vel_mod": -5,  "short": False},
    "muted":      {"dur_factor": 0.85, "vel_mod": -15, "short": False},
    "swell":      {"dur_factor": 0.90, "vel_mod": 0,   "short": False},
    "fanfare":    {"dur_factor": 0.70, "vel_mod": 5,   "short": False},
    "rip":        {"dur_factor": 0.15, "vel_mod": 8,   "short": True},
}

# Dynamic curve shapes
_CURVE_FLAT = "flat"
_CURVE_CRESC = "crescendo"
_CURVE_DECRESC = "decrescendo"
_CURVE_SWELL = "swell"
_CURVE_DIM = "diminuendo"

# Register velocity offsets (low=warmer/softer, high=brilliant/louder)
_REGISTER_VEL_OFFSET = {
    1: -8,   # low register: warm, round
    2: 0,    # middle register: balanced
    3: 10,   # high register: brilliant, powerful
}


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


# ---------------------------------------------------------------------------
# Base class for orchestral brass
# ---------------------------------------------------------------------------

class _OrchestralBrassBase(PhraseGenerator):
    """Base class shared by all orchestral brass generators."""
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
        self._range = BRASS_RANGES.get(self.instrument, BRASS_RANGES["trumpet"])
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

        # Register-aware velocity
        base += _REGISTER_VEL_OFFSET.get(self.register, 0)

        # Con sordino reduces volume significantly
        if self.con_sordino:
            base = int(base * 0.7)

        return _apply_dynamic_curve(base, progress, self.dynamic_curve, base)

    def _resolve_pitch(self, pc: int, anchor: int, key: Scale) -> int:
        pitch = nearest_pitch(int(pc), anchor)
        pitch = snap_to_scale(pitch, key)
        return max(self._range["low"], min(self._range["high"], pitch))

    def _needs_breath(self, elapsed_in_phrase: float, vel: int) -> bool:
        """Brass instruments need breath pauses. Higher intensity = more frequent."""
        breath_interval = max(2.0, 6.0 - (vel / 127.0) * 4.0)
        return elapsed_in_phrase >= breath_interval

    def _generate_rip(
        self,
        target_pitch: int,
        onset: float,
        key: Scale,
        prev_pitch: int,
    ) -> list[NoteInfo]:
        """Generate 3-5 rapid ascending scale notes leading to target pitch."""
        rip_notes: list[NoteInfo] = []
        num_notes = random.randint(3, 5)
        scale_pcs = [int(d) % 12 for d in key.degrees()]

        # Start from below the target
        start_pitch = max(
            self._range["low"],
            target_pitch - random.randint(5, 9),
        )
        start_pitch = snap_to_scale(start_pitch, key)

        direction = 1 if target_pitch > prev_pitch else -1
        current_pitch = start_pitch
        total_span = abs(target_pitch - start_pitch)
        step = max(1, total_span // num_notes) if total_span > 0 else 1

        rip_dur = 0.08  # Fast rip notes
        for i in range(num_notes):
            current_pitch = snap_to_scale(current_pitch, key)
            current_pitch = max(self._range["low"], min(self._range["high"], current_pitch))
            vel = int(70 + i * 8)
            rip_notes.append(NoteInfo(
                pitch=current_pitch,
                start=round(onset + i * rip_dur, 6),
                duration=rip_dur * 0.7,
                velocity=max(1, min(127, vel)),
            ))
            current_pitch += direction * step

        return rip_notes

    def _generate_fanfare(
        self,
        chord: ChordLabel,
        onset: float,
        key: Scale,
        prev_pitch: int,
        base_vel: int,
    ) -> list[NoteInfo]:
        """Generate ascending arpeggiated pattern on chord tones (root-3rd-5th-octave)."""
        fanfare_notes: list[NoteInfo] = []
        pcs = chord.pitch_classes()
        if not pcs:
            return fanfare_notes

        # Build ascending arpeggio from chord tones
        arpeggio_pcs = []
        if len(pcs) >= 1:
            arpeggio_pcs.append(pcs[0])          # root
        if len(pcs) >= 2:
            arpeggio_pcs.append(pcs[1])          # third
        if len(pcs) >= 3:
            arpeggio_pcs.append(pcs[2])          # fifth
        # Add octave
        arpeggio_pcs.append((pcs[0] + 12) % 12)

        note_dur = chord.duration / max(len(arpeggio_pcs), 1)
        current_pitch = prev_pitch

        for i, pc in enumerate(arpeggio_pcs):
            pitch = self._resolve_pitch(pc, current_pitch, key)
            # Fanfare should ascend — if not ascending, push upward
            if i > 0 and pitch <= current_pitch:
                pitch = snap_to_scale(current_pitch + random.randint(2, 5), key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            vel = min(127, base_vel + i * 8)
            fanfare_notes.append(NoteInfo(
                pitch=pitch,
                start=round(onset + i * note_dur, 6),
                duration=max(0.05, note_dur * 0.85),
                velocity=max(1, min(127, vel)),
            ))
            current_pitch = pitch

        return fanfare_notes


# ---------------------------------------------------------------------------
# Trumpet Generator
# ---------------------------------------------------------------------------

class TrumpetGenerator(_OrchestralBrassBase):
    """
    Solo trumpet (Bb) — A3–Bb5 range. Brilliant and powerful in upper register.

    articulation: sustained, staccato, legato, muted, swell, fanfare, rip
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    con_sordino: muted brass (straight mute), softer and more nasal
    register: 1–3 (low/middle/high, affects velocity and tone)
    fanfare_mode: generates ascending arpeggiated patterns instead of sustained
    """

    name: str = "Trumpet"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        con_sordino: bool = False,
        register: int = 2,
        fanfare_mode: bool = False,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = "trumpet"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.con_sordino = con_sordino
        self.register = max(1, min(3, register))
        self.fanfare_mode = fanfare_mode
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
        art = BRASS_ARTICULATIONS.get(self.articulation, BRASS_ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        breath_elapsed = 0.0
        prev_pitch = anchor
        self._last_context = None

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                breath_elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress)
            vel += art["vel_mod"]

            # Breath pause: brass needs breath every 4-6 beats at high intensity
            if breath_elapsed > 0 and self._needs_breath(breath_elapsed, vel):
                breath_elapsed = 0.0
                elapsed += chord.duration
                continue
            breath_elapsed += chord.duration

            # Fanfare mode: ascending arpeggiated pattern
            if self.fanfare_mode:
                fanfare_notes = self._generate_fanfare(
                    chord, chord.start, key, prev_pitch, vel,
                )
                notes.extend(fanfare_notes)
                if fanfare_notes:
                    prev_pitch = fanfare_notes[-1].pitch
                elapsed += chord.duration
                continue

            # Rip articulation: rapid ascending scalar passage into target
            if self.articulation == "rip":
                # Pick target pitch (chord tone)
                pc = pcs[0]
                target = self._resolve_pitch(pc, anchor, key)
                rip_notes = self._generate_rip(target, chord.start, key, prev_pitch)
                notes.extend(rip_notes)
                # Main target note
                notes.append(NoteInfo(
                    pitch=target,
                    start=round(chord.start + len(rip_notes) * 0.08, 6),
                    duration=max(0.05, chord.duration * 0.5),
                    velocity=max(1, min(127, vel + 5)),
                ))
                prev_pitch = target
                elapsed += chord.duration
                continue

            # Strong chord-tone bias (80% chord tones — brass is very chordal)
            if random.random() < 0.80:
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

            onset = chord.start + random.uniform(0.0, 0.01)
            note_dur = chord.duration * art["dur_factor"]
            vel_final = max(1, min(127, vel + random.randint(-3, 3)))

            notes.append(NoteInfo(
                pitch=pitch,
                start=round(onset, 6),
                duration=max(0.05, note_dur),
                velocity=vel_final,
            ))

            prev_pitch = pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )

        return notes


# ---------------------------------------------------------------------------
# Trombone Generator
# ---------------------------------------------------------------------------

class TromboneGenerator(_OrchestralBrassBase):
    """
    Solo trombone — E2–Bb4 range. Rich, powerful, slide instrument.
    Bass trombone mode shifts range down 4 semitones.

    articulation: sustained, staccato, legato, muted, swell, fanfare, rip
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    con_sordino: muted brass, softer tone
    register: 1–3 (low/middle/high)
    fanfare_mode: generates ascending arpeggiated patterns
    bass_voice: when True, preferentially plays bass trombone range (lower by 4 semitones)
    """

    name: str = "Trombone"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        con_sordino: bool = False,
        register: int = 2,
        fanfare_mode: bool = False,
        bass_voice: bool = False,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.bass_voice = bass_voice
        self.instrument = "bass_trombone" if bass_voice else "trombone"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.con_sordino = con_sordino
        self.register = max(1, min(3, register))
        self.fanfare_mode = fanfare_mode
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
        art = BRASS_ARTICULATIONS.get(self.articulation, BRASS_ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        breath_elapsed = 0.0
        prev_pitch = anchor
        self._last_context = None

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                breath_elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress)
            vel += art["vel_mod"]

            # Breath pause
            if breath_elapsed > 0 and self._needs_breath(breath_elapsed, vel):
                breath_elapsed = 0.0
                elapsed += chord.duration
                continue
            breath_elapsed += chord.duration

            # Fanfare mode
            if self.fanfare_mode:
                fanfare_notes = self._generate_fanfare(
                    chord, chord.start, key, prev_pitch, vel,
                )
                notes.extend(fanfare_notes)
                if fanfare_notes:
                    prev_pitch = fanfare_notes[-1].pitch
                elapsed += chord.duration
                continue

            # Rip articulation
            if self.articulation == "rip":
                pc = pcs[0]
                target = self._resolve_pitch(pc, anchor, key)
                rip_notes = self._generate_rip(target, chord.start, key, prev_pitch)
                notes.extend(rip_notes)
                notes.append(NoteInfo(
                    pitch=target,
                    start=round(chord.start + len(rip_notes) * 0.08, 6),
                    duration=max(0.05, chord.duration * 0.5),
                    velocity=max(1, min(127, vel + 5)),
                ))
                prev_pitch = target
                elapsed += chord.duration
                continue

            # Bass voice: strongly prefer root and fifth
            if self.bass_voice and pcs:
                pc = pcs[0]  # root
                if random.random() < 0.3 and len(pcs) > 2:
                    pc = pcs[2] % 12  # fifth
            else:
                # Strong chord-tone bias
                if random.random() < 0.80:
                    pc = random.choice(pcs)
                else:
                    scale_pcs = [int(d) % 12 for d in key.degrees()]
                    pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            # Trombone slide: allow slightly wider intervals than trumpet
            if abs(pitch - prev_pitch) > 9 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 4)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            onset = chord.start + random.uniform(0.0, 0.01)
            note_dur = chord.duration * art["dur_factor"]
            vel_final = max(1, min(127, vel + random.randint(-3, 3)))

            notes.append(NoteInfo(
                pitch=pitch,
                start=round(onset, 6),
                duration=max(0.05, note_dur),
                velocity=vel_final,
            ))

            prev_pitch = pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )

        return notes


# ---------------------------------------------------------------------------
# French Horn Generator
# ---------------------------------------------------------------------------

class FrenchHornGenerator(_OrchestralBrassBase):
    """
    Solo French horn — Bb1–Bb4 range. Warm, mellow tone, wide range.

    articulation: sustained, staccato, legato, muted, swell, fanfare, rip
    dynamic_curve: flat, crescendo, decrescendo, swell, diminuendo
    con_sordino: hand-muted horn, softer and more covered tone
    register: 1–3 (low/middle/high)
    fanfare_mode: generates ascending arpeggiated patterns
    """

    name: str = "French Horn"

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "sustained",
        dynamic_curve: str = "flat",
        con_sordino: bool = False,
        register: int = 2,
        fanfare_mode: bool = False,
        note_density: float = 1.0,
    ) -> None:
        super().__init__(params)
        self.instrument = "french_horn"
        self.articulation = articulation
        self.dynamic_curve = dynamic_curve
        self.con_sordino = con_sordino
        self.register = max(1, min(3, register))
        self.fanfare_mode = fanfare_mode
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
        art = BRASS_ARTICULATIONS.get(self.articulation, BRASS_ARTICULATIONS["sustained"])
        anchor = self._anchor()
        elapsed = 0.0
        breath_elapsed = 0.0
        prev_pitch = anchor
        self._last_context = None

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                elapsed += chord.duration
                breath_elapsed += chord.duration
                continue

            progress = elapsed / max(duration_beats, 1.0)
            vel = self._velocity(progress)
            vel += art["vel_mod"]

            # French horn is naturally softer — reduce base velocity slightly
            vel = max(1, vel - 5)

            # Breath pause
            if breath_elapsed > 0 and self._needs_breath(breath_elapsed, vel):
                breath_elapsed = 0.0
                elapsed += chord.duration
                continue
            breath_elapsed += chord.duration

            # Fanfare mode
            if self.fanfare_mode:
                fanfare_notes = self._generate_fanfare(
                    chord, chord.start, key, prev_pitch, vel,
                )
                notes.extend(fanfare_notes)
                if fanfare_notes:
                    prev_pitch = fanfare_notes[-1].pitch
                elapsed += chord.duration
                continue

            # Rip articulation
            if self.articulation == "rip":
                pc = pcs[0]
                target = self._resolve_pitch(pc, anchor, key)
                rip_notes = self._generate_rip(target, chord.start, key, prev_pitch)
                notes.extend(rip_notes)
                notes.append(NoteInfo(
                    pitch=target,
                    start=round(chord.start + len(rip_notes) * 0.08, 6),
                    duration=max(0.05, chord.duration * 0.5),
                    velocity=max(1, min(127, vel + 5)),
                ))
                prev_pitch = target
                elapsed += chord.duration
                continue

            # Strong chord-tone bias
            if random.random() < 0.80:
                pc = random.choice(pcs)
            else:
                scale_pcs = [int(d) % 12 for d in key.degrees()]
                pc = random.choice(scale_pcs)

            pitch = self._resolve_pitch(pc, prev_pitch, key)

            # Stepwise smoothing
            if abs(pitch - prev_pitch) > 7 and self.params.leap_probability < 0.5:
                direction = 1 if pitch > prev_pitch else -1
                pitch = prev_pitch + direction * random.randint(1, 3)
                pitch = snap_to_scale(pitch, key)
                pitch = max(self._range["low"], min(self._range["high"], pitch))

            onset = chord.start + random.uniform(0.0, 0.01)
            note_dur = chord.duration * art["dur_factor"]
            vel_final = max(1, min(127, vel + random.randint(-2, 2)))

            notes.append(NoteInfo(
                pitch=pitch,
                start=round(onset, 6),
                duration=max(0.05, note_dur),
                velocity=vel_final,
            ))

            prev_pitch = pitch
            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )

        return notes
