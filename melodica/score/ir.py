# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.score.ir — Song Intermediate Representation (IR).

Strictly decoupled domain data structures representing a song score:
- Bar: rhythmic bar containing timed chord labels
- Section: structural song section (Intro, Verse, Chorus) with bars and repeat rules
- TrackArrange: arrangement specifications per instrument track
- Song: complete musical composition model (form, tempo, scale, sections, arrange)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

from melodica.types import ChordLabel, Scale, Mode


@dataclass
class Bar:
    """A single musical bar containing chords and timing."""
    index: int
    chords: list[ChordLabel] = field(default_factory=list)
    beats: float = 4.0
    raw_text: str = ""

    def copy_with_offset(self, start_beat_offset: float, new_index: int | None = None) -> Bar:
        """Create a clone of this bar shifted to an absolute start beat offset."""
        shifted_chords = []
        for ch in self.chords:
            shifted = ChordLabel(
                root=ch.root,
                quality=ch.quality,
                extensions=list(ch.extensions) if ch.extensions else [],
                bass=ch.bass,
                inversion=ch.inversion,
                start=round(ch.start + start_beat_offset, 6),
                duration=ch.duration,
                degree=ch.degree,
                function=ch.function,
            )
            shifted_chords.append(shifted)
        return Bar(
            index=new_index if new_index is not None else self.index,
            chords=shifted_chords,
            beats=self.beats,
            raw_text=self.raw_text,
        )


@dataclass
class Section:
    """A musical section (e.g. Intro, Verse, Chorus) composed of bars."""
    name: str
    bars: list[Bar] = field(default_factory=list)
    repeats: int = 1
    target_bars: int | None = None
    key: Scale | None = None
    arrange_overrides: dict[str, Any] = field(default_factory=dict)

    def effective_bars(self) -> list[Bar]:
        """
        Return the unrolled sequence of bars for this section,
        handling repeat multipliers (x2) or target bar padding (8 bars).
        """
        if not self.bars:
            return []

        base_bars = self.bars
        if self.target_bars is not None and self.target_bars > len(base_bars):
            # Pad / loop bars to reach target count
            padded: list[Bar] = []
            while len(padded) < self.target_bars:
                needed = self.target_bars - len(padded)
                padded.extend(base_bars[:needed])
            base_bars = padded

        # Apply repeat multiplier (x2, x3...)
        result: list[Bar] = []
        for r in range(max(1, self.repeats)):
            result.extend(base_bars)
        return result

    def bar_count(self) -> int:
        """Total number of bars in this section after repeats."""
        return len(self.effective_bars())


@dataclass
class TrackArrange:
    """Arrangement instructions for a single instrument track."""
    name: str
    instrument: str | None = None
    family: str | None = None
    style: str | None = None
    groove: str | None = None
    intensity: float = 0.7
    density: float = 0.7
    octave_shift: int = 0
    range: tuple[int, int] | None = None
    articulation: str | None = None
    algorithm: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class Song:
    """
    Complete structured musical score IR.
    """
    title: str = "Untitled"
    key: Scale = field(default_factory=lambda: Scale(root=0, mode=Mode.MAJOR))
    tempo: float = 120.0
    time_signature: tuple[int, int] = (4, 4)
    feel: str = "straight"
    seed: int | None = None
    sections: dict[str, Section] = field(default_factory=dict)
    form: list[str] = field(default_factory=list)
    arrange: dict[str, TrackArrange] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def beats_per_bar(self) -> float:
        """Calculate number of quarter-note beats per bar based on time signature."""
        num, denom = self.time_signature
        return num * (4.0 / denom)

    def total_bars(self) -> int:
        """Calculate total number of bars across the entire song form."""
        form_seq = self.form or list(self.sections.keys())
        total = 0
        for name in form_seq:
            sec = self.sections.get(name)
            if sec:
                total += sec.bar_count()
        return total

    def total_beats(self) -> float:
        """Calculate total playback duration in quarter-note beats."""
        return self.total_bars() * self.beats_per_bar

    def unrolled_timeline(self) -> tuple[list[tuple[str, float]], list[ChordLabel]]:
        """
        Unroll the full song form into:
        1. Markers: list of (section_name, start_beat)
        2. Absolute Chords: all ChordLabels with global absolute start beats.
        """
        form_seq = self.form or list(self.sections.keys())
        markers: list[tuple[str, float]] = []
        all_chords: list[ChordLabel] = []

        current_beat = 0.0
        for sec_name in form_seq:
            sec = self.sections.get(sec_name)
            if not sec:
                continue

            markers.append((sec_name, current_beat))
            eff_bars = sec.effective_bars()

            for bar in eff_bars:
                bar_dur = bar.beats or self.beats_per_bar
                for ch in bar.chords:
                    shifted = ChordLabel(
                        root=ch.root,
                        quality=ch.quality,
                        extensions=list(ch.extensions) if ch.extensions else [],
                        bass=ch.bass,
                        inversion=ch.inversion,
                        start=round(current_beat + ch.start, 6),
                        duration=ch.duration,
                        degree=ch.degree,
                        function=ch.function,
                    )
                    all_chords.append(shifted)
                current_beat += bar_dur

        return markers, all_chords

    def to_song_text(self) -> str:
        """Serialize Song IR back into human-readable .song format."""
        from melodica.score.serializer import serialize_song
        return serialize_song(self)
