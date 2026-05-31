"""Tests for orchestration_rules — InstrumentRange, OrchestrationRules."""

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.orchestration_rules import (
    InstrumentRange, OrchestrationRules, OrchestrationWarning, INSTRUMENTS,
)


class TestInstrumentDatabase:
    def test_instruments_exist(self):
        assert len(INSTRUMENTS) >= 25

    def test_common_instruments_present(self):
        for name in ("violin", "viola", "cello", "contrabass", "flute", "oboe",
                      "french_horn", "trumpet", "trombone", "piano", "harp"):
            assert name in INSTRUMENTS

    def test_range_sanity(self):
        for name, ir in INSTRUMENTS.items():
            assert ir.min_midi <= ir.comfortable_low, f"{name}: min > comfortable_low"
            assert ir.comfortable_low <= ir.comfortable_high, f"{name}: comfortable range inverted"
            assert ir.comfortable_high <= ir.max_midi, f"{name}: comfortable_high > max"


class TestOrchestrationRulesValidate:
    def setup_method(self):
        self.rules = OrchestrationRules()

    def test_valid_notes_no_warnings(self):
        notes = [NoteInfo(pitch=60, start=0, duration=1, velocity=64)]
        warnings = self.rules.validate(notes, "violin")
        assert all(w.severity != "error" for w in warnings)

    def test_below_range(self):
        notes = [NoteInfo(pitch=30, start=0, duration=1, velocity=64)]
        warnings = self.rules.validate(notes, "violin")
        assert any(w.severity == "error" and "below" in w.message for w in warnings)

    def test_above_range(self):
        notes = [NoteInfo(pitch=110, start=0, duration=1, velocity=64)]
        warnings = self.rules.validate(notes, "violin")
        assert any(w.severity == "error" and "above" in w.message for w in warnings)

    def test_extended_register_info(self):
        notes = [NoteInfo(pitch=97, start=0, duration=1, velocity=64)]
        warnings = self.rules.validate(notes, "violin")
        assert any(w.severity == "info" for w in warnings)

    def test_unknown_instrument(self):
        notes = [NoteInfo(pitch=60, start=0, duration=1, velocity=64)]
        warnings = self.rules.validate(notes, "kazoo")
        assert any(w.severity == "error" and "Unknown" in w.message for w in warnings)


class TestOrchestrationRulesClamp:
    def setup_method(self):
        self.rules = OrchestrationRules()

    def test_clamp_low(self):
        notes = [NoteInfo(pitch=20, start=0, duration=1, velocity=64)]
        clamped = self.rules.clamp_to_range(notes, "violin")
        assert clamped[0].pitch == 55  # violin min

    def test_clamp_high(self):
        notes = [NoteInfo(pitch=120, start=0, duration=1, velocity=64)]
        clamped = self.rules.clamp_to_range(notes, "violin")
        assert clamped[0].pitch == 103  # violin max

    def test_clamp_preserves_other_fields(self):
        notes = [NoteInfo(pitch=20, start=1.5, duration=2.0, velocity=80,
                          articulation="staccato")]
        clamped = self.rules.clamp_to_range(notes, "violin")
        assert clamped[0].start == 1.5
        assert clamped[0].duration == 2.0
        assert clamped[0].velocity == 80

    def test_unknown_instrument_returns_unchanged(self):
        notes = [NoteInfo(pitch=20, start=0, duration=1, velocity=64)]
        result = self.rules.clamp_to_range(notes, "kazoo")
        assert result == notes


class TestOrchestrationRulesHelpers:
    def setup_method(self):
        self.rules = OrchestrationRules()

    def test_suggest_octave_returns_comfortable(self):
        suggestion = self.rules.suggest_octave("violin", 60)
        ir = INSTRUMENTS["violin"]
        assert ir.comfortable_low <= suggestion <= ir.comfortable_high

    def test_register_at_middle(self):
        reg = self.rules.register_at("violin", 72)
        assert reg == "middle"

    def test_register_at_unknown(self):
        reg = self.rules.register_at("kazoo", 60)
        assert reg == "unknown"

    def test_blend_with_overlapping(self):
        result = self.rules.blend_with("violin", "viola")
        assert result["overlap_semitones"] > 0
        assert result["blend_quality"] in ("strong", "moderate", "weak")

    def test_blend_with_unknown(self):
        result = self.rules.blend_with("violin", "kazoo")
        assert "error" in result
