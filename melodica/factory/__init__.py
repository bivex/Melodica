"""Factory package — entry point for generator creation."""

from __future__ import annotations

import random
from typing import Any

from melodica.generators import GeneratorParams
from melodica.types import NoteInfo
from ._registry import GENERATOR_REGISTRY


def create_generator(
    generator_type: str,
    params: GeneratorParams,
    cfg_params: dict[str, Any] | None = None,
) -> Any:
    """
    Create a generator instance based on type string and config params.

    Args:
        generator_type: String key identifying the generator (e.g., "melody", "trap_drums").
        params: GeneratorParams instance with core parameters.
        cfg_params: Optional dict of additional configuration for the generator.

    Returns:
        Instantiated generator object, or None if generator_type is not registered.
    """
    p = cfg_params or {}
    factory_fn = GENERATOR_REGISTRY.get(generator_type)
    if factory_fn is None:
        return None
    return factory_fn(params, p)


def _create_markov_rhythm(p: dict[str, Any]):
    """Helper to create MarkovRhythmGenerator (lazy import to avoid circular deps)."""
    from melodica.rhythm.markov_rhythm import MarkovRhythmGenerator as MRG

    return MRG(
        style=p.get("markov_style", "straight"),
        syncopation=p.get("syncopation", 0.15),
        phrase_length=p.get("phrase_length", 8),
        seed=p.get("seed", None),
    )


def apply_variation(
    var_name: str,
    notes: list[NoteInfo],
) -> list[NoteInfo]:
    """Apply a named variation transformation to a list of notes."""
    match var_name:
        case "transpose_up":
            return [
                NoteInfo(
                    pitch=n.pitch + 12,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "transpose_down":
            return [
                NoteInfo(
                    pitch=n.pitch - 12,
                    start=n.start,
                    duration=n.duration,
                    velocity=n.velocity,
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "staccato":
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration * 0.3,
                    velocity=n.velocity,
                    articulation="staccato",
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "legato":
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=n.start,
                    duration=n.duration * 1.5,
                    velocity=n.velocity,
                    articulation="legato",
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "humanize":
            return [
                NoteInfo(
                    pitch=n.pitch,
                    start=round(n.start + random.uniform(-0.05, 0.05), 6),
                    duration=n.duration,
                    velocity=max(1, min(127, n.velocity + random.randint(-10, 10))),
                    articulation=n.articulation,
                    expression=dict(n.expression),
                )
                for n in notes
            ]
        case "octave_double":
            result = list(notes)
            for n in notes:
                result.append(
                    NoteInfo(
                        pitch=n.pitch + 12,
                        start=n.start,
                        duration=n.duration,
                        velocity=max(1, n.velocity - 15),
                        articulation=n.articulation,
                        expression=dict(n.expression),
                    )
                )
            return result
        case _:
            return notes


# Register markov_rhythm into the registry (takes only cfg, no params)
if "markov_rhythm" not in GENERATOR_REGISTRY:
    GENERATOR_REGISTRY["markov_rhythm"] = lambda params, cfg: _create_markov_rhythm(cfg)  # type: ignore

__all__ = ["create_generator", "apply_variation", "GENERATOR_REGISTRY"]
