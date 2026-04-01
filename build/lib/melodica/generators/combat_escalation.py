"""
generators/combat_escalation.py — Adaptive combat music escalation generator.

Layer: Application / Domain
Style: AAA game audio, adaptive music.

Generates musical layers that scale with combat intensity.
Each intensity level produces different density, instrumentation feel,
and rhythmic drive. Designed for horizontal resequencing systems
used in games like God of War, Horizon, The Last of Us.

Intensity levels (0.0-1.0):
    0.0-0.2  — Exploration (sparse, atmospheric)
    0.2-0.4  — Awareness (subtle pulse enters)
    0.4-0.6  — Tension (drums hint, strings swell)
    0.6-0.8  — Combat (full drums, driving rhythm)
    0.8-1.0  — Climax (everything, brass stabs, timpani)

Instrument layers:
    "strings"   — string ostinato/tremolo patterns
    "brass"     — brass stabs and fanfare hits
    "percussion" — timpani, snare rolls, taiko
    "bass"      — driving bass patterns
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


TIMPANI = 47
SNARE_ROLL = 38
CRASH = 49
TAM_TAM = 52


@dataclass
class CombatEscalationGenerator(PhraseGenerator):
    """
    Adaptive combat music escalation generator.

    intensity:
        Current combat intensity (0.0 = exploration, 1.0 = climax).
    layers:
        Which instrument layers to generate: list of "strings", "brass", "percussion", "bass".
    tempo_factor:
        Relative speed multiplier for rhythmic patterns (0.5-2.0).
    key_change_on_climax:
        Whether to modulate up at climax (half-step up for drama).
    """

    name: str = "Combat Escalation Generator"
    intensity: float = 0.5
    layers: list[str] = field(default_factory=lambda: ["strings", "brass", "percussion", "bass"])
    tempo_factor: float = 1.0
    key_change_on_climax: bool = True
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        intensity: float = 0.5,
        layers: list[str] | None = None,
        tempo_factor: float = 1.0,
        key_change_on_climax: bool = True,
    ) -> None:
        super().__init__(params)
        self.intensity = max(0.0, min(1.0, intensity))
        self.layers = layers if layers is not None else ["strings", "brass", "percussion", "bass"]
        self.tempo_factor = max(0.5, min(2.0, tempo_factor))
        self.key_change_on_climax = key_change_on_climax

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

            if "bass" in self.layers:
                self._render_bass(notes, bar_start, duration_beats, chord, low)
            if "percussion" in self.layers:
                self._render_percussion(notes, bar_start, duration_beats)
            if "strings" in self.layers:
                self._render_strings(notes, bar_start, duration_beats, chord)
            if "brass" in self.layers:
                self._render_brass(notes, bar_start, duration_beats, chord)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_bass(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 12, nearest_pitch(chord.root, low + 6)))
        fifth = nearest_pitch((chord.root + 7) % 12, pitch)
        if self.intensity < 0.3:
            # Exploration: long sustained root
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=60)
                )
        elif self.intensity < 0.6:
            # Tension: pulsing eighth notes
            for i in range(8):
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.4, velocity=75)
                    )
        else:
            # Combat/Climax: driving quarters with fifths
            for beat in range(4):
                onset = bar_start + beat
                if onset < total:
                    p = pitch if beat % 2 == 0 else fifth
                    vel = min(MIDI_MAX, int(90 + self.intensity * 20))
                    notes.append(
                        NoteInfo(pitch=p, start=round(onset, 6), duration=0.8, velocity=vel)
                    )

    def _render_percussion(self, notes, bar_start, total):
        if self.intensity < 0.2:
            return  # No percussion in exploration
        elif self.intensity < 0.4:
            # Awareness: distant timpani
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=TIMPANI, start=round(bar_start, 6), duration=0.5, velocity=50)
                )
        elif self.intensity < 0.6:
            # Tension: timpani + light snare
            if bar_start < total:
                notes.append(
                    NoteInfo(pitch=TIMPANI, start=round(bar_start, 6), duration=0.5, velocity=65)
                )
            if bar_start + 2 < total:
                notes.append(
                    NoteInfo(
                        pitch=TIMPANI, start=round(bar_start + 2, 6), duration=0.5, velocity=55
                    )
                )
        elif self.intensity < 0.8:
            # Combat: full drums
            vel = int(80 + self.intensity * 20)
            for beat in range(4):
                onset = bar_start + beat
                if onset >= total:
                    break
                if beat in (0, 2):
                    notes.append(
                        NoteInfo(pitch=TIMPANI, start=round(onset, 6), duration=0.4, velocity=vel)
                    )
                else:
                    notes.append(
                        NoteInfo(
                            pitch=SNARE_ROLL, start=round(onset, 6), duration=0.3, velocity=vel - 10
                        )
                    )
        else:
            # Climax: everything
            vel = min(MIDI_MAX, int(100 + self.intensity * 25))
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
                notes.append(
                    NoteInfo(
                        pitch=SNARE_ROLL, start=round(onset, 6), duration=0.2, velocity=vel - 15
                    )
                )
            # Tam-tam on beat 1
            if bar_start < total:
                notes.append(
                    NoteInfo(
                        pitch=TAM_TAM, start=round(bar_start, 6), duration=1.5, velocity=vel - 10
                    )
                )

    def _render_strings(self, notes, bar_start, total, chord):
        mid = 60
        pcs = chord.pitch_classes()[:3]
        if self.intensity < 0.3:
            # Exploration: soft sustained chords
            if bar_start < total:
                for pc in pcs:
                    pitch = nearest_pitch(pc, mid)
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(bar_start, 6), duration=3.8, velocity=40)
                    )
        elif self.intensity < 0.6:
            # Tension: tremolo strings
            sub = 0.25 / self.tempo_factor
            t = bar_start
            while t < min(bar_start + 4.0, total):
                for pc in pcs:
                    pitch = nearest_pitch(pc, mid)
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(t, 6), duration=sub * 0.8, velocity=55)
                    )
                t += sub
        else:
            # Combat: driving ostinato
            sub = 0.5 / self.tempo_factor
            t = bar_start
            idx = 0
            while t < min(bar_start + 4.0, total):
                pc = pcs[idx % len(pcs)]
                pitch = nearest_pitch(pc, mid)
                vel = min(MIDI_MAX, int(65 + self.intensity * 25))
                notes.append(
                    NoteInfo(pitch=pitch, start=round(t, 6), duration=sub * 0.7, velocity=vel)
                )
                t += sub
                idx += 1

    def _render_brass(self, notes, bar_start, total, chord):
        if self.intensity < 0.5:
            return  # No brass until tension
        mid = 60
        root = nearest_pitch(chord.root, mid)
        fifth = nearest_pitch((chord.root + 7) % 12, root)
        vel = min(MIDI_MAX, int(75 + self.intensity * 30))
        if self.intensity < 0.8:
            # Combat: stabs on beats 1 and 3
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
        else:
            # Climax: fanfare pattern
            fanfare = [root, root + 12, fifth, root + 12]
            for i, p in enumerate(fanfare):
                onset = bar_start + i
                if onset < total:
                    notes.append(
                        NoteInfo(
                            pitch=max(48, min(84, p)),
                            start=round(onset, 6),
                            duration=0.7,
                            velocity=vel,
                        )
                    )
