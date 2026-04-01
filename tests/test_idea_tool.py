import pytest
from melodica.types import Scale, Mode, NoteInfo
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, quick_compose
from melodica.modifiers import HumanizeModifier, TransposeModifier


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


class TestIdeaTool:
    def test_generate_full_composition(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            tracks=[
                TrackConfig(name="melody", generator_type="melody"),
                TrackConfig(name="bass", generator_type="bass"),
                TrackConfig(name="chords", generator_type="chord"),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()

        assert "melody" in result
        assert "bass" in result
        assert "chords" in result
        assert len(result["melody"]) > 0
        assert len(result["bass"]) > 0
        assert len(result["chords"]) > 0

    def test_chord_progression(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            tracks=[TrackConfig(name="melody", generator_type="melody")],
        )
        tool = IdeaTool(config)
        tool.generate()
        chords = tool.get_chords()
        assert len(chords) == 4

    def test_arrangement_patterns(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            tracks=[
                TrackConfig(name="melody", generator_type="melody", arrangement="AABA"),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["melody"]) > 0

    def test_with_percussion(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            tracks=[
                TrackConfig(name="melody", generator_type="melody"),
                TrackConfig(name="drums", generator_type="percussion"),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["drums"]) > 0

    def test_with_ostinato(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            tracks=[
                TrackConfig(name="ostinato", generator_type="ostinato"),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["ostinato"]) > 0

    def test_with_tension_curve(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=8,
            use_tension_curve=True,
            tracks=[TrackConfig(name="melody", generator_type="melody")],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["melody"]) > 0

    def test_with_non_chord_tones(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            use_non_chord_tones=True,
            tracks=[TrackConfig(name="melody", generator_type="melody")],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["melody"]) > 0

    def test_multiple_styles(self):
        for style in ["pop", "jazz", "rock", "cinematic"]:
            config = IdeaToolConfig(
                scale=C_MAJOR,
                bars=4,
                style=style,
                tracks=[TrackConfig(name="melody", generator_type="melody")],
            )
            tool = IdeaTool(config)
            result = tool.generate()
            assert len(result["melody"]) > 0

    def test_variations(self):
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=4,
            tracks=[
                TrackConfig(
                    name="melody", generator_type="melody", variations=["humanize", "octave_double"]
                ),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["melody"]) > 0


class TestWorkflows:
    def test_workflow_harmonize_melody(self):
        seed = [NoteInfo(pitch=60 + i, start=float(i) * 0.5, duration=0.45) for i in range(8)]
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            workflow="harmonize_melody",
            seed_melody=seed,
            use_harmonic_verifier=False,
            tracks=[
                TrackConfig(name="melody", generator_type="melody"),
                TrackConfig(name="bass", generator_type="bass"),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert result["melody"] == seed  # seed passed through unchanged
        assert len(result["bass"]) > 0
        assert len(tool.get_chords()) > 0

    def test_workflow_generate_melody_then_harmonize(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.NATURAL_MINOR),
            bars=4,
            workflow="generate_melody_then_harmonize",
            tracks=[
                TrackConfig(name="melody", generator_type="melody"),
                TrackConfig(name="bass", generator_type="bass"),
            ],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert len(result["melody"]) > 0
        assert len(result["bass"]) > 0
        assert len(tool.get_chords()) > 0

    def test_workflow_harmonize_melody_no_seed_falls_back(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            workflow="harmonize_melody",
            seed_melody=None,
            tracks=[TrackConfig(name="melody", generator_type="melody")],
        )
        result = IdeaTool(config).generate()
        assert len(result["melody"]) > 0


class TestNewGeneratorTypes:
    def test_markov_generator(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="m", generator_type="markov")],
        )
        assert len(IdeaTool(config).generate()["m"]) > 0

    def test_ambient_generator(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="a", generator_type="ambient")],
        )
        assert len(IdeaTool(config).generate()["a"]) > 0

    def test_dyads_generator(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="d", generator_type="dyads")],
        )
        assert len(IdeaTool(config).generate()["d"]) > 0

    def test_canon_generator(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="c", generator_type="canon")],
        )
        assert len(IdeaTool(config).generate()["c"]) > 0

    def test_call_response_generator(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="cr", generator_type="call_response")],
        )
        assert len(IdeaTool(config).generate()["cr"]) > 0

    def test_unknown_generator_returns_empty(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="x", generator_type="nonexistent_type")],
        )
        assert IdeaTool(config).generate()["x"] == []


class TestRenderTracks:
    def test_render_tracks_returns_track_objects(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[
                TrackConfig(name="melody", generator_type="melody", instrument="violin"),
                TrackConfig(name="bass", generator_type="bass", instrument="cello"),
                TrackConfig(name="drums", generator_type="percussion", instrument="percussion"),
            ],
        )
        tracks = IdeaTool(config).render_tracks()
        assert tracks["melody"].program == 40  # violin GM program
        assert tracks["bass"].program == 42  # cello GM program
        assert tracks["drums"].channel == 9  # percussion on channel 9
        assert tracks["melody"].channel != 9

    def test_render_tracks_no_channel_collision(self):
        """15 non-percussion tracks must each get a unique channel (0-8, 10-15)."""
        track_cfgs = [
            TrackConfig(name=f"t{i}", generator_type="melody", density=0.3) for i in range(15)
        ]
        config = IdeaToolConfig(scale=Scale(root=0, mode=Mode.MAJOR), bars=2, tracks=track_cfgs)
        tracks = IdeaTool(config).render_tracks()
        channels = [t.channel for t in tracks.values()]
        assert 9 not in channels
        assert len(set(channels)) == len(channels)  # all unique


class TestModifiersAndVoiceLeading:
    def test_track_config_modifiers_applied(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[
                TrackConfig(
                    name="melody",
                    generator_type="melody",
                    modifiers=[HumanizeModifier(timing_std=0.02, velocity_std=5)],
                )
            ],
        )
        result = IdeaTool(config).generate()
        assert len(result["melody"]) > 0

    def test_use_voice_leading(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            use_voice_leading=True,
            tracks=[TrackConfig(name="melody", generator_type="melody")],
        )
        result = IdeaTool(config).generate()
        assert len(result["melody"]) > 0

    def test_use_texture_control(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            use_tension_curve=True,
            use_texture_control=True,
            tracks=[TrackConfig(name="chords", generator_type="chord")],
        )
        result = IdeaTool(config).generate()
        # texture control may filter some notes; just check it doesn't crash
        assert isinstance(result["chords"], list)

    def test_variations_preserve_articulation(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[
                TrackConfig(
                    name="m",
                    generator_type="melody",
                    variations=["staccato"],
                )
            ],
        )
        result = IdeaTool(config).generate()
        staccato_notes = [n for n in result["m"] if n.articulation == "staccato"]
        assert len(staccato_notes) > 0


class TestContextThreading:
    def test_context_preserved_across_calls(self):
        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="melody", generator_type="melody")],
        )
        tool = IdeaTool(config)
        tool.generate()
        assert "melody" in tool._track_contexts
        ctx = tool._track_contexts["melody"]
        assert ctx.prev_pitch is not None

    def test_stale_context_cleaned_up(self):
        tool = IdeaTool(
            IdeaToolConfig(
                scale=Scale(root=0, mode=Mode.MAJOR),
                bars=4,
                tracks=[TrackConfig(name="old_track", generator_type="melody")],
            )
        )
        tool.generate()
        assert "old_track" in tool._track_contexts

        # Change config to different track
        tool.config.tracks = [TrackConfig(name="new_track", generator_type="melody")]
        tool.generate()
        assert "old_track" not in tool._track_contexts
        assert "new_track" in tool._track_contexts


class TestChordsInResult:
    def test_chords_key_contains_chord_labels(self):
        from melodica.types import ChordLabel

        config = IdeaToolConfig(
            scale=Scale(root=0, mode=Mode.MAJOR),
            bars=4,
            tracks=[TrackConfig(name="m", generator_type="melody")],
        )
        result = IdeaTool(config).generate()
        assert "_chords" in result
        assert len(result["_chords"]) == 4
        assert all(isinstance(c, ChordLabel) for c in result["_chords"])


class TestQuickCompose:
    def test_quick_compose(self):
        result = quick_compose(style="pop", bars=4, tracks=["melody", "bass"])
        assert "melody" in result
        assert "bass" in result
        assert len(result["melody"]) > 0
        assert len(result["bass"]) > 0

    def test_quick_compose_with_percussion(self):
        result = quick_compose(style="rock", bars=4, tracks=["melody", "bass", "percussion"])
        assert len(result["percussion"]) > 0
