"""
tests/test_expert_orchestrator.py — Tests for the new music21-inspired expert orchestration and harmony modules.
"""

import pytest
from melodica.types import NoteInfo, ChordLabel, Quality
from melodica.composer.orchestrator import analyze_orchestration, get_interval_name
from melodica.composer.harmonic_verifier import detect_clashes, VerifierConfig, verify_and_fix


def test_get_interval_name():
    assert get_interval_name(0) == "Unison"
    assert get_interval_name(1) == "Minor Second"
    assert get_interval_name(12) == "Perfect Octave"
    assert get_interval_name(19) == "Perfect Twelfth"
    assert get_interval_name(24) == "Perfect Double-octave"
    assert get_interval_name(31) == "Perfect Nineteenth"
    assert get_interval_name(36) == "Perfect Triple-octave"
    assert get_interval_name(13) == "Octave + Minor Second"


def test_analyze_orchestration_basic():
    # Only passing instruments
    instruments = {
        "Violins_I": 40,  # Violin (Sustained)
        "Contrabass": 43,  # Contrabass (Sustained)
        "Harp": 46,  # Harp (Plucked)
    }
    alerts = analyze_orchestration(instruments)
    # Check that it returns a list of alerts
    assert isinstance(alerts, list)


def test_analyze_orchestration_cinematic_preset():
    instruments = {
        "Violins_I": 40,   # Violin
        "Contrabass": 43,  # Contrabass
    }
    # Create notes forming many octaves and fifths (Cinematic style)
    tracks = {
        "Violins_I": [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=72, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=67, start=0.0, duration=1.0, velocity=80),
        ],
        "Contrabass": [
            NoteInfo(pitch=36, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=48, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=43, start=0.0, duration=1.0, velocity=80),
        ],
    }
    alerts = analyze_orchestration(instruments, tracks=tracks)
    # Should detect Cinematic Preset match or high octaves/fifths
    cinematic_alerts = [a for a in alerts if "Cinematic" in a]
    assert len(cinematic_alerts) > 0 or any("Top intervals detected" in a for a in alerts)


def test_analyze_orchestration_low_interval_mud():
    instruments = {
        "Cello": 42,
        "Contrabass": 43,
    }
    # Overlapping thirds in very low register (below pitch 48)
    tracks = {
        "Cello": [
            NoteInfo(pitch=40, start=i * 0.5, duration=0.4, velocity=80) for i in range(5)
        ],
        "Contrabass": [
            NoteInfo(pitch=43, start=i * 0.5, duration=0.4, velocity=80) for i in range(5)
        ],
    }
    alerts = analyze_orchestration(instruments, tracks=tracks)
    mud_alerts = [a for a in alerts if "Low-Interval Mud" in a]
    assert len(mud_alerts) > 0


def test_analyze_orchestration_conflict_ambitus():
    instruments = {
        "Violins_I": 40,
        "Violins_II": 41,
    }
    # Two sustained instruments with completely identical note ranges
    tracks = {
        "Violins_I": [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80),
            NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=80),
        ],
        "Violins_II": [
            NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80),
            NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=80),
            NoteInfo(pitch=67, start=2.0, duration=1.0, velocity=80),
        ],
    }
    alerts = analyze_orchestration(instruments, tracks=tracks)
    ambitus_alerts = [a for a in alerts if "Orchestration Blur" in a]
    assert len(ambitus_alerts) > 0


def test_analyze_orchestration_mid_range_clutter():
    instruments = {
        "Violins_I": 40,
        "Violins_II": 41,
        "Viola": 42,
        "Cello": 43,
    }
    # More than 3 instruments playing in 36-60 range simultaneously
    tracks = {
        "Violins_I": [NoteInfo(pitch=50, start=i * 1.0, duration=0.9, velocity=80) for i in range(4)],
        "Violins_II": [NoteInfo(pitch=52, start=i * 1.0, duration=0.9, velocity=80) for i in range(4)],
        "Viola": [NoteInfo(pitch=55, start=i * 1.0, duration=0.9, velocity=80) for i in range(4)],
        "Cello": [NoteInfo(pitch=48, start=i * 1.0, duration=0.9, velocity=80) for i in range(4)],
    }
    alerts = analyze_orchestration(instruments, tracks=tracks)
    clutter_alerts = [a for a in alerts if "Mid-Range Clutter" in a]
    assert len(clutter_alerts) > 0


def test_functional_dissonance_allow_chord_tones():
    # C major 7th chord (C, E, G, B) = root 0, quality MAJOR7
    # Note A is C (60), Note B is B (71) -> interval is 11 semitones (M7 clash)
    tracks = {
        "Violins_I": [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=80)],
        "Violins_II": [NoteInfo(pitch=71, start=0.0, duration=1.0, velocity=80)],
    }
    config = VerifierConfig(dissonance_tolerance=0.5)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR7, start=0.0, duration=2.0)]
    
    # Without chords, this would be a clash
    clashes_no_chords = detect_clashes(tracks, config)
    assert len(clashes_no_chords) > 0
    
    # With chords, it should be recognized as valid chord tones and ignored!
    clashes_with_chords = detect_clashes(tracks, config, chords=chords)
    assert len(clashes_with_chords) == 0


def test_functional_dissonance_allow_dominant_tritone():
    # G7 dominant chord (G, B, D, F) = root 7, quality DOMINANT7
    # Note A is B (59), Note B is F (65) -> interval is 6 semitones (Tritone clash)
    tracks = {
        "Violins_I": [NoteInfo(pitch=59, start=0.0, duration=1.0, velocity=80)],
        "Violins_II": [NoteInfo(pitch=65, start=0.0, duration=1.0, velocity=80)],
    }
    config = VerifierConfig(dissonance_tolerance=0.5)
    chords = [ChordLabel(root=7, quality=Quality.DOMINANT7, start=0.0, duration=2.0)]
    
    # With dominant chords, the structural tritone is allowed!
    clashes = detect_clashes(tracks, config, chords=chords)
    assert len(clashes) == 0


def test_dynamic_mid_range_strictness():
    # 4 tracks playing in 36-60 range simultaneously
    # Tracks A and B have a mild dissonance M2 (2 semitones, e.g. pitch 50 and 52)
    # Normally, M2 is allowed with tolerance = 0.8
    tracks = {
        "track1": [NoteInfo(pitch=50, start=0.0, duration=1.0, velocity=80)],
        "track2": [NoteInfo(pitch=52, start=0.0, duration=1.0, velocity=80)],
        "track3": [NoteInfo(pitch=40, start=0.0, duration=1.0, velocity=80)],
        "track4": [NoteInfo(pitch=45, start=0.0, duration=1.0, velocity=80)],
    }
    config = VerifierConfig(dissonance_tolerance=0.8)
    
    # Without active mid count logic, M2 is allowed under 0.8 tolerance
    # Let's test with a filtered subset of 2 tracks (no mid-range clutter)
    subset_tracks = {
        "track1": [NoteInfo(pitch=50, start=0.0, duration=1.0, velocity=80)],
        "track2": [NoteInfo(pitch=52, start=0.0, duration=1.0, velocity=80)],
    }
    clashes_subset = detect_clashes(subset_tracks, config)
    assert len(clashes_subset) == 0
    
    # With 4 tracks playing, mid-range count > 3, tolerance decreases to 0.5
    # Since severity of M2 is "mild", under tolerance 0.5 it should trigger a clash!
    clashes_cluttered = detect_clashes(tracks, config)
    assert len(clashes_cluttered) > 0
