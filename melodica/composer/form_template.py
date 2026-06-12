"""composer/form_template.py — Classical musical form templates.

Generates IdeaPart sequences for standard musical forms:
  BINARY         — AB or AABB
  TERNARY        — ABA (da capo)
  RONDO          — ABACABA / ABACA
  SONATA         — Exposition(P·T·S·C) → Development → Recapitulation
  THROUGH_COMPOSED — ABCD (no repeats)
  VARIATIONS     — Theme + N variations
  ARCH           — ABCBA (symmetrical)
  STROPHIC       — AAAA (same material repeated)

Usage
-----
    from melodica.types import Scale, Mode
    from melodica.composer.form_template import FormTemplate, form_plan

    scale = Scale(0, Mode.MAJOR)
    parts = form_plan(FormTemplate.SONATA, scale, total_bars=64)
    for p in parts:
        print(p.name, p.scale, p.section_type)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from melodica.types import Scale, Mode, SectionRole, SectionFunction
from melodica.idea_tool import IdeaPart


class FormTemplate(Enum):
    """Standard musical form templates."""
    BINARY           = "binary"
    TERNARY          = "ternary"
    RONDO            = "rondo"
    RONDO_5          = "rondo_5"        # ABACA
    SONATA           = "sonata"
    THROUGH_COMPOSED = "through_composed"
    VARIATIONS       = "variations"
    ARCH             = "arch"           # ABCBA
    STROPHIC         = "strophic"


def _dominant_scale(scale: Scale) -> Scale:
    """Return the dominant key (root + 7 semitones, same mode)."""
    return Scale((scale.root + 7) % 12, scale.mode)


def _relative_scale(scale: Scale) -> Scale:
    """Return relative minor (if major) or relative major (if minor)."""
    if scale.mode == Mode.MAJOR:
        return Scale((scale.root + 9) % 12, Mode.NATURAL_MINOR)
    return Scale((scale.root + 3) % 12, Mode.MAJOR)


def _subdominant_scale(scale: Scale) -> Scale:
    return Scale((scale.root + 5) % 12, scale.mode)


def _mediant_scale(scale: Scale) -> Scale:
    """Mediant — root + 4 semitones (major third above)."""
    return Scale((scale.root + 4) % 12, scale.mode)


def _parallel_minor(scale: Scale) -> Scale:
    if scale.mode == Mode.MAJOR:
        return Scale(scale.root, Mode.NATURAL_MINOR)
    return Scale(scale.root, Mode.MAJOR)


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def _part(
    name: str,
    bars: int,
    scale: Scale,
    role: SectionRole | None = None,
    function: SectionFunction | None = None,
    modulation: str | None = None,
    style: str | None = None,
) -> IdeaPart:
    return IdeaPart(
        name=name,
        bars=bars,
        scale=scale,
        section_type=role,
        section_function=function,
        modulation_strategy=modulation,
        style=style,
    )


# ---------------------------------------------------------------------------
# form_plan — main entry point
# ---------------------------------------------------------------------------

def form_plan(
    template: FormTemplate,
    scale: Scale,
    total_bars: int = 64,
    *,
    n_variations: int = 4,
    rondo_episodes: int = 2,
    development_ratio: float = 0.25,
    style: str | None = None,
) -> list[IdeaPart]:
    """Generate an IdeaPart sequence for a given musical form.

    Parameters
    ----------
    template : FormTemplate
        The form to generate.
    scale : Scale
        Home key of the composition.
    total_bars : int
        Total bar count to distribute across sections.
    n_variations : int
        Number of variations (VARIATIONS template only).
    rondo_episodes : int
        Number of episodes in rondo (2 = ABACA, 3 = ABACABA).
    development_ratio : float
        Fraction of total_bars for sonata development section.
    style : str | None
        Style hint propagated to all parts.

    Returns
    -------
    list[IdeaPart]
        Ordered structural sections ready for album_pipeline.
    """
    if template == FormTemplate.BINARY:
        return _binary(scale, total_bars, style)
    elif template == FormTemplate.TERNARY:
        return _ternary(scale, total_bars, style)
    elif template == FormTemplate.RONDO:
        return _rondo(scale, total_bars, episodes=rondo_episodes, style=style)
    elif template == FormTemplate.RONDO_5:
        return _rondo(scale, total_bars, episodes=2, style=style)
    elif template == FormTemplate.SONATA:
        return _sonata(scale, total_bars, development_ratio=development_ratio, style=style)
    elif template == FormTemplate.THROUGH_COMPOSED:
        return _through_composed(scale, total_bars, style=style)
    elif template == FormTemplate.VARIATIONS:
        return _variations(scale, total_bars, n=n_variations, style=style)
    elif template == FormTemplate.ARCH:
        return _arch(scale, total_bars, style=style)
    elif template == FormTemplate.STROPHIC:
        return _strophic(scale, total_bars, style=style)
    else:
        raise ValueError(f"Unknown form template: {template}")


# ---------------------------------------------------------------------------
# Individual form builders
# ---------------------------------------------------------------------------

def _binary(scale: Scale, bars: int, style: str | None) -> list[IdeaPart]:
    """AB or AABB — two contrasting sections."""
    a = bars // 2
    b = bars - a
    dom = _dominant_scale(scale)
    return [
        _part("A", a, scale, SectionRole.VERSE, SectionFunction.BUILD, style=style),
        _part("B", b, dom, SectionRole.CHORUS, SectionFunction.RELEASE,
              modulation="pivot", style=style),
    ]


def _ternary(scale: Scale, bars: int, style: str | None) -> list[IdeaPart]:
    """ABA — statement, contrast, return."""
    a = bars // 3
    b = bars // 3
    a2 = bars - a - b
    contrast = _relative_scale(scale) if scale.mode == Mode.MAJOR else _dominant_scale(scale)
    return [
        _part("A",  a,  scale,    SectionRole.VERSE,  SectionFunction.BUILD, style=style),
        _part("B",  b,  contrast, SectionRole.BRIDGE, SectionFunction.SUSTAIN,
              modulation="pivot", style=style),
        _part("A′", a2, scale,    SectionRole.CHORUS,  SectionFunction.RELEASE,
              modulation="dominant", style=style),
    ]


def _rondo(scale: Scale, bars: int, episodes: int, style: str | None) -> list[IdeaPart]:
    """ABACA(BA) — refrain alternates with episodes."""
    # n_refrains = episodes + 1, n_sections = 2*episodes + 1
    n_sections = 2 * episodes + 1
    refrain_bars = max(4, bars // (n_sections + episodes // 2))
    episode_bars = max(4, (bars - refrain_bars * (episodes + 1)) // episodes)

    episode_keys = [
        _dominant_scale(scale),
        _relative_scale(scale),
        _subdominant_scale(scale),
    ]

    parts: list[IdeaPart] = []
    ep_idx = 0
    for i in range(n_sections):
        if i % 2 == 0:
            # Refrain (A)
            suffix = "" if i == 0 else f"′" * (i // 2)
            parts.append(_part(
                f"A{suffix}", refrain_bars, scale,
                SectionRole.REFRAIN, SectionFunction.SUSTAIN,
                modulation=("dominant" if i > 0 else None),
                style=style,
            ))
        else:
            # Episode (B, C, ...)
            ep_scale = episode_keys[ep_idx % len(episode_keys)]
            label = chr(ord("B") + ep_idx)
            parts.append(_part(
                label, episode_bars, ep_scale,
                SectionRole.BRIDGE, SectionFunction.BUILD,
                modulation="pivot", style=style,
            ))
            ep_idx += 1

    return parts


def _sonata(
    scale: Scale,
    bars: int,
    development_ratio: float,
    style: str | None,
) -> list[IdeaPart]:
    """Exposition(P·T·S·C) → Development → Recapitulation(P·T·S·C)."""
    dev_bars = max(8, int(bars * development_ratio))
    exp_bars = (bars - dev_bars) * 2 // 3
    recap_bars = bars - dev_bars - exp_bars

    # Key relationships
    if scale.mode == Mode.MAJOR:
        s_key = _dominant_scale(scale)   # S-zone in dominant
    else:
        s_key = _relative_scale(scale)   # S-zone in relative major

    # Distribute exposition bars
    p_bars = max(4, exp_bars * 3 // 10)
    t_bars = max(2, exp_bars * 2 // 10)
    s_bars = max(4, exp_bars * 3 // 10)
    c_bars = max(2, exp_bars - p_bars - t_bars - s_bars)

    # Distribute recapitulation bars (everything in tonic)
    rp_bars = max(4, recap_bars * 3 // 10)
    rt_bars = max(2, recap_bars * 2 // 10)
    rs_bars = max(4, recap_bars * 3 // 10)
    rc_bars = max(2, recap_bars - rp_bars - rt_bars - rs_bars)

    return [
        # Exposition
        _part("P",  p_bars, scale,  SectionRole.INTRO,      SectionFunction.BUILD,
              style=style),
        _part("T",  t_bars, scale,  SectionRole.INTERLUDE,  SectionFunction.BUILD,
              modulation="pivot", style=style),
        _part("S",  s_bars, s_key,  SectionRole.VERSE,      SectionFunction.SUSTAIN,
              modulation="pivot", style=style),
        _part("C",  c_bars, s_key,  SectionRole.PRE_CHORUS, SectionFunction.BUILD,
              style=style),
        # Development
        _part("Dev", dev_bars, _mediant_scale(scale), SectionRole.BRIDGE,
              SectionFunction.BUILD, modulation="chromatic", style=style),
        # Recapitulation
        _part("P′",  rp_bars, scale, SectionRole.VERSE,     SectionFunction.RELEASE,
              modulation="dominant", style=style),
        _part("T′",  rt_bars, scale, SectionRole.INTERLUDE, SectionFunction.SUSTAIN,
              style=style),
        _part("S′",  rs_bars, scale, SectionRole.CHORUS,    SectionFunction.RELEASE,
              style=style),
        _part("C′",  rc_bars, scale, SectionRole.CODA,      SectionFunction.FADE,
              style=style),
    ]


def _through_composed(scale: Scale, bars: int, style: str | None) -> list[IdeaPart]:
    """ABCD — no repeats, continuous new material."""
    n = max(3, min(6, bars // 8))
    chunk = bars // n
    remainder = bars - chunk * n

    keys = [scale]
    for i in range(1, n):
        # Alternate: dominant, relative, subdominant, mediant, parallel minor
        transforms = [_dominant_scale, _relative_scale, _subdominant_scale,
                      _mediant_scale, _parallel_minor]
        keys.append(transforms[(i - 1) % len(transforms)](scale))

    roles = [SectionRole.INTRO, SectionRole.VERSE, SectionRole.BRIDGE,
             SectionRole.CHORUS, SectionRole.CLIMAX, SectionRole.CODA]
    functions = [SectionFunction.BUILD, SectionFunction.SUSTAIN, SectionFunction.BUILD,
                 SectionFunction.RELEASE, SectionFunction.SUSTAIN, SectionFunction.FADE]

    parts = []
    for i in range(n):
        b = chunk + (remainder if i == n - 1 else 0)
        label = chr(ord("A") + i)
        parts.append(_part(
            label, b, keys[i],
            roles[i % len(roles)],
            functions[i % len(functions)],
            modulation=("pivot" if i > 0 else None),
            style=style,
        ))
    return parts


def _variations(scale: Scale, bars: int, n: int, style: str | None) -> list[IdeaPart]:
    """Theme + N variations."""
    chunk = max(4, bars // (n + 1))
    theme_bars = chunk
    var_bars = (bars - theme_bars) // n

    # Variation key/mode sequence: tonic, dominant, parallel minor, subdominant, ...
    var_keys = [
        scale,
        _dominant_scale(scale),
        _parallel_minor(scale),
        _subdominant_scale(scale),
        _relative_scale(scale),
    ]
    var_functions = [
        SectionFunction.BUILD,
        SectionFunction.SUSTAIN,
        SectionFunction.BUILD,
        SectionFunction.RELEASE,
        SectionFunction.FADE,
    ]

    parts = [_part("Theme", theme_bars, scale, SectionRole.VERSE,
                   SectionFunction.SUSTAIN, style=style)]
    for i in range(n):
        k = var_keys[i % len(var_keys)]
        fn = var_functions[i % len(var_functions)]
        mod = "pivot" if k.root != scale.root else None
        parts.append(_part(
            f"Var {i + 1}", var_bars, k,
            SectionRole.VERSE, fn,
            modulation=mod, style=style,
        ))
    return parts


def _arch(scale: Scale, bars: int, style: str | None) -> list[IdeaPart]:
    """ABCBA — symmetrical arch form."""
    chunk = bars // 5
    rem = bars - chunk * 5
    contrast1 = _dominant_scale(scale)
    contrast2 = _relative_scale(scale)
    peak = _mediant_scale(scale)
    return [
        _part("A",  chunk,       scale,      SectionRole.INTRO,   SectionFunction.BUILD,
              style=style),
        _part("B",  chunk,       contrast1,  SectionRole.VERSE,   SectionFunction.BUILD,
              modulation="pivot", style=style),
        _part("C",  chunk + rem, peak,       SectionRole.CLIMAX,  SectionFunction.SUSTAIN,
              modulation="chromatic", style=style),
        _part("B′", chunk,       contrast1,  SectionRole.BRIDGE,  SectionFunction.RELEASE,
              modulation="dominant", style=style),
        _part("A′", chunk,       scale,      SectionRole.OUTRO,   SectionFunction.FADE,
              modulation="pivot", style=style),
    ]


def _strophic(scale: Scale, bars: int, style: str | None) -> list[IdeaPart]:
    """AAAA — same material repeated (song verse form)."""
    n = max(2, min(6, bars // 8))
    chunk = bars // n
    parts = []
    for i in range(n):
        suffix = "′" * i
        parts.append(_part(
            f"A{suffix}", chunk, scale,
            SectionRole.VERSE, SectionFunction.SUSTAIN,
            style=style,
        ))
    return parts
