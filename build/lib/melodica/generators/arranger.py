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
generators/arranger.py — Arrangement structure generator.

Layer: Application / Domain
Style: All genres — pop, rock, jazz, EDM, film.

The arranger generator manages the high-level structure of a piece,
sequencing other generators through verse, chorus, bridge, and other
sections. It outputs notes from a composite of section-specific
generator selections.

This is a meta-generator that orchestrates the arrangement.

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


@dataclass
class ArrangerGenerator(PhraseGenerator):
    """
    Arrangement structure generator.

    Manages section-based note generation by varying density, register,
    and rhythmic complexity across sections.

    form:
        Arrangement form (see above).
    section_length:
        Length of each section in bars.
    variation_seed:
        Random seed for reproducible arrangements.
    intensity_map:
        Per-section intensity overrides. E.g., {"chorus": 0.9, "verse": 0.5}
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
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        form: str = "verse_chorus",
        section_length: int = 8,
        variation_seed: int = 0,
        intensity_map: dict[str, float] | None = None,
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

        sections = FORM_SECTIONS.get(self.form, FORM_SECTIONS["verse_chorus"])
        bars_per_section = self.section_length
        beats_per_section = bars_per_section * 4

        notes: list[NoteInfo] = []
        low = self.params.key_range_low
        high = self.params.key_range_high
        mid = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else mid
        last_chord: ChordLabel | None = None
        rng = random.Random(self.variation_seed)

        section_idx = 0
        t = 0.0
        while t < duration_beats:
            section_name = sections[section_idx % len(sections)]
            intensity = self.intensity_map.get(section_name, 0.6)
            section_end = min(t + beats_per_section, duration_beats)

            # Generate notes for this section with section-specific parameters
            section_notes = self._generate_section(
                chords, key, t, section_end, intensity, prev_pitch, rng, mid, low, high
            )
            notes.extend(section_notes)
            if section_notes:
                prev_pitch = section_notes[-1].pitch

            t = section_end
            section_idx += 1

        if chords:
            last_chord = chords[-1]

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
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
        """
        Generate section notes with distinct strategies by intensity level:

        - Low  (intro/outro, intensity < 0.45): sparse whole-chord pads, slow rhythm,
          low register. One chord voicing per harmony change.
        - Mid  (verse/bridge, 0.45–0.7): single-voice melody-like line at 1-beat steps,
          mid register, moderate velocity.
        - High (chorus, intensity > 0.7): full block chords (all tones) on every beat,
          upper register, high velocity with accent on beat 1.
        """
        notes = []
        vel_base = int(30 + intensity * 70)

        slot_chords = [c for c in chords if c.start < end and c.end > start]
        if not slot_chords:
            return notes

        # ── LOW: pad/ambient — one voicing per chord change ──────────────────
        if intensity < 0.45:
            for chord in slot_chords:
                c_start = max(chord.start, start)
                c_end = min(chord.end(), end)
                if c_start >= end:
                    break
                pcs = chord.pitch_classes()
                if not pcs:
                    continue
                # Spread voicing: root + fifth + octave, low register
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

        # ── MID: single melodic voice at quarter-note steps ──────────────────
        elif intensity <= 0.7:
            step = 1.0
            t = start
            while t < end:
                chord = chord_at(chords, t)
                if chord is None:
                    t += step
                    continue
                if rng.random() > 0.25:  # 75% fill rate
                    pcs = chord.pitch_classes()
                    if pcs:
                        # Stepwise bias: prefer close pitch classes
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

        # ── HIGH: full block chords every beat, accented ─────────────────────
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
