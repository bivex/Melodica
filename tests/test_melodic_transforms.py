# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.melodic_transforms import (
    diatonic_inversion,
    diatonic_retrograde,
    diatonic_augmentation,
    diatonic_diminution,
    diatonic_retrograde_inversion,
    melodic_inversion,
    melodic_retrograde,
    melodic_augmentation,
    melodic_diminution,
    melodic_retrograde_inversion,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)  # C, D, E, F, G, A, B


def test_diatonic_inversion():
    # C4 -> E4 -> G4 (scale degree indices 0, 2, 4 in C major)
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0),
        NoteInfo(pitch=64, start=1.0, duration=1.0),
        NoteInfo(pitch=67, start=2.0, duration=1.0),
    ]

    # Invert around C4 (60)
    # Degree index C4 (0) -> 0. Inverted: 0 - 0 = 0 -> C4 (60)
    # Degree index E4 (2) -> 2. Inverted: 0 - 2 = -2 -> 5th degree in octave 4, i.e., A3 (57)
    # Degree index G4 (4) -> 4. Inverted: 0 - 4 = -4 -> 3rd degree in octave 4, i.e., F3 (53)
    inverted = diatonic_inversion(notes, C_MAJOR)
    assert len(inverted) == 3
    assert inverted[0].pitch == 60
    assert inverted[1].pitch == 57
    assert inverted[2].pitch == 53

    # Check that melodic_inversion behaves exactly the same
    mel_inverted = melodic_inversion(notes, C_MAJOR)
    assert [n.pitch for n in mel_inverted] == [60, 57, 53]


def test_diatonic_retrograde():
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0),
        NoteInfo(pitch=64, start=1.0, duration=1.0),
        NoteInfo(pitch=67, start=2.0, duration=2.0),
    ]
    # Total end time = 2.0 + 2.0 = 4.0
    # Retrograde:
    # Note 1 (67) start = 4.0 - (2.0 + 2.0) = 0.0, dur = 2.0
    # Note 2 (64) start = 4.0 - (1.0 + 1.0) = 2.0, dur = 1.0
    # Note 3 (60) start = 4.0 - (0.0 + 1.0) = 3.0, dur = 1.0
    retro = diatonic_retrograde(notes)
    assert len(retro) == 3
    assert retro[0].pitch == 67
    assert retro[0].start == 0.0
    assert retro[0].duration == 2.0
    
    assert retro[1].pitch == 64
    assert retro[1].start == 2.0
    
    assert retro[2].pitch == 60
    assert retro[2].start == 3.0

    # Check that melodic_retrograde behaves exactly the same
    mel_retro = melodic_retrograde(notes)
    assert [n.pitch for n in mel_retro] == [67, 64, 60]


def test_diatonic_augmentation_diminution():
    notes = [
        NoteInfo(pitch=60, start=1.0, duration=2.0),
    ]
    aug = diatonic_augmentation(notes, factor=2.0)
    assert aug[0].start == 2.0
    assert aug[0].duration == 4.0

    dim = diatonic_diminution(notes, factor=2.0)
    assert dim[0].start == 0.5
    assert dim[0].duration == 1.0

    # Check that melodic_* behaves exactly the same
    mel_aug = melodic_augmentation(notes, factor=2.0)
    assert mel_aug[0].start == 2.0
    assert mel_aug[0].duration == 4.0

    mel_dim = melodic_diminution(notes, factor=2.0)
    assert mel_dim[0].start == 0.5
    assert mel_dim[0].duration == 1.0


def test_diatonic_retrograde_inversion():
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0),
        NoteInfo(pitch=64, start=1.0, duration=1.0),
    ]
    # Inversion: 60 (at 0.0), 57 (at 1.0)
    # Retrograde of that: 57 (at 0.0), 60 (at 1.0)
    ri = diatonic_retrograde_inversion(notes, C_MAJOR)
    assert len(ri) == 2
    assert ri[0].pitch == 57
    assert ri[0].start == 0.0
    assert ri[1].pitch == 60
    assert ri[1].start == 1.0

    # Check that melodic_retrograde_inversion behaves exactly the same
    mel_ri = melodic_retrograde_inversion(notes, C_MAJOR)
    assert [n.pitch for n in mel_ri] == [57, 60]
