# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

import pytest
from melodica.idea_tool import TrackConfig, IdeaPart
from melodica.generators import TimpaniGenerator, ViolinGenerator, DroneGenerator, PianoCompGenerator, SnareDrumGenerator
from melodica.types import ChordLabel, Scale, Mode, Quality, HarmonicFunction
from melodica.composer.chord_enrichers import applied_dominant_enricher


def test_generator_type_inference():
    # 1. Verification of class-to-type map inference
    assert TrackConfig(generator=TimpaniGenerator()).generator_type == "timpani"
    assert TrackConfig(generator=ViolinGenerator()).generator_type == "violin"
    assert TrackConfig(generator=DroneGenerator()).generator_type == "drone"
    assert TrackConfig(generator=PianoCompGenerator()).generator_type == "piano_comp"
    assert TrackConfig(generator=SnareDrumGenerator()).generator_type == "snare_drum"

    # Fall-back default for unknown generator or no generator
    assert TrackConfig().generator_type == "melody"


def test_applied_dominant_enricher():
    scale = Scale(root=0, mode=Mode.MAJOR)  # C Major
    part = IdeaPart(bars=4, time_signature=(4, 4), scale=scale)

    # Progression: I -> ii -> V -> I
    # diatonic chords relative to C major
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),     # I (C)
        ChordLabel(root=2, quality=Quality.MINOR, start=4.0, duration=4.0),     # ii (Dm)
        ChordLabel(root=7, quality=Quality.MAJOR, start=8.0, duration=4.0),     # V (G)
        ChordLabel(root=0, quality=Quality.MAJOR, start=12.0, duration=4.0),    # I (C)
    ]

    enriched = applied_dominant_enricher(chords, [part])

    # Expected:
    # C major (I) is tonic -> no secondary dominant before it (start=0.0)
    # Dm (ii) is diatonic and not tonic -> we expect secondary dominant (A7, root=9, DOMINANT7) before it.
    #   The preceding chord C (I) was 4.0 beats, it should be split into C (2.0 beats) and A7 (2.0 beats).
    # G (V) is diatonic and not tonic -> we expect secondary dominant (D7, root=2, DOMINANT7) before it.
    #   The preceding chord Dm (ii) was 4.0 beats, it should be split into Dm (2.0 beats) and D7 (2.0 beats).
    # C (I) is tonic -> no secondary dominant before it.
    
    # We should have more chords now
    assert len(enriched) > len(chords)

    # Let's verify the actual chords in sequence
    # 0: C major (duration 2.0)
    # 1: A7 (secondary dominant of Dm, root 9, DOMINANT7, start 2.0, duration 2.0)
    # 2: Dm (duration 2.0)
    # 3: D7 (secondary dominant of G, root 2, DOMINANT7, start 6.0, duration 2.0)
    # 4: G (duration 4.0)
    # 5: C (duration 4.0)
    
    assert enriched[0].root == 0
    assert enriched[0].duration == 2.0

    assert enriched[1].root == 9
    assert enriched[1].quality == Quality.DOMINANT7
    assert enriched[1].start == 2.0
    assert enriched[1].duration == 2.0

    assert enriched[2].root == 2
    assert enriched[2].duration == 2.0

    assert enriched[3].root == 2
    assert enriched[3].quality == Quality.DOMINANT7
    assert enriched[3].start == 6.0
    assert enriched[3].duration == 2.0

    assert enriched[4].root == 7
    assert enriched[4].duration == 4.0

    assert enriched[5].root == 0
    assert enriched[5].duration == 4.0
