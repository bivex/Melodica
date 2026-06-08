"""AABA / ABAC jazz form generator.

Generates 32-bar song forms used by ~90% of jazz standards
(Autumn Leaves, All The Things You Are, Rhythm Changes, etc.).

Provides:
  - Structural chord progression templates (AABA, ABAC, AB)
  - Per-section harmonic functions (tonic, subdominant, dominant, turnaround)
  - Integration with other generators via section markers

Does NOT generate audio — outputs a structural plan (chord labels + bar ranges)
that other generators consume.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types_pkg._notes import NoteInfo
from melodica.types_pkg._theory import ChordLabel, Scale

# ---------------------------------------------------------------------------
# Common jazz turnarounds and cadences (as Roman numeral patterns)
# ---------------------------------------------------------------------------

_TURNAROUNDS_MAJOR = [
    ["Imaj7", "VIm7", "IIm7", "V7"],  # I-vi-ii-V
    ["Imaj7", "III7", "VIm7", "IIm7"],  # I-III-vi-ii (Coltrane)
    ["Imaj7", "IVmaj7", "IIIm7", "VIm7"],  # Descending
    ["Imaj7", "#Idim7", "IIm7", "V7"],  # Chromatic approach
    ["IIIm7", "VIm7", "IIm7", "V7"],  # iii-VI-ii-V (start on relative)
]

_TURNAROUNDS_MINOR = [
    ["Im6", "IVm7", "bVIImaj7", "V7alt"],
    ["Im6", "bIIImaj7", "bVIm7", "IIm7b5"],
    ["Im7", "IVm7", "bVIIdom7", "IIIm7b5"],
]

# ---------------------------------------------------------------------------
# A-section harmonic templates (8 bars each)
# ---------------------------------------------------------------------------

# Each template is 8 bars of Roman numerals relative to the key
_A_TEMPLATES = {
    "rhythm_changes": [
        "Imaj7", "VIm7", "IIm7", "V7",
        "Imaj7", "VIm7", "IIm7", "V7",
    ],
    "autumn_leaves_a": [
        "IIm7", "V7", "Imaj7", "IVmaj7",
        "VII0", "III7", "VIm7", "VIm7",
    ],
    "standard_tonic": [
        "Imaj7", "Imaj7", "IVmaj7", "IVmaj7",
        "IIIm7", "VIm7", "IIm7", "V7",
    ],
    "all_the_things": [
        "VIm7", "II7", "VImaj7", "Imaj7",
        "IVmaj7", "IVmaj7", "IIm7", "V7",
    ],
    "solar": [
        "Im7", "IV7", "bIIImaj7", "bVImaj7",
        "IIm7", "V7", "Imaj7", "Imaj7",
    ],
}

# B-section (bridge) templates
_B_TEMPLATES = {
    "rhythm_bridge": [
        "III7", "III7", "VI7", "VI7",
        "II7", "II7", "V7", "V7",
    ],
    "standard_bridge": [
        "IVmaj7", "IVmaj7", "IIIm7", "VIm7",
        "IIm7", "V7", "IIIm7", "VIm7",
    ],
    "autumn_leaves_b": [
        "IIm7", "V7", "Imaj7", "IVmaj7",
        "VII0", "III7", "VIm7", "V7",
    ],
    "tritone_bridge": [
        "bVIImaj7", "bVIImaj7", "bIIImaj7", "bIIImaj7",
        "bVIm7", "II7", "IIm7", "V7",
    ],
}

# C-section for ABAC forms
_C_TEMPLATES = {
    "contrasting": [
        "IVmaj7", "IVmaj7", "IIIm7", "VIm7",
        "IIm7", "V7", "Imaj7", "Imaj7",
    ],
    "modal_contrast": [
        "bVImaj7", "bVImaj7", "bIIImaj7", "bIIImaj7",
        "IIm7", "V7", "IIm7", "V7",
    ],
}


@dataclass
class SectionPlan:
    """A section of a jazz form with chord labels and metadata."""

    name: str  # "A", "B", "C"
    bars: int
    chords: list[ChordLabel]
    start_bar: int = 0


@dataclass
class AABA_FormGenerator(PhraseGenerator):
    """Generate 32-bar (or 16-bar) jazz form structures.

    This generator produces a *structural plan* (list of SectionPlan objects)
    and can also render a skeleton of chord tones marking each section boundary.

    Parameters
    ----------
    form_type : str
        "AABA" (default, 32 bars), "ABAC" (32 bars), "AB" (16 bars),
        or "blues" (12 bars).
    a_template : str
        Template name for A sections (see _A_TEMPLATES keys).
    b_template : str
        Template name for B section / bridge.
    c_template : str
        Template name for C section (ABAC only).
    turnaround_type : str
        "standard", "coltrane", "chromatic", or "random".
    bars_per_section : int
        Section length in bars (default 8).
    vary_a2 : bool
        Slightly alter the 2nd A section (rare in standards but common in practice).
    """

    name: str = field(default="aaba_form", init=False)
    form_type: str = "AABA"
    a_template: str = "standard_tonic"
    b_template: str = "standard_bridge"
    c_template: str = "contrasting"
    turnaround_type: str = "standard"
    bars_per_section: int = 8
    vary_a2: bool = False
    params: GeneratorParams = field(default_factory=GeneratorParams)

    def __post_init__(self) -> None:
        valid = ("AABA", "ABAC", "AB", "blues")
        if self.form_type not in valid:
            raise ValueError(f"form_type must be one of {valid}, got {self.form_type!r}")

    def _pick_turnaround(self, key: Scale) -> list[str]:
        is_minor = key.mode.value in ("minor", "dorian", "harmonic_minor", "melodic_minor")
        pool = _TURNAROUNDS_MINOR if is_minor else _TURNAROUNDS_MAJOR
        if self.turnaround_type == "random":
            return random.choice(pool)
        idx = hash(self.turnaround_type) % len(pool)
        return pool[idx]

    def _roman_to_chords(self, romans: list[str], key: Scale) -> list[ChordLabel]:
        chords: list[ChordLabel] = []
        for r in romans:
            try:
                chords.append(key.parse_roman(r))
            except ValueError:
                # Fallback: treat as Imaj7
                chords.append(key.diatonic_chord(1, seventh=True))
        return chords

    def build_sections(self, key: Scale) -> list[SectionPlan]:
        """Build the full form as a list of SectionPlan objects."""
        a_chords = self._roman_to_chords(_A_TEMPLATES[self.a_template], key)
        b_chords = self._roman_to_chords(_B_TEMPLATES[self.b_template], key)

        sections: list[SectionPlan] = []
        bar = 0

        if self.form_type == "AABA":
            # A1
            sections.append(SectionPlan(name="A1", bars=self.bars_per_section, chords=a_chords, start_bar=bar))
            bar += self.bars_per_section
            # A2 (optional variation)
            a2_chords = self._maybe_vary_a(a_chords, key) if self.vary_a2 else list(a_chords)
            sections.append(SectionPlan(name="A2", bars=self.bars_per_section, chords=a2_chords, start_bar=bar))
            bar += self.bars_per_section
            # B (bridge)
            sections.append(SectionPlan(name="B", bars=self.bars_per_section, chords=b_chords, start_bar=bar))
            bar += self.bars_per_section
            # A3 with turnaround ending
            a3_chords = self._add_turnaround(list(a_chords), key)
            sections.append(SectionPlan(name="A3", bars=self.bars_per_section, chords=a3_chords, start_bar=bar))

        elif self.form_type == "ABAC":
            sections.append(SectionPlan(name="A1", bars=self.bars_per_section, chords=a_chords, start_bar=bar))
            bar += self.bars_per_section
            sections.append(SectionPlan(name="B", bars=self.bars_per_section, chords=b_chords, start_bar=bar))
            bar += self.bars_per_section
            c_chords = self._roman_to_chords(_C_TEMPLATES[self.c_template], key)
            sections.append(SectionPlan(name="A2", bars=self.bars_per_section, chords=list(a_chords), start_bar=bar))
            bar += self.bars_per_section
            sections.append(SectionPlan(name="C", bars=self.bars_per_section, chords=c_chords, start_bar=bar))

        elif self.form_type == "AB":
            sections.append(SectionPlan(name="A", bars=self.bars_per_section, chords=a_chords, start_bar=bar))
            bar += self.bars_per_section
            sections.append(SectionPlan(name="B", bars=self.bars_per_section, chords=b_chords, start_bar=bar))

        elif self.form_type == "blues":
            blues_chords = self._build_12bar_blues(key)
            sections.append(SectionPlan(name="Blues", bars=12, chords=blues_chords, start_bar=0))

        return sections

    def _maybe_vary_a(self, a_chords: list[ChordLabel], key: Scale) -> list[ChordLabel]:
        """Subtly vary the second A section — reharmonize 1-2 bars."""
        varied = list(a_chords)
        bar_to_change = random.randint(0, len(varied) - 1)
        # Substitute with a diatonic neighbor
        try:
            varied[bar_to_change] = key.diatonic_chord(random.choice([2, 3, 4, 6]), seventh=True)
        except (ValueError, IndexError):
            pass
        return varied

    def _add_turnaround(self, chords: list[ChordLabel], key: Scale) -> list[ChordLabel]:
        """Replace last 2-4 bars with a turnaround."""
        result = list(chords)
        if len(result) >= 4:
            ta_romans = self._pick_turnaround(key)
            ta_chords = self._roman_to_chords(ta_romans, key)
            result[-len(ta_chords):] = ta_chords[:len(result) - (len(result) - len(ta_chords))]
        return result

    def _build_12bar_blues(self, key: Scale) -> list[ChordLabel]:
        """Standard 12-bar blues with optional quick change."""
        root = key.root
        # I - IV - V as Roman numerals
        i7 = key.parse_roman("I7") if key.mode.value in ("major", "ionian", "mixolydian") else key.parse_roman("Im7")
        iv7 = key.parse_roman("IV7") if key.mode.value in ("major", "ionian", "mixolydian") else key.parse_roman("IVm7")
        v7 = key.parse_roman("V7") if key.mode.value in ("major", "ionian", "mixolydian") else key.parse_roman("Vm7")

        # Basic 12-bar: I(4) IV(2) I(2) V(2) I(2)
        bars = [i7] * 4 + [iv7] * 2 + [i7] * 2 + [v7] * 2 + [i7] * 2

        # Quick change: bar 2 becomes IV
        if random.random() < 0.5:
            bars[1] = iv7

        return bars

    def expand_chords_for_duration(
        self,
        sections: list[SectionPlan],
        beats_per_bar: int = 4,
    ) -> list[ChordLabel]:
        """Expand section chords to a flat list, one chord per bar."""
        expanded: list[ChordLabel] = []
        for section in sections:
            chords = section.chords
            bars = section.bars
            # Repeat or truncate chords to fill bars
            if len(chords) < bars:
                # Repeat last chord to fill
                while len(chords) < bars:
                    chords.append(chords[-1])
            elif len(chords) > bars:
                chords = chords[:bars]
            expanded.extend(chords)
        return expanded

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        """Render section-boundary markers as quiet root notes.

        This is a structural generator — it outputs quiet reference notes
        marking section starts. Other generators should use `build_sections()`
        directly and call `expand_chords_for_duration()`.
        """
        sections = self.build_sections(key)
        beats_per_bar = 4
        notes: list[NoteInfo] = []

        for section in sections:
            start_beat = section.start_bar * beats_per_bar
            if start_beat >= duration_beats:
                break

            root_pc = section.chords[0].root if section.chords else key.root
            pitch = root_pc + 60  # Middle C area

            notes.append(NoteInfo(
                pitch=min(pitch, 127),
                start=float(start_beat),
                duration=0.5,
                velocity=35,  # Quiet marker
                articulation="staccato",
            ))

        return notes
