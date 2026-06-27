# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
voice_leading.py — Post-generation parallel-motion correction.

Corrects parallel fifths and octaves between all pairs of pitched voices
AFTER generation, without touching the generators themselves.

Algorithm (Aldwell & Schachter §11):
  1. Snap all tracks to a beat grid (0.25 beat resolution).
  2. For each consecutive pair of grid slots where two voices share common
     slots, compute the interval at t and t+1.
  3. If interval is a perfect fifth (7 st) or octave (12/24 st) at BOTH
     t and t+1, AND both voices move in the same direction → parallel motion.
  4. Correction: shift the UPPER voice note at t+1 by one octave in the
     direction that breaks the parallelism (oblique motion), clamped to the
     instrument's comfortable range. If no valid octave shift exists, skip
     the note (rest — better than a wrong parallel).

Usage:
    from melodica.voice_leading import correct_parallels
    tracks_data = correct_parallels(tracks_data, instruments=gm_map)
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from melodica.types import NoteInfo

# ---------------------------------------------------------------------------
# Comfortable pitch ranges per GM program number (approximate).
# Used to constrain octave shifts to playable registers.
# ---------------------------------------------------------------------------

# (min_midi, max_midi) comfortable range keyed by GM program (0-indexed).
# Covers the instruments used in Melodica orchestral generators.
_GM_RANGE: dict[int, tuple[int, int]] = {
    # Strings
    40: (55, 103),   # Violin
    41: (48, 91),    # Viola
    42: (36, 79),    # Cello
    43: (28, 60),    # Contrabass
    44: (40, 84),    # Tremolo Strings
    45: (36, 79),    # Pizzicato Strings
    48: (48, 84),    # String Ensemble 1
    49: (48, 84),    # String Ensemble 2
    # Choir
    52: (48, 81),    # Choir Aahs
    53: (48, 81),    # Voice Oohs
    # Brass
    56: (52, 82),    # Trumpet
    57: (36, 72),    # Trombone
    58: (28, 58),    # Tuba
    60: (36, 77),    # French Horn
    61: (36, 77),    # Brass Section
    # Woodwinds
    68: (58, 91),    # Oboe
    71: (50, 91),    # Clarinet
    73: (60, 96),    # Flute
    # Keyboards / Pitched Percussion
     9: (72, 108),   # Glockenspiel (GM channel 10 offset — here program 9)
    11: (60, 96),    # Vibraphone
    12: (36, 96),    # Marimba
    13: (60, 84),    # Xylophone
    # Harp / Piano
     0: (21, 108),   # Piano
    46: (24, 103),   # Orchestral Harp
    47: (36, 60),    # Timpani
    # Synth / Pads
    38: (24, 60),    # Synth Bass 1
    39: (24, 60),    # Synth Bass 2
    80: (55, 108),   # Synth Lead 1
    81: (55, 108),   # Synth Lead 2
    88: (48, 96),    # Pad 1 (New Age)
    89: (48, 96),    # Pad 2 (Warm)
    92: (48, 96),    # Pad 5 (Bowed)
}

_DEFAULT_RANGE = (24, 108)  # fallback if program unknown


def _get_range(program: int | None) -> tuple[int, int]:
    if program is None:
        return _DEFAULT_RANGE
    return _GM_RANGE.get(program, _DEFAULT_RANGE)


# ---------------------------------------------------------------------------
# Core correction
# ---------------------------------------------------------------------------

_PARALLEL_RAW = {7, 12, 24}       # raw semitone intervals that matter
_PARALLEL_MOD = {7, 0}            # mod-12 equivalents (0 = octave/unison)
_SAMPLE = 0.25                     # beat grid resolution
_MIN_INSTANCES = 1                 # fix any parallel found (validator fires at ≥2, but 1 found pair can become 2 after octave shift)


def correct_parallels(
    tracks_data: dict[str, list[NoteInfo]],
    instruments: dict[str, int] | None = None,
) -> dict[str, list[NoteInfo]]:
    """Return a corrected copy of tracks_data with parallel 5ths/8ths resolved.

    tracks_data: { "TrackName": [NoteInfo, ...] }
    instruments: { "TrackName": gm_program } — used for range clamping.
                 Tracks absent from the map use a wide default range.

    Returns a new dict; original notes are not mutated.
    """
    from melodica.form_validator import _is_percussion

    # Work on mutable copies (replace() produces new NoteInfo instances)
    result: dict[str, list[NoteInfo]] = {
        name: list(notes) for name, notes in tracks_data.items()
    }

    pitched_names = [n for n in result if not n.startswith("_") and not _is_percussion(n) and result[n]]
    if len(pitched_names) < 2:
        return result

    instr = instruments or {}

    # Build index: name → {slot: list_index} for fast lookup & mutation
    def _build_index(notes: list[NoteInfo]) -> dict[int, int]:
        """Map grid slot → index of the lowest-pitched note at that slot."""
        idx: dict[int, int] = {}
        for i, n in enumerate(notes):
            t_start = float(n.start)
            t_end = t_start + float(n.duration)
            slot_s = int(t_start / _SAMPLE)
            slot_e = max(slot_s + 1, int(t_end / _SAMPLE))
            for slot in range(slot_s, slot_e):
                if slot not in idx or int(notes[idx[slot]].pitch) > int(n.pitch):
                    idx[slot] = i
        return idx

    indexes = {name: _build_index(result[name]) for name in pitched_names}

    for i, name_a in enumerate(pitched_names):
        for name_b in pitched_names[i + 1:]:
            idx_a = indexes[name_a]
            idx_b = indexes[name_b]
            common = sorted(set(idx_a) & set(idx_b))
            if len(common) < 2:
                continue

            # First pass: identify parallel instances
            parallel_slots: list[tuple[int, int, bool]] = []  # (s0, s1, is_octave)
            for k in range(len(common) - 1):
                s0, s1 = common[k], common[k + 1]
                if s1 - s0 > 4:
                    continue
                na0 = result[name_a][idx_a[s0]]
                na1 = result[name_a][idx_a[s1]]
                nb0 = result[name_b][idx_b[s0]]
                nb1 = result[name_b][idx_b[s1]]

                pa0, pa1 = int(na0.pitch), int(na1.pitch)
                pb0, pb1 = int(nb0.pitch), int(nb1.pitch)

                raw0 = abs(pa0 - pb0)
                raw1 = abs(pa1 - pb1)
                mod0 = raw0 % 12
                mod1 = raw1 % 12

                is_fifth  = (mod0 == 7 and mod1 == 7)
                is_octave = (raw0 in {0, 12, 24} and raw1 in {0, 12, 24})

                if not (is_fifth or is_octave):
                    continue

                move_a = pa1 - pa0
                move_b = pb1 - pb0
                if move_a == 0 and move_b == 0:
                    continue
                if (move_a >= 0) == (move_b >= 0):  # same direction
                    parallel_slots.append((s0, s1, is_octave))

            if len(parallel_slots) < _MIN_INSTANCES:
                continue

            # Second pass: fix each parallel by shifting upper voice at s1
            lo_a, hi_a = _get_range(instr.get(name_a))
            lo_b, hi_b = _get_range(instr.get(name_b))

            for s0, s1, is_octave in parallel_slots:
                na1 = result[name_a][idx_a[s1]]
                nb1 = result[name_b][idx_b[s1]]
                pa1 = int(na1.pitch)
                pb1 = int(nb1.pitch)

                # Upper voice = higher pitch
                if pa1 >= pb1:
                    upper_name, upper_idx = name_a, idx_a[s1]
                    lo_u, hi_u = lo_a, hi_a
                    lower_pitch = pb1
                else:
                    upper_name, upper_idx = name_b, idx_b[s1]
                    lo_u, hi_u = lo_b, hi_b
                    lower_pitch = pa1

                upper_note = result[upper_name][upper_idx]
                up = int(upper_note.pitch)

                # Try shifting up one octave, then down one octave
                for shift in (12, -12):
                    candidate = up + shift
                    if lo_u <= candidate <= hi_u:
                        # Verify the new interval is NOT another parallel
                        new_raw = abs(candidate - lower_pitch)
                        new_mod = new_raw % 12
                        if new_mod != 7 and new_raw not in {0, 12, 24}:
                            result[upper_name][upper_idx] = _note_with_pitch(
                                upper_note, candidate
                            )
                            # Rebuild index for that track since pitch changed
                            indexes[upper_name] = _build_index(result[upper_name])
                            break
                # If no valid shift found, leave note unchanged (rare)

    return result


def _note_with_pitch(note: NoteInfo, new_pitch: int) -> NoteInfo:
    """Return a copy of note with pitch replaced."""
    from melodica.types import NoteInfo as _NI
    return _NI(
        pitch=new_pitch,
        start=note.start,
        duration=note.duration,
        velocity=note.velocity,
        absolute=note.absolute,
        articulation=note.articulation,
        expression=dict(note.expression),
    )
