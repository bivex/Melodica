# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.percussion_latino import ShakerGenerator
from melodica.generators.sound_design import WindMachineGenerator
from melodica.generators.orchestral_drum import ConcertBassDrumGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_shaker_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # Test different instruments and rhythm styles
    for inst, pitch in [("shaker", 82), ("maracas", 70), ("cabasa", 69)]:
        gen = ShakerGenerator(instrument=inst, rhythm_style="16th", note_density=1.0)
        notes = gen.render(chords, C_MAJOR, 4.0)
        assert len(notes) > 0
        for note in notes:
            assert note.pitch == pitch
            assert note.absolute is True

    # Test accented vs 8th rhythm style
    gen_8th = ShakerGenerator(instrument="shaker", rhythm_style="8th", note_density=1.0)
    notes_8th = gen_8th.render(chords, C_MAJOR, 4.0)
    assert len(notes_8th) == 8  # 4 beats, 8th notes -> 8 steps


def test_wind_machine_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]

    # Test different effect types and curves
    for eff, pitch in [("thunder", 82), ("rainstick", 83), ("wind", 84)]:
        gen = WindMachineGenerator(effect_type=eff, intensity_curve="swell", note_density=1.0)
        notes = gen.render(chords, C_MAJOR, 4.0)
        assert len(notes) == 1
        note = notes[0]
        assert note.pitch == pitch
        assert note.absolute is True
        assert note.expression is not None
        assert 11 in note.expression

    # Test fade curve
    gen_fade = WindMachineGenerator(effect_type="wind", intensity_curve="fade", note_density=1.0)
    notes_fade = gen_fade.render(chords, C_MAJOR, 4.0)
    assert len(notes_fade) == 1
    # First CC 11 value should be higher than the last CC 11 value in a fade
    cc11_points = notes_fade[0].expression[11]
    assert cc11_points[0][1] > cc11_points[-1][1]


def test_concert_bass_drum_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]

    # Test single impact
    gen_single = ConcertBassDrumGenerator(drum_type="bass_drum", pattern_type="single_impact")
    notes_single = gen_single.render(chords, C_MAJOR, 4.0)
    assert len(notes_single) == 1
    assert notes_single[0].pitch == 35
    assert notes_single[0].absolute is True
    assert notes_single[0].duration == 0.5

    # Test roll
    gen_roll = ConcertBassDrumGenerator(drum_type="tenor_drum", pattern_type="roll", roll_subdivision=0.25)
    notes_roll = gen_roll.render(chords, C_MAJOR, 4.0)
    # 4 beats * 0.95 = 3.8 dur. 3.8 / 0.25 = 15.2 -> 16 notes
    assert len(notes_roll) >= 15
    for note in notes_roll:
        assert note.pitch == 47

    # Test crescendo
    gen_cres = ConcertBassDrumGenerator(drum_type="bass_drum", pattern_type="crescendo", roll_subdivision=0.25)
    notes_cres = gen_cres.render(chords, C_MAJOR, 4.0)
    assert len(notes_cres) >= 15
    # Crescendo should end with higher velocity notes than it starts with
    assert notes_cres[-1].velocity > notes_cres[0].velocity
