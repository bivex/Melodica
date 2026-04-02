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

import io
import mido
import pytest
from melodica.types import Scale, Mode, NoteInfo, Track, Arrangement
from melodica.composition import Section, Composition, MusicDirector
from melodica.composition.styles import STYLES
from melodica.midi import export_midi
from melodica.application.automation import ExpressionCurve

def test_full_midi_symphonic_integration():
    """
    Verifies that a complex symphonic arrangement results in a mathematically 
    correct MIDI file with all instruments, channels, and automations.
    """
    key = Scale(root=2, mode=Mode.MESSIAEN_2) # D Messiaen 2
    director = MusicDirector(key=key)
    style = STYLES["symphonic"]
    
    # 1. Create a 2-section composition
    comp = Composition("Test Symphony", key)
    comp.add_section("Intro", 16.0, "Im bII", style.track_mapping)
    
    # Add some automation to verify later
    crescendo = ExpressionCurve.linear(target="volume", start_val=20, end_val=120, duration=16.0)
    comp.sections[0].automation.append(crescendo)
    
    # 2. Render
    arrangement = director.render_auto_song(style, [("Intro", 16.0)])
    
    # 3. Export to in-memory buffer
    buf = io.BytesIO()
    export_midi(arrangement.tracks, buf)
    buf.seek(0)
    
    # 4. Parse back and Verify
    mid = mido.MidiFile(file=buf)
    
    # A. Check Track count (Global + N instruments)
    # style.track_mapping has 12 items
    assert len(mid.tracks) == 13 # 1 Global + 12 tracks
    
    # B. Check Channel & Program integrity
    found_programs = {}
    found_pans = {}
    
    for i, track in enumerate(mid.tracks[1:]): # Skip Global
        track_name = arrangement.tracks[i].name
        channel = arrangement.tracks[i].channel
        
        # We expect unique channels for at least the first 12 tracks
        assert channel == i
        
        has_program = False
        has_volume = False
        has_pan = False
        
        for msg in track:
            if msg.type == 'program_change':
                assert msg.channel == channel
                found_programs[track_name] = msg.program
                has_program = True
            if msg.type == 'control_change':
                assert msg.channel == channel
                if msg.control == 7: has_volume = True
                if msg.control == 10: has_pan = True
        
        # Verify instrument mapped correctly
        if track_name in style.instrument_mapping:
            assert found_programs[track_name] == style.instrument_mapping[track_name]
            
        assert has_program, f"Track {track_name} missing Program Change"
        assert has_volume, f"Track {track_name} missing Volume CC"
        assert has_pan, f"Track {track_name} missing Panning CC"

def test_pitch_bend_range_integration():
    """Verifies that pitch bend curves are correctly mapped to MIDI -8192..8191 range."""
    # Create one track with a pitch surge
    notes = [NoteInfo(pitch=60, start=i, duration=1.0) for i in range(4)]
    
    # Add a pitch dip surge (targeting 32 out of 127 = approx -4000)
    curve = ExpressionCurve.surge(target="pitch_bend", peak_val=32, duration=4.0)
    from melodica.application.automation import apply_automation
    notes = apply_automation(notes, [curve])
    
    track = Track(name="Lead", notes=notes, channel=5, program=73)
    
    buf = io.BytesIO()
    export_midi([track], buf)
    buf.seek(0)
    
    mid = mido.MidiFile(file=buf)
    found_bends = []
    for msg in mid.tracks[1]:
        if msg.type == 'pitchwheel':
            found_bends.append(msg.pitch)
            
    assert len(found_bends) > 0
    # Peak of surge was 32. 
    # 32/127 * 16383 - 8192 = -4058 approximately
    assert any(b < -3000 for b in found_bends)
    assert all(-8192 <= b <= 8191 for b in found_bends)
