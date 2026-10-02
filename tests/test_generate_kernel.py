# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import math
import pytest
from melodica.types import ChordLabel, NoteInfo, Scale, Mode
from melodica.theory.chords import Quality
from melodica.generate.kernel import (
    apply_note_density,
    resolve_bounded_pitch,
    fit_to_range,
    generate_lfo_cc,
    limit_polyphony,
    apply_phrase_arch,
    apply_dynamic_curve,
)

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_apply_note_density():
    chords = [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=1.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=1.0, duration=1.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=2.0, duration=1.0),
        ChordLabel(root=0, quality=Quality.MAJOR, start=3.0, duration=1.0),
    ]
    # Full density
    assert len(apply_note_density(chords, 1.0)) == 4
    # Thinning
    assert len(apply_note_density(chords, 0.5)) == 2
    # Zero density
    assert len(apply_note_density(chords, 0.0)) == 0


def test_resolve_bounded_pitch():
    # Pitch class 0 (C) with anchor around C4 (60)
    pitch = resolve_bounded_pitch(0, 60, C_MAJOR, 50, 70)
    assert pitch == 60

    # Bounds enforcement
    pitch_high = resolve_bounded_pitch(0, 80, C_MAJOR, 50, 65)
    assert pitch_high <= 65
    assert pitch_high >= 50


def test_fit_to_range():
    assert fit_to_range(36, 48, 72) == 48
    assert fit_to_range(84, 48, 72) == 72
    assert fit_to_range(60, 48, 72) == 60


def test_generate_lfo_cc():
    points = generate_lfo_cc(duration=1.0, hz=5.0, base=80, depth=10, step=0.05)
    assert len(points) == 20
    assert all(0 <= p[1] <= 127 for p in points)
    assert any(p[1] >= 85 for p in points)
    assert any(p[1] <= 75 for p in points)


def test_limit_polyphony():
    # 4 notes starting at the same time
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=2.0, velocity=50),
        NoteInfo(pitch=64, start=0.0, duration=2.0, velocity=70),
        NoteInfo(pitch=67, start=0.0, duration=2.0, velocity=80),
        NoteInfo(pitch=71, start=0.0, duration=2.0, velocity=90),
    ]
    limited = limit_polyphony(notes, max_polyphony=2)
    assert len(limited) == 2
    # Loudest notes retained
    pitches = {n.pitch for n in limited}
    assert pitches == {67, 71}


def test_apply_phrase_arch():
    notes = [
        NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=60),
        NoteInfo(pitch=62, start=1.0, duration=1.0, velocity=60),
        NoteInfo(pitch=64, start=2.0, duration=1.0, velocity=60),
    ]
    arched = apply_phrase_arch(notes, arch_strength=0.3)
    assert len(arched) == 3
    # Center note should be louder than start and end
    assert arched[1].velocity > arched[0].velocity
    assert arched[1].velocity > arched[2].velocity


def test_apply_dynamic_curve():
    assert apply_dynamic_curve(vel=60, progress=0.0, curve="crescendo", base=60) == 60
    assert apply_dynamic_curve(vel=60, progress=1.0, curve="crescendo", base=60) == 90
    assert apply_dynamic_curve(vel=60, progress=0.0, curve="decrescendo", base=60) == 90
    assert apply_dynamic_curve(vel=60, progress=1.0, curve="decrescendo", base=60) == 60
