# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-02 03:04
# Last Updated: 2026-04-02 03:04
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators.supersaw_pad import SupersawPadGenerator
from melodica.generators.synth_bass import SynthBassGenerator
from melodica.generators.bass_wobble import BassWobbleGenerator
from melodica.generators.filter_sweep import FilterSweepGenerator
from melodica.generators.sidechain_pump import SidechainPumpGenerator
from melodica.generators.nebula import NebulaGenerator
from melodica.generators.breakbeat import BreakbeatGenerator
from melodica.generators.trap_drums import TrapDrumsGenerator
from melodica.generators.four_on_floor import FourOnFloorGenerator
from melodica.generators.beat_repeat import BeatRepeatGenerator
from melodica.generators.electronic_drums import ElectronicDrumsGenerator
from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestLeadSynthGenerator:
    def test_produces_notes(self):
        gen = LeadSynthGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("style", ["trance", "techno", "retro", "supersaw"])
    def test_styles(self, style):
        gen = LeadSynthGenerator(style=style)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            LeadSynthGenerator(style="dubstep")

    @pytest.mark.parametrize("note_length", ["legato", "staccato", "mixed"])
    def test_note_lengths(self, note_length):
        gen = LeadSynthGenerator(note_length=note_length)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_note_length_raises(self):
        with pytest.raises(ValueError):
            LeadSynthGenerator(note_length="pizzicato")

    def test_portamento(self):
        gen = LeadSynthGenerator(portamento=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_vibrato(self):
        gen = LeadSynthGenerator(vibrato_rate=2.0, vibrato_depth=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestSupersawPadGenerator:
    def test_produces_notes(self):
        gen = SupersawPadGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["trance", "ambient", "stabs", "plucks"])
    def test_variants(self, variant):
        gen = SupersawPadGenerator(variant=variant)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_voice_count(self):
        gen = SupersawPadGenerator(voice_count=7)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_detune(self):
        gen = SupersawPadGenerator(detune_amount=0.3)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_sidechain_feel(self):
        gen = SupersawPadGenerator(sidechain_feel=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestSynthBassGenerator:
    def test_produces_notes(self):
        gen = SynthBassGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("waveform", ["saw", "square", "sine", "acid"])
    def test_waveforms(self, waveform):
        gen = SynthBassGenerator(waveform=waveform)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["acid_line", "reese", "sub_kick", "wobble", "plucked"])
    def test_patterns(self, pattern):
        gen = SynthBassGenerator(pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_slide_probability(self):
        gen = SynthBassGenerator(slide_probability=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_in_bass_range(self):
        gen = SynthBassGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert n.pitch <= 72


class TestBassWobbleGenerator:
    def test_produces_notes(self):
        gen = BassWobbleGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("rate", ["1/4", "1/8", "1/16", "triplet"])
    def test_wobble_rates(self, rate):
        gen = BassWobbleGenerator(wobble_rate=rate)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("waveform", ["saw", "square", "sine"])
    def test_waveforms(self, waveform):
        gen = BassWobbleGenerator(waveform=waveform)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_slide(self):
        gen = BassWobbleGenerator(pitch_slide=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_in_bass_range(self):
        gen = BassWobbleGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert n.pitch <= 72


class TestFilterSweepGenerator:
    def test_produces_notes(self):
        gen = FilterSweepGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize(
        "sweep_type", ["lowpass_open", "lowpass_close", "bandpass", "highpass"]
    )
    def test_sweep_types(self, sweep_type):
        gen = FilterSweepGenerator(sweep_type=sweep_type)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_sweep_type_raises(self):
        with pytest.raises(ValueError):
            FilterSweepGenerator(sweep_type="notch")

    @pytest.mark.parametrize("curve", ["linear", "exponential"])
    def test_curves(self, curve):
        gen = FilterSweepGenerator(curve=curve)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_curve_raises(self):
        with pytest.raises(ValueError):
            FilterSweepGenerator(curve="logarithmic")

    def test_resonance(self):
        gen = FilterSweepGenerator(resonance=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestSidechainPumpGenerator:
    def test_produces_notes(self):
        gen = SidechainPumpGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("rate", ["1/4", "1/8"])
    def test_rates(self, rate):
        gen = SidechainPumpGenerator(rate=rate)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_rate_raises(self):
        with pytest.raises(ValueError):
            SidechainPumpGenerator(rate="1/16")

    def test_depth(self):
        gen = SidechainPumpGenerator(depth=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_attack_release(self):
        gen = SidechainPumpGenerator(attack=0.1, release=2.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestNebulaGenerator:
    def test_produces_notes(self):
        gen = NebulaGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["cloud", "cascade", "swell", "granular", "stasis"])
    def test_variants(self, variant):
        gen = NebulaGenerator(variant=variant)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_density_notes(self):
        gen = NebulaGenerator(density_notes=12)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_spread(self):
        gen = NebulaGenerator(pitch_spread=24)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_use_scale_tones(self):
        gen = NebulaGenerator(use_scale_tones=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestBreakbeatGenerator:
    def test_produces_notes(self):
        gen = BreakbeatGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["amen", "funky", "think", "dnb", "idm"])
    def test_variants(self, variant):
        gen = BreakbeatGenerator(variant=variant)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_chop_probability(self):
        gen = BreakbeatGenerator(chop_probability=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_no_ghost_notes(self):
        gen = BreakbeatGenerator(ghost_notes=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_double_time(self):
        gen = BreakbeatGenerator(double_time=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestTrapDrumsGenerator:
    def test_produces_notes(self):
        gen = TrapDrumsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["standard", "drill", "melodic", "minimal"])
    def test_variants(self, variant):
        gen = TrapDrumsGenerator(variant=variant)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("kick_pattern", ["standard", "syncopated", "sparse"])
    def test_kick_patterns(self, kick_pattern):
        gen = TrapDrumsGenerator(kick_pattern=kick_pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_hat_rolls(self):
        gen = TrapDrumsGenerator(hat_roll_density=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_clap_on_two(self):
        gen = TrapDrumsGenerator(clap_on_two=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestFourOnFloorGenerator:
    def test_produces_notes(self):
        gen = FourOnFloorGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("variant", ["house", "techno", "disco", "progressive"])
    def test_variants(self, variant):
        gen = FourOnFloorGenerator(variant=variant)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("hihat_style", ["closed", "open", "mixed"])
    def test_hihat_styles(self, hihat_style):
        gen = FourOnFloorGenerator(hihat_style=hihat_style)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_swing(self):
        gen = FourOnFloorGenerator(swing=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestBeatRepeatGenerator:
    def test_produces_notes(self):
        gen = BeatRepeatGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize(
        "repeat_type", ["accelerate", "decelerate", "constant", "gate", "glitch", "reverse"]
    )
    def test_repeat_types(self, repeat_type):
        gen = BeatRepeatGenerator(repeat_type=repeat_type)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_stutter_length(self):
        gen = BeatRepeatGenerator(stutter_length=8.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_pitch_shift(self):
        gen = BeatRepeatGenerator(pitch_shift=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestElectronicDrumsGenerator:
    def test_produces_notes(self):
        gen = ElectronicDrumsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("kit", ["909", "808", "cr78", "linn"])
    def test_kits(self, kit):
        gen = ElectronicDrumsGenerator(kit=kit)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["four_on_floor", "breakbeat", "minimal", "techno"])
    def test_patterns(self, pattern):
        gen = ElectronicDrumsGenerator(pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_sidechain(self):
        gen = ElectronicDrumsGenerator(sidechain=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestDrumKitPatternGenerator:
    def test_produces_notes(self):
        gen = DrumKitPatternGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("style", ["rock", "jazz", "latin", "funk", "hiphop"])
    def test_styles(self, style):
        gen = DrumKitPatternGenerator(style=style)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("hihat_pattern", ["eighth", "sixteenth", "open"])
    def test_hihat_patterns(self, hihat_pattern):
        gen = DrumKitPatternGenerator(hihat_pattern=hihat_pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_fill_frequency(self):
        gen = DrumKitPatternGenerator(fill_frequency=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0
