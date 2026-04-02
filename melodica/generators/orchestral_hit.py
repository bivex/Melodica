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
generators/orchestral_hit.py — Cinematic orchestral hit generator.

Layer: Application / Domain
Style: Film scoring, trailer music, cinematic, dramatic stings.

Produces impactful orchestral hits: staccato stabs, sustained chords,
riser-into-hit impacts, and deep "braam" brass tones.

Types:
    "staccato"    — short, punchy orchestral stab
    "sustain"     — sustained orchestral chord
    "riser_hit"   — ascending buildup into a hit
    "braam"       — deep, low brass impact (Inception-style)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class OrchestralHitGenerator(PhraseGenerator):
    """
    Cinematic orchestral hits.

    hit_type:
        "staccato", "sustain", "riser_hit", "braam"
    voicing:
        "unison" — single pitch, "octave" — doubled, "chord" — full triad
    duration:
        Base hit duration in beats.
    reverb_tail:
        Extra duration for reverb tail simulation (beats).
    """

    name: str = "Orchestral Hit Generator"
    hit_type: str = "staccato"
    voicing: str = "chord"
    duration: float = 0.5
    reverb_tail: float = 2.0
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        hit_type: str = "staccato",
        voicing: str = "chord",
        duration: float = 0.5,
        reverb_tail: float = 2.0,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.hit_type = hit_type
        self.voicing = voicing
        self.duration = max(0.1, min(8.0, duration))
        self.reverb_tail = max(0.0, min(8.0, reverb_tail))
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
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord = chords[-1]

        for chord in chords:
            hit_pitches = self._get_hit_pitches(chord, mid)

            if self.hit_type == "riser_hit":
                # Rising buildup before the hit
                riser_dur = min(chord.duration * 0.6, 2.0)
                riser_start = chord.start
                riser_pc = chord.root
                for i in range(int(riser_dur / 0.25)):
                    p = nearest_pitch(int(riser_pc), mid - 12 + i * 2)
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    vel = int(30 + i * 8)
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(riser_start + i * 0.25, 6),
                            duration=0.2,
                            velocity=min(127, vel),
                        )
                    )
                # The hit itself
                hit_onset = chord.start + riser_dur
            else:
                hit_onset = chord.start

            # Main hit
            hit_dur = self.duration
            if self.hit_type == "braam":
                hit_dur = self.duration * 1.5
            elif self.hit_type == "sustain":
                hit_dur = chord.duration * 0.9

            for p in hit_pitches:
                vel = self._hit_velocity()
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(hit_onset, 6),
                        duration=hit_dur,
                        velocity=vel,
                    )
                )

            # Reverb tail: quiet sustained note
            if self.reverb_tail > 0 and hit_pitches:
                tail_pitch = hit_pitches[0]
                notes.append(
                    NoteInfo(
                        pitch=tail_pitch,
                        start=round(hit_onset + hit_dur, 6),
                        duration=self.reverb_tail,
                        velocity=max(1, int(self._hit_velocity() * 0.2)),
                    )
                )

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_hit_pitches(self, chord: ChordLabel, anchor: int) -> list[int]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [nearest_pitch(chord.root, anchor)]

        if self.voicing == "unison":
            p = nearest_pitch(int(pcs[0]), anchor)
            return [max(self.params.key_range_low, min(self.params.key_range_high, p))]

        elif self.voicing == "octave":
            lo = nearest_pitch(int(pcs[0]), anchor - 12)
            hi = nearest_pitch(int(pcs[0]), anchor)
            return [
                max(self.params.key_range_low, min(self.params.key_range_high, lo)),
                max(self.params.key_range_low, min(self.params.key_range_high, hi)),
            ]

        else:  # chord
            pitches = []
            for i, pc in enumerate(pcs[:4]):
                offset = (i - len(pcs) // 2) * 12
                p = nearest_pitch(int(pc), anchor + offset)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                pitches.append(p)
            return sorted(set(pitches))

    def _hit_velocity(self) -> int:
        base = {"staccato": 110, "sustain": 90, "riser_hit": 115, "braam": 120}
        return min(127, base.get(self.hit_type, 100) + int(self.params.density * 15))
