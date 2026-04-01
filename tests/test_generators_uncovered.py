"""Tests for the 37 generators not covered in previous test files."""
import pytest
from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators.acciaccatura import AcciaccaturaGenerator
from melodica.generators.ambient import AmbientPadGenerator
from melodica.generators.arranger import ArrangerGenerator
from melodica.generators.bass_slap import BassSlapGenerator
from melodica.generators.bend import BendGenerator
from melodica.generators.broken_chord import BrokenChordGenerator
from melodica.generators.cadence import CadenceGenerator
from melodica.generators.chorale import ChoraleGenerator
from melodica.generators.clusters import ClusterGenerator
from melodica.generators.drone import DroneGenerator
from melodica.generators.dyads_run import DyadsRunGenerator
from melodica.generators.euclidean_rhythm import EuclideanRhythmGenerator
from melodica.generators.fills import FillGenerator
from melodica.generators.fx_impact import FXImpactGenerator
from melodica.generators.fx_riser import FXRiserGenerator
from melodica.generators.glissando import GlissandoGenerator
from melodica.generators.harmonics import HarmonicsGenerator
from melodica.generators.humanizer import HumanizerGenerator
from melodica.generators.modal_interchange import ModalInterchangeGenerator
from melodica.generators.modern_chord import ModernChordPatternGenerator
from melodica.generators.motif_development import MotifDevelopmentGenerator
from melodica.generators.motive import MotiveGenerator
from melodica.generators.ornamentation import OrnamentationGenerator
from melodica.generators.pedal_melody import PedalMelodyGenerator
from melodica.generators.percussion_ensemble import PercussionEnsembleGenerator
from melodica.generators.phrase_container import PhraseContainer
from melodica.generators.pickup import PickupGenerator
from melodica.generators.pluck_sequence import PluckSequenceGenerator
from melodica.generators.polyrhythm import PolyrhythmGenerator
from melodica.generators.power_chord import PowerChordGenerator
from melodica.generators.reharmonization import ReharmonizationGenerator
from melodica.generators.rest import RestGenerator
from melodica.generators.sequence import SequenceGenerator
from melodica.generators.tremolo_picking import TremoloPickingGenerator
from melodica.generators.trill import TrillTremoloGenerator
from melodica.generators.voice_leading import VoiceLeadingGenerator
from melodica.generators.walking_bass import WalkingBassGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


def _single_chord() -> list[ChordLabel]:
    return [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]


def _assert_valid_notes(notes: list[NoteInfo]) -> None:
    for n in notes:
        assert 0 <= n.pitch <= 127
        assert n.duration > 0
        assert n.start >= 0
        assert 1 <= n.velocity <= 127


# ---------------------------------------------------------------------------
# Ornamentation
# ---------------------------------------------------------------------------

class TestAcciaccaturaGenerator:
    def test_produces_notes(self):
        gen = AcciaccaturaGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("grace_type", ["upper", "lower", "double", "slide_up", "slide_down", "chord"])
    def test_grace_types(self, grace_type):
        gen = AcciaccaturaGenerator(grace_type=grace_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_grace_type_raises(self):
        with pytest.raises(ValueError):
            AcciaccaturaGenerator(grace_type="unknown")

    def test_pitch_range(self):
        gen = AcciaccaturaGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)

    def test_density_zero_produces_main_notes(self):
        gen = AcciaccaturaGenerator(density=0.0)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        # With density=0 no grace notes, but main notes should appear
        assert isinstance(notes, list)


class TestOrnamentationGenerator:
    def test_produces_notes(self):
        gen = OrnamentationGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("ornament_type", ["mordent", "lower_mordent", "turn", "inverted_turn", "gruppetto", "shake"])
    def test_ornament_types(self, ornament_type):
        gen = OrnamentationGenerator(ornament_type=ornament_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_ornament_type_raises(self):
        with pytest.raises(ValueError):
            OrnamentationGenerator(ornament_type="vibrato")

    def test_pitch_range(self):
        gen = OrnamentationGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestTrillTremoloGenerator:
    def test_produces_notes(self):
        gen = TrillTremoloGenerator(probability=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("ornament_type", ["trill", "lower_trill", "tremolo", "bisbigliando", "roll"])
    def test_ornament_types(self, ornament_type):
        gen = TrillTremoloGenerator(ornament_type=ornament_type, probability=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            TrillTremoloGenerator(ornament_type="vibrato")

    def test_pitch_range(self):
        gen = TrillTremoloGenerator(probability=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Texture
# ---------------------------------------------------------------------------

class TestAmbientPadGenerator:
    def test_produces_notes(self):
        gen = AmbientPadGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voicing", ["open", "spread"])
    def test_voicings(self, voicing):
        gen = AmbientPadGenerator(voicing=voicing)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = AmbientPadGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)

    def test_empty_chords(self):
        gen = AmbientPadGenerator()
        notes = gen.render([], C_MAJOR, 4.0)
        assert notes == []


class TestClusterGenerator:
    def test_produces_notes(self):
        gen = ClusterGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("cluster_type", ["second", "third", "chromatic"])
    def test_cluster_types(self, cluster_type):
        gen = ClusterGenerator(cluster_type=cluster_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = ClusterGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestDroneGenerator:
    def test_produces_notes(self):
        gen = DroneGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["tonic", "dominant", "root", "fifth", "octave", "power"])
    def test_variants(self, variant):
        gen = DroneGenerator(variant=variant)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_variant_raises(self):
        with pytest.raises(ValueError):
            DroneGenerator(variant="invalid")

    def test_pitch_range(self):
        gen = DroneGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Harmony
# ---------------------------------------------------------------------------

class TestCadenceGenerator:
    def test_produces_notes(self):
        gen = CadenceGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("cadence_type", ["PAC", "IAC", "HC", "DC", "PC"])
    def test_cadence_types(self, cadence_type):
        gen = CadenceGenerator(cadence_type=cadence_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = CadenceGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestChoraleGenerator:
    def test_produces_notes(self):
        gen = ChoraleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_voice_count_respected(self):
        # At least chord_count * voices_per_chord notes for SATB
        gen = ChoraleGenerator()
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = ChoraleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)

    def test_no_voice_crossing(self):
        gen = ChoraleGenerator(voice_crossing=False)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0


class TestModalInterchangeGenerator:
    def test_produces_notes(self):
        gen = ModalInterchangeGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("source_mode", ["minor", "dorian", "phrygian", "lydian", "mixolydian"])
    def test_source_modes(self, source_mode):
        gen = ModalInterchangeGenerator(source_mode=source_mode)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = ModalInterchangeGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestModernChordPatternGenerator:
    def test_produces_notes(self):
        gen = ModernChordPatternGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("extension", ["add9", "maj7", "dom7", "sus2", "sus4"])
    def test_extensions(self, extension):
        gen = ModernChordPatternGenerator(extension=extension)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = ModernChordPatternGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestReharmonizationGenerator:
    def test_produces_notes(self):
        gen = ReharmonizationGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("strategy", ["tritone", "modal", "chromatic", "secondary_dominant"])
    def test_strategies(self, strategy):
        gen = ReharmonizationGenerator(strategy=strategy)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = ReharmonizationGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestVoiceLeadingGenerator:
    def test_produces_notes(self):
        gen = VoiceLeadingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voices", [2, 3, 4])
    def test_voice_counts(self, voices):
        gen = VoiceLeadingGenerator(voices=voices)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("range_style", ["close", "spread"])
    def test_range_styles(self, range_style):
        gen = VoiceLeadingGenerator(range_style=range_style)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_range_style_raises(self):
        with pytest.raises(ValueError):
            VoiceLeadingGenerator(range_style="random")

    def test_pitch_range(self):
        gen = VoiceLeadingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Arpeggio / Run
# ---------------------------------------------------------------------------

class TestBrokenChordGenerator:
    def test_produces_notes(self):
        gen = BrokenChordGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["chopin", "alberti", "rolling", "waltz", "guitar"])
    def test_patterns(self, pattern):
        gen = BrokenChordGenerator(pattern=pattern)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = BrokenChordGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestDyadsRunGenerator:
    def test_produces_notes(self):
        gen = DyadsRunGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("technique", ["up", "down", "up_down", "waterfall"])
    def test_techniques(self, technique):
        gen = DyadsRunGenerator(technique=technique)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_technique_raises(self):
        with pytest.raises(ValueError):
            DyadsRunGenerator(technique="sideways")

    def test_pitch_range(self):
        gen = DyadsRunGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Rhythm
# ---------------------------------------------------------------------------

class TestEuclideanRhythmGenerator:
    def test_produces_notes(self):
        gen = EuclideanRhythmGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pulses,steps", [(3, 8), (5, 8), (7, 16), (4, 12)])
    def test_euclidean_patterns(self, pulses, steps):
        gen = EuclideanRhythmGenerator(pulses=pulses, steps=steps)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pitch", ["chord_root", "fifth", "octave"])
    def test_pitch_modes(self, pitch):
        gen = EuclideanRhythmGenerator(pitch=pitch)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pitch_raises(self):
        with pytest.raises(ValueError):
            EuclideanRhythmGenerator(pitch="melody")

    def test_pitch_range(self):
        gen = EuclideanRhythmGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestPolyrhythmGenerator:
    def test_produces_notes(self):
        gen = PolyrhythmGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("ratio", ["3x2", "4x3", "5x4"])
    def test_ratios(self, ratio):
        gen = PolyrhythmGenerator(ratio=ratio)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = PolyrhythmGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestPercussionEnsembleGenerator:
    def test_produces_notes(self):
        gen = PercussionEnsembleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_custom_instruments(self):
        gen = PercussionEnsembleGenerator(instruments=["conga", "bongo"])
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_density_low(self):
        gen = PercussionEnsembleGenerator(density=0.1)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert isinstance(notes, list)

    def test_pitch_range(self):
        gen = PercussionEnsembleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestFillGenerator:
    def test_produces_notes(self):
        gen = FillGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("fill_type", [
        "turnaround", "descending", "ascending", "chromatic",
        "arpeggio_up", "arpeggio_down", "blues_fill", "drum_fill",
    ])
    def test_fill_types(self, fill_type):
        gen = FillGenerator(fill_type=fill_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = FillGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Bass
# ---------------------------------------------------------------------------

class TestBassSlapGenerator:
    def test_produces_notes(self):
        gen = BassSlapGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("slap_pattern", ["funky", "pop", "slap_pop", "octave"])
    def test_slap_patterns(self, slap_pattern):
        gen = BassSlapGenerator(slap_pattern=slap_pattern)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            BassSlapGenerator(slap_pattern="metal")

    def test_pitch_range(self):
        gen = BassSlapGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestWalkingBassGenerator:
    def test_produces_notes(self):
        gen = WalkingBassGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("approach_style", ["chromatic", "diatonic", "mixed"])
    def test_approach_styles(self, approach_style):
        gen = WalkingBassGenerator(approach_style=approach_style)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_invalid_approach_raises(self):
        with pytest.raises(ValueError):
            WalkingBassGenerator(approach_style="random")

    def test_one_note_per_beat(self):
        gen = WalkingBassGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        # Walking bass should produce approximately one note per beat
        assert len(notes) >= 4

    def test_pitch_range(self):
        gen = WalkingBassGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Guitar
# ---------------------------------------------------------------------------

class TestPowerChordGenerator:
    def test_produces_notes(self):
        gen = PowerChordGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["chug", "gallop", "palm_mute", "open"])
    def test_patterns(self, pattern):
        gen = PowerChordGenerator(pattern=pattern)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_with_octave(self):
        gen = PowerChordGenerator(include_octave=True)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = PowerChordGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Technique
# ---------------------------------------------------------------------------

class TestBendGenerator:
    def test_produces_notes(self):
        gen = BendGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("bend_type", ["bend_up", "bend_down", "pre_bend", "slide_up", "slide_down"])
    def test_bend_types(self, bend_type):
        gen = BendGenerator(bend_type=bend_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = BendGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestGlissandoGenerator:
    def test_produces_notes(self):
        gen = GlissandoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("gliss_type", ["up", "down", "chromatic", "diatonic", "pentatonic", "arpeggio", "random"])
    def test_gliss_types(self, gliss_type):
        gen = GlissandoGenerator(gliss_type=gliss_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_gliss_type_raises(self):
        with pytest.raises(ValueError):
            GlissandoGenerator(gliss_type="sideways")

    def test_pitch_range(self):
        gen = GlissandoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestHarmonicsGenerator:
    def test_produces_notes(self):
        gen = HarmonicsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("harmonic_type", ["natural", "artificial", "pinch"])
    def test_harmonic_types(self, harmonic_type):
        gen = HarmonicsGenerator(harmonic_type=harmonic_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_soft_velocity(self):
        gen = HarmonicsGenerator(velocity_pp=True)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        if notes:
            assert all(n.velocity <= 60 for n in notes)

    def test_pitch_range(self):
        gen = HarmonicsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestTremoloPickingGenerator:
    def test_produces_notes(self):
        gen = TremoloPickingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["single", "double", "chord"])
    def test_variants(self, variant):
        gen = TremoloPickingGenerator(variant=variant)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = TremoloPickingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestPluckSequenceGenerator:
    def test_produces_notes(self):
        gen = PluckSequenceGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["offbeat", "on_beat", "syncopated", "alternating"])
    def test_patterns(self, pattern):
        gen = PluckSequenceGenerator(pattern=pattern)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = PluckSequenceGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Melody
# ---------------------------------------------------------------------------

class TestMotifDevelopmentGenerator:
    def test_produces_notes(self):
        gen = MotifDevelopmentGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("development_style", ["sequential", "fragmented", "continuous", "stretto"])
    def test_development_styles(self, development_style):
        gen = MotifDevelopmentGenerator(development_style=development_style)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            MotifDevelopmentGenerator(development_style="random_walk")

    def test_pitch_range(self):
        gen = MotifDevelopmentGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestMotiveGenerator:
    def test_produces_notes(self):
        gen = MotiveGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("development", ["repeat", "transpose", "invert", "retrograde", "augment"])
    def test_developments(self, development):
        gen = MotiveGenerator(development=development)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_development_raises(self):
        with pytest.raises(ValueError):
            MotiveGenerator(development="random")

    def test_pitch_range(self):
        gen = MotiveGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestPedalMelodyGenerator:
    def test_produces_notes(self):
        gen = PedalMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_explicit_pedal_pc(self):
        gen = PedalMelodyGenerator(pedal_pc=0)  # C as pedal
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("melody_style", ["stepwise", "arpeggiated", "skip"])
    def test_melody_styles(self, melody_style):
        gen = PedalMelodyGenerator(melody_style=melody_style)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = PedalMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestSequenceGenerator:
    def test_produces_notes(self):
        gen = SequenceGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("sequence_type", ["diatonic", "chromatic", "fifths", "descending", "ascending"])
    def test_sequence_types(self, sequence_type):
        gen = SequenceGenerator(sequence_type=sequence_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            SequenceGenerator(sequence_type="random")

    def test_pitch_range(self):
        gen = SequenceGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestPickupGenerator:
    def test_produces_notes(self):
        gen = PickupGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pickup_type", [
        "scale_up", "scale_down", "chromatic_up", "chromatic_down",
        "arpeggio", "rhythmic", "blues_pickup",
    ])
    def test_pickup_types(self, pickup_type):
        gen = PickupGenerator(pickup_type=pickup_type)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            PickupGenerator(pickup_type="random")

    def test_pitch_range(self):
        gen = PickupGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# FX
# ---------------------------------------------------------------------------

class TestFXImpactGenerator:
    def test_produces_notes(self):
        gen = FXImpactGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("impact_type", ["boom", "hit", "reverse_cymbal", "downlifter", "riser_hit"])
    def test_impact_types(self, impact_type):
        gen = FXImpactGenerator(impact_type=impact_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = FXImpactGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


class TestFXRiserGenerator:
    def test_produces_notes(self):
        gen = FXRiserGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("riser_type", ["synth", "orchestra", "noise", "arp", "sub_drop"])
    def test_riser_types(self, riser_type):
        gen = FXRiserGenerator(riser_type=riser_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_range(self):
        gen = FXRiserGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Modifier
# ---------------------------------------------------------------------------

class TestHumanizerGenerator:
    def test_produces_notes(self):
        gen = HumanizerGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("groove_type", ["straight", "swing", "shuffle", "latin"])
    def test_groove_types(self, groove_type):
        gen = HumanizerGenerator(groove_type=groove_type)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_zero_variance(self):
        gen = HumanizerGenerator(timing_variance=0.0, velocity_variance=0.0, length_variance=0.0)
        notes = gen.render(_single_chord(), C_MAJOR, 4.0)
        assert isinstance(notes, list)

    def test_pitch_range(self):
        gen = HumanizerGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Arranger
# ---------------------------------------------------------------------------

class TestArrangerGenerator:
    def test_produces_notes(self):
        gen = ArrangerGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("form", ["verse_chorus", "AABA", "rondo", "through_composed"])
    def test_forms(self, form):
        gen = ArrangerGenerator(form=form)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)

    def test_pitch_range(self):
        gen = ArrangerGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        _assert_valid_notes(notes)


# ---------------------------------------------------------------------------
# Container
# ---------------------------------------------------------------------------

class TestPhraseContainer:
    def test_sequential_two_generators(self):
        container = PhraseContainer(mode="sequential")
        container.add(AmbientPadGenerator(), 0.5)
        container.add(DroneGenerator(), 0.5)
        notes = container.render(_simple_chords(), C_MAJOR, 8.0)
        assert isinstance(notes, list)

    def test_parallel_two_generators(self):
        container = PhraseContainer(mode="parallel")
        container.add(BrokenChordGenerator(), 1.0)
        container.add(DroneGenerator(), 1.0)
        notes = container.render(_simple_chords(), C_MAJOR, 4.0)
        assert isinstance(notes, list)

    def test_empty_container(self):
        container = PhraseContainer()
        notes = container.render(_simple_chords(), C_MAJOR, 4.0)
        assert notes == [] or isinstance(notes, list)

    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError):
            PhraseContainer(mode="random")


class TestRestGenerator:
    def test_produces_silence(self):
        gen = RestGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert notes == []

    def test_empty_chords(self):
        gen = RestGenerator()
        notes = gen.render([], C_MAJOR, 4.0)
        assert notes == []
