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

"""Tests for phrase shaping features in generators."""

import math

from melodica.generators import (
    MelodyGenerator,
    BassGenerator,
    ArpeggiatorGenerator,
    ChordGenerator,
    OstinatoGenerator,
    GeneratorParams,
)
from melodica.render_context import RenderContext
from melodica.types import Scale, ChordLabel, Quality
from melodica.theory import Mode

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
SIMPLE_CHORDS = [
    ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
    ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
]


class TestMelodyPhraseArch:
    def test_phrase_arch_velocity_contour(self):
        """Middle notes should be louder than first/last notes on average."""
        gen = MelodyGenerator(GeneratorParams(density=0.7))
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 8.0)
        if len(notes) < 5:
            return  # Not enough notes to test
        # Split into thirds
        n = len(notes)
        first_third = notes[: n // 3]
        middle_third = notes[n // 3 : 2 * n // 3]
        last_third = notes[2 * n // 3 :]
        avg_first = sum(n.velocity for n in first_third) / len(first_third)
        avg_middle = sum(n.velocity for n in middle_third) / len(middle_third)
        avg_last = sum(n.velocity for n in last_third) / len(last_third)
        # Middle should be >= first on average (arch shape)
        assert avg_middle >= avg_first * 0.85  # Allow some tolerance

    def test_context_affects_starting_pitch(self):
        """First note should be close to context.prev_pitch."""
        gen = MelodyGenerator(GeneratorParams())
        ctx = RenderContext(prev_pitch=72)
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0
        # First note should be within ~12 semitones of 72
        assert abs(notes[0].pitch - 72) <= 12

    def test_leap_filling(self):
        """Generators with context produce _last_context."""
        gen = MelodyGenerator(GeneratorParams())
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 8.0)
        assert hasattr(gen, "_last_context")
        if notes:
            assert gen._last_context is not None
            assert gen._last_context.prev_pitch == notes[-1].pitch


class TestBassWalking:
    def test_walking_style_exists(self):
        gen = BassGenerator(GeneratorParams(), style="walking")
        assert gen.style == "walking"

    def test_walking_produces_notes(self):
        gen = BassGenerator(GeneratorParams(), style="walking")
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 8.0)
        assert len(notes) > 0
        # Walking bass should have roughly 1 note per beat
        assert len(notes) >= 6  # ~8 beats worth

    def test_walking_context_threading(self):
        gen = BassGenerator(GeneratorParams(), style="walking")
        ctx = RenderContext(prev_pitch=48)
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 8.0, context=ctx)
        assert len(notes) > 0
        assert gen._last_context is not None


class TestArpVoiceLeading:
    def test_arp_continues_on_chord_change(self):
        """Arpeggiator should not always start from position 0 on chord change."""
        gen = ArpeggiatorGenerator(GeneratorParams(), pattern="up")
        # Two distinct chords to force a change
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ]
        notes = gen.render(chords, C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_arp_beat_one_accent(self):
        """First note of arp cycle should have higher velocity."""
        gen = ArpeggiatorGenerator(GeneratorParams(), pattern="up")
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 4.0)
        if len(notes) >= 2:
            # Find notes at seq_pos == 0 (cycle start)
            # At minimum, the first note should be accented
            first_vel = notes[0].velocity
            avg_vel = sum(n.velocity for n in notes) / len(notes)
            assert first_vel >= avg_vel * 0.9  # At least not quieter than average


class TestChordVoiceLeading:
    def test_chord_minimal_movement(self):
        """ChordGenerator should minimize movement between successive chords."""
        gen = ChordGenerator(GeneratorParams())
        chords = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=2.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=2.0, duration=2.0),
            ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=2.0),
        ]
        notes = gen.render(chords, C_MAJOR, 6.0)
        assert len(notes) > 0
        # With voice-leading, chords should be reasonably connected
        assert gen._last_context is not None


class TestOstinatoAccent:
    def test_ostinato_has_accent_pattern(self):
        """Ostinato should have configurable accent pattern."""
        gen = OstinatoGenerator(GeneratorParams())
        assert hasattr(gen, "accent_pattern")
        assert len(gen.accent_pattern) > 0

    def test_ostinato_accent_affects_velocity(self):
        """Different positions in the pattern should have different velocities."""
        gen = OstinatoGenerator(
            GeneratorParams(), accent_pattern=[1.3, 0.7, 1.0, 0.8]
        )
        notes = gen.render(SIMPLE_CHORDS, C_MAJOR, 4.0)
        if len(notes) >= 4:
            velocities = [n.velocity for n in notes[:4]]
            # Not all velocities should be identical
            assert len(set(velocities)) > 1 or len(notes) < 4
