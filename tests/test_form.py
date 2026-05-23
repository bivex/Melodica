# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

import pytest
from melodica.types import Scale, Mode
from melodica.form import FormSection, MusicalForm

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def test_form_section_creation():
    sec = FormSection(
        name="intro",
        start_beat=0.0,
        duration_beats=16.0,
        dynamics="pp",
        tempo_multiplier=0.8,
        active_families=["strings"],
        mood="tense",
    )
    assert sec.name == "intro"
    assert sec.start_beat == 0.0
    assert sec.end_beat == 16.0
    assert sec.dynamics == "pp"
    assert sec.tempo_multiplier == 0.8
    assert sec.active_families == ["strings"]


def test_sonata_form():
    form = MusicalForm.sonata(C_MAJOR, 240.0)
    assert len(form.sections) == 5
    assert form.sections[0].name == "intro"
    assert form.sections[1].name == "exposition"
    assert form.sections[2].name == "development"
    assert form.sections[3].name == "recapitulation"
    assert form.sections[4].name == "coda"

    # Total beats check
    total_dur = sum(sec.duration_beats for sec in form.sections)
    assert abs(total_dur - 240.0) < 0.01
    
    # Verify tempo map exists and covers the form
    assert len(form.tempo_map) > 0
    assert form.tempo_map[0][0] == 0.0


def test_ternary_form():
    form = MusicalForm.ternary(C_MAJOR, 120.0)
    assert len(form.sections) == 3
    assert form.sections[0].name == "A"
    assert form.sections[1].name == "B"
    assert form.sections[2].name == "A_prime"

    total_dur = sum(sec.duration_beats for sec in form.sections)
    assert abs(total_dur - 120.0) < 0.01


def test_rondo_form():
    form = MusicalForm.rondo(C_MAJOR, 200.0)
    assert len(form.sections) == 5
    assert form.sections[0].name == "A1"
    assert form.sections[4].name == "A3"

    total_dur = sum(sec.duration_beats for sec in form.sections)
    assert abs(total_dur - 200.0) < 0.01
