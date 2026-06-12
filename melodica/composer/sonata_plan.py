"""composer/sonata_plan.py — Detailed Sonata Form planner.

Models the classical sonata form with full P/T/S/C zone granularity,
including harmonic tension profiles per zone, development fragmentation
strategy, and recapitulation transposition.

Theory basis (Grove Dictionary):
  Exposition: P (tonic) → T (transition, modulating) → S (new key) → C (cadential)
  Development: fragments exposition themes, traverses many keys
  Recapitulation: P → T → S (back in tonic) → C (tonic)
  Optional: Introduction (slow), Coda

Usage
-----
    from melodica.types import Scale, Mode
    from melodica.composer.sonata_plan import SonataFormPlan

    plan = SonataFormPlan(Scale(0, Mode.MAJOR), total_bars=96)
    parts = plan.build()
    for p in parts:
        print(p)

    # Access individual zones
    print(plan.exposition_key)   # dominant
    print(plan.development_keys) # list of keys traversed
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.idea_tool import IdeaPart
from melodica.composer.cof_navigator import CoFNavigator, cof_distance


# Zone labels used in IdeaPart.name
ZONE_P    = "P"     # Primary theme
ZONE_T    = "T"     # Transition
ZONE_S    = "S"     # Secondary theme
ZONE_C    = "C"     # Closing / cadential
ZONE_DEV  = "Dev"   # Development
ZONE_CODA = "Coda"  # Optional coda


def _dominant(scale: Scale) -> Scale:
    return Scale((scale.root + 7) % 12, scale.mode)


def _relative(scale: Scale) -> Scale:
    if scale.mode == Mode.MAJOR:
        return Scale((scale.root + 9) % 12, Mode.NATURAL_MINOR)
    return Scale((scale.root + 3) % 12, Mode.MAJOR)


def _mediant(scale: Scale) -> Scale:
    return Scale((scale.root + 4) % 12, scale.mode)


def _submediant(scale: Scale) -> Scale:
    return Scale((scale.root + 9) % 12, scale.mode)


def _leading_tone(scale: Scale) -> Scale:
    return Scale((scale.root + 11) % 12, scale.mode)


@dataclass
class SonataFormPlan:
    """Detailed sonata form planner.

    Parameters
    ----------
    home_key : Scale
        The tonic key of the movement.
    total_bars : int
        Total bar count to distribute.
    include_introduction : bool
        Prepend a slow introduction (default False).
    include_coda : bool
        Append a coda (default True).
    development_strategy : str
        How the development traverses keys:
        'cof_chain'   — step around circle of fifths
        'enharmonic'  — use dim7 pivot reinterpretations
        'dramatic'    — alternate relative minor and dominant
    exposition_repeat : bool
        Mark exposition for repeat (informational only — sets IdeaPart style hint).
    style : str | None
        Style propagated to all parts.

    Computed attributes (after build())
    ------------------------------------
    exposition_key : Scale
        Key of the S and C zones (dominant for major, relative major for minor).
    development_keys : list[Scale]
        Keys traversed in the development section.
    """

    home_key: Scale
    total_bars: int = 96
    include_introduction: bool = False
    include_coda: bool = True
    development_strategy: Literal["cof_chain", "enharmonic", "dramatic"] = "cof_chain"
    exposition_repeat: bool = True
    style: str | None = None

    # Computed
    exposition_key: Scale = field(init=False)
    development_keys: list[Scale] = field(init=False, default_factory=list)

    def __post_init__(self):
        # S/C zone key
        if self.home_key.mode == Mode.MAJOR:
            self.exposition_key = _dominant(self.home_key)
        else:
            self.exposition_key = _relative(self.home_key)

        # Development keys: 3 keys around the CoF from home
        nav = CoFNavigator()
        steps = nav.plan_album(self.home_key, n_tracks=4, strategy=self.development_strategy)
        self.development_keys = [s.to_scale for s in steps[:3]]

    # ------------------------------------------------------------------
    # Bar allocation
    # ------------------------------------------------------------------

    def _allocate(self) -> dict[str, int]:
        """Distribute total_bars across structural sections."""
        bars = self.total_bars

        intro_bars = max(4, bars // 10) if self.include_introduction else 0
        coda_bars  = max(4, bars // 12) if self.include_coda else 0
        remaining  = bars - intro_bars - coda_bars

        # Development = 25% of remaining
        dev_bars = max(8, int(remaining * 0.25))
        # Exposition = Recapitulation = 37.5% each
        exp_bars   = max(16, int(remaining * 0.375))
        recap_bars = remaining - dev_bars - exp_bars

        # Within exposition: P=30%, T=20%, S=30%, C=20%
        def _zone(total: int) -> tuple[int, int, int, int]:
            p = max(4, int(total * 0.30))
            t = max(2, int(total * 0.20))
            s = max(4, int(total * 0.30))
            c = max(2, total - p - t - s)
            return p, t, s, c

        ep, et, es, ec = _zone(exp_bars)
        rp, rt, rs, rc = _zone(recap_bars)

        return {
            "intro":  intro_bars,
            "P":      ep, "T":  et, "S":  es, "C":  ec,
            "Dev":    dev_bars,
            "P′":     rp, "T′": rt, "S′": rs, "C′": rc,
            "coda":   coda_bars,
        }

    # ------------------------------------------------------------------
    # IdeaPart builders
    # ------------------------------------------------------------------

    def _part(
        self,
        name: str,
        bars: int,
        scale: Scale,
        role: SectionRole,
        function: SectionFunction,
        modulation: str | None = None,
        style_hint: str | None = None,
    ) -> IdeaPart:
        st = style_hint or self.style
        return IdeaPart(
            name=name,
            bars=bars,
            scale=scale,
            section_type=role,
            section_function=function,
            modulation_strategy=modulation,
            style=st,
        )

    # ------------------------------------------------------------------
    # build()
    # ------------------------------------------------------------------

    def build(self) -> list[IdeaPart]:
        """Build the full IdeaPart sequence.

        Returns
        -------
        list[IdeaPart]
            Ordered structural sections. Names follow standard notation:
            P, T, S, C (exposition), Dev, P′, T′, S′, C′ (recapitulation),
            optionally prefixed by Intro and followed by Coda.
        """
        alloc = self._allocate()
        hk = self.home_key
        ek = self.exposition_key
        dev_key = self.development_keys[0] if self.development_keys else _mediant(hk)

        parts: list[IdeaPart] = []

        # --- Introduction (optional) ---
        if self.include_introduction and alloc["intro"] > 0:
            parts.append(self._part(
                "Intro", alloc["intro"], hk,
                SectionRole.INTRO, SectionFunction.BUILD,
                style_hint="slow",
            ))

        # --- Exposition ---
        # P: primary theme in tonic, assertive, establishes home key
        parts.append(self._part(
            ZONE_P, alloc["P"], hk,
            SectionRole.VERSE, SectionFunction.BUILD,
        ))
        # T: transition, modulates from tonic to exposition key
        parts.append(self._part(
            ZONE_T, alloc["T"], hk,
            SectionRole.INTERLUDE, SectionFunction.BUILD,
            modulation="pivot",
        ))
        # S: secondary theme in new key — lyrical contrast to P
        parts.append(self._part(
            ZONE_S, alloc["S"], ek,
            SectionRole.VERSE, SectionFunction.SUSTAIN,
            modulation="pivot",
        ))
        # C: closing zone, cadential, reinforces new key
        parts.append(self._part(
            ZONE_C, alloc["C"], ek,
            SectionRole.PRE_CHORUS, SectionFunction.BUILD,
        ))

        # --- Development ---
        # Unstable, fragments themes, traverses multiple keys
        parts.append(self._part(
            ZONE_DEV, alloc["Dev"], dev_key,
            SectionRole.BRIDGE, SectionFunction.BUILD,
            modulation="chromatic",
            style_hint="unstable",
        ))

        # --- Recapitulation ---
        # P′: primary theme back in tonic
        parts.append(self._part(
            "P′", alloc["P′"], hk,
            SectionRole.CHORUS, SectionFunction.RELEASE,
            modulation="dominant",
        ))
        # T′: transition stays in tonic (no modulation)
        parts.append(self._part(
            "T′", alloc["T′"], hk,
            SectionRole.INTERLUDE, SectionFunction.SUSTAIN,
        ))
        # S′: secondary theme now in tonic (key resolved back)
        parts.append(self._part(
            "S′", alloc["S′"], hk,
            SectionRole.VERSE, SectionFunction.RELEASE,
            modulation="dominant" if hk.root != ek.root else None,
        ))
        # C′: closing in tonic — final cadence
        parts.append(self._part(
            "C′", alloc["C′"], hk,
            SectionRole.CODA, SectionFunction.FADE,
        ))

        # --- Coda (optional) ---
        if self.include_coda and alloc["coda"] > 0:
            parts.append(self._part(
                ZONE_CODA, alloc["coda"], hk,
                SectionRole.OUTRO, SectionFunction.FADE,
            ))

        return parts

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def summary(self) -> str:
        """Return a compact summary string."""
        alloc = self._allocate()
        hk_name = f"{self.home_key.root}/{self.home_key.mode.name}"
        ek_name = f"{self.exposition_key.root}/{self.exposition_key.mode.name}"
        dev_names = [f"{k.root}" for k in self.development_keys]
        recap_alloc = alloc["P′"] + alloc["T′"] + alloc["S′"] + alloc["C′"]
        lines = [
            f"SonataFormPlan: {hk_name} → {ek_name} (exposition key)",
            f"  Total bars: {self.total_bars}",
            f"  Intro: {alloc['intro']}b | Exposition: {alloc['P']+alloc['T']+alloc['S']+alloc['C']}b "
            f"| Dev: {alloc['Dev']}b | Recap: {recap_alloc}b "
            f"| Coda: {alloc['coda']}b",
            f"  Dev keys: {dev_names}",
            f"  Strategy: {self.development_strategy}",
        ]
        return "\n".join(lines)

    def __repr__(self) -> str:
        return (f"SonataFormPlan(home={self.home_key.root}/{self.home_key.mode.name}, "
                f"bars={self.total_bars})")
