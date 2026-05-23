# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.synth_modern import SynthLeadGenerator, SynthPadGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_synth_lead_generator():
    gen = SynthLeadGenerator(lead_type="sawtooth", glide_speed=0.15)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    assert len(notes) >= 1
    # Check filter sweep CC 74 exists
    assert notes[0].expression is not None


def test_synth_pad_generator():
    gen = SynthPadGenerator(pad_type="warm", swell=True)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    notes = gen.render(chords, C_MAJOR, 4.0)
    # Pads generate multi-voice voicing layers
    assert len(notes) >= 2
