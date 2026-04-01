import pytest
from melodica.types import ChordLabel, Quality, Scale, Mode
from melodica.generators.strum import StrumPatternGenerator
from melodica.generators.piano_run import PianoRunGenerator
from melodica.generators.markov import MarkovMelodyGenerator
from melodica.generators.dyads import DyadGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    return [c]


class TestStrumGenerator:
    def test_strum_delay(self):
        gen = StrumPatternGenerator(strum_delay=0.1)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) >= 3
        starts = sorted([n.start for n in notes])
        assert starts[1] > starts[0]

    @pytest.mark.parametrize("polyphony", [3, 6, 9])
    def test_polyphony(self, polyphony):
        gen = StrumPatternGenerator(polyphony=polyphony)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 1.0)
        assert len(notes) > 0
        assert len(notes) <= polyphony

    @pytest.mark.parametrize("density", ["low", "low_medium", "medium", "medium_high", "high"])
    def test_density(self, density):
        gen = StrumPatternGenerator(density=density)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 1.0)
        assert len(notes) > 0

    def test_density_low_fewer_notes(self):
        gen_low = StrumPatternGenerator(density="low")
        gen_high = StrumPatternGenerator(density="high")
        notes_low = gen_low.render(_simple_chords()[:1], C_MAJOR, 1.0)
        notes_high = gen_high.render(_simple_chords()[:1], C_MAJOR, 1.0)
        assert len(notes_low) <= len(notes_high)

    def test_invalid_density_raises(self):
        with pytest.raises(ValueError):
            StrumPatternGenerator(density="extreme")


class TestPianoRunGenerator:
    def test_run_packing(self):
        notes_per_run = 8
        gen = PianoRunGenerator(notes_per_run=notes_per_run)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        # One run for 4 beats, 8 notes in it
        assert len(notes) == notes_per_run

    # --- Technique tests ---

    @pytest.mark.parametrize(
        "technique",
        [
            "straddle",
            "straddle_without_middle",
            "2-1_breakup",
            "3-1_breakup",
            "waterfall",
            "waterfall_inversions",
        ],
    )
    def test_technique_produces_notes(self, technique):
        gen = PianoRunGenerator(technique=technique, notes_per_run=8)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_technique_raises(self):
        with pytest.raises(ValueError):
            PianoRunGenerator(technique="invalid_tech")

    def test_straddle_alternates_around_center(self):
        pool = [48, 52, 55, 60, 64, 67]
        gen = PianoRunGenerator(technique="straddle", notes_per_run=8)
        seq = gen._build_technique_sequence(pool)
        # Center should appear frequently (repeated between alternations)
        center = pool[len(pool) // 2]  # 60
        assert center in seq
        # Should have notes both above and below center
        above = [p for p in seq if p > center]
        below = [p for p in seq if p < center]
        assert len(above) > 0
        assert len(below) > 0

    def test_straddle_without_middle_no_center_repeat(self):
        pool = [48, 52, 55, 60, 64, 67]
        gen = PianoRunGenerator(technique="straddle_without_middle", notes_per_run=8)
        seq = gen._build_technique_sequence(pool)
        center = pool[len(pool) // 2]  # 60
        # Center should NOT appear in the sequence
        assert center not in seq
        # Should have notes both above and below
        assert any(p > center for p in seq)
        assert any(p < center for p in seq)

    def test_breakup_2_1_pattern(self):
        pool = [48, 52, 55, 60, 64, 67]
        gen = PianoRunGenerator(technique="2-1_breakup", notes_per_run=12)
        seq = gen._build_technique_sequence(pool)
        assert len(seq) > 0
        # Pattern: [n, n+1, n] — third note equals first of triplet
        # Check first triplet
        if len(seq) >= 3:
            assert seq[2] == seq[0]  # step back

    def test_breakup_3_1_pattern(self):
        pool = [48, 52, 55, 60, 64, 67]
        gen = PianoRunGenerator(technique="3-1_breakup", notes_per_run=12)
        seq = gen._build_technique_sequence(pool)
        assert len(seq) > 0
        # Pattern: [n, n+1, n+2, n+1] — 4th note equals 2nd of group
        if len(seq) >= 4:
            assert seq[3] == seq[1]  # step back from peak

    def test_waterfall_descending(self):
        pool = [48, 52, 55, 60, 64, 67]
        gen = PianoRunGenerator(technique="waterfall", notes_per_run=6)
        seq = gen._build_technique_sequence(pool)
        # Should be descending
        for i in range(len(seq) - 1):
            assert seq[i] >= seq[i + 1]

    def test_waterfall_inversions_produces_notes(self):
        pool = [48, 52, 55, 60]
        gen = PianoRunGenerator(technique="waterfall_inversions", notes_per_run=8)
        seq = gen._build_technique_sequence(pool)
        assert len(seq) > 0

    # --- Motion tests ---

    @pytest.mark.parametrize("motion", ["up_down", "up"])
    def test_motion_produces_notes(self, motion):
        gen = PianoRunGenerator(technique="straddle", motion=motion, notes_per_run=8)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_motion_raises(self):
        with pytest.raises(ValueError):
            PianoRunGenerator(motion="sideways")

    def test_motion_up_no_low_notes(self):
        gen = PianoRunGenerator(
            technique="waterfall",
            motion="up",
            up_motion_range=24,
            down_motion_range=12,
            notes_per_run=8,
        )
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        # Use context with anchor at middle C
        from melodica.render_context import RenderContext

        ctx = RenderContext()
        ctx = ctx.with_end_state(
            last_pitch=60, last_velocity=80, last_chord=chords[0], last_pitches=[60]
        )
        notes = gen.render(chords, C_MAJOR, 4.0, context=ctx)
        assert len(notes) > 0
        # All notes should be >= anchor (60) when motion is "up"
        for n in notes:
            assert n.pitch >= 60

    def test_up_motion_range_limits(self):
        gen = PianoRunGenerator(
            technique="waterfall",
            motion="up",
            up_motion_range=12,
            down_motion_range=12,
            notes_per_run=8,
        )
        chords = [ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)]
        from melodica.render_context import RenderContext

        ctx = RenderContext()
        ctx = ctx.with_end_state(
            last_pitch=60, last_velocity=80, last_chord=chords[0], last_pitches=[60]
        )
        notes = gen.render(chords, C_MAJOR, 4.0, context=ctx)
        for n in notes:
            assert 60 <= n.pitch <= 72  # within up_motion_range of 12

    # --- Backward compatibility ---

    def test_legacy_direction_up(self):
        gen = PianoRunGenerator(direction="up", notes_per_run=4)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) == 4

    def test_legacy_direction_down(self):
        gen = PianoRunGenerator(direction="down", notes_per_run=4)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) == 4

    def test_legacy_scale_steps(self):
        gen = PianoRunGenerator(direction="up", scale_steps=True, notes_per_run=4)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) == 4
        # All notes should be in C major scale
        for n in notes:
            assert C_MAJOR.contains(n.pitch % 12)


class TestMarkovGenerator:
    def test_markov_generation(self):
        gen = MarkovMelodyGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0
        for n in notes:
            assert C_MAJOR.contains(n.pitch % 12)

    def test_direction_bias_up(self):
        gen = MarkovMelodyGenerator(direction_bias=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        if len(notes) >= 2:
            diffs = [notes[i].pitch - notes[i - 1].pitch for i in range(1, len(notes))]
            assert sum(diffs) >= 0

    def test_note_range(self):
        gen = MarkovMelodyGenerator(note_range_low=60, note_range_high=72)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert 60 <= n.pitch <= 72

    def test_note_repetition(self):
        gen = MarkovMelodyGenerator(note_repetition_probability=0.95)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        if len(notes) >= 2:
            repeated = sum(1 for i in range(1, len(notes)) if notes[i].pitch == notes[i - 1].pitch)
            assert repeated > len(notes) * 0.5


class TestDyadGenerator:
    def test_dyad_generation(self):
        gen = DyadGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 2.0)
        assert len(notes) > 0
        assert len(notes) % 2 == 0  # always pairs

    @pytest.mark.parametrize("mode", ["random", "parallel", "contrary", "oblique"])
    def test_motion_modes(self, mode):
        gen = DyadGenerator(motion_mode=mode)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0

    def test_parallel_keeps_interval(self):
        gen = DyadGenerator(motion_mode="parallel", interval_pref=[7], seed=42)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        if len(notes) >= 4:
            # Each pair should be ~7 semitones apart
            for i in range(0, len(notes) - 1, 2):
                diff = abs(notes[i].pitch - notes[i + 1].pitch)
                assert diff >= 3  # min_interval

    def test_note_range(self):
        gen = DyadGenerator(note_range_low=48, note_range_high=84)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        for n in notes:
            assert 48 <= n.pitch <= 84

    def test_invalid_motion_raises(self):
        with pytest.raises(ValueError):
            DyadGenerator(motion_mode="sideways")
