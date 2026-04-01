"""
generators/clusters.py — Tone cluster generator.

Layer: Application / Domain
Style: Avant-garde, experimental, film scoring, noise.

Tone clusters are groups of adjacent notes played simultaneously,
creating dense, dissonant, or atmospheric textures.

Types:
    "second"    — clusters of major/minor seconds
    "fourth"    — clusters of perfect fourths
    "mixed"     — alternating second and fourth clusters
    "white_key" — clusters using only white keys (diatonic)
    "chromatic" — full chromatic clusters
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
class ClusterGenerator(PhraseGenerator):
    """
    Tone cluster generator.

    cluster_type:
        "second", "fourth", "mixed", "white_key", "chromatic"
    cluster_width:
        Number of notes in each cluster (2–6).
    duration_per_cluster:
        Duration of each cluster in beats.
    movement:
        How clusters move between events:
        "step" — move by one semitone
        "random" — random position
        "follow_chord" — center on chord root
    """

    name: str = "Cluster Generator"
    cluster_type: str = "second"
    cluster_width: int = 3
    duration_per_cluster: float = 2.0
    movement: str = "follow_chord"
    rhythm: RhythmGenerator | None = None
    _last_context: RenderContext | None = field(default=None, init=False, repr=False)

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        cluster_type: str = "second",
        cluster_width: int = 3,
        duration_per_cluster: float = 2.0,
        movement: str = "follow_chord",
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        self.cluster_type = cluster_type
        self.cluster_width = max(2, min(6, cluster_width))
        self.duration_per_cluster = max(0.25, min(8.0, duration_per_cluster))
        self.movement = movement
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
        mid = (low + high) // 2

        prev_center = mid
        last_chord: ChordLabel | None = None

        for event in events:
            chord = chord_at(chords, event.onset)
            if chord is None:
                continue
            last_chord = chord

            # Center of the cluster
            if self.movement == "follow_chord":
                center = nearest_pitch(chord.root, prev_center)
            elif self.movement == "step":
                center = prev_center + random.choice([-1, 0, 1])
            else:
                center = random.randint(low + 6, high - 6)

            center = max(low + self.cluster_width, min(high - self.cluster_width, center))

            # Build cluster pitches
            cluster_pitches = self._build_cluster(center, key, low, high)
            vel = self._velocity()
            dur = min(self.duration_per_cluster, duration_beats - event.onset)

            if dur <= 0:
                continue

            for p in cluster_pitches:
                notes.append(
                    NoteInfo(
                        pitch=p,
                        start=round(event.onset, 6),
                        duration=dur,
                        velocity=max(1, min(127, vel)),
                    )
                )

            prev_center = center

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=last_chord,
            )
        return notes

    def _build_cluster(self, center: int, key: Scale, low: int, high: int) -> list[int]:
        w = self.cluster_width
        half = w // 2

        if self.cluster_type == "second":
            return [max(low, min(high, center - half + i)) for i in range(w)]

        elif self.cluster_type == "fourth":
            return [max(low, min(high, center + i * 5)) for i in range(-half + 1, half + 1)]

        elif self.cluster_type == "mixed":
            if random.random() < 0.5:
                return [max(low, min(high, center - half + i)) for i in range(w)]
            else:
                return [max(low, min(high, center + i * 5)) for i in range(-half + 1, half + 1)]

        elif self.cluster_type == "white_key":
            # Use only diatonic pitches
            degs = [int(d) for d in key.degrees()]
            pitches = []
            for i in range(-half, half + 1):
                pc = (center + i * 2) % 12
                if key.contains(pc):
                    pitches.append(max(low, min(high, nearest_pitch(pc, center))))
            if not pitches:
                pitches = [max(low, min(high, center))]
            return sorted(set(pitches))[:w]

        elif self.cluster_type == "chromatic":
            return [max(low, min(high, center - half + i)) for i in range(w)]

        return [max(low, min(high, center))]

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            dur = min(self.duration_per_cluster, duration_beats - t)
            events.append(RhythmEvent(onset=round(t, 6), duration=dur))
            t += self.duration_per_cluster
        return events

    def _velocity(self) -> int:
        return int(45 + self.params.density * 30)
