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
from melodica.generators.alberti_bass import AlbertiBassGenerator
from melodica.generators.boogie_woogie import BoogieWoogieGenerator
from melodica.generators.stride_piano import StridePianoGenerator
from melodica.generators.ragtime import RagtimeGenerator
from melodica.generators.organ_drawbars import OrganDrawbarsGenerator
from melodica.generators.keys_arpeggio import KeysArpeggioGenerator
from melodica.generators.piano_comp import PianoCompGenerator
from melodica.generators.hocket import HocketGenerator
from melodica.generators.montuno import MontunoGenerator
from melodica.generators.tango import TangoGenerator
from melodica.generators.waltz import WaltzGenerator
from melodica.generators.reggae_skank import ReggaeSkankGenerator
from melodica.generators.sax_solo import SaxSoloGenerator
from melodica.generators.blues_lick import BluesLickGenerator
from melodica.generators.counterpoint import CounterpointGenerator
from melodica.generators.countermelody import CountermelodyGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestAlbertiBassGenerator:
    def test_produces_notes(self):
        gen = AlbertiBassGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("pattern", ["1-5-3-5", "1-3-5-3", "1-5-3-1"])
    def test_patterns(self, pattern):
        gen = AlbertiBassGenerator(pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_subdivision(self):
        gen = AlbertiBassGenerator(subdivision=0.25)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_voice_lead_off(self):
        gen = AlbertiBassGenerator(voice_lead=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pitch_in_bass_range(self):
        gen = AlbertiBassGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert n.pitch <= 72


class TestBoogieWoogieGenerator:
    def test_produces_notes(self):
        gen = BoogieWoogieGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pattern(self):
        gen = BoogieWoogieGenerator(pattern="standard")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_octave_bass_off(self):
        gen = BoogieWoogieGenerator(octave_bass=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_swing(self):
        gen = BoogieWoogieGenerator(swing=0.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_accent_on_one(self):
        gen = BoogieWoogieGenerator(accent_on_one=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestStridePianoGenerator:
    def test_produces_notes(self):
        gen = StridePianoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            StridePianoGenerator(pattern="invalid")

    def test_bass_octave_doubled(self):
        gen = StridePianoGenerator(bass_octave_doubled=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voicing", ["closed", "open"])
    def test_voicings(self, voicing):
        gen = StridePianoGenerator(chord_voicing=voicing)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_chromatic_approach(self):
        gen = StridePianoGenerator(chromatic_approach=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_ornaments(self):
        gen = StridePianoGenerator(ornaments=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestRagtimeGenerator:
    def test_produces_notes(self):
        gen = RagtimeGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pattern(self):
        gen = RagtimeGenerator(pattern="classic")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_melody_density(self):
        gen = RagtimeGenerator(melody_density=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_left_hand_only(self):
        gen = RagtimeGenerator(left_hand=True, right_hand=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_right_hand_only(self):
        gen = RagtimeGenerator(left_hand=False, right_hand=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestOrganDrawbarsGenerator:
    def test_produces_notes(self):
        gen = OrganDrawbarsGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_registration_raises(self):
        with pytest.raises(ValueError):
            OrganDrawbarsGenerator(registration="invalid")

    def test_invalid_leslie_raises(self):
        with pytest.raises(ValueError):
            OrganDrawbarsGenerator(leslie_speed="turbo")

    def test_percussion(self):
        gen = OrganDrawbarsGenerator(percussion=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_vibrato(self):
        gen = OrganDrawbarsGenerator(vibrato=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestKeysArpeggioGenerator:
    def test_produces_notes(self):
        gen = KeysArpeggioGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            KeysArpeggioGenerator(arp_pattern="sideways")

    def test_rate(self):
        gen = KeysArpeggioGenerator(rate=0.125)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_octave_spread(self):
        gen = KeysArpeggioGenerator(octave_spread=3)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_swing(self):
        gen = KeysArpeggioGenerator(swing=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_lfo(self):
        gen = KeysArpeggioGenerator(lfo_rate=1.0, lfo_depth=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestPianoCompGenerator:
    def test_produces_notes(self):
        gen = PianoCompGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_comp_style_raises(self):
        with pytest.raises(ValueError):
            PianoCompGenerator(comp_style="invalid")

    def test_invalid_voicing_raises(self):
        with pytest.raises(ValueError):
            PianoCompGenerator(voicing_type="invalid")

    def test_invalid_accent_raises(self):
        with pytest.raises(ValueError):
            PianoCompGenerator(accent_pattern="invalid")

    def test_chord_density(self):
        gen = PianoCompGenerator(chord_density=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestHocketGenerator:
    def test_produces_notes(self):
        gen = HocketGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            HocketGenerator(hocket_pattern="invalid")

    def test_voice_index(self):
        gen = HocketGenerator(voice_index=1)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_euclidean_params(self):
        gen = HocketGenerator(euclidean_pulses=5, euclidean_steps=8)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestMontunoGenerator:
    def test_produces_notes(self):
        gen = MontunoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_pattern_raises(self):
        with pytest.raises(ValueError):
            MontunoGenerator(pattern="invalid")

    def test_invalid_clave_raises(self):
        with pytest.raises(ValueError):
            MontunoGenerator(clave_type="invalid")

    def test_tumbao_bass(self):
        gen = MontunoGenerator(tumbao_bass=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dynamic_pattern(self):
        gen = MontunoGenerator(dynamic_pattern=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_octave_doubling(self):
        gen = MontunoGenerator(octave_doubling=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestTangoGenerator:
    def test_produces_notes(self):
        gen = TangoGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_pattern(self):
        gen = TangoGenerator(pattern="marcato")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_accent(self):
        gen = TangoGenerator(accent=2.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_staccato_chords(self):
        gen = TangoGenerator(staccato_chords=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestWaltzGenerator:
    def test_produces_notes(self):
        gen = WaltzGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_variant(self):
        gen = WaltzGenerator(variant="viennese")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_bass_octave(self):
        gen = WaltzGenerator(include_bass_octave=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_staccato(self):
        gen = WaltzGenerator(staccato_chords=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestReggaeSkankGenerator:
    def test_produces_notes(self):
        gen = ReggaeSkankGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_variant(self):
        gen = ReggaeSkankGenerator(variant="skank")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_staccato(self):
        gen = ReggaeSkankGenerator(staccato=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_mute_probability(self):
        gen = ReggaeSkankGenerator(mute_probability=0.5)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestSaxSoloGenerator:
    def test_produces_notes(self):
        gen = SaxSoloGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_style(self):
        gen = SaxSoloGenerator(style="bebop")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_vibrato(self):
        gen = SaxSoloGenerator(vibrato_depth=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_blues_notes(self):
        gen = SaxSoloGenerator(blues_notes=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_chromaticism(self):
        gen = SaxSoloGenerator(chromaticism=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestBluesLickGenerator:
    def test_produces_notes(self):
        gen = BluesLickGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            BluesLickGenerator(lick_style="invalid")

    def test_phrase_length(self):
        gen = BluesLickGenerator(phrase_length=8)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_rest_probability(self):
        gen = BluesLickGenerator(rest_probability=0.9)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # With high rest probability, fewer notes but still some
        assert isinstance(notes, list)

    def test_bend_probability(self):
        gen = BluesLickGenerator(bend_probability=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert isinstance(notes, list)


class TestCounterpointGenerator:
    def test_produces_notes(self):
        gen = CounterpointGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("species", [1, 2, 3, 4, 5])
    def test_species(self, species):
        gen = CounterpointGenerator(species=species)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("voices", [2, 3, 4])
    def test_voices(self, voices):
        gen = CounterpointGenerator(voices=voices)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_cantus_position(self):
        gen = CounterpointGenerator(cantus_position="above")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dissonance_rules_off(self):
        gen = CounterpointGenerator(dissonance_rules=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestCountermelodyGenerator:
    def test_produces_notes(self):
        primary = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
            NoteInfo(pitch=67, start=1.0, duration=0.5, velocity=80),
            NoteInfo(pitch=72, start=1.5, duration=0.5, velocity=80),
        ]
        gen = CountermelodyGenerator(primary_melody=primary)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("motion", ["contrary", "oblique", "mixed"])
    def test_motion_preferences(self, motion):
        primary = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
        ]
        gen = CountermelodyGenerator(primary_melody=primary, motion_preference=motion)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0

    def test_invalid_motion_raises(self):
        with pytest.raises(ValueError):
            CountermelodyGenerator(motion_preference="parallel")

    def test_dissonance_on_weak(self):
        primary = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
        ]
        gen = CountermelodyGenerator(primary_melody=primary, dissonance_on_weak=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0

    def test_interval_limit(self):
        primary = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
        ]
        gen = CountermelodyGenerator(primary_melody=primary, interval_limit=12)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0
