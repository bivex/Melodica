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
generators/chord_voicing.py — Chord voicing generator.

Generates chords in specific voicing configurations used in jazz,
pop, and classical music. Unlike the basic chord generator, this
produces multi-note voicings with controlled spacing.

Voicing types:
    "close"     — all notes within one octave (tight)
    "open"      — notes spread beyond one octave
    "drop2"     — second-highest voice dropped an octave
    "drop3"     — third-highest voice dropped an octave
    "cluster"   — seconds and semitones (tense)
    "spread"    — wide spacing with doublings
    "shearing"  — George Shearing style (block chords with melody on top)
    "rootless"  — jazz rootless voicing (3-7-9-13)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


def _build_close(root: int, intervals: list[int]) -> list[int]:
    """Close voicing: all within one octave."""
    return [root + i for i in sorted(intervals)]


def _build_open(root: int, intervals: list[int]) -> list[int]:
    """Open voicing: alternate voices up/down an octave."""
    notes = sorted(intervals)
    result = []
    for i, n in enumerate(notes):
        result.append(root + n + (12 if i % 2 == 1 else 0))
    return sorted(result)


def _build_drop2(root: int, intervals: list[int]) -> list[int]:
    """Drop-2: second-highest note dropped an octave."""
    notes = sorted([root + i for i in intervals])
    if len(notes) >= 2:
        notes[-2] -= 12
    return sorted(notes)


def _build_drop3(root: int, intervals: list[int]) -> list[int]:
    """Drop-3: third-highest note dropped an octave."""
    notes = sorted([root + i for i in intervals])
    if len(notes) >= 3:
        notes[-3] -= 12
    return sorted(notes)


def _build_cluster(root: int, intervals: list[int]) -> list[int]:
    """Cluster voicing: tightly packed seconds."""
    base = root
    return [base + i * 2 for i in range(min(len(intervals), 4))]


def _build_spread(root: int, intervals: list[int]) -> list[int]:
    """Spread voicing: wide spacing with octave doublings."""
    notes = sorted(intervals)
    result = []
    for i, n in enumerate(notes):
        oct_shift = (i // 2) * 12
        result.append(root + n + oct_shift)
    return sorted(result)


def _build_shearing(root: int, intervals: list[int]) -> list[int]:
    """Shearing voicing: block chord, melody note on top."""
    notes = sorted([root + i for i in intervals])
    if len(notes) >= 2:
        notes[-1] += 12  # melody note up an octave
    return sorted(notes)


def _get_chord_tones(intervals: list[int]) -> tuple[int, int, int, int, int]:
    third = 4
    if len(intervals) > 1:
        third = intervals[1]
    
    fifth = 7
    if len(intervals) > 2:
        fifth = intervals[2]
        
    seventh = 10
    if len(intervals) > 3:
        seventh = intervals[3]
    elif third == 3:
        seventh = 10
    else:
        seventh = 11

    ninth = 14
    thirteenth = 21
    return third, fifth, seventh, ninth, thirteenth


def _build_rootless_a(root: int, intervals: list[int]) -> list[int]:
    """Category A rootless voicing: 3rd, 5th/13th, 7th, 9th."""
    third, fifth, seventh, ninth, thirteenth = _get_chord_tones(intervals)
    note3 = root + third
    note5 = root + (thirteenth if seventh == 10 and third == 4 else fifth)
    note7 = root + seventh
    note9 = root + ninth
    return sorted([note3, note5, note7, note9])


def _build_rootless_b(root: int, intervals: list[int]) -> list[int]:
    """Category B rootless voicing: 7th, 9th, 3rd, 5th/13th."""
    third, fifth, seventh, ninth, thirteenth = _get_chord_tones(intervals)
    note7 = root + seventh
    note9 = root + ninth
    note3 = root + third + 12
    note5 = root + (thirteenth if seventh == 10 and third == 4 else fifth) + 12
    return sorted([note7, note9, note3, note5])


def _build_quartal(root: int, intervals: list[int]) -> list[int]:
    """Quartal voicing: stacks of perfect 4ths (McCoy Tyner style)."""
    return [root + i * 5 for i in range(min(len(intervals), 4))]


def _build_so_what(root: int, intervals: list[int]) -> list[int]:
    """So What voicing: parallel 4th-based structure (Bill Evans / Miles Davis)."""
    # Dm9 = D-F-A-C-E → intervals [0,5,10,15,17] from root
    return [root, root + 5, root + 10, root + 15, root + 17]


_BUILDERS = {
    "close": _build_close,
    "open": _build_open,
    "drop2": _build_drop2,
    "drop3": _build_drop3,
    "cluster": _build_cluster,
    "spread": _build_spread,
    "shearing": _build_shearing,
    "rootless": _build_rootless_a,
    "rootless_a": _build_rootless_a,
    "rootless_b": _build_rootless_b,
    "quartal": _build_quartal,
    "so_what": _build_so_what,
}


# Chord quality → intervals from root
_CHORD_INTERVALS = {
    "major": [0, 4, 7],
    "minor": [0, 3, 7],
    "dominant7": [0, 4, 7, 10],
    "major7": [0, 4, 7, 11],
    "minor7": [0, 3, 7, 10],
    "dim": [0, 3, 6],
    "aug": [0, 4, 8],
    "sus2": [0, 2, 7],
    "sus4": [0, 5, 7],
}


@dataclass
class ChordVoicingGenerator(PhraseGenerator):
    """
    Chord voicing generator.

    Produces chords in specific voicing configurations.

    voicing:
        Voicing type. See _BUILDERS.
    rhythm_pattern:
        "sustained" — one chord per chord change
        "rhythmic" — repeated chords on subdivision
        "arp_up" / "arp_down" — arpeggiated voicing
    octave:
        Base octave (MIDI octave number, 4 = middle C octave).
    velocity_curve:
        "flat", "crescendo", "decrescendo", "accent_first".
    """

    name: str = "Chord Voicing Generator"
    voicing: str = "drop2"
    rhythm_pattern: str = "sustained"
    octave: int = 4
    velocity_curve: str = "flat"
    inversion: int = 0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voicing: str = "drop2",
        rhythm_pattern: str = "sustained",
        octave: int = 4,
        velocity_curve: str = "flat",
        inversion: int = 0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if voicing not in _BUILDERS:
            raise ValueError(f"Unknown voicing: {voicing!r}; expected one of {sorted(_BUILDERS)}")
        self.voicing = voicing
        self.rhythm_pattern = rhythm_pattern
        self.octave = max(1, min(7, octave))
        self.velocity_curve = velocity_curve
        self.inversion = inversion
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

        notes: list[NoteInfo] = []
        builder = _BUILDERS[self.voicing]
        subdivision = 1.0 if self.rhythm_pattern == "sustained" else 0.5
        t = 0.0

        while t < duration_beats:
            chord = chord_at(chords, t)
            root_pc = chord.root % 12
            base_midi = root_pc + self.octave * 12
            quality = str(chord.quality).lower().replace("quality.", "")
            intervals = list(_CHORD_INTERVALS.get(quality, [0, 4, 7]))

            # Apply inversion: rotate intervals so bass note is first
            inv = self.inversion
            if hasattr(chord, "inversion") and chord.inversion is not None:
                inv = chord.inversion
            if 0 < inv < len(intervals):
                bass_interval = intervals[inv]
                intervals = [i - bass_interval for i in intervals]
                # Move bass interval up an octave
                intervals = intervals[inv:] + [i + 12 for i in intervals[:inv]]

            pitches = builder(base_midi, intervals)
            pitches = [snap_to_scale(max(0, min(127, p)), key) for p in pitches]

            chord_dur = (
                min(chord.end - t, duration_beats - t)
                if hasattr(chord, "end")
                else min(4.0, duration_beats - t)
            )
            if chord_dur <= 0:
                t += 0.5
                continue

            if self.rhythm_pattern in ("arp_up", "arp_down"):
                ordered = pitches if self.rhythm_pattern == "arp_up" else list(reversed(pitches))
                step_dur = chord_dur / max(1, len(ordered))
                for i, p in enumerate(ordered):
                    onset = t + i * step_dur
                    if onset >= duration_beats:
                        break
                    vel = self._vel(i, len(ordered), t, duration_beats)
                    notes.append(
                        NoteInfo(
                            pitch=p, start=round(onset, 6), duration=step_dur * 0.9, velocity=vel
                        )
                    )
            else:
                vel = self._vel(0, 1, t, duration_beats)
                for p in pitches:
                    notes.append(
                        NoteInfo(pitch=p, start=round(t, 6), duration=chord_dur, velocity=vel)
                    )

            t += chord_dur

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chord_at(chords, duration_beats) if chords else None,
            )
        return notes

    def _vel(self, idx: int, total: int, t: float, dur: float) -> int:
        base = int(self.params.density * 100)
        if self.velocity_curve == "crescendo":
            factor = 0.6 + 0.4 * (t / max(0.1, dur))
        elif self.velocity_curve == "decrescendo":
            factor = 1.0 - 0.4 * (t / max(0.1, dur))
        elif self.velocity_curve == "accent_first" and idx == 0:
            factor = 1.2
        else:
            factor = 0.9
        return max(1, min(127, int(base * factor)))
