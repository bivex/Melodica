# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
engines/__init__.py — Engine registry and shared interface.

Layer: Application
Rules:
  - Defines the HarmonizerPort protocol (ISP: one method).
  - Provides build_engine() factory to avoid direct instantiation by callers.
  - OCP: new engines are added without modifying this file's interface.
"""

from __future__ import annotations

import typing
from typing import Callable, Protocol

from melodica.types import ChordLabel, HarmonizationEngine, HarmonizationRequest
from melodica.engines.microtuning import MicrotuningEngine


class HarmonizerPort(Protocol):
    """
    Port that every harmonization engine must satisfy.
    Callers depend only on this protocol — never on concrete engine classes.
    """

    def harmonize(self, req: HarmonizationRequest) -> list[ChordLabel]: ...


EngineFactory = Callable[..., HarmonizerPort]


class EngineRegistry:
    """
    Registry for harmonization engine factories supporting the Open-Closed Principle.
    Allows runtime registration of new/custom harmonization engines without modifying core files.
    """

    _custom_factories: dict[str | int, EngineFactory] = {}

    @classmethod
    def register(cls, key: str | int | HarmonizationEngine, factory: EngineFactory) -> None:
        """Register a custom engine factory for a key (string, integer, or HarmonizationEngine)."""
        if isinstance(key, HarmonizationEngine):
            cls._custom_factories[key.value] = factory
            cls._custom_factories[key.name.lower()] = factory
        elif isinstance(key, str):
            cls._custom_factories[key.lower().replace("-", "_").replace(" ", "_")] = factory
        else:
            cls._custom_factories[key] = factory

    @classmethod
    def unregister(cls, key: str | int | HarmonizationEngine) -> None:
        """Remove a custom engine factory."""
        if isinstance(key, HarmonizationEngine):
            cls._custom_factories.pop(key.value, None)
            cls._custom_factories.pop(key.name.lower(), None)
        elif isinstance(key, str):
            cls._custom_factories.pop(key.lower().replace("-", "_").replace(" ", "_"), None)
        else:
            cls._custom_factories.pop(key, None)

    @classmethod
    def get(cls, key: str | int | HarmonizationEngine) -> EngineFactory | None:
        """Look up a registered engine factory."""
        if key in cls._custom_factories:
            return cls._custom_factories[key]
        if isinstance(key, str):
            normalized = key.lower().replace("-", "_").replace(" ", "_")
            return cls._custom_factories.get(normalized)
        return None


def build_engine(engine_id: int | str | HarmonizationEngine = 4, **kwargs: object) -> HarmonizerPort:
    """
    Factory: construct the appropriate engine by ID, name, or registered factory.

    engine_id: 0 = Functional, 1 = RuleBased, 2 = Adaptive, 3 = HMM, 4 = Coupled HMM (default),
               or a string name / registered custom engine.
    kwargs:    forwarded to engine constructors

    OCP compliance: register new engines with EngineRegistry.register().
    """
    # 1. Check custom registry first
    custom_factory = EngineRegistry.get(engine_id)
    if custom_factory is not None:
        return custom_factory(**kwargs)

    # 2. Resolve to standard HarmonizationEngine
    try:
        resolved = HarmonizationEngine.from_value(engine_id)
    except ValueError:
        raise ValueError(f"Unknown engine {engine_id!r}. Must be 0, 1, 2, 3, 4 or registered in EngineRegistry.")

    from melodica.engines.adaptive import AdaptiveEngine
    from melodica.engines.coupled_hmm_engine import CoupledHMMEngine
    from melodica.engines.functional import FunctionalEngine
    from melodica.engines.rule_based import RuleBasedEngine
    from melodica.engines.hmm_engine import HMMEngine

    match resolved:
        case HarmonizationEngine.FUNCTIONAL:
            return FunctionalEngine()
        case HarmonizationEngine.RULE_BASED:
            rule_db = kwargs.get("rule_db")
            return RuleBasedEngine(rule_db=rule_db)  # type: ignore[arg-type]
        case HarmonizationEngine.ADAPTIVE:
            allowed = {
                "simplicity_weight",
                "melody_fit_weight",
                "stability_weight",
                "allow_modal_mixture",
            }
            engine_kwargs = {k: v for k, v in kwargs.items() if k in allowed}
            return AdaptiveEngine(**engine_kwargs)  # type: ignore[arg-type]
        case HarmonizationEngine.HMM:
            melody_weight = kwargs.get("melody_weight", 0.4)
            voice_weight = kwargs.get("voice_weight", 0.3)
            transition_weight = kwargs.get("transition_weight", 0.3)
            engine_kwargs = {
                k: v for k, v in kwargs.items()
                if k not in ("melody_weight", "voice_weight", "transition_weight")
            }
            return HMMEngine(
                melody_weight=melody_weight,  # type: ignore[arg-type]
                voice_weight=voice_weight,  # type: ignore[arg-type]
                transition_weight=transition_weight,  # type: ignore[arg-type]
                **engine_kwargs,
            )
        case HarmonizationEngine.COUPLED_HMM:
            return CoupledHMMEngine(**kwargs)
        case _:
            raise ValueError(f"Unknown engine_id {engine_id}. Must be 0, 1, 2, 3, or 4.")
