"""
generators/synthwave.py — Synthwave / Retrowave pattern generator.

Layer: Application / Domain
Style: Synthwave, retrowave, outrun, vaporwave, darksynth.

Generates characteristic synthwave elements:
  - Arpeggiated synth bass
  - Gated pad chords
  - Retro drum machine patterns
  - Lead synth melodies

Variants:
    "outrun"     — outrun (driving, energetic)
    "chillwave"  — chillwave (slower, atmospheric)
    "darksynth"  — darksynth (aggressive, dark)
    "retro_pop"  — 80s retro pop
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
HH_CLOSED = 42
HH_OPEN = 46
CLAP = 39
CRASH = 49


@dataclass
class SynthwaveGenerator(PhraseGenerator):
    """
    Synthwave / Retrowave pattern generator.

    variant:
        "outrun", "chillwave", "darksynth", "retro_pop"
    arp_pattern:
        "up", "down", "updown", "octave" — bass arpeggio pattern.
    gated_pads:
        Whether to include gated reverb pad chords.
    include_lead:
        Whether to include lead synth melody.
    gate_rate:
        Rate of gate effect in beats (0.25 = 16th, 0.5 = 8th).
    """

    name: str = "Synthwave Generator"
    variant: str = "outrun"
    arp_pattern: str = "up"
    gated_pads: bool = True
    include_lead: bool = True
    gate_rate: float = 0.5
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "outrun",
        arp_pattern: str = "up",
        gated_pads: bool = True,
        include_lead: bool = True,
        gate_rate: float = 0.5,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.arp_pattern = arp_pattern
        self.gated_pads = gated_pads
        self.include_lead = include_lead
        self.gate_rate = max(0.125, min(1.0, gate_rate))

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
            self._render_drums(notes, bar_start, duration_beats)
            self._render_bass_arp(notes, bar_start, duration_beats, chord, low)
            if self.gated_pads:
                self._render_gated_pads(notes, bar_start, duration_beats, chord)
            if self.include_lead:
                self._render_lead(notes, bar_start, duration_beats, chord, key)
            bar_start += 4.0
        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_drums(self, notes, bar_start, total):
        for beat in range(4):
            onset = bar_start + beat
            if onset >= total:
                break
            notes.append(NoteInfo(pitch=KICK, start=round(onset, 6), duration=0.3, velocity=110))
        for beat in [1, 3]:
            onset = bar_start + beat
            if onset < total:
                notes.append(
                    NoteInfo(pitch=SNARE, start=round(onset, 6), duration=0.2, velocity=105)
                )
                notes.append(
                    NoteInfo(pitch=CLAP, start=round(onset, 6), duration=0.15, velocity=90)
                )
        for i in range(8):
            onset = bar_start + i * 0.5
            if onset >= total:
                break
            notes.append(
                NoteInfo(
                    pitch=HH_CLOSED,
                    start=round(onset, 6),
                    duration=0.1,
                    velocity=65 if i % 2 == 0 else 50,
                )
            )

    def _render_bass_arp(self, notes, bar_start, total, chord, low):
        pitch = max(low, min(low + 18, nearest_pitch(chord.root, low + 12)))
        fifth = nearest_pitch((chord.root + 7) % 12, pitch)
        octave = pitch + 12
        if self.arp_pattern == "up":
            seq = [pitch, fifth, octave, fifth]
        elif self.arp_pattern == "down":
            seq = [octave, fifth, pitch, fifth]
        elif self.arp_pattern == "updown":
            seq = [pitch, fifth, octave, fifth, pitch, fifth, octave, fifth]
        else:
            seq = [pitch, octave, pitch, octave]
        sub = 0.25 if self.variant == "darksynth" else 0.5
        t = bar_start
        idx = 0
        while t < min(bar_start + 4.0, total):
            notes.append(
                NoteInfo(
                    pitch=seq[idx % len(seq)], start=round(t, 6), duration=sub * 0.8, velocity=85
                )
            )
            t += sub
            idx += 1

    def _render_gated_pads(self, notes, bar_start, total, chord):
        mid = 60
        pcs = chord.pitch_classes()[:3]
        t = bar_start
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.6:
                for pc in pcs:
                    pitch = nearest_pitch(pc, mid)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(t, 6),
                            duration=self.gate_rate * 0.7,
                            velocity=55,
                        )
                    )
            t += self.gate_rate

    def _render_lead(self, notes, bar_start, total, chord, key):
        mid = 72
        pcs = [int(d) for d in key.degrees()]
        t = bar_start
        prev = mid
        while t < min(bar_start + 4.0, total):
            if random.random() < 0.6:
                pc = random.choice(pcs)
                pitch = nearest_pitch(pc, prev)
                dur = random.choice([0.5, 1.0])
                notes.append(
                    NoteInfo(
                        pitch=max(60, min(84, pitch)), start=round(t, 6), duration=dur, velocity=80
                    )
                )
                prev = pitch
            t += 0.5
