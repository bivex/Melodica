# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/arpeggiator.py — ArpeggiatorGenerator.

Layer: Application / Domain

Expands each chord into a sequence of its tones in a given pattern,
repeating until duration_beats is covered.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.rhythm import RhythmEvent, RhythmGenerator
from melodica.render_context import RenderContext
from melodica import types
from melodica.utils import chord_pitches_closed, chord_pitches_open, chord_pitches_spread, snap_to_scale


PATTERNS = frozenset(
    {
        # Classic direction patterns
        "up",
        "down",
        "up_down",
        "down_up",
        "up_down_full",
        "down_up_full",
        # Structural patterns
        "converge",
        "diverge",
        "con_diverge",
        # Guitar fingerpicking
        "pinky_up_down",
        "pinky_up",
        "thumb_up_down",
        "thumb_up",
        # Random
        "random",
        "random_neighbor",
        # Block chord
        "chord",
        # Genre-specific patterns
        "alberti",  # classical broken chord (low-high-mid-high)
        "octave",  # EDM/trance — root + octave pumping
        "octave_up",  # ascending octave doublings
        "octave_pump",  # octave pump (root-octave-root-octave)
        "neighbor_up",  # ornamental — each tone with upper neighbor
        "waltz",  # waltz bass (root, 5th, 8th per chord)
        "broken_chord",  # ascending then next chord from top
        "arpeggio_up",  # classical baroque — up then up from next chord
        "power",  # rock — root + 5th only
        "fifth_circle",  # cycle through 5ths (root-5th-9th-...)
    }
)
VOICINGS = frozenset({"closed", "open", "spread"})


@dataclass
class ArpeggiatorGenerator(PhraseGenerator):
    """
    Arpeggiator — cycles chord tones in configurable order.

    pattern:
        "up"              – ascending
        "down"            – descending
        "up_down"         – ascending then descending (no duplicate endpoints)
        "down_up"         – descending then ascending (no duplicate endpoints)
        "up_down_full"    – ascending then full descending
        "down_up_full"    – descending then full ascending
        "converge"        – edges toward center
        "diverge"         – center toward edges
        "con_diverge"     – converge then diverge
        "pinky_up_down"   – from top note, ascending then descending
        "pinky_up"        – from top note, ascending
        "thumb_up_down"   – from bottom note, ascending then descending
        "thumb_up"        – from bottom note, ascending
        "random"          – shuffled
        "random_neighbor" – each step picks a neighboring pitch at random
        "chord"           – block chord

        Genre-specific:
        "alberti"         – classical broken chord: low, high, mid, high
        "octave"          – EDM/trance: root pitch across octaves
        "octave_up"       – ascending octave doublings of all pitch classes
        "octave_pump"     – root ↔ octave pumping
        "neighbor_up"     – ornamental: each tone with upper neighbor
        "waltz"           – waltz bass: root, 5th, octave
        "broken_chord"    – ascending then next chord from top
        "arpeggio_up"     – baroque: ascending sweep then restart
        "power"           – rock: root + 5th only
        "fifth_circle"    – cycle through 5ths (root, 5th, 9th, ...)

    note_duration: beats per arp note
    """

    name: str = "Arpeggiator"
    pattern: str = "up"
    note_duration: float = 0.25
    voicing: str = "closed"
    octaves: int = 1
    rhythm: RhythmGenerator | None = None

    def __init__(
        self,
        params: GeneratorParams | None = None,
        *,
        pattern: str = "up",
        note_duration: float = 0.25,
        voicing: str = "closed",
        octaves: int = 1,
        rhythm: RhythmGenerator | None = None,
    ) -> None:
        super().__init__(params)
        if pattern not in PATTERNS:
            raise ValueError(f"pattern must be one of {sorted(PATTERNS)}; got {pattern!r}")
        if voicing not in VOICINGS:
            raise ValueError(f"voicing must be one of {sorted(VOICINGS)}; got {voicing!r}")
        self.pattern = pattern
        self.note_duration = note_duration
        self.voicing = voicing
        self.octaves = max(1, octaves)
        self.rhythm = rhythm

    def render(
        self,
        chords: list[types.ChordLabel],
        key: types.Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[types.NoteInfo]:
        if not chords:
            return []

        events = self._build_events(duration_beats)
        notes: list[types.NoteInfo] = []

        chord_idx = 0
        current_pitches = self._pitches_for_chord(chords[0])
        seq = self._make_sequence(current_pitches)
        seq_pos = 0
        last_pitch: int | None = None

        for event in events:
            # Advance chord if needed
            while chord_idx + 1 < len(chords) and event.onset >= chords[chord_idx + 1].start:
                chord_idx += 1
                current_pitches = self._pitches_for_chord(chords[chord_idx])
                seq = self._make_sequence(current_pitches)
                if last_pitch is not None:
                    seq_pos = self._continue_sequence(seq, last_pitch)
                else:
                    seq_pos = 0

            if not seq:
                continue

            base_vel = self._velocity()

            if self.pattern == "chord":
                vel = int(base_vel * event.velocity_factor)
                notes.extend(self._render_block_chord(current_pitches, event, vel))
                if current_pitches:
                    last_pitch = current_pitches[-1]
            else:
                accent = 1.15 if seq_pos % len(seq) == 0 else 1.0
                vel = int(base_vel * accent * event.velocity_factor)
                pitch = seq[seq_pos % len(seq)]
                seq_pos += 1
                notes.append(
                    types.NoteInfo(
                        pitch=pitch,
                        start=round(event.onset, 6),
                        duration=event.duration,
                        velocity=max(0, min(types.MIDI_MAX, vel)),
                    )
                )
                last_pitch = pitch

        if notes:
            self._last_context = (context or RenderContext()).with_end_state(
                last_pitch=notes[-1].pitch,
                last_velocity=notes[-1].velocity,
                last_chord=chords[chord_idx] if chords else None,
                last_pitches=[notes[-1].pitch],
            )

        return notes

    def _render_block_chord(
        self, pitches: list[int], event: RhythmEvent, vel: int
    ) -> list[types.NoteInfo]:
        return [
            types.NoteInfo(
                pitch=p,
                start=round(event.onset, 6),
                duration=event.duration,
                velocity=max(0, min(types.MIDI_MAX, vel)),
            )
            for p in pitches
        ]

    # ------------------------------------------------------------------

    def _build_events(self, duration_beats: float) -> list[RhythmEvent]:
        if self.rhythm is not None:
            return self.rhythm.generate(duration_beats)
        t, events = 0.0, []
        while t < duration_beats:
            events.append(RhythmEvent(onset=round(t, 6), duration=self.note_duration * 0.95))
            t += self.note_duration
        return events

    def _pitches_for_chord(self, chord: types.ChordLabel) -> list[int]:
        if self.voicing == "open":
            base_pitches = chord_pitches_open(chord, self.params.key_range_low)
        elif self.voicing == "spread":
            base_pitches = chord_pitches_spread(chord, self.params.key_range_low)
        else:
            base_pitches = chord_pitches_closed(chord, self.params.key_range_low)

        pitches = list(base_pitches)
        for i in range(1, self.octaves):
            pitches.extend([snap_to_scale(p + types.OCTAVE * i, key) for p in base_pitches])

        return sorted(list(set(pitches)))

    def _make_sequence(self, pitches: list[int]) -> list[int]:
        if not pitches:
            return []
        n = len(pitches)
        match self.pattern:
            case "up":
                return sorted(pitches)
            case "down":
                return sorted(pitches, reverse=True)
            case "up_down":
                # Up then back down, endpoints not repeated
                # [0,1,2,3] → [0,1,2,3,2,1]
                up = sorted(pitches)
                return up + up[-2:0:-1]
            case "down_up":
                # Down then back up, endpoints not repeated
                # [0,1,2,3] → [3,2,1,0,1,2]
                dn = sorted(pitches, reverse=True)
                return dn + dn[-2:0:-1]
            case "up_down_full":
                # Up then full descending (endpoints repeated at junction)
                # [0,1,2,3] → [0,1,2,3,3,2,1,0]
                up = sorted(pitches)
                return up + up[::-1]
            case "down_up_full":
                # Down then full ascending (endpoints repeated at junction)
                # [0,1,2,3] → [3,2,1,0,0,1,2,3]
                dn = sorted(pitches, reverse=True)
                return dn + dn[::-1]
            case "converge":
                # Edges toward center: first, last, 2nd, 2nd-last, ...
                # [0,1,2,3,4] → [0,4,1,3,2]
                # [0,1,2,3]   → [0,3,1,2]
                up = sorted(pitches)
                result = []
                lo, hi = 0, n - 1
                while lo <= hi:
                    result.append(up[lo])
                    if lo != hi:
                        result.append(up[hi])
                    lo += 1
                    hi -= 1
                return result
            case "diverge":
                # Center toward edges: mid, mid+1, mid-1, ...
                # [0,1,2,3,4] → [2,3,1,4,0]
                # [0,1,2,3]   → [1,2,0,3]
                up = sorted(pitches)
                result = []
                mid = n // 2
                offset = 0
                while len(result) < n:
                    if offset == 0:
                        result.append(up[mid])
                    else:
                        if mid + offset < n:
                            result.append(up[mid + offset])
                        if mid - offset >= 0 and len(result) < n:
                            result.append(up[mid - offset])
                    offset += 1
                return result[:n]
            case "con_diverge":
                # Converge then diverge (without repeating center)
                # [0,1,2,3,4] → [0,4,1,3,2,3,1,4,0]
                up = sorted(pitches)
                con = []
                lo, hi = 0, n - 1
                while lo <= hi:
                    con.append(up[lo])
                    if lo != hi:
                        con.append(up[hi])
                    lo += 1
                    hi -= 1
                # diverge part: con[-2] back outward (skip center which is con[-1])
                return con + con[-2::-1]
            case "pinky_up_down":
                # From top note, ascending (wrapping), then descending (wrapping)
                # [0,1,2,3] → [3,0,1,2,1,0,3]
                up = sorted(pitches)
                asc = [up[-1]] + up[:-1]  # start from top, wrap
                desc = list(reversed(asc[1:-1]))  # back without endpoints
                return asc + desc
            case "pinky_up":
                # From top note, ascending (wrapping)
                # [0,1,2,3] → [3,0,1,2]
                up = sorted(pitches)
                return [up[-1]] + up[:-1]
            case "thumb_up_down":
                # Mirror of pinky_up_down: from bottom note, descend (wrapping to top),
                # then ascend back — the thumb's view of the keyboard.
                # [0,1,2,3] → [0,3,2,1,2,3]
                up = sorted(pitches)
                dn = [up[0]] + up[1:][::-1]
                return dn + dn[-2:0:-1]
            case "thumb_up":
                # From bottom note, descend (wrapping to top)
                # Mirror of pinky_up: [0,1,2,3] → [0,3,2,1]
                up = sorted(pitches)
                return [up[0]] + up[1:][::-1]
            case "random":
                shuffled = list(pitches)
                random.shuffle(shuffled)
                return shuffled
            case "random_neighbor":
                # Random walk: each step moves ±1 index
                return self._random_neighbor_walk(pitches)

            # --- Genre-specific patterns ---

            case "alberti":
                # Classical broken chord: low, high, mid, high
                # [0,1,2,3] → [0,3,1,3,0,3,1,3]
                # [0,1,2]   → [0,2,1,2]
                up = sorted(pitches)
                if n < 3:
                    return up * 4
                low, mid, high = up[0], up[1], up[-1]
                return [low, high, mid, high]

            case "octave":
                # EDM/trance: root pitch class across octaves (ascending)
                # Extract unique pitch classes, take root, pump through octaves
                # [48,52,55,60,64,67] → [48,60,72,84] (root = 48, pitch class 0)
                pcs = sorted({p % 12 for p in pitches})
                root_pc = pcs[0]
                octave_pitches = sorted(p for p in pitches if p % 12 == root_pc)
                return octave_pitches if octave_pitches else sorted(pitches)

            case "octave_up":
                # Ascending octave doublings: each pitch class going up
                # [48,52,55] → [48,52,55] (single octave, just ascending)
                # With octaves > 1: natural ascending order already works
                return sorted(pitches)

            case "octave_pump":
                # Root ↔ octave pumping
                # For each unique pitch class: play low then high octave
                # [48,52,55,60,64,67] → [48,60,52,64,55,67]
                pcs = sorted({p % 12 for p in pitches})
                result = []
                for pc in pcs:
                    low = min(p for p in pitches if p % 12 == pc)
                    high = max(p for p in pitches if p % 12 == pc)
                    result.append(low)
                    if high != low:
                        result.append(high)
                return result

            case "neighbor_up":
                # Ornamental: each ascending step includes upper neighbor
                # [60,64,67] → [60,64,64,67,67,64]
                # [0,1,2,3] → [0,1,1,2,2,3,3,2]
                up = sorted(pitches)
                result = []
                for i, p in enumerate(up):
                    result.append(p)
                    neighbor = up[min(i + 1, n - 1)]
                    if neighbor != p:
                        result.append(neighbor)
                # Descend back (skip last which was already added as neighbor)
                for i in range(n - 2, -1, -1):
                    result.append(up[i])
                return result

            case "waltz":
                # Waltz bass: root, 5th, octave
                # For 3+ note chord: 1st, 2nd, 3rd... then cycle
                # Typically: [0,2,4] indices → root, fifth, octave
                # [0,1,2] → [0,2,0] (root, fifth, root)
                up = sorted(pitches)
                if n < 3:
                    return up * 3
                # Pick root (index 0), fifth (index ~n//2), and top (last)
                root = up[0]
                fifth = up[n // 2]
                octave = up[-1]
                return [root, fifth, octave]

            case "broken_chord":
                # Ascending sweep then drop to next chord from top
                # Like baroque broken chord: go up, then jump down
                # [0,1,2,3] → [0,1,2,3,0,1,2,3]
                return sorted(pitches)

            case "arpeggio_up":
                # Baroque ascending sweep — same as up (context-dependent)
                return sorted(pitches)

            case "power":
                # Rock power chord: root + 5th only
                # From any chord, extract root and fifth
                up = sorted(pitches)
                if n < 2:
                    return up * 2
                return [up[0], up[n // 2]]

            case "fifth_circle":
                # Cycle through 5ths: root, 5th, 9th(=2nd), ...
                # Walk by perfect 5th intervals (7 semitones)
                # [48,52,55] → [48,55,52] (root, fifth, third — by fifths)
                up = sorted(pitches)
                root = up[0]
                fifth_chain = []
                current_pc = root % 12
                visited = set()
                while current_pc not in visited and len(fifth_chain) < n:
                    visited.add(current_pc)
                    # Find the pitch with this pitch class
                    matches = [p for p in up if p % 12 == current_pc]
                    if matches:
                        fifth_chain.append(matches[0])
                    current_pc = (current_pc + 7) % 12
                # Fill remaining with unvisited pitch classes
                for p in up:
                    if p not in fifth_chain:
                        fifth_chain.append(p)
                return fifth_chain

            case _:
                return sorted(pitches)

    def _random_neighbor_walk(self, pitches: list[int], length: int = 64) -> list[int]:
        """Generate a random walk over sorted pitches, each step ±1 index."""
        up = sorted(pitches)
        n = len(up)
        if n <= 1:
            return list(up) * length
        walk = [random.randint(0, n - 1)]
        for _ in range(length - 1):
            prev = walk[-1]
            if prev == 0:
                walk.append(1)
            elif prev == n - 1:
                walk.append(n - 2)
            else:
                walk.append(prev + random.choice([-1, 1]))
        return [up[i] for i in walk]

    def _continue_sequence(self, new_seq: list[int], last_pitch: int) -> int:
        """Find the index in new_seq closest to last_pitch."""
        if not new_seq:
            return 0
        return min(range(len(new_seq)), key=lambda i: abs(new_seq[i] - last_pitch))

    def _velocity(self) -> int:
        return int(55 + self.params.density * 45)
