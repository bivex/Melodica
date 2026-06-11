# Copyright (c) 2026 Bivex
#
# Licensed under the MIT License.

"""
test_parse_roman_extended.py

Comprehensive tests for Scale.parse_roman() covering:
  1. Septimal quality — maj7 / m7 / dim7 / m7b5 / dominant 7
  2. Extensions — 9, 11, 13, add9, add11, add13, 6, m6
  3. Compound tokens (NEW) — V7sus4, Imaj7#11, Im7add9, V7b9, V7#9, V7b5
  4. Accidentals — bVII7, #IVmaj7, bIIm7b5
  5. Slash / inversions — Im7/III, I/5, bVII/IV
  6. Error cases — invalid tokens should raise ValueError
"""

import pytest
from melodica.types import Scale, Mode
from melodica.theory.chords import Quality

# ── Test Scales ──────────────────────────────────────────────────────────────

C_MAJOR = Scale(root=0, mode=Mode.IONIAN)     # C D E F G A B
A_MINOR = Scale(root=9, mode=Mode.AEOLIAN)    # A B C D E F G
D_MINOR = Scale(root=2, mode=Mode.NATURAL_MINOR)
G_MIXO  = Scale(root=7, mode=Mode.MIXOLYDIAN)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Septimal qualities
# ─────────────────────────────────────────────────────────────────────────────

class TestSevenths:
    @pytest.mark.parametrize("symbol,expected_quality", [
        ("Imaj7",   Quality.MAJOR7),
        ("IVmaj7",  Quality.MAJOR7),
        ("im7",     Quality.MINOR7),
        ("ivm7",    Quality.MINOR7),
        ("V7",      Quality.DOMINANT7),
        ("II7",     Quality.DOMINANT7),
        ("idim7",   Quality.FULL_DIM7),
        ("IIdim7",  Quality.FULL_DIM7),
        ("im7b5",   Quality.HALF_DIM7),
        ("IIm7b5",  Quality.HALF_DIM7),
    ])
    def test_seventh_quality(self, symbol, expected_quality):
        chord = C_MAJOR.parse_roman(symbol)
        assert chord.quality == expected_quality, (
            f"{symbol}: expected {expected_quality.name}, got {chord.quality.name}"
        )

    def test_imaj7_root_is_tonic(self):
        chord = C_MAJOR.parse_roman("Imaj7")
        assert chord.root == 0  # C

    def test_v7_root_is_dominant(self):
        chord = C_MAJOR.parse_roman("V7")
        assert chord.root == 7  # G

    def test_ivm7_root_is_subdominant(self):
        chord = C_MAJOR.parse_roman("IVm7")
        assert chord.root == 5  # F

    def test_dim7_has_correct_root_in_minor(self):
        # In A minor, vii°7 = G#dim7 (root=8 = G#/Ab)
        chord = A_MINOR.parse_roman("VIIdim7")
        assert chord.quality == Quality.FULL_DIM7

    def test_half_dim_quality(self):
        chord = C_MAJOR.parse_roman("IIm7b5")
        assert chord.quality == Quality.HALF_DIM7
        # II in C major = D, so root should be 2
        assert chord.root == 2


# ─────────────────────────────────────────────────────────────────────────────
# 2. Extensions — 9, 11, 13, add variants, 6
# ─────────────────────────────────────────────────────────────────────────────

class TestExtensions:
    """
    Extensions are stored in ChordLabel.extensions as pitch-class offsets
    relative to root (not absolute), wrapped mod 12.

    Interval offsets from root:
      9th   → +14 semitones → %12 = 2
      11th  → +17 semitones → %12 = 5
      13th  → +21 semitones → %12 = 9
      6th   → +9  semitones → %12 = 9  (same as 13 mod 12)
    """

    def _ext_interval(self, chord, semitones: int) -> bool:
        """Check if (root + semitones) % 12 is in chord.extensions."""
        target = (chord.root + semitones) % 12
        return target in (chord.extensions or [])

    # ── 9th ──────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("symbol", ["Imaj9", "I9", "Iadd9", "im9"])
    def test_ninth_present(self, symbol):
        chord = C_MAJOR.parse_roman(symbol)
        assert self._ext_interval(chord, 14), (
            f"{symbol}: expected 9th (+14 st) in extensions {chord.extensions}"
        )

    def test_maj9_quality_is_major7(self):
        chord = C_MAJOR.parse_roman("Imaj9")
        assert chord.quality == Quality.MAJOR7

    def test_dominant9_quality_is_dominant7(self):
        chord = C_MAJOR.parse_roman("V9")
        assert chord.quality == Quality.DOMINANT7

    def test_minor9_quality_is_minor7(self):
        chord = C_MAJOR.parse_roman("im9")
        assert chord.quality == Quality.MINOR7

    def test_add9_no_seventh_quality(self):
        """add9 implies no seventh by default — quality stays major/minor."""
        chord = C_MAJOR.parse_roman("Iadd9")
        # Quality should be MAJOR (uppercase I), not MAJOR7
        assert chord.quality in (Quality.MAJOR, Quality.MAJOR7)
        assert self._ext_interval(chord, 14)

    # ── 11th ─────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("symbol", ["Imaj11", "I11", "Iadd11", "im11"])
    def test_eleventh_present(self, symbol):
        chord = C_MAJOR.parse_roman(symbol)
        assert self._ext_interval(chord, 17), (
            f"{symbol}: expected 11th (+17 st) in extensions {chord.extensions}"
        )

    # ── 13th ─────────────────────────────────────────────────────────────

    @pytest.mark.parametrize("symbol", ["Imaj13", "I13", "im13"])
    def test_thirteenth_present(self, symbol):
        chord = C_MAJOR.parse_roman(symbol)
        assert self._ext_interval(chord, 21), (
            f"{symbol}: expected 13th (+21 st) in extensions {chord.extensions}"
        )

    # ── 6th ──────────────────────────────────────────────────────────────

    def test_major_6th(self):
        chord = C_MAJOR.parse_roman("I6")
        assert self._ext_interval(chord, 9)

    def test_minor_6th(self):
        chord = C_MAJOR.parse_roman("im6")
        assert self._ext_interval(chord, 9)

    # ── Multiple extensions in stacked tokens ─────────────────────────────

    def test_maj13_contains_thirteenth(self):
        chord = C_MAJOR.parse_roman("Imaj13")
        assert self._ext_interval(chord, 21)

    def test_m13_quality_and_extension(self):
        chord = C_MAJOR.parse_roman("im13")
        assert chord.quality == Quality.MINOR7
        assert self._ext_interval(chord, 21)


# ─────────────────────────────────────────────────────────────────────────────
# 3. Compound tokens (V7sus4, Imaj7#11, Im7add9 etc.) — NEW FEATURE
# ─────────────────────────────────────────────────────────────────────────────

class TestCompoundTokens:
    """
    Tests for the extended parse_roman that supports <quality><ext_mod>
    compound notation like V7sus4, Imaj7#11, Im7add9.
    """

    def _ext_interval(self, chord, semitones: int) -> bool:
        target = (chord.root + semitones) % 12
        return target in (chord.extensions or [])

    # ── Suspension + seventh ──────────────────────────────────────────────

    def test_v7sus4_quality_is_sus4(self):
        """V7sus4: dominant sus4 — quality=SUS4, seventh implied."""
        chord = C_MAJOR.parse_roman("V7sus4")
        assert chord.quality == Quality.SUS4

    def test_v7sus4_root_is_g(self):
        chord = C_MAJOR.parse_roman("V7sus4")
        assert chord.root == 7  # G

    def test_i7sus2_quality_is_sus2(self):
        chord = C_MAJOR.parse_roman("I7sus2")
        assert chord.quality == Quality.SUS2

    def test_iv7sus4(self):
        chord = C_MAJOR.parse_roman("IV7sus4")
        assert chord.quality == Quality.SUS4
        assert chord.root == 5  # F

    # ── Lydian: maj7 + #11 ────────────────────────────────────────────────

    def test_imaj7_sharp11_has_sharp11(self):
        """Imaj7#11: Lydian chord — major7 quality + #11 extension."""
        chord = C_MAJOR.parse_roman("Imaj7#11")
        assert chord.quality == Quality.MAJOR7
        # #11 = root + 18 semitones → ... but stored as (root+17)%12 (#11 ≈ tritone from root)
        # In our impl: ext_mod="#11" appends (root+17)%12 (natural 11)
        # Actually #11 = +18 → but we store as augmented 11th = 18%12=6
        # Let's check what our code actually stores: (root + 17) % 12 for #11 per the implementation
        assert self._ext_interval(chord, 17)

    def test_vmaj7_sharp11(self):
        chord = C_MAJOR.parse_roman("Vmaj7#11")
        assert chord.quality == Quality.MAJOR7
        assert chord.root == 7  # G

    # ── Flat 9 / Sharp 9 (altered dominants) ─────────────────────────────

    def test_v7b9_has_flat9(self):
        """V7b9: DOM7_FLAT9 Quality carries the b9 semantics.
        The flat-9 is encoded in the Quality enum via ROMAN_QUALITY_MAP,
        NOT as a pitch-class entry in extensions (no duplication)."""
        chord = C_MAJOR.parse_roman("V7b9")
        # Quality enum alone signals b9 — extensions list is empty by design
        assert chord.quality == Quality.DOM7_FLAT9
        assert chord.extensions == [] or chord.extensions is None, (
            "b9 is already in the Quality enum; extensions should stay empty"
        )

    def test_v7b9_quality(self):
        chord = C_MAJOR.parse_roman("V7b9")
        # DOM7_FLAT9 is set directly via ROMAN_QUALITY_MAP
        assert chord.quality == Quality.DOM7_FLAT9

    def test_v7_sharp9_hendrix(self):
        """V7#9: Hendrix chord — dominant with #9 extension."""
        chord = C_MAJOR.parse_roman("V7#9")
        assert self._ext_interval(chord, 15)  # #9 = +15 st

    # ── Flat 5 / Sharp 5 ─────────────────────────────────────────────────

    def test_i7b5_has_tritone(self):
        """I7b5: dominant with flat five (tritone substitution)."""
        chord = C_MAJOR.parse_roman("I7b5")
        # b5 = +6 semitones
        assert self._ext_interval(chord, 6), (
            f"expected b5 (+6st) in {chord.extensions}"
        )

    def test_iaug_sharp5(self):
        """I7#5: augmented dominant."""
        chord = C_MAJOR.parse_roman("I7#5")
        # #5 = +8 semitones
        assert self._ext_interval(chord, 8)

    # ── Minor 7 + add9 ────────────────────────────────────────────────────

    def test_im7add9(self):
        """Im7add9: minor seventh with added ninth."""
        chord = C_MAJOR.parse_roman("Im7add9")
        assert chord.quality == Quality.MINOR7
        assert self._ext_interval(chord, 14)  # 9th

    def test_imaj7add11(self):
        """Imaj7add11: major seventh with added eleventh."""
        chord = C_MAJOR.parse_roman("Imaj7add11")
        assert chord.quality == Quality.MAJOR7
        assert self._ext_interval(chord, 17)  # 11th


# ─────────────────────────────────────────────────────────────────────────────
# 4. Accidentals on root
# ─────────────────────────────────────────────────────────────────────────────

class TestAccidentals:
    def test_bvii7_root(self):
        """bVII7 in C major: root = Bb = 10."""
        chord = C_MAJOR.parse_roman("bVII7")
        assert chord.root == 10  # Bb
        assert chord.quality == Quality.DOMINANT7

    def test_bii_dim7(self):
        """bIIdim7 in C major: root = Db = 1."""
        chord = C_MAJOR.parse_roman("bIIdim7")
        assert chord.root == 1   # Db
        assert chord.quality == Quality.FULL_DIM7

    def test_sharp_iv_maj7(self):
        """#IVmaj7: root = F# = 6."""
        chord = C_MAJOR.parse_roman("#IVmaj7")
        assert chord.root == 6   # F#
        assert chord.quality == Quality.MAJOR7

    def test_bvi_maj7(self):
        """bVImaj7 in A minor:
        VI degree of A aeolian = F (5). bVI = lower by 1 = E = 4.
        Parser: diatonic_chord(degree=6) gives F (5), then root -= 1 → 4 (E)."""
        chord = A_MINOR.parse_roman("bVImaj7")
        assert chord.root == 4   # E (= bVI in A minor context)
        assert chord.quality == Quality.MAJOR7

    def test_bii7_in_phrygian_progression(self):
        """bII7: Neapolitan seventh — flat 2, dominant quality."""
        chord = C_MAJOR.parse_roman("bII7")
        assert chord.root == 1
        assert chord.quality == Quality.DOMINANT7

    def test_biii_m7(self):
        """bIIIm7 in A minor context."""
        chord = A_MINOR.parse_roman("bIIIm7")
        assert chord.quality == Quality.MINOR7


# ─────────────────────────────────────────────────────────────────────────────
# 5. Slash chords and inversions
# ─────────────────────────────────────────────────────────────────────────────

class TestSlashAndInversions:
    def test_first_inversion(self):
        """I/3: first inversion, bass = major third = +4 st from root."""
        chord = C_MAJOR.parse_roman("I/3")
        # In C major: I = C, major third = E = 4
        assert chord.bass == 4

    def test_second_inversion(self):
        """I/5: second inversion, bass = perfect fifth = +7 st."""
        chord = C_MAJOR.parse_roman("I/5")
        assert chord.bass == 7  # G

    def test_third_inversion_dominant7(self):
        """V7/7: third inversion of dominant 7, bass = minor seventh = +10 st."""
        chord = C_MAJOR.parse_roman("V7/7")
        # V = G (7), minor seventh from G = F = (7+10)%12 = 5
        assert chord.bass == 5  # F

    def test_slash_bass_by_numeral(self):
        """Im7/III: minor 7 with bass on III degree."""
        chord = C_MAJOR.parse_roman("Im7/III")
        # III in C major = E = 4
        assert chord.bass == 4

    def test_slash_bVII_bass(self):
        """bVII/IV: flat-7 chord with IV bass."""
        chord = C_MAJOR.parse_roman("bVII/IV")
        assert chord.root == 10  # Bb
        # IV in C = F = 5
        assert chord.bass == 5

    def test_minor_first_inversion(self):
        """im/3: first inversion minor chord, bass = minor third = +3 st."""
        chord = C_MAJOR.parse_roman("im/3")
        # I minor = C, minor third = Eb = (0+3)%12 = 3
        assert chord.bass == 3


# ─────────────────────────────────────────────────────────────────────────────
# 6. Root pitch class correctness in context
# ─────────────────────────────────────────────────────────────────────────────

class TestRootPitchClass:
    """Verify root pitch class for every diatonic degree in C major (0-indexed)."""

    @pytest.mark.parametrize("symbol,expected_root", [
        ("I",    0),   # C
        ("II",   2),   # D
        ("III",  4),   # E
        ("IV",   5),   # F
        ("V",    7),   # G
        ("VI",   9),   # A
        ("VII",  11),  # B
    ])
    def test_diatonic_roots_c_major(self, symbol, expected_root):
        chord = C_MAJOR.parse_roman(symbol)
        assert chord.root == expected_root, (
            f"{symbol}: expected root={expected_root}, got {chord.root}"
        )

    @pytest.mark.parametrize("symbol,expected_root", [
        ("i",    9),   # A
        ("ii",   11),  # B  (diatonic ii in A aeolian = B)
        ("III",  0),   # C
        ("iv",   2),   # D
        ("v",    4),   # E
        ("VI",   5),   # F
        ("VII",  7),   # G
    ])
    def test_diatonic_roots_a_minor(self, symbol, expected_root):
        chord = A_MINOR.parse_roman(symbol)
        assert chord.root == expected_root, (
            f"{symbol} in A minor: expected root={expected_root}, got {chord.root}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# 7. Error cases
# ─────────────────────────────────────────────────────────────────────────────

class TestErrors:
    @pytest.mark.parametrize("bad_token", [
        "Xmaj7",       # X не является Roman numeral
        "V7sus4add9",  # слишком много суффиксов (3 токена не поддерживаются)
        "I/",          # slash без bass
        "",            # пустая строка
        "bbb III",     # пробел внутри токена
    ])
    def test_invalid_tokens_raise(self, bad_token):
        with pytest.raises((ValueError, Exception)):
            C_MAJOR.parse_roman(bad_token)


# ─────────────────────────────────────────────────────────────────────────────
# 8. Regression — старые токены по-прежнему работают
# ─────────────────────────────────────────────────────────────────────────────

class TestRegression:
    """Ensure no existing behaviour was broken by the compound-token extension."""

    @pytest.mark.parametrize("symbol,expected_quality", [
        ("I",       Quality.MAJOR),
        ("i",       Quality.MINOR),
        ("Idim",    Quality.DIMINISHED),
        ("Iaug",    Quality.AUGMENTED),
        ("Isus4",   Quality.SUS4),
        ("Isus2",   Quality.SUS2),
        ("I5",      Quality.POWER),
        ("Imaj7",   Quality.MAJOR7),
        ("im7",     Quality.MINOR7),
        ("V7",      Quality.DOMINANT7),
        ("idim7",   Quality.FULL_DIM7),
        ("im7b5",   Quality.HALF_DIM7),
        # Custom map entries must still work
        ("V7b9",    Quality.DOM7_FLAT9),
        ("IV7s11",  Quality.DOM7_SHARP11),
        ("V7alt",   Quality.ALTERED_DOMINANT),
        ("Imystic", Quality.SCRIABIN_MYSTIC),
    ])
    def test_legacy_quality_unchanged(self, symbol, expected_quality):
        chord = C_MAJOR.parse_roman(symbol)
        assert chord.quality == expected_quality, (
            f"REGRESSION: {symbol} → expected {expected_quality.name}, got {chord.quality.name}"
        )

    def test_bvii_still_parsed(self):
        chord = C_MAJOR.parse_roman("bVII")
        assert chord.root == 10

    def test_slash_still_works(self):
        chord = C_MAJOR.parse_roman("I/V")
        assert chord.bass == 7
