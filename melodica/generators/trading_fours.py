"""Trading fours (and eights) generator.

Simulates the jazz tradition of "trading" — alternating improvised
phrases between two instruments. Used in:
  - Head-solo-head arrangements
  - Jazz battle / cutting contests
  - Educational call-and-response exercises

Structure:
  Player A plays N bars → Player B plays N bars → repeat

Players: Miles Davis / John Coltrane (Kind of Blue),
         Sonny Rollins / Elvin Jones, Wynton Marsalis / ensemble.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale
from melodica.utils import nearest_pitch, snap_to_scale, chord_at


@dataclass
class TradingFoursGenerator(PhraseGenerator):
    """Generate trading 4s/8s between two pitch ranges.

    Parameters
    ----------
    trade_length : int
        Bars per trade (4 = trading fours, 8 = trading eights).
    player_a_range : tuple[int, int]
        (low, high) MIDI pitch range for player A.
    player_b_range : tuple[int, int]
        (low, high) MIDI pitch range for player B.
    style : str
        "call_response" — B answers A's idea.
        "independent" — each player plays their own phrase.
        "escalating" — intensity increases with each trade.
    density : float
        Notes per beat within each trade phrase (0.5–2.0).
    connect_trades : bool
        Smooth connection between end of one trade and start of next.
    """

    name: str = field(default="trading_fours", init=False)
    trade_length: int = 4
    player_a_range: tuple[int, int] = (60, 84)
    player_b_range: tuple[int, int] = (48, 72)
    style: str = "call_response"
    density: float = 1.0
    connect_trades: bool = True
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        if self.trade_length not in (2, 4, 8):
            raise ValueError(f"trade_length must be 2, 4, or 8, got {self.trade_length}")
        valid_styles = ("call_response", "independent", "escalating")
        if self.style not in valid_styles:
            raise ValueError(f"style must be one of {valid_styles}")

    def _build_phrase(
        self,
        chord: ChordLabel,
        key: Scale,
        pitch_range: tuple[int, int],
        n_beats: float,
        prev_phrase: list[int] | None = None,
        escalation: float = 0.0,
    ) -> list[tuple[int, float]]:
        """Build a single trade phrase. Returns list of (pitch, duration)."""
        low, high = pitch_range
        pcs = chord.pitch_classes()
        degs = key.degrees()
        anchor = (low + high) // 2

        notes_per_beat = max(0.5, self.density)
        total_notes = max(1, int(n_beats * notes_per_beat))
        beat_dur = n_beats / total_notes

        result: list[tuple[int, float]] = []

        # If call_response and we have a previous phrase, echo it
        if self.style == "call_response" and prev_phrase:
            # Transpose previous phrase to our range
            for p in prev_phrase[:total_notes]:
                p_clamped = max(low, min(high, p))
                result.append((p_clamped, beat_dur))
            # Pad if needed
            while len(result) < total_notes:
                result.append((max(low, min(high, anchor)), beat_dur))
            return result

        # Generate new phrase
        current = anchor
        for i in range(total_notes):
            if random.random() < 0.55 and pcs:
                pc = int(random.choice(pcs))
            elif degs:
                pc = int(random.choice(degs)) % 12
            else:
                pc = chord.root

            p = nearest_pitch(pc, current)
            p = max(low, min(high, p))

            # Escalation: wider intervals over time
            if self.style == "escalating" and random.random() < escalation * 0.3:
                leap = random.choice([3, 4, 5, 7])
                direction = random.choice([-1, 1])
                p = max(low, min(high, current + direction * leap))

            result.append((p, beat_dur))
            current = p

        return result

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if not chords:
            return []

        base_vel = self.base_velocity()
        notes: list[NoteInfo] = []
        beats_per_trade = self.trade_length * 4  # 4/4 time
        trade_count = 0
        t = 0.0
        prev_phrase: list[int] | None = None

        while t < duration_beats:
            # Determine which player
            is_player_a = (trade_count % 2 == 0)
            pitch_range = self.player_a_range if is_player_a else self.player_b_range

            # Get chord for this trade
            chord = chord_at(chords, t)
            if chord is None:
                t += beats_per_trade
                trade_count += 1
                continue

            # Build phrase
            escalation = min(1.0, trade_count * 0.1) if self.style == "escalating" else 0.0
            phrase = self._build_phrase(
                chord, key, pitch_range,
                beats_per_trade, prev_phrase, escalation,
            )
            prev_phrase = [p for p, _ in phrase]

            # Velocity
            vel = base_vel
            if self.style == "escalating":
                vel = min(127, base_vel + int(escalation * 20))

            # Emit notes
            note_t = t
            for pitch, dur in phrase:
                if note_t >= t + beats_per_trade or note_t >= duration_beats:
                    break
                notes.append(NoteInfo(
                    pitch=pitch,
                    start=round(note_t, 4),
                    duration=dur * 0.85,
                    velocity=max(1, min(127, vel + random.randint(-4, 4))),
                ))
                note_t += dur

            t += beats_per_trade
            trade_count += 1

        return notes
