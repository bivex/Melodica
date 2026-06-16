# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/sax_section.py — Saxophone section generator.
Implements a 5-saxophone big band section (2 Alto, 2 Tenor, 1 Baritone)
with block or drop-2 voicings.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.generators.wind_brass_solo import _WindBrassSoloBase
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


@dataclass
class SaxophoneSectionGenerator(_WindBrassSoloBase):
    """
    Saxophone section generator (2 Alto, 2 Tenor, 1 Baritone).
    
    voicing_style:
        "block" (four-way close), "drop_2" (drop second voice an octave)
    baritone_doubles_lead:
        If True, Baritone sax doubles Lead Alto an octave lower.
    velocity_spread:
        Random velocity variation among players.
    note_density:
        Ensemble density scaling.
    """
    name: str = "Saxophone Section"
    voicing_style: str = "block"
    baritone_doubles_lead: bool = True
    velocity_spread: int = 8
    note_density: float = 1.0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        voicing_style: str = "block",
        baritone_doubles_lead: bool = True,
        velocity_spread: int = 8,
        note_density: float = 1.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.voicing_style = voicing_style
        self.baritone_doubles_lead = baritone_doubles_lead
        self.velocity_spread = max(0, velocity_spread)
        self.note_density = note_density
        self.rhythm = rhythm

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        # Apply density-based chord filtering/subdivision
        chords = self._apply_note_density(chords)
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        
        # Lead Alto register range: Eb3 (51) to F6 (89)
        # Mid-point anchor for lead melody
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        alto_low, alto_high = max(51, self.params.key_range_low), min(89, self.params.key_range_high)
        prev_lead_pitch = mid

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue

            # 1. Pick Lead Alto Pitch
            pcs = chord.pitch_classes()
            if not pcs:
                pcs = [chord.root]

            # Melodic movement: prefer stepwise or small leaps
            pc = random.choice(pcs)
            lead_pitch = nearest_pitch(pc, prev_lead_pitch)
            lead_pitch = snap_to_scale(lead_pitch, key)
            lead_pitch = max(alto_low, min(alto_high, lead_pitch))
            prev_lead_pitch = lead_pitch

            # 2. Voice Chord Down
            # helper to find next lower chord tone
            def get_next_tone_down(from_pitch: int) -> int:
                curr = from_pitch - 1
                while curr > 12:
                    if (curr % 12) in pcs:
                        return curr
                    curr -= 1
                return from_pitch - 12

            v0 = lead_pitch
            v1 = get_next_tone_down(v0)
            v2 = get_next_tone_down(v1)
            v3 = get_next_tone_down(v2)

            # Drop-2 modification: drop the second voice from the top (v1) down an octave
            if self.voicing_style == "drop_2":
                v1 = v1 - 12

            # Baritone sax voicing
            if self.baritone_doubles_lead:
                v4 = lead_pitch - 12
            else:
                lowest_upper = min(v0, v1, v2, v3)
                v4 = get_next_tone_down(lowest_upper)

            # 3. Distribute to Saxophone registers
            # Alto 1: v0 (Lead) -> Range 51-89
            # Alto 2: v1 -> Range 51-89
            # Tenor 1: v2 -> Range 44-75
            # Tenor 2: v3 -> Range 44-75
            # Baritone: v4 -> Range 36-68
            raw_pitches = [v0, v1, v2, v3, v4]
            ranges = [
                (51, 89),  # Alto 1
                (51, 89),  # Alto 2
                (44, 75),  # Tenor 1
                (44, 75),  # Tenor 2
                (36, 68),  # Baritone
            ]

            base_vel = int(72 + self.params.density * 15)

            for idx, p in enumerate(raw_pitches):
                low_r, high_r = ranges[idx]
                
                # Transpose by octaves if out of instrument range
                while p < low_r:
                    p += 12
                while p > high_r:
                    p -= 12
                
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))

                # Human timing stagger and velocity spread
                delay = 0.0 if idx == 0 else random.uniform(0.005, 0.018)
                vel = base_vel + random.randint(-self.velocity_spread, self.velocity_spread)
                
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(event.onset + delay, 6),
                        duration=round(event.duration * 0.95, 6),
                        velocity=max(1, min(127, vel)),
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[0].pitch,  # use lead voice
                last_velocity=notes[0].velocity,
                last_chord=chords[-1],
            )

        return sorted(notes, key=lambda x: x.start)

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        # Default swing big-band rhythms
        t, events = 0.0, []
        while t < duration_beats:
            dur = random.choice([0.25, 0.5, 0.5, 0.75, 1.0])
            events.append(RhythmEvent(onset=round(t, 6), duration=min(dur, duration_beats - t)))
            t += dur
        return events
