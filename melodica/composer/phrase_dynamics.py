"""composer/phrase_dynamics.py — Per-phrase dynamic breathing.

Applies a natural phrase arc to each detected phrase in a melody:
  - crescendo from phrase start to ~65% of phrase length
  - diminuendo from 65% to phrase end
  - last note of phrase gets a slight diminuendo tail (-8 vel)
  - first note of phrase gets a slight accent (+5 vel)

Phrase boundaries are detected by:
  1. Explicit rest gaps >= gap_threshold beats
  2. Long notes (duration >= phrase_note_threshold beats)

Usage:
    from melodica.composer.phrase_dynamics import PhraseDynamicsShaper
    shaped = PhraseDynamicsShaper(phrase_beats=8.0).apply(notes)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

from melodica.types_pkg._notes import NoteInfo


@dataclass
class PhraseDynamicsShaper:
    """Apply per-phrase crescendo/diminuendo breathing to a note list.

    Parameters
    ----------
    phrase_beats : float
        Expected phrase length in beats. Used as fallback when gap detection
        fails to find natural boundaries (default: 8.0 = 2 bars at 4/4).
    gap_threshold : float
        Rest gap >= this value triggers a new phrase (default: 0.5 beats).
    cresc_peak : float
        Fraction of phrase at which crescendo peaks (default: 0.65).
    cresc_gain : float
        Max velocity gain at peak relative to phrase average (default: 12).
    dim_loss : float
        Velocity reduction at phrase end relative to peak (default: 18).
    tail_loss : int
        Extra velocity reduction on the final note of each phrase (default: 8).
    head_gain : int
        Extra velocity boost on the first note of each phrase (default: 5).
    role_scale : dict
        Per-role scaling of gain/loss. Defaults: bass=0.4, pad=0.5, choir=0.7,
        strings=1.0, lead=1.0, perc=0.0.
    """

    phrase_beats: float = 8.0
    gap_threshold: float = 0.5
    cresc_peak: float = 0.65
    cresc_gain: float = 12.0
    dim_loss: float = 18.0
    tail_loss: int = 8
    head_gain: int = 5
    role_scale: dict[str, float] = field(default_factory=lambda: {
        "bass":    0.35,
        "pedal":   0.20,
        "pad":     0.50,
        "choir":   0.75,
        "strings": 1.00,
        "violin":  1.00,
        "viola":   0.95,
        "cello":   0.90,
        "lead":    1.00,
        "flute":   1.00,
        "oboe":    0.95,
        "clarinet":1.00,
        "horn":    0.85,
        "brass":   0.80,
        "harp":    0.70,
        "glock":   0.60,
        "perc":    0.00,   # percussion: no phrase shaping
        "timp":    0.20,
    })

    def _scale_for(self, track_name: str) -> float:
        """Lookup role scale from track name (substring match)."""
        name = track_name.lower()
        for key, scale in self.role_scale.items():
            if key in name:
                return scale
        return 0.80  # default

    def apply(
        self,
        notes: List[NoteInfo],
        track_name: str = "lead",
    ) -> List[NoteInfo]:
        """Return new notes with phrase dynamic shaping applied."""
        if not notes:
            return notes

        scale = self._scale_for(track_name)
        if scale == 0.0:
            return list(notes)

        phrases = self._detect_phrases(notes)
        result: List[NoteInfo] = []

        for phrase in phrases:
            result.extend(self._shape_phrase(phrase, scale))

        return result

    def apply_tracks(
        self,
        tracks: dict[str, List[NoteInfo]],
    ) -> dict[str, List[NoteInfo]]:
        """Apply phrase shaping to all tracks in a dict."""
        return {name: self.apply(notes, name) for name, notes in tracks.items()}

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _detect_phrases(self, notes: List[NoteInfo]) -> List[List[NoteInfo]]:
        """Split notes into phrases by rest gaps."""
        if not notes:
            return []

        sorted_notes = sorted(notes, key=lambda n: n.start)
        phrases: List[List[NoteInfo]] = []
        current: List[NoteInfo] = [sorted_notes[0]]

        for prev, curr in zip(sorted_notes, sorted_notes[1:]):
            gap = curr.start - (prev.start + prev.duration)
            if gap >= self.gap_threshold:
                phrases.append(current)
                current = [curr]
            else:
                current.append(curr)

        if current:
            phrases.append(current)

        # Split long phrases into phrase_beats chunks if no natural gaps
        result: List[List[NoteInfo]] = []
        for phrase in phrases:
            if not phrase:
                continue
            p_start = phrase[0].start
            p_end = phrase[-1].start + phrase[-1].duration
            p_len = p_end - p_start
            if p_len <= self.phrase_beats * 1.5:
                result.append(phrase)
            else:
                # Force-split by phrase_beats
                sub: List[NoteInfo] = []
                chunk_start = p_start
                for n in phrase:
                    if n.start >= chunk_start + self.phrase_beats and sub:
                        result.append(sub)
                        sub = []
                        chunk_start = n.start
                    sub.append(n)
                if sub:
                    result.append(sub)

        return result

    def _shape_phrase(
        self,
        phrase: List[NoteInfo],
        scale: float,
    ) -> List[NoteInfo]:
        """Apply crescendo arch to a single phrase."""
        if not phrase:
            return []

        p_start = phrase[0].start
        p_end = phrase[-1].start + phrase[-1].duration
        p_len = max(p_end - p_start, 0.001)
        peak_beat = p_start + p_len * self.cresc_peak

        shaped: List[NoteInfo] = []
        for i, n in enumerate(phrase):
            pos = (n.start - p_start) / p_len  # 0.0 .. 1.0
            is_first = (i == 0)
            is_last = (i == len(phrase) - 1)

            # Phrase arch: rise to cresc_peak, fall after
            if pos <= self.cresc_peak:
                # crescendo: 0 → cresc_gain
                t = pos / self.cresc_peak
                delta = self.cresc_gain * scale * _ease_in(t)
            else:
                # diminuendo: cresc_gain → 0 → -dim_loss
                t = (pos - self.cresc_peak) / (1.0 - self.cresc_peak)
                delta = self.cresc_gain * scale * (1.0 - t) - self.dim_loss * scale * t

            # Head accent
            if is_first:
                delta += self.head_gain * scale

            # Tail diminuendo
            if is_last:
                delta -= self.tail_loss * scale

            new_vel = max(8, min(127, round(n.velocity + delta)))
            shaped.append(NoteInfo(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=new_vel,
                articulation=n.articulation,
                expression=n.expression,
            ))

        return shaped


def _ease_in(t: float) -> float:
    """Smooth ease-in curve (sine)."""
    return math.sin(t * math.pi * 0.5)


# ---------------------------------------------------------------------------
# Pipeline integration helper
# ---------------------------------------------------------------------------


def apply_phrase_dynamics_to_pipeline(
    tracks: dict[str, List[NoteInfo]],
    phrase_beats: float = 8.0,
    gap_threshold: float = 0.5,
) -> dict[str, List[NoteInfo]]:
    """Convenience wrapper for use in album pipeline stages."""
    shaper = PhraseDynamicsShaper(
        phrase_beats=phrase_beats,
        gap_threshold=gap_threshold,
    )
    return shaper.apply_tracks(tracks)
