"""
generators/highlife_guitar.py — Highlife / Afrobeat Guitar pattern generator.

Layer: Application / Domain
Style: Highlife, Afrobeat, Jùjú, Palm wine, Afro-rock.

Generates characteristic West African guitar patterns:
  - Palm-muted arpeggiated riffs
  - Interlocking guitar parts
  - Pentatonic melodies
  - Fela Kuti-style Afrobeat comping

Variants:
    "highlife"    — classic highlife guitar (bright, arpeggiated)
    "afrobeat"    — Fela Kuti style (rhythmic, driving)
    "juju"        — King Sunny Ade Jùjú style
    "palm_wine"   — Palm wine guitar (gentle, melodic)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at


@dataclass
class HighlifeGuitarGenerator(PhraseGenerator):
    """
    Highlife / Afrobeat Guitar pattern generator.

    variant:
        "highlife", "afrobeat", "juju", "palm_wine"
    riff_density:
        Density of guitar riff notes (0.0-1.0).
    palm_mute_ratio:
        Ratio of palm-muted notes (0.0-1.0).
    octave_doubling:
        Whether to double riffs at the octave.
    interlocking:
        Whether to generate interlocking two-guitar patterns.
    pentatonic_bias:
        Bias toward pentatonic scale (0.0-1.0).
    """

    name: str = "Highlife Guitar Generator"
    variant: str = "highlife"
    riff_density: float = 0.7
    palm_mute_ratio: float = 0.3
    octave_doubling: bool = True
    interlocking: bool = False
    pentatonic_bias: float = 0.6
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "highlife",
        riff_density: float = 0.7,
        palm_mute_ratio: float = 0.3,
        octave_doubling: bool = True,
        interlocking: bool = False,
        pentatonic_bias: float = 0.6,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.riff_density = max(0.0, min(1.0, riff_density))
        self.palm_mute_ratio = max(0.0, min(1.0, palm_mute_ratio))
        self.octave_doubling = octave_doubling
        self.interlocking = interlocking
        self.pentatonic_bias = max(0.0, min(1.0, pentatonic_bias))

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
        last_chord = chords[-1]
        bar_start = 0.0

        while bar_start < duration_beats:
            chord = chord_at(chords, bar_start)
            if chord is None:
                bar_start += 4.0
                continue

            self._render_riff(notes, bar_start, duration_beats, chord, key)
            if self.interlocking:
                self._render_interlocking(notes, bar_start, duration_beats, chord, key)

            bar_start += 4.0

        notes.sort(key=lambda n: n.start)
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _get_scale_pcs(self, key: Scale) -> list[int]:
        """Get scale pitch classes, biased toward pentatonic."""
        full = [int(d) for d in key.degrees()]
        if random.random() < self.pentatonic_bias:
            # Pentatonic: degrees 1, 2, 3, 5, 6
            if len(full) >= 6:
                return [full[0], full[1], full[2], full[4], full[5]]
        return full

    def _render_riff(self, notes, bar_start, total, chord, key):
        mid = 66  # Guitar register
        root_pc = chord.root
        scale_pcs = self._get_scale_pcs(key)

        if self.variant == "highlife":
            # Bright arpeggiated pattern
            offsets = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]
            prev = nearest_pitch(root_pc, mid)
            for off in offsets:
                if random.random() > self.riff_density:
                    continue
                onset = bar_start + off
                if onset >= total:
                    break
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                pitch = max(48, min(84, pitch))
                is_mute = random.random() < self.palm_mute_ratio
                vel = 65 if is_mute else 75
                dur = 0.3 if is_mute else 0.4
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=dur, velocity=vel)
                )
                if self.octave_doubling and not is_mute:
                    notes.append(
                        NoteInfo(
                            pitch=pitch + 12, start=round(onset, 6), duration=dur, velocity=vel - 15
                        )
                    )
                prev = pitch

        elif self.variant == "afrobeat":
            # Driving rhythmic pattern
            offsets = [0.0, 0.75, 1.5, 2.0, 2.75, 3.5]
            prev = nearest_pitch(root_pc, mid)
            for off in offsets:
                if random.random() > self.riff_density:
                    continue
                onset = bar_start + off
                if onset >= total:
                    break
                pc = root_pc if off in (0.0, 2.0) else random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                pitch = max(48, min(84, pitch))
                is_mute = random.random() < self.palm_mute_ratio
                vel = 80 if off in (0.0, 2.0) else 65
                notes.append(
                    NoteInfo(pitch=pitch, start=round(onset, 6), duration=0.3, velocity=vel)
                )
                prev = pitch

        elif self.variant == "juju":
            # Jùjú: cascading arpeggios
            prev = nearest_pitch(root_pc, mid)
            for i in range(16):
                if random.random() > self.riff_density:
                    continue
                onset = bar_start + i * 0.25
                if onset >= total:
                    break
                pc = scale_pcs[i % len(scale_pcs)]
                pitch = nearest_pitch(pc, prev)
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, pitch)),
                        start=round(onset, 6),
                        duration=0.2,
                        velocity=60,
                    )
                )
                prev = pitch

        else:  # palm_wine
            # Gentle, melodic
            offsets = [0.0, 1.0, 2.0, 3.0]
            prev = nearest_pitch(root_pc, mid)
            for off in offsets:
                onset = bar_start + off
                if onset >= total:
                    break
                pc = random.choice(scale_pcs)
                pitch = nearest_pitch(pc, prev)
                notes.append(
                    NoteInfo(
                        pitch=max(48, min(84, pitch)),
                        start=round(onset, 6),
                        duration=0.9,
                        velocity=55,
                    )
                )
                prev = pitch

    def _render_interlocking(self, notes, bar_start, total, chord, key):
        """Second guitar part — interlocking with the first."""
        mid = 72
        root_pc = chord.root
        scale_pcs = self._get_scale_pcs(key)
        # Offset by a sixteenth from main pattern
        for i in range(8):
            if random.random() > self.riff_density * 0.6:
                continue
            onset = bar_start + i * 0.5 + 0.25
            if onset >= total:
                break
            pc = random.choice(scale_pcs)
            pitch = nearest_pitch(pc, mid)
            notes.append(
                NoteInfo(
                    pitch=max(48, min(84, pitch)), start=round(onset, 6), duration=0.3, velocity=60
                )
            )
