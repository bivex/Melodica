# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.sfx_percussion import SFXPercussionGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_sfx_percussion_chromatic():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Tinkle Bell
    gen_bell = SFXPercussionGenerator(instrument="tinkle_bell")
    notes_bell = gen_bell.render(chords, C_MAJOR, 4.0)
    assert len(notes_bell) == 1
    assert notes_bell[0].pitch > 70
    assert notes_bell[0].duration < 1.0

    # 2. Agogo
    gen_agogo = SFXPercussionGenerator(instrument="agogo")
    notes_agogo = gen_agogo.render(chords, C_MAJOR, 4.0)
    assert len(notes_agogo) == 2
    assert notes_agogo[0].start == 0.0
    assert notes_agogo[1].start == 0.5

    # 3. Steel Drums (rolls)
    gen_steel = SFXPercussionGenerator(instrument="steel_drums")
    notes_steel = gen_steel.render(chords, C_MAJOR, 4.0)
    assert len(notes_steel) == 6  # roll notes

    # 4. Woodblock
    gen_wood = SFXPercussionGenerator(instrument="woodblock")
    notes_wood = gen_wood.render(chords, C_MAJOR, 4.0)
    assert len(notes_wood) == 1
    assert notes_wood[0].duration == 0.08

    # 5. Taiko Drum
    gen_taiko = SFXPercussionGenerator(instrument="taiko_drum")
    notes_taiko = gen_taiko.render(chords, C_MAJOR, 4.0)
    assert len(notes_taiko) == 1
    assert notes_taiko[0].pitch < 60
    assert notes_taiko[0].velocity > 100

    # 6. Synth Drum
    gen_synth_drum = SFXPercussionGenerator(instrument="synth_drum")
    notes_synth_drum = gen_synth_drum.render(chords, C_MAJOR, 4.0)
    assert len(notes_synth_drum) == 1
    assert "pitch_bend" in notes_synth_drum[0].expression

    # 7. Reverse Cymbal
    gen_rev = SFXPercussionGenerator(instrument="reverse_cymbal")
    notes_rev = gen_rev.render(chords, C_MAJOR, 4.0)
    assert len(notes_rev) == 1
    assert 11 in notes_rev[0].expression


def test_sfx_percussion_effects():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]

    # 1. Seashore
    gen_sea = SFXPercussionGenerator(instrument="seashore")
    notes_sea = gen_sea.render(chords, C_MAJOR, 4.0)
    assert len(notes_sea) == 1
    assert 11 in notes_sea[0].expression
    assert 74 in notes_sea[0].expression

    # 2. Bird Tweet
    gen_bird = SFXPercussionGenerator(instrument="bird_tweet")
    notes_bird = gen_bird.render(chords, C_MAJOR, 4.0)
    assert len(notes_bird) == 3

    # 3. Telephone
    gen_tel = SFXPercussionGenerator(instrument="telephone")
    notes_tel = gen_tel.render(chords, C_MAJOR, 4.0)
    assert len(notes_tel) == 2
    assert notes_tel[1].start == 0.18

    # 4. Helicopter
    gen_heli = SFXPercussionGenerator(instrument="helicopter")
    notes_heli = gen_heli.render(chords, C_MAJOR, 4.0)
    assert len(notes_heli) == 1
    assert 11 in notes_heli[0].expression
    assert 10 in notes_heli[0].expression

    # 5. Applause
    gen_app = SFXPercussionGenerator(instrument="applause")
    notes_app = gen_app.render(chords, C_MAJOR, 4.0)
    assert len(notes_app) == 1
    assert 11 in notes_app[0].expression

    # 6. Gunshot
    gen_gun = SFXPercussionGenerator(instrument="gunshot")
    notes_gun = gen_gun.render(chords, C_MAJOR, 4.0)
    assert len(notes_gun) == 1
    assert notes_gun[0].velocity > 115
    assert notes_gun[0].duration == 0.12
