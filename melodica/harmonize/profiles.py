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

Profiles:
  ``pop``  — triadic / functional-pop objective (``completion_bonus=0``). This is
             the behavior every generator had before profiles existed; the safe
             default.
  ``jazz`` — extended-harmony objective (``completion_bonus≈5``). The
             set-completion term lets maj7/min7/dom7 win when the melody spells
             them, recovering ii–V–I and secondary dominants. See
             ``docs/HARMONIZATION_CEILING.md`` for the full diagnosis.

The genre-defining knob is ``completion_bonus``. Other knobs (``key_coupling_weight``,
``color_chord_penalty``, …) are left at their ``HMMConfig`` defaults and can be
overridden per call — e.g. ``harmonizer_profile("jazz", key_coupling_weight=0.3)``.
Tuning those for real lead sheets is pending corpus validation.
"""

from __future__ import annotations

from dataclasses import replace

from melodica.harmonize.coupled_hmm import HMMConfig

# Stored presets. completion_bonus is the genre-defining knob.
_PROFILES: dict[str, HMMConfig] = {
    "pop": HMMConfig(completion_bonus=0.0),
    "jazz": HMMConfig(completion_bonus=5.0),
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
