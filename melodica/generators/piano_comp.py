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
generators/piano_comp.py — Jazz/pop piano comping generator.

Layer: Application / Domain

Shell voicings = root + 3rd/7th. Jazz comp places chords on offbeats.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale, MIDI_MAX
from melodica.utils import nearest_pitch, chord_at, snap_to_scale


COMP_STYLES = {"jazz", "pop", "bossa", "waltz"}
VOICING_TYPES = {"shell", "rootless", "close"}
ACCENT_PATTERNS = {"2_4", "syncopated", "charleston"}

_STYLE_RHYTHMS: dict[str, list[float]] = {
    "jazz": [0.5, 1.5, 2.5, 3.5],
    "pop": [0.0, 1.0, 2.0, 3.0],
    "bossa": [0.0, 0.75, 1.5, 2.5, 3.0],
    "waltz": [0.0, 1.0, 2.0],
}

_ACCENT_MAP: dict[str, list[float]] = {
    "2_4": [0.8, 1.2, 0.8, 1.2],
    "syncopated": [1.1, 0.7, 1.0, 0.9, 1.15],
    "charleston": [1.2, 0.6, 0.8, 1.0, 0.7],
}


@dataclass
class PianoCompGenerator(PhraseGenerator):
    name: str = "Piano Comp"
    comp_style: str = "jazz"
    voicing_type: str = "shell"
    accent_pattern: str = "2_4"
    chord_density: float = 0.7
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        comp_style: str = "jazz",
        voicing_type: str = "shell",
        accent_pattern: str = "2_4",
        chord_density: float = 0.7,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if comp_style not in COMP_STYLES:
            raise ValueError(f"comp_style must be one of {COMP_STYLES}; got {comp_style!r}")
        if voicing_type not in VOICING_TYPES:
            raise ValueError(f"voicing_type must be one of {VOICING_TYPES}; got {voicing_type!r}")
        if accent_pattern not in ACCENT_PATTERNS:
            raise ValueError(
                f"accent_pattern must be one of {ACCENT_PATTERNS}; got {accent_pattern!r}"
            )
        self.comp_style = comp_style
        self.voicing_type = voicing_type
        self.accent_pattern = accent_pattern
        self.chord_density = max(0.0, min(1.0, chord_density))
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
        last_chord: ChordLabel | None = None
        accents = _ACCENT_MAP.get(self.accent_pattern, [1.0, 0.8, 1.0, 0.8])
        prev_pitches: list[int] = []

        for idx, event in enumerate(events):
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord
            pitches = self._build_voicing(chord, prev_pitches)
            if not pitches:
                continue
            prev_pitches = pitches
            accent = accents[idx % len(accents)]
            vel = int(self._velocity() * event.velocity_factor * accent)
            for pitch in pitches:
                pitch = snap_to_scale(max(self.params.key_range_low, min(self.params.key_range_high, pitch)), key)
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(0, min(MIDI_MAX, vel)),
                    )
                )
        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
                last_pitches=prev_pitches,
            )
        return notes

    def _build_voicing(self, chord: ChordLabel, prev_pitches: list[int]) -> list[int]:
        anchor = (
            prev_pitches[0]
            if prev_pitches
            else (self.params.key_range_low + self.params.key_range_high) // 2
        )
        root_pc = chord.bass if chord.bass is not None else chord.root
        pcs = chord.pitch_classes()

        if self.voicing_type == "shell":
            target_pcs = self._shell_pcs(chord, root_pc, pcs)
        elif self.voicing_type == "rootless":
            target_pcs = self._rootless_pcs(chord, root_pc, pcs)
        else:
            target_pcs = list(pcs)

        pitches = []
        for pc in target_pcs:
            p = nearest_pitch(int(pc), anchor)
            if self.params.key_range_low <= p <= self.params.key_range_high:
                pitches.append(p)
        if self.chord_density < 1.0 and len(pitches) > 2:
            keep = max(2, int(len(pitches) * self.chord_density))
            pitches = sorted(pitches)[:keep]
        return sorted(pitches)

    def _shell_pcs(self, chord: ChordLabel, root_pc: int, pcs: list[int]) -> list[int]:
        result = [root_pc]
        for pc in pcs:
            ivl = (int(pc) - int(root_pc)) % 12
            if ivl in (3, 4, 10, 11):
                result.append(pc)
        return sorted(set(result)) if len(result) > 1 else sorted(pcs[:3])

    def _rootless_pcs(self, chord: ChordLabel, root_pc: int, pcs: list[int]) -> list[int]:
        result = [pc for pc in pcs if (int(pc) - int(root_pc)) % 12 in (3, 4, 7, 10, 11)]
        if chord.extensions:
            result.append((int(root_pc) + 2) % 12)
        return sorted(set(result)) if result else sorted(pcs[:4])

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        offsets = _STYLE_RHYTHMS.get(self.comp_style, _STYLE_RHYTHMS["jazz"])
        bpb = 3 if self.comp_style == "waltz" else 4
        t, events = 0.0, []
        while t < duration_beats:
            for off in offsets:
                onset = t + off
                if onset >= duration_beats:
                    break
                events.append(
                    RhythmEvent(
                        onset=round(onset, 6), duration=round(min(0.45, (bpb - off) * 0.45), 6)
                    )
                )
            t += bpb
        return events

    def _velocity(self) -> int:
        return int(60 + self.params.density * 35)
