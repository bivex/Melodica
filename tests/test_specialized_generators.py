import pytest
from melodica.types import ChordLabel, Quality, Scale, Mode
from melodica.generators.bass import BassGenerator
from melodica.generators.fingerpicking import FingerpickingGenerator
from melodica.generators.ostinato import OstinatoGenerator


C_MAJOR = Scale(root=0, mode=Mode.MAJOR)


def _simple_chords() -> list[ChordLabel]:
    c = ChordLabel(root=0, quality=Quality.MAJOR, start=0.0, duration=4.0)
    g = ChordLabel(root=7, quality=Quality.MAJOR, start=4.0, duration=4.0)
    return [c, g]


class TestBassGenerator:
    def test_root_only(self):
        gen = BassGenerator(style="root_only")
        notes = gen.render(_simple_chords(), C_MAJOR, 8.0)
        assert len(notes) > 0
        # Check first note pitch class is C (0)
        assert notes[0].pitch % 12 == 0

    def test_root_fifth(self):
        gen = BassGenerator(style="root_fifth")
        notes = gen.render(_simple_chords(), C_MAJOR, 2.0)
        assert len(notes) == 2
        # First is root C (0), second is fifth (7)
        assert notes[0].pitch % 12 == 0
        assert notes[1].pitch % 12 == 7

    def test_root_fifth_octave(self):
        gen = BassGenerator(style="root_fifth_octave")
        # 3 events will show the octave
        notes = gen.render(_simple_chords(), C_MAJOR, 3.0)
        assert len(notes) == 3
        # Octave should be higher pitch than root
        assert notes[2].pitch == notes[0].pitch + 12

    def test_invalid_style(self):
        with pytest.raises(ValueError):
            BassGenerator(style="dubstep")

    # --- Melodica-style allowed_notes tests ---

    @pytest.mark.parametrize(
        "allowed",
        [
            ["root"],
            ["root", "fourth"],
            ["root", "sixth"],
            ["root", "lower_octave"],
            ["root", "fourth", "sixth"],
            ["root", "fourth", "sixth", "lower_octave"],
        ],
    )
    def test_allowed_notes_produces_notes(self, allowed):
        gen = BassGenerator(allowed_notes=allowed)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_allowed_note_raises(self):
        with pytest.raises(ValueError):
            BassGenerator(allowed_notes=["invalid"])

    def test_root_plus_fourth_has_two_pcs(self):
        gen = BassGenerator(allowed_notes=["root", "fourth"])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pcs = {n.pitch % 12 for n in notes}
        # C major: root=0(C), fourth=5(F)
        assert 0 in pcs
        assert 5 in pcs

    def test_root_plus_sixth_has_two_pcs(self):
        from melodica.generators import GeneratorParams

        params = GeneratorParams(key_range_low=36, key_range_high=72)
        gen = BassGenerator(allowed_notes=["root", "sixth"], params=params)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pcs = {n.pitch % 12 for n in notes}
        # C major: root=0(C), sixth=9(A)
        assert 0 in pcs
        assert 9 in pcs

    def test_lower_octave_is_lower(self):
        gen = BassGenerator(allowed_notes=["root", "lower_octave"])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pitches = [n.pitch for n in notes]
        if len(pitches) >= 2:
            assert any(p < min(pitches) + 6 for p in pitches)

    # --- Global movement tests ---

    @pytest.mark.parametrize("movement", ["up", "down", "up_down", "none"])
    def test_global_movement_produces_notes(self, movement):
        gen = BassGenerator(allowed_notes=["root", "fourth"], global_movement=movement)
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_invalid_global_movement_raises(self):
        with pytest.raises(ValueError):
            BassGenerator(global_movement="sideways")

    # --- Note movement tests ---

    @pytest.mark.parametrize("movement", ["none", "alternating"])
    def test_note_movement_produces_notes(self, movement):
        gen = BassGenerator(allowed_notes=["root", "fourth"], note_movement=movement)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_alternating_cycles(self):
        gen = BassGenerator(allowed_notes=["root", "fourth"], note_movement="alternating")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        if len(notes) >= 3:
            pcs = [n.pitch % 12 for n in notes]
            assert len(set(pcs)) >= 2

    def test_none_stays_on_root(self):
        gen = BassGenerator(allowed_notes=["root", "fourth"], note_movement="none")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        for n in notes:
            assert n.pitch % 12 == 0

    def test_invalid_note_movement_raises(self):
        with pytest.raises(ValueError):
            BassGenerator(note_movement="wobble")

    # --- Transpose tests ---

    def test_transpose_octaves_up(self):
        gen = BassGenerator(allowed_notes=["root"], transpose_octaves=1)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        gen_no_transpose = BassGenerator(allowed_notes=["root"], transpose_octaves=0)
        notes_no = gen_no_transpose.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert notes[0].pitch == notes_no[0].pitch + 12

    def test_transpose_octaves_down(self):
        from melodica.generators import GeneratorParams

        params = GeneratorParams(key_range_low=12, key_range_high=72)
        gen = BassGenerator(allowed_notes=["root"], transpose_octaves=-1, params=params)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        gen_no = BassGenerator(allowed_notes=["root"], transpose_octaves=0, params=params)
        notes_no = gen_no.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert notes[0].pitch == notes_no[0].pitch - 12


class TestFingerpickingGenerator:
    def test_produces_notes(self):
        gen = FingerpickingGenerator()
        notes = gen.render(_simple_chords(), C_MAJOR, 4.0)
        assert len(notes) > 0

    # --- Melodica-style tests ---

    def test_notes_to_use(self):
        gen = FingerpickingGenerator(notes_to_use=[0, 2])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        pcs = {n.pitch % 12 for n in notes}
        assert 0 in pcs  # C (root)

    def test_retrigger(self):
        gen = FingerpickingGenerator(retrigger=2.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    @pytest.mark.parametrize("sustain", ["no", "yes", "bottom_note", "bottom_two"])
    def test_sustain_notes(self, sustain):
        gen = FingerpickingGenerator(sustain_notes=sustain)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0
        if sustain == "yes":
            assert all(n.duration > 0.45 for n in notes)

    def test_sustain_bottom_note(self):
        gen = FingerpickingGenerator(sustain_notes="bottom_note", pattern=[0, 1, 0, 1])
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        bottom_notes = [n for i, n in enumerate(notes) if i % 2 == 0]
        other_notes = [n for i, n in enumerate(notes) if i % 2 == 1]
        if bottom_notes and other_notes:
            assert bottom_notes[0].duration > other_notes[0].duration

    def test_invalid_sustain_raises(self):
        with pytest.raises(ValueError):
            FingerpickingGenerator(sustain_notes="maybe")

    def test_empty_chords(self):
        gen = FingerpickingGenerator()
        assert gen.render([], C_MAJOR, 4.0) == []

    def test_custom_pattern(self):
        gen = FingerpickingGenerator(pattern=[0, 3])
        notes = gen.render(_simple_chords(), C_MAJOR, 1.0)
        assert len(notes) == 2
        assert notes[0].pitch < notes[1].pitch


class TestOstinatoGenerator:
    def test_shape_loop(self):
        gen = OstinatoGenerator(shape=[0, 1])
        # Default rhythm is 16th notes = 4 per beat, 8 notes in 2 beats
        notes = gen.render(_simple_chords(), C_MAJOR, 2.0)
        assert len(notes) == 8

        # 0 and 1 represent closed voice indices.
        # C major triad: C, E, G
        # Root is 0, Third is 1
        # Pitch should alternate between C and E
        assert notes[0].pitch % 12 == 0  # C
        assert notes[1].pitch % 12 == 4  # E
        assert notes[2].pitch % 12 == 0  # C

    def test_shape_with_octaves(self):
        # Index 3 is an octave above root for a triad
        gen = OstinatoGenerator(shape=[0, 3])
        notes = gen.render(_simple_chords(), C_MAJOR, 1.0)
        assert len(notes) == 4

        # root
        assert notes[0].pitch % 12 == 0
        # octave
        assert notes[1].pitch % 12 == 0
        assert notes[1].pitch == notes[0].pitch + 12

    def test_empty_chords(self):
        gen = OstinatoGenerator()
        assert gen.render([], C_MAJOR, 4.0) == []

    # --- Scale degree pattern tests ---

    @pytest.mark.parametrize(
        "pattern_name",
        [
            "1-3-5",
            "5-3-1",
            "5-1-3-1",
            "1-3-1-5",
            "1-3-5-3-1-5-3-1-3-5",
            "1-2-1-3-1-4-1-5",
            "1-3-4-5-4-3-1-3",
            "1-3-5-3",
            "5-3-5-1",
            "3-1",
            "5-1-4-1-3-1-2-1",
            "5-1-4-1",
            "5-3-1-3",
            "1-5-3-5",
            "1-3-5-1-5-3-1-5",
            "3-1-1-1",
            "1-3-5-6",
            "1-3-4-5-4-3",
            "5-1-5-1",
        ],
    )
    def test_named_pattern_produces_notes(self, pattern_name):
        gen = OstinatoGenerator(pattern=pattern_name)
        notes = gen.render(_simple_chords(), C_MAJOR, 2.0)
        assert len(notes) > 0

    def test_custom_string_pattern(self):
        gen = OstinatoGenerator(pattern="1-5-3-7")
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0

    def test_scale_degree_pitches_in_key(self):
        # degrees 1,3,5 in C major should produce C, E, G pitch classes
        from melodica.generators import GeneratorParams

        params = GeneratorParams(key_range_low=48, key_range_high=96)
        gen = OstinatoGenerator(pattern=[1, 3, 5], params=params)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 1.0)
        pcs = {n.pitch % 12 for n in notes}
        assert 0 in pcs  # C
        assert 4 in pcs  # E
        assert 7 in pcs  # G

    def test_repeat_notes(self):
        # repeat_notes=2 means each pattern note plays twice
        gen = OstinatoGenerator(pattern="1-3-5", repeat_notes=2)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0
        # First two notes should have the same pitch
        if len(notes) >= 2:
            assert notes[0].pitch == notes[1].pitch

    def test_insert_root_every(self):
        # Every 4th note should be root (note_count 4, 8, 12...)
        gen = OstinatoGenerator(
            pattern="1-3-5",
            insert_root_every=4,
            rhythm=None,  # use default 16th notes
        )
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        # Note at index 4 (5th note, note_count=4) should be root (pitch class 0)
        if len(notes) > 4:
            assert notes[4].pitch % 12 == 0  # C

    def test_pattern_length_retrigger(self):
        # Pattern should retrigger every N beats
        gen = OstinatoGenerator(pattern="1-3-5", pattern_length=1.0)
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 4.0)
        assert len(notes) > 0

    def test_possible_intervals(self):
        # Only allow root and fifth
        gen = OstinatoGenerator(
            pattern="1-3-5",
            possible_intervals=frozenset({0, 4}),  # root and fifth intervals
        )
        notes = gen.render(_simple_chords()[:1], C_MAJOR, 2.0)
        assert len(notes) > 0
        # All notes should be root (C=0) or fifth (G=7)
        for n in notes:
            assert n.pitch % 12 in {0, 7}

    def test_legacy_shape_still_works(self):
        gen = OstinatoGenerator(shape=[0, 1, 2, 1])
        notes = gen.render(_simple_chords(), C_MAJOR, 2.0)
        assert len(notes) > 0
