# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-06-08
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/polyrhythm.py — Polyrhythmic note generator.

Layer: Application / Domain
Style: Jazz, African music, minimalism, contemporary classical, electronic.

Generates notes in a polyrhythmic relationship: two or more streams
of notes with different subdivisions playing simultaneously.

Jazz-specific presets:
    "clave"     — 3:2 son clave (Afro-Cuban foundation)
    "tresillo"  — 3:2 tresillo (Cuban habanera pattern)
    "cinquillo" — 5:2 cinquillo cubano
    "hemiola"   — 3:4 hemiola (West African / Brahms)

Standard polyrhythms:
    "3v2" — triplet against eighth notes
    "5v4" — quintuplets against sixteenths
    "3v4" — triplet against sixteenths
    "7v8" — septuplets against eighths
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


# Jazz preset patterns (onset positions within cycle, 0.0–1.0)
_CLAVE_SON = [0.0, 0.375, 0.75, 1.5, 1.875]       # 3-2 son clave in 2 bars
_TRESILLO = [0.0, 0.375, 0.75, 1.5, 1.75, 2.25, 2.625, 3.0, 3.75]  # 3+3+2
_CINQUILLO = [0.0, 0.25, 0.5, 0.75, 1.0, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.0, 3.25, 3.5, 3.75]
_HEMIOLA_3_4 = [0.0, 1.333, 2.667, 4.0, 5.333, 6.667]  # 3 groups of 2 vs 2 groups of 3

_PRESETS: dict[str, list[float]] = {
    "clave": _CLAVE_SON,
    "tresillo": _TRESILLO,
    "cinquillo": _CINQUILLO,
    "hemiola": _HEMIOLA_3_4,
}


@dataclass
class PolyrhythmGenerator(PhraseGenerator):
    """
    Polyrhythmic note generator.

    ratio:
        Polyrhythm ratio as "AxB" string (e.g., "3x2", "5x4"),
        or a preset name: "clave", "tresillo", "cinquillo", "hemiola".
    stream_a_pitch:
        Pitch selection for stream A: "chord_root", "chord_tone", "scale_tone".
    stream_b_pitch:
        Pitch selection for stream B: "fifth", "chord_root", "chord_tone".
    pitch_offset:
        Semitone offset between stream A and B pitches.
    duration:
        Duration of the polyrhythm cycle in beats.
    accent_pattern:
        "first" — accent first beat of each group.
        "pulse" — accent downbeats of the bar.
        "none" — flat dynamics.
    variation:
        Probability of micro-timing variation (0–1).
    """

    name: str = "Polyrhythm Generator"
    ratio: str = "3x2"
    stream_a_pitch: str = "chord_root"
    stream_b_pitch: str = "fifth"
    pitch_offset: int = 7
    duration: float = 4.0
    accent_pattern: str = "first"
    variation: float = 0.1
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        ratio: str = "3x2",
        stream_a_pitch: str = "chord_root",
        stream_b_pitch: str = "fifth",
        pitch_offset: int = 7,
        duration: float = 4.0,
        accent_pattern: str = "first",
        variation: float = 0.1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.ratio = ratio
        self.stream_a_pitch = stream_a_pitch
        self.stream_b_pitch = stream_b_pitch
        self.pitch_offset = pitch_offset
        self.duration = max(1.0, min(16.0, duration))
        self.accent_pattern = accent_pattern
        self.variation = max(0.0, min(1.0, variation))
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        # Check for preset
        preset = _PRESETS.get(self.ratio)
        if preset is not None:
            return self._render_preset(preset, chords, key, duration_beats, context)

        a, b = self._parse_ratio()
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        last_chord: ChordLabel | None = None
        cycle_dur = self.duration

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += cycle_dur
                continue
            last_chord = chord

            # Stream A
            pitch_a = self._pick_pitch(chord, self.stream_a_pitch, anchor, key, low, high)
            for i in range(a):
                onset = t + (i / a) * cycle_dur
                if onset >= duration_beats:
                    break
                n_dur = (cycle_dur / a) * 0.85
                vel = self._accent_vel(i, a, chord, onset)
                notes.append(NoteInfo(
                    pitch=max(low, min(high, pitch_a)),
                    start=max(0.0, round(onset + self._micro_time(), 6)),
                    duration=n_dur,
                    velocity=max(1, min(127, vel)),
                ))

            # Stream B
            pitch_b = self._pick_pitch(chord, self.stream_b_pitch, anchor, key, low, high)
            pitch_b = max(low, min(high, pitch_b + self.pitch_offset))
            for i in range(b):
                onset = t + (i / b) * cycle_dur
                if onset >= duration_beats:
                    break
                n_dur = (cycle_dur / b) * 0.85
                vel = self._accent_vel(i, b, chord, onset) - 5
                notes.append(NoteInfo(
                    pitch=pitch_b,
                    start=max(0.0, round(onset + self._micro_time(), 6)),
                    duration=n_dur,
                    velocity=max(1, min(127, vel)),
                ))

            t += cycle_dur

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_preset(
        self,
        onsets: list[float],
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        # Compute cycle length from max onset
        cycle_len = max(onsets) + 1.0 if onsets else 4.0
        last_chord: ChordLabel | None = None

        t = 0.0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += cycle_len
                continue
            last_chord = chord

            for i, offset in enumerate(onsets):
                onset = t + offset
                if onset >= duration_beats:
                    break

                pitch = self._pick_pitch(chord, self.stream_a_pitch, anchor, key, low, high)
                vel = int(60 + self.params.density * 30)
                if i == 0:
                    vel = min(127, vel + 15)
                elif self.accent_pattern == "pulse" and offset % 1.0 < 0.01:
                    vel = min(127, vel + 10)

                gap = (onsets[i + 1] - offset) if i + 1 < len(onsets) else 1.0
                notes.append(NoteInfo(
                    pitch=max(low, min(high, pitch)),
                    start=max(0.0, round(onset + self._micro_time(), 6)),
                    duration=gap * 0.85,
                    velocity=max(1, min(127, vel)),
                ))

            t += cycle_len

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _micro_time(self) -> float:
        if self.variation <= 0:
            return 0.0
        return random.gauss(0, self.variation * 0.05)

    def _accent_vel(self, idx: int, total: int, chord: ChordLabel, onset: float) -> int:
        base = int(60 + self.params.density * 30)
        if self.accent_pattern == "first" and idx == 0:
            return min(127, base + 15)
        if self.accent_pattern == "pulse" and onset % 1.0 < 0.01:
            return min(127, base + 10)
        return base

    def _parse_ratio(self) -> tuple[int, int]:
        parts = self.ratio.split("x")
        if len(parts) != 2:
            return (3, 2)
        try:
            return (int(parts[0]), int(parts[1]))
        except ValueError:
            return (3, 2)

    def _pick_pitch(
        self,
        chord: ChordLabel,
        strategy: str,
        anchor: int,
        key: Scale,
        low: int,
        high: int,
    ) -> int:
        if strategy == "chord_root":
            return nearest_pitch(chord.root, anchor)
        elif strategy == "chord_tone":
            pcs = chord.pitch_classes()
            return nearest_pitch(int(random.choice(pcs)), anchor)
        elif strategy == "scale_tone":
            degs = key.degrees()
            return (
                nearest_pitch(int(random.choice(degs)), anchor)
                if degs
                else nearest_pitch(chord.root, anchor)
            )
        elif strategy == "fifth":
            return nearest_pitch((chord.root + 7) % 12, anchor)
        return nearest_pitch(chord.root, anchor)


# ---------------------------------------------------------------------------
# HemiolaLayer — metric destabilization before modulation / section boundary
# ---------------------------------------------------------------------------

def hemiola_layer(
    chords: "list[ChordLabel]",
    key: "Scale",
    start_beat: float,
    duration_beats: float,
    *,
    pitch: int = 60,
    velocity: int = 62,
    note_dur: float = 0.45,
    beats_per_bar: int = 4,
) -> "list[NoteInfo]":
    """Generate a hemiola layer — 3-against-2 metric grouping.

    Produces a stream of notes accented in groups of 3 across a region that
    is metrically organised in groups of 2 (or 4).  The result creates the
    characteristic 'pull' feeling used before cadences and modulation points.

    Place it in the 2–4 bars before a section change for maximum effect.

    Parameters
    ----------
    chords : list[ChordLabel]
        Chord context (used for pitch selection).
    key : Scale
        Current scale (used for chord-tone snapping).
    start_beat : float
        Beat position where the hemiola begins.
    duration_beats : float
        How many beats the hemiola covers (typically 4–8).
    pitch : int
        Reference MIDI pitch for octave placement.
    velocity : int
        Base velocity. Notes on hemiola downbeats get +15.
    note_dur : float
        Duration of each hemiola note in beats.
    beats_per_bar : int
        Meter denominator (used to determine hemiola subdivision).

    Returns
    -------
    list[NoteInfo]
        Notes forming the hemiola layer, ready to merge into any track.
    """
    # Hemiola: 3 equal notes in the space of 2 beats
    # subdivision = 2/3 of a beat
    subdivision = (beats_per_bar * 2) / (beats_per_bar * 3)  # = 2/3
    n_notes = max(1, int(duration_beats / subdivision))

    # Snap pitch to chord tones
    def _snap(beat: float) -> int:
        if not chords:
            return pitch
        chord = chord_at(chords, beat)
        if chord is None:
            return pitch
        pcs = chord.pitch_classes() if hasattr(chord, "pitch_classes") else [chord.root]
        ref_oct = pitch // 12
        best = pitch
        best_dist = 127
        for pc in pcs:
            for oct_off in (-1, 0, 1):
                cand = pc + (ref_oct + oct_off) * 12
                dist = abs(cand - pitch)
                if dist < best_dist:
                    best_dist = dist
                    best = cand
        return max(0, min(127, best))

    notes: list[NoteInfo] = []
    for i in range(n_notes):
        beat = start_beat + i * subdivision
        # Accent every 3rd note (hemiola downbeat)
        is_hemiola_beat = (i % 3 == 0)
        vel = min(127, velocity + (15 if is_hemiola_beat else 0))
        p = _snap(beat)
        notes.append(NoteInfo(
            pitch=p,
            start=round(beat, 6),
            duration=note_dur,
            velocity=vel,
        ))
    return notes


def polyrhythm_section(
    chords: "list[ChordLabel]",
    key: "Scale",
    start_beat: float,
    duration_beats: float,
    ratio: str = "3x2",
    *,
    pitch_a: int = 60,
    pitch_b: int = 67,
    velocity: int = 58,
    note_dur: float = 0.4,
) -> "tuple[list[NoteInfo], list[NoteInfo]]":
    """Generate two interlocking polyrhythm streams (A and B) as plain note lists.

    Unlike PolyrhythmGenerator (which requires a full PhraseGenerator context),
    this function works directly with beat offsets — useful in section_builder
    and album scripts.

    Parameters
    ----------
    ratio : str
        \"AxB\" string — e.g. \"3x2\", \"5x4\".
    pitch_a, pitch_b : int
        Reference MIDI pitches for stream A and B.
    velocity : int
        Base velocity.
    note_dur : float
        Duration of each note.

    Returns
    -------
    (stream_a, stream_b) : tuple[list[NoteInfo], list[NoteInfo]]
    """
    parts = ratio.lower().split("x")
    a, b = (int(parts[0]), int(parts[1])) if len(parts) == 2 else (3, 2)

    lcm_val = (a * b) // __import__("math").gcd(a, b)
    cycle_beats = float(lcm_val)

    n_cycles = max(1, int(duration_beats / cycle_beats))

    stream_a: list[NoteInfo] = []
    stream_b: list[NoteInfo] = []

    for cycle in range(n_cycles):
        base = start_beat + cycle * cycle_beats
        step_a = cycle_beats / a
        step_b = cycle_beats / b
        for i in range(a):
            beat = base + i * step_a
            stream_a.append(NoteInfo(
                pitch=pitch_a, start=round(beat, 6),
                duration=note_dur, velocity=min(127, velocity + (10 if i == 0 else 0)),
            ))
        for i in range(b):
            beat = base + i * step_b
            stream_b.append(NoteInfo(
                pitch=pitch_b, start=round(beat, 6),
                duration=note_dur, velocity=min(127, velocity + (8 if i == 0 else 0)),
            ))

    return stream_a, stream_b
