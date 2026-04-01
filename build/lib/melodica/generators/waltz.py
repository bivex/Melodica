"""
generators/waltz.py — Waltz accompaniment generator.

Layer: Application / Domain
Style: Classical waltz, Viennese waltz, jazz waltz.

The waltz pattern in 3/4 time:
    Beat 1: bass note (root)
    Beat 2: chord voicing
    Beat 3: chord voicing (or bass fifth)

Variants:
    "viennese"  — classic Viennese waltz (oom-pah-pah)
    "jazz"      — jazz waltz with walking bass feel
    "romantic"  — Chopin-style waltz with arpeggiated chords
    "modern"    — contemporary waltz (syncopated)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_pitches_closed, chord_at


@dataclass
class WaltzGenerator(PhraseGenerator):
    """
    Waltz accompaniment pattern generator (3/4 time).

    variant:
        "viennese", "jazz", "romantic", "modern"
    include_bass_octave:
        Double bass at octave below.
    staccato_chords:
        Play chords short (characteristic of waltz).
    """

    name: str = "Waltz Generator"
    variant: str = "viennese"
    include_bass_octave: bool = True
    staccato_chords: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "viennese",
        include_bass_octave: bool = True,
        staccato_chords: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.include_bass_octave = include_bass_octave
        self.staccato_chords = staccato_chords
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
        low = max(28, self.params.key_range_low)
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        prev_bass = low + 12
        last_chord: ChordLabel | None = None

        t = 0.0
        beat = 0
        while t < duration_beats:
            chord = chord_at(chords, t)
            if chord is None:
                t += 1.0
                beat += 1
                continue
            last_chord = chord

            beat_in_bar = beat % 3
            vel = self._velocity(beat_in_bar)

            if self.variant == "viennese":
                if beat_in_bar == 0:
                    # Bass on 1
                    bass = nearest_pitch(chord.root, prev_bass)
                    bass = max(low, min(mid - 5, bass))
                    notes.append(
                        NoteInfo(pitch=bass, start=round(t, 6), duration=0.9, velocity=vel)
                    )
                    if self.include_bass_octave:
                        notes.append(
                            NoteInfo(
                                pitch=max(low, bass - 12),
                                start=round(t, 6),
                                duration=0.9,
                                velocity=int(vel * 0.7),
                            )
                        )
                    prev_bass = bass
                else:
                    # Chord on 2 and 3
                    dur = 0.35 if self.staccato_chords else 0.85
                    voicing = chord_pitches_closed(chord, mid)
                    for p in voicing:
                        notes.append(
                            NoteInfo(pitch=p, start=round(t, 6), duration=dur, velocity=vel)
                        )

            elif self.variant == "jazz":
                if beat_in_bar == 0:
                    bass = nearest_pitch(chord.root, prev_bass)
                    bass = max(low, min(mid - 5, bass))
                    notes.append(
                        NoteInfo(pitch=bass, start=round(t, 6), duration=0.9, velocity=vel)
                    )
                    prev_bass = bass
                elif beat_in_bar == 1:
                    # Chord on 2
                    voicing = chord_pitches_closed(chord, mid)
                    for p in voicing:
                        notes.append(
                            NoteInfo(
                                pitch=p, start=round(t, 6), duration=0.4, velocity=int(vel * 0.9)
                            )
                        )
                else:
                    # Chord on 3
                    voicing = chord_pitches_closed(chord, mid)
                    for p in voicing:
                        notes.append(
                            NoteInfo(
                                pitch=p, start=round(t, 6), duration=0.4, velocity=int(vel * 0.85)
                            )
                        )

            elif self.variant == "romantic":
                if beat_in_bar == 0:
                    bass = nearest_pitch(chord.root, prev_bass)
                    bass = max(low, min(mid - 5, bass))
                    notes.append(
                        NoteInfo(pitch=bass, start=round(t, 6), duration=0.9, velocity=vel)
                    )
                    prev_bass = bass
                else:
                    # Arpeggiated chord
                    voicing = chord_pitches_closed(chord, mid)
                    for i, p in enumerate(voicing):
                        notes.append(
                            NoteInfo(
                                pitch=p, start=round(t + i * 0.08, 6), duration=0.7, velocity=vel
                            )
                        )

            elif self.variant == "modern":
                # Syncopated
                if beat_in_bar == 0:
                    bass = nearest_pitch(chord.root, prev_bass)
                    bass = max(low, min(mid - 5, bass))
                    notes.append(
                        NoteInfo(pitch=bass, start=round(t, 6), duration=0.9, velocity=vel)
                    )
                    prev_bass = bass
                elif beat_in_bar == 1:
                    # Anticipated chord
                    voicing = chord_pitches_closed(chord, mid)
                    for p in voicing:
                        notes.append(
                            NoteInfo(pitch=p, start=round(t + 0.3, 6), duration=0.3, velocity=vel)
                        )
                else:
                    voicing = chord_pitches_closed(chord, mid)
                    for p in voicing:
                        notes.append(
                            NoteInfo(pitch=p, start=round(t, 6), duration=0.8, velocity=vel)
                        )

            t += 1.0
            beat += 1

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _velocity(self, beat_in_bar: int) -> int:
        base = int(60 + self.params.density * 30)
        if beat_in_bar == 0:
            return min(127, int(base * 1.15))
        return int(base * 0.9)
