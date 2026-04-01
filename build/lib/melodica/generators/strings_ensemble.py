"""
generators/strings_ensemble.py — Full string ensemble with divisi and dynamics.

Layer: Application / Domain
Style: Classical, cinematic, orchestral, pop ballad, film scoring.

Produces string section textures with configurable divisi (voice splitting),
articulation types, and dynamic curves. Supports chamber, full orchestra,
and solo string textures.

Articulations:
    "sustained" — long bow, connected notes
    "staccato"  — short, detached
    "tremolo"   — rapid bow reiteration
    "pizz"      — pizzicato, plucked
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale
from melodica.utils import nearest_pitch, chord_at


SECTION_VOICE_COUNTS: dict[str, int] = {
    "solo": 1,
    "chamber": 3,
    "full": 5,
}

ARTICULATION_CONF: dict[str, dict] = {
    "sustained": {"dur_factor": 0.95, "vel_mod": 0, "tremolo": False},
    "staccato": {"dur_factor": 0.25, "vel_mod": 12, "tremolo": False},
    "tremolo": {"dur_factor": 0.95, "vel_mod": 5, "tremolo": True},
    "pizz": {"dur_factor": 0.15, "vel_mod": 8, "tremolo": False},
}


@dataclass
class StringsEnsembleGenerator(PhraseGenerator):
    """
    Full string ensemble with divisi and dynamics.

    section_size:
        "solo", "chamber", "full"
    articulation:
        "sustained", "staccato", "tremolo", "pizz"
    divisi:
        Number of divisi divisions per chord (1–6).
    dynamic_curve:
        "crescendo", "flat", "swell"
    """

    name: str = "Strings Ensemble Generator"
    section_size: str = "full"
    articulation: str = "sustained"
    divisi: int = 4
    dynamic_curve: str = "flat"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        section_size: str = "full",
        articulation: str = "sustained",
        divisi: int = 4,
        dynamic_curve: str = "flat",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.section_size = section_size
        self.articulation = articulation
        self.divisi = max(1, min(6, divisi))
        self.dynamic_curve = dynamic_curve
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
        last_chord = chords[-1]
        voice_count = SECTION_VOICE_COUNTS.get(self.section_size, 3)
        art = ARTICULATION_CONF.get(self.articulation, ARTICULATION_CONF["sustained"])
        elapsed = 0.0

        for chord in chords:
            pcs = chord.pitch_classes()
            if not pcs:
                continue

            for div_idx in range(self.divisi):
                pc = pcs[div_idx % len(pcs)]
                spread = (div_idx - self.divisi // 2) * 3
                anchor = mid + spread
                pitch = nearest_pitch(int(pc), anchor)
                pitch = max(self.params.key_range_low, min(self.params.key_range_high, pitch))

                for _ in range(voice_count):
                    vel = self._velocity(elapsed / max(duration_beats, 1.0))
                    vel += art["vel_mod"]
                    vel += random.randint(-5, 5)
                    vel = max(1, min(127, vel))

                    onset = chord.start + random.uniform(0.0, 0.02)
                    note_dur = chord.duration * art["dur_factor"]

                    if art["tremolo"]:
                        # Tremolo: split into rapid reiterations
                        grain = 0.125
                        gt = onset
                        while gt < onset + note_dur:
                            notes.append(
                                NoteInfo(
                                    pitch=pitch,
                                    start=round(gt, 6),
                                    duration=grain * 0.8,
                                    velocity=max(1, vel + random.randint(-3, 3)),
                                )
                            )
                            gt += grain
                    else:
                        notes.append(
                            NoteInfo(
                                pitch=pitch,
                                start=round(onset, 6),
                                duration=max(0.08, note_dur),
                                velocity=vel,
                            )
                        )

            elapsed += chord.duration

        notes.sort(key=lambda n: n.start)

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _velocity(self, progress: float) -> int:
        base = int(50 + self.params.density * 30)
        if self.dynamic_curve == "crescendo":
            return int(base + progress * 30)
        elif self.dynamic_curve == "swell":
            return int(base + 15 * (1.0 - abs(2.0 * progress - 1.0)))
        return base
