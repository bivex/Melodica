# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
tests/test_architectural_improvements.py — Verification of architectural enhancements.

Tests:
- Fluent RhythmBuilder API
- PhraseModifier implementations for melody processors (Ornament, FillLeaps, VelocityContour)
- ModifierPipeline composition with melody modifiers
- PhraseGenerator Decorator family (PitchConstrained, Humanized, Cached, Pipeline)
- HarmonizationEngine IntEnum & HarmonizationRequest validation
"""

from __future__ import annotations

import pytest

from melodica.generators import (
    CachedGenerator,
    ChordGenerator,
    GeneratorParams,
    HumanizedGenerator,
    MelodyGenerator,
    PipelineGenerator,
    PitchConstrainedGenerator,
)
from melodica.generators._melody_rhythm import GrooveProfile, RhythmBuilder
from melodica.modifiers import (
    FillLeapsModifier,
    ModifierContext,
    ModifierPipeline,
    OrnamentModifier,
    VelocityContourModifier,
)
from melodica.types import (
    ChordLabel,
    HarmonizationEngine,
    HarmonizationRequest,
    MusicTimeline,
    Note,
    NoteInfo,
    Quality,
    Scale,
)

C_MAJOR = Scale(0, "major")
SAMPLE_CHORDS = [
    ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=2.0),
    ChordLabel(root=5, quality=Quality.MINOR, start=2.0, duration=2.0),
]


class TestFluentRhythmBuilder:
    def test_fluent_chaining_produces_events(self):
        builder = (
            RhythmBuilder()
            .with_phrase_length(4.0)
            .with_density(0.7)
            .with_syncopation(0.3)
            .with_rhythm_variety(0.2)
            .with_groove(GrooveProfile(beats_per_bar=4, denominator=4))
        )
        events = builder.build(4.0)
        assert len(events) > 0
        assert all(0.0 <= e.onset < 4.0 for e in events)

    def test_with_motif(self):
        builder = RhythmBuilder().with_rhythm_motif([1.0, 0.5, 0.5, 2.0])
        events = builder.build(8.0)
        assert len(events) >= 4


class TestMelodyModifiersAndPipeline:
    def test_ornament_modifier(self):
        mod = OrnamentModifier(ornament_probability=1.0, low_pitch=48, high_pitch=84)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=90),
            NoteInfo(pitch=64, start=2.0, duration=1.0, velocity=90),
        ]
        ctx = ModifierContext(
            duration_beats=4.0,
            chords=SAMPLE_CHORDS,
            timeline=MusicTimeline(chords=SAMPLE_CHORDS),
            scale=C_MAJOR,
        )
        modified = mod.modify(notes, ctx)
        # Should add at least one grace note
        assert len(modified) > len(notes)
        assert any(n.duration < 0.1 for n in modified)

    def test_fill_leaps_modifier(self):
        mod = FillLeapsModifier(min_leap_semitones=4)
        # Leap of 7 semitones (C4 to G4)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=80),
        ]
        ctx = ModifierContext(
            duration_beats=4.0,
            chords=SAMPLE_CHORDS,
            timeline=MusicTimeline(chords=SAMPLE_CHORDS),
            scale=C_MAJOR,
        )
        modified = mod.modify(notes, ctx)
        assert len(modified) > 2
        # Intermediate pitch should be between 60 and 67
        pitches = [n.pitch for n in modified]
        assert any(60 < p < 67 for p in pitches)

    def test_velocity_contour_modifier(self):
        mod = VelocityContourModifier(contour="crescendo", phrase_length=4.0)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=60),
            NoteInfo(pitch=62, start=1.5, duration=0.5, velocity=60),
            NoteInfo(pitch=64, start=3.5, duration=0.5, velocity=60),
        ]
        ctx = ModifierContext(
            duration_beats=4.0,
            chords=SAMPLE_CHORDS,
            timeline=MusicTimeline(chords=SAMPLE_CHORDS),
            scale=C_MAJOR,
        )
        modified = mod.modify(notes, ctx)
        # Last note near end of crescendo should have higher velocity than first note (accounting for downbeat accent)
        assert modified[-1].velocity > 60

    def test_modifier_pipeline_integration(self):
        base_notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=70),
            NoteInfo(pitch=72, start=2.0, duration=1.0, velocity=70),
        ]
        pipeline = ModifierPipeline(base_notes=base_notes)
        pipeline.add_modifier(FillLeapsModifier(min_leap_semitones=5))
        pipeline.add_modifier(VelocityContourModifier(contour="arch"))

        ctx = ModifierContext(
            duration_beats=4.0,
            chords=SAMPLE_CHORDS,
            timeline=MusicTimeline(chords=SAMPLE_CHORDS),
            scale=C_MAJOR,
        )
        result = pipeline.process(ctx)
        assert len(result) > 2
        # Base notes must remain intact (non-destructive)
        assert len(pipeline.base_notes) == 2


class TestGeneratorDecorators:
    def test_pitch_constrained_generator(self):
        base_gen = ChordGenerator()
        constrained = PitchConstrainedGenerator(base_gen, min_pitch=60, max_pitch=72, mode="octave_fold")
        notes = constrained.render(SAMPLE_CHORDS, C_MAJOR, 4.0)
        assert len(notes) > 0
        assert all(60 <= n.pitch <= 72 for n in notes)

    def test_humanized_generator(self):
        base_gen = ChordGenerator()
        humanized = HumanizedGenerator(base_gen, timing_jitter_beats=0.02, velocity_jitter=5)
        notes = humanized.render(SAMPLE_CHORDS, C_MAJOR, 4.0)
        assert len(notes) > 0
        assert all(n.start >= 0.0 for n in notes)

    def test_cached_generator(self):
        base_gen = ChordGenerator()
        cached = CachedGenerator(base_gen)
        res1 = cached.render(SAMPLE_CHORDS, C_MAJOR, 4.0)
        res2 = cached.render(SAMPLE_CHORDS, C_MAJOR, 4.0)
        assert len(res1) == len(res2)
        assert [(n.pitch, n.start) for n in res1] == [(n.pitch, n.start) for n in res2]
        cached.clear_cache()
        assert len(cached._cache) == 0

    def test_pipeline_generator(self):
        base_gen = ChordGenerator()
        piped = PipelineGenerator(
            base_gen,
            modifiers=[VelocityContourModifier(contour="crescendo")],
        )
        notes = piped.render(SAMPLE_CHORDS, C_MAJOR, 4.0)
        assert len(notes) > 0


class TestHarmonizationEngineEnum:
    def test_enum_members_and_resolution(self):
        assert HarmonizationEngine.FUNCTIONAL == 0
        assert HarmonizationEngine.RULE_BASED == 1
        assert HarmonizationEngine.ADAPTIVE == 2
        assert HarmonizationEngine.HMM == 3
        assert HarmonizationEngine.COUPLED_HMM == 4

        assert HarmonizationEngine.from_value("coupled_hmm") == HarmonizationEngine.COUPLED_HMM
        assert HarmonizationEngine.from_value("adaptive") == HarmonizationEngine.ADAPTIVE
        assert HarmonizationEngine.from_value(0) == HarmonizationEngine.FUNCTIONAL

    def test_harmonization_request_with_enum(self):
        melody = [Note(pitch=60, start=0.0, duration=1.0), Note(pitch=62, start=1.0, duration=1.0)]
        req = HarmonizationRequest(
            melody=melody,
            key=C_MAJOR,
            engine=HarmonizationEngine.COUPLED_HMM,
        )
        assert req.engine == HarmonizationEngine.COUPLED_HMM
        assert HarmonizationEngine.from_value(req.engine) == HarmonizationEngine.COUPLED_HMM

    def test_invalid_engine_raises(self):
        melody = [Note(pitch=60, start=0.0, duration=1.0)]
        with pytest.raises(ValueError):
            HarmonizationRequest(melody=melody, key=C_MAJOR, engine="non_existent_engine")
        with pytest.raises(ValueError):
            HarmonizationRequest(melody=melody, key=C_MAJOR, engine=99)


class TestDSPPipelineAndAudioEffects:
    def test_dsp_pipeline_chaining_and_bypass(self):
        import numpy as np
        from melodica.dsp_effects import DSPPipeline, HardClipper, AutoPumper, ParallelDSP

        # Create dummy stereo audio (2 channels, 1000 samples)
        audio = np.random.uniform(-0.8, 0.8, (2, 1000)).astype(np.float32)

        pipe = (
            DSPPipeline()
            .add(HardClipper(threshold_db=-6.0, makeup_db=2.0), dry_wet=0.8)
            .add(AutoPumper(bpm=120.0, depth=0.5))
        )
        out = pipe.process(audio)
        assert out.shape == audio.shape
        assert not np.array_equal(out, audio)

        # Bypass first effect
        pipe.set_bypass(0, True)
        out_bypassed = pipe.process(audio)
        assert out_bypassed.shape == audio.shape

    def test_parallel_dsp(self):
        import numpy as np
        from melodica.dsp_effects import ParallelDSP, HardClipper

        audio = np.random.uniform(-0.5, 0.5, (2, 500)).astype(np.float32)
        parallel = (
            ParallelDSP()
            .add_branch(HardClipper(threshold_db=-3.0), mix=0.7)
            .add_branch(HardClipper(threshold_db=-10.0), mix=0.3)
        )
        out = parallel.process(audio)
        assert out.shape == audio.shape
        assert np.max(np.abs(out)) <= 1.0


class TestEngineRegistry:
    def test_custom_engine_registration_and_dispatch(self):
        from melodica.engines import EngineRegistry, build_engine, HarmonizerPort

        class MockCustomEngine(HarmonizerPort):
            def harmonize(self, req: HarmonizationRequest) -> list[ChordLabel]:
                return [ChordLabel(root=req.melody[0].pitch % 12, quality=Quality.MAJOR, start=0.0, duration=4.0)]

        EngineRegistry.register("custom_test_engine", lambda **kw: MockCustomEngine())

        eng = build_engine("custom_test_engine")
        req = HarmonizationRequest(melody=[Note(pitch=65, start=0.0, duration=1.0)], key=C_MAJOR)
        chords = eng.harmonize(req)
        assert len(chords) == 1
        assert chords[0].root == 5  # F (pitch 65 % 12)

        # Cleanup
        EngineRegistry.unregister("custom_test_engine")
        assert EngineRegistry.get("custom_test_engine") is None


class TestDensityStrategyAndInstrumentProfile:
    def test_density_strategy_subdivision_and_thinning(self):
        from melodica.generators.density import DensityStrategy, InstrumentProfile

        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]

        # 2x subdivision
        sub = DensityStrategy.apply(chords, note_density=2.0)
        assert len(sub) == 2
        assert sub[0].duration == 2.0
        assert sub[1].duration == 2.0

        # Thinning
        chords_4 = [
            ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=1.0),
            ChordLabel(root=2, quality=Quality.MINOR, start=1.0, duration=1.0),
            ChordLabel(root=4, quality=Quality.MINOR, start=2.0, duration=1.0),
            ChordLabel(root=5, quality=Quality.MAJOR, start=3.0, duration=1.0),
        ]
        thinned = DensityStrategy.apply(chords_4, note_density=0.5)
        assert len(thinned) < len(chords_4)

        # Instrument profile
        profile = InstrumentProfile(name="Flute", min_pitch=60, max_pitch=96, default_velocity=75, note_density=2.0)
        assert len(profile.apply_density(chords)) == 2
        vel = profile.resolve_velocity()
        assert 1 <= vel <= 127


class TestContextBridge:
    def test_render_to_modifier_context_and_back(self):
        from melodica.render_context import RenderContext
        from melodica.modifiers import ModifierContext

        rc = RenderContext(prev_pitch=67, prev_velocity=85, current_scale=C_MAJOR)
        mc = rc.to_modifier_context(duration_beats=4.0, chords=SAMPLE_CHORDS)

        assert isinstance(mc, ModifierContext)
        assert mc.duration_beats == 4.0
        assert mc.scale == C_MAJOR

        rc_back = mc.to_render_context(prev_pitch=69, prev_velocity=90)
        assert isinstance(rc_back, RenderContext)
        assert rc_back.prev_pitch == 69
        assert rc_back.current_scale == C_MAJOR


class TestHarmonizationSegmentation:
    def test_segmentation_change_points_and_observations(self):
        from melodica.harmonize._observation import HarmonizationSegmentation
        from melodica.types import BarGrid

        # Change points
        cp_bars = HarmonizationSegmentation.get_change_points(16.0, chord_change="bars", bar_grid=BarGrid(numerator=4, denominator=4))
        assert cp_bars == [0.0, 4.0, 8.0, 12.0]

        cp_strong = HarmonizationSegmentation.get_change_points(8.0, chord_change="strong_beats", bar_grid=BarGrid(numerator=4, denominator=4))
        assert cp_strong == [0.0, 2.0, 4.0, 6.0]

        # Observation extraction
        melody = [
            Note(pitch=60, start=0.0, duration=1.0),  # C (pc 0) in [0, 4)
            Note(pitch=64, start=2.0, duration=1.0),  # E (pc 4) in [0, 4)
            Note(pitch=67, start=4.5, duration=1.0),  # G (pc 7) in [4, 8)
        ]
        obs = HarmonizationSegmentation.extract_observations(melody, [0.0, 4.0, 8.0])
        assert len(obs) == 3
        assert obs[0] == [0, 4]
        assert obs[1] == [7]
        assert obs[2] == [0]  # default fallback


class TestFormValidator:
    def test_form_validator_rule_extensibility(self):
        from melodica.form_validator import FormValidator, FormIssue

        class CustomSilenceRule:
            name = "Custom Silence Rule"

            def evaluate(self, tracks_data, bpm=120.0, form=None):
                if not tracks_data:
                    return [FormIssue(code="CUST-1", severity="WARNING", message="No tracks provided.")]
                return []

        validator = FormValidator(rules=[CustomSilenceRule()])
        issues = validator.validate({})
        assert len(issues) == 1
        assert issues[0].code == "CUST-1"

        # Default rules with normal track data
        default_val = FormValidator()
        track_notes = {"Piano": [Note(pitch=60, start=0.0, duration=4.0)]}
        issues_def = default_val.validate(track_notes, bpm=120.0)
        assert isinstance(issues_def, list)



