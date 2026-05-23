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
generators/woodwinds_ensemble.py — Woodwind section harmonization.

Layer: Application / Domain
Style: Classical, film scoring, orchestral, chamber music.

Produces harmonized woodwind lines using flute, clarinet, oboe, and
bassoon voicings. Each section size controls how many instruments
participate in the texture.

Sections:
    "trio"    — flute, clarinet, oboe
    "quartet" — flute, clarinet, oboe, bassoon
    "full"    — doubled flute, clarinet, oboe, bassoon, english horn
"""

from __future__ import annotations

import random
import math
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


SECTION_VOICINGS: dict[str, list[int]] = {
    "solo": [0],
    "trio": [0, -1, 1],  # clarinet, oboe above, flute below anchor
    "quartet": [0, -1, 1, -2],  # + bassoon low
    "full": [0, 0, -1, 1, -2],  # doubled top + english horn
}

ARTICULATION_DURATIONS: dict[str, float] = {
    "legato": 0.95,
    "staccato": 0.3,
    "marcato": 0.7,
}

ARTICULATION_VELOCITY_BOOST: dict[str, int] = {
    "legato": 0,
    "staccato": 10,
    "marcato": 20,
}


@dataclass
class WoodwindsEnsembleGenerator(PhraseGenerator):
    """
    Woodwind section: flute, clarinet, oboe harmonized.

    section:
        "trio", "quartet", "full"
    articulation:
        "legato", "staccato", "marcato"
    dynamic_range:
        Controls velocity spread (0.0–1.0). Higher = more variation.
    """

    name: str = "Woodwinds Ensemble Generator"
    section: str = "quartet"
    ensemble_mode: str = "full"
    articulation: str = "legato"
    dynamic_range: float = 0.5
    breath_interval: float = 6.0
    breath_gap: float = 0.3
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        section: str = "quartet",
        ensemble_mode: str = "full",
        articulation: str = "legato",
        dynamic_range: float = 0.5,
        breath_interval: float = 6.0,
        breath_gap: float = 0.3,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.section = section
        self.ensemble_mode = ensemble_mode
        self.articulation = articulation
        self.dynamic_range = max(0.0, min(1.0, dynamic_range))
        self.breath_interval = max(2.0, breath_interval)
        self.breath_gap = max(0.0, min(1.0, breath_gap))
        self.rhythm = rhythm

    def _velocity(self, vel_boost: int = 0) -> int:
        base = self.base_velocity()
        vel_var = int(self.dynamic_range * 15)
        vel = base + vel_boost + random.randint(-vel_var, vel_var)
        return max(1, min(127, vel))

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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord = chords[-1]

        # Map ensemble_mode to section type
        mode = getattr(self, "ensemble_mode", "full")
        sec_type = self.section
        if mode == "solo":
            sec_type = "solo"
        elif mode == "chamber":
            sec_type = "trio"
        elif mode == "section":
            sec_type = "quartet"
        elif mode == "tutti":
            sec_type = "full"

        voicing_offsets = SECTION_VOICINGS.get(sec_type, SECTION_VOICINGS["quartet"])
        dur_factor = ARTICULATION_DURATIONS.get(self.articulation, 0.95)
        vel_boost = ARTICULATION_VELOCITY_BOOST.get(self.articulation, 0)

        # Per-instrument ranges: voice_idx maps to instrument regardless of section
        # 0=Flute, 1=Clarinet, 2=Oboe, 3=Bassoon, 4=English Horn
        instrument_ranges = {
            0: (60, 96),   # Flute
            1: (50, 91),   # Clarinet
            2: (58, 91),   # Oboe
            3: (34, 72),   # Bassoon
            4: (52, 84),   # English Horn
        }

        # Track cumulative play duration per voice to insert breath pauses
        # Higher density = longer before breath (4 + density*4 beats, range 4–8)
        breath_threshold_base = 4.0 + self.params.density * 4.0
        voice_accumulators = {v_idx: 0.0 for v_idx in range(len(voicing_offsets))}
        voice_breath_thresholds = {
            v_idx: breath_threshold_base + random.uniform(-0.5, 0.5)
            for v_idx in range(len(voicing_offsets))
        }
        # Track which voices are currently breathing (skip their event)
        voice_breathing = set()

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            for voice_idx, offset in enumerate(voicing_offsets):
                # Breath mark: check if this voice needs to breathe and skip the event
                accum = voice_accumulators[voice_idx]
                if accum >= voice_breath_thresholds[voice_idx]:
                    # Skip this chord event to simulate breathing
                    voice_accumulators[voice_idx] = 0.0
                    voice_breath_thresholds[voice_idx] = breath_threshold_base + random.uniform(-0.5, 0.5)
                    continue
                voice_accumulators[voice_idx] += chord.duration
                pc = pcs[voice_idx % len(pcs)]
                anchor = mid + offset * 12
                pitch = nearest_pitch(int(pc), anchor)

                # Transpose to natural instrument register range
                low_r, high_r = instrument_ranges.get(voice_idx, (34, 96))
                while pitch < low_r:
                    pitch += 12
                while pitch > high_r:
                    pitch -= 12
                pitch = snap_to_scale(pitch, key)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                vel = self._velocity(vel_boost)

                # Physical attack timing offset depending on the instrument voice index
                # Flutes (idx=0) are very fast, Oboes (idx=1) double reed slightly slower,
                # Clarinets (idx=2) medium, Bassoons (idx=3) slowest double reed response.
                inst_delay = 0.0
                if voice_idx == 1:    # Oboe
                    inst_delay = random.uniform(0.004, 0.012)
                elif voice_idx == 2:  # Clarinet
                    inst_delay = random.uniform(0.003, 0.010)
                elif voice_idx >= 3:  # Bassoon
                    inst_delay = random.uniform(0.010, 0.022)

                onset = chord.start + inst_delay + random.uniform(0.0, 0.005 * self.dynamic_range)
                note_dur = chord.duration * dur_factor

                # Acoustic Air Pressure LFO (CC 11 Expression fluctuations) on long legato notes
                expression = {}
                if self.articulation == "legato" and note_dur >= 1.0:
                    steps = 12
                    cc11_list = []
                    for s in range(steps + 1):
                        progress = s / steps
                        t_rel = progress * note_dur
                        # Pressure sweep: LFO starts dry and increases on long notes at 7Hz
                        fade = min(1.0, t_rel / 0.6)
                        lfo_val = int(80 + fade * 8 * math.sin(2 * math.pi * 7.0 * t_rel))
                        cc11_list.append((t_rel, max(0, min(127, lfo_val))))
                    expression[11] = cc11_list

                note = NoteInfo(
                    pitch=pitch,
                    start=round(onset, 6),
                    duration=max(0.1, note_dur),
                    velocity=vel,
                    articulation=self.articulation,
                )
                if expression:
                    note.expression = expression
                notes.append(note)

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes
