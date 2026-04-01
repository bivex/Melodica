"""
generators/nebula.py — Nebula / textural cluster generator.

Layer: Application / Domain
Style: Ambient, cinematic, drone, noise, experimental.

Produces slowly evolving textural clusters: sustained notes with
overlapping entries, creating nebulous harmonic clouds.

Variants:
    "cloud"     — overlapping sustained notes at random intervals
    "cascade"   — notes enter one by one, building a cluster
    "swell"     — crescendo then diminuendo cluster
    "granular"  — very short grains forming a texture
    "stasis"    — static sustained cluster
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


@dataclass
class NebulaGenerator(PhraseGenerator):
    """
    Textural / ambient cluster generator.

    variant:
        "cloud", "cascade", "swell", "granular", "stasis"
    density_notes:
        How many notes per 4-beat bar (3–8).
    pitch_spread:
        How many semitones the cluster spans (3–24).
    note_duration:
        Base note duration in beats (for "granular": very short).
    overlap:
        Fraction of overlap between consecutive notes (0–1).
    use_scale_tones:
        If True, snap to scale tones. If False, use chromatic.
    """

    name: str = "Nebula Generator"
    variant: str = "cloud"
    density_notes: int = 5
    pitch_spread: int = 12
    note_duration: float = 3.0
    overlap: float = 0.5
    use_scale_tones: bool = True
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        variant: str = "cloud",
        density_notes: int = 5,
        pitch_spread: int = 12,
        note_duration: float = 3.0,
        overlap: float = 0.5,
        use_scale_tones: bool = True,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.variant = variant
        self.density_notes = max(2, min(12, density_notes))
        self.pitch_spread = max(3, min(24, pitch_spread))
        self.note_duration = max(0.1, min(16.0, note_duration))
        self.overlap = max(0.0, min(0.9, overlap))
        self.use_scale_tones = use_scale_tones
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

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2
        last_chord: ChordLabel | None = None

        if self.variant == "cloud":
            notes = self._cloud(chords, key, duration_beats, mid)
        elif self.variant == "cascade":
            notes = self._cascade(chords, key, duration_beats, mid)
        elif self.variant == "swell":
            notes = self._swell(chords, key, duration_beats, mid)
        elif self.variant == "granular":
            notes = self._granular(chords, key, duration_beats, mid)
        elif self.variant == "stasis":
            notes = self._stasis(chords, key, duration_beats, mid)

        if chords:
            last_chord = chords[-1]

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _pick_pitches(self, chord: ChordLabel, key: Scale, anchor: int, count: int) -> list[int]:
        if self.use_scale_tones:
            pool = [int(d) for d in key.degrees()]
        else:
            pool = chord.pitch_classes()

        if not pool:
            pool = [chord.root]

        pitches = []
        half_spread = self.pitch_spread // 2
        for _ in range(count):
            pc = random.choice(pool)
            base = nearest_pitch(pc, anchor)
            offset = random.randint(-half_spread, half_spread)
            p = max(self.params.key_range_low, min(self.params.key_range_high, base + offset))
            pitches.append(p)
        return sorted(set(pitches))

    def _cloud(
        self, chords: list[ChordLabel], key: Scale, dur: float, anchor: int
    ) -> list[NoteInfo]:
        notes = []
        t = 0.0
        step = 4.0 / self.density_notes
        while t < dur:
            chord = chord_at(chords, t)
            if chord is None:
                t += 1.0
                continue
            pitches = self._pick_pitches(chord, key, anchor, 2)
            vel = self._velocity_swell(t, dur)
            for p in pitches:
                n_dur = self.note_duration
                notes.append(NoteInfo(pitch=p, start=round(t, 6), duration=n_dur, velocity=vel))
            t += step * (1.0 - self.overlap)
        return notes

    def _cascade(
        self, chords: list[ChordLabel], key: Scale, dur: float, anchor: int
    ) -> list[NoteInfo]:
        notes = []
        chord = chords[0] if chords else None
        if chord is None:
            return notes
        pitches = self._pick_pitches(chord, key, anchor, self.density_notes)
        t = 0.0
        step = dur / max(len(pitches), 1)
        for p in pitches:
            vel = self._velocity_swell(t, dur)
            notes.append(NoteInfo(pitch=p, start=round(t, 6), duration=dur - t, velocity=vel))
            t += step
        return notes

    def _swell(
        self, chords: list[ChordLabel], key: Scale, dur: float, anchor: int
    ) -> list[NoteInfo]:
        notes = []
        chord = chords[0] if chords else None
        if chord is None:
            return notes
        pitches = self._pick_pitches(chord, key, anchor, self.density_notes)
        for p in pitches:
            vel = self._velocity_swell(dur * 0.5, dur)
            notes.append(NoteInfo(pitch=p, start=0.0, duration=dur, velocity=vel))
        return notes

    def _granular(
        self, chords: list[ChordLabel], key: Scale, dur: float, anchor: int
    ) -> list[NoteInfo]:
        notes = []
        t = 0.0
        grain_dur = 0.125
        while t < dur:
            chord = chord_at(chords, t)
            if chord is None:
                t += grain_dur
                continue
            p = random.choice(self._pick_pitches(chord, key, anchor, 1))
            vel = int(self._velocity_swell(t, dur) * random.uniform(0.5, 1.0))
            notes.append(
                NoteInfo(pitch=p, start=round(t, 6), duration=grain_dur, velocity=max(1, vel))
            )
            t += grain_dur * random.uniform(0.5, 2.0)
        return notes

    def _stasis(
        self, chords: list[ChordLabel], key: Scale, dur: float, anchor: int
    ) -> list[NoteInfo]:
        notes = []
        chord = chords[0] if chords else None
        if chord is None:
            return notes
        pitches = self._pick_pitches(chord, key, anchor, self.density_notes)
        vel = int(35 + self.params.density * 20)
        for p in pitches:
            notes.append(NoteInfo(pitch=p, start=0.0, duration=dur, velocity=vel))
        return notes

    def _velocity_swell(self, elapsed: float, total: float) -> int:
        base = int(35 + self.params.density * 25)
        if total > 0:
            progress = elapsed / total
            factor = 0.5 + 0.5 * (1.0 - abs(2.0 * progress - 1.0))
            return int(base * factor)
        return base
