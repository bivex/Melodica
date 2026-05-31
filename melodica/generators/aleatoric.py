# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/aleatoric.py — Chance-based / aleatoric composition generators.

Six modes inspired by Cage, Lutoslawski, and Xenakis:
  tone_cluster, chance_operations, repeat_ad_lib, graphic_score,
  pointillist, textural_cloud.
"""

from __future__ import annotations

import random

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale


class AleatoricGenerator(PhraseGenerator):
    """Chance-based generator with six compositional modes.

    mode:
        "tone_cluster"      — Dense chromatic cluster within a pitch range.
        "chance_operations"  — Cage-inspired random note placement.
        "repeat_ad_lib"      — Repeated figure with slight variations.
        "graphic_score"      — Broad pitch regions with free rhythm.
        "pointillist"        — Isolated, scattered individual notes.
        "textural_cloud"     — Statistical density cloud (Xenakis-inspired).
    """

    name: str = "Aleatoric Generator"

    MODES = frozenset({
        "tone_cluster", "chance_operations", "repeat_ad_lib",
        "graphic_score", "pointillist", "textural_cloud",
    })

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        mode: str = "tone_cluster",
        density: float = 0.5,
    ) -> None:
        super().__init__(params)
        if mode not in self.MODES:
            raise ValueError(f"Unknown mode '{mode}'. Valid: {sorted(self.MODES)}")
        self.mode = mode
        self.density = density

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords or duration_beats <= 0:
            return []

        lo = self.params.key_range_low
        hi = self.params.key_range_high

        render_fn = {
            "tone_cluster": self._tone_cluster,
            "chance_operations": self._chance_operations,
            "repeat_ad_lib": self._repeat_ad_lib,
            "graphic_score": self._graphic_score,
            "pointillist": self._pointillist,
            "textural_cloud": self._textural_cloud,
        }[self.mode]

        notes = render_fn(lo, hi, duration_beats, key)
        notes.sort(key=lambda n: n.start)
        return notes

    # -- mode implementations --

    def _tone_cluster(self, lo: int, hi: int, dur: float, key: Scale) -> list[NoteInfo]:
        """Dense chromatic cluster — every semitone in range, simultaneous onset."""
        span = min(12, hi - lo)
        base = random.randint(lo, max(lo, hi - span))
        start = random.uniform(0, dur * 0.1)
        note_dur = dur * random.uniform(0.6, 1.0)
        vel = random.randint(30, 60)

        return [
            NoteInfo(pitch=base + i, start=start, duration=note_dur,
                     velocity=max(20, vel - abs(i - span // 2) * 3))
            for i in range(span + 1)
        ]

    def _chance_operations(self, lo: int, hi: int, dur: float, key: Scale) -> list[NoteInfo]:
        """Cage-inspired: I Ching-style random placement and pitch."""
        notes: list[NoteInfo] = []
        # Number of events determined by density
        n_events = max(4, int(dur * self.density * 2))
        for _ in range(n_events):
            if random.random() > self.density:
                continue
            t = random.uniform(0, dur)
            pitch = random.randint(lo, hi)
            note_dur = random.uniform(0.25, 4.0)
            vel = random.randint(30, 90)
            notes.append(NoteInfo(pitch=pitch, start=t, duration=note_dur, velocity=vel))
        return notes

    def _repeat_ad_lib(self, lo: int, hi: int, dur: float, key: Scale) -> list[NoteInfo]:
        """Repeated figure with micro-variations in pitch and rhythm."""
        notes: list[NoteInfo] = []
        # Create a short figure (3-6 notes)
        fig_len = random.randint(3, 6)
        figure: list[tuple[int, float, float, int]] = []
        for _ in range(fig_len):
            p = random.randint(lo, hi)
            d = random.uniform(0.5, 2.0)
            gap = random.uniform(0.25, 1.0)
            v = random.randint(40, 75)
            figure.append((p, d, gap, v))

        t = 0.0
        while t < dur:
            for p, d, gap, v in figure:
                if t >= dur:
                    break
                # Micro-variation: slight pitch and velocity shift
                p_var = max(lo, min(hi, p + random.choice([-1, 0, 0, 1])))
                v_var = max(20, min(100, v + random.randint(-5, 5)))
                d_var = d * random.uniform(0.9, 1.1)
                notes.append(NoteInfo(pitch=p_var, start=t, duration=d_var, velocity=v_var))
                t += d_var + gap * random.uniform(0.8, 1.2)
        return notes

    def _graphic_score(self, lo: int, hi: int, dur: float, key: Scale) -> list[NoteInfo]:
        """Broad pitch regions — 3-5 regions with free time placement."""
        notes: list[NoteInfo] = []
        n_regions = random.randint(3, 5)
        region_size = max(3, (hi - lo) // n_regions)

        for i in range(n_regions):
            region_lo = lo + i * region_size
            region_hi = min(hi, region_lo + region_size)
            region_start = dur * i / n_regions
            region_dur = dur / n_regions

            n_notes = random.randint(2, 6)
            for _ in range(n_notes):
                t = region_start + random.uniform(0, region_dur * 0.8)
                p = random.randint(region_lo, region_hi)
                d = random.uniform(1.0, region_dur * 0.6)
                v = random.randint(35, 70)
                notes.append(NoteInfo(pitch=p, start=t, duration=d, velocity=v))
        return notes

    def _pointillist(self, lo: int, hi: int, dur: float, key: Scale) -> list[NoteInfo]:
        """Isolated, scattered individual notes — Webern-inspired."""
        notes: list[NoteInfo] = []
        n_events = max(5, int(dur * self.density * 1.5))

        for _ in range(n_events):
            t = random.uniform(0, dur)
            p = random.randint(lo, hi)
            d = random.uniform(0.1, 0.5)  # Very short
            v = random.randint(50, 100)     # Can be quite loud
            notes.append(NoteInfo(pitch=p, start=t, duration=d, velocity=v))
        return notes

    def _textural_cloud(self, lo: int, hi: int, dur: float, key: Scale) -> list[NoteInfo]:
        """Xenakis-inspired: statistical density cloud."""
        notes: list[NoteInfo] = []

        # Cloud parameters
        cloud_center = (lo + hi) // 2
        cloud_spread = (hi - lo) // 3
        n_events = max(10, int(dur * self.density * 4))

        for _ in range(n_events):
            t = random.uniform(0, dur)
            # Gaussian-ish distribution around center
            p = int(random.gauss(cloud_center, cloud_spread / 2))
            p = max(lo, min(hi, p))
            d = random.uniform(0.25, 3.0)
            v = random.randint(25, 65)
            notes.append(NoteInfo(pitch=p, start=t, duration=d, velocity=v))
        return notes
