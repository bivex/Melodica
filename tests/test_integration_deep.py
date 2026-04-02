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

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pytest
from melodica.types import Scale, Mode, ChordLabel, Quality, MusicTimeline, KeyLabel, NoteInfo
from melodica.modifiers import ModifierContext
from melodica.generators.melody import MelodyGenerator
from melodica.generators.arpeggiator import ArpeggiatorGenerator
from melodica.rhythm.schillinger import SchillingerGenerator
from melodica.rhythm.library import get_rhythm
from melodica.modifiers.harmonic import TransposeModifier
from melodica.generators.chord_gen import ChordGenerator
from melodica.modifiers.rhythmic import QuantizeModifier, HumanizeModifier, FollowRhythmModifier
from melodica.presets import serialize_preset, deserialize_preset
from melodica_cli import parse_keys, parse_chords


def test_modulation_integration():
    """
    Test that MelodyGenerator correctly picks scale tones when modulation occurs.
    C Major (0-8 beats) -> G Major (8-16 beats).
    F is in C Major scale, but F# is in G Major scale.
    """
    # 1. Setup Timeline
    c_maj = Scale(root=0, mode=Mode.MAJOR)  # C D E F G A B
    g_maj = Scale(root=7, mode=Mode.MAJOR)  # G A B C D E F#

    keys = [KeyLabel(scale=c_maj, start=0.0), KeyLabel(scale=g_maj, start=8.0)]

    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=8.0),  # C
        ChordLabel(root=7, quality=Quality.MAJOR, start=8.0, duration=8.0),  # G
    ]

    timeline = MusicTimeline(chords=chords, keys=keys)

    # 2. Generate Melody
    # We'll use a high density to get many notes
    gen = MelodyGenerator(prefer_chord_tones=0.0)  # Force scale tones mostly
    gen.params.density = 0.8

    notes = gen.render(chords, timeline, 16.0)

    # 3. Verify
    for n in notes:
        pc = n.pitch % 12
        if n.start < 8.0:
            # Must be in C Major
            assert c_maj.contains(pc), f"Note {pc} at {n.start} not in C Major"
            # Should NOT be F# (6)
            assert pc != 6, f"F# found in C Major segment at {n.start}"
        else:
            # Must be in G Major
            assert g_maj.contains(pc), f"Note {pc} at {n.start} not in G Major"
            # Should NOT be F (5)
            assert pc != 5, f"F natural found in G Major segment at {n.start}"


def test_complex_modifier_chain_integration():
    """
    Generator -> Transpose -> Quantize -> Humanize.
    Tests the flow of ModifiedContext and note transformations.
    """
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    key = Scale(root=0, mode=Mode.MAJOR)
    timeline = MusicTimeline(chords=chords, keys=[KeyLabel(scale=key, start=0.0)])

    # Arpeggiator produces 16th notes by default (0.25)
    gen = ArpeggiatorGenerator(pattern="up", note_duration=0.25)
    notes = gen.render(chords, timeline, 4.0)

    # Chain
    mods = [
        TransposeModifier(semitones=2),  # C -> D
        QuantizeModifier(grid_resolution=0.5),  # Snap to 8th notes
        HumanizeModifier(timing_std=0.001),  # Subtle jitter
    ]

    ctx = ModifierContext(
        duration_beats=4.0, chords=chords, timeline=timeline, scale=Scale(0, Mode.MAJOR)
    )

    current_notes = notes
    for m in mods:
        current_notes = m.modify(current_notes, ctx)

    # Verify Transpose
    original_pcs = {n.pitch % 12 for n in notes}
    transposed_pcs = {n.pitch % 12 for n in current_notes}
    # {0, 4, 7} -> {2, 6, 9} (D Major triad instead of C)
    assert transposed_pcs == {(pc + 2) % 12 for pc in original_pcs}

    # Verify Quantize (roughly)
    for n in current_notes:
        # Snap to 0.5 grid should mean start % 0.5 is near 0
        rem = n.start % 0.5
        assert rem < 0.01 or rem > 0.49


def test_cli_keys_parsing_and_logic():
    """
    Tests if the CLI correctly handles the --keys argument and passes it to the engine.
    """
    keys_str = "0:C:major 8:D:major"
    keys = parse_keys(keys_str)

    assert len(keys) == 2
    assert keys[0].start == 0.0
    assert keys[0].scale.root == 0
    assert keys[1].start == 8.0
    assert keys[1].scale.root == 2
    assert keys[1].scale.mode == Mode.MAJOR


def test_end_to_end_midi_generation(tmp_path):
    """
    Mock-like end-to-end test that ensures the whole pipeline
    from CLI-like call to MIDI data works.
    """
    from melodica_cli import cmd_generate
    import types as py_types

    # Create a dummy args object
    class Args:
        chords = "C F G C"
        progression = None
        preset = "default"
        out = str(tmp_path / "test_out.mid")
        root = "C"
        mode = "major"
        keys = "0:C:major 8:G:major"

    args = Args()

    # This should run without crashing
    cmd_generate(args)

    assert Path(args.out).exists()
    assert Path(args.out).stat().st_size > 0


def test_harmonization_into_timeline():
    """
    Test detecting chords and then using that timeline for further generation.
    """
    from melodica.detection import detect_chords_from_midi
    from melodica.types import Note

    # C Major melody: C E G C
    melody = [Note(60, 0, 1), Note(64, 1, 1), Note(67, 2, 1), Note(72, 3, 1)]

    key = Scale(root=0, mode=Mode.MAJOR)
    chords = detect_chords_from_midi(melody, key=key)

    # Should detect C Major roughly
    assert len(chords) > 0
    assert chords[0].root == 0

    timeline = MusicTimeline(chords=chords, keys=[KeyLabel(scale=key, start=0.0)])

    # Now generate a bass line
    from melodica.generators.bass import BassGenerator

    bass_gen = BassGenerator()
    bass_notes = bass_gen.render(chords, timeline, 4.0)

    assert len(bass_notes) > 0
    # Bass should roughly follow the roots
    for n in bass_notes:
        assert n.pitch < 60


def test_schillinger_rhythm_integration():
    """
    Test Schillinger rhythm generator (interference of 3 against 4).
    Should produce a pattern of 12 units.
    """
    # 3 vs 4 at 4 units per beat = 3 beats total cycle
    gen = SchillingerGenerator(a=3, b=4, units_per_beat=4)
    events = gen.generate(3.0)

    # 3 units: hits at 0, 3, 6, 9, 12
    # 4 units: hits at 0, 4, 8, 12
    # Combined onsets: 0, 3, 4, 6, 8, 9, 12
    # Intervals: 3, 1, 2, 2, 1, 3 (Total 12 units = 3 beats)
    assert len(events) == 6
    assert events[0].onset == 0.0
    assert events[1].onset == 0.75  # 3/4
    assert events[2].onset == 1.0  # 4/4


def test_rhythm_library_integration():
    """
    Test that rhythms from the library can be used in generators.
    """
    rhythm = get_rhythm("straight_8_triplets")
    # Arpeggiator with triplet rhythm
    gen = ArpeggiatorGenerator(rhythm=rhythm)
    chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
    key = Scale(root=0, mode=Mode.MAJOR)

    notes = gen.render(chords, key, 4.0)

    # 3 notes per beat * 4 beats = 12 notes
    assert len(notes) == 12
    # Each note should be roughly 0.333 apart
    diff = notes[1].start - notes[0].start
    assert abs(diff - 0.333333) < 0.001


def test_follow_rhythm_integration():
    """
    Test that one track can follow the rhythm of another.
    """
    # 1. Source track (Melody) - syncopated
    melody_notes = [
        NoteInfo(60, 0.0, 0.25),
        NoteInfo(62, 0.75, 0.25),
        NoteInfo(64, 1.0, 0.5),
    ]

    # 2. Current track (Chords) - originally just a block chord
    chord_notes = [
        NoteInfo(48, 0.0, 4.0),
        NoteInfo(52, 0.0, 4.0),
        NoteInfo(55, 0.0, 4.0),
    ]

    # 3. Apply FollowRhythmModifier
    mod = FollowRhythmModifier(source_track="Melody")
    ctx = ModifierContext(
        duration_beats=4.0,
        chords=[],
        timeline=None,  # type: ignore
        scale=Scale(0, Mode.MAJOR),
        tracks={"Melody": melody_notes},
    )

    result = mod.modify(chord_notes, ctx)

    # 4. Verify
    # We expect 3 groups of notes (one for each melody onset)
    # Each group should have 3 notes (the chord tones)
    assert len(result) == 3 * 3

    onsets = sorted(list(set(n.start for n in result)))
    assert onsets == [0.0, 0.75, 1.0]

    # Check durations match melody
    durations = {n.start: n.duration for n in result}
    assert durations[0.0] == 0.25
    assert durations[0.75] == 0.25
    assert durations[1.0] == 0.5
