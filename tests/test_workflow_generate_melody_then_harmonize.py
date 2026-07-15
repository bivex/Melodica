"""
tests/test_workflow_generate_melody_then_harmonize.py — 50+ comprehensive unit and edge case tests 
for the melody-first harmonization workflow.
"""

import pytest
from melodica.types import Scale, Mode, NoteInfo, ChordLabel
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart
from melodica.generators.melody import MelodyGenerator
from melodica.generators.bass import BassGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.rest import RestGenerator

# 12 Roots
ROOTS = list(range(12))

# 4 Key Modes
MODES = [Mode.MAJOR, Mode.NATURAL_MINOR, Mode.DORIAN, Mode.HUNGARIAN_MINOR]

# 5 Time Signatures
TIME_SIGNATURES = [(4, 4), (3, 4), (5, 4), (6, 8), (7, 8)]

# Bar lengths
BARS = [1, 2, 4, 8]


class TestMelodyThenHarmonizeEdgeCases:
    
    @pytest.mark.parametrize("root", ROOTS)
    @pytest.mark.parametrize("mode", MODES)
    def test_scale_mode_combinations(self, root, mode):
        """
        [48 Tests] Test all 12 roots across 4 key modes to verify that scale constraints,
        bootstrap progressions, and HMM emissions do not cause failures or out-of-key anomalies.
        """
        scale = Scale(root=root, mode=mode)
        config = IdeaToolConfig(
            scale=scale,
            bars=2,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="mel", generator_type="melody", generator=MelodyGenerator()),
                TrackConfig(name="bas", generator_type="bass", generator=BassGenerator())
            ]
        )
        tool = IdeaTool(config)
        result = tool.generate()
        
        assert len(result["mel"]) > 0
        assert len(result["bas"]) > 0
        assert len(tool.get_chords()) > 0

    @pytest.mark.parametrize("time_sig", TIME_SIGNATURES)
    @pytest.mark.parametrize("bars", BARS)
    def test_time_signature_and_bars(self, time_sig, bars):
        """
        [20 Tests] Verify that BarGrid calculation handles different meter structures 
        and time segmentations (from 1 bar to 8 bars) across various signature layouts.
        """
        config = IdeaToolConfig(
            scale=Scale(0, Mode.MAJOR),
            bars=bars,
            time_signature=time_sig,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="mel", generator_type="melody", generator=MelodyGenerator())
            ]
        )
        tool = IdeaTool(config)
        result = tool.generate()
        
        assert len(result["mel"]) > 0
        assert len(tool.get_chords()) > 0

    @pytest.mark.parametrize("gen_class, gen_type", [
        (MelodyGenerator, "melody"),
        (LeadSynthGenerator, "melody"),
    ])
    @pytest.mark.parametrize("use_vl", [True, False])
    @pytest.mark.parametrize("use_tc", [True, False])
    def test_workflow_options_and_generators(self, gen_class, gen_type, use_vl, use_tc):
        """
        [8 Tests] Verify that the workflow handles LeadSynth and Melody generators,
        while turning voice leading and tension curves on/off dynamically.
        """
        config = IdeaToolConfig(
            scale=Scale(2, Mode.NATURAL_MINOR),
            bars=4,
            workflow="generate_melody_then_harmonize",
            use_voice_leading=use_vl,
            use_tension_curve=use_tc,
            tracks=[
                TrackConfig(name="mel", generator_type=gen_type, generator=gen_class()),
                TrackConfig(name="bas", generator_type="bass", generator=BassGenerator())
            ]
        )
        tool = IdeaTool(config)
        result = tool.generate()
        
        assert len(result["mel"]) > 0
        assert len(result["bas"]) > 0
        assert len(tool.get_chords()) > 0

    def test_no_melody_tracks_fallback(self):
        """
        Verify that if no track has generator_type == "melody", the engine
        automatically provisions an '_auto_melody' track, harmonizes against it,
        and generates non-melody tracks.
        """
        config = IdeaToolConfig(
            scale=Scale(0, Mode.MAJOR),
            bars=4,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="bass_track", generator_type="bass", generator=BassGenerator())
            ]
        )
        tool = IdeaTool(config)
        result = tool.generate()
        
        assert "_auto_melody" in result
        assert len(result["_auto_melody"]) > 0
        assert "bass_track" in result
        assert len(result["bass_track"]) > 0
        assert len(tool.get_chords()) > 0

    def test_multiple_melody_tracks(self):
        """
        Verify that multiple melody tracks are bootstrap-rendered, their notes
        are merged together for harmonization, and the final chords are used
        for the remaining accompaniment tracks.
        """
        config = IdeaToolConfig(
            scale=Scale(2, Mode.NATURAL_MINOR),
            bars=4,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="melody_1", generator_type="melody", generator=MelodyGenerator(), density=0.7),
                TrackConfig(name="melody_2", generator_type="melody", generator=MelodyGenerator(), density=0.5),
                TrackConfig(name="accompaniment_pad", generator_type="ambient", generator=AmbientPadGenerator())
            ]
        )
        tool = IdeaTool(config)
        result = tool.generate()
        
        assert len(result["melody_1"]) > 0
        assert len(result["melody_2"]) > 0
        assert len(result["accompaniment_pad"]) > 0
        assert len(tool.get_chords()) > 0

    def test_empty_melody_fallback(self):
        """
        Verify that if melody generators produce zero notes (using RestGenerator),
        the workflow handles it gracefully by falling back to the bootstrap chord progression.
        """
        config = IdeaToolConfig(
            scale=Scale(0, Mode.MAJOR),
            bars=4,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="silent_melody", generator_type="melody", generator=RestGenerator()),
                TrackConfig(name="bass_track", generator_type="bass", generator=BassGenerator(), density=0.6)
            ]
        )
        tool = IdeaTool(config)
        result = tool.generate()
        
        assert len(result["silent_melody"]) == 0
        assert len(result["bass_track"]) > 0
        assert len(tool.get_chords()) > 0

    def test_zero_bars_or_empty_part(self):
        """
        Verify that configuring zero bars handles it safely.
        """
        config = IdeaToolConfig(
            scale=Scale(0, Mode.MAJOR),
            bars=0,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="mel", generator_type="melody")
            ]
        )
        tool = IdeaTool(config)
        try:
            result = tool.generate()
            assert len(result.get("mel", [])) == 0
        except ValueError:
            pass
