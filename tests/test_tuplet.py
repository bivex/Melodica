# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.rhythm import Tuplet, TRIPLET


class TestTuplet:
    def test_triplet_ratio(self):
        t = Tuplet(3, 2, 1.0)
        assert abs(t.ratio - 2.0 / 3.0) < 1e-6

    def test_triplet_subdivide_count(self):
        t = Tuplet(3, 2, 1.0)
        slots = t.subdivide()
        assert len(slots) == 3

    def test_triplet_subdivide_duration(self):
        t = Tuplet(3, 2, 1.0)
        slots = t.subdivide()
        assert all(abs(s - 2.0 / 3.0) < 1e-6 for s in slots)

    def test_triplet_total_duration(self):
        t = Tuplet(3, 2, 1.0)
        total = sum(t.subdivide())
        assert abs(total - 2.0) < 1e-6

    def test_quintuplet(self):
        t = Tuplet(5, 4, 1.0)
        assert len(t.subdivide()) == 5
        assert abs(sum(t.subdivide()) - 4.0) < 1e-6

    def test_sextuplet(self):
        t = Tuplet(6, 4, 1.0)
        assert len(t.subdivide()) == 6
        assert abs(sum(t.subdivide()) - 4.0) < 1e-6

    def test_half_note_unit(self):
        t = Tuplet(3, 2, 2.0)
        slots = t.subdivide()
        assert abs(sum(slots) - 4.0) < 1e-6

    def test_eighth_note_unit(self):
        t = Tuplet(3, 2, 0.5)
        slots = t.subdivide()
        assert abs(sum(slots) - 1.0) < 1e-6

    def test_frozen(self):
        t = Tuplet(3, 2)
        with pytest.raises(AttributeError):
            t.count = 4

    def test_defaults(self):
        t = Tuplet()
        assert t.count == 3
        assert t.in_place_of == 2
        assert t.unit == 1.0


class TestTripletConstant:
    def test_exists(self):
        assert TRIPLET.count == 3
        assert TRIPLET.in_place_of == 2

    def test_subdivide_produces_three_equal_slots(self):
        slots = TRIPLET.subdivide()
        assert len(slots) == 3
        assert all(abs(s - slots[0]) < 1e-10 for s in slots)
