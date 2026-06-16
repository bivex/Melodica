"""generators/canon.py — Imitative counterpoint: canon generator.

Generates 2–4 canonic voices from a single melody.  Each follower voice
enters after a configurable beat delay and is transposed by a configurable
interval (default: fifth above = +7 semitones).

Supported canon types:
  canon_at_octave   — follower at +12 or -12 semitones
  canon_at_fifth    — follower at +7 semitones (classical default)
  canon_at_unison   — same pitch, different time entry
  crab_canon        — dux forward, comes backward (retrograde)
  inversion_canon   — dux forward, comes inverted (diatonic mirror)
  augmentation_canon — comes at 2× note durations

Usage
-----
    from melodica.types import Scale, Mode, NoteInfo
    from melodica.generators.canon import CanonGenerator

    melody = [NoteInfo(pitch=60+i, start=float(i), duration=1.0) for i in range(8)]
    gen = CanonGenerator(delay_beats=4.0, interval_semitones=7, n_voices=2)
    voices = gen.generate(melody, scale=Scale(0, Mode.MAJOR))
    # voices[0] = dux (original), voices[1] = comes (follower)
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass, field
from typing import Literal

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.types import Scale, Mode, ChordLabel, NoteInfo
from melodica.render_context import RenderContext
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


# ---------------------------------------------------------------------------
# Interval helpers
# ---------------------------------------------------------------------------

def _scale_degrees(scale: Scale) -> list[int]:
    """Return the pitch-class set for a scale (sorted)."""
    INTERVALS: dict[Mode, list[int]] = {
        Mode.MAJOR:         [0, 2, 4, 5, 7, 9, 11],
        Mode.NATURAL_MINOR: [0, 2, 3, 5, 7, 8, 10],
        Mode.HARMONIC_MINOR:[0, 2, 3, 5, 7, 8, 11],
        Mode.DORIAN:        [0, 2, 3, 5, 7, 9, 10],
        Mode.PHRYGIAN:      [0, 1, 3, 5, 7, 8, 10],
        Mode.LYDIAN:        [0, 2, 4, 6, 7, 9, 11],
        Mode.MIXOLYDIAN:    [0, 2, 4, 5, 7, 9, 10],
        Mode.LOCRIAN:       [0, 1, 3, 5, 6, 8, 10],
    }
    intervals = INTERVALS.get(scale.mode, INTERVALS[Mode.MAJOR])
    return [(scale.root + i) % 12 for i in intervals]


def _nearest_scale_pitch(pitch: int, scale_pcs: list[int]) -> int:
    """Snap a chromatic pitch to the nearest scale pitch-class, same octave."""
    octave = pitch // 12
    pc = pitch % 12
    best_pc = min(scale_pcs, key=lambda sp: min(abs(sp - pc), 12 - abs(sp - pc)))
    return octave * 12 + best_pc


def _diatonic_inversion(notes: list[NoteInfo], scale: Scale) -> list[NoteInfo]:
    """Mirror intervals around the first note, staying diatonic."""
    if not notes:
        return []
    pcs = _scale_degrees(scale)
    pivot = notes[0].pitch

    result: list[NoteInfo] = []
    for note in notes:
        interval = note.pitch - pivot
        inverted_raw = pivot - interval
        inverted_snapped = _nearest_scale_pitch(max(0, min(127, inverted_raw)), pcs)
        n = copy.copy(note)
        n.pitch = inverted_snapped
        result.append(n)
    return result


# ---------------------------------------------------------------------------
# Transform functions
# ---------------------------------------------------------------------------

def _shift_time(notes: list[NoteInfo], offset: float) -> list[NoteInfo]:
    result = []
    for n in notes:
        c = copy.copy(n)
        c.start = n.start + offset
        result.append(c)
    return result


def _transpose(notes: list[NoteInfo], semitones: int) -> list[NoteInfo]:
    result = []
    for n in notes:
        c = copy.copy(n)
        c.pitch = max(0, min(127, n.pitch + semitones))
        result.append(c)
    return result


def _retrograde(notes: list[NoteInfo]) -> list[NoteInfo]:
    """Reverse note order, preserving total duration and relative timing."""
    if not notes:
        return []
    total_end = max(n.start + n.duration for n in notes)
    result = []
    for n in reversed(notes):
        c = copy.copy(n)
        c.start = total_end - (n.start + n.duration)
        result.append(c)
    return sorted(result, key=lambda x: x.start)


def _augment(notes: list[NoteInfo], factor: float = 2.0) -> list[NoteInfo]:
    result = []
    for n in notes:
        c = copy.copy(n)
        c.start    = n.start * factor
        c.duration = n.duration * factor
        result.append(c)
    return result


def _diminish(notes: list[NoteInfo], factor: float = 2.0) -> list[NoteInfo]:
    return _augment(notes, 1.0 / factor)


def _scale_velocity(notes: list[NoteInfo], factor: float) -> list[NoteInfo]:
    result = []
    for n in notes:
        c = copy.copy(n)
        c.velocity = max(1, min(127, int(n.velocity * factor)))
        result.append(c)
    return result


# ---------------------------------------------------------------------------
# CanonGenerator
# ---------------------------------------------------------------------------

CanonType = Literal[
    "fifth", "octave", "unison",
    "crab", "inversion", "augmentation", "diminution",
]


@dataclass
class CanonGenerator(PhraseGenerator):
    """Generate imitative counterpoint (canon) voices from a dux melody.

    Parameters
    ----------
    delay_beats : float
        How many beats after the dux each comes voice enters.
    interval_semitones : int
        Transposition of comes voices in semitones.
        Ignored for 'crab', 'inversion', 'augmentation', 'diminution'.
    n_voices : int
        Total number of voices including the dux (2–4).
    canon_type : CanonType
        Transformation applied to follower voices.
    velocity_decay : float
        Velocity scaling per voice (0.85 = each voice 15% softer).
    """

    delay_beats: float = 4.0
    interval_semitones: int = 7        # default: canon at the fifth
    n_voices: int = 2
    canon_type: CanonType = "fifth"
    velocity_decay: float = 0.88

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        delay_beats: float = 4.0,
        interval_semitones: int = 7,
        n_voices: int = 2,
        canon_type: CanonType = "fifth",
        velocity_decay: float = 0.88,
        interval: int | None = None,
    ) -> None:
        super().__init__(params)
        self.delay_beats = delay_beats
        self.interval_semitones = interval if interval is not None else interval_semitones
        self.n_voices = n_voices
        self.canon_type = canon_type
        self.velocity_decay = velocity_decay

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []
            
        dux = []
        low = self.params.key_range_low if self.params else 60
        high = self.params.key_range_high if self.params else 80
        
        t = 0.0
        prev_pitch = (low + high) // 2
        
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is not None:
                pcs = chord.pitch_classes()
                if pcs:
                    pc = random.choice(pcs)
                    pitch = nearest_pitch(pc, prev_pitch)
                    pitch = snap_to_scale(pitch, key)
                    pitch = max(low, min(high, pitch))
                    prev_pitch = pitch
                    
                    dux.append(
                        NoteInfo(
                            pitch=pitch,
                            start=t,
                            duration=0.45,
                            velocity=80,
                        )
                    )
            t += 0.5
            
        voices = self.generate(dux, scale=key)
        return self.merge_voices(voices)

    def generate(
        self,
        dux: list[NoteInfo],
        scale: Scale | None = None,
    ) -> list[list[NoteInfo]]:
        """Generate canon voices.

        Parameters
        ----------
        dux : list[NoteInfo]
            The leading voice (original melody).
        scale : Scale | None
            Required for 'inversion' canon (diatonic mirroring).

        Returns
        -------
        list[list[NoteInfo]]
            List of voices: [dux, comes_1, comes_2, ...].
            Length = n_voices.
        """
        n = max(2, min(4, self.n_voices))
        _scale = scale or Scale(0, Mode.MAJOR)

        voices: list[list[NoteInfo]] = [list(dux)]

        for i in range(1, n):
            delay = self.delay_beats * i
            vel_factor = self.velocity_decay ** i

            if self.canon_type in ("fifth", "unison", "octave"):
                semitones = {
                    "fifth":  self.interval_semitones,
                    "unison": 0,
                    "octave": 12,
                }[self.canon_type]
                transformed = _transpose(dux, semitones * i)

            elif self.canon_type == "crab":
                # Crab canon: follower plays dux backwards
                transformed = _retrograde(dux)
                # Align crab start to same time window
                if transformed:
                    offset_correction = dux[0].start - transformed[0].start
                    transformed = _shift_time(transformed, offset_correction)

            elif self.canon_type == "inversion":
                transformed = _diatonic_inversion(dux, _scale)

            elif self.canon_type == "augmentation":
                transformed = _augment(dux, factor=2.0 ** i)

            elif self.canon_type == "diminution":
                transformed = _diminish(dux, factor=2.0 ** i)

            else:
                transformed = list(dux)

            # Apply time delay and velocity decay
            comes = _shift_time(transformed, delay)
            comes = _scale_velocity(comes, vel_factor)
            voices.append(comes)

        return voices

    def total_duration(self, dux: list[NoteInfo]) -> float:
        """Return the total duration of all voices combined."""
        if not dux:
            return 0.0
        dux_end = max(n.start + n.duration for n in dux)
        n_extra = max(0, self.n_voices - 1)
        return dux_end + self.delay_beats * n_extra

    def merge_voices(
        self,
        voices: list[list[NoteInfo]],
    ) -> list[NoteInfo]:
        """Flatten all voices into a single sorted note list."""
        merged: list[NoteInfo] = []
        for v in voices:
            merged.extend(v)
        return sorted(merged, key=lambda n: n.start)


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------

def canon_at_fifth(
    melody: list[NoteInfo],
    delay_beats: float = 4.0,
    n_voices: int = 2,
) -> list[list[NoteInfo]]:
    """Canon at the fifth — the classical default."""
    return CanonGenerator(
        delay_beats=delay_beats,
        interval_semitones=7,
        n_voices=n_voices,
        canon_type="fifth",
    ).generate(melody)


def canon_at_octave(
    melody: list[NoteInfo],
    delay_beats: float = 4.0,
    n_voices: int = 2,
) -> list[list[NoteInfo]]:
    """Canon at the octave."""
    return CanonGenerator(
        delay_beats=delay_beats,
        interval_semitones=12,
        n_voices=n_voices,
        canon_type="octave",
    ).generate(melody)


def crab_canon(melody: list[NoteInfo]) -> list[list[NoteInfo]]:
    """Crab canon: dux forward, comes backward."""
    return CanonGenerator(canon_type="crab", delay_beats=0.0).generate(melody)


def inversion_canon(
    melody: list[NoteInfo],
    scale: Scale,
    delay_beats: float = 4.0,
) -> list[list[NoteInfo]]:
    """Inversion canon: dux forward, comes diatonic mirror."""
    return CanonGenerator(
        canon_type="inversion",
        delay_beats=delay_beats,
    ).generate(melody, scale=scale)
