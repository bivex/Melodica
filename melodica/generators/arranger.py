# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/arranger.py — Arrangement structure generator.

Layer: Application / Domain
Style: All genres — pop, rock, jazz, EDM, film, orchestral.

The arranger manages high-level structure of a piece, sequencing
other generators through verse, chorus, bridge, and other sections.

It can work in two modes:
1. Orchestral mode (use_orchestral=True): delegates to OrchestralScoreGenerator
   for full multi-track orchestral arrangements with per-instrument voicing.
2. Classic mode (use_orchestral=False): lightweight inline generation with
   intensity-based density/register control (backwards compatible).

Both modes populate self.tracks and self.instruments for multi-track export.

Form patterns:
    "ABABCB"  — pop structure (intro-verse-chorus-verse-chorus-bridge-chorus)
    "AABA"    — jazz standard (32-bar AABA)
    "verse_chorus" — simple verse-chorus
    "through_composed" — continuously evolving
    "rondo"   — A-B-A-C-A
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


FORM_SECTIONS: dict[str, list[str]] = {
    "ABABCB": ["intro", "verse", "chorus", "verse", "chorus", "bridge", "chorus"],
    "AABA": ["A", "A", "B", "A"],
    "verse_chorus": ["verse", "chorus", "verse", "chorus"],
    "through_composed": ["A", "B", "C", "D"],
    "rondo": ["A", "B", "A", "C", "A"],
}

# Map abstract letters to section semantics for intensity
_LETTER_TO_INTENSITY = {
    "A": 0.6,
    "B": 0.75,
    "C": 0.85,
    "D": 0.7,
}


@dataclass
class ArrangerGenerator(PhraseGenerator):
    """
    Arrangement structure generator.

    form:
        Arrangement form (see FORM_SECTIONS).
    section_length:
        Length of each section in bars.
    variation_seed:
        Random seed for reproducible arrangements.
    intensity_map:
        Per-section intensity overrides. E.g., {"chorus": 0.9, "verse": 0.5}
    use_orchestral:
        If True, delegates to OrchestralScoreGenerator for full orchestral
        arrangement with proper instrument voicing and texture control.
        Populates self.tracks with per-instrument note lists.
    """

    name: str = "Arranger Generator"
    form: str = "verse_chorus"
    section_length: int = 8
    variation_seed: int = 0
    intensity_map: dict[str, float] = field(
        default_factory=lambda: {
            "intro": 0.3,
            "verse": 0.5,
            "chorus": 0.85,
            "bridge": 0.6,
            "outro": 0.4,
            "A": 0.6,
            "B": 0.7,
            "C": 0.75,
            "D": 0.8,
        }
    )
    use_orchestral: bool = False
    rhythm: RhythmGenerator | None = None

    # Multi-track output (populated after render)
    tracks: dict[str, list[NoteInfo]] = field(default_factory=dict, init=False, repr=False)
    instruments: dict[str, int] = field(default_factory=dict, init=False, repr=False)
    pan_map: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        form: str = "verse_chorus",
        section_length: int = 8,
        variation_seed: int = 0,
        intensity_map: dict[str, float] | None = None,
        use_orchestral: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.form = form
        self.section_length = max(4, min(32, section_length))
        self.variation_seed = variation_seed
        if intensity_map is not None:
            self.intensity_map = intensity_map
        else:
            self.intensity_map = {
                "intro": 0.3,
                "verse": 0.5,
                "chorus": 0.85,
                "bridge": 0.6,
                "outro": 0.4,
                "A": 0.6,
                "B": 0.7,
                "C": 0.75,
                "D": 0.8,
            }
        self.use_orchestral = use_orchestral
        self.rhythm = rhythm
        self.tracks = {}
        self.instruments = {}
        self.pan_map = {}

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        self.tracks = {}
        self.instruments = {}
        self.pan_map = {}

        sections = FORM_SECTIONS.get(self.form, FORM_SECTIONS["verse_chorus"])
        beats_per_section = self.section_length * 4

        # Build section tuples for orchestral mode
        section_tuples = []
        t = 0.0
        idx = 0
        while t < duration_beats:
            sec_name = sections[idx % len(sections)]
            dur = min(beats_per_section, duration_beats - t)
            section_tuples.append((sec_name, t, dur))
            t += dur
            idx += 1

        if self.use_orchestral:
            return self._render_orchestral(chords, key, duration_beats, section_tuples, context)
        else:
            return self._render_classic(chords, key, duration_beats, section_tuples, context)

    def _render_orchestral(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        section_tuples: list[tuple[str, float, float]],
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        from melodica.generators.orchestral_score import OrchestralScoreGenerator

        score = OrchestralScoreGenerator(
            self.params,
            sections=section_tuples,
        )
        all_notes = score.render(chords, key, duration_beats, context)

        # Copy multi-track output
        self.tracks = dict(score.tracks)
        self.instruments = dict(score.instruments)
        self.pan_map = dict(score.pan_map)

        if all_notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=all_notes[-1].pitch,
                last_velocity=all_notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )
        return all_notes

    def _render_classic(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        section_tuples: list[tuple[str, float, float]],
        context: RenderContext | None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2
        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else mid
        rng = random.Random(self.variation_seed)

        for sec_name, sec_start, sec_dur in section_tuples:
            intensity = self.intensity_map.get(sec_name, _LETTER_TO_INTENSITY.get(sec_name, 0.6))
            sec_end = sec_start + sec_dur

            sec_notes = self._generate_section(
                chords, key, sec_start, sec_end, intensity, prev_pitch, rng, mid, low, high
            )
            notes.extend(sec_notes)
            if sec_notes:
                prev_pitch = sec_notes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[-1] if chords else None,
            )

            # In classic mode, store as single track
            self.tracks["arranger"] = notes
            self.instruments["arranger"] = 0
            self.pan_map["arranger"] = 0.0

        return notes

    def _generate_section(
        self,
        chords: list[ChordLabel],
        key: Scale,
        start: float,
        end: float,
        intensity: float,
        prev_pitch: int,
        rng: random.Random,
        mid: int,
        low: int,
        high: int,
    ) -> list[NoteInfo]:
        notes = []
        vel_base = int(30 + intensity * 70)

        slot_chords = [c for c in chords if c.start < end and c.end > start]
        if not slot_chords:
            return notes

        if intensity < 0.45:
            for chord in slot_chords:
                c_start = max(chord.start, start)
                c_end = min(chord.end(), end)
                if c_start >= end:
                    break
                pcs = chord.pitch_classes()
                if not pcs:
                    continue
                root_pc = int(pcs[0])
                pitches = [nearest_pitch(root_pc, low + 12)]
                if len(pcs) > 1:
                    pitches.append(nearest_pitch(int(pcs[1]), pitches[0] + 5))
                dur = max(0.1, c_end - c_start) * 0.95
                for p in pitches:
                    p = max(low, min(mid, p))
                    notes.append(NoteInfo(
                        pitch=p,
                        start=round(c_start, 6),
                        duration=round(dur, 6),
                        velocity=max(1, min(127, vel_base + rng.randint(-5, 5))),
                    ))

        elif intensity <= 0.7:
            step = 1.0
            t = start
            while t < end:
                chord = chord_at(chords, t)
                if chord is None:
                    t += step
                    continue
                if rng.random() > 0.25:
                    pcs = chord.pitch_classes()
                    if pcs:
                        pc = min(pcs, key=lambda p: abs(nearest_pitch(int(p), prev_pitch) - prev_pitch))
                        pitch = nearest_pitch(int(pc), prev_pitch)
                        pitch = max(mid - 12, min(mid + 12, pitch))
                        pitch = max(low, min(high, pitch))
                        notes.append(NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=step * 0.85,
                            velocity=max(1, min(127, vel_base + rng.randint(-8, 8))),
                        ))
                        prev_pitch = pitch
                t += step

        else:
            step = 1.0
            t = start
            beat_in_section = 0
            while t < end:
                chord = chord_at(chords, t)
                if chord is None:
                    t += step
                    beat_in_section += 1
                    continue
                pcs = chord.pitch_classes()
                if pcs:
                    accent = 1.15 if beat_in_section % 4 == 0 else 1.0
                    for i, pc in enumerate(pcs):
                        octave_shift = 12 if i < len(pcs) // 2 else 0
                        pitch = nearest_pitch(int(pc), mid + octave_shift)
                        pitch = max(low, min(high, pitch))
                        vel = min(127, int(vel_base * accent) + rng.randint(-5, 5))
                        notes.append(NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=step * 0.88,
                            velocity=max(1, vel),
                        ))
                t += step
                beat_in_section += 1

        return notes
