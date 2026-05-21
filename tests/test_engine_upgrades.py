# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-21
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.types import (
    NoteInfo,
    Track,
    Scale,
    Mode,
    Quality,
    parse_progression,
)
from melodica.generators.accent import RhythmicAccentGenerator
from melodica.composer.automation import AutomationCurve
from melodica.generators.melody import MelodyGenerator


def test_chainable_note_transformations():
    """Test chainable algebraic transformations on NoteInfo."""
    note = NoteInfo(pitch=60, start=1.0, duration=2.0, velocity=64)
    # Apply chain: shift start to 2.0, pitch to 72, velocity to 96, then multiply by 2.0 (start becomes 4.0, duration becomes 4.0)
    note.shift_time(1.0).transpose(12).scale_velocity(1.5).time_stretch(2.0)

    assert note.pitch == 72
    assert note.start == 4.0
    assert note.duration == 4.0
    assert note.velocity == 96


def test_chainable_track_transformations():
    """Test chainable algebraic transformations on Track."""
    notes = [
        NoteInfo(pitch=60, start=1.0, duration=1.0, velocity=64),
        NoteInfo(pitch=62, start=2.0, duration=1.0, velocity=64),
    ]
    track = Track(name="Strings", notes=notes)
    track.shift_time(1.0).transpose(5).scale_velocity(0.5).time_stretch(3.0)

    # Note 1: start: (1+1)*3=6.0, duration: 1*3=3.0, pitch: 60+5=65, velocity: 64*0.5=32
    # Note 2: start: (2+1)*3=9.0, duration: 1*3=3.0, pitch: 62+5=67, velocity: 64*0.5=32
    assert track.notes[0].pitch == 65
    assert track.notes[0].start == 6.0
    assert track.notes[0].duration == 3.0
    assert track.notes[0].velocity == 32

    assert track.notes[1].pitch == 67
    assert track.notes[1].start == 9.0
    assert track.notes[1].duration == 3.0
    assert track.notes[1].velocity == 32


def test_roman_numeral_duration_parsing():
    """Test parse_progression with optional chord:duration syntax."""
    key = Scale(root=0, mode=Mode.NATURAL_MINOR)
    chords = parse_progression("i:2.0 - iv:4.0 - v:2.5", key)

    assert len(chords) == 3

    assert chords[0].quality == Quality.MINOR
    assert chords[0].root == 0
    assert chords[0].start == 0.0
    assert chords[0].duration == 2.0

    assert chords[1].quality == Quality.MINOR
    assert chords[1].root == 5
    assert chords[1].start == 2.0
    assert chords[1].duration == 4.0

    assert chords[2].quality == Quality.MINOR
    assert chords[2].root == 7
    assert chords[2].start == 6.0
    assert chords[2].duration == 2.5


def test_melody_generator_leitmotif():
    """Test leitmotif support (injecting, capturing, and replicating motifs)."""
    # 1. Injecting a base motif
    generator = MelodyGenerator(
        base_motif=[60, 62, 64],
        base_motif_rhythm=[0.5, 0.5, 1.0],
    )
    key = Scale(root=0, mode=Mode.MAJOR)
    chords = parse_progression("I - IV - V", key)

    notes = generator.render(chords, key, duration_beats=12.0)
    assert len(notes) > 0
    # Captured motif should be stored on the generator
    assert len(generator._stored_motif) >= 3

    # 2. Call and response using stored motif
    responder = MelodyGenerator()
    # Share the motif
    responder.base_motif = generator._stored_motif
    responder.base_motif_rhythm = generator._stored_rhythm

    notes_resp = responder.render(chords, key, duration_beats=12.0)
    assert len(notes_resp) > 0
    assert len(responder._stored_motif) >= 3


def test_rhythmic_accent_generator():
    """Test RhythmicAccentGenerator presets, dynamic mapping, and custom sequences."""
    key = Scale(root=0, mode=Mode.NATURAL_MINOR)
    chords = parse_progression("i:4.0 - iv:4.0", key)

    # Preset: march, dynamic root mapping, octave 2
    gen = RhythmicAccentGenerator(preset="march", pitch=None, octave=2)
    notes = gen.render(chords, key, duration_beats=8.0)

    # cycle of 4.0, each cycle has 8 beats in march -> total 16 notes
    assert len(notes) == 16
    # pitches for first 8 notes should map to chord root 0 (octave 2 -> 24)
    for n in notes[:8]:
        assert n.pitch == 24
    # pitches for next 8 notes should map to chord root 5 (octave 2 -> 29)
    for n in notes[8:]:
        assert n.pitch == 29

    # Preset: waltz, fixed pitch
    gen_waltz = RhythmicAccentGenerator(preset="waltz", pitch=36)
    notes_waltz = gen_waltz.render(chords, key, duration_beats=6.0)
    # cycle of 3.0, waltz has 3 beats -> total 6 notes for 6.0 beats
    assert len(notes_waltz) == 6
    for n in notes_waltz:
        assert n.pitch == 36

    # Custom sequence
    custom_seq = [(0.0, 110, 0.5), (1.5, 90, 0.5)]
    gen_custom = RhythmicAccentGenerator(custom_sequence=custom_seq, custom_cycle=2.0)
    notes_custom = gen_custom.render(chords, key, duration_beats=4.0)
    # 2 cycles of 2.0 -> 4 notes total
    assert len(notes_custom) == 4
    assert notes_custom[0].start == 0.0
    assert notes_custom[1].start == 1.5
    assert notes_custom[2].start == 2.0
    assert notes_custom[3].start == 3.5


def test_automation_curves():
    """Test AutomationCurve math and boundary clamping."""
    # Linear
    linear = AutomationCurve.linear(cc_num=11, start_val=0, end_val=100, start_beat=0.0, end_beat=4.0, steps=5)
    assert len(linear) == 5
    assert linear[0] == (0.0, 11, 0)
    assert linear[1] == (1.0, 11, 25)
    assert linear[2] == (2.0, 11, 50)
    assert linear[3] == (3.0, 11, 75)
    assert linear[4] == (4.0, 11, 100)

    # Sine LFO
    sine = AutomationCurve.sine_lfo(cc_num=1, min_val=20, max_val=80, start_beat=0.0, end_beat=4.0, period=2.0, steps_per_period=4)
    assert len(sine) >= 2
    for beat, cc, val in sine:
        assert cc == 1
        assert 20 <= val <= 80

    # Exponential
    expo = AutomationCurve.exponential(cc_num=74, start_val=10, end_val=110, start_beat=0.0, end_beat=4.0, exponent=2.0, steps=5)
    assert len(expo) == 5
    assert expo[0] == (0.0, 74, 10)
    # t = 1.0 (ratio 0.25): 10 + 100 * (0.25^2) = 10 + 6.25 = 16
    assert expo[1][2] == 16
    # t = 2.0 (ratio 0.5): 10 + 100 * (0.5^2) = 10 + 25 = 35
    assert expo[2][2] == 35
    assert expo[4] == (4.0, 74, 110)


def test_track_morph_humanize_swing():
    """Test morph_scale, humanize, and swing chainable methods on NoteInfo and Track."""
    scale_c_major = Scale(root=0, mode=Mode.MAJOR)          # C, D, E, F, G, A, B (degrees: 0, 2, 4, 5, 7, 9, 11)
    scale_c_minor = Scale(root=0, mode=Mode.NATURAL_MINOR)  # C, D, Eb, F, G, Ab, Bb (degrees: 0, 2, 3, 5, 7, 8, 10)

    # 1. Morph Scale
    note = NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=64)  # E (pitch class 4, index 2 in C Major)
    note.morph_scale(scale_c_major, scale_c_minor, strategy="degree")
    # Should morph to Eb (pitch class 3, index 2 in C Minor -> pitch 63)
    assert note.pitch == 63

    note2 = NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=64)
    note2.morph_scale(scale_c_major, scale_c_minor, strategy="nearest")
    # E (pitch class 4) is closest to Eb (3) or F (5). Nearest should resolve it.
    assert note2.pitch in (63, 65)

    # Track morph_scale
    track = Track(name="Lead", notes=[NoteInfo(pitch=64, start=1.0, duration=1.0, velocity=64)])
    track.morph_scale(scale_c_major, scale_c_minor, strategy="degree")
    assert track.notes[0].pitch == 63

    # 2. Humanize
    track_h = Track(name="Acoustic", notes=[NoteInfo(pitch=60, start=1.0, duration=1.0, velocity=64)])
    track_h.humanize(timing_std_beats=0.05, velocity_std=5.0)
    # The timing and velocity should deviate but stay in valid bounds
    assert track_h.notes[0].start != 1.0
    assert 0 <= track_h.notes[0].velocity <= 127

    # 3. Swing
    # For a swing resolution of 0.25 beats, odd grid multiples like start=0.25 should be delayed
    note_swing = NoteInfo(pitch=60, start=0.25, duration=0.25, velocity=64)
    note_swing.swing(factor=0.1, grid=0.25)
    assert note_swing.start == 0.25 + 0.1 * 0.25


def test_dynamic_tempo_export(tmp_path):
    """Test exporting multitrack MIDI with dynamic tempo events."""
    from melodica.composer.album_pipeline import produce_track, Mood
    import mido

    notes = [
        NoteInfo(pitch=60, start=0.0, duration=2.0, velocity=64),
        NoteInfo(pitch=62, start=2.0, duration=2.0, velocity=64),
    ]
    tracks = {"lead": notes}
    instruments = {"lead": 0}

    # Generate custom tempo events representing dynamic accelerando
    # Beat 0: 70 BPM, Beat 2: 120 BPM
    tempo_events = [(0.0, 70.0), (2.0, 120.0)]
    output_file = tmp_path / "test_tempo.mid"

    produce_track(
        tracks=tracks,
        bpm=70.0,
        instruments=instruments,
        path=output_file,
        mood=Mood.CHAMBER,
        tempo_events=tempo_events,
        verbose=False
    )

    # Read back MIDI file and inspect set_tempo events
    mid = mido.MidiFile(output_file)
    tempo_meta_msgs = []
    for tr in mid.tracks:
        for msg in tr:
            if msg.type == "set_tempo":
                tempo_meta_msgs.append(msg)

    # There should be two set_tempo events (initial at beat 0, second at beat 2)
    assert len(tempo_meta_msgs) == 2
    # First should be 70 BPM
    assert abs(mido.tempo2bpm(tempo_meta_msgs[0].tempo) - 70.0) < 0.01
    # Second should be 120 BPM
    assert abs(mido.tempo2bpm(tempo_meta_msgs[1].tempo) - 120.0) < 0.01

