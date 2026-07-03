# Copyright (c) 2026 Bivex
# Licensed under the MIT License.
"""
profiles.py — Named harmonizer profiles (genre presets).

A profile bundles the ``HMMConfig`` runtime tuning that fits a genre. The
supervised weights (pnote/pchange) are identical across profiles — only the
inference-time objective and structural biases differ.

Usage::

    from melodica.harmonize import harmonizer_profile
    from melodica.engines.coupled_hmm_engine import CoupledHMMEngine
    engine = CoupledHMMEngine(config=harmonizer_profile("jazz"))

Profiles (genre-defining knob = ``completion_bonus``; ``key_coupling_weight``
controls chromaticism, ``extended_chord_penalty`` the 9/dim extensions,
``color_chord_penalty`` the dim/aug/sus color):

  ``pop``  — triadic / functional-pop (``completion_bonus=0``); prior default,
             the behavior every generator had before profiles existed.
  ``jazz`` — 7th harmony, moderate coupling.
  Chromatic 7th (secondary dominants / tritone subs — low coupling):
    ``neo_soul``, ``gospel``
  Diatonic 7th loops (7ths but in-key — higher coupling):
    ``lofi``, ``bossa``, ``citypop``, ``lounge``

See ``docs/HARMONIZATION_CEILING.md``. Per-type completion weights (needed for
dom7-specific genres like blues/funk) are a future extension.

The genre-defining knob is ``completion_bonus``. Other knobs (``key_coupling_weight``,
``color_chord_penalty``, …) are left at their ``HMMConfig`` defaults and can be
overridden per call — e.g. ``harmonizer_profile("jazz", key_coupling_weight=0.3)``.
Tuning those for real lead sheets is pending corpus validation.
"""

from __future__ import annotations

from dataclasses import replace

from melodica.harmonize.coupled_hmm import HMMConfig

# Stored presets. completion_bonus is the genre-defining knob; the others shape
# chromaticism (key_coupling_weight), extensions (extended_chord_penalty on the
# 9/dim types 9,10,11), and color (color_chord_penalty on dim/aug/sus 2..5).
# See docs/HARMONIZATION_CEILING.md.
_PROFILES: dict[str, HMMConfig] = {
    # Triadic / functional-pop — prior default behavior.
    "pop":  HMMConfig(completion_bonus=0.0),
    # 7th-chord harmony, moderate coupling.
    "jazz": HMMConfig(completion_bonus=5.0, key_coupling_weight=0.5),
    # Chromatic 7th — secondary dominants / tritone subs (low coupling).
    "neo_soul": HMMConfig(completion_bonus=5.0, key_coupling_weight=0.3, extended_chord_penalty=0.0, color_chord_penalty=4.0),
    "gospel":   HMMConfig(completion_bonus=5.0, key_coupling_weight=0.3, extended_chord_penalty=0.2, color_chord_penalty=3.0),
    # Diatonic 7th loops — 7ths but in-key (higher coupling).
    "lofi":     HMMConfig(completion_bonus=4.0, key_coupling_weight=1.5, extended_chord_penalty=0.5, color_chord_penalty=8.0),
    "bossa":    HMMConfig(completion_bonus=4.0, key_coupling_weight=1.2, extended_chord_penalty=0.8, color_chord_penalty=6.0),
    "citypop":  HMMConfig(completion_bonus=3.0, key_coupling_weight=1.5, extended_chord_penalty=0.5, color_chord_penalty=5.0),
    "lounge":   HMMConfig(completion_bonus=3.0, key_coupling_weight=1.0, extended_chord_penalty=0.3, color_chord_penalty=4.0),
}

#: Public, read-only view of the named profile presets.
PROFILES: dict[str, HMMConfig] = dict(_PROFILES)


def harmonizer_profile(name: str = "pop", **overrides) -> HMMConfig:
    """Return a fresh ``HMMConfig`` for the named profile, with optional overrides.

    Always returns a copy, so mutating the result never affects the stored preset.
    """
    if name not in _PROFILES:
        raise ValueError(
            f"Unknown harmonizer profile {name!r}. Known: {sorted(_PROFILES)}."
        )
    base = _PROFILES[name]
    return replace(base, **overrides) if overrides else replace(base)
