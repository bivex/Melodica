"""
tests/test_tonality_bridge.py — Tests for the Tonality (mts) integration seam.

Covers:
  - HAVE_TONALITY flag / engine availability
  - plural ranked chord naming (C6-vs-Am7 ambiguity)
  - exact voice-leading distance
  - next-chord recommendation (V -> I ranking)
  - progression verification oracle
"""

import pytest

from melodica.theory import HAVE_TONALITY
from melodica.theory.chords import Quality
from melodica.theory.modes import Mode
from melodica.theory.tonality_bridge import (
    analyze_progression,
    name_chord_label,
    recommend_next,
    verify_progression,
    voice_lead_exact,
    voice_leading_distance,
)
from melodica.types import ChordLabel, Scale

pytestmark = pytest.mark.skipif(
    not HAVE_TONALITY, reason="mts (Tonality) submodule not available"
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


class TestPluralNaming:
    def test_unambiguous_major_seventh(self):
        naming = name_chord_label(ChordLabel(0, Quality.MAJOR7))  # Cmaj7 {0,4,7,11}
        assert naming.chosen is not None
        assert naming.chosen.interpretation.quality == "maj7"
        assert naming.is_ambiguous is False

    def test_c6_vs_am7_ambiguity_surfaces_alternatives(self):
        # A m7 set {9,0,4,7} admits both C6 and Am7 readings — must be surfaced.
        naming = name_chord_label(ChordLabel(9, Quality.MINOR7))
        qualities = {a.interpretation.quality for a in naming.alternatives} | {
            naming.chosen.interpretation.quality
        }
        assert naming.is_ambiguous is True
        assert {"maj6", "min7"}.issubset(qualities)


class TestVoiceLeading:
    def test_c_major_to_g_major_distance(self):
        # C {0,4,7} -> G {7,11,2}: minimal motion is 3 semitones.
        d = voice_leading_distance(ChordLabel(0, Quality.MAJOR), ChordLabel(7, Quality.MAJOR))
        assert d == 3

    def test_identity_is_zero(self):
        assert voice_leading_distance([0, 4, 7], [0, 4, 7]) == 0


class TestExactVoiceLeading:
    @staticmethod
    def _motion(a, b):
        return sum(abs(x - y) for x, y in zip(sorted(a), sorted(b)))

    def test_voicing_uses_only_target_pcs(self):
        src = [60, 64, 67]  # C major
        ex = voice_lead_exact(src, ChordLabel(7, Quality.MAJOR))  # -> G major
        target_pcs = ChordLabel(7, Quality.MAJOR).pitch_classes()
        assert all(p % 12 in target_pcs for p in ex.voicing)

    def test_realized_motion_matches_identity(self):
        # On equal-cardinality pc-distinct sets the realized total motion
        # equals the identity-level optimal distance.
        src = [60, 64, 67]
        ex = voice_lead_exact(src, ChordLabel(7, Quality.MAJOR))
        assert ex.realized_distance == ex.identity_distance == 3

    def test_exact_beats_or_matches_heuristic(self):
        # The inversion-only heuristic voice_lead can't drop a chord below the
        # source; exact voice-leading finds the minimal-motion realization.
        from melodica.theory.voicing import chord_to_notes, voice_lead

        for a, b in [
            (ChordLabel(0, Quality.MAJOR), ChordLabel(7, Quality.MAJOR)),
            (ChordLabel(0, Quality.MAJOR7), ChordLabel(5, Quality.MAJOR7)),
            (ChordLabel(2, Quality.MINOR7), ChordLabel(7, Quality.DOMINANT7)),
        ]:
            src = chord_to_notes(a)
            heuristic_motion = self._motion(src, voice_lead(src, b))
            ex = voice_lead_exact(src, b)
            assert ex.realized_distance <= heuristic_motion

    def test_accepts_chordlabel_source(self):
        # prev may be a ChordLabel, not just a MIDI list.
        ex = voice_lead_exact(ChordLabel(0, Quality.MAJOR), ChordLabel(9, Quality.MINOR))
        assert all(p % 12 in ChordLabel(9, Quality.MINOR).pitch_classes() for p in ex.voicing)
        assert ex.realized_distance <= 2  # C -> Am: one voice moves a tone

    def test_empty_inputs_raise(self):
        with pytest.raises(ValueError):
            voice_lead_exact([], ChordLabel(0, Quality.MAJOR))
        with pytest.raises(ValueError):
            voice_lead_exact([60, 64, 67], [])


class TestSuccession:
    def test_dominant_resolves_to_tonic_first(self):
        rec = recommend_next(ChordLabel(7, Quality.DOMINANT7), C_MAJOR)  # G7 in C
        assert rec is not None
        top = rec.candidates[0]
        assert top.root_pc == 0  # resolves to I (C)

    def test_modal_key_declines_to_guess(self):
        # Dorian is unsupported by mts succession -> None, not a raised error.
        dorian = Scale(root=0, mode=Mode.DORIAN)
        assert recommend_next(ChordLabel(7, Quality.DOMINANT7), dorian) is None


class TestVerifyProgression:
    def test_ii_v_i_is_fully_parseable(self):
        prog = [
            ChordLabel(2, Quality.MINOR7),     # Dm7
            ChordLabel(7, Quality.DOMINANT7),  # G7
            ChordLabel(0, Quality.MAJOR7),     # Cmaj7
        ]
        report = verify_progression(prog)
        assert report["n"] == 3
        assert report["unparseable"] == 0
        assert report["parseable"] == 3
        assert report["total_voice_leading"] >= 0
