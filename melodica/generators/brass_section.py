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
generators/brass_section.py — Brass section articulation generator.

Layer: Application / Domain
Style: Big band, orchestral, funk, cinematic.

Brass section hits, swells, and fanfares. Brass articulation is defined
by attack type, sustain, and release characteristics.

Articulations:
    "hit"      — short, accented stabs (forte-piano)
    "swell"    — crescendo from pp to ff
    "fanfare"  — ascending arpeggiated brass call
    "sustained" — long held notes with marcato attack
    "falls"    — notes with pitch falls at the end
    "doits"    — notes with upward pitch bends at the end
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at, chord_pitches_closed, snap_to_scale


@dataclass
class BrassSectionGenerator(PhraseGenerator):
    """
    Brass section articulation generator.

    articulation:
        "hit", "swell", "fanfare", "sustained", "falls", "doits"
    voicing:
        "closed", "open" — chord voicing style.
    intensity:
        Base velocity level (0.0–1.0).
    divisi_count:
        Number of brass voices (2–5).
    breath_gap:
        Rest between notes to simulate breath (in beats).
    """

    name: str = "Brass Section Generator"
    articulation: str = "hit"
    voicing: str = "closed"
    intensity: float = 0.8
    divisi_count: int = 3
    ensemble_mode: str = "full"
    breath_gap: float = 0.25
    mute: str | None = None
    con_sordino: bool = False
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        articulation: str = "hit",
        voicing: str = "closed",
        intensity: float = 0.8,
        divisi_count: int = 3,
        ensemble_mode: str = "full",
        breath_gap: float = 0.25,
        mute: str | None = None,
        con_sordino: bool = False,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.articulation = articulation
        self.voicing = voicing
        self.intensity = max(0.0, min(1.0, intensity))
        self.divisi_count = max(2, min(5, divisi_count))
        self.ensemble_mode = ensemble_mode
        self.breath_gap = max(0.0, min(1.0, breath_gap))
        self.mute = mute
        self.con_sordino = con_sordino
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

        events = self._build_events(duration_beats)
        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None
        # Per-voice register offsets for divisi spread
        divisi_offsets = [0, 7, -12, 12, -7]

        # Map ensemble_mode to local div_count
        mode = getattr(self, "ensemble_mode", "full")
        if mode == "solo":
            div_count = 1
        elif mode == "chamber":
            div_count = 3
        elif mode == "section":
            div_count = 4
        else:  # tutti
            div_count = 5

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Voicing and instrument registers mapping — each divisi voice gets its own register offset
            voicing_sub = []
            for v_idx in range(div_count):
                voice_anchor = mid + divisi_offsets[v_idx % len(divisi_offsets)]
                raw_voicing = chord_pitches_closed(chord, voice_anchor)
                raw_voicing = [snap_to_scale(p, key) for p in raw_voicing]
                raw_voicing = sorted(raw_voicing, reverse=True)
                voicing_sub.append(raw_voicing[0] if raw_voicing else voice_anchor)

            # Place each voice in its corresponding instrument's natural register:
            # Voice 0 (highest): Trumpet (58-84)
            # Voice 1: French Horn (41-72)
            # Voice 2: Trombone (31-70)
            # Voice 3+: Tuba / Contrabass Trombone (29-65)
            processed_voicing = []
            for idx, p in enumerate(voicing_sub):
                if idx == 0:  # Trumpet
                    low_r, high_r = 58, 84
                elif idx == 1:  # French Horn
                    low_r, high_r = 41, 72
                elif idx == 2:  # Trombone
                    low_r, high_r = 31, 70
                else:  # Tuba
                    low_r, high_r = 29, 65

                while p < low_r:
                    p += 12
                while p > high_r:
                    p -= 12
                p = snap_to_scale(p, key)
                p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                processed_voicing.append(p)

            voicing = processed_voicing

            # Build expression CC data
            expression = {}
            if self.mute == "straight":
                expression[74] = 60
            elif self.mute == "harmon":
                if self.articulation in ("swell", "sustained"):
                    steps = 10
                    cc74_list = []
                    for s in range(steps + 1):
                        t_rel = (s / steps) * event.duration
                        val = int(50 + 45 * (s / steps))
                        cc74_list.append((t_rel, val))
                    expression[74] = cc74_list
                else:
                    expression[74] = 85

            if self.articulation == "swell":
                steps = 15
                cc11_list = []
                for s in range(steps + 1):
                    t_rel = (s / steps) * event.duration
                    val = int(30 + 90 * (s / steps)**1.5)
                    cc11_list.append((t_rel, val))
                expression[11] = cc11_list

            if self.articulation == "hit":
                for idx, p in enumerate(voicing):
                    vel = int(self.intensity * 110)
                    if self.con_sordino:
                        vel = int(vel * 0.7)
                    # Staggered physical entry delay based on instrument voice
                    inst_delay = 0.0 if idx == 0 else random.uniform(0.005, 0.015)
                    note_onset = max(0.0, event.onset + inst_delay)
                    note = NoteInfo(
                        pitch=p,
                        start=round(note_onset, 6),
                        duration=event.duration * 0.6,
                        velocity=max(1, min(127, vel)),
                    )
                    if expression:
                        note.expression = expression.copy()
                    notes.append(note)

            elif self.articulation == "swell":
                segments = 4
                seg_dur = event.duration / segments
                for idx, p in enumerate(voicing):
                    inst_delay = 0.0 if idx == 0 else random.uniform(0.008, 0.020)
                    for seg in range(segments):
                        t_frac = seg / max(segments - 1, 1)
                        vel = int(self.intensity * (40 + 80 * t_frac))
                        if self.con_sordino:
                            vel = int(vel * 0.7)
                        note_onset = max(0.0, event.onset + inst_delay + seg * seg_dur)
                        note = NoteInfo(
                            pitch=p,
                            start=round(note_onset, 6),
                            duration=seg_dur,
                            velocity=max(1, min(127, vel)),
                        )
                        if expression:
                            note.expression = expression.copy()
                        notes.append(note)

            elif self.articulation == "fanfare":
                # Ascending arpeggio with micro-staggering
                t = event.onset
                step = event.duration / max(len(voicing), 1)
                for idx, p in enumerate(voicing):
                    vel = int(self.intensity * (80 + idx * 10))
                    if self.con_sordino:
                        vel = int(vel * 0.7)
                    inst_delay = 0.0 if idx == 0 else random.uniform(0.004, 0.012)
                    note_onset = max(0.0, t + inst_delay)
                    note = NoteInfo(
                        pitch=p,
                        start=round(note_onset, 6),
                        duration=event.duration - idx * step,
                        velocity=max(1, min(127, vel)),
                    )
                    if expression:
                        note.expression = expression.copy()
                    notes.append(note)
                    t += step

            elif self.articulation == "sustained":
                for idx, p in enumerate(voicing):
                    vel = int(self.intensity * 90)
                    if self.con_sordino:
                        vel = int(vel * 0.7)
                    inst_delay = 0.0 if idx == 0 else random.uniform(0.008, 0.020)
                    note_onset = max(0.0, event.onset + inst_delay)
                    note = NoteInfo(
                        pitch=p,
                        start=round(note_onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, vel)),
                    )
                    if expression:
                        note.expression = expression.copy()
                    notes.append(note)

            elif self.articulation in ("falls", "doits"):
                for idx, p in enumerate(voicing):
                    vel = int(self.intensity * 95)
                    if self.con_sordino:
                        vel = int(vel * 0.7)
                    # Staggered physical entry delay based on instrument voice
                    inst_delay = 0.0
                    if idx == 1:    # French Horn
                        inst_delay = random.uniform(0.008, 0.018)
                    elif idx == 2:  # Trombone
                        inst_delay = random.uniform(0.012, 0.024)
                    elif idx >= 3:  # Tuba
                        inst_delay = random.uniform(0.018, 0.032)
                        
                    note_onset = max(0.0, event.onset + inst_delay)
                    
                    # Continuous pitch fall/doit modeled via pitch bend curves on a single note
                    note = NoteInfo(
                        pitch=p,
                        start=round(note_onset, 6),
                        duration=event.duration,
                        velocity=max(1, min(127, vel)),
                    )
                    
                    expr_copy = expression.copy() if expression else {}
                    direction = -1 if self.articulation == "falls" else 1
                    
                    # Pitch bend curve: flat for 70% of duration, then rapid slide in final 30%
                    slide_start_t = event.duration * 0.70
                    steps = 10
                    pb_list = []
                    for s in range(steps + 1):
                        progress = s / steps
                        t_rel = slide_start_t + progress * (event.duration - slide_start_t)
                        # Slide depth: 6 semitones = 4096 MIDI pitch bend value (direction * 4096)
                        val = int(direction * 4096 * progress)
                        pb_list.append((t_rel, val))
                        
                    # Prepend a 0.0 flat bend at note start and slide start
                    pb_curve = [(0.0, 0), (slide_start_t, 0)] + pb_list
                    expr_copy["pitch_bend"] = pb_curve
                    
                    note.expression = expr_copy
                    notes.append(note)
            else:
                raise ValueError(f"Unknown BrassSectionGenerator articulation: {self.articulation!r}. Valid: hit, swell, fanfare, sustained, falls, doits")

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(2.0, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += dur + self.breath_gap
        return events
