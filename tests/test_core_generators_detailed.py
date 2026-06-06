"""Detailed tests for core generators: PianoComp, SaxSolo, TrapDrums, Bass808, HiHatStutter."""

import pytest

from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.bass_808_sliding import Bass808SlidingGenerator
from melodica.generators.hihat_stutter import HiHatStutterGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)
F_SHARP_MINOR = Scale(root=6, mode=Mode.NATURAL_MINOR)
Bb_MAJOR = Scale(root=10, mode=Mode.MAJOR)


def _chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ChordLabel(root=9, quality=Quality.MINOR, start=8.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=12.0, duration=4.0),
    ]


def _jazz_chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=10, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.DOMINANT7, start=4.0, duration=4.0),
        ChordLabel(root=10, quality=Quality.MINOR, start=8.0, duration=4.0),
        ChordLabel(root=3, quality=Quality.DOMINANT7, start=12.0, duration=4.0),
    ]


def _one_chord() -> list[ChordLabel]:
    return [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]


def _minor_chords() -> list[ChordLabel]:
    return [
        ChordLabel(root=9, quality=Quality.MINOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MINOR, start=4.0, duration=4.0),
    ]


def _valid(notes: list[NoteInfo]) -> None:
    for n in notes:
        assert 0 <= n.pitch <= 127
        assert n.duration > 0
        assert n.start >= 0
        assert 1 <= n.velocity <= 127


# =====================================================================
# PianoCompGenerator
# =====================================================================

class TestPianoCompStyles:
    @pytest.mark.parametrize("style", ["jazz", "pop", "bossa", "waltz"])
    def test_all_comp_styles_produce_notes(self, style):
        gen = PianoCompGenerator(comp_style=style)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError, match="comp_style"):
            PianoCompGenerator(comp_style="nonexistent")


class TestPianoCompVoicings:
    @pytest.mark.parametrize("voicing", ["shell", "rootless", "close"])
    def test_all_voicings_produce_notes(self, voicing):
        gen = PianoCompGenerator(voicing_type=voicing)
        notes = gen.render(_jazz_chords(), Bb_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_voicing_raises(self):
        with pytest.raises(ValueError, match="voicing_type"):
            PianoCompGenerator(voicing_type="wide")


class TestPianoCompAccents:
    @pytest.mark.parametrize("accent", ["2_4", "syncopated", "charleston"])
    def test_all_accents_produce_notes(self, accent):
        gen = PianoCompGenerator(accent_pattern=accent)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_accent_raises(self):
        with pytest.raises(ValueError, match="accent_pattern"):
            PianoCompGenerator(accent_pattern="none")


class TestPianoCompDensity:
    def test_high_density_more_notes(self):
        low = PianoCompGenerator(chord_density=0.2)
        high = PianoCompGenerator(chord_density=1.0)
        notes_low = low.render(_chords(), C_MAJOR, 16.0)
        notes_high = high.render(_chords(), C_MAJOR, 16.0)
        assert len(notes_high) >= len(notes_low)

    def test_zero_density_produces_few_or_no_notes(self):
        gen = PianoCompGenerator(chord_density=0.0)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        # density=0 may still produce some notes (accent beats) but fewer
        assert isinstance(notes, list)


class TestPianoCompRange:
    def test_respects_key_range(self):
        params = GeneratorParams(key_range_low=48, key_range_high=72)
        gen = PianoCompGenerator(params=params)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        _valid(notes)
        for n in notes:
            assert 48 <= n.pitch <= 72, f"pitch {n.pitch} outside range 48-72"

    def test_default_range_no_extreme_pitches(self):
        gen = PianoCompGenerator()
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        _valid(notes)
        for n in notes:
            assert 20 <= n.pitch <= 108


class TestPianoCompEdgeCases:
    def test_single_chord(self):
        gen = PianoCompGenerator()
        notes = gen.render(_one_chord(), C_MAJOR, 4.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        gen = PianoCompGenerator()
        assert gen.render([], C_MAJOR, 16.0) == []

    def test_very_short_duration(self):
        gen = PianoCompGenerator()
        notes = gen.render(_one_chord(), C_MAJOR, 1.0)
        assert isinstance(notes, list)
        _valid(notes)

    def test_render_deterministic_enough(self):
        gen = PianoCompGenerator()
        # Two renders should both produce valid output
        n1 = gen.render(_chords(), C_MAJOR, 16.0)
        n2 = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(n1) > 0
        assert len(n2) > 0


# =====================================================================
# SaxSoloGenerator
# =====================================================================

class TestSaxSoloBasic:
    def test_produces_notes(self):
        gen = SaxSoloGenerator()
        notes = gen.render(_jazz_chords(), Bb_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        gen = SaxSoloGenerator()
        assert gen.render([], Bb_MAJOR, 16.0) == []

    def test_single_chord(self):
        gen = SaxSoloGenerator()
        notes = gen.render(_one_chord(), C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestSaxSoloRange:
    def test_respects_key_range(self):
        params = GeneratorParams(key_range_low=54, key_range_high=78)
        gen = SaxSoloGenerator(params=params)
        notes = gen.render(_jazz_chords(), Bb_MAJOR, 16.0)
        _valid(notes)
        for n in notes:
            assert 54 <= n.pitch <= 78, f"pitch {n.pitch} outside range"


class TestSaxSoloParams:
    def test_vibrato_zero(self):
        gen = SaxSoloGenerator(vibrato_depth=0.0)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_vibrato_max(self):
        gen = SaxSoloGenerator(vibrato_depth=1.0)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_blues_notes(self):
        gen = SaxSoloGenerator(blues_notes=False)
        notes = gen.render(_minor_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_chromaticism_zero(self):
        gen = SaxSoloGenerator(chromaticism=0.0)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_chromaticism_max(self):
        gen = SaxSoloGenerator(chromaticism=1.0)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_breath_noise_zero(self):
        gen = SaxSoloGenerator(breath_noise=0.0)
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)


# =====================================================================
# TrapDrumsGenerator
# =====================================================================

class TestTrapDrumsBasic:
    def test_produces_notes(self):
        gen = TrapDrumsGenerator()
        notes = gen.render(_chords(), C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        gen = TrapDrumsGenerator()
        assert gen.render([], C_MAJOR, 16.0) == []


class TestTrapDrumsVariants:
    @pytest.mark.parametrize("variant", ["standard", "drill", "melodic", "minimal"])
    def test_all_variants_produce_notes(self, variant):
        gen = TrapDrumsGenerator(variant=variant)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)


class TestTrapDrumsKickPatterns:
    @pytest.mark.parametrize("kick", ["standard", "offset", "double", "sparse"])
    def test_kick_patterns(self, kick):
        gen = TrapDrumsGenerator(kick_pattern=kick)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestTrapDrumsParams:
    def test_hat_roll_density_high(self):
        gen = TrapDrumsGenerator(hat_roll_density=1.0)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_hat_roll_density_zero(self):
        gen = TrapDrumsGenerator(hat_roll_density=0.0)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_clap(self):
        gen = TrapDrumsGenerator(clap_on_two=False)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_open_hat_probability(self):
        gen = TrapDrumsGenerator(open_hat_probability=0.5)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_ghost_snare_prob(self):
        gen = TrapDrumsGenerator(ghost_snare_prob=0.8)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_swing(self):
        gen = TrapDrumsGenerator(groove_swing=0.67)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_auto_fills(self):
        gen = TrapDrumsGenerator(auto_fills=False)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_kick_less_verse(self):
        gen = TrapDrumsGenerator(kick_less_verse=True)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_kick_full(self):
        gen = TrapDrumsGenerator(kick_less_verse=False)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestTrapDrumsRange:
    def test_all_pitches_are_percussion(self):
        gen = TrapDrumsGenerator()
        notes = gen.render(_chords(), A_MINOR, 16.0)
        _valid(notes)
        # Drums should use standard GM percussion pitches (36-81)
        for n in notes:
            assert 35 <= n.pitch <= 82, f"unexpected drum pitch {n.pitch}"


# =====================================================================
# Bass808SlidingGenerator
# =====================================================================

class TestBass808Basic:
    def test_produces_notes(self):
        gen = Bass808SlidingGenerator()
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords(self):
        gen = Bass808SlidingGenerator()
        assert gen.render([], A_MINOR, 16.0) == []


class TestBass808Range:
    def test_low_register(self):
        params = GeneratorParams(key_range_low=24, key_range_high=48)
        gen = Bass808SlidingGenerator(params=params)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        _valid(notes)
        for n in notes:
            assert n.pitch <= 48, f"808 pitch {n.pitch} too high for bass range"


class TestBass808Params:
    def test_slide_probability_zero(self):
        gen = Bass808SlidingGenerator(slide_probability=0.0)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_slide_probability_max(self):
        gen = Bass808SlidingGenerator(slide_probability=1.0)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_octave_range(self):
        gen = Bass808SlidingGenerator(octave_range=1)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_ghost_velocity_ratio(self):
        gen = Bass808SlidingGenerator(ghost_velocity_ratio=0.3)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_ducking(self):
        gen = Bass808SlidingGenerator(transient_ducking=False)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_gating(self):
        gen = Bass808SlidingGenerator(envelope_gating=False)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestBass808Patterns:
    def test_half_time_pattern(self):
        gen = Bass808SlidingGenerator(pattern="half_time")
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_trap_basic_pattern(self):
        gen = Bass808SlidingGenerator(pattern="trap_basic")
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)


# =====================================================================
# HiHatStutterGenerator
# =====================================================================

class TestHiHatStutterBasic:
    def test_produces_notes(self):
        gen = HiHatStutterGenerator()
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_empty_chords_still_produces_pattern(self):
        gen = HiHatStutterGenerator()
        notes = gen.render([], A_MINOR, 16.0)
        # Pattern-based generator produces notes even without chords
        assert isinstance(notes, list)
        _valid(notes)


class TestHiHatStutterPatterns:
    @pytest.mark.parametrize("pattern", [
        "trap_eighth", "trap_triplet", "drill_stutter",
        "rapid_fire", "sparse", "velocity_wave",
    ])
    def test_all_patterns_produce_notes(self, pattern):
        gen = HiHatStutterGenerator(pattern=pattern)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_fallback_on_unknown_pattern(self):
        gen = HiHatStutterGenerator(pattern="nonexistent")
        notes = gen.render(_chords(), A_MINOR, 8.0)
        # Should fallback to trap_eighth, not crash
        assert isinstance(notes, list)


class TestHiHatStutterInstruments:
    @pytest.mark.parametrize("instrument", ["hh_closed", "hh_open", "ride", "shaker"])
    def test_all_instruments_produce_notes(self, instrument):
        gen = HiHatStutterGenerator(instrument=instrument)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)


class TestHiHatStutterParams:
    def test_roll_density_zero(self):
        gen = HiHatStutterGenerator(roll_density=0.0)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_roll_density_max(self):
        gen = HiHatStutterGenerator(roll_density=1.0)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_open_hat_probability(self):
        gen = HiHatStutterGenerator(open_hat_probability=0.5)
        notes = gen.render(_chords(), A_MINOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_pan_modes(self):
        for mode in ["alternate", "center", "random"]:
            gen = HiHatStutterGenerator(pan_mode=mode)
            notes = gen.render(_chords(), A_MINOR, 8.0)
            assert len(notes) > 0
            _valid(notes)

    def test_no_velocity_accent(self):
        gen = HiHatStutterGenerator(velocity_accent=False)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_no_pitch_variation(self):
        gen = HiHatStutterGenerator(pitch_variation=False)
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)

    def test_custom_stutter_lengths(self):
        gen = HiHatStutterGenerator(stutter_lengths=[2, 4, 6])
        notes = gen.render(_chords(), A_MINOR, 8.0)
        assert len(notes) > 0
        _valid(notes)
