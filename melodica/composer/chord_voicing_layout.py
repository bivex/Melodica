# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
composer/chord_voicing_layout.py — Orchestral chord voicing layout.
Voices a chord progression across multiple orchestral instruments following
classical voice leading and orchestration rules.
"""

from __future__ import annotations

import copy
import bisect
from typing import Any
from melodica.types import ChordLabel, NoteInfo, Scale, Mode

INSTRUMENT_RANGES: dict[str, tuple[int, int]] = {
    # Strings
    "double_bass": (24, 53),
    "contrabass": (24, 53),
    "cello": (36, 67),
    "viola": (48, 79),
    "violin": (55, 88),
    "strings": (36, 88),
    # Woodwinds
    "piccolo": (74, 102),
    "flute": (60, 96),
    "oboe": (58, 91),
    "clarinet": (50, 89),
    "bassoon": (34, 67),
    # Brass
    "trumpet": (54, 82),
    "horn": (34, 69),
    "french_horn": (34, 69),
    "trombone": (34, 67),
    "tuba": (28, 55),
    # Keys/Plucked/Perc (sparkling/bright doublers)
    "glockenspiel": (79, 102),
    "celesta": (60, 96),
    "harp": (30, 90),
    "piano": (21, 108),
}


class ChordVoicingLayout:
    """Orchestral chord voicing layout engine."""

    def __init__(
        self,
        instruments: list[str],
        doubling_hints: dict[str, str] | None = None,
    ) -> None:
        self.instruments = [inst.lower() for inst in instruments]
        self.doubling_hints = doubling_hints or {
            "violin": "glockenspiel",
            "celesta": "piccolo",
            "flute": "violin",
            "double_bass": "cello",
        }

    def _get_instrument_midpoint(self, inst: str) -> float:
        low, high = INSTRUMENT_RANGES.get(inst, (48, 72))
        return (low + high) / 2.0

    def voice_chord(
        self,
        chord: ChordLabel,
        melody_pitch: int | None = None,
    ) -> dict[str, int]:
        """Voice a single chord across the configured instruments."""
        # 1. Separate independent instruments from doublers
        unique_insts = list(set(self.instruments))
        independent_insts = []
        for inst in unique_insts:
            is_doubler = False
            for parent, child in self.doubling_hints.items():
                if inst == child and parent in unique_insts:
                    is_doubler = True
                    break
            if not is_doubler:
                independent_insts.append(inst)
        
        # If all were flagged as doublers, fallback to unique_insts to avoid empty voicing
        if not independent_insts:
            independent_insts = unique_insts

        sorted_insts = sorted(independent_insts, key=self._get_instrument_midpoint)

        if not sorted_insts:
            return {}

        # 2. Extract chord pitch classes
        pcs = chord.pitch_classes()
        if not pcs:
            pcs = [0, 4, 7]  # default to C major if empty

        root_pc = chord.root % 12
        if hasattr(chord.quality, "is_minor"):
            is_minor = chord.quality.is_minor
            is_diminished = chord.quality.is_diminished
            is_augmented = chord.quality.is_augmented
        else:
            qual_str = str(chord.quality).lower()
            is_minor = "min" in qual_str or "dim" in qual_str or "half" in qual_str
            is_diminished = "dim" in qual_str
            is_augmented = "aug" in qual_str

        third_pc = (root_pc + (3 if is_minor else 4)) % 12
        fifth_pc = (root_pc + (6 if is_diminished else (8 if is_augmented else 7))) % 12

        # 3. Assign pitches to instruments from bottom to top
        voicings: dict[str, int] = {}
        assigned_pitches: list[int] = []

        for idx, inst in enumerate(sorted_insts):
            low, high = INSTRUMENT_RANGES.get(inst, (48, 72))

            # Rules:
            # - Bass (lowest instrument) = Root
            if idx == 0:
                best_pitch = 48
                for p in range(low, high + 1):
                    if p % 12 == root_pc:
                        best_pitch = p
                        break
                voicings[inst] = best_pitch
                assigned_pitches.append(best_pitch)

            # - Top (highest instrument) = Melody or highest chord tone
            elif idx == len(sorted_insts) - 1:
                if melody_pitch is not None:
                    # Snap melody pitch to the instrument's range
                    best_pitch = max(low, min(high, melody_pitch))
                    # Optionally snap to nearest chord PC if close
                    melody_pc = best_pitch % 12
                    if melody_pc not in pcs:
                        # find closest pc
                        closest_pc = min(pcs, key=lambda x: min(abs(x - melody_pc), 12 - abs(x - melody_pc)))
                        diff = (closest_pc - melody_pc)
                        if diff > 6:
                            diff -= 12
                        elif diff < -6:
                            diff += 12
                        best_pitch = max(low, min(high, best_pitch + diff))
                else:
                    # Default: Highest pitch class of the chord in the upper register
                    best_pitch = high
                    for p in range(high, low - 1, -1):
                        if p % 12 in (third_pc, fifth_pc, root_pc):
                            best_pitch = p
                            break
                voicings[inst] = best_pitch
                assigned_pitches.append(best_pitch)

            # - Inner voices = Fifths, thirds, or other chord tones
            else:
                # Distribute third / fifth to avoid duplicate scale degrees close together
                prev_pitch = assigned_pitches[-1] if assigned_pitches else 48
                target_pc = third_pc if idx % 2 == 1 else fifth_pc
                if target_pc not in pcs:
                    target_pc = pcs[0]

                # Find pitch in range closest above prev_pitch
                best_pitch = prev_pitch + 4
                min_diff = 999
                for p in range(low, high + 1):
                    if p % 12 == target_pc:
                        diff = abs(p - (prev_pitch + 7))  # target perfect fifth above previous for good spacing
                        if diff < min_diff:
                            min_diff = diff
                            best_pitch = p

                voicings[inst] = best_pitch
                assigned_pitches.append(best_pitch)

        # 4. Handle doubling hints (e.g. glockenspiel doubles violin, piccolo doubles celesta, cello doubles double bass)
        # Apply doublings for instruments that are requested but were collapsed in unique_insts,
        # or special instrument combinations.
        final_voicings: dict[str, int] = {}
        for inst in self.instruments:
            if inst in voicings:
                final_voicings[inst] = voicings[inst]
            else:
                # Resolve doubling
                doubled_inst = None
                for key, val in self.doubling_hints.items():
                    if inst == val and key in voicings:
                        doubled_inst = key
                        break
                    elif inst == key and val in voicings:
                        doubled_inst = val
                        break

                if doubled_inst:
                    base_pitch = voicings[doubled_inst]
                    low, high = INSTRUMENT_RANGES.get(inst, (48, 72))
                    # Shift pitch up or down to fit in doubler's range
                    shifted_pitch = base_pitch
                    if inst in ("glockenspiel", "piccolo"):
                        shifted_pitch += 12
                        if shifted_pitch < low:
                            shifted_pitch += 12
                    elif inst == "double_bass":
                        shifted_pitch -= 12
                        if shifted_pitch > high:
                            shifted_pitch -= 12
                    # Clamp
                    shifted_pitch = max(low, min(high, shifted_pitch))
                    final_voicings[inst] = shifted_pitch
                else:
                    # Fallback: assign to the midpoint pitch class
                    fallback_pc = pcs[0]
                    low, high = INSTRUMENT_RANGES.get(inst, (48, 72))
                    best_p = (low + high) // 2
                    for p in range(low, high + 1):
                        if p % 12 == fallback_pc:
                            best_p = p
                            break
                    final_voicings[inst] = best_p

        return final_voicings

    def layout_progression(
        self,
        chords: list[ChordLabel],
        melody_notes: list[NoteInfo] | None = None,
    ) -> dict[str, list[NoteInfo]]:
        """Voice a full chord progression across the instruments."""
        result: dict[str, list[NoteInfo]] = {inst: [] for inst in self.instruments}
        if not chords:
            return result

        # Pre-sort melody notes by start time if provided
        melody_starts = []
        if melody_notes:
            melody_notes = sorted(melody_notes, key=lambda x: x.start)
            melody_starts = [n.start for n in melody_notes]

        for chord in chords:
            # 1. Determine melody pitch during this chord
            melody_pitch = None
            if melody_notes:
                idx = bisect.bisect_right(melody_starts, chord.start) - 1
                if 0 <= idx < len(melody_notes):
                    melody_pitch = melody_notes[idx].pitch

            # 2. Get voicing mapping for this chord
            voicing = self.voice_chord(chord, melody_pitch=melody_pitch)

            # 3. Create NoteInfo for each instrument
            for inst, pitch in voicing.items():
                # We need to map back to original casing if requested,
                # but dict keys in result are lowercased here.
                # Let's write notes to all matching instruments in self.instruments
                note = NoteInfo(
                    pitch=pitch,
                    start=chord.start,
                    duration=chord.duration,
                    velocity=80,
                )
                # Find matching keys in result (lowercase matches)
                for r_key in result:
                    if r_key.lower() == inst.lower():
                        result[r_key].append(copy.copy(note))

        # Sort all lists
        for inst in result:
            result[inst] = sorted(result[inst], key=lambda x: x.start)

        return result
