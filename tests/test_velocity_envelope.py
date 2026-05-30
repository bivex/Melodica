"""Tests for melodica.composer.velocity_envelope.VelocityEnvelope"""

import pytest

from melodica.types_pkg._notes import NoteInfo
from melodica.composer.velocity_envelope import VelocityEnvelope


def _make_notes(velocities: list[int] | None = None) -> list[NoteInfo]:
    vels = velocities or [80, 80, 80]
    return [
        NoteInfo(pitch=60 + i, start=float(i), duration=1.0, velocity=v)
        for i, v in enumerate(vels)
    ]


class TestAddPointAndVelocityAt:
    def test_two_points_interpolation(self):
        env = VelocityEnvelope()
        env.add_point(0.0, 40.0).add_point(4.0, 100.0)
        assert env.velocity_at(0.0) == pytest.approx(40.0)
        assert env.velocity_at(2.0) == pytest.approx(70.0)
        assert env.velocity_at(4.0) == pytest.approx(100.0)

    def test_before_first_point(self):
        env = VelocityEnvelope()
        env.add_point(2.0, 60.0)
        assert env.velocity_at(0.0) == pytest.approx(60.0)

    def test_after_last_point(self):
        env = VelocityEnvelope()
        env.add_point(0.0, 60.0)
        assert env.velocity_at(100.0) == pytest.approx(60.0)

    def test_empty_envelope(self):
        env = VelocityEnvelope()
        assert env.velocity_at(5.0) == pytest.approx(80.0)


class TestCrescendo:
    def test_rising_velocity(self):
        env = VelocityEnvelope()
        env.crescendo(0.0, 4.0, 30.0, 100.0, steps=4)
        assert env.velocity_at(0.0) == pytest.approx(30.0)
        assert env.velocity_at(4.0) == pytest.approx(100.0)
        mid = env.velocity_at(2.0)
        assert 30.0 < mid < 100.0


class TestDiminuendo:
    def test_falling_velocity(self):
        env = VelocityEnvelope()
        env.diminuendo(0.0, 4.0, 100.0, 30.0, steps=4)
        assert env.velocity_at(0.0) == pytest.approx(100.0)
        assert env.velocity_at(4.0) == pytest.approx(30.0)


class TestSwell:
    def test_crescendo_then_diminuendo(self):
        env = VelocityEnvelope()
        env.swell(peak_beat=4.0, start_vel=30.0, peak_vel=110.0, end_vel=40.0,
                  start_beat=0.0, end_beat=8.0)
        assert env.velocity_at(0.0) == pytest.approx(30.0)
        assert env.velocity_at(4.0) == pytest.approx(110.0)
        assert env.velocity_at(8.0) == pytest.approx(40.0)


class TestSubito:
    def test_instant_change(self):
        env = VelocityEnvelope()
        env.subito(4.0, 30.0)
        # After beat 4, velocity should be 30
        assert env.velocity_at(4.0) == pytest.approx(30.0)
        assert env.velocity_at(10.0) == pytest.approx(30.0)


class TestTerrace:
    def test_terrace_dynamics(self):
        env = VelocityEnvelope()
        env.terrace([(0.0, 40.0), (4.0, 80.0), (8.0, 60.0)])
        # At beat 2, interpolates linearly between (0,40) and (4,80) → 60
        assert env.velocity_at(2.0) == pytest.approx(60.0)
        # At beat 6, interpolates between (4,80) and (8,60) → 70
        assert env.velocity_at(6.0) == pytest.approx(70.0)
        # Exact points
        assert env.velocity_at(0.0) == pytest.approx(40.0)
        assert env.velocity_at(4.0) == pytest.approx(80.0)


class TestApply:
    def test_scales_velocity(self):
        env = VelocityEnvelope()
        env.add_point(0.0, 40.0).add_point(4.0, 120.0)
        notes = _make_notes()
        result = env.apply(notes)
        # Note at beat 0: env_vel=40, scale=0.5, vel=round(80*0.5)=40
        assert result[0].velocity == 40
        # Note at beat 1: env_vel=60, scale=0.75, vel=round(80*0.75)=60
        assert result[1].velocity == 60
        # Note at beat 2: env_vel=80, scale=1.0, vel=80
        assert result[2].velocity == 80

    def test_clamp_range(self):
        env = VelocityEnvelope()
        env.add_point(0.0, 200.0)
        notes = _make_notes([127])
        result = env.apply(notes)
        assert result[0].velocity <= 127
        assert result[0].velocity >= 1

    def test_returns_new_notes(self):
        env = VelocityEnvelope()
        env.add_point(0.0, 40.0)
        notes = _make_notes()
        result = env.apply(notes)
        assert result is not notes
        assert result[0] is not notes[0]

    def test_empty_envelope_preserves(self):
        env = VelocityEnvelope()
        notes = _make_notes([64, 64, 64])
        result = env.apply(notes)
        assert [n.velocity for n in result] == [64, 64, 64]
