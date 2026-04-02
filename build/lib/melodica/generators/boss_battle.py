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
generators/boss_battle.py — Boss battle music generator.

Layer: Application / Domain
Style: Boss battles, RPG, action games.

Generates epic boss battle music with phase-based escalation:
  - Phase 1 (intro): boss appears, dramatic entrance
  - Phase 2 (build): intensity rises, boss reveals patterns
  - Phase 3 (fight): full combat, driving rhythm
  - Phase 4 (climax): desperate final stand

Each phase has characteristic:
  - Density and velocity
  - Brass/choir presence
  - Percussion drive
  - Key/modal shifts

Variants:
    "epic"        — standard epic boss (orchestral)
    "dark_lord"   — dark, villainous boss
    "dragon"      — primal, elemental boss
    "final"       — final boss (maximum drama)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


KICK = 36
SNARE = 38
TIMPANI = 47
CRASH = 49
TAM_TAM = 52


@dataclass
class BossBattleGenerator(PhraseGenerator):
    """
    Boss battle music generator with phase-based escalation.

    phase:
        "intro", "build", "fight", "climax"
    variant:
        "epic", "dark_lord", "dragon", "final"
    choir_stabs:
        Whether to include choir chord stabs.
    brass_fanfare:
        Whether to include brass fanfare hits.
    timpani_drive:
        Whether to include driving timpani.
    """

    name: str = "Boss Battle Generator"
    phase: str = "fight"
    variant: str = "epic"
    choir_stabs: bool = True
    brass_fanfare: bool = True
    timpani_drive: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        phase: str = "fight",
        variant: str = "epic",
        choir_stabs: bool = True,
        brass_fanfare: bool = True,
        timpani_drive: bool = True,
    ) -> None:
        super().__init__(params)
        self.phase = phase
        self.variant = variant
        self.choir_stabs = choir_stabs
        self.brass_fanfare = brass_fanfare
        self.timpani_drive = timpani_drive

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
        low = max(24, self.params.key_range_low)
        last_chord = chords[-1]
        bar_start = 0.0

        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            self._render_bass(notes, bar_start, duration_beats, chord, low)
            self._render_strings(notes, bar_start, duration_beats, chord)
            if self.timpani_drive:
                self._render_percussion(notes, bar_start, duration_beats)
            if self.brass_fanfare:
                self._render_brass(notes, bar_start, duration_beats, chord)
            if self.choir_stabs:
                self._render_choir(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _phase_vel(self, base: int) -> int:
        multiplier = {"intro": 0.6, "build": 0.75, "fight": 0.9, "climax": 1.0}.get(self.phase, 0.9)
        return min(MIDI_MAX, int(base * multiplier))

    def _phase_density(self) -> float:
        return {"intro": 0.3, "build": 0.5, "fight": 0.8, "climax": 1.0}.get(self.phase, 0.8)

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        fifth = nearest_pitch((chord.root + 7) % 12, pitch)
        if self.phase == "intro":
            if bar_start < total:
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(bar_start, 6),
                        duration=3.8,
                        velocity=self._phase_vel(70),
                    )
                )
        elif self.phase == "build":
            for beat in range(4):
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=0.8,
                            velocity=self._phase_vel(80),
                        )
                    )
        else:
            for beat in range(4):
                onset = bar_start + beat
                if onset < total:
                    p = pitch if beat % 2 == 0 else fifth
                    notes.append(
                        NoteInfo(
                            pitch=p,
                            start=round(onset, 6),
                            duration=0.6,
                            velocity=self._phase_vel(95),
                        )
                    )

    def _render_strings(self, notes, bar_start, total, chord):
        mid = 60
        pcs = chord.pitch_classes()[:3]
        dens = self._phase_density()
        if self.phase == "intro":
            sub = 0.5
        elif self.phase == "climax":
            sub = 0.125
        else:
            sub = 0.25
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            if random.random() < dens:
                pc = pcs[idx % len(pcs)]
                pitch = nearest_pitch(pc, mid)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(t, 6),
                        duration=sub * 0.8,
                        velocity=self._phase_vel(65),
                    )
                )
            t += sub
            idx += 1

    def _render_percussion(self, notes, bar_start, total):
        if self.phase == "intro":
            if bar_start < total:
                notes.append(
                    NoteInfo(
                        pitch=TIMPANI,
                        start=round(bar_start, 6),
                        duration=1.0,
                        velocity=self._phase_vel(60),
                    )
                )
        elif self.phase == "build":
            for beat in [0, 2]:
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=TIMPANI,
                            start=round(onset, 6),
                            duration=0.5,
                            velocity=self._phase_vel(75),
                        )
                    )
        else:
            vel = self._phase_vel(100)
            for beat in range(4):
                onset = bar_start + beat
                if onset >= total:
                    break
                notes.append(
                    NoteInfo(pitch=TIMPANI, start=round(onset, 6), duration=0.3, velocity=vel)
                )
                if beat == 0:
                    notes.append(
                        NoteInfo(pitch=CRASH, start=round(onset, 6), duration=0.8, velocity=vel)
                    )
            if self.phase == "climax":
                notes.append(
                    NoteInfo(
                        pitch=TAM_TAM, start=round(bar_start, 6), duration=2.0, velocity=vel - 10
                    )
                )

    def _render_brass(self, notes, bar_start, total, chord):
        if self.phase in ("intro",):
            return
        mid = 60
        root = nearest_pitch(chord.root, mid)
        fifth = nearest_pitch((chord.root + 7) % 12, root)
        vel = self._phase_vel(90)
        if self.phase == "build":
            for beat in [0, 2]:
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=root, start=round(onset, 6), duration=0.5, velocity=vel)
                    )
        elif self.phase == "fight":
            for beat in [0, 2]:
                onset = bar_start + beat
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=root, start=round(onset, 6), duration=0.5, velocity=vel)
                    )
                    notes.append(
                        NoteInfo(
                            pitch=fifth, start=round(onset, 6), duration=0.5, velocity=vel - 10
                        )
                    )
        else:  # climax — fanfare
            fanfare_pitches = [root, root + 12, fifth, root + 12, fifth + 12]
            for i, p in enumerate(fanfare_pitches):
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=max(48, min(84, p)),
                            start=round(onset, 6),
                            duration=0.4,
                            velocity=vel,
                        )
                    )

    def _render_choir(self, notes, bar_start, total, chord):
        mid = 60
        pcs = chord.pitch_classes()[:4]
        vel = self._phase_vel(75)
        if self.phase in ("fight", "climax"):
            for beat in [0, 2]:
                onset = bar_start + beat
                if onset < total:
                    for pc in pcs:
                        pitch = nearest_pitch(pc, mid)
                        notes.append(
                            NoteInfo(pitch=pitch, start=round(onset, 6), duration=1.0, velocity=vel)
                        )
