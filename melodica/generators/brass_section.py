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
    breath_gap: float = 0.25
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
        breath_gap: float = 0.25,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.articulation = articulation
        self.voicing = voicing
        self.intensity = max(0.0, min(1.0, intensity))
        self.divisi_count = max(2, min(5, divisi_count))
        self.breath_gap = max(0.0, min(1.0, breath_gap))
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

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            voicing = chord_pitches_closed(chord, mid)
            voicing = [snap_to_scale(p, key) for p in voicing]
            voicing = voicing[: self.divisi_count]

            if self.articulation == "hit":
                for p in voicing:
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    vel = int(self.intensity * 110)
                    # Marcato: loud attack, quick decay
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=event.duration * 0.6,
                            velocity=max(1, min(127, vel)),
                        )
                    )

            elif self.articulation == "swell":
                for p in voicing:
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    vel = int(self.intensity * 50)  # Start soft
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=event.duration,
                            velocity=max(1, min(127, vel)),
                        )
                    )

            elif self.articulation == "fanfare":
                # Ascending arpeggio
                t = event.onset
                step = event.duration / max(len(voicing), 1)
                for i, p in enumerate(voicing):
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    vel = int(self.intensity * (80 + i * 10))
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(t, 6),
                            duration=event.duration - i * step,
                            velocity=max(1, min(127, vel)),
                        )
                    )
                    t += step

            elif self.articulation == "sustained":
                for p in voicing:
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    vel = int(self.intensity * 90)
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=event.duration,
                            velocity=max(1, min(127, vel)),
                        )
                    )

            elif self.articulation in ("falls", "doits"):
                for p in voicing:
                    p = max(self.params.key_range_low, min(self.params.key_range_high, p))
                    vel = int(self.intensity * 95)
                    # Main note
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(event.onset, 6),
                            duration=event.duration * 0.7,
                            velocity=max(1, min(127, vel)),
                        )
                    )
                    # Fall or doit
                    direction = -1 if self.articulation == "falls" else 1
                    t = event.onset + event.duration * 0.7
                    for s in range(4):
                        fall_p = p + direction * (s + 1)
                        fall_p = max(
                            self.params.key_range_low, min(self.params.key_range_high, fall_p)
                        )
                        notes.append(
                            NoteInfo(
                                pitch=fall_p,
                                start=round(t, 6),
                                duration=0.1,
                                velocity=max(1, int(vel * 0.7 - s * 5)),
                            )
                        )
                        t += 0.1

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
