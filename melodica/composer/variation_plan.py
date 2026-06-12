"""composer/variation_plan.py — Variation form planner.

Generates a series of IdeaPart variations from a theme IdeaPart.
Each variation applies a different transformation type, following
classical and jazz variation practice.

Variation types (per Wikipedia / Grove):
  melodic      — elaborate the melody (SchenkerianElaborator)
  rhythmic     — different rhythm preset, same harmony
  harmonic     — reharmonized chord progression
  modal        — parallel minor/major key shift
  reductive    — stripped down (fewer notes, thinner texture)
  contrapuntal — add countermelody / imitative texture

Usage
-----
    from melodica.types import Scale, Mode
    from melodica.idea_tool import IdeaPart
    from melodica.composer.variation_plan import VariationPlan

    theme = IdeaPart(name="Theme", bars=8, scale=Scale(0, Mode.MAJOR))
    plan = VariationPlan(theme, n_variations=5)
    parts = plan.build()
    for p in parts:
        print(p.name, p.variation_type, p.scale)
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace as dc_replace
from typing import Literal

from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.idea_tool import IdeaPart


# Ordered cycle of variation types (classical practice order)
_VAR_CYCLE: list[str] = [
    "melodic",
    "rhythmic",
    "harmonic",
    "modal",
    "reductive",
    "contrapuntal",
]

# Rhythm preset suggestions per variation index (for rhythmic variations)
_RHYTHMIC_PRESETS: list[str] = [
    "straight_16ths",
    "dotted_8_16th",
    "straight_8_triplets",
    "funk_sixteenth",
    "waltz_jazz",
    "bossa_nova",
]

# Progression type suggestions for harmonic variations
_HARMONIC_PROGRESSIONS: list[str] = [
    "secondary_dominant",
    "chromatic_descent",
    "modal_interchange",
    "neapolitan",
    "augmented_sixth",
]


def _parallel_key(scale: Scale) -> Scale:
    if scale.mode == Mode.MAJOR:
        return Scale(scale.root, Mode.NATURAL_MINOR)
    return Scale(scale.root, Mode.MAJOR)


def _dominant(scale: Scale) -> Scale:
    return Scale((scale.root + 7) % 12, scale.mode)


def _subdominant(scale: Scale) -> Scale:
    return Scale((scale.root + 5) % 12, scale.mode)


@dataclass
class VariationPlan:
    """Generate a variation series from a theme IdeaPart.

    Parameters
    ----------
    theme : IdeaPart
        The original theme to vary. Must have a name set.
    n_variations : int
        Number of variations to generate (default 4, max 12).
    types : list[str] | None
        Explicit variation type sequence. None = use _VAR_CYCLE.
        Available: 'melodic', 'rhythmic', 'harmonic', 'modal',
                   'reductive', 'contrapuntal'.
    include_theme : bool
        Prepend the original theme to the output (default True).
    include_finale : bool
        Append a finale variation (fast, full texture) (default False).
    key_plan : list[Scale] | None
        Explicit per-variation key sequence. None = auto-derived.
        Length must equal n_variations.

    Notes
    -----
    variation_of and variation_type fields on each output IdeaPart
    are set so that downstream processors (album_pipeline, MotifDevelopmentPlan)
    can apply the appropriate transformation automatically.
    """

    theme: IdeaPart
    n_variations: int = 4
    types: list[str] | None = None
    include_theme: bool = True
    include_finale: bool = False
    key_plan: list[Scale] | None = None

    def __post_init__(self):
        self.n_variations = max(1, min(12, self.n_variations))
        if self.key_plan and len(self.key_plan) != self.n_variations:
            raise ValueError(
                f"key_plan length ({len(self.key_plan)}) must equal "
                f"n_variations ({self.n_variations})"
            )

    # ------------------------------------------------------------------
    # Key derivation
    # ------------------------------------------------------------------

    def _derive_keys(self) -> list[Scale]:
        """Auto-derive a key sequence for the variations."""
        base = self.theme.scale or Scale(0, Mode.MAJOR)
        keys = []
        transforms = [
            lambda s: s,                        # same key
            lambda s: _dominant(s),             # dominant
            lambda s: _parallel_key(s),         # parallel minor/major
            lambda s: _subdominant(s),          # subdominant
            lambda s: s,                        # back to tonic
            lambda s: _parallel_key(s),         # parallel again (deeper)
            lambda s: s,                        # tonic
            lambda s: _dominant(s),
            lambda s: s,
            lambda s: _parallel_key(s),
            lambda s: s,
            lambda s: s,
        ]
        for i in range(self.n_variations):
            keys.append(transforms[i % len(transforms)](base))
        return keys

    # ------------------------------------------------------------------
    # Section function progression
    # ------------------------------------------------------------------

    def _functions(self) -> list[SectionFunction]:
        """Return a tension arc of section functions for the variations."""
        if self.n_variations <= 1:
            return [SectionFunction.SUSTAIN]
        arc = []
        for i in range(self.n_variations):
            t = i / (self.n_variations - 1)
            if t < 0.3:
                arc.append(SectionFunction.BUILD)
            elif t < 0.7:
                arc.append(SectionFunction.SUSTAIN)
            elif t < 0.9:
                arc.append(SectionFunction.BUILD)
            else:
                arc.append(SectionFunction.RELEASE)
        return arc

    # ------------------------------------------------------------------
    # build()
    # ------------------------------------------------------------------

    def build(self) -> list[IdeaPart]:
        """Build the full variation sequence.

        Returns
        -------
        list[IdeaPart]
            Theme (optional) + N variations + finale (optional).
            Each variation has variation_of = theme.name and
            variation_type set to the transformation type.
        """
        theme_name = self.theme.name or "Theme"
        base_scale = self.theme.scale or Scale(0, Mode.MAJOR)
        base_bars  = self.theme.bars or 8

        var_types = self.types or _VAR_CYCLE
        keys      = self.key_plan or self._derive_keys()
        functions = self._functions()

        parts: list[IdeaPart] = []

        # Original theme
        if self.include_theme:
            parts.append(dc_replace(
                self.theme,
                variation_of=None,
                variation_type=None,
                section_type=self.theme.section_type or SectionRole.VERSE,
                section_function=self.theme.section_function or SectionFunction.SUSTAIN,
            ))

        # Variations
        for i in range(self.n_variations):
            vtype = var_types[i % len(var_types)]
            vkey  = keys[i]
            vfn   = functions[i]
            modulation = "pivot" if vkey.root != base_scale.root else None

            # Rhythm preset hint for rhythmic variations
            style_hint = self.theme.style
            if vtype == "rhythmic":
                style_hint = _RHYTHMIC_PRESETS[i % len(_RHYTHMIC_PRESETS)]
            elif vtype == "harmonic":
                style_hint = _HARMONIC_PROGRESSIONS[i % len(_HARMONIC_PROGRESSIONS)]

            # Bar count: reductive shrinks, finale expands
            bars = base_bars
            if vtype == "reductive":
                bars = max(4, base_bars * 3 // 4)

            ordinal = _ordinal(i + 1)
            parts.append(IdeaPart(
                name=f"Var {ordinal}",
                bars=bars,
                scale=vkey,
                section_type=SectionRole.VERSE,
                section_function=vfn,
                modulation_strategy=modulation,
                style=style_hint,
                variation_of=theme_name,
                variation_type=vtype,
            ))

        # Finale
        if self.include_finale:
            last_scale = parts[-1].scale if parts and parts[-1].scale else base_scale
            parts.append(IdeaPart(
                name="Finale",
                bars=base_bars * 2,
                scale=base_scale,
                section_type=SectionRole.CODA,
                section_function=SectionFunction.RELEASE,
                modulation_strategy="dominant" if last_scale.root != base_scale.root else None,
                style="fast",
                variation_of=theme_name,
                variation_type="melodic",
            ))

        return parts

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def summary(self) -> str:
        parts = self.build()
        lines = [f"VariationPlan: '{self.theme.name}' × {self.n_variations} variations"]
        for p in parts:
            k = f"{p.scale.root}/{p.scale.mode.name}" if p.scale else "?"
            vt = p.variation_type or "original"
            lines.append(f"  {p.name:<12} {p.bars:>3}b  key={k:<22}  type={vt}")
        return "\n".join(lines)


def _ordinal(n: int) -> str:
    """Return ordinal suffix: 1→I, 2→II, ... using Roman numerals up to 12."""
    _ROMAN = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII"]
    if 1 <= n <= len(_ROMAN):
        return _ROMAN[n - 1]
    return str(n)
