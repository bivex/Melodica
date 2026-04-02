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

"""tests/test_engines.py — Integration tests for all three harmonization engines."""

import pytest
from melodica.types import ChordLabel, HarmonizationRequest, Mode, Note, Scale
from melodica.engines.functional import FunctionalEngine
from melodica.engines.rule_based import RuleBasedEngine
from melodica.engines.adaptive import AdaptiveEngine
from melodica import harmonize


def _c_major_melody() -> list[Note]:
    """Simple C major scale fragment for testing."""
    pitches = [60, 62, 64, 65, 67, 69, 71, 72]
    return [Note(pitch=p, start=float(i), duration=1.0) for i, p in enumerate(pitches)]


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


class TestFunctionalEngine:
    def test_returns_chord_sequence(self):
        req = HarmonizationRequest(melody=_c_major_melody(), key=C_MAJOR, chord_rhythm=2.0)
        engine = FunctionalEngine()
        chords = engine.harmonize(req)
        assert isinstance(chords, list)
        assert len(chords) > 0
        assert all(isinstance(c, ChordLabel) for c in chords)

    def test_timing_coverage(self):
        melody = _c_major_melody()
        req = HarmonizationRequest(melody=melody, key=C_MAJOR, chord_rhythm=4.0)
        chords = FunctionalEngine().harmonize(req)
        assert chords[0].start == 0.0
        last = chords[-1]
        melody_end = max(n.start + n.duration for n in melody)
        assert last.end >= melody_end - 4.0  # within one rhythm window

    def test_diatonic_only(self):
        req = HarmonizationRequest(melody=_c_major_melody(), key=C_MAJOR, chord_rhythm=2.0)
        chords = FunctionalEngine().harmonize(req)
        # All chord roots should be in C major
        major_degs = C_MAJOR.degrees()
        for c in chords:
            assert c.root in major_degs, f"Non-diatonic root {c.root} in {c}"


class TestRuleBasedEngine:
    def test_returns_nonempty(self):
        req = HarmonizationRequest(melody=_c_major_melody(), key=C_MAJOR, chord_rhythm=2.0)
        chords = RuleBasedEngine().harmonize(req)
        assert len(chords) == len(_c_major_melody()) // 2 + (len(_c_major_melody()) % 2)

    def test_with_custom_rule_db(self):
        from melodica.rule_db import ChordProgressionRuleDB
        db = ChordProgressionRuleDB.default()
        req = HarmonizationRequest(melody=_c_major_melody(), key=C_MAJOR, chord_rhythm=2.0, rule_db=db)
        engine = RuleBasedEngine(rule_db=db)
        chords = engine.harmonize(req)
        assert chords  # non-empty result

    def test_chord_sequence_length(self):
        melody = [Note(pitch=60 + i, start=float(i), duration=1.0) for i in range(8)]
        req = HarmonizationRequest(melody=melody, key=C_MAJOR, chord_rhythm=2.0)
        chords = RuleBasedEngine().harmonize(req)
        assert len(chords) == 4  # 8 beats / 2 beats per chord


class TestAdaptiveEngine:
    def test_returns_chord_sequence(self):
        req = HarmonizationRequest(melody=_c_major_melody(), key=C_MAJOR, chord_rhythm=2.0)
        engine = AdaptiveEngine()
        chords = engine.harmonize(req)
        assert isinstance(chords, list)
        assert all(isinstance(c, ChordLabel) for c in chords)

    def test_custom_weights(self):
        req = HarmonizationRequest(melody=_c_major_melody(), key=C_MAJOR, chord_rhythm=2.0)
        engine = AdaptiveEngine(simplicity_weight=0.8, melody_fit_weight=0.2)
        chords = engine.harmonize(req)
        assert chords  # should still produce output

    def test_search_candidates_nonempty(self):
        from melodica.engines.adaptive import NoteSectionHarm
        engine = AdaptiveEngine()
        seg = NoteSectionHarm(
            segment_start=0.0,
            segment_end=2.0,
            melody_pitches=[0, 4, 7],  # C E G
        )
        candidates = engine.search_candidates(seg, C_MAJOR)
        assert len(candidates) > 0

    def test_score_candidates(self):
        from melodica.engines.adaptive import NoteSectionHarm
        engine = AdaptiveEngine()
        seg = NoteSectionHarm(
            segment_start=0.0,
            segment_end=2.0,
            melody_pitches=[0, 4, 7],
        )
        candidates = engine.search_candidates(seg, C_MAJOR)
        scored = engine.score_candidates(candidates, seg, key=C_MAJOR)
        assert len(scored) == len(candidates)
        assert all(isinstance(s, float) for _, s in scored)


class TestUnifiedHarmonize:
    def test_functional_by_name(self):
        melody = _c_major_melody()
        chords = harmonize(melody, engine="functional", chord_rhythm=4.0, key=C_MAJOR)
        assert chords

    def test_adaptive_auto_key(self):
        melody = _c_major_melody()
        chords = harmonize(melody, engine="adaptive", chord_rhythm=4.0)
        assert chords

    def test_invalid_engine_name(self):
        with pytest.raises(ValueError):
            harmonize(_c_major_melody(), engine="magic")

    def test_invalid_engine_int(self):
        with pytest.raises(ValueError):
            harmonize(_c_major_melody(), engine=99, key=C_MAJOR)
