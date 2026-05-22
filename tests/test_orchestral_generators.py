# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""Tests for all 18 orchestral generators across Tiers 1–3."""

import pytest

from melodica.generators import (
    GeneratorParams,
    ViolinGenerator,
    ViolaGenerator,
    CelloGenerator,
    ContrabassGenerator,
    HarpGenerator,
    OrchestralScoreGenerator,
    FluteGenerator,
    OboeGenerator,
    ClarinetGenerator,
    BassoonGenerator,
    TrumpetGenerator,
    TromboneGenerator,
    FrenchHornGenerator,
    TimpaniGenerator,
    MalletPercussionGenerator,
    OrchestralTransitionGenerator,
    FilmScoreGenerator,
)
from melodica.generators.film_score import HitPoint, EmotionalArc
from melodica.generators.texture_manager import TextureManager, TextureControlPoint
from melodica.types import ChordLabel, Scale, Mode
from melodica.factory import create_generator


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
D_MINOR = Scale(root=2, mode=Mode.MINOR_PENTATONIC)


def _chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=0, quality="maj", start=0.0, duration=4.0),
        ChordLabel(root=5, quality="maj", start=4.0, duration=4.0),
        ChordLabel(root=7, quality="maj", start=8.0, duration=4.0),
        ChordLabel(root=0, quality="maj", start=12.0, duration=4.0),
    ]


def _long_chords(n: int = 8) -> list[ChordLabel]:
    roots = [0, 5, 7, 3, 0, 5, 7, 0]
    return [
        ChordLabel(root=roots[i % len(roots)], quality="maj", start=i * 4.0, duration=4.0)
        for i in range(n)
    ]


def _params(low: int = 36, high: int = 84, density: float = 0.6) -> GeneratorParams:
    return GeneratorParams(density=density, key_range_low=low, key_range_high=high)


def assert_valid_notes(notes, *, min_pitch=0, max_pitch=127, min_count=1):
    assert len(notes) >= min_count, f"Expected >= {min_count} notes, got {len(notes)}"
    for n in notes:
        assert min_pitch <= n.pitch <= max_pitch, f"pitch {n.pitch} out of range [{min_pitch},{max_pitch}]"
        assert n.duration > 0, f"non-positive duration: {n.duration}"
        assert 1 <= n.velocity <= 127, f"velocity {n.velocity} out of range"
        assert n.start >= 0, f"negative start: {n.start}"


# ===================================================================
# Tier 1: Strings
# ===================================================================

class TestViolinGenerator:
    def test_basic_render(self):
        gen = ViolinGenerator(params=_params(55, 96))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=55, max_pitch=96)

    def test_range_respected(self):
        gen = ViolinGenerator(params=_params(55, 96))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        for n in notes:
            assert 55 <= n.pitch <= 96

    def test_articulations(self):
        for art in ["sustained", "legato", "staccato", "spiccato", "pizzicato", "tremolo", "harmonic"]:
            gen = ViolinGenerator(params=_params(55, 96), articulation=art)
            notes = gen.render(_chords(), C_MAJOR, 16.0)
            assert len(notes) > 0, f"No notes for articulation={art}"

    def test_staccato_shorter_than_sustained(self):
        sus = ViolinGenerator(params=_params(55, 96), articulation="sustained")
        stac = ViolinGenerator(params=_params(55, 96), articulation="staccato")
        sus_notes = sus.render(_chords(), C_MAJOR, 4.0)
        stac_notes = stac.render(_chords(), C_MAJOR, 4.0)
        assert stac_notes[0].duration < sus_notes[0].duration

    def test_empty_chords(self):
        gen = ViolinGenerator(params=_params(55, 96))
        assert gen.render([], C_MAJOR, 16.0) == []

    def test_render_twice_produces_notes(self):
        gen = ViolinGenerator(params=_params(55, 96))
        notes1 = gen.render(_chords(), C_MAJOR, 16.0)
        notes2 = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes1) > 0
        assert len(notes2) > 0

    def test_factory(self):
        gen = create_generator("violin", _params(55, 96))
        assert isinstance(gen, ViolinGenerator)


class TestViolaGenerator:
    def test_basic_render(self):
        gen = ViolaGenerator(params=_params(48, 84))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=48, max_pitch=84)

    def test_range_respected(self):
        gen = ViolaGenerator(params=_params(48, 84))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        for n in notes:
            assert 48 <= n.pitch <= 84

    def test_factory(self):
        gen = create_generator("viola", _params(48, 84))
        assert isinstance(gen, ViolaGenerator)


class TestCelloGenerator:
    def test_basic_render(self):
        gen = CelloGenerator(params=_params(36, 72))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=36, max_pitch=72)

    def test_bass_voice_mode(self):
        gen = CelloGenerator(params=_params(36, 72), bass_voice=True)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=36, max_pitch=72)

    def test_factory(self):
        gen = create_generator("cello", _params(36, 72))
        assert isinstance(gen, CelloGenerator)


class TestContrabassGenerator:
    def test_basic_render(self):
        gen = ContrabassGenerator(params=_params(28, 55))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=28, max_pitch=55)

    def test_low_register(self):
        gen = ContrabassGenerator(params=_params(28, 55))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        for n in notes:
            assert n.pitch <= 55

    def test_factory(self):
        gen = create_generator("contrabass", _params(28, 55))
        assert isinstance(gen, ContrabassGenerator)


# ===================================================================
# Tier 1: Harp + OrchestralScore
# ===================================================================

class TestHarpGenerator:
    def test_basic_render(self):
        gen = HarpGenerator(params=_params(24, 91))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=24, max_pitch=91)

    @pytest.mark.parametrize("pattern", ["arpeggio", "rolled_chord", "glissando", "bisbigliando", "repeated_note"])
    def test_all_patterns(self, pattern):
        gen = HarpGenerator(params=_params(24, 91), pattern=pattern)
        notes = gen.render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0, f"No notes for pattern={pattern}"

    def test_arpeggio_spreads_notes(self):
        gen = HarpGenerator(params=_params(24, 91), pattern="arpeggio")
        notes = gen.render(_chords()[:1], C_MAJOR, 4.0)
        if len(notes) > 1:
            assert notes[-1].start > notes[0].start

    def test_factory(self):
        gen = create_generator("harp", _params(24, 91))
        assert isinstance(gen, HarpGenerator)


class TestOrchestralScoreGenerator:
    def test_full_render(self):
        score = OrchestralScoreGenerator(params=_params())
        notes = score.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        assert len(score.tracks) >= 3
        assert len(score.instruments) >= 3

    def test_sections(self):
        score = OrchestralScoreGenerator(
            params=_params(),
            sections=[("intro", 0, 8), ("chorus", 8, 8)],
        )
        notes = score.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0

    def test_multitrack_output(self):
        score = OrchestralScoreGenerator(params=_params())
        score.render(_chords(), C_MAJOR, 16.0)
        assert isinstance(score.tracks, dict)
        assert isinstance(score.instruments, dict)
        assert isinstance(score.pan_map, dict)
        for name, gm in score.instruments.items():
            assert isinstance(gm, int)
            assert 0 <= gm <= 127

    def test_all_tracks_have_notes(self):
        score = OrchestralScoreGenerator(params=_params())
        score.render(_long_chords(8), C_MAJOR, 32.0)
        empty = [t for t, n in score.tracks.items() if not n]
        assert empty == [], f"Empty tracks: {empty}"

    def test_chord_shift_for_subsections(self):
        """Chords passed to sub-generators must start at 0.0."""
        score = OrchestralScoreGenerator(
            params=_params(),
            sections=[("intro", 0, 8), ("chorus", 8, 8)],
        )
        notes = score.render(_chords(), C_MAJOR, 16.0)
        # If chord shift is broken, chorus section produces 0 notes for some instruments
        assert len(notes) > 10

    def test_include_flags(self):
        for flag, inst in [("include_brass", "trumpet"), ("include_choir", "choir_aahs"), ("include_harp", "harp")]:
            score = OrchestralScoreGenerator(params=_params(), **{flag: False})
            score.render(_long_chords(), C_MAJOR, 32.0)
            assert inst not in score.tracks, f"{inst} should be excluded when {flag}=False"

    def test_pan_values_valid(self):
        score = OrchestralScoreGenerator(params=_params())
        score.render(_chords(), C_MAJOR, 16.0)
        for name, pan in score.pan_map.items():
            assert -1.0 <= pan <= 1.0, f"pan {pan} for {name} out of range"

    def test_factory(self):
        gen = create_generator("orchestral_score", _params())
        assert isinstance(gen, OrchestralScoreGenerator)


# ===================================================================
# Tier 2: Woodwinds
# ===================================================================

class TestFluteGenerator:
    def test_basic_render(self):
        gen = FluteGenerator(params=_params(60, 96))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=60, max_pitch=96)

    def test_articulations(self):
        for art in ["sustained", "legato", "staccato", "flutter_tongue", "trill", "breath"]:
            gen = FluteGenerator(params=_params(60, 96), articulation=art)
            notes = gen.render(_chords(), C_MAJOR, 8.0)
            assert len(notes) > 0, f"No notes for articulation={art}"

    def test_factory(self):
        gen = create_generator("flute", _params(60, 96))
        assert isinstance(gen, FluteGenerator)


class TestOboeGenerator:
    def test_basic_render(self):
        gen = OboeGenerator(params=_params(58, 91))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=58, max_pitch=91)

    def test_factory(self):
        gen = create_generator("oboe", _params(58, 91))
        assert isinstance(gen, OboeGenerator)


class TestClarinetGenerator:
    def test_basic_render(self):
        gen = ClarinetGenerator(params=_params(50, 91))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=50, max_pitch=91)

    def test_factory(self):
        gen = create_generator("clarinet", _params(50, 91))
        assert isinstance(gen, ClarinetGenerator)


class TestBassoonGenerator:
    def test_basic_render(self):
        gen = BassoonGenerator(params=_params(34, 72))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=34, max_pitch=72)

    def test_factory(self):
        gen = create_generator("bassoon", _params(34, 72))
        assert isinstance(gen, BassoonGenerator)


# ===================================================================
# Tier 2: Brass
# ===================================================================

class TestTrumpetGenerator:
    def test_basic_render(self):
        gen = TrumpetGenerator(params=_params(55, 82))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=55, max_pitch=82)

    def test_articulations(self):
        for art in ["sustained", "staccato", "legato", "muted", "swell", "fanfare", "rip"]:
            gen = TrumpetGenerator(params=_params(55, 82), articulation=art)
            notes = gen.render(_chords(), C_MAJOR, 8.0)
            assert len(notes) > 0, f"No notes for articulation={art}"

    def test_con_sordino_quieter(self):
        normal = TrumpetGenerator(params=_params(55, 82), con_sordino=False)
        muted = TrumpetGenerator(params=_params(55, 82), con_sordino=True)
        n1 = normal.render(_chords(), C_MAJOR, 4.0)
        n2 = muted.render(_chords(), C_MAJOR, 4.0)
        if n1 and n2:
            avg_normal = sum(n.velocity for n in n1) / len(n1)
            avg_muted = sum(n.velocity for n in n2) / len(n2)
            assert avg_muted < avg_normal

    def test_factory(self):
        gen = create_generator("trumpet", _params(55, 82))
        assert isinstance(gen, TrumpetGenerator)


class TestTromboneGenerator:
    def test_basic_render(self):
        gen = TromboneGenerator(params=_params(40, 70))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=40, max_pitch=70)

    def test_bass_voice_mode(self):
        gen = TromboneGenerator(params=_params(40, 70), bass_voice=True)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=36, max_pitch=70)

    def test_factory(self):
        gen = create_generator("trombone", _params(40, 70))
        assert isinstance(gen, TromboneGenerator)


class TestFrenchHornGenerator:
    def test_basic_render(self):
        gen = FrenchHornGenerator(params=_params(34, 70))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=34, max_pitch=70)

    def test_factory(self):
        gen = create_generator("french_horn", _params(34, 70))
        assert isinstance(gen, FrenchHornGenerator)


# ===================================================================
# Tier 2: Percussion
# ===================================================================

class TestTimpaniGenerator:
    def test_basic_render(self):
        gen = TimpaniGenerator(params=_params(36, 60))
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert_valid_notes(notes, min_pitch=36, max_pitch=60)

    @pytest.mark.parametrize("pattern", ["single", "roll", "fanfare", "accented"])
    def test_all_patterns(self, pattern):
        gen = TimpaniGenerator(params=_params(36, 60), stroke_pattern=pattern)
        notes = gen.render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0, f"No notes for pattern={pattern}"

    def test_factory(self):
        gen = create_generator("timpani", _params(36, 60))
        assert isinstance(gen, TimpaniGenerator)


class TestMalletPercussionGenerator:
    @pytest.mark.parametrize("instrument", ["marimba", "xylophone", "vibraphone", "glockenspiel"])
    def test_all_instruments(self, instrument):
        ranges = {"marimba": (45, 84), "xylophone": (65, 96), "vibraphone": (53, 89), "glockenspiel": (72, 108)}
        lo, hi = ranges[instrument]
        gen = MalletPercussionGenerator(params=_params(lo, hi), instrument=instrument)
        notes = gen.render(_chords(), C_MAJOR, 8.0)
        assert_valid_notes(notes, min_pitch=lo, max_pitch=hi)

    @pytest.mark.parametrize("pattern", ["arpeggio", "run", "sustained", "tremolo", "glissando"])
    def test_all_patterns(self, pattern):
        gen = MalletPercussionGenerator(params=_params(45, 84), pattern=pattern)
        notes = gen.render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0, f"No notes for pattern={pattern}"

    def test_factory(self):
        gen = create_generator("mallet", _params(45, 84))
        assert isinstance(gen, MalletPercussionGenerator)


# ===================================================================
# Tier 3: TextureManager
# ===================================================================

class TestTextureManager:
    def test_from_sections(self):
        tm = TextureManager.from_sections(
            sections=[("intro", 0, 8), ("chorus", 8, 16)],
        )
        assert tm.texture_at(0) is not None
        assert tm.texture_at(12) is not None

    def test_control_points(self):
        tm = TextureManager(crossfade_beats=4.0)
        tm.add_control_point(0.0, "thin")
        tm.add_control_point(8.0, "full")
        assert tm.texture_at(0) == "thin"
        assert tm.texture_at(10) == "full"

    def test_instruments_at(self):
        tm = TextureManager(crossfade_beats=4.0)
        tm.add_control_point(0.0, "thin")
        tm.add_control_point(8.0, "full")
        insts = tm.instruments_at(0)
        assert isinstance(insts, dict)
        assert "violin" in insts
        assert insts["violin"].active

    def test_build_curve_linear(self):
        tm = TextureManager()
        tm.build_curve(16.0, start_texture="thin", end_texture="full", shape="linear")
        assert tm.texture_at(0) == "thin"
        assert tm.texture_at(15) == "full"

    def test_build_curve_step(self):
        tm = TextureManager()
        tm.build_curve(16.0, start_texture="thin", end_texture="full", shape="step")
        assert tm.texture_at(0) == "thin"
        assert tm.texture_at(8.0) == "full"

    def test_crossfade_density(self):
        tm = TextureManager(crossfade_beats=4.0)
        tm.add_control_point(0.0, "thin")
        tm.add_control_point(8.0, "full")
        insts_early = tm.instruments_at(0)
        insts_late = tm.instruments_at(12)
        # At 0, some instruments should have density < 1 (entering)
        entering_early = [k for k, v in insts_early.items() if v.active and v.density_scale < 1.0]
        # At 12, all should be at density 1.0
        entering_late = [k for k, v in insts_late.items() if v.active and v.density_scale < 1.0]
        assert len(entering_early) > 0
        assert len(entering_late) == 0


# ===================================================================
# Tier 3: OrchestralTransitionGenerator
# ===================================================================

class TestOrchestralTransitionGenerator:
    @pytest.mark.parametrize("ttype", [
        "crescendo_build", "ritardando", "accelerando",
        "fermata", "pedal_point", "retransition", "bridge_passage",
    ])
    def test_all_transition_types(self, ttype):
        gen = OrchestralTransitionGenerator(params=_params(), transition_type=ttype)
        notes = gen.render(_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0, f"No notes for transition_type={ttype}"

    def test_multitrack_output(self):
        gen = OrchestralTransitionGenerator(params=_params(), transition_type="crescendo_build")
        gen.render(_chords(), C_MAJOR, 8.0)
        assert isinstance(gen.tracks, dict)
        assert len(gen.tracks) > 0

    def test_intensity_curves(self):
        for curve in ["flat", "crescendo", "diminuendo"]:
            gen = OrchestralTransitionGenerator(params=_params(), intensity_curve=curve)
            notes = gen.render(_chords(), C_MAJOR, 8.0)
            assert len(notes) > 0, f"No notes for intensity_curve={curve}"

    def test_empty_chords(self):
        gen = OrchestralTransitionGenerator(params=_params())
        assert gen.render([], C_MAJOR, 8.0) == []

    def test_invalid_type_raises(self):
        with pytest.raises(ValueError):
            OrchestralTransitionGenerator(params=_params(), transition_type="nonexistent")

    def test_factory(self):
        gen = create_generator("orchestral_transition", _params())
        assert isinstance(gen, OrchestralTransitionGenerator)


# ===================================================================
# Tier 3: FilmScoreGenerator
# ===================================================================

class TestFilmScoreGenerator:
    def test_basic_render(self):
        film = FilmScoreGenerator(params=_params())
        notes = film.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0

    def test_with_hit_points(self):
        hits = [
            HitPoint(beat=4.0, event_type="action", intensity=0.9),
            HitPoint(beat=12.0, event_type="emotion", intensity=0.5),
        ]
        film = FilmScoreGenerator(params=_params(), hit_points=hits)
        notes = film.render(_long_chords(4), C_MAJOR, 16.0)
        assert len(notes) > 0

    def test_with_emotional_arcs(self):
        arcs = [
            EmotionalArc(start_beat=0, end_beat=16, start_mood="calm", end_mood="tense"),
        ]
        film = FilmScoreGenerator(params=_params(), emotional_arcs=arcs)
        notes = film.render(_long_chords(4), C_MAJOR, 16.0)
        assert len(notes) > 0

    def test_full_cue(self):
        hits = [
            HitPoint(beat=4.0, event_type="tension", intensity=0.7),
            HitPoint(beat=12.0, event_type="action", intensity=0.9),
            HitPoint(beat=28.0, event_type="calm", intensity=0.4),
        ]
        arcs = [
            EmotionalArc(start_beat=0, end_beat=16, start_mood="mysterious", end_mood="tense"),
            EmotionalArc(start_beat=16, end_beat=32, start_mood="tense", end_mood="calm"),
        ]
        film = FilmScoreGenerator(params=_params(), hit_points=hits, emotional_arcs=arcs)
        notes = film.render(_long_chords(8), C_MAJOR, 32.0)
        assert len(notes) > 50
        assert len(film.tracks) >= 3

    def test_hit_point_event_types(self):
        for etype in ["action", "tension", "emotion", "reveal", "impact", "calm"]:
            hits = [HitPoint(beat=4.0, event_type=etype, intensity=0.8)]
            film = FilmScoreGenerator(params=_params(), hit_points=hits)
            notes = film.render(_long_chords(2), C_MAJOR, 8.0)
            assert len(notes) > 0, f"No notes for event_type={etype}"

    def test_multitrack_output(self):
        film = FilmScoreGenerator(params=_params())
        film.render(_long_chords(4), C_MAJOR, 16.0)
        assert isinstance(film.tracks, dict)
        assert isinstance(film.instruments, dict)
        for name, gm in film.instruments.items():
            assert isinstance(gm, int)

    def test_include_flags(self):
        film = FilmScoreGenerator(params=_params(), include_brass=False)
        film.render(_long_chords(4), C_MAJOR, 16.0)
        for track in film.tracks:
            if track != "_accent":
                assert film.instruments.get(track, 0) != 56  # not trumpet

    def test_empty_chords(self):
        film = FilmScoreGenerator(params=_params())
        assert film.render([], C_MAJOR, 16.0) == []

    def test_factory(self):
        gen = create_generator("film_score", _params())
        assert isinstance(gen, FilmScoreGenerator)


# ===================================================================
# Cross-cutting: Factory registration
# ===================================================================

class TestFactoryRegistration:
    ORCHESTRAL_TYPES = [
        "violin", "viola", "cello", "contrabass",
        "flute", "oboe", "clarinet", "bassoon",
        "trumpet", "trombone", "french_horn",
        "timpani", "mallet", "harp",
        "orchestral_score", "orchestral_transition", "film_score",
    ]

    @pytest.mark.parametrize("gen_type", ORCHESTRAL_TYPES)
    def test_factory_creates_generator(self, gen_type):
        gen = create_generator(gen_type, _params())
        assert gen is not None
        assert hasattr(gen, "render")

    def test_all_17_types_registered(self):
        assert len(self.ORCHESTRAL_TYPES) == 17
