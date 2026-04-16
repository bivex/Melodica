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
generators/reggae_skank.py — Reggae skank / offbeat rhythm generator.

Layer: Application / Domain
Style: Reggae, ska, dub, dancehall.

The "skank" is the characteristic offbeat guitar/keyboard chop in reggae:
chords played on the "and" of each beat (the upbeats), creating the
signature reggae groove.  In ska the same pattern is played faster.

Variants:
    "skank"      — standard reggae offbeat chop
    "ska"        — faster ska upstroke pattern
    "one_drop"   — one-drop rhythm (emphasis on beat 3)
    "rockers"    — steppers/rockers (four-on-the-floor bass + skank)
    "dub"        — sparse dub pattern (beat 3 emphasis, long reverb feel)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_pitches_closed, chord_at, snap_to_scale


@dataclass
class ReggaeSkankGenerator(PhraseGenerator):
    """
    Reggae skank offbeat rhythm generator.

    variant:
        "skank", "ska", "one_drop", "rockers", "dub"
    staccato:
        Play chords very short (staccato chop).
    mute_probability:
        Probability of a palm-muted (dead) chop.
    """

    name: str = "Reggae Skank Generator"
    variant: str = "skank"
    staccato: bool = True
    mute_probability: float = 0.1
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "skank",
        staccato: bool = True,
        mute_probability: float = 0.1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.staccato = staccato
        self.mute_probability = max(0.0, min(1.0, mute_probability))
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

            if not self._should_play(event.onset):
                continue

            voicing = chord_pitches_closed(chord, mid)
            is_muted = random.random() < self.mute_probability
            dur = event.duration * 0.2 if self.staccato else event.duration * 0.6
            vel = self._velocity()

            if is_muted:
                vel = int(vel * 0.5)
                dur *= 0.3

            for p in voicing:
                notes.append(
                    NoteInfo(
                        pitch=snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, p)), key),
                        start=round(event.onset, 6),
                        duration=dur,
                        velocity=max(1, min(127, vel)),
                    )
                )

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _should_play(self, onset: float) -> bool:
        beat_in_bar = onset % 4.0

        if self.variant == "skank":
            # Play on upbeats (&1, &2, &3, &4)
            frac = beat_in_bar % 1.0
            return 0.4 < frac < 0.6

        elif self.variant == "ska":
            # More upstrokes, faster
            frac = beat_in_bar % 1.0
            return 0.4 < frac < 0.6 or 0.9 < frac < 1.0

        elif self.variant == "one_drop":
            # Emphasis on beat 3, skip beats 1 and 2
            if 2.5 < beat_in_bar < 3.5:
                return True
            frac = beat_in_bar % 1.0
            return 0.4 < frac < 0.6

        elif self.variant == "rockers":
            # Play on every upbeat + bass on downbeat
            frac = beat_in_bar % 1.0
            return 0.4 < frac < 0.6 or beat_in_bar < 0.2

        elif self.variant == "dub":
            # Very sparse: only beat 3 and one upbeat
            if 2.5 < beat_in_bar < 3.5:
                return True
            if 0.4 < beat_in_bar < 0.6:
                return True
            return False

        return True

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Fine grid to allow pattern selection
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=0.4))
            t += 0.5
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 30)
