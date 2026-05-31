"""LeitmotifRegistry — semantic binding layer for thematic motifs.

Maps named motifs to characters, places, emotions via tags, and provides
render() with chainable transforms using Motif.develop().
Supports variants, evolution tracking, mood-based rendering, layering,
and automatic counter-motif generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from melodica.composer.motif import Motif, _copy_note, _clamp_pitch
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import Scale


MOOD_PRESETS: dict[str, dict] = {
    "dark":       {"invert": True, "diminish_factor": 2.0, "transpose": -6},
    "triumphant":  {"transpose": 7, "augment_factor": 1.5},
    "tender":      {"augment_factor": 1.8, "fragment_end": 4.0},
    "aggressive":  {"diminish_factor": 2.0, "retrograde": True},
    "mysterious":  {"invert": True, "augment_factor": 2.0, "transpose": 3},
    "nostalgic":   {"retrograde": True, "augment_factor": 2.0},
    "urgent":      {"diminish_factor": 2.5},
    "ethereal":    {"augment_factor": 3.0, "transpose": 12},
}


@dataclass(slots=True)
class Leitmotif:
    """A named, tagged motif with instrument and register preferences."""

    name: str
    motif: Motif
    tags: list[str]
    default_instrument: int
    default_velocity: int
    register: int  # 0=low, 1=mid, 2=high
    _variants: dict[str, Motif] = field(default_factory=dict, repr=False)
    _evolution_log: list[str] = field(default_factory=list, repr=False)

    def __post_init__(self):
        self._variants["default"] = self.motif


@dataclass
class LeitmotifRegistry:
    """Central registry for leitmotifs with semantic tag queries."""

    _motifs: dict[str, Leitmotif] = field(default_factory=dict)

    def register(
        self,
        name: str,
        motif: Motif,
        tags: list[str] | None = None,
        instrument: int = 48,
        velocity: int = 70,
        register: int = 1,
    ) -> Leitmotif:
        entry = Leitmotif(
            name=name,
            motif=motif,
            tags=tags or [],
            default_instrument=instrument,
            default_velocity=velocity,
            register=register,
        )
        self._motifs[name] = entry
        return entry

    def get(self, name: str) -> Leitmotif | None:
        return self._motifs.get(name)

    def by_tag(self, tag: str) -> list[Leitmotif]:
        return [m for m in self._motifs.values() if tag in m.tags]

    def register_variant(self, name: str, variant_name: str, motif: Motif) -> None:
        """Store an additional variant of an existing leitmotif."""
        entry = self._motifs.get(name)
        if entry is None:
            raise KeyError(f"Leitmotif {name!r} not registered")
        entry._variants[variant_name] = motif

    def evolve(
        self,
        name: str,
        target_variant: str,
        **transform_kw,
    ) -> Motif:
        """Apply transform chain to a leitmotif and store as a named variant."""
        entry = self._motifs.get(name)
        if entry is None:
            raise KeyError(f"Leitmotif {name!r} not registered")
        source = entry._variants.get(
            transform_kw.pop("source_variant", "default"), entry.motif
        )
        developed = source.develop(**transform_kw)
        entry._variants[target_variant] = developed
        summary = ", ".join(f"{k}={v!r}" for k, v in transform_kw.items())
        entry._evolution_log.append(f"{target_variant} <- {summary}")
        return developed

    def render(
        self,
        name: str,
        *,
        offset: float = 0.0,
        variant: str | None = None,
        transpose: int = 0,
        augment_factor: float | None = None,
        diminish_factor: float | None = None,
        invert: bool = False,
        retrograde: bool = False,
        fragment_start: float | None = None,
        fragment_end: float | None = None,
        sequence_intervals: list[int] | None = None,
        sequence_spacing: float | None = None,
        **extra_kw,
    ) -> list[NoteInfo]:
        """Render a named motif with optional transforms, returning notes at *offset*."""
        entry = self._motifs.get(name)
        if entry is None:
            return []

        source = entry._variants.get(variant, entry.motif) if variant else entry.motif

        developed = source.develop(
            transpose=transpose if transpose != 0 else None,
            augment_factor=augment_factor,
            diminish_factor=diminish_factor,
            invert=invert,
            retrograde=retrograde,
            fragment_start=fragment_start,
            fragment_end=fragment_end,
            sequence_intervals=sequence_intervals,
            sequence_spacing=sequence_spacing,
            **extra_kw,
        )
        return developed.render(offset=offset)

    def render_for(
        self,
        name: str,
        mood: str,
        *,
        intensity: float = 1.0,
        offset: float = 0.0,
    ) -> list[NoteInfo]:
        """Contextual rendering using mood presets. *intensity* scales augment/diminish factors."""
        preset = MOOD_PRESETS.get(mood)
        if preset is None:
            return self.render(name, offset=offset)
        kw = dict(preset)
        if intensity != 1.0:
            for key in ("augment_factor", "diminish_factor"):
                if key in kw:
                    kw[key] = kw[key] * intensity
        return self.render(name, offset=offset, **kw)

    def layer(
        self,
        names: list[str],
        offsets: list[float],
        **render_kw,
    ) -> list[NoteInfo]:
        """Polyphonic combination of multiple motifs at given offsets."""
        all_notes: list[NoteInfo] = []
        for name, off in zip(names, offsets):
            all_notes.extend(self.render(name, offset=off, **render_kw))
        all_notes.sort(key=lambda n: n.start)
        return all_notes

    def counter_motif(
        self,
        name: str,
        scale: Scale,
        rhythm_pattern: list[float] | None = None,
    ) -> Motif:
        """Auto-generate a contrasting motif: inverted intervals, reversed rhythm."""
        entry = self._motifs.get(name)
        if entry is None:
            raise KeyError(f"Leitmotif {name!r} not registered")
        notes = entry.motif.notes
        if not notes:
            return Motif.from_notes([])

        sorted_notes = sorted(notes, key=lambda n: n.start)
        first_pitch = sorted_notes[0].pitch

        if rhythm_pattern is None:
            pattern = [n.duration for n in sorted_notes]
        else:
            pattern = list(rhythm_pattern)

        new_notes: list[NoteInfo] = []
        t = 0.0
        for i, orig in enumerate(sorted_notes):
            delta = orig.pitch - first_pitch
            new_pitch = _clamp_pitch(first_pitch - delta)
            dur = pattern[i % len(pattern)]
            new_notes.append(NoteInfo(
                pitch=new_pitch,
                start=t,
                duration=dur,
                velocity=orig.velocity,
            ))
            t += dur
        return Motif.from_notes(new_notes)

    def render_all(
        self,
        *,
        tag: str | None = None,
        offset: float = 0.0,
        **transform_kw,
    ) -> list[NoteInfo]:
        """Render all motifs (optionally filtered by tag) and merge."""
        entries = (
            self.by_tag(tag) if tag else list(self._motifs.values())
        )
        all_notes: list[NoteInfo] = []
        for entry in entries:
            notes = self.render(entry.name, offset=offset, **transform_kw)
            all_notes.extend(notes)
        all_notes.sort(key=lambda n: n.start)
        return all_notes
