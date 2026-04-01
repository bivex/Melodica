"""
engines/__init__.py — Engine registry and shared interface.

Layer: Application
Rules:
  - Defines the HarmonizerPort protocol (ISP: one method).
  - Provides build_engine() factory to avoid direct instantiation by callers.
  - OCP: new engines are added without modifying this file's interface.
"""

from __future__ import annotations

from typing import Protocol

from melodica.types import ChordLabel, HarmonizationRequest


class HarmonizerPort(Protocol):
    """
    Port that every harmonization engine must satisfy.
    Callers depend only on this protocol — never on concrete engine classes.
    """

    def harmonize(self, req: HarmonizationRequest) -> list[ChordLabel]: ...


def build_engine(engine_id: int = 3, **kwargs: object) -> HarmonizerPort:
    """
    Factory: construct the appropriate engine by ID.

    engine_id: 0 = Functional, 1 = RuleBased, 2 = Adaptive, 3 = HMM (default)
    kwargs:    forwarded to engine constructors

    OCP compliance: add a new ID branch here instead of modifying engine code.
    """
    from melodica.engines.adaptive import AdaptiveEngine
    from melodica.engines.functional import FunctionalEngine
    from melodica.engines.rule_based import RuleBasedEngine
    from melodica.engines.hmm_engine import HMMEngine

    match engine_id:
        case 0:
            return FunctionalEngine()
        case 1:
            rule_db = kwargs.get("rule_db")
            return RuleBasedEngine(rule_db=rule_db)  # type: ignore[arg-type]
        case 2:
            allowed = {
                "simplicity_weight",
                "melody_fit_weight",
                "stability_weight",
                "allow_modal_mixture",
            }
            engine_kwargs = {k: v for k, v in kwargs.items() if k in allowed}
            return AdaptiveEngine(**engine_kwargs)  # type: ignore[arg-type]
        case 3:
            return HMMEngine(
                melody_weight=kwargs.get("melody_weight", 0.4),  # type: ignore[arg-type]
                voice_weight=kwargs.get("voice_weight", 0.3),  # type: ignore[arg-type]
                transition_weight=kwargs.get("transition_weight", 0.3),  # type: ignore[arg-type]
            )
        case _:
            raise ValueError(f"Unknown engine_id {engine_id}. Must be 0, 1, 2, or 3.")
