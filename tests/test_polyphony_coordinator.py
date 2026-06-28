# Copyright (c) 2026 Bivex
# Licensed under the MIT License.

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.composer.polyphony_coordinator import PolyphonicVoiceCoordinator


def test_polyphony_coordinator_clash_resolution():
    # C major scale
    scale = Scale(0, Mode.MAJOR)
    coordinator = PolyphonicVoiceCoordinator(scale)

    tracks = {
        "solo_melody": [
            # High-priority solo note: pitch = 60 (C4), starts at 0.0, lasts 4.0
            NoteInfo(pitch=60, start=0.0, duration=4.0)
        ],
        "backing_pad": [
            # Low-priority pad note: pitch = 61 (C#4), overlaps and clashes (interval of 1)
            # Should be shifted diatonically up to D (62) or down to B (59)
            NoteInfo(pitch=61, start=1.0, duration=2.0)
        ]
    }

    resolved = coordinator.coordinate(tracks)
    
    # Solo melody should remain unchanged (pitch 60)
    assert resolved["solo_melody"][0].pitch == 60
    
    # Backing pad note should have resolved its clash (interval not in (0, 1, 2, 6))
    new_pitch = resolved["backing_pad"][0].pitch
    assert new_pitch != 61
    
    # Pitch difference should not be 0, 1, 2, or 6
    diff = abs(new_pitch - 60) % 12
    assert diff not in (0, 1, 2, 6)
