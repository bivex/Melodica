# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-08-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""
generators/decorators.py — Decorators & Middleware for PhraseGenerator.

Layer: Application / Domain

Provides composable generator decorators implementing cross-cutting concerns:
- PitchConstrainedGenerator: Tessitura / pitch range bounding (octave shifting or clamping)
- HumanizedGenerator: Dynamic micro-timing and velocity variation
- CachedGenerator: In-memory cache for deterministic or heavy generators
- PipelineGenerator: Chained execution of ModifierPipeline after generation
"""

from __future__ import annotations

import dataclasses
import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from melodica.generators import GeneratorParams, PhraseGenerator
from melodica.render_context import RenderContext
from melodica.types import ChordLabel, NoteInfo, Scale

if TYPE_CHECKING:
    from melodica.modifiers import ModifierContext, ModifierPipeline, PhraseModifier


@dataclass
class PitchConstrainedGenerator(PhraseGenerator):
    """
    Decorator that constrains all generated note pitches to a target range [min_pitch, max_pitch].
    Uses octave transposition where possible to preserve pitch classes.
    """

    name: str = "Pitch Constrained Generator"
    wrapped_generator: PhraseGenerator | None = None
    min_pitch: int = 36  # C2
    max_pitch: int = 84  # C6
    mode: str = "octave_fold"  # "octave_fold" or "clamp"

    def __init__(
        self,
        wrapped_generator: PhraseGenerator | None = None,
        *,
        min_pitch: int = 36,
        max_pitch: int = 84,
        mode: str = "octave_fold",
        params: GeneratorParams | None = None,
    ) -> None:
        super().__init__(params)
        self.wrapped_generator = wrapped_generator
        self.min_pitch = min_pitch
        self.max_pitch = max_pitch
        self.mode = mode

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if self.wrapped_generator is None:
            return []

        notes = self.wrapped_generator.render(chords, key, duration_beats, context)
        constrained: list[NoteInfo] = []

        for n in notes:
            pitch = n.pitch
            if self.mode == "octave_fold":
                while pitch < self.min_pitch:
                    pitch += 12
                while pitch > self.max_pitch:
                    pitch -= 12
            else:
                pitch = max(self.min_pitch, min(self.max_pitch, pitch))

            new_n = dataclasses.replace(n, pitch=pitch)
            new_n.expression = dict(n.expression)
            constrained.append(new_n)

        return constrained


@dataclass
class HumanizedGenerator(PhraseGenerator):
    """
    Decorator that applies micro-timing offsets and subtle velocity variations
    to the wrapped generator's output.
    """

    name: str = "Humanized Generator"
    wrapped_generator: PhraseGenerator | None = None
    timing_jitter_beats: float = 0.015
    velocity_jitter: int = 6

    def __init__(
        self,
        wrapped_generator: PhraseGenerator | None = None,
        *,
        timing_jitter_beats: float = 0.015,
        velocity_jitter: int = 6,
        params: GeneratorParams | None = None,
    ) -> None:
        super().__init__(params)
        self.wrapped_generator = wrapped_generator
        self.timing_jitter_beats = timing_jitter_beats
        self.velocity_jitter = velocity_jitter

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if self.wrapped_generator is None:
            return []

        notes = self.wrapped_generator.render(chords, key, duration_beats, context)
        humanized: list[NoteInfo] = []

        for n in notes:
            t_offset = random.uniform(-self.timing_jitter_beats, self.timing_jitter_beats)
            v_offset = random.randint(-self.velocity_jitter, self.velocity_jitter)

            new_start = max(0.0, round(n.start + t_offset, 6))
            new_vel = max(1, min(127, n.velocity + v_offset))

            new_n = dataclasses.replace(n, start=new_start, velocity=new_vel)
            new_n.expression = dict(n.expression)
            humanized.append(new_n)

        humanized.sort(key=lambda n: (n.start, n.pitch))
        return humanized


@dataclass
class CachedGenerator(PhraseGenerator):
    """
    Decorator that caches the rendered notes of the wrapped generator in memory
    keyed by chord sequence, scale, and duration.
    """

    name: str = "Cached Generator"
    wrapped_generator: PhraseGenerator | None = None
    _cache: dict[tuple, list[NoteInfo]] = field(default_factory=dict, init=False, repr=False)

    def __init__(
        self,
        wrapped_generator: PhraseGenerator | None = None,
        params: GeneratorParams | None = None,
    ) -> None:
        super().__init__(params)
        self.wrapped_generator = wrapped_generator
        self._cache = {}

    def clear_cache(self) -> None:
        self._cache.clear()

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if self.wrapped_generator is None:
            return []

        chord_key = tuple((c.root, c.quality, c.start, c.duration) for c in chords)
        cache_key = (chord_key, key.root, str(key.mode), duration_beats)

        if cache_key in self._cache:
            # Return fresh clones to prevent callers mutating cache
            return [dataclasses.replace(n, expression=dict(n.expression)) for n in self._cache[cache_key]]

        result = self.wrapped_generator.render(chords, key, duration_beats, context)
        self._cache[cache_key] = [dataclasses.replace(n, expression=dict(n.expression)) for n in result]
        return result


@dataclass
class PipelineGenerator(PhraseGenerator):
    """
    Decorator that executes a modifier pipeline or list of PhraseModifiers
    over the rendered output of the wrapped generator.
    """

    name: str = "Pipeline Generator"
    wrapped_generator: PhraseGenerator | None = None
    modifiers: list[PhraseModifier] = field(default_factory=list)

    def __init__(
        self,
        wrapped_generator: PhraseGenerator | None = None,
        modifiers: list[PhraseModifier] | None = None,
        params: GeneratorParams | None = None,
    ) -> None:
        super().__init__(params)
        self.wrapped_generator = wrapped_generator
        self.modifiers = list(modifiers) if modifiers is not None else []

    def render(
        self,
        chords: list[ChordLabel],
        key: Scale,
        duration_beats: float,
        context: RenderContext | None = None,
    ) -> list[NoteInfo]:
        if self.wrapped_generator is None:
            return []

        notes = self.wrapped_generator.render(chords, key, duration_beats, context)
        if not self.modifiers:
            return notes

        from melodica.modifiers import ModifierContext, ModifierPipeline

        # Build pipeline and process
        pipeline = ModifierPipeline(base_notes=notes, modifiers=self.modifiers)
        timeline = context.timeline if context and hasattr(context, "timeline") and context.timeline is not None else None
        
        if timeline is None:
            from melodica.types import MusicTimeline
            timeline = MusicTimeline(chords=chords)

        mod_ctx = ModifierContext(
            duration_beats=duration_beats,
            chords=chords,
            timeline=timeline,
            scale=key,
        )

        return pipeline.process(mod_ctx)
