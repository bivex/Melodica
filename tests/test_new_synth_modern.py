# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.synth_modern import SynthLeadGenerator, SynthPadGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_synth_lead_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Sawtooth Lead
    gen_saw = SynthLeadGenerator(lead_type="sawtooth", glide_speed=0.15)
    notes_saw = gen_saw.render(chords, C_MAJOR, 4.0)
    assert len(notes_saw) >= 1
    assert notes_saw[0].expression is not None
    assert 74 in notes_saw[0].expression

    # 2. Charang Lead (adds delayed octave pop note)
    gen_charang = SynthLeadGenerator(lead_type="charang")
    notes_charang = gen_charang.render(chords, C_MAJOR, 4.0)
    assert len(notes_charang) == 2
    assert notes_charang[1].pitch == notes_charang[0].pitch + 12

    # 3. Fifths Lead (layers parallel 5th)
    gen_fifths = SynthLeadGenerator(lead_type="fifths")
    notes_fifths = gen_fifths.render(chords, C_MAJOR, 4.0)
    assert len(notes_fifths) == 2
    assert notes_fifths[1].pitch == notes_fifths[0].pitch + 7

    # 4. Bass Lead (layers deep sub-octave)
    gen_bass = SynthLeadGenerator(lead_type="bass_lead")
    notes_bass = gen_bass.render(chords, C_MAJOR, 4.0)
    assert len(notes_bass) == 2
    assert notes_bass[0].pitch == notes_bass[1].pitch + 12  # Bass is 12 semitones lower

    # 5. Voice Lead (adds CC 1 LFO vocal vibrato sweep)
    gen_voice = SynthLeadGenerator(lead_type="voice")
    notes_voice = gen_voice.render(chords, C_MAJOR, 4.0)
    assert len(notes_voice) == 1
    assert notes_voice[0].expression is not None
    assert 1 in notes_voice[0].expression


def test_synth_pad_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    # 1. Warm Pad
    gen_warm = SynthPadGenerator(pad_type="warm", swell=True)
    notes_warm = gen_warm.render(chords, C_MAJOR, 4.0)
    assert len(notes_warm) >= 2
    assert notes_warm[0].expression is not None
    assert 11 in notes_warm[0].expression

    # 2. Bowed Pad (slow string crescendo)
    gen_bowed = SynthPadGenerator(pad_type="bowed")
    notes_bowed = gen_bowed.render(chords, C_MAJOR, 4.0)
    assert len(notes_bowed) >= 2
    assert 11 in notes_bowed[0].expression

    # 3. Metallic Pad (quiet high overtone chime)
    gen_metal = SynthPadGenerator(pad_type="metallic")
    notes_metal = gen_metal.render(chords, C_MAJOR, 4.0)
    # Renders voicing + 1 metallic overtone note
    assert len(notes_metal) >= 3
    # Look for the metallic overtone note (shorter duration: 0.6)
    metal_chimes = [n for n in notes_metal if n.duration == 0.6]
    assert len(metal_chimes) == 1

    # 4. Sweep Pad (resonant sweeping CC 74 filter)
    gen_sweep = SynthPadGenerator(pad_type="sweep")
    notes_sweep = gen_sweep.render(chords, C_MAJOR, 4.0)
    assert len(notes_sweep) >= 2
    assert 74 in notes_sweep[0].expression
    assert len(notes_sweep[0].expression[74]) > 2
