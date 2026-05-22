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
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


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

        import math
        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord = chords[-1]

        for chord in chords:
            if self.hit_type == "braam":
                # Deep, low brass impact
                hit_pitches = self._get_hit_pitches(chord, mid - 24, key)
            else:
                hit_pitches = self._get_hit_pitches(chord, mid, key)

            if self.hit_type == "riser_hit":
                # Rising continuous buildup note before the hit
                riser_dur = min(chord.duration * 0.6, 2.0)
                riser_start = chord.start
                
                # Single continuous note sweeping up in pitch and volume
                riser_pitch = nearest_pitch(int(chord.root), mid - 12)
                riser_pitch = snap_to_scale(riser_pitch, key)
                riser_pitch = max(self.params.key_range_low, min(self.params.key_range_high, riser_pitch))
                
                riser_expr = {}
                pb_list = []
                cc11_list = []
                steps = 20
                for s in range(steps + 1):
                    t_rel = (s / steps) * riser_dur
                    # Pitch sweep: exponential curve up an octave (8191 units)
                    bend = int(8191 * (s / steps)**2.0)
                    pb_list.append((t_rel, bend))
                    
                    # Expression crescendo from 20 to 125
                    val = int(20 + 105 * (s / steps))
                    cc11_list.append((t_rel, val))
                    
                riser_expr["pitch_bend"] = pb_list
                riser_expr[11] = cc11_list
                
                riser_note = NoteInfo(
                    pitch=riser_pitch,
                    start=round(riser_start, 6),
                    duration=riser_dur,
                    velocity=40,
                )
                riser_note.expression = riser_expr
                notes.append(riser_note)
                
                # The hit itself starts at the end of the riser
                hit_onset = chord.start + riser_dur
            else:
                hit_onset = chord.start

            # Main hit duration
            hit_dur = self.duration
            if self.hit_type == "braam":
                hit_dur = self.duration * 1.8
            elif self.hit_type == "sustain":
                hit_dur = chord.duration * 0.9

            expression = {}
            if self.hit_type == "braam":
                # Deep low growl with a pitch fall:
                # Starts at +200 cents (1365 units) and falls to -2000 cents (-13653 units)
                pb_list = []
                steps = 15
                for s in range(steps + 1):
                    t_rel = (s / steps) * hit_dur
                    bend = int(1365 - 15018 * (s / steps)**1.5)
                    pb_list.append((t_rel, bend))
                expression["pitch_bend"] = pb_list

                # Growling CC 74 Filter Cutoff LFO modulation
                cc74_list = []
                cc_steps = 25
                for s in range(cc_steps + 1):
                    t_rel = (s / cc_steps) * hit_dur
                    base_cutoff = 110 - 65 * (s / cc_steps)
                    growl = math.sin((s / cc_steps) * hit_dur * 14 * math.pi * 2) * 15
                    cc74_list.append((t_rel, max(10, min(127, int(base_cutoff + growl)))))
                expression[74] = cc74_list

            for p in hit_pitches:
                vel = self._hit_velocity()
                note = NoteInfo(
                    pitch=p,
                    start=round(hit_onset, 6),
                    duration=hit_dur,
                    velocity=vel,
                    articulation="braam" if self.hit_type == "braam" else "hit",
                )
                if expression:
                    note.expression = expression.copy()
                notes.append(note)

            # Reverb tail: quiet sustained note
            if self.reverb_tail > 0 and hit_pitches:
                tail_pitch = hit_pitches[0]
                tail_note = NoteInfo(
                    pitch=tail_pitch,
                    start=round(hit_onset + hit_dur, 6),
                    duration=self.reverb_tail,
                    velocity=max(1, int(self._hit_velocity() * 0.2)),
                    articulation="sustain",
                )
                # Keep filter somewhat closed for the fading reverb tail
                if self.hit_type == "braam":
                    tail_note.expression = {74: 40}
                notes.append(tail_note)

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_hit_pitches(self, chord: ChordLabel, anchor: int, key: Scale) -> list[int]:
        pcs = chord.pitch_classes()
        if not pcs:
            return [snap_to_scale(nearest_pitch(chord.root, anchor), key)]

        if self.voicing == "unison":
            p = nearest_pitch(int(pcs[0]), anchor)
            p = snap_to_scale(p, key)
            return [max(self.params.key_range_low, min(self.params.key_range_high, p))]

        elif self.voicing == "octave":
            lo = nearest_pitch(int(pcs[0]), anchor - 12)
            hi = nearest_pitch(int(pcs[0]), anchor)
            lo = snap_to_scale(lo, key)
            hi = snap_to_scale(hi, key)
            return [
                max(self.params.key_range_low, min(self.params.key_range_high, lo)),
                max(self.params.key_range_low, min(self.params.key_range_high, hi)),
            ]

        else:  # chord
            pitches = []
            for i, pc in enumerate(pcs[:4]):
                offset = (i - len(pcs) // 2) * 12
                p = nearest_pitch(int(pc), anchor + offset)
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                pitches.append(p)
            return sorted(set(pitches))

    def _hit_velocity(self) -> int:
        base = {"staccato": 110, "sustain": 90, "riser_hit": 115, "braam": 120}
        return min(127, base.get(self.hit_type, 100) + int(self.params.density * 15))
