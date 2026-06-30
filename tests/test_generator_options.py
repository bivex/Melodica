# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

"""
test_generator_options.py — tests for the declarative generator option contract.

Covers:
  - OptionSpec / validate_options / validate_option (the foundation)
  - PhraseGenerator.valid_options / describe introspection
  - Each migrated generator: accepts valid options, rejects typos (the whole
    point — silent coercion must no longer hide typos), and publishes an
    OPTION_SCHEMA whose defaults are themselves valid.
"""

import pytest

from melodica.generators import PhraseGenerator
from melodica.generators._options import OptionSpec, validate_option, validate_options


# ---------------------------------------------------------------------------
# Foundation: OptionSpec + validators
# ---------------------------------------------------------------------------

class TestOptionSpec:
    def test_valid_construction(self):
        spec = OptionSpec("style", frozenset({"a", "b"}), default="a")
        assert spec.name == "style"
        assert spec.default == "a"

    def test_default_outside_choices_is_author_bug(self):
        # A schema whose own default is invalid is a generator-author mistake,
        # not a caller error — it must fail at schema definition time.
        with pytest.raises(ValueError, match="default"):
            OptionSpec("style", frozenset({"a", "b"}), default="c")


class TestValidators:
    def test_validate_option_accepts_member(self):
        spec = OptionSpec("x", frozenset({"a", "b"}), default="a")
        assert validate_option(spec, "b", "Owner") == "b"

    def test_validate_option_rejects_typo_with_helpful_message(self):
        spec = OptionSpec("x", frozenset({"a", "b"}), default="a")
        with pytest.raises(ValueError) as exc:
            validate_option(spec, "c", "Owner")
        msg = str(exc.value)
        assert "Owner.x" in msg
        assert "'a', 'b'" in msg  # sorted choices present
        assert "'c'" in msg       # offending value present

    def test_validate_options_only_checks_present_keys(self):
        spec = OptionSpec("x", frozenset({"a", "b"}), default="a")
        # caller omitted 'x' entirely → no error, returns empty
        out = validate_options((spec,), {}, owner="O")
        assert out == {}

    def test_validate_options_check_default_passes_for_valid_schema(self):
        # A schema whose defaults are all valid passes the check_default sweep.
        spec = OptionSpec("x", frozenset({"a", "b"}), default="a")
        validate_options((spec,), {}, owner="O", check_default=True)  # no raise

    def test_option_spec_rejects_invalid_default_at_construction(self):
        # An invalid default is a schema-author bug and is caught when the
        # OptionSpec itself is built (not deferred to validate_options).
        with pytest.raises(ValueError, match="default"):
            OptionSpec("y", frozenset({"a", "b"}), default="c")


# ---------------------------------------------------------------------------
# PhraseGenerator introspection
# ---------------------------------------------------------------------------

class TestIntrospection:
    def test_base_phrase_generator_has_empty_schema(self):
        # unmigrated generators are unaffected — the default is an empty schema
        assert PhraseGenerator.OPTION_SCHEMA == ()
        assert PhraseGenerator.valid_options() == {}

    def test_describe_empty_schema(self):
        assert "no OPTION_SCHEMA" in PhraseGenerator.describe()

    def test_subclass_introspection(self):
        from melodica.generators.bass import BassGenerator
        opts = BassGenerator.valid_options()
        assert "style" in opts
        assert "walking" in opts["style"]
        desc = BassGenerator.describe()
        assert "BassGenerator" in desc
        assert "style" in desc


# ---------------------------------------------------------------------------
# Migrated generators: valid accepted, typos rejected, defaults are valid
# ---------------------------------------------------------------------------

# Each entry: (generator class, {kwarg: valid_value}, {kwarg: invalid_value})
MIGRATED = [
    ("melodica.generators.bass:BassGenerator",
     {"style": "walking"}, {"style": "driving"}),
    ("melodica.generators.nebula:NebulaGenerator",
     {"variant": "granular"}, {"variant": "mist"}),
    ("melodica.generators.tubular_bells:TubularBellsGenerator",
     {"stroke_pattern": "chime"}, {"stroke_pattern": "bang"}),
    ("melodica.generators.orchestral_brass:FrenchHornGenerator",
     {"articulation": "fanfare"}, {"articulation": "plucked"}),
    ("melodica.generators.orchestral_brass:TrumpetGenerator",
     {"dynamic_curve": "crescendo"}, {"dynamic_curve": "loud"}),
    ("melodica.generators.orchestral_brass:TromboneGenerator",
     {"articulation": "legato"}, {"articulation": "bowed"}),
    ("melodica.generators.strings_ensemble:StringsEnsembleGenerator",
     {"section_size": "chamber"}, {"section_size": "huge"}),
    ("melodica.generators.canon:CanonGenerator",
     {"canon_type": "inversion"}, {"canon_type": "mirror"}),
]


def _load(qualified: str):
    mod, cls = qualified.split(":")
    import importlib
    return getattr(importlib.import_module(mod), cls)


@pytest.mark.parametrize("qualified,valid_kw,invalid_kw", MIGRATED)
def test_migrated_accepts_valid_option(qualified, valid_kw, invalid_kw):
    Gen = _load(qualified)
    # valid value must construct without error
    inst = Gen(**valid_kw)
    for k, v in valid_kw.items():
        assert getattr(inst, k) == v


@pytest.mark.parametrize("qualified,valid_kw,invalid_kw", MIGRATED)
def test_migrated_rejects_typo(qualified, valid_kw, invalid_kw):
    Gen = _load(qualified)
    # the invalid value must raise — no silent coercion to a default
    with pytest.raises(ValueError) as exc:
        Gen(**invalid_kw)
    msg = str(exc.value)
    # error names the offending option and value
    bad_opt = next(iter(invalid_kw))
    assert bad_opt in msg
    assert repr(invalid_kw[bad_opt]) in msg


@pytest.mark.parametrize("qualified,valid_kw,invalid_kw", MIGRATED)
def test_migrated_schema_defaults_are_valid(qualified, valid_kw, invalid_kw):
    Gen = _load(qualified)
    # every declared default must be a member of its own choice set
    for spec in Gen.OPTION_SCHEMA:
        assert spec.default in spec.choices


@pytest.mark.parametrize("qualified,valid_kw,invalid_kw", MIGRATED)
def test_migrated_publishes_schema(qualified, valid_kw, invalid_kw):
    Gen = _load(qualified)
    assert len(Gen.OPTION_SCHEMA) >= 1, f"{Gen.__name__} should declare OPTION_SCHEMA"
    assert Gen.valid_options()  # non-empty introspection
