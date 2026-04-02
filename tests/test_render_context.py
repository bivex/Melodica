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

"""Tests for RenderContext cross-phrase state."""

from melodica.render_context import RenderContext
from melodica.types import ChordLabel, Quality


class TestRenderContext:
    def test_defaults(self):
        ctx = RenderContext()
        assert ctx.prev_pitch is None
        assert ctx.prev_velocity is None
        assert ctx.phrase_position == 0.0
        assert ctx.prev_chord is None
        assert ctx.prev_pitches == []

    def test_with_end_state_returns_new(self):
        ctx = RenderContext(phrase_position=0.5)
        new = ctx.with_end_state(last_pitch=72, last_velocity=100)
        assert new.prev_pitch == 72
        assert new.prev_velocity == 100
        assert new.phrase_position == 0.5  # preserved
        # Original unchanged
        assert ctx.prev_pitch is None

    def test_with_end_state_preserves_existing(self):
        ctx = RenderContext(prev_pitch=60, prev_velocity=80)
        new = ctx.with_end_state(last_velocity=90)
        assert new.prev_pitch == 60  # preserved
        assert new.prev_velocity == 90  # updated

    def test_passing_to_generator(self):
        """Verify context can be passed to any generator without error."""
        from melodica.generators import MelodyGenerator, BassGenerator, ArpeggiatorGenerator
        from melodica.generators import GeneratorParams
        from melodica.types import Scale
        from melodica.theory import Mode

        key = Scale(root=0, mode=Mode.MAJOR)
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        ctx = RenderContext(prev_pitch=72, prev_velocity=80, phrase_position=0.3)

        for Gen in [MelodyGenerator, BassGenerator, ArpeggiatorGenerator]:
            gen = Gen(GeneratorParams())
            notes = gen.render(chords, key, 4.0, context=ctx)
            assert isinstance(notes, list)

    def test_context_none_default(self):
        """Calling render with no context works as before."""
        from melodica.generators import MelodyGenerator, GeneratorParams
        from melodica.types import Scale, ChordLabel, Quality
        from melodica.theory import Mode

        key = Scale(root=0, mode=Mode.MAJOR)
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        gen = MelodyGenerator(GeneratorParams())
        notes = gen.render(chords, key, 4.0)
        assert isinstance(notes, list)
        assert len(notes) > 0
