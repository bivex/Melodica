"""
tests/test_audit_coverage.py — Coverage tests for architectural audit fixes (2026-05-29).

Covers:
  #1  PhraseInstance.render() key type extraction
  #2  Rhythm library aliases + dynamic presets
  #3  SECTION_ENERGY dict copy (not aliased)
  #5  Generator validation (10 files, 11 locations)
  #8  STYLE_INSTRUMENTS dead code removed
  #10 NoteInfo velocity validation
  #11 electronic_drums dead code removed + type hint fix
  #13 MixingDesk exponential fade
  #14 MixingDesk velocity cap at 127
"""

import math
import pytest

from melodica.types import (
    ChordLabel,
    KeyLabel,
    Mode,
    MusicTimeline,
    NoteInfo,
    PhraseInstance,
    Quality,
    Scale,
    SECTION_ENERGY,
    SECTION_ROLE_ENERGY,
    StaticPhrase,
)
from melodica.rhythm import RhythmEvent
from melodica.rhythm.library import (
    DYNAMIC_RHYTHM_REGISTRY,
    RHYTHM_LIBRARY,
    get_rhythm,
    StaticRhythmGenerator,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
_SIMPLE_CHORDS = [
    ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
    ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
]


# ---------------------------------------------------------------------------
# #10 — NoteInfo velocity validation
# ---------------------------------------------------------------------------

class TestNoteInfoVelocityValidation:
    def test_valid_velocity_zero(self):
        n = NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=0)
        assert n.velocity == 0

    def test_valid_velocity_max(self):
        n = NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=127)
        assert n.velocity == 127

    def test_velocity_too_high(self):
        with pytest.raises(ValueError, match="velocity"):
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=128)

    def test_velocity_negative(self):
        with pytest.raises(ValueError, match="velocity"):
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=-1)

    def test_velocity_126_ok(self):
        n = NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=126)
        assert n.velocity == 126


# ---------------------------------------------------------------------------
# #3 — SECTION_ENERGY is a copy, not an alias
# ---------------------------------------------------------------------------

class TestSectionEnergyCopy:
    def test_not_same_object(self):
        assert SECTION_ENERGY is not SECTION_ROLE_ENERGY

    def test_same_content(self):
        assert dict(SECTION_ENERGY) == dict(SECTION_ROLE_ENERGY)

    def test_mutation_isolation(self):
        from melodica.types import SectionRole
        original = SECTION_ROLE_ENERGY.get(SectionRole.VERSE)
        try:
            SECTION_ENERGY[SectionRole.VERSE] = 999.0
            assert SECTION_ROLE_ENERGY[SectionRole.VERSE] == original
        finally:
            SECTION_ENERGY[SectionRole.VERSE] = original


# ---------------------------------------------------------------------------
# #1 — PhraseInstance.render() key type extraction
# ---------------------------------------------------------------------------

class TestPhraseInstanceKeyExtraction:
    def test_render_with_scale(self):
        """Passing Scale directly should work (auto-wrapped in MusicTimeline)."""
        from melodica.generators.melody import MelodyGenerator
        gen = MelodyGenerator()
        pi = PhraseInstance(generator=gen)
        notes = pi.render(_SIMPLE_CHORDS, C_MAJOR, 8.0)
        assert isinstance(notes, list)
        assert len(notes) > 0

    def test_render_with_timeline(self):
        """Passing MusicTimeline should extract Scale via get_key_at(0.0)."""
        from melodica.generators.melody import MelodyGenerator
        gen = MelodyGenerator()
        pi = PhraseInstance(generator=gen)
        timeline = MusicTimeline(
            chords=_SIMPLE_CHORDS,
            keys=[KeyLabel(scale=C_MAJOR, start=0, duration=8)],
        )
        notes = pi.render(_SIMPLE_CHORDS, timeline, 8.0)
        assert isinstance(notes, list)
        assert len(notes) > 0

    def test_render_static_ignores_timeline(self):
        static_notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80)]
        pi = PhraseInstance(static=StaticPhrase(notes=static_notes))
        notes = pi.render(_SIMPLE_CHORDS, C_MAJOR, 4.0)
        assert len(notes) == 1
        assert notes[0].pitch == 60


# ---------------------------------------------------------------------------
# #2 — Rhythm library aliases
# ---------------------------------------------------------------------------

class TestRhythmLibraryAliases:
    @pytest.mark.parametrize("alias", [
        "gavotte",
        "shamisen_jongara",
        "jrpg_battle",
        "touhou_boss_theme",
        "koto_sakura_sakura",
        "noh_taiko_mitsuji",
        "bon_odori",
        "shakuhachi_ma",
        "gagaku_kakko_pattern",
        "yatai_bayashi",
        "city_pop_groove",
        "jrock_gallop",
        "visual_kei_tremolo",
        "alberti_bass",
        "bolero_ravel",
        "hc_chip_8bit_loop",
        "hc_arcade_simple",
        "hc_fever_mode",
        "lofi_lazy_hats",
        "downtempo_piano_stabs",
    ])
    def test_alias_exists(self, alias):
        assert alias in RHYTHM_LIBRARY, f"Alias {alias!r} not in RHYTHM_LIBRARY"
        assert len(RHYTHM_LIBRARY[alias]) > 0

    @pytest.mark.parametrize("alias,target", [
        ("gavotte", "cls_gavotte_2_2"),
        ("alberti_bass", "cls_alberti_8th"),
        ("city_pop_groove", "jp_city_pop_groove_16th"),
    ])
    def test_alias_points_to_target(self, alias, target):
        if target in RHYTHM_LIBRARY:
            assert RHYTHM_LIBRARY[alias] is RHYTHM_LIBRARY[target]


class TestRhythmLibraryDynamicPresets:
    @pytest.mark.parametrize("name", [
        "markov",
        "probabilistic",
        "markov:syncopated",
        "markov:swing",
        "markov:ballad",
        "markov:slow",
        "markov:dirge",
        "probabilistic:dense",
        "probabilistic:sparse",
        "arpeggio:slow",
    ])
    def test_dynamic_preset_registered(self, name):
        assert name in DYNAMIC_RHYTHM_REGISTRY, f"{name!r} not in DYNAMIC_RHYTHM_REGISTRY"

    def test_get_rhythm_returns_generator(self):
        gen = get_rhythm("markov:slow")
        assert hasattr(gen, "generate")

    def test_get_rhythm_static_preset(self):
        gen = get_rhythm("straight_quarters")
        assert isinstance(gen, StaticRhythmGenerator)
        events = gen.generate(4.0)
        assert len(events) > 0

    def test_get_rhythm_missing_falls_back(self):
        gen = get_rhythm("nonexistent_preset_xyz")
        assert isinstance(gen, StaticRhythmGenerator)
        events = gen.generate(4.0)
        assert len(events) > 0  # falls back to straight_quarters


# ---------------------------------------------------------------------------
# #5 — Generator validation (invalid params raise ValueError)
# ---------------------------------------------------------------------------

class TestGeneratorValidation:
    def _chords_and_key(self):
        return _SIMPLE_CHORDS, C_MAJOR, 8.0

    def test_nebula_invalid_variant(self):
        from melodica.generators.nebula import NebulaGenerator
        gen = NebulaGenerator(variant="nonexistent")
        with pytest.raises(ValueError, match="variant"):
            gen.render(*self._chords_and_key())

    @pytest.mark.parametrize("variant", ["cloud", "cascade", "swell", "granular", "stasis"])
    def test_nebula_valid_variants(self, variant):
        from melodica.generators.nebula import NebulaGenerator
        gen = NebulaGenerator(variant=variant)
        notes = gen.render(*self._chords_and_key())
        assert len(notes) > 0

    def test_brass_section_invalid_articulation(self):
        from melodica.generators.brass_section import BrassSectionGenerator
        gen = BrassSectionGenerator(articulation="nonexistent")
        with pytest.raises(ValueError, match="articulation"):
            gen.render(*self._chords_and_key())

    def test_supersaw_pad_invalid_variant(self):
        from melodica.generators.supersaw_pad import SupersawPadGenerator
        gen = SupersawPadGenerator(variant="nonexistent")
        with pytest.raises(ValueError, match="variant"):
            gen.render(*self._chords_and_key())

    def test_fx_riser_invalid_type(self):
        from melodica.generators.fx_riser import FXRiserGenerator
        gen = FXRiserGenerator(riser_type="nonexistent")
        with pytest.raises(ValueError, match="riser_type"):
            gen.render(*self._chords_and_key())

    def test_fx_impact_invalid_type(self):
        from melodica.generators.fx_impact import FXImpactGenerator
        gen = FXImpactGenerator(impact_type="nonexistent")
        with pytest.raises(ValueError, match="impact_type"):
            gen.render(*self._chords_and_key())

    def test_horror_dissonance_invalid_variant(self):
        from melodica.generators.horror_dissonance import HorrorDissonanceGenerator
        gen = HorrorDissonanceGenerator(variant="nonexistent")
        with pytest.raises(ValueError, match="variant"):
            gen.render(*self._chords_and_key())

    def test_beat_repeat_invalid_type(self):
        from melodica.generators.beat_repeat import BeatRepeatGenerator
        gen = BeatRepeatGenerator(repeat_type="nonexistent")
        with pytest.raises(ValueError, match="repeat_type"):
            gen.render(*self._chords_and_key())

    def test_four_on_floor_invalid_variant(self):
        from melodica.generators.four_on_floor import FourOnFloorGenerator
        gen = FourOnFloorGenerator(variant="nonexistent")
        with pytest.raises(ValueError, match="variant"):
            gen.render(*self._chords_and_key())

    def test_bend_invalid_type(self):
        from melodica.generators.bend import BendGenerator
        gen = BendGenerator(bend_type="nonexistent")
        with pytest.raises(ValueError, match="bend_type"):
            gen.render(*self._chords_and_key())

    def test_ethnic_world_invalid_instrument_init(self):
        from melodica.generators.ethnic_world import EthnicWorldGenerator
        with pytest.raises(ValueError, match="instrument"):
            EthnicWorldGenerator(instrument="nonexistent")


# ---------------------------------------------------------------------------
# #8 — STYLE_INSTRUMENTS removed from midi.py
# ---------------------------------------------------------------------------

class TestDeadCodeRemoved:
    def test_style_instruments_not_in_midi(self):
        import melodica.midi as midi_mod
        assert not hasattr(midi_mod, "STYLE_INSTRUMENTS"), "STYLE_INSTRUMENTS should be removed"


# ---------------------------------------------------------------------------
# #11 — electronic_drums: dead code removed, type hint fixed
# ---------------------------------------------------------------------------

class TestElectronicDrumsCleanup:
    def test_no_lowercase_any_type_hint(self):
        """groove_template should use proper type, not bare `any`."""
        import inspect
        from melodica.generators.electronic_drums import ElectronicDrumsGenerator
        src = inspect.getsource(ElectronicDrumsGenerator)
        # Check that 'groove_template: any' (lowercase) is not present
        assert "groove_template: any" not in src, "groove_template should not use bare 'any'"

    def test_class_length_reasonable(self):
        """Dead code (112 lines) should be removed — class should be < 800 lines."""
        import inspect
        from melodica.generators.electronic_drums import ElectronicDrumsGenerator
        src = inspect.getsource(ElectronicDrumsGenerator)
        line_count = src.count("\n")
        assert line_count < 800, f"ElectronicDrumsGenerator has {line_count} lines, expected < 800 after dead code removal"


# ---------------------------------------------------------------------------
# #13 — MixingDesk fade is exponential, not linear
# ---------------------------------------------------------------------------

class TestMixingDeskExponentialFade:
    def test_fade_is_exponential(self):
        from melodica.shorts_mixing import MixingDesk
        desk = MixingDesk()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100),
            NoteInfo(pitch=60, start=1.0, duration=1.0, velocity=100),
            NoteInfo(pitch=60, start=2.0, duration=1.0, velocity=100),
            NoteInfo(pitch=60, start=3.0, duration=1.0, velocity=100),
        ]
        tracks = {"bass": notes}
        faded = desk.apply_fade_loop_end(tracks, loop_start_beat=0.0, fade_beats=4.0)
        faded_notes = faded["bass"]
        # With exponential decay: factor = exp(-3 * pos / fade_beats)
        # pos=0: factor=1.0, pos=1: exp(-0.75)≈0.472, pos=2: exp(-1.5)≈0.223, pos=3: exp(-2.25)≈0.105
        # Verify decay is faster than linear
        v0 = faded_notes[0].velocity
        v1 = faded_notes[1].velocity
        v3 = faded_notes[3].velocity
        # Exponential: v3 should be much less than linear prediction (v0 * 0.25 = 25)
        assert v3 < v0 * 0.25, f"Fade should be exponential: v0={v0}, v3={v3}"

    def test_fade_drops_silent_notes(self):
        from melodica.shorts_mixing import MixingDesk
        desk = MixingDesk()
        notes = [NoteInfo(pitch=60, start=10.0, duration=1.0, velocity=100)]
        tracks = {"bass": notes}
        faded = desk.apply_fade_loop_end(tracks, loop_start_beat=0.0, fade_beats=2.0)
        # pos=10, fade=2: factor = exp(-3*10/2) = exp(-15) ≈ 3e-7 < 0.01
        assert len(faded["bass"]) == 0


# ---------------------------------------------------------------------------
# #14 — MixingDesk velocity cap at 127
# ---------------------------------------------------------------------------

class TestMixingDeskVelocityCap:
    def test_velocity_caps_at_127(self):
        from melodica.shorts_mixing import MixingDesk
        desk = MixingDesk(track_gains={"lead": 2.0})  # 2x gain
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100)]
        tracks = {"lead": notes}
        sections = [("Hook", 1, [])]
        mixed = desk.apply_mixing(tracks, sections, bpm=120)
        assert mixed["lead"][0].velocity <= 127

    def test_velocity_never_zero(self):
        from melodica.shorts_mixing import MixingDesk
        desk = MixingDesk(track_gains={"pad": 0.001})
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=1)]
        tracks = {"pad": notes}
        sections = [("Loop", 1, [])]
        mixed = desk.apply_mixing(tracks, sections, bpm=120)
        assert mixed["pad"][0].velocity >= 1

    def test_auto_gain_low_register(self):
        from melodica.shorts_mixing import MixingDesk
        gain = MixingDesk._auto_gain([NoteInfo(pitch=36, start=0, duration=1, velocity=80)])
        assert gain > 1.0  # low register gets boost

    def test_auto_gain_high_register(self):
        from melodica.shorts_mixing import MixingDesk
        gain = MixingDesk._auto_gain([NoteInfo(pitch=96, start=0, duration=1, velocity=80)])
        assert gain < 1.0  # high register gets attenuation

    def test_auto_gain_empty(self):
        from melodica.shorts_mixing import MixingDesk
        gain = MixingDesk._auto_gain([])
        assert gain == 1.0
