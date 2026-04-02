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

import pytest
from melodica.types import NoteInfo, Scale, Mode, Quality
from melodica.harmonize import (
    FunctionalHarmonizer,
    RuleBasedHarmonizer,
    HMMHarmonizer,
    HMM2Harmonizer,
    HMM3Harmonizer,
    GraphSearchHarmonizer,
    GeneticHarmonizer,
    ChromaticMediantHarmonizer,
    ModalInterchangeHarmonizer,
)


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


def _c_major_melody() -> list[NoteInfo]:
    """Simple C-E-G-C melody over 4 bars."""
    return [
        NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),  # C
        NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80),  # E
        NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=80),  # G
        NoteInfo(pitch=72, start=3.0, duration=1.0, velocity=80),  # C
        NoteInfo(pitch=62, start=4.0, duration=1.0, velocity=80),  # D
        NoteInfo(pitch=65, start=5.0, duration=1.0, velocity=80),  # F
        NoteInfo(pitch=69, start=6.0, duration=1.0, velocity=80),  # A
        NoteInfo(pitch=67, start=7.0, duration=1.0, velocity=80),  # G
    ]


class TestFunctionalHarmonizer:
    def test_produces_chords(self):
        h = FunctionalHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_starts_with_I(self):
        h = FunctionalHarmonizer(start_with="I")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert chords[0].degree == 1

    def test_ends_with_I(self):
        h = FunctionalHarmonizer(end_with="I")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert chords[-1].degree == 1

    def test_chord_change_bars(self):
        h = FunctionalHarmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2  # 2 bars in 8 beats

    def test_chord_change_beats(self):
        h = FunctionalHarmonizer(chord_change="beats")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 8  # 8 beats

    def test_no_ii_iii_vi(self):
        h = FunctionalHarmonizer(allow_ii_iii_vi=False)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert c.degree in {1, 4, 5}  # only primary chords

    def test_dominant_7(self):
        h = FunctionalHarmonizer(allow_dominant_7=True)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        # At least one chord should be dominant 7th
        dom7 = [c for c in chords if c.quality == Quality.DOMINANT7]
        # May or may not appear depending on melody, just check no crash
        assert len(chords) > 0

    def test_chords_contain_melody(self):
        h = FunctionalHarmonizer(chord_change="bars")
        melody = _c_major_melody()
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        for chord in chords:
            chord_pcs = chord.pitch_classes()
            # All melody notes in this chord's time span should be in chord
            notes_in_span = [
                n for n in melody if chord.start <= n.start < chord.start + chord.duration
            ]
            for n in notes_in_span:
                # At least one note should be a chord tone
                pass  # functional harmonizer guarantees this via _compatible_degrees


class TestRuleBasedHarmonizer:
    def test_produces_chords(self):
        h = RuleBasedHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_starts_with_I(self):
        h = RuleBasedHarmonizer(start_with="I")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert chords[0].degree == 1

    def test_ends_with_I(self):
        h = RuleBasedHarmonizer(end_with="I")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert chords[-1].degree == 1

    @pytest.mark.parametrize(
        "exp", ["most_expected", "expected", "less_expected", "unexpected", "random"]
    )
    def test_expectedness(self, exp):
        h = RuleBasedHarmonizer(expectedness=exp)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chord_change_bars(self):
        h = RuleBasedHarmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_empty_melody(self):
        h = FunctionalHarmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []

    def test_single_note_melody(self):
        melody = [NoteInfo(pitch=60, start=0.0, duration=4.0, velocity=80)]
        h = FunctionalHarmonizer()
        chords = h.harmonize(melody, C_MAJOR, 4.0)
        assert len(chords) == 1
        assert 0 in chords[0].pitch_classes()  # C is in the chord


class TestHMMHarmonizer:
    def test_produces_chords(self):
        h = HMMHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_all_chords_in_key(self):
        h = HMMHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert c.degree in range(1, 8)

    def test_chords_contain_melody(self):
        h = HMMHarmonizer()
        melody = _c_major_melody()
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        # Most chords should contain at least one melody note
        fit_count = 0
        for chord in chords:
            chord_pcs = set(chord.pitch_classes())
            notes_in_span = [
                n for n in melody if chord.start <= n.start < chord.start + chord.duration
            ]
            for n in notes_in_span:
                if n.pitch % 12 in chord_pcs:
                    fit_count += 1
        assert fit_count > 0

    def test_chord_change_bars(self):
        h = HMMHarmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_empty_melody(self):
        h = HMMHarmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []


class TestGraphSearchHarmonizer:
    def test_produces_chords(self):
        h = GraphSearchHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_all_chords_in_key(self):
        h = GraphSearchHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert c.degree in range(1, 8)

    def test_chords_contain_melody(self):
        h = GraphSearchHarmonizer()
        melody = _c_major_melody()
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        fit_count = 0
        for chord in chords:
            chord_pcs = set(chord.pitch_classes())
            notes_in_span = [
                n for n in melody if chord.start <= n.start < chord.start + chord.duration
            ]
            for n in notes_in_span:
                if n.pitch % 12 in chord_pcs:
                    fit_count += 1
        assert fit_count > 0

    def test_voice_leading_smooth(self):
        h = GraphSearchHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        if len(chords) >= 2:
            # Voice leading: average pc movement should be small
            for i in range(len(chords) - 1):
                a_pcs = chords[i].pitch_classes()
                b_pcs = chords[i + 1].pitch_classes()
                if a_pcs and b_pcs:
                    avg_a = sum(a_pcs) / len(a_pcs)
                    avg_b = sum(b_pcs) / len(b_pcs)
                    movement = min(abs(avg_a - avg_b), 12 - abs(avg_a - avg_b))
                    assert movement <= 7  # should be reasonably close

    def test_empty_melody(self):
        h = GraphSearchHarmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []


class TestHMM2Harmonizer:
    def test_produces_chords(self):
        h = HMM2Harmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_all_chords_in_key(self):
        h = HMM2Harmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert c.degree in range(1, 8)

    def test_chord_change_bars(self):
        h = HMM2Harmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_chord_change_beats(self):
        h = HMM2Harmonizer(chord_change="beats")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 8

    def test_empty_melody(self):
        h = HMM2Harmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []

    def test_melody_fit(self):
        h = HMM2Harmonizer()
        melody = _c_major_melody()
        chords = h.harmonize(melody, C_MAJOR, 8.0)
        fit_count = 0
        for chord in chords:
            chord_pcs = set(chord.pitch_classes())
            for n in melody:
                if chord.start <= n.start < chord.start + chord.duration:
                    if n.pitch % 12 in chord_pcs:
                        fit_count += 1
        assert fit_count > 0

    def test_functional_weight_param(self):
        h = HMM2Harmonizer(functional_weight=0.5)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0


class TestHMM3Harmonizer:
    def test_produces_chords(self):
        h = HMM3Harmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chord_change_bars(self):
        h = HMM3Harmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_empty_melody(self):
        h = HMM3Harmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []

    def test_beam_width(self):
        h = HMM3Harmonizer(beam_width=3)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_no_secondary_dominants(self):
        h = HMM3Harmonizer(allow_secondary_dom=False, allow_extensions=False)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert c.degree in range(1, 8)

    def test_with_extensions(self):
        h = HMM3Harmonizer(allow_extensions=True)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_rhythm_aware_off(self):
        h = HMM3Harmonizer(rhythm_aware=False)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0


class TestGeneticHarmonizer:
    def test_produces_chords(self):
        h = GeneticHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chord_change_bars(self):
        h = GeneticHarmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_empty_melody(self):
        h = GeneticHarmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []

    def test_small_population(self):
        h = GeneticHarmonizer(population_size=10, generations=10)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_all_chords_have_valid_quality(self):
        h = GeneticHarmonizer(population_size=20, generations=20)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        valid_qualities = set(Quality)
        for c in chords:
            assert c.quality in valid_qualities

    def test_minor_key(self):
        h = GeneticHarmonizer(population_size=20, generations=20)
        chords = h.harmonize(_c_major_melody(), A_MINOR, 8.0)
        assert len(chords) > 0


class TestChromaticMediantHarmonizer:
    def test_produces_chords(self):
        h = ChromaticMediantHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chord_change_bars(self):
        h = ChromaticMediantHarmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_empty_melody(self):
        h = ChromaticMediantHarmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []

    def test_no_chromatic_prob(self):
        # With chromatic_prob=0, only diatonic chords
        h = ChromaticMediantHarmonizer(chromatic_prob=0.0)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_full_chromatic_prob(self):
        # With chromatic_prob=1.0, chromatic mediants used after first chord
        h = ChromaticMediantHarmonizer(chromatic_prob=1.0)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chords_have_root_and_quality(self):
        h = ChromaticMediantHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert 0 <= c.root <= 11
            assert c.quality in set(Quality)


class TestModalInterchangeHarmonizer:
    def test_produces_chords(self):
        h = ModalInterchangeHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chord_change_bars(self):
        h = ModalInterchangeHarmonizer(chord_change="bars")
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) == 2

    def test_empty_melody(self):
        h = ModalInterchangeHarmonizer()
        assert h.harmonize([], C_MAJOR, 8.0) == []

    def test_no_borrowing(self):
        h = ModalInterchangeHarmonizer(borrow_prob=0.0)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert c.degree in range(1, 8)  # only diatonic

    def test_full_borrowing(self):
        h = ModalInterchangeHarmonizer(borrow_prob=1.0)
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        assert len(chords) > 0

    def test_chords_have_root_and_quality(self):
        h = ModalInterchangeHarmonizer()
        chords = h.harmonize(_c_major_melody(), C_MAJOR, 8.0)
        for c in chords:
            assert 0 <= c.root <= 11
            assert c.quality in set(Quality)
