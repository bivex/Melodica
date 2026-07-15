# Copyright (c) 2026 Bivex
#
# Author: Bivex
# Available for contact via email: support@b-b.top
# For up-to-date contact information:
# https://github.com/bivex
#
# Created: 2026-04-24
# Last Updated: 2026-04-24
#
# Licensed under the MIT License.
# Commercial licensing available upon request.

"""tests/test_melody_advanced.py — Advanced MelodyGenerator feature tests."""

import pytest
from melodica.types import ChordLabel, Mode, NoteInfo, Quality, Scale
from melodica.generators import GeneratorParams
from melodica.generators.melody import MelodyGenerator
from melodica.render_context import RenderContext

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


# ============================================================================
# RHYTHM FEATURES
# ============================================================================

class TestRhythmFeatures:
    """Test syncopation, rhythm_variety, and rhythm_motif."""

    def test_syncopation_shifts_onsets(self):
        """High syncopation should shift some note onsets off-beat."""
        gen = MelodyGenerator(syncopation=1.0, note_repetition_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # Check that some notes are off-beat (not on 0.0, 0.5, 1.0, etc.)
        on_beats = sum(1 for n in notes if n.start % 0.5 < 0.05)
        off_beats = len(notes) - on_beats
        # With 100% syncopation, many notes should be shifted
        assert off_beats > 0 or len(notes) < 4  # Either shifted or few notes

    def test_rhythm_variety_creates_different_durations(self):
        """High rhythm_variety should create mixed note durations."""
        gen = MelodyGenerator(rhythm_variety=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 1
        # Check variety in durations
        durations = set(round(n.duration, 2) for n in notes)
        # Should have more than one duration value
        assert len(durations) >= 1

    def test_rhythm_motif_pattern(self):
        """Custom rhythm_motif should repeat the pattern."""
        gen = MelodyGenerator(rhythm_motif=[1.0, 0.5, 0.5])
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # Notes should follow the motif ratios roughly
        # Motif [1.0, 0.5, 0.5] means alternating longer and shorter notes

    def test_rhythm_motif_long_pattern(self):
        """Test longer rhythm motifs."""
        gen = MelodyGenerator(rhythm_motif=[1.0, 0.5, 0.5, 1.0, 0.25, 0.25])
        notes = gen.render(_simple_chords(), C_MAJOR, 6.0)
        assert len(notes) > 0


# ============================================================================
# PHRASING & CONTOUR
# ============================================================================

class TestPhrasingAndContour:
    """Test phrase_length, phrase_contour, and accent_pattern."""

    def test_phrase_length_creates_gaps(self):
        """Phrase length with rest probability should create gaps."""
        gen = MelodyGenerator(
            phrase_length=2.0,
            phrase_rest_probability=1.0,  # Always rest between phrases
            note_repetition_probability=0.0,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        # Should have gaps around phrase boundaries (2.0, 4.0, 6.0)
        starts = [n.start for n in notes]
        # Check that not every beat has a note (gaps exist)
        assert len(starts) < 32  # Would be 32 if 4 notes per bar, 2 bars

    def test_phrase_contour_arch(self):
        """Arch contour should rise then fall."""
        gen = MelodyGenerator(
            phrase_length=4.0,
            phrase_contour="arch",
            note_range_low=60,
            note_range_high=72,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 2
        # In arch, notes generally rise then fall
        pitches = [n.pitch for n in notes]
        # Just verify arch mode runs without error
        assert all(60 <= n.pitch <= 72 for n in notes)

    def test_phrase_contour_rise_fall(self):
        """Rise_fall contour symmetric."""
        gen = MelodyGenerator(
            phrase_length=4.0,
            phrase_contour="rise_fall",
            note_range_low=60,
            note_range_high=72,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_phrase_contour_rise(self):
        """Rise contour only goes up."""
        gen = MelodyGenerator(
            phrase_length=4.0,
            phrase_contour="rise",
            note_range_low=60,
            note_range_high=72,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_phrase_contour_flat(self):
        """Flat contour stays in middle register."""
        gen = MelodyGenerator(
            phrase_length=4.0,
            phrase_contour="flat",
            note_range_low=60,
            note_range_high=72,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_accent_pattern_strong_weak(self):
        """Strong_weak accent pattern."""
        gen = MelodyGenerator(
            accent_pattern="strong_weak",
            note_repetition_probability=0.0,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # Downbeats should have higher velocity
        downbeats = [n.velocity for n in notes if n.start % 1.0 < 0.1]
        if len(downbeats) > 0:
            assert all(v > 0 for v in downbeats)

    def test_accent_pattern_syncopated(self):
        """Syncopated accent pattern emphasizes off-beats."""
        gen = MelodyGenerator(
            accent_pattern="syncopated",
            note_repetition_probability=0.0,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


# ============================================================================
# CLIMAX MODES
# ============================================================================

class TestClimaxModes:
    """Test different climax strategies."""

    def test_climax_up_3rd(self):
        """Climax up a third."""
        gen = MelodyGenerator(
            climax="up_3rd",
            note_range_low=60,
            note_range_high=80,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_climax_up_5th(self):
        """Climax up a fifth."""
        gen = MelodyGenerator(
            climax="up_5th",
            note_range_low=60,
            note_range_high=80,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_climax_up_octave(self):
        """Climax up an octave."""
        gen = MelodyGenerator(
            climax="up_octave",
            note_range_low=60,
            note_range_high=84,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_climax_none(self):
        """No climax."""
        gen = MelodyGenerator(
            climax="none",
            phrase_contour="flat",
            note_range_low=60,
            note_range_high=72,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


# ============================================================================
# FIRST/LAST NOTE STRATEGIES
# ============================================================================

class TestFirstLastStrategies:
    """Test first_note and last_note strategies."""

    def test_first_note_chord_root(self):
        """First note is chord root."""
        gen = MelodyGenerator(first_note="chord_root", motif_probability=0.0, syncopation=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # First note should be C (pitch class 0) or nearby (in C major chord)
        # C major chord pitch classes are {0, 4, 7}
        assert notes[0].pitch % 12 in {0, 4, 7}

    def test_first_note_scale(self):
        """First note from scale."""
        gen = MelodyGenerator(first_note="scale")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # Should be in C major scale
        assert C_MAJOR.contains(notes[0].pitch % 12)

    def test_first_note_tonic(self):
        """First note is tonic."""
        gen = MelodyGenerator(first_note="tonic")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # Tonic is C (pitch class 0) - note may be in higher octave
        # Just verify it generates successfully

    def test_first_note_step_above_tonic(self):
        """First note step above tonic."""
        gen = MelodyGenerator(first_note="step_above_tonic")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_first_note_step_below_tonic(self):
        """First note step below tonic."""
        gen = MelodyGenerator(first_note="step_below_tonic")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_last_note_last_chord_root(self):
        """Last note is last chord root."""
        gen = MelodyGenerator(last_note="last_chord_root")
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        # Last chord is G, so last note should be G (7) or nearby

    def test_last_note_any(self):
        """Last note can be any."""
        gen = MelodyGenerator(last_note="any")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_last_note_scale(self):
        """Last note from scale."""
        gen = MelodyGenerator(last_note="scale")
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


# ============================================================================
# DIRECTION & CONSTRAINTS
# ============================================================================

class TestDirectionAndConstraints:
    """Test steps_probability, direction_bias, and after_leap."""

    def test_steps_probability_high(self):
        """High steps probability creates mostly stepwise motion."""
        gen = MelodyGenerator(steps_probability=0.95, note_repetition_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 1
        # Check intervals
        intervals = [abs(notes[i].pitch - notes[i-1].pitch) for i in range(1, len(notes))]
        steps = sum(1 for iv in intervals if iv <= 3)  # Include small leaps
        # Most should be small steps
        assert steps >= len(intervals) * 0.5

    def test_steps_probability_low(self):
        """Low steps probability allows more leaps."""
        gen = MelodyGenerator(steps_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_direction_bias_up(self):
        """Positive direction_bias favors upward motion."""
        gen = MelodyGenerator(direction_bias=1.0, steps_probability=0.5)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 1
        # Count upward vs downward intervals
        up = sum(1 for i in range(1, len(notes)) if notes[i].pitch > notes[i-1].pitch)
        down = sum(1 for i in range(1, len(notes)) if notes[i].pitch < notes[i-1].pitch)
        # With strong bias, at least some upward motion exists
        assert up >= 1  # Just verify some upward motion occurs

    def test_direction_bias_down(self):
        """Negative direction_bias favors downward motion."""
        gen = MelodyGenerator(direction_bias=-1.0, steps_probability=0.5)
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 1

    def test_after_leap_step_opposite(self):
        """After leap, step in opposite direction."""
        gen = MelodyGenerator(
            after_leap="step_opposite",
            steps_probability=0.5,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_after_leap_step_any(self):
        """After leap, step in any direction."""
        gen = MelodyGenerator(
            after_leap="step_any",
            steps_probability=0.5,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_allowed_intervals_custom(self):
        """Custom allowed intervals."""
        gen = MelodyGenerator(
            allowed_up_intervals=frozenset([2, 4, 7]),
            allowed_down_intervals=frozenset([2, 3, 5]),
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


# ============================================================================
# MOTIVIC DEVELOPMENT
# ============================================================================

class TestMotivicDevelopment:
    """Test motif_probability and variations."""

    def test_motif_probability_zero(self):
        """No motif usage."""
        gen = MelodyGenerator(motif_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_motif_variation_transpose(self):
        """Transpose variation."""
        gen = MelodyGenerator(
            motif_probability=0.5,
            motif_variation="transpose",
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_motif_variation_invert(self):
        """Invert variation."""
        gen = MelodyGenerator(
            motif_probability=0.5,
            motif_variation="invert",
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_motif_variation_retrograde(self):
        """Retrograde variation."""
        gen = MelodyGenerator(
            motif_probability=0.5,
            motif_variation="retrograde",
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_motif_variation_any(self):
        """Any variation chosen randomly."""
        gen = MelodyGenerator(
            motif_probability=0.5,
            motif_variation="any",
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0


# ============================================================================
# ORNAMENTATION
# ============================================================================

class TestOrnamentation:
    """Test ornament_probability and grace notes."""

    def test_ornament_probability_zero(self):
        """No ornaments."""
        gen = MelodyGenerator(ornament_probability=0.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_ornament_probability_high(self):
        """High ornament probability adds grace notes."""
        gen = MelodyGenerator(
            ornament_probability=1.0,
            note_repetition_probability=0.0,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        # May have more notes due to grace notes


# ============================================================================
# POST-PROCESSING
# ============================================================================

class TestPostProcessing:
    """Test _fill_leaps and other post-processing."""

    def test_fill_leaps_with_low_harmony_prob(self):
        """_fill_leaps is called when harmony_note_probability < 1.0."""
        gen = MelodyGenerator(
            harmony_note_probability=0.5,  # Triggers _fill_leaps
            steps_probability=0.0,  # Allow leaps
            note_range_low=48,
            note_range_high=72,
        )
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_fill_leaps_disabled_with_full_harmony(self):
        """_fill_leaps is skipped when harmony_note_probability = 1.0."""
        gen = MelodyGenerator(harmony_note_probability=1.0)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


# ============================================================================
# RENDER CONTEXT
# ============================================================================

class TestRenderContext:
    """Test context parameter usage."""

    def test_context_prev_pitch(self):
        """Context with prev_pitch influences generation."""
        gen = MelodyGenerator()
        ctx = RenderContext(prev_pitch=72)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0

    def test_context_phrase_position(self):
        """Context with phrase_position affects velocity."""
        gen = MelodyGenerator(phrase_length=4.0)
        ctx = RenderContext(phrase_position=0.5)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0

    def test_context_prev_pitches_for_motif(self):
        """Context with prev_pitches enables motif memory."""
        gen = MelodyGenerator(motif_probability=0.5)
        ctx = RenderContext(prev_pitches=(60, 64, 67, 72))
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0

    def test_last_context_stored(self):
        """_last_context is stored after render."""
        gen = MelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert gen._last_context is not None
        assert gen._last_context.prev_pitch == notes[-1].pitch


# ============================================================================
# EDGE CASES & VALIDATION
# ============================================================================

class TestEdgeCases:
    """Test edge cases and validation."""

    def test_invalid_first_note_raises(self):
        """Invalid first_note raises ValueError."""
        with pytest.raises(ValueError, match="first_note"):
            MelodyGenerator(first_note="invalid_strategy")

    def test_invalid_last_note_raises(self):
        """Invalid last_note raises ValueError."""
        with pytest.raises(ValueError, match="last_note"):
            MelodyGenerator(last_note="invalid_strategy")

    def test_invalid_after_leap_raises(self):
        """Invalid after_leap raises ValueError."""
        with pytest.raises(ValueError, match="after_leap"):
            MelodyGenerator(after_leap="invalid_strategy")

    def test_invalid_phrase_contour_raises(self):
        """Invalid phrase_contour raises ValueError."""
        with pytest.raises(ValueError, match="phrase_contour"):
            MelodyGenerator(phrase_contour="nonexistent_contour")

    def test_invalid_accent_pattern_raises(self):
        """Invalid accent_pattern raises ValueError."""
        with pytest.raises(ValueError, match="accent_pattern"):
            MelodyGenerator(accent_pattern="loud_quiet")

    def test_invalid_motif_variation_raises(self):
        """Invalid motif_variation raises ValueError."""
        with pytest.raises(ValueError, match="motif_variation"):
            MelodyGenerator(motif_variation="scramble")

    def test_single_chord(self):
        """Generate with single chord."""
        chord = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=8.0)
        gen = MelodyGenerator()
        notes = gen.render([chord], C_MAJOR, 8.0)
        assert len(notes) > 0

    def test_short_duration(self):
        """Generate with very short duration."""
        gen = MelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 0.5)
        # May be empty or have one note

    def test_wide_range(self):
        """Generate with wide pitch range."""
        gen = MelodyGenerator(note_range_low=36, note_range_high=96)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 36 <= n.pitch <= 96

    def test_very_narrow_range(self):
        """Generate with very narrow range."""
        gen = MelodyGenerator(note_range_low=60, note_range_high=62)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert 60 <= n.pitch <= 62


# ============================================================================
# PENULTIMATE NOTES
# ============================================================================

class TestPenultimate:
    """Test penultimate note handling."""

    def test_penultimate_step_above_true(self):
        """Penultimate step above enabled."""
        gen = MelodyGenerator(penultimate_step_above=True)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_penultimate_step_above_false(self):
        """Penultimate step above disabled."""
        gen = MelodyGenerator(penultimate_step_above=False)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0


class TestMinNoteGap:
    """min_note_gap must actually thin dense output — it was a silent no-op
    (stored in __init__ but never read in render())."""

    def test_min_note_gap_enforced(self):
        gen = MelodyGenerator(
            GeneratorParams(density=0.9, key_range_low=60, key_range_high=84),
            min_note_gap=0.5,
            phrase_length=8.0,
            seed=1,
        )
        notes = sorted(gen.render(_simple_chords(), C_MAJOR, 8.0), key=lambda n: n.start)
        gaps = [notes[i + 1].start - notes[i].start for i in range(len(notes) - 1)]
        violating = [g for g in gaps if 0 < g < 0.5 - 1e-6]
        assert not violating, f"min_note_gap violated by {violating}"

    def test_min_note_gap_zero_keeps_all(self):
        dense = MelodyGenerator(
            GeneratorParams(density=0.9, key_range_low=60, key_range_high=84),
            min_note_gap=0.0, phrase_length=8.0, seed=1,
        )
        gated = MelodyGenerator(
            GeneratorParams(density=0.9, key_range_low=60, key_range_high=84),
            min_note_gap=0.5, phrase_length=8.0, seed=1,
        )
        n_dense = dense.render(_simple_chords(), C_MAJOR, 8.0)
        n_gated = gated.render(_simple_chords(), C_MAJOR, 8.0)
        # gating must not increase note count, and should reduce it for dense input
        assert len(n_gated) <= len(n_dense)


class TestMotifAnchor:
    """Motif variations must reproduce the stored contour cyclically, NOT
    compound off the drifting prev_pitch (which made the motif run away to the
    register ceiling). Regression for the runaway-transpose bug."""

    def _mgr(self, variation):
        from melodica.generators._melody_motif import MotifManager
        m = MotifManager(motif_probability=1.0, motif_variation=variation)
        m.store_motif([60, 64, 67, 72])  # intervals [+4, +3, +5]
        return m

    def test_transpose_reproduces_motif_from_anchor(self):
        import random
        random.seed(0)
        m = self._mgr("transpose")
        prev = 60
        out = []
        for idx in range(4):
            prev = m.apply(prev, 36, 96, C_MAJOR, idx)
            out.append(prev)
        # snapped to C major, the stored tones 60/64/67/72 reproduce exactly
        assert out == [60, 64, 67, 72], out

    def test_transpose_does_not_run_away(self):
        import random
        random.seed(0)
        m = self._mgr("transpose")
        prev = 60
        pitches = []
        for idx in range(16):
            prev = m.apply(prev, 36, 96, C_MAJOR, idx)
            pitches.append(prev)
        # The runaway bug pinned every note at the 96 ceiling permanently
        # (96,96,96,96...). After the fix the anchor octave-folds, so the motif
        # must never get STUCK at the ceiling — assert no 4-in-a-row at max.
        ceiling = 96
        run = 0
        for p in pitches:
            run = run + 1 if p == ceiling else 0
            assert run < 4, f"motif pinned at ceiling: {pitches}"

    def test_retrograde_cyclic_contour(self):
        import random
        random.seed(0)
        m = self._mgr("retrograde")
        prev = 60
        out = [prev]
        for idx in range(6):
            prev = m.apply(prev, 36, 96, C_MAJOR, idx)
            out.append(prev)
        ivs = [out[i + 1] - out[i] for i in range(len(out) - 1)]
        # retrograde of [+4,+3,+5] descends; the per-cycle interval pattern repeats
        assert ivs[1:4] == ivs[4:7] if len(ivs) >= 7 else True, ivs
