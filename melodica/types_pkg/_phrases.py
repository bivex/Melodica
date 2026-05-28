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

"""Phrase generation and arrangement types."""

from __future__ import annotations


import dataclasses
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import TYPE_CHECKING, List

from melodica.theory import Mode, Quality, CHORD_TEMPLATES, MODE_DATABASE, get_mode_intervals


from melodica.types_pkg._notes import NoteInfo, Note
from melodica.types_pkg._theory import ChordLabel, Scale, Quality
from melodica.types_pkg._timeline import MusicTimeline, KeyLabel, TimeSignatureLabel

@dataclass
class StaticPhrase:
    notes: list[NoteInfo]

@dataclass
class HarmonizationRequest:
    melody: list[Note]
    key: Scale
    engine: int | str = 0                 # 0=functional, 1=rule_based, 2=adaptive, 3/4=hmm, 'fibril'
    chord_rhythm: float = 4.0
    allow_secondary_dominants: bool = True
    allow_borrowed_chords: bool = False
    rule_db: "object | None" = None

    def __post_init__(self) -> None:
        if not self.melody:
            raise ValueError("Melody must not be empty.")
        if self.chord_rhythm <= 0:
            raise ValueError("chord_rhythm must be > 0.")
        valid_engines = {0, 1, 2, 3, 4}
        if not isinstance(self.engine, str) and self.engine not in valid_engines:
            raise ValueError(f"Invalid engine: {self.engine}")

class PhraseGeneratorProtocol(ABC):
    name: str
    params: "object"

    @abstractmethod
    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: "RenderContext | None" = None,
    ) -> list[NoteInfo]: ...

@dataclass
class PhraseInstance:
    generator: "PhraseGeneratorProtocol | None" = None
    static: StaticPhrase | None = None
    modifiers: "list[object]" = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.generator is None and self.static is None:
            raise ValueError("PhraseInstance must have either a generator or static notes.")
        if self.generator is not None and self.static is not None:
            raise ValueError("PhraseInstance cannot have both a generator and static notes.")

    def is_parametric(self) -> bool:
        return self.generator is not None

    def modify(self, notes: list[NoteInfo], context: "ModifierContext") -> list[NoteInfo]:
        for mod in self.modifiers:
            if hasattr(mod, "modify"):
                notes = mod.modify(notes, context)
        return notes

    def render(self, chords: list[ChordLabel], timeline: MusicTimeline | Scale, total_beats: float, context: "RenderContext | None" = None) -> list[NoteInfo]:
        if isinstance(timeline, Scale):
            timeline = MusicTimeline(chords=chords, keys=[KeyLabel(scale=timeline, start=0, duration=total_beats)])

        if self.generator:
            key_scale = timeline.get_key_at(0.0) if hasattr(timeline, "get_key_at") else timeline
            notes = self.generator.render(chords, key_scale, total_beats, context)
        else:
            notes = list(self.static.notes) if self.static else []

        if self.modifiers:
            from melodica.modifiers import ModifierContext
            active_scale = timeline.get_key_at(0.0) if hasattr(timeline, "get_key_at") else timeline
            mod_ctx = ModifierContext(
                duration_beats=total_beats,
                chords=chords,
                timeline=timeline,
                scale=active_scale,
            )
            notes = self.modify(notes, mod_ctx)
        return notes

@dataclass
class ArrangementSlot:
    """One placed phrase on the timeline (mirrors Idea Tool output)."""
    phrase: "PhraseInstance"
    start_beat: float
    label: str  # letter from phrase_order ("A", "B", …)

@dataclass
class IdeaTrack:
    """
    (Track Idea) block.
    """
    seed_phrases: list[PhraseInstance]
    generator: PhraseGeneratorProtocol | None = None
    phrase_order: str = "A"
    random_order: bool = False

    def __post_init__(self) -> None:
        if not self.seed_phrases:
            raise ValueError("IdeaTrack.seed_phrases must not be empty.")

@dataclass
class Track:
    """
    A full musical track (part) in an arrangement.
    Contains the rendered notes and metadata like instrument name or MIDI channel.
    """
    name: str
    notes: list[NoteInfo] = field(default_factory=list)
    channel: int = 0
    program: int = 0        # General MIDI Program Number (0-127)
    instrument_name: str = ""  # Meta: instrument label in DAW track header
    volume: int = 100       # CC 7  — channel volume
    pan: int = 64           # CC 10 — stereo position (0=L, 64=C, 127=R)
    expression: int = 127   # CC 11 — expression (dynamic shaping within volume)
    modulation: int = 0     # CC 1  — vibrato depth (applied by automation; 0 at start)
    attack: int = 64        # CC 73 — envelope attack time (64=neutral)
    release: int = 64       # CC 72 — envelope release time (64=neutral)
    brightness: int = 64    # CC 74 — filter cutoff / tonal brightness (64=neutral)
    reverb: int = 40        # CC 91 — reverb send level
    chorus: int = 0         # CC 93 — chorus send level
    vibrato: int = 0            # CC 3  — vibrato depth (0=off at start; per-note automation)
    sustain_pedal: int = 0      # CC 64 — sustain/articulation trigger (0=off)
    keyswitch_events: list[tuple[float, int]] = field(default_factory=list)
    # keyswitch_events: list of (beat_position, midi_note_pitch) emitted as 1-tick notes
    pitch_bend_range: int = 2  # semitones; sent as RPN 0x0000 at track start

    def shift_time(self, offset: float) -> Track:
        for note in self.notes:
            note.shift_time(offset)
        return self

    def transpose(self, semitones: int) -> Track:
        for note in self.notes:
            note.transpose(semitones)
        return self

    def scale_velocity(self, factor: float) -> Track:
        for note in self.notes:
            note.scale_velocity(factor)
        return self

    def time_stretch(self, multiplier: float) -> Track:
        for note in self.notes:
            note.time_stretch(multiplier)
        return self

    def morph_scale(self, from_scale: Scale, to_scale: Scale, strategy: str = "degree") -> Track:
        for note in self.notes:
            note.morph_scale(from_scale, to_scale, strategy)
        return self

    def humanize(self, timing_std_beats: float = 0.01, velocity_std: float = 3.0) -> Track:
        for note in self.notes:
            note.humanize(timing_std_beats, velocity_std)
        return self

    def swing(self, factor: float = 0.1, grid: float = 0.25) -> Track:
        for note in self.notes:
            note.swing(factor, grid)
        return self



@dataclass
class Arrangement:
    """
    Top-level domain object for a multi-part composition.
    Combines a timeline (chords/keys) with multiple tracks.
    """
    name: str
    timeline: MusicTimeline
    tracks: list[Track] = field(default_factory=list)
    total_beats: float = 0.0
