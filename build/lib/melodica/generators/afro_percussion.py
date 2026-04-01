"""
generators/afro_percussion.py — African percussion ensemble generator.

Layer: Application / Domain
Style: All African genres, world music, Afro fusion.

Dedicated African percussion instruments with authentic patterns:
  - Djembe (West African hand drum)
  - Congas (Cuban/African)
  - Shekere (gourd shaker)
  - Talking drum (pitched drum)
  - Udu (clay pot drum)
  - Kora-like patterns (harp-like)
  - Balafon patterns (xylophone)

Patterns:
    "west_african"  — West African (djembe, shekere)
    "cuban_afro"    — Cuban/African fusion (congas, bata)
    "south_african" — South African (marimba, djembe)
    "east_african"  — East African (taarab influenced)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


DJEMBE_HIGH = 60
DJEMBE_MID = 55
DJEMBE_LOW = 50
CONGA_HIGH = 62
CONGA_LOW = 56
SHEKERE = 70
UDU = 48
BALAFON_LOW = 72
BALAFON_HIGH = 96


@dataclass
class AfroPercussionGenerator(PhraseGenerator):
    """
    African percussion ensemble generator.

    ensemble:
        "west_african", "cuban_afro", "south_african", "east_african"
    density:
        Overall percussion density (0.0-1.0).
    include_pitched:
        Whether to include pitched percussion (balafon, marimba).
    call_response:
        Whether to include call-response patterns.
    swing:
        Swing amount for groove (0.5-0.75).
    """

    name: str = "Afro Percussion Generator"
    ensemble: str = "west_african"
    density: float = 0.6
    include_pitched: bool = True
    call_response: bool = True
    swing: float = 0.55
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        ensemble: str = "west_african",
        density: float = 0.6,
        include_pitched: bool = True,
        call_response: bool = True,
        swing: float = 0.55,
    ) -> None:
        super().__init__(params)
        self.ensemble = ensemble
        self.density = max(0.0, min(1.0, density))
        self.include_pitched = include_pitched
        self.call_response = call_response
        self.swing = max(0.5, min(0.75, swing))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        notes: list[NoteInfo] = []
        last_chord = chords[-1] if chords else None
        bar_start = 0.0

        while bar_start < duration_beats:
            if self.ensemble == "west_african":
                self._render_west_african(notes, bar_start, duration_beats, last_chord)
            elif self.ensemble == "cuban_afro":
                self._render_cuban(notes, bar_start, duration_beats, last_chord)
            elif self.ensemble == "south_african":
                self._render_south_african(notes, bar_start, duration_beats, last_chord)
            else:
                self._render_east_african(notes, bar_start, duration_beats, last_chord)
            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _render_west_african(self, notes, bar_start, total, chord):
        """Djembe patterns with shekere and optional balafon."""
        # Djembe pattern (12/8 feel compressed to 4/4)
        # Tone: open hit, Slap: sharp hit, Bass: low hit
        djembe_pattern = [
            (0.0, DJEMBE_LOW, 90, 0.3, "B"),  # Bass
            (0.5, DJEMBE_MID, 75, 0.2, "T"),  # Tone
            (1.0, DJEMBE_HIGH, 95, 0.2, "S"),  # Slap
            (1.5, DJEMBE_MID, 70, 0.2, "T"),
            (2.0, DJEMBE_LOW, 85, 0.3, "B"),
            (2.5, DJEMBE_HIGH, 90, 0.2, "S"),
            (3.0, DJEMBE_MID, 80, 0.2, "T"),
            (3.5, DJEMBE_HIGH, 70, 0.15, "S"),
        ]
        for off, pitch, vel, dur, _ in djembe_pattern:
            if random.random() > self.density:
                continue
            onset = bar_start + off
            if onset < total:
                v = vel + int(random.gauss(0, 8))
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(onset, 6),
                        duration=dur,
                        velocity=max(30, min(MIDI_MAX, v)),
                    )
                )

        # Shekere (constant eighth notes)
        for i in range(8):
            if random.random() < self.density * 0.7:
                onset = bar_start + i * 0.5
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=SHEKERE, start=round(onset, 6), duration=0.08, velocity=45)
                    )

        # Call-response: answered by pitched percussion
        if self.call_response and random.random() < 0.5:
            self._render_balafon_response(notes, bar_start, total, chord)

    def _render_cuban(self, notes, bar_start, total, chord):
        """Cuban conga patterns with bata influence."""
        conga_pattern = [
            (0.0, CONGA_LOW, 90, 0.25),
            (0.75, CONGA_HIGH, 80, 0.15),
            (1.0, CONGA_LOW, 85, 0.25),
            (1.5, CONGA_HIGH, 75, 0.15),
            (2.0, CONGA_LOW, 90, 0.25),
            (2.75, CONGA_HIGH, 80, 0.15),
            (3.0, CONGA_LOW, 85, 0.25),
            (3.5, CONGA_HIGH, 70, 0.15),
        ]
        for off, pitch, vel, dur in conga_pattern:
            if random.random() > self.density:
                continue
            onset = bar_start + off
            if onset < total:
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=dur, velocity=vel)
                )

    def _render_south_african(self, notes, bar_start, total, chord):
        """South African marimba + percussion."""
        # Marimba pattern
        if self.include_pitched and chord:
            root_pc = chord.root
            mid = 78
            pcs = [root_pc, (root_pc + 7) % 12, (root_pc + 3) % 12, root_pc]
            for i, off in enumerate([0.0, 0.5, 1.0, 1.5]):
                onset = bar_start + off
                if onset >= total:
                    continue
                pitch = nearest_pitch(pcs[i % len(pcs)], mid)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.4, velocity=70)
                )

        # Djembe
        for off in [0.0, 1.0, 2.0, 3.0]:
            if random.random() < self.density:
                onset = bar_start + off
                if onset < total:
                    notes.append(
                        NoteInfo(pitch=DJEMBE_LOW, start=round(onset, 6), duration=0.3, velocity=85)
                    )

    def _render_east_african(self, notes, bar_start, total, chord):
        """East African taarab-influenced percussion."""
        for i in range(16):
            if random.random() < self.density * 0.5:
                onset = bar_start + i * 0.25
                if onset >= total:
                    break
                pitch = random.choice([DJEMBE_MID, DJEMBE_HIGH, UDU])
                vel = 55 + random.randint(-10, 10)
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.1, velocity=vel)
                )

    def _render_balafon_response(self, notes, bar_start, total, chord):
        """Balafon (xylophone) response phrase."""
        if not chord:
            return
        root_pc = chord.root
        mid = 84
        pcs = [root_pc, (root_pc + 4) % 12, (root_pc + 7) % 12, (root_pc + 11) % 12]
        # Response starts on beat 2 or 3
        resp_start = bar_start + random.choice([1.0, 2.0])
        for i in range(4):
            onset = resp_start + i * 0.25
            if onset >= min(bar_start + 4.0, total):
                break
            pitch = nearest_pitch(pcs[i % len(pcs)], mid)
            notes.append(NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.2, velocity=65))
