# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode, ChordLabel
from melodica.theory.chords import Quality
from melodica.generators.country_ensemble import PedalSteelGenerator, DobroLapSteelGenerator, FiddleGenerator

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_pedal_steel_generator():
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=4.0, duration=4.0),  # modulation / chord change to trigger slides
    ]
    
    gen = PedalSteelGenerator(slide_speed=0.25, volume_swell=True)
    notes = gen.render(chords, C_MAJOR, 8.0)
    
    assert len(notes) >= 3
    # Check volume swells (CC 11)
    assert any(n.expression is not None and 11 in n.expression for n in notes)
    # Check slide pitch bends
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)


def test_dobro_lap_steel_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = DobroLapSteelGenerator(scoop_depth=1.5, vibrato_depth=0.2)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    assert len(notes) >= 1
    # Check pitch bend scoop and vibrato is present
    assert any(n.expression is not None and "pitch_bend" in n.expression for n in notes)


def test_fiddle_generator():
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    
    gen = FiddleGenerator(double_stop_probability=1.0, open_string_drone=True)
    notes = gen.render(chords, C_MAJOR, 4.0)
    
    # Since double stop probability is 1.0, it should generate more than 1 note per event
    assert len(notes) >= 2
