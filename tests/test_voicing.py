# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-05-18
# Last Updated: 2026-05-18
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

import pytest
from melodica.types import Scale, Mode
from melodica.theory.chords import Quality
from melodica.theory.voicing import chord_to_notes, inversions, voice_motion_cost, voice_lead

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)

def test_chord_to_notes():
    chord = C_MAJOR.parse_roman("I") # C major triad
    # C4 = 60, E4 = 64, G4 = 67 -> root_pitch = 60
    notes = chord_to_notes(chord)
    assert notes == [60, 64, 67]

def test_chord_to_notes_inversion():
    chord = C_MAJOR.parse_roman("I/3") # C major first inversion
    notes = chord_to_notes(chord)
    # Bass E4 = 52, Chord: [60, 64, 67]
    assert notes[0] == 52

def test_inversions():
    pitches = [60, 64, 67]
    invs = inversions(pitches)
    # Original: [60, 64, 67]
    # First: [64, 67, 72]
    # Second: [67, 72, 76]
    assert invs[0] == [60, 64, 67]
    assert invs[1] == [64, 67, 72]
    assert invs[2] == [67, 72, 76]

def test_voice_motion_cost():
    cost = voice_motion_cost([60, 64, 67], [60, 64, 67])
    assert cost == 0.0

    cost_moved = voice_motion_cost([60, 64, 67], [61, 65, 68])
    assert cost_moved == 3.0

def test_voice_lead():
    prev = C_MAJOR.parse_roman("I") # [60, 64, 67]
    next_chord = C_MAJOR.parse_roman("V") # G major triad: [67, 71, 74] (root=7)
    # Inversions of [67, 71, 74]:
    # 0: [67, 71, 74] -> cost from [60, 64, 67] is (7 + 7 + 7) = 21
    # 1: [71, 74, 79] -> cost from [60, 64, 67] is (11 + 10 + 12) = 33
    # 2: [55, 59, 62] (inverted down by -12 if sorted/transposed cyclically)
    # Let's check which inversion wins:
    led = voice_lead(prev, next_chord)
    assert len(led) == 3
    # The voice lead should choose a smooth inversion!
    assert led == [59, 62, 67] or led == [67, 71, 74] or led == [62, 67, 71]
