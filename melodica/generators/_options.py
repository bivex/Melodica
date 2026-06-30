# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
generators/_options.py — declarative option schema for PhraseGenerator subclasses.

Before this module, each generator validated its string-valued options ad-hoc
in its own ``__init__`` with one of three inconsistent behaviours: raise
(bass), silent coercion via ``dict.get(key, default)`` (brass / strings /
tubular bells — a typo silently swapped in the default!), or deferred-to-render
(nebula). The boilerplate ``if x not in SET: raise ValueError(...)`` was copied
into ~43 files.

This module gives generators ONE way to declare and validate their options:

    OPTION_SCHEMA = (
        OptionSpec("style", choices=STYLES, default="root_only",
                   description="bass movement style"),
        ...
    )

A generator's ``__init__`` then validates in one call::

    validate_options(self.OPTION_SCHEMA, {"style": style, ...}, owner=type(self).__name__)

Validation is STRICT (the bass.py behaviour): an invalid value raises
``ValueError`` at construction time with a message naming the option, the valid
choices, and the offending value — so typos fail loudly instead of silently
producing wrong output.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


@dataclass(frozen=True)
class OptionSpec:
    """Declarative description of a single string-valued generator option.

    Attributes:
        name:        the option's keyword-argument name (e.g. ``"style"``).
        choices:     the complete set of valid string values.
        default:     the value used when the caller omits the option. Must be a
                     member of ``choices`` (checked lazily by ``validate_options``
                     when ``check_default=True``).
        description: optional human-readable doc, surfaced by ``describe()``.
    """

    name: str
    choices: frozenset[str]
    default: str
    description: str = ""

    def __post_init__(self) -> None:
        # Catch schema-author mistakes early: a default outside the choice set
        # is almost certainly a bug in the generator, not a caller error.
        if self.default not in self.choices:
            raise ValueError(
                f"OptionSpec({self.name!r}) default {self.default!r} is not in "
                f"its own choices {sorted(self.choices)}"
            )


def validate_option(
    spec: OptionSpec, value: Any, owner: str, *, check_default: bool = False
) -> str:
    """Validate a single value against an OptionSpec; return it if valid.

    Raises ``ValueError`` if ``value`` is not in ``spec.choices``. Strict by
    design — there is no silent fallback, because the whole point is that a
    typo must surface here rather than mutate the music unnoticed.
    """
    if value not in spec.choices:
        raise ValueError(
            f"{owner}.{spec.name} must be one of {sorted(spec.choices)}; "
            f"got {value!r}"
        )
    return value


def validate_options(
    specs: Iterable[OptionSpec],
    values: dict[str, Any],
    owner: str,
    *,
    check_default: bool = False,
) -> dict[str, str]:
    """Validate a mapping of option values against a schema.

    Args:
        specs:        the generator's ``OPTION_SCHEMA``.
        values:       the kwargs actually passed (name -> value).
        owner:        class name, used in error messages.
        check_default: if True, also assert each spec's ``default`` is a valid
                       choice (use in tests / schema sanity checks).

    Returns:
        A dict of name -> validated value (a copy of ``values``, restricted to
        the schema's names, all confirmed valid).

    Only options PRESENT in ``values`` are checked — callers that omit an
    option rely on the generator's own default assignment, which is outside
    this function's scope.
    """
    out: dict[str, str] = {}
    for spec in specs:
        if check_default:
            validate_option(spec, spec.default, owner)
        if spec.name in values:
            out[spec.name] = validate_option(spec, values[spec.name], owner)
    return out
