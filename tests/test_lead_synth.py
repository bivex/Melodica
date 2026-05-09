# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""tests/test_lead_synth.py — Tests for LeadSynthGenerator."""

import pytest
from melodica.generators.lead_synth import LeadSynthGenerator
from melodica.generators import GeneratorParams
from melodica.types import ChordLabel, Mode, NoteInfo, Quality, Scale
from melodica.render_context import RenderContext

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords():
    return [
        ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0),
        ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0),
        ChordLabel(root=9, quality=Quality.MINOR, start=8.0, duration=4.0),
        ChordLabel(root=5, quality=Quality.MAJOR, start=12.0, duration=4.0),
    ]


class TestLeadSynthBasic:
    """Basic generation tests."""

    def test_generates_notes(self):
        gen = LeadSynthGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 16.0, None)
        assert len(notes) > 0

    def test_notes_within_key_range(self):
        params = GeneratorParams(key_range_low=60, key_range_high=72)
        gen = LeadSynthGenerator(params=params)
        notes = gen.render(_simple_chords(), C_MAJOR, 16.0, None)
        for n in notes:
            assert 60 <= n.pitch <= 72

    def test_all_notes_have_required_fields(self):
        gen = LeadSynthGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0, None)
        for n in notes:
            assert isinstance(n.pitch, int)
            assert isinstance(n.start, float)
            assert isinstance(n.duration, float)
            assert isinstance(n.velocity, int)
            assert 0 <= n.velocity <= 127

    def test_notes_start_positive(self):
        gen = LeadSynthGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0, None)
        assert all(n.start >= 0 for n in notes)


class TestLeadSynthStyles:
    """Style-specific behaviour."""

    def test_techno_produces_dense_notes(self):
        gen_techno = LeadSynthGenerator(style="techno", note_length="staccato")
        gen_retro = LeadSynthGenerator(style="retro", note_length="staccato")
        notes_techno = gen_techno.render(_simple_chords(), C_MAJOR, 8.0, None)
        notes_retro = gen_retro.render(_simple_chords(), C_MAJOR, 8.0, None)
        # Techno should be significantly denser
        assert len(notes_techno) > len(notes_retro) * 2

    def test_retro_less_dense(self):
        gen_retro = LeadSynthGenerator(style="retro", note_length="staccato")
        notes = gen_retro.render(_simple_chords(), C_MAJOR, 8.0, None)
        # Retro uses step=1.0 → approx one note per beat
        # 8 beats → expect ~8 notes (allow ±2 due to edge conditions)
        assert 6 <= len(notes) <= 10

    def test_trance_legato_long_duration(self):
        gen = LeadSynthGenerator(style="trance", note_length="legato")
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0, None)
        if notes:
            avg_dur = sum(n.duration for n in notes) / len(notes)
            # Legato notes are long (typically > 0.5 beat)
            assert avg_dur > 0.3

    def test_staccato_short_duration(self):
        gen = LeadSynthGenerator(style="techno", note_length="staccato")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0, None)
        if notes:
            max_dur = max(n.duration for n in notes)
            # Staccato notes are short (< 0.5)
            assert max_dur < 0.6


class TestLeadSynthArticulation:
    """Articulation logic."""

    def test_mixed_alternates(self):
        gen = LeadSynthGenerator(style="retro", note_length="mixed")
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0, None)
        # Mixed: even-index notes longer, odd shorter (see code)
        durations = [n.duration for n in notes]
        # We can't guarantee strict alternation due to rhythm generation,
        # but we can check there is variance > 20% of mean
        mean = sum(durations) / len(durations)
        variances = [abs(d - mean) for d in durations]
        assert max(variances) > 0.2 * mean


class TestLeadSynthHarmony:
    """Harmonic constraints."""

    def test_notes_belong_to_current_chord(self):
        """All generated notes should be chord tones of the chord at their start."""
        gen = LeadSynthGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 16.0, None)
        for n in notes:
            # Determine which chord this note belongs to
            chord = None
            for c in _simple_chords():
                if c.start <= n.start < c.end:
                    chord = c
                    break
            assert chord is not None, f"Note at {n.start} outside chords"
            # Pitch class must be in chord's pitch classes
            pc = n.pitch % 12
            assert pc in chord.pitch_classes(), (
                f"Pitch class {pc} not in chord {chord.root} {chord.quality}"
            )

    def test_notes_within_scale(self):
        """Notes should belong to the scale (not necessarily chord tones on weak beats)."""
        gen = LeadSynthGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 16.0, None)
        scale_degrees = C_MAJOR.degrees()
        for n in notes:
            pc = n.pitch % 12
            # Allow any scale degree (including passing tones)
            # But LeadSynth only picks chord tones, so this should hold
            assert any(abs(pc - d) < 0.5 for d in scale_degrees), (
                f"Pitch class {pc} not in scale {scale_degrees}"
            )


class TestLeadSynthParameters:
    """Parameter bounds."""

    def test_density_affects_velocity(self):
        low_density = GeneratorParams(density=0.2)
        high_density = GeneratorParams(density=0.9)
        gen_low = LeadSynthGenerator(params=low_density)
        gen_high = LeadSynthGenerator(params=high_density)
        notes_low = gen_low.render(_simple_chords(), C_MAJOR, 8.0, None)
        notes_high = gen_high.render(_simple_chords(), C_MAJOR, 8.0, None)
        # Density affects base velocity: higher density → higher velocity
        avg_low = sum(n.velocity for n in notes_low) / len(notes_low)
        avg_high = sum(n.velocity for n in notes_high) / len(notes_high)
        assert avg_high > avg_low

    def test_invalid_style_raises(self):
        with pytest.raises(ValueError):
            LeadSynthGenerator(style="invalid_style")

    def test_invalid_note_length_raises(self):
        with pytest.raises(ValueError):
            LeadSynthGenerator(note_length="invalid")

    def test_portamento_clamped(self):
        gen = LeadSynthGenerator(portamento=5.0)  # too high
        assert 0.0 <= gen.portamento <= 1.0

    def test_vibrato_rate_clamped(self):
        gen = LeadSynthGenerator(vibrato_rate=0.01)
        assert 0.1 <= gen.vibrato_rate <= 2.0
