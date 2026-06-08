"""Jazz turnaround generator.

Turnarounds are the final 2-4 bars of a chorus that lead back to the
tonic (or into the next section). They are the harmonic glue of jazz.

Common patterns:
  - I-VI-II-V (standard)
  - I-bIII-VI-II-V (Coltrane / descending major)
  - III-VI-II-V (start on relative)
  - Tritone substitution: I-bII7-I-II-V
  - Bird changes (chromatic ii-V pairs)
  - Backdoor: IV-bVII7-I
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Literal

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Quality, Scale
from melodica.utils import nearest_pitch

# ---------------------------------------------------------------------------
# Turnaround templates — each is 2 or 4 bars (2 chords per bar)
# ---------------------------------------------------------------------------

_TurnaroundId = Literal[
    "standard",
    "coltrane",
    "tritone_sub",
    "bird",
    "backdoor",
    "parker",
    "descending",
    "chromatic_ii_v",
]

# Roman numeral sequences for turnarounds in major keys
_MAJOR_TURNAROUNDS: dict[_TurnaroundId, list[str]] = {
    "standard":       ["Imaj7", "VIm7", "IIm7", "V7"],
    "coltrane":       ["IIIm7", "VI7", "IIm7", "V7"],
    "tritone_sub":    ["Imaj7", "bII7", "IIm7", "V7"],
    "bird":           ["Imaj7", "#Idim7", "IIm7", "V7"],
    "backdoor":       ["IVmaj7", "bVII7", "Imaj7", "Imaj7"],
    "parker":         ["Imaj7", "VI7", "bIIIm7", "bVI7"],
    "descending":     ["bIIImaj7", "bVImaj7", "IIm7", "V7"],
    "chromatic_ii_v": ["bVIIm7", "bIII7", "IIm7", "V7"],
}

_MINOR_TURNAROUNDS: dict[_TurnaroundId, list[str]] = {
    "standard":       ["Im7", "bVImaj7", "IIm7b5", "V7alt"],
    "coltrane":       ["bIIImaj7", "bVI7", "IIm7b5", "V7alt"],
    "tritone_sub":    ["Im7", "bII7", "IIm7b5", "V7alt"],
    "bird":           ["Im7", "bIIdim7", "IIm7b5", "V7alt"],
    "backdoor":       ["IVm7", "bVII7", "Im7", "Im7"],
    "parker":         ["Im7", "VI7", "bIIIm7", "bVI7"],
    "descending":     ["bVImaj7", "bIImaj7", "IIm7b5", "V7alt"],
    "chromatic_ii_v": ["bVIIm7", "bIII7", "IIm7b5", "V7alt"],
}


@dataclass
class TurnaroundGenerator(PhraseGenerator):
    """Generate turnaround chord progressions for the end of a chorus.

    Parameters
    ----------
    turnaround_type : str
        One of: "standard", "coltrane", "tritone_sub", "bird",
        "backdoor", "parker", "descending", "chromatic_ii_v".
        Use "auto" to let the generator pick based on context.
    bars : int
        2 or 4 bars (default 2). Each bar gets 2 chords.
    beats_per_bar : int
        Meter (default 4).
    render_mode : str
        "chords" — output chord tones as notes.
        "arpeggio" — arpeggiate each chord.
        "guide_tones" — just 3rd and 7th of each chord.
    velocity_profile : str
        "crescendo" (build tension toward tonic), "flat", "decrescendo".
    connect_to_root : bool
        End on the tonic (I) chord as the last chord.
    """

    name: str = field(default="turnaround", init=False)
    turnaround_type: str = "standard"
    bars: int = 2
    beats_per_bar: int = 4
    render_mode: str = "chords"
    velocity_profile: str = "crescendo"
    connect_to_root: bool = True
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid = set(_MAJOR_TURNAROUNDS.keys()) | {"auto"}
        if self.turnaround_type not in valid:
            raise ValueError(f"turnaround_type must be one of {sorted(valid)}, got {self.turnaround_type!r}")
        if self.bars not in (2, 4):
            raise ValueError(f"bars must be 2 or 4, got {self.bars}")
        if self.render_mode not in ("chords", "arpeggio", "guide_tones"):
            raise ValueError(f"render_mode must be chords/arpeggio/guide_tones, got {self.render_mode!r}")

    def build_chords(self, key: Scale) -> list[ChordLabel]:
        """Build the turnaround chord progression."""
        is_minor = key.mode.value in ("minor", "dorian", "harmonic_minor", "melodic_minor")
        pool = _MINOR_TURNAROUNDS if is_minor else _MAJOR_TURNAROUNDS

        ta_type: _TurnaroundId = "standard"  # fallback
        if self.turnaround_type == "auto":
            ta_type = random.choice(list(pool.keys()))
        elif self.turnaround_type in pool:
            ta_type = self.turnaround_type  # type: ignore[assignment]

        romans = pool[ta_type]
        chords = []
        for r in romans:
            try:
                chords.append(key.parse_roman(r))
            except ValueError:
                chords.append(key.diatonic_chord(1, seventh=True))

        # For 4-bar turnarounds, extend the progression
        if self.bars == 4 and len(chords) == 4:
            # Repeat with variation
            chords = chords + list(chords)
            # Vary second half
            if len(chords) > 6:
                try:
                    chords[5] = key.parse_roman("VIm7" if not is_minor else "bVImaj7")
                except ValueError:
                    pass

        # Optionally ensure we end on tonic
        if self.connect_to_root and chords:
            last = chords[-1]
            if last.root != key.root:
                tonic = key.diatonic_chord(1, seventh=True)
                chords[-1] = tonic

        return chords

    def _velocity_at(self, idx: int, total: int) -> int:
        base = self.base_velocity()
        if self.velocity_profile == "flat" or total <= 1:
            return base
        if self.velocity_profile == "crescendo":
            progress = idx / max(1, total - 1)
            return min(127, int(base + progress * 20))
        # decrescendo
        progress = idx / max(1, total - 1)
        return max(1, int(base + (1 - progress) * 20))

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        ta_chords = self.build_chords(key)
        if not ta_chords:
            return []

        bpb = self.beats_per_bar
        total_bars = self.bars
        beats_per_chord = (bpb * total_bars) / len(ta_chords)

        notes: list[NoteInfo] = []
        mid = (self.params.key_range_low + self.params.key_range_high) // 2

        for i, chord in enumerate(ta_chords):
            start_beat = i * beats_per_chord
            vel = self._velocity_at(i, len(ta_chords))
            pcs = chord.pitch_classes()

            if self.render_mode == "guide_tones":
                # 3rd and 7th only — the essential guide tones
                root_pc = chord.root
                template_root_3rd = (root_pc + 4) % 12 if chord.quality in (
                    Quality.MAJOR, Quality.MAJOR7, Quality.DOMINANT7,
                ) else (root_pc + 3) % 12
                template_root_7th = (root_pc + 11) % 12 if chord.quality in (
                    Quality.MAJOR7,
                ) else (root_pc + 10) % 12

                for pc in (template_root_3rd, template_root_7th):
                    p = nearest_pitch(pc, mid)
                    if self.params.key_range_low <= p <= self.params.key_range_high:
                        notes.append(NoteInfo(
                            pitch=p,
                            start=round(start_beat, 4),
                            duration=round(beats_per_chord * 0.85, 4),
                            velocity=vel,
                        ))

            elif self.render_mode == "arpeggio":
                # Spread chord tones across the beat
                for j, pc in enumerate(pcs[:4]):
                    p = nearest_pitch(pc, mid + j * 4)
                    if self.params.key_range_low <= p <= self.params.key_range_high:
                        notes.append(NoteInfo(
                            pitch=p,
                            start=round(start_beat + j * (beats_per_chord / len(pcs[:4])), 4),
                            duration=round(beats_per_chord * 0.4, 4),
                            velocity=max(1, vel - j * 5),
                        ))

            else:  # "chords" — block chords
                for pc in pcs[:4]:
                    p = nearest_pitch(pc, mid)
                    if self.params.key_range_low <= p <= self.params.key_range_high:
                        notes.append(NoteInfo(
                            pitch=p,
                            start=round(start_beat, 4),
                            duration=round(beats_per_chord * 0.8, 4),
                            velocity=vel,
                        ))

        return notes
