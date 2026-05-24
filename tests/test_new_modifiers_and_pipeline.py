# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import NoteInfo, ChordLabel, Quality, Scale, Mode, MusicTimeline, KeyLabel
from melodica.modifiers import ModifierContext, ModifierPipeline
from melodica.modifiers.rhythmic import (
    RhythmicDensityModifier,
    PolyrhythmLayerModifier,
    AdaptiveSwingModifier,
    MetricAccentModifier,
)
from melodica.modifiers.harmonic import ChordToneSnapModifier
from melodica.modifiers.dynamic import VelocityCurveModifier, ExpressionLFOModifier
from melodica.modifiers.voicings import ChordVoicingSpreadModifier, SmartDivisiModifier
from melodica.modifiers.variations_articulation import (
    SlideLegatoModifier,
    ArticulationByLengthModifier,
    OverlapSafetyModifier,
)
from melodica.modifiers.rc_variations_structural import (
    PhraseBoundaryModifier,
    MotifTransformModifier,
)

@pytest.fixture
def dummy_context():
    key = Scale(root=0, mode=Mode.MAJOR)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0, duration=4)]
    timeline = MusicTimeline(chords=chords, keys=[KeyLabel(scale=key, start=0, duration=4)])
    return ModifierContext(duration_beats=4.0, chords=chords, timeline=timeline, scale=key)

def test_modifier_pipeline(dummy_context):
    base_notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=64)]
    pipeline = ModifierPipeline(base_notes=base_notes)
    
    from melodica.modifiers.harmonic import TransposeModifier
    pipeline.add_modifier(TransposeModifier(semitones=12))
    
    # Process
    out = pipeline.process(dummy_context)
    assert out[0].pitch == 72
    assert pipeline.base_notes[0].pitch == 60 # Non-destructive
    
    # Bypass
    pipeline.set_bypass(0, True)
    out_bypassed = pipeline.process(dummy_context)
    assert out_bypassed[0].pitch == 60
    
    # Reorder/Insert
    pipeline.set_bypass(0, False)
    pipeline.insert_modifier(0, TransposeModifier(semitones=-12))
    out_chain = pipeline.process(dummy_context)
    assert out_chain[0].pitch == 60 # -12 + 12 = 0
    
    # Remove
    pipeline.remove_modifier(0)
    out_removed = pipeline.process(dummy_context)
    assert out_removed[0].pitch == 72

def test_chord_tone_snap_modifier(dummy_context):
    # C Major chord (0, 4, 7)
    # D (2) is not in chord. Nearest are C(0) or E(4).
    notes = [NoteInfo(pitch=62, start=0.0, duration=1.0)]
    mod = ChordToneSnapModifier()
    out = mod.modify(notes, dummy_context)
    assert out[0].pitch in [60, 64]

def test_phrase_boundary_modifier(dummy_context):
    # Context duration is 4.0. Note starts at 3.5, duration 1.0 (ends at 4.5).
    notes = [NoteInfo(pitch=60, start=3.5, duration=1.0)]
    mod = PhraseBoundaryModifier(breath_beats=0.1)
    out = mod.modify(notes, dummy_context)
    # 4.0 - 0.1 = 3.9 limit.
    # Start is 3.5, so new duration should be 3.9 - 3.5 = 0.4.
    assert out[0].duration == pytest.approx(0.4)

def test_velocity_curve_modifier(dummy_context):
    notes = [NoteInfo(pitch=60, start=0.0, duration=1.0), NoteInfo(60, 4.0, 1.0)]
    mod = VelocityCurveModifier(start_vel=40, end_vel=100, curve="exponential")
    out = mod.modify(notes, dummy_context)
    # total_len = 5.0
    # Progress at 0.0 -> 0.0 -> 40
    # Progress at 4.0 -> 0.8 -> 0.8^2 = 0.64 -> 40 + 60*0.64 = 78.4 -> 78
    assert out[0].velocity == 40
    assert out[1].velocity == 78

def test_rhythmic_density_modifier(dummy_context):
    notes = [NoteInfo(60, i, 0.5) for i in range(10)]
    mod = RhythmicDensityModifier(density=0.5)
    out = mod.modify(notes, dummy_context)
    assert len(out) < 10

def test_chord_voicing_spread_modifier(dummy_context):
    notes = [NoteInfo(60, 0.0, 1.0), NoteInfo(64, 0.0, 1.0), NoteInfo(67, 0.0, 1.0)]
    mod = ChordVoicingSpreadModifier(spread_mode="open")
    out = mod.modify(notes, dummy_context)
    # open: lowest -12, highest +12
    pitches = sorted([n.pitch for n in out])
    assert pitches == [48, 64, 79]

def test_slide_legato_modifier(dummy_context):
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0),
        NoteInfo(pitch=62, start=1.0, duration=1.0),
    ]
    mod = SlideLegatoModifier(max_gap=0.05, slide_beats=0.2)
    out = mod.modify(notes, dummy_context)
    assert "pitch_bend" in out[0].expression
    assert len(out[0].expression["pitch_bend"]) > 0

def test_polyrhythm_layer_modifier(dummy_context):
    notes = [NoteInfo(60, 0, 4)]
    mod = PolyrhythmLayerModifier(tuple_count=3, base_count=4)
    out = mod.modify(notes, dummy_context)
    # Original + 3 new notes (at 0, 1.33, 2.66)
    assert len(out) == 4

def test_motif_transform_modifier(dummy_context):
    notes = [
        NoteInfo(60, 0.0, 1.0),
        NoteInfo(62, 1.0, 1.0),
    ]
    # Retrograde: start at 4 - (1+1) = 2.0 and 4 - (0+1) = 3.0
    mod = MotifTransformModifier(transform_type="retrograde")
    out = mod.modify(notes, dummy_context)
    assert out[0].start == 2.0
    assert out[1].start == 3.0
    
    # Inversion around 60: 60 -> 60, 62 -> 58
    mod_inv = MotifTransformModifier(transform_type="inversion", axis_pitch=60)
    out_inv = mod_inv.modify(notes, dummy_context)
    assert out_inv[0].pitch == 60
    assert out_inv[1].pitch == 58

def test_adaptive_swing_modifier(dummy_context):
    notes = [NoteInfo(60, 0.0, 0.5), NoteInfo(60, 1.5, 0.5)]
    mod = AdaptiveSwingModifier(start_swing=0.5, end_swing=1.0, grid=1.0)
    out = mod.modify(notes, dummy_context)
    # At start=0.0, progress=0, swing=0.5 -> delay=0
    assert out[0].start == 0.0
    # At start=1.5, progress>0, swing>0.5 -> delay>0
    assert out[1].start > 1.5

def test_metric_accent_modifier(dummy_context):
    notes = [
        NoteInfo(60, 0.0, 1.0, 64), # Beat 1
        NoteInfo(60, 1.0, 1.0, 64), # Beat 2
    ]
    mod = MetricAccentModifier(strength=1.0)
    out = mod.modify(notes, dummy_context)
    assert out[0].velocity > out[1].velocity

def test_smart_divisi_modifier(dummy_context):
    notes = [
        NoteInfo(67, 0.0, 1.0), # Top
        NoteInfo(64, 0.0, 1.0),
        NoteInfo(60, 0.0, 1.0), # Bottom
    ]
    mod = SmartDivisiModifier(voice_index=0) # Highest
    out = mod.modify(notes, dummy_context)
    assert len(out) == 1
    assert out[0].pitch == 67
    
    mod_bot = SmartDivisiModifier(voice_index=0, from_bottom=True)
    out_bot = mod_bot.modify(notes, dummy_context)
    assert out_bot[0].pitch == 60

def test_expression_lfo_modifier(dummy_context):
    notes = [NoteInfo(60, 0.0, 2.0)]
    mod = ExpressionLFOModifier(cc_num=1, frequency=1.0)
    out = mod.modify(notes, dummy_context)
    assert 1 in out[0].expression
    assert len(out[0].expression[1]) > 10

def test_articulation_by_length_modifier(dummy_context):
    notes = [
        NoteInfo(60, 0.0, 0.1), # short
        NoteInfo(60, 1.0, 1.0), # long
    ]
    mod = ArticulationByLengthModifier(short_threshold=0.2, short_articulation="pizz", long_articulation="arco")
    out = mod.modify(notes, dummy_context)
    assert out[0].articulation == "pizz"
    assert out[1].articulation == "arco"

def test_overlap_safety_modifier(dummy_context):
    notes = [
        NoteInfo(60, 0.0, 1.05),
        NoteInfo(60, 1.0, 1.0),
    ]
    mod = OverlapSafetyModifier(gap_beats=0.05)
    out = mod.modify(notes, dummy_context)
    # n1 should be truncated to 1.0 - 0.05 = 0.95
    assert out[0].duration == pytest.approx(0.95)
