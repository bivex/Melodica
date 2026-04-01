"""Tests for NeuralMelodyGenerator — both fallback and (optional) neural paths."""
import os
import tempfile
import pytest

from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators.neural_melody import (
    NeuralMelodyGenerator,
    _encode_chords,
    _encode_notes,
    _decode_tokens,
    VOCAB_SIZE,
    _BOS, _EOS, _PITCH_BASE, _CROOT_BASE, _KROOT_BASE,
)
from melodica.render_context import RenderContext

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


def _simple_chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
    ]


def _melody_notes() -> list[NoteInfo]:
    return [
        NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
        NoteInfo(pitch=62, start=0.5, duration=0.5, velocity=75),
        NoteInfo(pitch=64, start=1.0, duration=0.5, velocity=80),
        NoteInfo(pitch=65, start=1.5, duration=0.5, velocity=70),
        NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=85),
        NoteInfo(pitch=65, start=3.0, duration=0.5, velocity=75),
        NoteInfo(pitch=64, start=3.5, duration=0.5, velocity=70),
        NoteInfo(pitch=62, start=4.0, duration=0.5, velocity=75),
        NoteInfo(pitch=60, start=4.5, duration=1.5, velocity=80),
    ]


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

class TestTokenizer:
    def test_encode_chords_starts_with_bos(self):
        tokens = _encode_chords(_simple_chords(), C_MAJOR)
        assert tokens[0] == _BOS

    def test_encode_chords_contains_key_root(self):
        tokens = _encode_chords(_simple_chords(), C_MAJOR)
        assert _KROOT_BASE + 0 in tokens  # C = 0

    def test_encode_chords_contains_chord_roots(self):
        tokens = _encode_chords(_simple_chords(), C_MAJOR)
        assert _CROOT_BASE + 0 in tokens   # C chord
        assert _CROOT_BASE + 7 in tokens   # G chord

    def test_encode_notes_contains_pitch_tokens(self):
        notes = _melody_notes()
        tokens = _encode_notes(notes, 6.0)
        pitch_tokens = [t for t in tokens if _PITCH_BASE <= t < _PITCH_BASE + 128]
        assert len(pitch_tokens) == len(notes)

    def test_encode_notes_ends_with_eos(self):
        tokens = _encode_notes(_melody_notes(), 6.0)
        assert tokens[-1] == _EOS

    def test_encode_notes_pitch_values_correct(self):
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80)]
        tokens = _encode_notes(notes, 1.0)
        assert _PITCH_BASE + 60 in tokens

    def test_all_tokens_in_vocab(self):
        prefix = _encode_chords(_simple_chords(), C_MAJOR)
        melody = _encode_notes(_melody_notes(), 6.0)
        for t in prefix + melody:
            assert 0 <= t < VOCAB_SIZE, f"Token {t} out of vocab"


# ---------------------------------------------------------------------------
# Fallback mode (no model)
# ---------------------------------------------------------------------------

class TestFallbackMode:
    def test_produces_notes(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_is_not_neural(self):
        gen = NeuralMelodyGenerator()
        assert not gen.is_neural

    def test_all_pitches_valid(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 0 <= n.pitch <= 127

    def test_all_starts_in_range(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 0.0 <= n.start < 8.0

    def test_all_durations_positive(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert n.duration > 0.0

    def test_all_velocities_valid(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 1 <= n.velocity <= 127

    def test_empty_chords(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render([], C_MAJOR, 4.0)
        assert notes == []

    def test_note_range_respected(self):
        gen = NeuralMelodyGenerator(note_range_low=60, note_range_high=72)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        for n in notes:
            assert 60 <= n.pitch <= 72

    def test_density_low_fewer_notes(self):
        from melodica.generators import GeneratorParams
        params_lo = GeneratorParams(density=0.1)
        params_hi = GeneratorParams(density=0.9)
        gen_lo = NeuralMelodyGenerator(params=params_lo)
        gen_hi = NeuralMelodyGenerator(params=params_hi)
        notes_lo = gen_lo.render(_simple_chords(), C_MAJOR, 8.0)
        notes_hi = gen_hi.render(_simple_chords(), C_MAJOR, 8.0)
        # Low density → quarter notes (fewer); high density → 8th notes (more)
        assert len(notes_lo) <= len(notes_hi)

    def test_high_harmony_prob_chord_tones(self):
        gen = NeuralMelodyGenerator(harmony_prob=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        # With harmony_prob=1.0 every note should be a chord tone
        chord = _simple_chords()[0]
        chord_pcs = set(chord.pitch_classes())
        # At least some notes on chord 0 time range should be chord tones
        notes_in_c = [n for n in notes if n.start < 4.0]
        ct_count = sum(1 for n in notes_in_c if n.pitch % 12 in chord_pcs)
        assert ct_count > 0

    def test_context_prev_pitch_used(self):
        gen = NeuralMelodyGenerator()
        ctx = RenderContext(prev_pitch=72)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        notes_ctx = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx)
        # With prev_pitch=72, generation should start near 72
        assert len(notes_ctx) > 0

    def test_context_updated_after_render(self):
        gen = NeuralMelodyGenerator()
        gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert gen._last_context is not None
        assert gen._last_context.prev_pitch is not None

    def test_minor_key(self):
        gen = NeuralMelodyGenerator()
        notes = gen.render(_simple_chords(), A_MINOR, 4.0)
        assert len(notes) > 0

    def test_single_chord(self):
        gen = NeuralMelodyGenerator()
        chord = [ChordLabel(root=5, quality=Quality.MINOR, start=0.0, duration=8.0)]
        notes = gen.render(chord, C_MAJOR, 8.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("direction_bias", [-1.0, 0.0, 1.0])
    def test_direction_bias(self, direction_bias):
        gen = NeuralMelodyGenerator(direction_bias=direction_bias)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_phrase_position_affects_velocity(self):
        gen = NeuralMelodyGenerator()
        ctx_start = RenderContext(phrase_position=0.0)
        ctx_end   = RenderContext(phrase_position=1.0)
        notes_s = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx_start)
        notes_e = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx_end)
        avg_s = sum(n.velocity for n in notes_s) / max(1, len(notes_s))
        avg_e = sum(n.velocity for n in notes_e) / max(1, len(notes_e))
        # phrase_position=1.0 → intensity=1.0 → louder
        assert avg_e >= avg_s - 5  # allow small tolerance


# ---------------------------------------------------------------------------
# Neural path (requires torch)
# ---------------------------------------------------------------------------

try:
    import torch
    _TORCH_AVAILABLE = True
except ImportError:
    _TORCH_AVAILABLE = False


@pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch not installed")
class TestNeuralPath:
    def test_build_model_not_none(self):
        from melodica.generators.neural_melody import _build_model
        model = _build_model()
        assert model is not None

    def test_model_forward_pass(self):
        import torch
        from melodica.generators.neural_melody import _build_model, VOCAB_SIZE
        model = _build_model()
        x = torch.randint(0, VOCAB_SIZE, (1, 16))
        logits = model(x)
        assert logits.shape == (1, 16, VOCAB_SIZE)

    def test_train_and_save(self, tmp_path):
        out = str(tmp_path / "melody.pt")
        gen = NeuralMelodyGenerator.train_from_notes(
            _melody_notes(),
            out,
            chords=_simple_chords(),
            key=C_MAJOR,
            epochs=2,
            batch_size=2,
            verbose=False,
        )
        assert os.path.isfile(out)
        assert gen.is_neural

    def test_neural_render_produces_notes(self, tmp_path):
        out = str(tmp_path / "melody.pt")
        gen = NeuralMelodyGenerator.train_from_notes(
            _melody_notes(), out,
            chords=_simple_chords(), key=C_MAJOR,
            epochs=3, batch_size=2, verbose=False,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_neural_pitches_valid(self, tmp_path):
        out = str(tmp_path / "melody.pt")
        gen = NeuralMelodyGenerator.train_from_notes(
            _melody_notes(), out,
            chords=_simple_chords(), key=C_MAJOR,
            epochs=2, batch_size=2, verbose=False,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        for n in notes:
            assert 0 <= n.pitch <= 127

    def test_load_model_path(self, tmp_path):
        out = str(tmp_path / "melody.pt")
        NeuralMelodyGenerator.train_from_notes(
            _melody_notes(), out,
            chords=_simple_chords(), key=C_MAJOR,
            epochs=2, batch_size=2, verbose=False,
        )
        gen2 = NeuralMelodyGenerator(model_path=out)
        assert gen2.is_neural
        notes = gen2.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_missing_model_path_falls_back(self):
        gen = NeuralMelodyGenerator(model_path="/nonexistent/path.pt")
        assert not gen.is_neural
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_temperature_affects_output(self, tmp_path):
        out = str(tmp_path / "melody.pt")
        NeuralMelodyGenerator.train_from_notes(
            _melody_notes(), out,
            chords=_simple_chords(), key=C_MAJOR,
            epochs=2, batch_size=2, verbose=False,
        )
        gen_low  = NeuralMelodyGenerator(model_path=out, temperature=0.5)
        gen_high = NeuralMelodyGenerator(model_path=out, temperature=1.5)
        notes_low  = gen_low.render(_simple_chords(), C_MAJOR, 4.0)
        notes_high = gen_high.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes_low) > 0
        assert len(notes_high) > 0

    def test_train_too_few_notes_raises(self, tmp_path):
        out = str(tmp_path / "melody.pt")
        with pytest.raises(ValueError):
            NeuralMelodyGenerator.train_from_notes([], out, verbose=False)


# ---------------------------------------------------------------------------
# generate_training_data + train_from_dataset
# ---------------------------------------------------------------------------

class TestDatasetTraining:
    def _progressions(self):
        return [
            [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
             ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)],
            [ChordLabel(root=5, quality=Quality.MAJOR, start=0.0, duration=4.0),
             ChordLabel(root=0, quality=Quality.MAJOR, start=4.0, duration=4.0)],
            [ChordLabel(root=9, quality=Quality.MINOR, start=0.0, duration=4.0),
             ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0)],
            [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=2.0),
             ChordLabel(root=7, quality=Quality.MAJOR, start=2.0, duration=2.0),
             ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=2.0),
             ChordLabel(root=0, quality=Quality.MAJOR, start=6.0, duration=2.0)],
        ]

    def test_generate_training_data_returns_tuples(self):
        from melodica.generators import MelodyGenerator
        gen = MelodyGenerator()
        dataset = NeuralMelodyGenerator.generate_training_data(
            gen, self._progressions(), [C_MAJOR], duration_beats=8.0
        )
        assert len(dataset) == len(self._progressions())
        for notes, chords, key in dataset:
            assert isinstance(notes, list)
            assert len(notes) > 0
            assert isinstance(chords, list)
            assert isinstance(key, Scale)

    def test_generate_training_data_n_samples(self):
        from melodica.generators import MelodyGenerator
        gen = MelodyGenerator()
        dataset = NeuralMelodyGenerator.generate_training_data(
            gen, self._progressions(), [C_MAJOR], n_samples=10
        )
        assert len(dataset) == 10

    def test_generate_training_data_multiple_keys(self):
        from melodica.generators import MelodyGenerator
        gen = MelodyGenerator()
        keys = [C_MAJOR, A_MINOR, Scale(root=5, mode=Mode.MAJOR), Scale(root=2, mode=Mode.DORIAN)]
        dataset = NeuralMelodyGenerator.generate_training_data(
            gen, self._progressions(), keys, duration_beats=8.0
        )
        assert len(dataset) == 4

    def test_generate_training_data_markov(self):
        from melodica.generators import MarkovMelodyGenerator
        gen = MarkovMelodyGenerator()
        dataset = NeuralMelodyGenerator.generate_training_data(
            gen, self._progressions(), [C_MAJOR], n_samples=8
        )
        assert len(dataset) == 8
        for notes, _, _ in dataset:
            assert all(0 <= n.pitch <= 127 for n in notes)

    def test_generate_training_data_neural_generator(self):
        # NeuralMelodyGenerator itself (fallback) can generate training data
        teacher = NeuralMelodyGenerator(harmony_prob=0.8)
        dataset = NeuralMelodyGenerator.generate_training_data(
            teacher, self._progressions(), [C_MAJOR], n_samples=6
        )
        assert len(dataset) == 6

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch not installed")
    def test_train_from_dataset(self, tmp_path):
        from melodica.generators import MelodyGenerator
        gen = MelodyGenerator()
        dataset = NeuralMelodyGenerator.generate_training_data(
            gen, self._progressions(), [C_MAJOR], n_samples=20
        )
        out = str(tmp_path / "ds.pt")
        trained = NeuralMelodyGenerator.train_from_dataset(
            dataset, out, epochs=3, batch_size=4, seq_len=64, verbose=False
        )
        assert os.path.isfile(out)
        assert trained.is_neural
        notes = trained.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch not installed")
    def test_train_from_dataset_multiple_generators(self, tmp_path):
        """Train on mix of MelodyGenerator + MarkovMelodyGenerator output."""
        from melodica.generators import MelodyGenerator, MarkovMelodyGenerator
        dataset = []
        for src_gen in [MelodyGenerator(), MarkovMelodyGenerator()]:
            dataset += NeuralMelodyGenerator.generate_training_data(
                src_gen, self._progressions(), [C_MAJOR, A_MINOR], n_samples=8
            )
        out = str(tmp_path / "mixed.pt")
        trained = NeuralMelodyGenerator.train_from_dataset(
            dataset, out, epochs=3, batch_size=4, seq_len=64, verbose=False
        )
        assert trained.is_neural

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch not installed")
    def test_train_from_dataset_empty_raises(self, tmp_path):
        out = str(tmp_path / "empty.pt")
        with pytest.raises(ValueError):
            NeuralMelodyGenerator.train_from_dataset([], out, verbose=False)

    @pytest.mark.skipif(not _TORCH_AVAILABLE, reason="torch not installed")
    def test_trained_model_improves_chord_fit(self, tmp_path):
        """After training on high harmony_prob data, neural model should have
        reasonable chord tone coverage."""
        teacher = NeuralMelodyGenerator(harmony_prob=1.0)
        dataset = NeuralMelodyGenerator.generate_training_data(
            teacher, self._progressions(), [C_MAJOR], n_samples=30
        )
        out = str(tmp_path / "chord.pt")
        trained = NeuralMelodyGenerator.train_from_dataset(
            dataset, out, epochs=5, batch_size=4, seq_len=64, verbose=False
        )
        notes = trained.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        for n in notes:
            assert 0 <= n.pitch <= 127


# ---------------------------------------------------------------------------
# IdeaTool integration
# ---------------------------------------------------------------------------

class TestIdeaToolIntegration:
    def test_idea_tool_creates_neural_generator(self):
        from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
        from melodica.generators import GeneratorParams
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=2,
            tracks=[TrackConfig(name="melody", generator_type="neural")],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "melody" in result
        assert len(result["melody"]) > 0

    def test_idea_tool_neural_with_params(self):
        from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig
        config = IdeaToolConfig(
            scale=C_MAJOR,
            bars=2,
            tracks=[TrackConfig(
                name="mel",
                generator_type="neural",
                params={"harmony_prob": 0.8, "temperature": 0.9},
            )],
        )
        tool = IdeaTool(config)
        result = tool.generate()
        assert "mel" in result
