# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

import pytest
from melodica.types import ChordLabel, NoteInfo, Scale, Mode, Quality
from melodica.composer.chord_voicing_layout import ChordVoicingLayout
from melodica.generators.chord_layout import ChordLayoutGenerator
from melodica.idea_tool import IdeaTool, IdeaToolConfig, TrackConfig, IdeaPart


def test_chord_voicing_layout_rules():
    # C major chord (0, 4, 7)
    chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    
    # 4 standard strings instruments
    instruments = ["double_bass", "cello", "viola", "violin"]
    layout = ChordVoicingLayout(instruments=instruments)
    
    voicing = layout.voice_chord(chord)
    
    # Check that each instrument is assigned a pitch
    assert "double_bass" in voicing
    assert "cello" in voicing
    assert "viola" in voicing
    assert "violin" in voicing
    
    # Bass rule: double_bass (lowest) plays the root pitch class (0 = C)
    assert voicing["double_bass"] % 12 == 0
    # Check register logic: double_bass is low (between 24 and 53)
    assert 24 <= voicing["double_bass"] <= 53
    
    # Inner voices rule: cello, viola play thirds / fifths
    assert voicing["cello"] % 12 in (4, 7, 0)
    assert voicing["viola"] % 12 in (4, 7, 0)
    
    # Violin (highest) should play in its register
    assert 55 <= voicing["violin"] <= 88


def test_chord_voicing_layout_with_melody():
    chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    instruments = ["double_bass", "cello", "viola", "violin"]
    layout = ChordVoicingLayout(instruments=instruments)
    
    # Melody pitch = G5 (79)
    voicing = layout.voice_chord(chord, melody_pitch=79)
    
    # The highest instrument (violin) should snap to G5 (79)
    assert voicing["violin"] == 79


def test_chord_voicing_layout_doubling():
    # strings + glockenspiel doubling
    instruments = ["violin", "glockenspiel"]
    layout = ChordVoicingLayout(instruments=instruments)
    chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    
    voicing = layout.voice_chord(chord)
    
    # Glockenspiel should double violin but in a higher register
    v_pitch = voicing["violin"]
    g_pitch = voicing["glockenspiel"]
    
    assert g_pitch % 12 == v_pitch % 12
    assert g_pitch > v_pitch


def test_chord_layout_generator_integration():
    config = IdeaToolConfig(
        scale=Scale(0, Mode.MAJOR),
        bars=4,
        tracks=[
            TrackConfig(
                name="violin_track",
                generator_type="chord_layout",
                instrument="violin",
                params={
                    "instrument_name": "violin",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            ),
            TrackConfig(
                name="cello_track",
                generator_type="chord_layout",
                instrument="cello",
                params={
                    "instrument_name": "cello",
                    "instruments": ["double_bass", "cello", "viola", "violin"]
                }
            )
        ],
        parts=[
            IdeaPart(name="Verse", bars=4)
        ]
    )
    
    tool = IdeaTool(config)
    result = tool.generate()
    
    assert "violin_track" in result
    assert "cello_track" in result
    assert len(result["violin_track"]) > 0
    assert len(result["cello_track"]) > 0
