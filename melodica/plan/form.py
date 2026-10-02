# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
melodica.plan.form — Musical form generation, architecture patterns, and validation.

Connects form plan templates (AABA, Sonata, Rondo) and formal musical syntax
validation (voice crossings, range boundaries, consecutive leaps).
"""

from __future__ import annotations

from melodica.form import FormTemplate, generate_form_plan
from melodica.form_validator import (
    ArrangementValidator,
    FormRuleViolation,
    ValidationReport,
    validate_arrangement,
)

__all__ = [
    "FormTemplate",
    "generate_form_plan",
    "ArrangementValidator",
    "FormRuleViolation",
    "ValidationReport",
    "validate_arrangement",
]
