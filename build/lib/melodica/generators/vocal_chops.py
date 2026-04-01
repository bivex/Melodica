"""
generators/vocal_chops.py — Vocal chop / sample chop generator.

Layer: Application / Domain
Style: Future bass, pop, EDM, hip-hop production.

Vocal chops are short vocal samples arranged into melodic patterns.
This generator creates the note patterns; actual vocal timbre comes
from the sampler/synth assigned to the track.

Processing types:
    "reverse"      — reversed vocal hits
    "stutter"      — beat-repeat stutter
    "pitch_shift"  — pitched vocal melody
    "formant"      — formant-shifted texture
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
class VocalChopsGenerator(PhraseGenerator):
    """
    Vocal chop / sample chop generator.

    processing:
        "reverse", "stutter", "pitch_shift", "formant"
    density:
        Note density (0.0–1.0).
    source_pitch:
        Base MIDI pitch for the vocal sample.
    chop_pattern:
        "syncopated", "offbeat", "random", "melodic"
    stutter_speed:
        For "stutter" processing: subdivision of repeats.
    """

    name: str = "Vocal Chops Generator"
    processing: str = "pitch_shift"
    density: float = 0.6
    source_pitch: int = 60
    chop_pattern: str = "syncopated"
    stutter_speed: float = 0.125
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        processing: str = "pitch_shift",
        density: float = 0.6,
        source_pitch: int = 60,
        chop_pattern: str = "syncopated",
        stutter_speed: float = 0.125,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.processing = processing
        self.density = max(0.0, min(1.0, density))
        self.source_pitch = max(36, min(84, source_pitch))
        self.chop_pattern = chop_pattern
        self.stutter_speed = max(0.03125, min(0.5, stutter_speed))
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
        anchor = self.source_pitch

        prev_pitch = context.prev_pitch if context and context.prev_pitch is not None else anchor
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            if random.random() > self.density:
                continue

            pcs = chord.pitch_classes()
            if not pcs:
                continue

            if self.processing == "stutter":
                # Rapid repeats of the same pitch
                t = event.onset
                end = min(event.onset + event.duration, duration_beats)
                pc = random.choice(pcs)
                pitch = max(low, min(high, nearest_pitch(int(pc), prev_pitch)))
                vel = self._velocity()
                while t < end:
                    n_dur = min(self.stutter_speed, end - t)
                    notes.append(
                        NoteInfo(pitch=pitch, start=round(t, 6), duration=n_dur * 0.8, velocity=vel)
                    )
                    t += self.stutter_speed
                prev_pitch = pitch

            elif self.processing == "reverse":
                # Reversed: note starts softly and builds
                pc = random.choice(pcs)
                pitch = max(low, min(high, nearest_pitch(int(pc), prev_pitch)))
                for i in range(4):
                    prog = i / 3
                    vel = int(20 + self._velocity() * prog)
                    onset = event.onset + i * (event.duration / 4)
                    notes.append(
                        NoteInfo(
                            pitch=pitch,
                            start=round(onset, 6),
                            duration=event.duration / 4,
                            velocity=max(1, vel),
                        )
                    )
                prev_pitch = pitch

            else:  # pitch_shift / formant
                pc = random.choice(pcs)
                pitch = max(low, min(high, nearest_pitch(int(pc), prev_pitch)))
                vel = self._velocity()
                notes.append(
                    NoteInfo(
                        pitch=pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=vel,
                    )
                )
                prev_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)

        if self.chop_pattern == "syncopated":
            t, events = 0.0, []
            while t < duration_beats:
                for off in [0.0, 0.75, 1.5, 2.0, 2.75, 3.5]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.4))
                t += 4.0
            return events

        elif self.chop_pattern == "offbeat":
            t, events = 0.0, []
            while t < duration_beats:
                for off in [0.5, 1.5, 2.5, 3.5]:
                    onset = t + off
                    if onset < duration_beats:
                        events.append(RhythmEvent(onset=round(onset, 6), duration=0.35))
                t += 4.0
            return events

        elif self.chop_pattern == "random":
            t, events = 0.0, []
            while t < duration_beats:
                num = random.randint(3, 8)
                for _ in range(num):
                    off = round(random.uniform(0, 3.9), 2)
                    onset = t + off
                    if onset < duration_beats:
                        events.append(
                            RhythmEvent(onset=round(onset, 6), duration=random.uniform(0.15, 0.5))
                        )
                t += 4.0
            return events

        else:  # melodic
            t, events = 0.0, []
            while t < duration_beats:
                events.append(RhythmEvent(onset=round(t, 6), duration=0.5))
                t += 0.5
            return events

    def _velocity(self) -> int:
        return int(55 + self.params.density * 35)
