# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

from melodica.generators._melody_rhythm import GrooveProfile, METER_STRENGTHS


class TestGrooveProfileMeter:
    def test_default_is_four_four(self):
        g = GrooveProfile()
        assert g.beats_per_bar == 4
        assert g.denominator == 4

    def test_four_four_strengths(self):
        g = GrooveProfile()
        assert g.beat_strength(0.0) == 1.0
        assert g.beat_strength(1.0) == 0.7
        assert g.beat_strength(2.0) == 0.9
        assert g.beat_strength(3.0) == 0.6

    def test_three_four_strengths(self):
        g = GrooveProfile(beats_per_bar=3, denominator=4)
        assert g.beat_strength(0.0) == 1.0
        assert g.beat_strength(1.0) == 0.6
        assert g.beat_strength(2.0) == 0.8

    def test_six_eight_strengths(self):
        g = GrooveProfile(beats_per_bar=6, denominator=8)
        assert g.beat_strength(0.0) == 1.0
        assert abs(g.beat_strength(1.5) - 0.85) < 0.01
        assert g.beat_strength(3.0) == 0.9

    def test_five_four_strengths(self):
        g = GrooveProfile(beats_per_bar=5, denominator=4)
        assert g.beat_strength(0.0) == 1.0
        assert g.beat_strength(4.0) == 0.75

    def test_seven_eight_strengths(self):
        g = GrooveProfile(beats_per_bar=7, denominator=8)
        assert g.beat_strength(0.0) == 1.0
        assert abs(g.beat_strength(1.5) - 0.75) < 0.01

    def test_offbeat_strength(self):
        g = GrooveProfile()
        s = g.beat_strength(0.5)
        assert 0.3 < s < 0.5

    def test_sixteenth_strength(self):
        g = GrooveProfile()
        s = g.beat_strength(0.25)
        assert 0.1 < s < 0.3

    def test_wraps_across_bars(self):
        g = GrooveProfile(beats_per_bar=3, denominator=4)
        # 3.0 is the start of bar 2 → should be beat 1 of next bar
        assert g.beat_strength(3.0) == 1.0
        assert g.beat_strength(4.0) == 0.6

    def test_custom_strengths(self):
        g = GrooveProfile(strengths={0.0: 0.95, 1.0: 0.50})
        assert g.beat_strength(0.0) == 0.95
        assert g.beat_strength(1.0) == 0.50

    def test_unknown_meter_falls_back_to_four_four(self):
        g = GrooveProfile(beats_per_bar=11, denominator=16)
        # Should fall back to 4/4 strengths
        assert g.beat_strength(0.0) == 1.0


class TestMeterStrengthsTable:
    def test_has_common_meters(self):
        assert (4, 4) in METER_STRENGTHS
        assert (3, 4) in METER_STRENGTHS
        assert (6, 8) in METER_STRENGTHS

    def test_five_entries(self):
        assert len(METER_STRENGTHS) == 5

    def test_strengths_are_normalized(self):
        for meter, strengths in METER_STRENGTHS.items():
            for pos, s in strengths.items():
                assert 0.0 <= s <= 1.0, f"{meter} pos {pos}: {s}"
