"""
tests/test_theory.py — Tests for untested public APIs in types_pkg/_theory.py.

Covers:
  - parse_progression()
  - Scale.parse_roman()
  - Scale.get_parallel_scale()
  - Scale.borrowed_chord()
"""

import pytest
from melodica.types import Scale, Mode, Quality, ChordLabel
from melodica.types_pkg._theory import parse_progression

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
A_MINOR = Scale(root=9, mode=Mode.NATURAL_MINOR)


# ===================================================================
# §1 — Scale.get_parallel_scale
# ===================================================================


class TestGetParallelScale:
    def test_c_major_to_minor(self):
        parallel = C_MAJOR.get_parallel_scale(Mode.NATURAL_MINOR)
        assert parallel.root == 0
        assert parallel.mode == Mode.NATURAL_MINOR

    def test_preserves_root(self):
        for mode in [Mode.DORIAN, Mode.PHRYGIAN, Mode.LYDIAN, Mode.MIXOLYDIAN]:
            p = C_MAJOR.get_parallel_scale(mode)
            assert p.root == 0

    def test_a_minor_to_major(self):
        parallel = A_MINOR.get_parallel_scale(Mode.MAJOR)
        assert parallel.root == 9
        assert parallel.mode == Mode.MAJOR

    def test_different_root(self):
        d_major = Scale(root=2, mode=Mode.MAJOR)
        parallel = d_major.get_parallel_scale(Mode.NATURAL_MINOR)
        assert parallel.root == 2
        assert parallel.mode == Mode.NATURAL_MINOR


# ===================================================================
# §2 — Scale.parse_roman
# ===================================================================


class TestParseRoman:
    def test_major_I(self):
        chord = C_MAJOR.parse_roman("I")
        assert chord.root == 0
        assert chord.quality == Quality.MAJOR

    def test_minor_ii(self):
        chord = C_MAJOR.parse_roman("ii")
        assert chord.root == 2
        assert chord.quality == Quality.MINOR

    def test_minor_v(self):
        chord = C_MAJOR.parse_roman("v")
        assert chord.root == 7
        assert chord.quality == Quality.MINOR

    def test_V7(self):
        chord = C_MAJOR.parse_roman("V7")
        assert chord.root == 7
        assert chord.quality == Quality.DOMINANT7

    def test_Im7(self):
        chord = C_MAJOR.parse_roman("Im7")
        assert chord.root == 0
        assert chord.quality == Quality.MINOR7

    def test_Vmaj7(self):
        chord = C_MAJOR.parse_roman("Vmaj7")
        assert chord.root == 7
        assert chord.quality == Quality.MAJOR7

    def test_invalid_returns_tonic(self):
        """Unparseable string raises ValueError."""
        with pytest.raises(ValueError):
            C_MAJOR.parse_roman("ZZZZ")

    def test_all_degrees(self):
        expected_roots = [0, 2, 4, 5, 7, 9, 11]
        for i, numeral in enumerate(["I", "II", "III", "IV", "V", "VI", "VII"]):
            chord = C_MAJOR.parse_roman(numeral)
            assert chord.root == expected_roots[i]

    def test_minor_scale_degrees(self):
        chord = A_MINOR.parse_roman("i")
        assert chord.root == 9
        assert chord.quality == Quality.MINOR

    def test_bVII(self):
        """Flat VII should parse with flat root (Bb = 10)."""
        chord = C_MAJOR.parse_roman("bVII")
        assert chord.root == 10  # bVII of C major = Bb (10)


# ===================================================================
# §3 — Scale.borrowed_chord
# ===================================================================


class TestBorrowedChord:
    def test_borrow_from_minor(self):
        """Borrow iv from parallel minor."""
        chord = C_MAJOR.borrowed_chord(4, Mode.NATURAL_MINOR)
        # iv in C minor = F minor
        assert chord.root == 5
        assert chord.quality == Quality.MINOR

    def test_borrow_bVII(self):
        """VII of C natural minor = Bb (pitch class 10)."""
        chord = C_MAJOR.borrowed_chord(7, Mode.NATURAL_MINOR)
        assert chord.root == 10  # VII in natural minor = Bb

    def test_borrow_with_seventh(self):
        chord = C_MAJOR.borrowed_chord(5, Mode.NATURAL_MINOR, seventh=True)
        # v in C natural minor = G minor (with 7th)
        assert chord.root == 7

    def test_borrow_preserves_root(self):
        d_major = Scale(root=2, mode=Mode.MAJOR)
        chord = d_major.borrowed_chord(1, Mode.NATURAL_MINOR)
        assert chord.root == 2  # same pitch class


# ===================================================================
# §4 — parse_progression
# ===================================================================


class TestParseProgression:
    def test_basic_progression(self):
        chords = parse_progression("I IV V I", C_MAJOR)
        assert len(chords) == 4
        assert chords[0].root == 0
        assert chords[1].root == 5
        assert chords[2].root == 7
        assert chords[3].root == 0

    def test_timings(self):
        chords = parse_progression("I V", C_MAJOR)
        assert chords[0].start == 0.0
        assert chords[0].duration == 4.0
        assert chords[1].start == 4.0
        assert chords[1].duration == 4.0

    def test_dash_delimiter(self):
        chords = parse_progression("I - V - vi - IV", C_MAJOR)
        assert len(chords) == 4

    def test_minor_progression(self):
        chords = parse_progression("i iv v i", A_MINOR)
        assert chords[0].quality == Quality.MINOR
        assert chords[1].quality == Quality.MINOR

    def test_empty_string(self):
        chords = parse_progression("", C_MAJOR)
        assert chords == []

    def test_seventh_chords(self):
        chords = parse_progression("Im7 IV7 Vmaj7", C_MAJOR)
        assert len(chords) == 3

    def test_single_chord(self):
        chords = parse_progression("I", C_MAJOR)
        assert len(chords) == 1
        assert chords[0].start == 0.0


# ===================================================================
# §5 — Parse Roman Expert Extensions & Inversions
# ===================================================================


class TestParseRomanExpertExtensions:
    def test_mystic_chord(self):
        chord = C_MAJOR.parse_roman("Imystic")
        assert chord.root == 0
        assert chord.quality == Quality.SCRIABIN_MYSTIC

    def test_jazz_alterations(self):
        chord_sharp11 = C_MAJOR.parse_roman("V7s11")
        assert chord_sharp11.root == 7
        assert chord_sharp11.quality == Quality.DOM7_SHARP11

        chord_flat9 = C_MAJOR.parse_roman("I7b9")
        assert chord_flat9.root == 0
        assert chord_flat9.quality == Quality.DOM7_FLAT9

        chord_sharp9 = C_MAJOR.parse_roman("V7s9")
        assert chord_sharp9.root == 7
        assert chord_sharp9.quality == Quality.DOM7_SHARP9

    def test_modal_colors(self):
        chord_phryg = C_MAJOR.parse_roman("Iphryg")
        assert chord_phryg.root == 0
        assert chord_phryg.quality == Quality.PHRYGIAN_MAJOR

        chord_lydaug = C_MAJOR.parse_roman("Ilyda")
        assert chord_lydaug.root == 0
        assert chord_lydaug.quality == Quality.LYDIAN_AUG

    def test_inversions(self):
        # I/3 (first inversion) -> bass = 3rd (E = 4)
        chord_first = C_MAJOR.parse_roman("I/3")
        assert chord_first.root == 0
        assert chord_first.bass == 4

        # ii/3 (first inversion of minor) -> bass = minor 3rd of D (F = 5)
        chord_first_min = C_MAJOR.parse_roman("ii/3")
        assert chord_first_min.root == 2
        assert chord_first_min.bass == 5

        # I/5 (second inversion) -> bass = 5th (G = 7)
        chord_second = C_MAJOR.parse_roman("I/5")
        assert chord_second.root == 0
        assert chord_second.bass == 7

        # V7/7 (third inversion) -> bass = 7th of G7 (F = 5)
        chord_third = C_MAJOR.parse_roman("V7/7")
        assert chord_third.root == 7
        assert chord_third.bass == 5


class TestPickModes:
    def test_pick_by_genre_trap(self):
        from melodica.theory import pick_modes
        trap_modes = pick_modes(genre="trap")
        assert Mode.PHRYGIAN_DOMINANT in trap_modes
        assert Mode.DOUBLE_HARMONIC in trap_modes

    def test_pick_by_genre_lofi(self):
        from melodica.theory import pick_modes
        lofi_modes = pick_modes(genre="lofi")
        assert Mode.DORIAN_PENTATONIC in lofi_modes
        assert Mode.MINOR_HEXATONIC in lofi_modes
        assert Mode.SUSPENDED_PENTA in lofi_modes

    def test_pick_by_bpm(self):
        from melodica.theory import pick_modes
        # 130 BPM should matches trap and epic, but not chill lofi modes
        fast_modes = pick_modes(bpm=130, max_results=100)
        assert Mode.PHRYGIAN_DOMINANT in fast_modes
        assert Mode.DORIAN_PENTATONIC not in fast_modes

    def test_pick_by_energy(self):
        from melodica.theory import pick_modes
        # Highly energetic modes
        hi_energy = pick_modes(energy=0.95, max_results=3)
        assert Mode.SUPER_LOCRIAN in hi_energy


class TestModeAliases:
    def test_ionian_aeolian_aliases(self):
        ionian_scale = Scale(root=0, mode=Mode.IONIAN)
        major_scale = Scale(root=0, mode=Mode.MAJOR)
        assert ionian_scale.degrees() == major_scale.degrees()

        aeolian_scale = Scale(root=9, mode=Mode.AEOLIAN)
        minor_scale = Scale(root=9, mode=Mode.NATURAL_MINOR)
        assert aeolian_scale.degrees() == minor_scale.degrees()


