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

    def test_hihat_choking(self):
        gen = TrapDrumsGenerator(choke_hats=True, open_hat_probability=0.5, hat_roll_density=0.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        hh_open = 46
        hh_closed = 42
        for i, n in enumerate(notes):
            if n.pitch == hh_open:
                for j in range(i + 1, len(notes)):
                    next_n = notes[j]
                    if next_n.pitch == hh_closed:
                        if next_n.start < n.start + 0.25:
                            assert n.duration < 0.25
                        break

    def test_swing_and_pocket_delays(self):
        gen = TrapDrumsGenerator(groove_swing=0.6, swing_grid=0.25, snare_delay=0.05, hihat_delay=0.02, ghost_snare_prob=0.0, hat_roll_density=0.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        snare_notes = [n for n in notes if n.pitch == 38]
        for sn in snare_notes:
            beat_in_bar = sn.start % 4.0
            assert abs((beat_in_bar - 1.05) % 2.0) < 0.001 or abs((beat_in_bar - 3.05) % 2.0) < 0.001

    def test_sidechain_ducking(self):
        gen = TrapDrumsGenerator(sidechain_depth=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        gen_no_sc = TrapDrumsGenerator(sidechain_depth=0.0)
        notes_no_sc = gen_no_sc.render(_simple_chords()[:1], C_MAJOR, 4.0)
        kick_onsets = [n.start for n in notes if n.pitch in (36,)]
        for n in notes:
            if n.pitch != 36 and n.start in kick_onsets:
                matching = [m for m in notes_no_sc if m.pitch == n.pitch and m.start == n.start]
                if matching:
                    assert n.velocity < matching[0].velocity


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


class TestDrumSectionDynamicsAndFills:
    def test_section_dynamics(self):
        from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
        from melodica.generators.electronic_drums import ElectronicDrumsGenerator
        from melodica.generators.trap_drums import TrapDrumsGenerator
        from melodica.render_context import RenderContext

        chords = _simple_chords()

        for gen_cls in [DrumKitPatternGenerator, ElectronicDrumsGenerator, TrapDrumsGenerator]:
            # Render intro
            ctx_intro = RenderContext()
            ctx_intro.section_type = "intro"
            notes_intro = gen_cls().render(chords, C_MAJOR, 4.0, context=ctx_intro)

            # Render chorus
            ctx_chorus = RenderContext()
            ctx_chorus.section_type = "chorus"
            notes_chorus = gen_cls().render(chords, C_MAJOR, 4.0, context=ctx_chorus)

            # Assert that the first Kick note (pitch 36) at start 0.0 is louder in chorus than in intro
            kick_intro = next(n for n in notes_intro if n.pitch == 36 and abs(n.start) < 0.01)
            kick_chorus = next(n for n in notes_chorus if n.pitch == 36 and abs(n.start) < 0.01)
            assert kick_chorus.velocity > kick_intro.velocity

    def test_pre_chorus_crescendo(self):
        from melodica.generators.electronic_drums import ElectronicDrumsGenerator
        from melodica.render_context import RenderContext

        ctx = RenderContext()
        ctx.section_type = "pre_chorus"
        gen = ElectronicDrumsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 16.0, context=ctx)
        
        # Compare notes in the first bar (start < 4.0) with notes in the last bar (start >= 12.0)
        first_bar_vels = [n.velocity for n in notes if n.start < 4.0]
        last_bar_vels = [n.velocity for n in notes if 12.0 <= n.start < 16.0]
        
        if first_bar_vels and last_bar_vels:
            avg_first = sum(first_bar_vels) / len(first_bar_vels)
            avg_last = sum(last_bar_vels) / len(last_bar_vels)
            # Crescendo should make the last bar velocity higher than the first bar
            assert avg_last > avg_first

    def test_phrase_boundary_fills(self):
        from melodica.generators.trap_drums import TrapDrumsGenerator
        from melodica.generators.drum_kit_pattern import DrumKitPatternGenerator
        from melodica.render_context import RenderContext

        chords = _simple_chords()

        # 1. Trap Drums fill test
        ctx_fill = RenderContext()
        ctx_fill.section_type = "chorus"
        ctx_fill.auto_fills = True
        
        gen_trap = TrapDrumsGenerator(ghost_snare_prob=0.0)
        notes_fill = gen_trap.render(chords, C_MAJOR, 8.0, context=ctx_fill)
        
        snare_fills = [n for n in notes_fill if n.pitch == 38 and n.start >= 6.0]
        assert len(snare_fills) >= 2
        
        ctx_nofill = RenderContext()
        ctx_nofill.section_type = "chorus"
        ctx_nofill.auto_fills = False
        notes_nofill = gen_trap.render(chords, C_MAJOR, 8.0, context=ctx_nofill)
        
        snare_nofill = [n for n in notes_nofill if n.pitch == 38 and n.start >= 6.0]
        assert len(snare_nofill) <= 1

        # 2. Drum Kit fill test
        ctx_kit = RenderContext()
        ctx_kit.section_type = "verse"
        ctx_kit.auto_fills = True
        gen_kit = DrumKitPatternGenerator()
        notes_kit = gen_kit.render(chords, C_MAJOR, 8.0, context=ctx_kit)
        
        fill_pitches = [38, 41, 45, 48]
        kit_fills = [n for n in notes_kit if n.pitch in fill_pitches and n.start >= 6.0]
        assert len(kit_fills) >= 2

