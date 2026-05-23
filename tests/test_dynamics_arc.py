# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode
from melodica.form import MusicalForm
from melodica.dynamics_arc import DynamicsArc, DYNAMICS_MAP

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_dynamics_arc_interpolation():
    points = [(0.0, 0.2), (10.0, 0.8)]
    arc = DynamicsArc(curve_type="custom", control_points=points)
    
    # Boundary tests
    assert arc.velocity_at(-1.0) == 0.2
    assert arc.velocity_at(0.0) == 0.2
    assert arc.velocity_at(10.0) == 0.8
    assert arc.velocity_at(15.0) == 0.8
    
    # Midpoint interpolation
    assert abs(arc.velocity_at(5.0) - 0.5) < 0.01
    assert abs(arc.velocity_at(2.5) - 0.35) < 0.01


def test_dynamics_arc_from_form():
    form = MusicalForm.ternary(C_MAJOR, 100.0)
    arc = DynamicsArc.from_form(form)
    
    # First section (A) is "mf" (0.7)
    assert abs(arc.velocity_at(0.0) - 0.7) < 0.01
    assert abs(arc.velocity_at(20.0) - 0.7) < 0.01
    
    # Second section (B) starts at 40.0 with "p" (0.4)
    # The transition occurs between 40.0 and 40.0 + min(4.0, 30*0.2) = 44.0.
    # At 40.0, the value should be 0.7
    assert abs(arc.velocity_at(40.0) - 0.7) < 0.01
    # At 44.0, the value should be 0.4
    assert abs(arc.velocity_at(44.0) - 0.4) < 0.01
    # Between 40.0 and 44.0, it should smoothly interpolate: e.g. at 42.0 it is 0.55
    assert abs(arc.velocity_at(42.0) - 0.55) < 0.01
