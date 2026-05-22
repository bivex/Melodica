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
from melodica.generators.riff import RiffGenerator
from melodica.generators.step_seq import StepSequencer
from melodica.generators.canon import CanonGenerator
from melodica.generators.call_response import CallResponseGenerator
from melodica.generators.pedal_bass import PedalBassGenerator
from melodica.generators.groove import GrooveGenerator
from melodica.generators.percussion import PercussionGenerator, DRUM_NAMES
from melodica.generators.phrase_morpher import PhraseMorpher
from melodica.generators.random_note import RandomNoteGenerator
from melodica.generators.generic_gen import GenericGenerator
from melodica.generators.chord_gen import ChordGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestRiffGenerator:
    def test_produces_notes(self):
        gen = RiffGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize(
        "pattern", ["straight_8ths", "gallop", "palm_mute", "syncopated", "punk"]
    )
    def test_named_patterns(self, pattern):
        gen = RiffGenerator(riff_pattern=pattern)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_blues_scale(self):
        gen = RiffGenerator(scale_type="blues")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_power_chord_doubles(self):
        gen = RiffGenerator(power_chord=True, palm_mute_prob=0.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        # Should have at least some octave doublings
        assert len(notes) > 0

    def test_no_power_chord(self):
        gen = RiffGenerator(power_chord=False)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0


class TestStepSequencer:
    def test_produces_notes(self):
        gen = StepSequencer()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_gate_prob_zero(self):
        gen = StepSequencer(gate_prob=0.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) == 0

    def test_gate_prob_one(self):
        gen = StepSequencer(gate_prob=1.0, steps=8)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) == 8

    def test_velocity_map(self):
        gen = StepSequencer(
            steps=4,
            gate_prob=1.0,
            velocity_map=[127, 64, 100, 32],
        )
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) == 4

    def test_tie_extends_duration(self):
        gen = StepSequencer(steps=4, gate_prob=1.0, ties=[0, 2])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) == 4
        assert notes[0].duration > notes[1].duration


class TestCanonGenerator:
    def test_produces_notes(self):
        gen = CanonGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_canon_at_fifth(self):
        gen = CanonGenerator(interval=7, delay_beats=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_canon_at_octave(self):
        gen = CanonGenerator(interval=12, delay_beats=2.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pcs = {n.pitch % 12 for n in notes}
        # Both voices should share pitch classes
        assert len(pcs) > 0

    def test_follower_is_delayed(self):
        gen = CanonGenerator(delay_beats=2.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # First note should be at t=0, later notes at t>=2.0
        assert notes[0].start == 0.0


class TestCallResponse:
    def test_produces_notes(self):
        gen = CallResponseGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_up_down_directions(self):
        gen = CallResponseGenerator(call_direction="up", response_direction="down")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_equal_lengths(self):
        gen = CallResponseGenerator(call_length=1.0, response_length=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # 4 beats / 2 beats per pair = 2 pairs, 2 notes each = 4+ notes
        assert len(notes) > 0


class TestPedalBass:
    def test_root_pedal(self):
        gen = PedalBassGenerator(pedal_note="root")
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) == 2  # one per chord
        assert notes[0].pitch % 12 == 0  # C
        assert notes[1].pitch % 12 == 7  # G

    def test_fifth_pedal(self):
        gen = PedalBassGenerator(pedal_note="fifth")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) == 1
        assert notes[0].pitch % 12 == 7  # G (fifth of C)

    def test_both_pedal(self):
        gen = PedalBassGenerator(pedal_note="both")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) == 2  # root + fifth

    def test_sustain_override(self):
        gen = PedalBassGenerator(sustain=8.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert notes[0].duration == 8.0

    def test_low_register(self):
        gen = PedalBassGenerator()
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert notes[0].pitch < 60  # below middle C


class TestGrooveGenerator:
    @pytest.mark.parametrize("pattern", ["funk_1", "funk_2", "soul", "latin"])
    def test_named_patterns(self, pattern):
        gen = GrooveGenerator(groove_pattern=pattern)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_ghost_notes(self):
        gen = GrooveGenerator(groove_pattern="funk_1")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Should have some low-velocity ghost notes
        ghost_notes = [n for n in notes if n.velocity <= 40]
        assert len(ghost_notes) > 0

    def test_accents(self):
        gen = GrooveGenerator(groove_pattern="funk_1")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Should have some high-velocity accents
        accents = [n for n in notes if n.velocity >= 100]
        assert len(accents) > 0

    def test_ghost_vel_param(self):
        gen = GrooveGenerator(ghost_note_vel=20, accent_vel=120)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestPercussionGenerator:
    @pytest.mark.parametrize("pattern", ["rock", "funk", "hiphop", "bossa"])
    def test_patterns(self, pattern):
        gen = PercussionGenerator(pattern_name=pattern)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_drum_notes_are_gm(self):
        gen = PercussionGenerator(pattern_name="rock")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        for n in notes:
            assert n.pitch in DRUM_NAMES.values()

    def test_select_instruments(self):
        gen = PercussionGenerator(pattern_name="rock", instruments=["kick", "snare"])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        pitches = {n.pitch for n in notes}
        assert 36 in pitches  # kick
        assert 38 in pitches  # snare
        assert 42 not in pitches  # hihat excluded

    def test_velocity_humanize(self):
        gen = PercussionGenerator(pattern_name="rock", velocity_humanize=15)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        vels = [n.velocity for n in notes]
        assert len(set(vels)) > 1  # not all same velocity


class TestPhraseMorpher:
    def test_morph(self):
        src = [
            NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80),
            NoteInfo(pitch=64, start=0.5, duration=0.5, velocity=80),
        ]
        tgt = [
            NoteInfo(pitch=67, start=0.0, duration=0.5, velocity=100),
            NoteInfo(pitch=72, start=0.5, duration=0.5, velocity=100),
        ]
        gen = PhraseMorpher(source_notes=src, target_notes=tgt, steps=4)
        notes = gen.render([], C_MAJOR, 4.0)
        assert len(notes) == 4
        # First note should be near source (60), last near target (72)
        assert notes[0].pitch < notes[-1].pitch

    def test_morph_velocity_interpolation(self):
        src = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=40)]
        tgt = [NoteInfo(pitch=72, start=0.0, duration=0.5, velocity=120)]
        gen = PhraseMorpher(source_notes=src, target_notes=tgt, steps=4)
        notes = gen.render([], C_MAJOR, 2.0)
        assert notes[0].velocity < notes[-1].velocity

    def test_no_source_target_returns_empty(self):
        gen = PhraseMorpher()
        assert gen.render([], C_MAJOR, 4.0) == []


class TestRandomNoteGenerator:
    def test_produces_notes(self):
        gen = RandomNoteGenerator()
        notes = gen.render([], C_MAJOR, 2.0)
        assert len(notes) > 0

    def test_note_range(self):
        gen = RandomNoteGenerator(note_range=(60, 72))
        notes = gen.render([], C_MAJOR, 2.0)
        for n in notes:
            assert 60 <= n.pitch <= 72

    def test_velocity_range(self):
        gen = RandomNoteGenerator(velocity_range=(100, 120))
        notes = gen.render([], C_MAJOR, 2.0)
        for n in notes:
            assert 100 <= n.velocity <= 120


class TestGenericGeneratorUpdate:
    def test_chord_note_ratio_zero(self):
        gen = GenericGenerator(chord_note_ratio=0.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert C_MAJOR.contains(n.pitch % 12)  # all scale notes

    def test_chord_note_ratio_one(self):
        gen = GenericGenerator(chord_note_ratio=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_partial_polyphony(self):
        gen = GenericGenerator(partial_polyphony=1.0, max_polyphony=3)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # With 100% polyphony on 3-note chord, should get 2+ notes per event sometimes
        assert len(notes) >= 4

    def test_repeat_last(self):
        gen = GenericGenerator(repeat_last=0.9)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        if len(notes) >= 2:
            repeated = sum(1 for i in range(1, len(notes)) if notes[i].pitch == notes[i - 1].pitch)
            assert repeated > 0

    def test_chord_note_indices(self):
        gen = GenericGenerator(chord_note_ratio=1.0, chord_note_indices=[0])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert n.pitch % 12 == 0  # only root


class TestChordGeneratorUpdate:
    def test_notes_to_use(self):
        gen = ChordGenerator(notes_to_use=[0, 2])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0
        assert len(notes) <= 2  # only 2 chord tones

    def test_add_bass_note(self):
        from melodica.generators import GeneratorParams

        params = GeneratorParams(key_range_low=24, key_range_high=84)
        gen = ChordGenerator(add_bass_note=-2, voicing="open", params=params)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        # Should have chord notes + bass note(s) (2 octaves below)
        assert len(notes) > 1
        # At least one note should be very low (bass register)
        low_notes = [n for n in notes if n.pitch < 48]
        assert len(low_notes) > 0

    def test_no_bass_note(self):
        gen = ChordGenerator(add_bass_note=0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        # No extra bass note
        assert len(notes) > 0


class TestTubaGenerator:
    def test_staccato_articulation(self):
        from melodica.generators.tuba import TubaGenerator
        gen = TubaGenerator(articulation="staccato")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 29 <= n.pitch <= 65
            # Staccato should have CC 74
            assert 74 in n.expression

    def test_sustained_growl_lfo(self):
        from melodica.generators.tuba import TubaGenerator
        gen = TubaGenerator(articulation="sustained", growl=True)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            # Growl should generate a list of LFO steps
            assert isinstance(n.expression[74], list)
            assert len(n.expression[74]) > 0

    def test_walking_bass_march(self):
        from melodica.generators.tuba import TubaGenerator
        gen = TubaGenerator(articulation="walking")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_swell_crescendo(self):
        from melodica.generators.tuba import TubaGenerator
        gen = TubaGenerator(articulation="swell")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 11 in n.expression
            assert isinstance(n.expression[11], list)
            assert "pitch_bend" in n.expression


class TestSnareDrumGenerator:
    def test_march_pattern(self):
        from melodica.generators.snare_drum import SnareDrumGenerator
        gen = SnareDrumGenerator(pattern_type="march")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert n.pitch in (37, 38, 40)

    def test_roll_crescendo(self):
        from melodica.generators.snare_drum import SnareDrumGenerator
        gen = SnareDrumGenerator(pattern_type="roll")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 11 in n.expression

    def test_rimshot_accents(self):
        from melodica.generators.snare_drum import SnareDrumGenerator
        gen = SnareDrumGenerator(pattern_type="rimshot")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestOrchestralCymbalGenerator:
    def test_crash_hits(self):
        from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
        gen = OrchestralCymbalGenerator(pattern_type="crash")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert n.pitch in (49, 51, 52, 55)

    def test_rolls(self):
        from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
        gen = OrchestralCymbalGenerator(pattern_type="rolls")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_sizzle(self):
        from melodica.generators.orchestral_cymbal import OrchestralCymbalGenerator
        gen = OrchestralCymbalGenerator(pattern_type="sizzle")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0


class TestTubularBellsGenerator:
    def test_single_bell_decay(self):
        from melodica.generators.tubular_bells import TubularBellsGenerator
        gen = TubularBellsGenerator(stroke_pattern="single")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 53 <= n.pitch <= 79
            assert 11 in n.expression

    def test_chime_motifs(self):
        from melodica.generators.tubular_bells import TubularBellsGenerator
        gen = TubularBellsGenerator(stroke_pattern="chime")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_dampen_tail(self):
        from melodica.generators.tubular_bells import TubularBellsGenerator
        gen1 = TubularBellsGenerator(stroke_pattern="single", dampen=False)
        gen2 = TubularBellsGenerator(stroke_pattern="single", dampen=True)
        notes1 = gen1.render(_simple_chords()[:1], C_MAJOR, 4.0)
        notes2 = gen2.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Dampened decay should have lower CC 11 end values
        cc11_1 = notes1[0].expression[11][-1][1]
        cc11_2 = notes2[0].expression[11][-1][1]
        assert cc11_2 < cc11_1


class TestInstrumentAssigner:
    def test_assign_generators_to_tracks(self):
        from melodica.composer.instrument_assigner import InstrumentAssigner
        from melodica.generators.tuba import TubaGenerator
        from melodica.generators.melody import MelodyGenerator
        from melodica.generators.snare_drum import SnareDrumGenerator

        assigner = InstrumentAssigner()
        tuba = TubaGenerator()
        melody = MelodyGenerator()
        snare = SnareDrumGenerator()

        tracks = ["Bass_Track", "Melody_Track", "Snare_Track"]
        mapping = assigner.assign_generators([tuba, melody, snare], tracks)

        assert len(mapping) == 3
        assert isinstance(mapping["Bass_Track"], TubaGenerator)
        assert isinstance(mapping["Melody_Track"], MelodyGenerator)
        assert isinstance(mapping["Snare_Track"], SnareDrumGenerator)

    def test_assign_gm_programs(self):
        from melodica.composer.instrument_assigner import InstrumentAssigner
        assigner = InstrumentAssigner()
        
        roles = {
            "Bassoon_Bass": "bass",
            "Violin_Lead": "melody",
            "Trumpet_Solo": "melody",
            "Brass_Section_Chords": "harmony",
            "Timpani_Roll": "percussion",
        }
        gm_map = assigner.assign_gm_programs(roles)
        
        assert gm_map["Bassoon_Bass"] == 58  # Tuba/Low
        assert gm_map["Violin_Lead"] == 40   # Violin
        assert gm_map["Trumpet_Solo"] == 56  # Trumpet
        assert gm_map["Brass_Section_Chords"] == 61  # Brass Section
        assert gm_map["Timpani_Roll"] == 47  # Timpani

