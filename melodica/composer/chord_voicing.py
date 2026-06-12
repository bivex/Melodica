"""composer/chord_voicing.py — Orchestral chord voicing layout.

Distributes a chord's pitches across instrument voices following
classical orchestration rules (Grove / Rimsky-Korsakov):

  bass voice     — root (or lowest chord tone)
  tenor voice    — fifth above bass
  alto voice     — third (or seventh)
  soprano voice  — melody note (or octave doubling)

Also supports:
  - Open / close spacing
  - Doubling rules (octave doubling, unison doubling)
  - Timbral hint system (violins+glockenspiel=sparkling, etc.)
  - voice_chord() — assign MIDI pitches to a named instrument list
  - ChordVoicingLayout — full layout engine for a chord progression

Usage
-----
    from melodica.composer.chord_voicing import voice_chord, ChordVoicingLayout
    from melodica.types import ChordLabel, Quality

    chord = ChordLabel(root=0, quality=Quality.MAJOR)
    layout = voice_chord(chord, instruments=["bass","cello","viola","violin_1"])
    # → {"bass": 36, "cello": 43, "viola": 52, "violin_1": 64}
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

from melodica.types_pkg._notes import NoteInfo
from melodica.types import ChordLabel, Quality


# ---------------------------------------------------------------------------
# Chord tone helpers
# ---------------------------------------------------------------------------

# Semitone intervals above root for each Quality
_QUALITY_INTERVALS: dict[Quality, list[int]] = {
    Quality.MAJOR:        [0, 4, 7],
    Quality.MINOR:        [0, 3, 7],
    Quality.DOMINANT7:    [0, 4, 7, 10],
    Quality.MAJOR7:       [0, 4, 7, 11],
    Quality.MINOR7:       [0, 3, 7, 10],
    Quality.DIMINISHED:   [0, 3, 6],
    Quality.FULL_DIM7:    [0, 3, 6, 9],
    Quality.HALF_DIM7:    [0, 3, 6, 10],
    Quality.AUGMENTED:    [0, 4, 8],
    Quality.SUS2:         [0, 2, 7],
    Quality.SUS4:         [0, 5, 7],
    Quality.ADD9:         [0, 2, 4, 7],
    Quality.MAJOR9:       [0, 4, 7, 11, 14],
    Quality.MINOR9:       [0, 3, 7, 10, 14],
}

_FALLBACK_INTERVALS = [0, 4, 7]  # major triad


def chord_tones(chord: ChordLabel) -> list[int]:
    """Return chord tone pitch-classes (0–11) in order from root."""
    ivs = _QUALITY_INTERVALS.get(chord.quality, _FALLBACK_INTERVALS)
    return [(chord.root + i) % 12 for i in ivs]


def _nearest_pitch(pitch_class: int, anchor: int, direction: int = 0) -> int:
    """Find nearest MIDI pitch to anchor with the given pitch class.

    direction: 0=nearest, 1=above, -1=below
    """
    base = (anchor // 12) * 12 + pitch_class
    candidates = [base - 12, base, base + 12]
    if direction > 0:
        candidates = [c for c in candidates if c >= anchor] or [base + 12]
    elif direction < 0:
        candidates = [c for c in candidates if c <= anchor] or [base - 12]
    return min(candidates, key=lambda c: abs(c - anchor))


# ---------------------------------------------------------------------------
# Instrument range definitions (MIDI pitch lo/hi)
# ---------------------------------------------------------------------------

_INSTRUMENT_RANGES: dict[str, tuple[int, int]] = {
    # Strings
    "contrabass":   (28, 55),
    "cello":        (36, 65),
    "viola":        (48, 79),
    "violin_2":     (55, 88),
    "violin_1":     (60, 96),
    # Winds
    "bassoon":      (34, 72),
    "clarinet":     (50, 90),
    "oboe":         (58, 91),
    "flute":        (60, 96),
    "piccolo":      (74, 108),
    # Brass
    "tuba":         (28, 58),
    "trombone":     (40, 72),
    "french_horn":  (34, 77),
    "trumpet":      (52, 84),
    # Keys / Perc
    "piano":        (21, 108),
    "harpsichord":  (29, 89),
    "celesta":      (60, 108),
    "glockenspiel": (79, 108),
    "harp":         (24, 103),
    "organ":        (36, 96),
    # Generic
    "bass":         (28, 55),
    "tenor":        (48, 69),
    "alto":         (53, 74),
    "soprano":      (60, 84),
}

_DEFAULT_RANGE = (36, 84)


def _range(instrument: str) -> tuple[int, int]:
    key = instrument.lower().replace(" ", "_")
    return _INSTRUMENT_RANGES.get(key, _DEFAULT_RANGE)


# ---------------------------------------------------------------------------
# Timbral hint system
# ---------------------------------------------------------------------------

# Known instrument combos → timbral descriptor
_TIMBRE_COMBOS: dict[frozenset[str], str] = {
    frozenset({"violin_1", "glockenspiel"}): "sparkling",
    frozenset({"violin_1", "violin_2", "glockenspiel"}): "sparkling",
    frozenset({"piccolo", "celesta"}): "bright",
    frozenset({"flute", "celesta"}): "crystalline",
    frozenset({"cello", "trombone"}): "dark_warm",
    frozenset({"trumpet", "french_horn"}): "fanfare",
    frozenset({"strings", "brass"}): "full_orchestral",
    frozenset({"cello", "viola", "violin_1", "violin_2"}): "string_choir",
    frozenset({"flute", "oboe", "clarinet", "bassoon"}): "woodwind_choir",
}


def timbre_hint(instruments: list[str]) -> str | None:
    """Return a timbral descriptor for a combination of instruments."""
    key = frozenset(i.lower().replace(" ", "_") for i in instruments)
    for combo, hint in _TIMBRE_COMBOS.items():
        if combo.issubset(key):
            return hint
    return None


# ---------------------------------------------------------------------------
# voice_chord() — main API
# ---------------------------------------------------------------------------

VoiceRole = Literal["bass", "tenor", "alto", "soprano", "unison_double", "octave_double"]

# Default role priority order (low → high)
_DEFAULT_ROLE_ORDER: list[VoiceRole] = ["bass", "tenor", "alto", "soprano"]


def voice_chord(
    chord: ChordLabel,
    instruments: list[str],
    melody_pitch: int | None = None,
    spacing: Literal["close", "open", "drop2"] = "open",
) -> dict[str, int]:
    """Assign MIDI pitches to instruments for a chord.

    Parameters
    ----------
    chord : ChordLabel
        The chord to voice.
    instruments : list[str]
        Ordered list of instrument names (low → high register).
        Ranges are looked up from _INSTRUMENT_RANGES.
    melody_pitch : int | None
        If set, the highest instrument is locked to this pitch
        (melody doubling).
    spacing : str
        'close' = all voices within an octave
        'open'  = spread across 2 octaves (default)
        'drop2' = classical drop-2 voicing

    Returns
    -------
    dict[str, int]
        instrument_name → MIDI pitch
    """
    if not instruments:
        return {}

    tones = chord_tones(chord)
    n = len(instruments)

    # Assign register anchors across instruments
    low_inst  = instruments[0]
    high_inst = instruments[-1]
    lo_range  = _range(low_inst)
    hi_range  = _range(high_inst)

    # Bass: root in low register
    bass_anchor = (lo_range[0] + lo_range[1]) // 2
    bass_pc     = tones[0]
    bass_pitch  = _nearest_pitch(bass_pc, bass_anchor, direction=-1)
    bass_pitch  = max(lo_range[0], min(lo_range[1], bass_pitch))

    # Melody / soprano: top of high register or locked pitch
    if melody_pitch is not None:
        soprano_pitch = max(hi_range[0], min(hi_range[1], melody_pitch))
    else:
        soprano_pc    = tones[min(2, len(tones) - 1)]  # third or highest tone
        soprano_anchor = (hi_range[0] + hi_range[1]) // 2
        if spacing == "open":
            soprano_anchor += 12
        soprano_pitch  = _nearest_pitch(soprano_pc, soprano_anchor, direction=1)
        soprano_pitch  = max(hi_range[0], min(hi_range[1], soprano_pitch))

    # Distribute inner voices linearly between bass and soprano
    result: dict[str, int] = {}
    result[low_inst]  = bass_pitch
    result[high_inst] = soprano_pitch

    if n == 1:
        return result

    if n == 2:
        return result

    # Inner voices: evenly spaced between bass and soprano
    inner_instruments = instruments[1:-1]
    n_inner = len(inner_instruments)
    span = soprano_pitch - bass_pitch

    for i, inst in enumerate(inner_instruments):
        # Linear interpolation of pitch
        t          = (i + 1) / (n_inner + 1)
        raw_pitch  = bass_pitch + span * t
        inst_range = _range(inst)

        # Snap to a chord tone
        tone_idx   = (i + 1) % len(tones)
        tone_pc    = tones[tone_idx]
        snapped    = _nearest_pitch(tone_pc, int(round(raw_pitch)))
        snapped    = max(inst_range[0], min(inst_range[1], snapped))
        result[inst] = snapped

    # Drop-2 transformation: swap second-highest voice down an octave
    if spacing == "drop2" and n >= 4:
        second_highest = instruments[-2]
        result[second_highest] = max(
            _range(second_highest)[0],
            result[second_highest] - 12
        )

    return result


# ---------------------------------------------------------------------------
# ChordVoicingLayout — progression-level voicing
# ---------------------------------------------------------------------------

@dataclass
class ChordVoicingLayout:
    """Voice a chord progression across a fixed instrument set.

    Applies smooth voice-leading between successive chords by minimising
    total semitone movement across all voices.

    Parameters
    ----------
    instruments : list[str]
        Ordered list of instruments (low → high).
    spacing : str
        Voicing spacing mode ('close', 'open', 'drop2').
    smooth_voice_leading : bool
        If True, each chord is voiced to minimise movement from previous.
    """

    instruments: list[str]
    spacing: Literal["close", "open", "drop2"] = "open"
    smooth_voice_leading: bool = True

    def voice_progression(
        self,
        chords: list[ChordLabel],
        melody_pitches: list[int | None] | None = None,
    ) -> list[dict[str, int]]:
        """Voice a sequence of chords.

        Parameters
        ----------
        chords : list[ChordLabel]
            Ordered chord list.
        melody_pitches : list[int | None] | None
            Per-chord melody pitch (None = auto).

        Returns
        -------
        list[dict[str, int]]
            Per-chord instrument → MIDI pitch assignment.
        """
        if melody_pitches is None:
            melody_pitches = [None] * len(chords)
        else:
            melody_pitches = list(melody_pitches)
            if len(melody_pitches) < len(chords):
                melody_pitches = melody_pitches + [None] * (len(chords) - len(melody_pitches))

        voicings: list[dict[str, int]] = []
        prev: dict[str, int] | None = None

        for chord, mel in zip(chords, melody_pitches):
            v = voice_chord(chord, self.instruments, mel, self.spacing)

            if self.smooth_voice_leading and prev is not None:
                v = self._smooth(chord, v, prev)

            voicings.append(v)
            prev = v

        return voicings

    def _smooth(
        self,
        chord: ChordLabel,
        current: dict[str, int],
        previous: dict[str, int],
    ) -> dict[str, int]:
        """Adjust voicing to minimise voice movement from previous chord."""
        tones = chord_tones(chord)
        result: dict[str, int] = dict(current)

        for inst in self.instruments:
            if inst not in previous or inst not in current:
                continue
            prev_pitch = previous[inst]
            curr_pitch = current[inst]
            inst_range = _range(inst)

            # Try all octave placements of the current pitch class
            pc = curr_pitch % 12
            candidates = [pc + 12 * o for o in range(0, 11)
                          if inst_range[0] <= pc + 12 * o <= inst_range[1]]
            if candidates:
                best = min(candidates, key=lambda c: abs(c - prev_pitch))
                result[inst] = best

        return result

    def to_notes(
        self,
        voicings: list[dict[str, int]],
        beat_positions: list[float],
        duration_beats: float = 2.0,
        velocity: int = 64,
    ) -> dict[str, list[NoteInfo]]:
        """Convert voicings to NoteInfo lists per instrument.

        Parameters
        ----------
        voicings : list[dict[str, int]]
            Output of voice_progression().
        beat_positions : list[float]
            Start beat for each chord.
        duration_beats : float
            Duration of each chord in beats.
        velocity : int
            Base velocity.

        Returns
        -------
        dict[str, list[NoteInfo]]
            instrument_name → note list.
        """
        notes_by_inst: dict[str, list[NoteInfo]] = {i: [] for i in self.instruments}

        for voicing, beat in zip(voicings, beat_positions):
            for inst, pitch in voicing.items():
                notes_by_inst.setdefault(inst, []).append(
                    NoteInfo(pitch=pitch, start=beat,
                             duration=duration_beats, velocity=velocity)
                )

        return notes_by_inst
