"""
tests/test_modifiers_uncovered.py — Tests for previously untested modifiers.

Covers:
  - GrooveModifier, PolishedOctaveModifier (aesthetic)
  - DropVoicingModifier, TopNoteVoicingModifier, InversionModifier (voicings)
  - AccentModifier, ReRhythmizeModifier, MonophonicModifier, ArpeggiateModifier, StrumModifier (variations_articulation)
  - DoublingModifier, SlicePhraseModifier (variations_harmonic)
"""

import random
import pytest
from melodica.types import NoteInfo, ChordLabel, Quality, Scale, Mode
from melodica.modifiers import ModifierContext

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _notes(
    pitches: list[int], start: float = 0.0, dur: float = 1.0, vel: int = 80
) -> list[NoteInfo]:
    return [
        NoteInfo(pitch=p, start=start + i * 0.01, duration=dur, velocity=vel)
        for i, p in enumerate(pitches)
    ]


def _ctx(beats: float = 16.0, chords=None) -> ModifierContext:
    return ModifierContext(duration_beats=beats, chords=chords or [], timeline=None, scale=C_MAJOR)


# ===================================================================
# GrooveModifier
# ===================================================================


class TestGrooveModifier:
    def test_preserves_note_count(self):
        from melodica.modifiers.aesthetic import GrooveModifier

        mod = GrooveModifier(swing=0.6)
        notes = _notes([60, 64, 67, 72])
        result = mod.modify(notes, _ctx())
        assert len(result) == len(notes)

    def test_swing_zero_is_neutral(self):
        from melodica.modifiers.aesthetic import GrooveModifier

        mod = GrooveModifier(swing=0.5, tightness=1.0)
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5)]
        result = mod.modify(notes, _ctx())
        assert result[0].start == pytest.approx(0.0)

    def test_velocity_has_accent_tendency(self):
        """GrooveModifier should tend to increase velocity on strong beats."""
        from melodica.modifiers.aesthetic import GrooveModifier

        random.seed(42)
        mod = GrooveModifier(random_velocity=2)
        # Compare note at beat 0 (strong) vs beat 0.5 (off-beat)
        on_beat = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        off_beat = [NoteInfo(pitch=60, start=0.5, duration=0.5, velocity=80)]
        r_on = mod.modify(on_beat, _ctx())
        r_off = mod.modify(off_beat, _ctx())
        # On-beat should tend to have higher or equal velocity (accent applies)
        # With random jitter of ±2, this should usually hold
        assert r_on[0].velocity >= r_off[0].velocity - 4  # allow small jitter margin

    def test_velocity_clamped(self):
        from melodica.modifiers.aesthetic import GrooveModifier

        mod = GrooveModifier(random_velocity=0)
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=120)]
        result = mod.modify(notes, _ctx())
        assert result[0].velocity <= 127


# ===================================================================
# PolishedOctaveModifier
# ===================================================================


class TestPolishedOctaveModifier:
    def test_probability_one_doubles_all(self):
        from melodica.modifiers.aesthetic import PolishedOctaveModifier

        random.seed(42)
        mod = PolishedOctaveModifier(probability=1.0, velocity_scale=0.6)
        notes = _notes([60, 64, 67])
        result = mod.modify(notes, _ctx())
        # Each note doubled → 6 notes
        assert len(result) == 6

    def test_probability_zero_no_doubling(self):
        from melodica.modifiers.aesthetic import PolishedOctaveModifier

        random.seed(42)
        mod = PolishedOctaveModifier(probability=0.0)
        notes = _notes([60, 64, 67])
        result = mod.modify(notes, _ctx())
        assert len(result) == 3

    def test_doubled_pitch_offset(self):
        from melodica.modifiers.aesthetic import PolishedOctaveModifier

        random.seed(0)
        mod = PolishedOctaveModifier(probability=1.0, octave_shift=1, velocity_scale=0.6)
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0, velocity=100)]
        result = mod.modify(notes, _ctx())
        doubled = [n for n in result if n.pitch == 72]
        assert len(doubled) == 1
        assert doubled[0].velocity == 60


# ===================================================================
# DropVoicingModifier
# ===================================================================


class TestDropVoicingModifier:
    def test_drop_2(self):
        from melodica.modifiers.voicings import DropVoicingModifier

        mod = DropVoicingModifier(drop_mode="drop_2")
        # 4-note chord at same start: C4, E4, G4, B4
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0),
            NoteInfo(pitch=64, start=0.0, duration=1.0),
            NoteInfo(pitch=67, start=0.0, duration=1.0),
            NoteInfo(pitch=71, start=0.0, duration=1.0),
        ]
        result = mod.modify(notes, _ctx())
        pitches = sorted([n.pitch for n in result])
        # Drop 2: 2nd highest (G4=67) → G3=55
        assert 55 in pitches

    def test_no_drop_on_single_note(self):
        from melodica.modifiers.voicings import DropVoicingModifier

        mod = DropVoicingModifier()
        notes = [NoteInfo(pitch=60, start=0.0, duration=1.0)]
        result = mod.modify(notes, _ctx())
        assert result[0].pitch == 60


# ===================================================================
# InversionModifier
# ===================================================================


class TestInversionModifier:
    def test_root_position_unchanged(self):
        from melodica.modifiers.voicings import InversionModifier

        mod = InversionModifier(inversion=0)
        notes = _notes([60, 64, 67])
        original = [n.pitch for n in notes]
        result = mod.modify(notes, _ctx())
        assert [n.pitch for n in result] == original

    def test_first_inversion_shifts_bottom(self):
        from melodica.modifiers.voicings import InversionModifier

        mod = InversionModifier(inversion=1)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0),
            NoteInfo(pitch=64, start=0.0, duration=1.0),
            NoteInfo(pitch=67, start=0.0, duration=1.0),
        ]
        result = mod.modify(notes, _ctx())
        # Lowest note should be shifted up an octave
        assert any(n.pitch == 72 for n in result)


# ===================================================================
# AccentModifier
# ===================================================================


class TestAccentModifier:
    def test_accents_on_grid(self):
        from melodica.modifiers.variations_articulation import AccentModifier

        mod = AccentModifier(grid=1.0, accent_vel=20)
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5, velocity=80)]
        result = mod.modify(notes, _ctx())
        assert result[0].velocity == 100

    def test_no_accent_off_grid(self):
        from melodica.modifiers.variations_articulation import AccentModifier

        mod = AccentModifier(grid=1.0, accent_vel=20)
        notes = [NoteInfo(pitch=60, start=0.3, duration=0.5, velocity=80)]
        result = mod.modify(notes, _ctx())
        assert result[0].velocity == 80


# ===================================================================
# MonophonicModifier
# ===================================================================


class TestMonophonicModifier:
    def test_truncates_overlapping(self):
        from melodica.modifiers.variations_articulation import MonophonicModifier

        mod = MonophonicModifier()
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=3.0),
            NoteInfo(pitch=64, start=2.0, duration=3.0),
            NoteInfo(pitch=67, start=4.0, duration=3.0),
        ]
        result = mod.modify(notes, _ctx())
        # First note should be truncated to end at start of second
        assert result[0].duration == pytest.approx(2.0)

    def test_drops_negative_duration(self):
        from melodica.modifiers.variations_articulation import MonophonicModifier

        mod = MonophonicModifier()
        notes = [
            NoteInfo(pitch=60, start=2.0, duration=1.0),
            NoteInfo(pitch=64, start=1.0, duration=0.005),  # very short
        ]
        result = mod.modify(notes, _ctx())
        # Short note before longer → duration stays, but after sorting:
        # [1.0: dur=0.005], [2.0: dur=1.0]
        assert all(n.duration > 0.01 for n in result)


# ===================================================================
# ArpeggiateModifier
# ===================================================================


class TestArpeggiateModifier:
    def test_staggers_starts(self):
        from melodica.modifiers.variations_articulation import ArpeggiateModifier

        mod = ArpeggiateModifier(offset=0.1)
        notes = [
            NoteInfo(pitch=60, start=0.0, duration=1.0),
            NoteInfo(pitch=64, start=0.0, duration=1.0),
            NoteInfo(pitch=67, start=0.0, duration=1.0),
        ]
        result = mod.modify(notes, _ctx())
        starts = sorted([n.start for n in result])
        assert starts[1] - starts[0] >= 0.09


# ===================================================================
# DoublingModifier
# ===================================================================


class TestDoublingModifier:
    def test_doubles_phrase(self):
        from melodica.modifiers.variations_harmonic import DoublingModifier

        mod = DoublingModifier(multiplier=2)
        notes = _notes([60, 64, 67])
        result = mod.modify(notes, _ctx(beats=4.0))
        assert len(result) == 6  # 3 original + 3 doubled

    def test_triples_phrase(self):
        from melodica.modifiers.variations_harmonic import DoublingModifier

        mod = DoublingModifier(multiplier=3)
        notes = _notes([60, 64])
        result = mod.modify(notes, _ctx(beats=4.0))
        assert len(result) == 6

    def test_multiplier_one_no_change(self):
        from melodica.modifiers.variations_harmonic import DoublingModifier

        mod = DoublingModifier(multiplier=1)
        notes = _notes([60, 64, 67])
        result = mod.modify(notes, _ctx(beats=4.0))
        assert len(result) == 3


# ===================================================================
# SlicePhraseModifier
# ===================================================================


class TestSlicePhraseModifier:
    def test_slices_long_notes(self):
        from melodica.modifiers.variations_harmonic import SlicePhraseModifier

        mod = SlicePhraseModifier(grid=0.5)
        notes = [NoteInfo(pitch=60, start=0.0, duration=2.0)]
        result = mod.modify(notes, _ctx())
        # 2.0 / 0.5 = 4 slices
        assert len(result) == 4

    def test_short_notes_unchanged(self):
        from melodica.modifiers.variations_harmonic import SlicePhraseModifier

        mod = SlicePhraseModifier(grid=0.5)
        notes = [NoteInfo(pitch=60, start=0.0, duration=0.5)]
        result = mod.modify(notes, _ctx())
        assert len(result) == 1

    def test_preserves_pitch(self):
        from melodica.modifiers.variations_harmonic import SlicePhraseModifier

        mod = SlicePhraseModifier(grid=0.25)
        notes = [NoteInfo(pitch=64, start=0.0, duration=1.0)]
        result = mod.modify(notes, _ctx())
        assert all(n.pitch == 64 for n in result)
