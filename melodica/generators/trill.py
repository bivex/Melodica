"""
generators/trill.py — Trill and tremolo ornament generator.

Layer: Application / Domain
Style: Baroque, classical, romantic, orchestral.

Trills rapidly alternate between two adjacent notes (usually a whole or half
step apart). Tremolos rapidly repeat a single note or alternate between two
notes at wider intervals.

Variants:
    "trill"      — rapid alternation between note and upper neighbor
    "lower_trill"— rapid alternation between note and lower neighbor (mordent-like)
    "tremolo"    — rapid repetition of the same pitch
    "bisbigliando"— timbral tremolo (trill between enharmonic equivalents / microtones)
    "roll"       — wide-interval tremolo (e.g., octave roll on piano)
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
class TrillTremoloGenerator(PhraseGenerator):
    """
    Trill / tremolo ornament generator.

    ornament_type:
        "trill", "lower_trill", "tremolo", "bisbigliando", "roll"
    speed:
        Subdivision in beats: 0.125 = 32nd notes (fast trill),
        0.25 = 16th notes, 0.5 = eighth notes (slow trill).
    base_note_strategy:
        How to choose the base note:
        "chord_root" — always start from chord root
        "chord_tone" — random chord tone
        "scale_tone" — random scale tone
        "prev_note"  — continue from previous note
    neighbor_interval:
        Semitone interval to the neighbor note (1=half step, 2=whole step).
        "auto" picks based on the scale context.
    duration_range:
        (min, max) beats for each trill/tremolo event.
    probability:
        Probability of placing an ornament at each eligible event.
    """

    name: str = "Trill/Tremolo Generator"
    ornament_type: str = "trill"
    speed: float = 0.125
    base_note_strategy: str = "chord_tone"
    neighbor_interval: int | str = "auto"
    duration_range: tuple[float, float] = (0.5, 2.0)
    probability: float = 0.8
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        ornament_type: str = "trill",
        speed: float = 0.125,
        base_note_strategy: str = "chord_tone",
        neighbor_interval: int | str = "auto",
        duration_range: tuple[float, float] = (0.5, 2.0),
        probability: float = 0.8,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if ornament_type not in ("trill", "lower_trill", "tremolo", "bisbigliando", "roll"):
            raise ValueError(
                f"ornament_type must be one of 'trill', 'lower_trill', 'tremolo', "
                f"'bisbigliando', 'roll'; got {ornament_type!r}"
            )
        self.ornament_type = ornament_type
        self.speed = max(0.0625, min(0.5, speed))
        self.base_note_strategy = base_note_strategy
        self.neighbor_interval = neighbor_interval
        self.duration_range = (
            max(0.25, duration_range[0]),
            max(duration_range[0], duration_range[1]),
        )
        self.probability = max(0.0, min(1.0, probability))
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
        low = self.params.key_range_low
        high = self.params.key_range_high
        anchor = (low + high) // 2

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            if random.random() > self.probability:
                continue

            # Base note
            base_pitch = self._pick_base(chord, prev_pitch, key, low, high)

            # Ornament duration
            orn_dur = random.uniform(*self.duration_range)
            orn_dur = min(orn_dur, duration_beats - event.onset)

            if self.ornament_type == "tremolo":
                subnotes = self._tremolo(base_pitch, event.onset, orn_dur, low, high)
            elif self.ornament_type == "roll":
                subnotes = self._roll(base_pitch, event.onset, orn_dur, low, high)
            else:
                # trill, lower_trill, bisbigliando
                neighbor = self._neighbor(base_pitch, chord, key, low, high)
                subnotes = self._trill(base_pitch, neighbor, event.onset, orn_dur, low, high)

            notes.extend(subnotes)
            if subnotes:
                prev_pitch = subnotes[-1].pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    # ------------------------------------------------------------------
    # Base note selection
    # ------------------------------------------------------------------

    def _pick_base(
        self, chord: ChordLabel, prev_pitch: int, key: Scale, low: int, high: int
    ) -> int:
        if self.base_note_strategy == "chord_root":
            return nearest_pitch(chord.root, prev_pitch)
        elif self.base_note_strategy == "chord_tone":
            pcs = chord.pitch_classes()
            pc = random.choice(pcs) if pcs else chord.root
            return nearest_pitch(pc, prev_pitch)
        elif self.base_note_strategy == "scale_tone":
            degs = key.degrees()
            if degs:
                pc = int(random.choice(degs))
                return nearest_pitch(pc, prev_pitch)
            return nearest_pitch(chord.root, prev_pitch)
        else:  # prev_note
            return prev_pitch

    # ------------------------------------------------------------------
    # Neighbor note
    # ------------------------------------------------------------------

    def _neighbor(self, base: int, chord: ChordLabel, key: Scale, low: int, high: int) -> int:
        if self.ornament_type == "bisbigliando":
            # Enharmonic micro-shift (simulate with +1 semitone)
            return max(low, min(high, base + 1))

        if isinstance(self.neighbor_interval, int):
            interval = self.neighbor_interval
        else:
            # Auto: find the closest scale tone that's a half or whole step away
            degs = key.degrees()
            base_pc = base % 12
            candidates = []
            for d in degs:
                diff = abs(int(d) - base_pc)
                diff = min(diff, 12 - diff)
                if 1 <= diff <= 2:
                    candidates.append(int(d))
            if candidates:
                target_pc = min(candidates, key=lambda d: abs(int(d) - base_pc))
                interval = (target_pc - base_pc) % 12
                if interval > 6:
                    interval = interval - 12
            else:
                interval = 1  # default half step

        if self.ornament_type == "lower_trill":
            interval = -abs(interval)
        else:
            interval = abs(interval)

        neighbor = base + interval
        return max(low, min(high, neighbor))

    # ------------------------------------------------------------------
    # Ornament patterns
    # ------------------------------------------------------------------

    def _trill(
        self, base: int, neighbor: int, onset: float, dur: float, low: int, high: int
    ) -> list[NoteInfo]:
        """Rapid alternation between base and neighbor."""
        notes: list[NoteInfo] = []
        t = onset
        end = onset + dur
        use_base = True

        vel = self._velocity()
        while t < end:
            pitch = base if use_base else neighbor
            pitch = max(low, min(high, pitch))
            n_dur = min(self.speed, end - t)
            if n_dur <= 0:
                break
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=n_dur * 0.9,
                    velocity=max(1, min(127, vel)),
                )
            )
            t += self.speed
            use_base = not use_base

        return notes

    def _tremolo(self, pitch: int, onset: float, dur: float, low: int, high: int) -> list[NoteInfo]:
        """Rapid repetition of a single pitch."""
        notes: list[NoteInfo] = []
        t = onset
        end = onset + dur
        pitch = max(low, min(high, pitch))

        vel = self._velocity()
        while t < end:
            n_dur = min(self.speed, end - t)
            if n_dur <= 0:
                break
            # Slight velocity variation for realism
            v = max(1, min(127, vel + random.randint(-5, 5)))
            notes.append(
                NoteInfo(
                    pitch=pitch,
                    start=round(t, 6),
                    duration=n_dur * 0.85,
                    velocity=v,
                )
            )
            t += self.speed

        return notes

    def _roll(self, base: int, onset: float, dur: float, low: int, high: int) -> list[NoteInfo]:
        """Wide-interval tremolo (e.g., octave roll)."""
        notes: list[NoteInfo] = []
        t = onset
        end = onset + dur
        pitches = [base, base + 12]
        pitches = [max(low, min(high, p)) for p in pitches]

        vel = self._velocity()
        idx = 0
        while t < end:
            n_dur = min(self.speed, end - t)
            if n_dur <= 0:
                break
            notes.append(
                NoteInfo(
                    pitch=pitches[idx % len(pitches)],
                    start=round(t, 6),
                    duration=n_dur * 0.85,
                    velocity=max(1, min(127, vel)),
                )
            )
            t += self.speed
            idx += 1

        return notes

    # ------------------------------------------------------------------
    # Rhythm & velocity
    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        # Default: events at half-note intervals
        t, events = 0.0, []
        while t < duration_beats:
            dur = random.uniform(*self.duration_range)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += dur + random.uniform(0.25, 1.0)
        return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
