# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode
from melodica.idea_tool import IdeaPart
from melodica.composer.tension_curve import TensionCurve
from melodica.composer.tempo_modulator import TempoModulator


def test_tempo_modulator_ritardando():
    parts = [
        IdeaPart(name="Verse", bars=4, tempo=120, time_signature=(4, 4)),
        IdeaPart(name="Chorus", bars=4, tempo=140, time_signature=(4, 4)),
    ]

    modulator = TempoModulator(
        default_tempo=120,
        ritardando_beats=4.0,
        ritardando_factor=0.8,
        use_tension_tempo=False
    )

    events = modulator.generate_events(parts)
    
    # Initial tempo at 0.0 is 120.0
    assert events[0] == (0.0, 120.0)

    # Ritardando should happen at the end of Verse (beats 12 to 16)
    # And at the end of Chorus (beats 28 to 32)
    rit_events_verse = [e for e in events if 12.0 <= e[0] < 16.0]
    assert len(rit_events_verse) > 0
    # Final step of ritardando in Verse should be 120 * 0.8 = 96.0
    assert rit_events_verse[-1][1] == 96.0

    # Baseline chorus starts at 16.0 with tempo 140.0
    chorus_start = [e for e in events if e[0] == 16.0]
    assert len(chorus_start) == 1
    assert chorus_start[0][1] == 140.0


def test_tempo_modulator_tension():
    parts = [
        IdeaPart(name="Verse", bars=8, tempo=100, time_signature=(4, 4))
    ]

    curve = TensionCurve(total_beats=32.0, curve_type="classical")
    modulator = TempoModulator(
        default_tempo=100,
        ritardando_beats=0.0,  # disable ritardando to test pure tension modulation
        use_tension_tempo=True,
        tension_tempo_range=20.0
    )

    events = modulator.generate_events(parts, tension_curve=curve)
    
    # Tension-based tempo adjustments should be generated every 2 beats
    tension_events = [e for e in events if e[0] > 0.0]
    assert len(tension_events) > 0
    
    # Verify tempo values change according to tension
    bpms = [e[1] for e in tension_events]
    assert len(set(bpms)) > 1  # should not be all the same tempo
