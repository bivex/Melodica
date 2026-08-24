# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import NoteInfo, Scale, Mode
from melodica.form import FormSection, MusicalForm
from melodica.form_validator import FormValidator, FormIssue, validate

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
G_MAJOR = Scale(root=7, mode=Mode.MAJOR)


def test_form_validator_defaults():
    validator = FormValidator()
    assert len(validator.rules) == 2


def test_form_validator_empty_tracks():
    issues = validate({}, bpm=120.0)
    assert issues == []


def test_arrangement_registers_and_density():
    # Tracks with notes spanning all registers and staggered entrance
    tracks_data = {
        "bass": [
            NoteInfo(pitch=36, start=0.0, duration=4.0, velocity=80),
            NoteInfo(pitch=40, start=4.0, duration=4.0, velocity=85),
        ],
        "lead": [
            NoteInfo(pitch=60, start=2.0, duration=4.0, velocity=75),
            NoteInfo(pitch=88, start=6.0, duration=4.0, velocity=90),
        ],
    }
    validator = FormValidator()
    issues = validator.validate(tracks_data, bpm=120.0)
    # Check that it executed without error and produced structured FormIssue items
    assert isinstance(issues, list)
    for issue in issues:
        assert isinstance(issue, FormIssue)
        assert issue.code.startswith("ARR-") or issue.code.startswith("FORM-")


def test_form_sonata_validation():
    form = MusicalForm.sonata(C_MAJOR, 120.0)
    tracks_data = {
        "violin": [
            NoteInfo(pitch=64, start=0.0, duration=16.0, velocity=70),
            NoteInfo(pitch=67, start=16.0, duration=32.0, velocity=85),
            NoteInfo(pitch=69, start=48.0, duration=32.0, velocity=90),
            NoteInfo(pitch=64, start=80.0, duration=32.0, velocity=80),
            NoteInfo(pitch=60, start=112.0, duration=8.0, velocity=60),
        ],
        "cello": [
            NoteInfo(pitch=36, start=0.0, duration=120.0, velocity=75),
        ]
    }
    validator = FormValidator()
    issues = validator.validate(tracks_data, bpm=120.0, form=form)
    assert isinstance(issues, list)
