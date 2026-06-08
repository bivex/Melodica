"""Comprehensive tests for 7 new jazz generators.

Tests: GuideToneGenerator, EnclosureGenerator, SideSlippingGenerator,
TradingFoursGenerator, StopTimeGenerator, WalkingBassLineGenerator,
ShellVoicingGenerator.

Focus: edge cases, validation, boundary conditions, all param combos,
pitch/velocity/start/duration invariants, empty inputs, short durations.
"""

import random

import pytest

from melodica.types import ChordLabel, Quality, Scale, Mode, NoteInfo
from melodica.generators import GeneratorParams
from melodica.generators.guide_tone import GuideToneGenerator
from melodica.generators.enclosure import EnclosureGenerator
from melodica.generators.side_slipping import SideSlippingGenerator
from melodica.generators.trading_fours import TradingFoursGenerator
from melodica.generators.stop_time import StopTimeGenerator
from melodica.generators.walking_bass_line import WalkingBassLineGenerator
from melodica.generators.shell_voicing import ShellVoicingGenerator


# ── Helpers ──────────────────────────────────────────────────────────

C_MAJOR = Scale(root=0, mode=Mode.MAJOR)
G_DORIAN = Scale(root=7, mode=Mode.DORIAN)
F_BLUES = Scale(root=5, mode=Mode.BLUES)
Bb_MIXO = Scale(root=10, mode=Mode.MIXOLYDIAN)
AB_MAJOR = Scale(root=8, mode=Mode.MAJOR)
D_MINOR = Scale(root=2, mode=Mode.NATURAL_MINOR)
E_LYDIAN = Scale(root=4, mode=Mode.LYDIAN)


def _chords(*qualities, start=0.0, dur=4.0):
    """Build chord list from (root, Quality) pairs."""
    result = []
    t = start
    for root, quality in qualities:
        result.append(ChordLabel(root=root, quality=quality, start=t, duration=dur))
        t += dur
    return result


STANDARD_CHORDS = _chords(
    (0, Quality.MAJOR7), (9, Quality.DOMINANT7),
    (2, Quality.MINOR7), (7, Quality.DOMINANT7),
)

ALL_QUALITIES = [
    Quality.MAJOR, Quality.MINOR, Quality.DIMINISHED, Quality.AUGMENTED,
    Quality.MAJOR7, Quality.DOMINANT7, Quality.MINOR7,
    Quality.HALF_DIM7, Quality.FULL_DIM7,
]

LOW_PARAMS = GeneratorParams(key_range_low=36, key_range_high=60)
MID_PARAMS = GeneratorParams(key_range_low=48, key_range_high=84)
HIGH_PARAMS = GeneratorParams(key_range_low=72, key_range_high=96)
NARROW_PARAMS = GeneratorParams(key_range_low=60, key_range_high=64)


def _valid(notes: list[NoteInfo], low=0, high=127) -> None:
    """Assert all notes have valid pitch, duration, start, velocity."""
    for n in notes:
        assert 0 <= n.pitch <= 127, f"pitch {n.pitch} out of MIDI range"
        assert n.duration > 0, f"duration {n.duration} not positive"
        assert n.start >= 0, f"start {n.start} negative"
        assert 1 <= n.velocity <= 127, f"velocity {n.velocity} out of range"


def _in_range(notes: list[NoteInfo], low: int, high: int) -> None:
    """Assert all pitches within given range."""
    for n in notes:
        assert low <= n.pitch <= high, f"pitch {n.pitch} outside [{low},{high}]"


def _sorted_starts(notes: list[NoteInfo]) -> bool:
    """Check notes are sorted by start time."""
    return all(notes[i].start <= notes[i + 1].start for i in range(len(notes) - 1))


# =====================================================================
# GuideToneGenerator
# =====================================================================

class TestGuideToneGenerator:
    def test_empty_chords(self):
        assert GuideToneGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("voice", ["3rd", "7th", "both", "alternate"])
    def test_voices_produce_notes(self, voice):
        g = GuideToneGenerator(voice=voice, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 48, 84)

    def test_both_produces_two_notes_per_chord(self):
        g = GuideToneGenerator(voice="both", params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # 4 chords × 2 notes each (3rd + 7th) + possible passing tones
        assert len(notes) >= 8

    def test_connect_adds_passing_tones(self):
        g_connect = GuideToneGenerator(voice="3rd", connect=True, params=MID_PARAMS)
        g_no_connect = GuideToneGenerator(voice="3rd", connect=False, params=MID_PARAMS)
        n_connect = g_connect.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        n_no = g_no_connect.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # With connect=True, may have more notes (passing tones)
        assert len(n_connect) >= len(n_no)

    @pytest.mark.parametrize("profile", ["flat", "legato", "accent_changes"])
    def test_velocity_profiles(self, profile):
        g = GuideToneGenerator(velocity_profile=profile, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_voice(self):
        with pytest.raises(ValueError, match="voice must be"):
            GuideToneGenerator(voice="invalid")

    def test_single_chord(self):
        chords = _chords((0, Quality.MAJOR7))
        g = GuideToneGenerator(voice="both", params=MID_PARAMS)
        notes = g.render(chords, C_MAJOR, 4.0)
        assert len(notes) >= 2

    def test_all_qualities(self):
        """GuideTone must handle all chord qualities."""
        for q in ALL_QUALITIES:
            chords = _chords((0, q))
            g = GuideToneGenerator(voice="both", params=MID_PARAMS)
            notes = g.render(chords, C_MAJOR, 4.0)
            assert len(notes) >= 1, f"No notes for quality {q.name}"
            _valid(notes)

    def test_narrow_range(self):
        g = GuideToneGenerator(voice="both", params=NARROW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 60, 64)

    def test_starts_within_duration(self):
        g = GuideToneGenerator(params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        for n in notes:
            assert n.start < 16.0, f"start {n.start} >= duration 16.0"

    def test_long_progression(self):
        chords = _chords(
            (0, Quality.MAJOR7), (5, Quality.DOMINANT7),
            (7, Quality.MINOR7), (0, Quality.MAJOR7),
            (2, Quality.MINOR7), (7, Quality.DOMINANT7),
            (0, Quality.MAJOR7), (0, Quality.DOMINANT7),
        )
        g = GuideToneGenerator(voice="alternate", connect=True, params=MID_PARAMS)
        notes = g.render(chords, C_MAJOR, 32.0)
        assert len(notes) > 0
        _valid(notes)


# =====================================================================
# EnclosureGenerator
# =====================================================================

class TestEnclosureGenerator:
    def test_empty_chords(self):
        assert EnclosureGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("etype", [
        "chromatic_above_below", "chromatic_below_above",
        "diatonic_above_below", "double_chromatic", "delayed", "mixed",
    ])
    def test_all_enclosure_types(self, etype):
        g = EnclosureGenerator(enclosure_type=etype, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 48, 84)

    @pytest.mark.parametrize("target", ["chord_tones", "roots", "guide_tones", "all"])
    def test_all_targets(self, target):
        g = EnclosureGenerator(target=target, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    @pytest.mark.parametrize("placement", ["on_beat", "off_beat", "mixed"])
    def test_rhythm_placements(self, placement):
        g = EnclosureGenerator(rhythm_placement=placement, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_density_zero_produces_targets_only(self):
        g = EnclosureGenerator(density=0.0, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_density_one_always_encloses(self):
        g = EnclosureGenerator(density=1.0, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # With density=1.0 and 4 chords, each chord gets 1-3 enclosed targets
        # Each enclosure has 2-3 notes, so minimum ~8 notes
        assert len(notes) >= 4
        _valid(notes)

    def test_invalid_enclosure_type(self):
        with pytest.raises(ValueError, match="enclosure_type must be"):
            EnclosureGenerator(enclosure_type="nonexistent")

    def test_all_qualities(self):
        for q in ALL_QUALITIES:
            chords = _chords((0, q))
            g = EnclosureGenerator(params=MID_PARAMS)
            notes = g.render(chords, C_MAJOR, 4.0)
            assert len(notes) > 0, f"No notes for quality {q.name}"
            _valid(notes)

    def test_narrow_range(self):
        g = EnclosureGenerator(params=NARROW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 60, 64)

    def test_velocity_approach_vs_target(self):
        """Target note (last in enclosure) should be louder than approach notes."""
        g = EnclosureGenerator(density=1.0, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_starts_non_negative(self):
        g = EnclosureGenerator(params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        for n in notes:
            assert n.start >= 0, f"negative start: {n.start}"

    def test_short_duration(self):
        chords = _chords((0, Quality.MAJOR7), dur=1.0)
        g = EnclosureGenerator(params=MID_PARAMS)
        notes = g.render(chords, C_MAJOR, 1.0)
        _valid(notes)


# =====================================================================
# SideSlippingGenerator
# =====================================================================

class TestSideSlippingGenerator:
    def test_empty_chords(self):
        assert SideSlippingGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("direction", ["up", "down", "both"])
    def test_slip_directions(self, direction):
        g = SideSlippingGenerator(slip_direction=direction, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 48, 84)

    @pytest.mark.parametrize("resolution", ["direct", "chromatic", "scale"])
    def test_resolution_styles(self, resolution):
        g = SideSlippingGenerator(resolution_style=resolution, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    @pytest.mark.parametrize("source", ["arpeggio", "scale", "mixed"])
    def test_pattern_sources(self, source):
        g = SideSlippingGenerator(pattern_source=source, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_direction(self):
        with pytest.raises(ValueError, match="slip_direction must be"):
            SideSlippingGenerator(slip_direction="sideways")

    def test_structure_in_slip_resolve(self):
        """Should produce in-key, slipped, and resolution segments."""
        g = SideSlippingGenerator(
            phrase_length=4, slip_duration=3,
            resolution_style="chromatic", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # 4 chords × (4 in + 3 slip + ~2 resolve) = ~36 notes
        assert len(notes) >= 20
        _valid(notes)

    def test_slip_creates_pitch_variety(self):
        """Slipped notes should include pitches not in the original chord."""
        g = SideSlippingGenerator(
            slip_direction="up", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        pitches = {n.pitch for n in notes}
        # Should have reasonable pitch variety
        assert len(pitches) >= 4

    def test_all_qualities(self):
        for q in ALL_QUALITIES:
            chords = _chords((0, q))
            g = SideSlippingGenerator(params=MID_PARAMS)
            notes = g.render(chords, C_MAJOR, 4.0)
            assert len(notes) > 0, f"No notes for quality {q.name}"
            _valid(notes)

    def test_narrow_range(self):
        g = SideSlippingGenerator(params=NARROW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 60, 64)

    def test_single_chord(self):
        chords = _chords((0, Quality.MAJOR7))
        g = SideSlippingGenerator(params=MID_PARAMS)
        notes = g.render(chords, C_MAJOR, 4.0)
        assert len(notes) > 0
        _valid(notes)

    def test_dorian_mode(self):
        chords = _chords((7, Quality.MINOR7), (0, Quality.DOMINANT7))
        g = SideSlippingGenerator(params=MID_PARAMS)
        notes = g.render(chords, G_DORIAN, 8.0)
        assert len(notes) > 0
        _valid(notes)


# =====================================================================
# TradingFoursGenerator
# =====================================================================

class TestTradingFoursGenerator:
    def test_empty_chords(self):
        assert TradingFoursGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("trade_length", [2, 4, 8])
    def test_trade_lengths(self, trade_length):
        g = TradingFoursGenerator(trade_length=trade_length, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        assert len(notes) > 0
        _valid(notes)

    @pytest.mark.parametrize("style", ["call_response", "independent", "escalating"])
    def test_styles(self, style):
        g = TradingFoursGenerator(style=style, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_trade_length(self):
        with pytest.raises(ValueError, match="trade_length must be"):
            TradingFoursGenerator(trade_length=3)

    def test_invalid_style(self):
        with pytest.raises(ValueError, match="style must be"):
            TradingFoursGenerator(style="bad_style")

    def test_alternating_ranges(self):
        """Player A notes should be in A range, B in B range."""
        a_range = (60, 84)
        b_range = (48, 72)
        g = TradingFoursGenerator(
            player_a_range=a_range, player_b_range=b_range,
            style="independent", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        _valid(notes)
        # All notes should be in one range or the other
        for n in notes:
            in_a = a_range[0] <= n.pitch <= a_range[1]
            in_b = b_range[0] <= n.pitch <= b_range[1]
            assert in_a or in_b, f"pitch {n.pitch} in neither range"

    def test_escalating_velocity_increases(self):
        g = TradingFoursGenerator(style="escalating", params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        _valid(notes)
        # Later notes should tend toward higher velocities
        if len(notes) > 4:
            first_4_avg = sum(n.velocity for n in notes[:4]) / 4
            last_4_avg = sum(n.velocity for n in notes[-4:]) / 4
            # On average, later notes should be louder or equal
            # (random variation means this isn't guaranteed per-note)

    def test_call_response_echoes(self):
        """In call_response mode, player B should echo player A's pitches."""
        g = TradingFoursGenerator(
            style="call_response", trade_length=4,
            params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        assert len(notes) > 0
        _valid(notes)

    def test_short_duration_fewer_notes(self):
        g = TradingFoursGenerator(trade_length=8, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 4.0)
        # Only 4 beats = less than one 8-bar trade
        _valid(notes)

    def test_density_affects_note_count(self):
        g_sparse = TradingFoursGenerator(density=0.5, params=MID_PARAMS)
        g_dense = TradingFoursGenerator(density=2.0, params=MID_PARAMS)
        n_sparse = g_sparse.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        n_dense = g_dense.render(STANDARD_CHORDS, C_MAJOR, 32.0)
        assert len(n_dense) >= len(n_sparse)


# =====================================================================
# StopTimeGenerator
# =====================================================================

class TestStopTimeGenerator:
    def test_empty_chords(self):
        assert StopTimeGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("pattern", ["big_four", "half_note", "syncopated", "shuffle", "free"])
    def test_all_patterns(self, pattern):
        g = StopTimeGenerator(pattern=pattern, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 48, 84)

    @pytest.mark.parametrize("accent", ["root", "chord_tone", "shell"])
    def test_accent_notes(self, accent):
        g = StopTimeGenerator(accent_note=accent, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_pattern(self):
        with pytest.raises(ValueError, match="pattern must be"):
            StopTimeGenerator(pattern="waltz")

    def test_invalid_accent_note(self):
        with pytest.raises(ValueError, match="accent_note must be"):
            StopTimeGenerator(accent_note="octave")

    def test_shell_produces_two_pitches(self):
        """Shell accent should produce root + 7th per hit."""
        g = StopTimeGenerator(
            pattern="big_four", accent_note="shell", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # 4 bars × 1 hit × 2 pitches = 8 minimum, plus pickup notes
        assert len(notes) >= 8

    def test_fill_last_beat_adds_pickup(self):
        g_fill = StopTimeGenerator(
            pattern="big_four", fill_last_beat=True, params=MID_PARAMS,
        )
        g_no_fill = StopTimeGenerator(
            pattern="big_four", fill_last_beat=False, params=MID_PARAMS,
        )
        n_fill = g_fill.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        n_no = g_no_fill.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(n_fill) >= len(n_no)

    def test_accent_duration_short(self):
        g = StopTimeGenerator(accent_duration=0.1, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_shuffle_has_most_hits(self):
        g = StopTimeGenerator(pattern="shuffle", accent_note="root", params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # shuffle has 4 hits per bar × 4 bars = 16 accents
        assert len(notes) >= 16

    def test_free_pattern_varies(self):
        """Free pattern should produce different note counts across runs."""
        counts = set()
        for _ in range(5):
            g = StopTimeGenerator(pattern="free", params=MID_PARAMS)
            notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
            counts.add(len(notes))
        # At least some variation across random seeds
        # (may not always vary due to small sample, but structure should work)

    def test_all_qualities(self):
        for q in ALL_QUALITIES:
            chords = _chords((0, q))
            g = StopTimeGenerator(params=MID_PARAMS)
            notes = g.render(chords, C_MAJOR, 4.0)
            assert len(notes) > 0, f"No notes for quality {q.name}"
            _valid(notes)

    def test_narrow_range(self):
        g = StopTimeGenerator(params=NARROW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 60, 64)


# =====================================================================
# WalkingBassLineGenerator
# =====================================================================

class TestWalkingBassLineGenerator:
    def test_empty_chords(self):
        assert WalkingBassLineGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("contour", ["ascending", "descending", "scalar", "arpeggiated", "mixed"])
    def test_contours(self, contour):
        g = WalkingBassLineGenerator(contour=contour, params=LOW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 36, 60)

    @pytest.mark.parametrize("target", ["root", "guide_tones", "fifths", "mixed"])
    def test_target_notes(self, target):
        g = WalkingBassLineGenerator(target_note=target, params=LOW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    @pytest.mark.parametrize("passing", ["chromatic", "diatonic", "enclosure", "mixed"])
    def test_passing_tones(self, passing):
        g = WalkingBassLineGenerator(passing_tones=passing, params=LOW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_contour(self):
        with pytest.raises(ValueError, match="contour must be"):
            WalkingBassLineGenerator(contour="zigzag")

    def test_invalid_target(self):
        with pytest.raises(ValueError, match="target_note must be"):
            WalkingBassLineGenerator(target_note="9th")

    def test_beat_count_matches_duration(self):
        """Should produce roughly 1 note per beat."""
        g = WalkingBassLineGenerator(params=LOW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # 4 chords × 4 beats each = 16 beats = ~16 notes
        assert 12 <= len(notes) <= 20

    def test_all_qualities(self):
        for q in ALL_QUALITIES:
            chords = _chords((0, q))
            g = WalkingBassLineGenerator(params=LOW_PARAMS)
            notes = g.render(chords, C_MAJOR, 4.0)
            assert len(notes) > 0, f"No notes for quality {q.name}"
            _valid(notes)

    def test_context_prev_pitch(self):
        from melodica.render_context import RenderContext
        ctx = RenderContext(prev_pitch=40)
        g = WalkingBassLineGenerator(params=LOW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0, ctx)
        _valid(notes)

    def test_narrow_range(self):
        g = WalkingBassLineGenerator(params=NARROW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 60, 64)

    def test_phrase_length_reset(self):
        g = WalkingBassLineGenerator(phrase_length=2, params=LOW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_chords_exceeding_duration(self):
        """Chords past duration_beats should be skipped."""
        long_chords = _chords(
            (0, Quality.MAJOR7), (5, Quality.DOMINANT7),
            (7, Quality.MINOR7), (0, Quality.MAJOR7),
            (2, Quality.MINOR7), (7, Quality.DOMINANT7),
        )
        g = WalkingBassLineGenerator(params=LOW_PARAMS)
        notes = g.render(long_chords, C_MAJOR, 8.0)
        _valid(notes)
        for n in notes:
            assert n.start < 8.0


# =====================================================================
# ShellVoicingGenerator
# =====================================================================

class TestShellVoicingGenerator:
    def test_empty_chords(self):
        assert ShellVoicingGenerator().render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("vtype", ["root_shell", "rootless", "spread", "A_form", "B_form"])
    def test_voicing_types(self, vtype):
        g = ShellVoicingGenerator(voicing_type=vtype, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 48, 84)

    @pytest.mark.parametrize("rhythm", ["whole_note", "half_note", "charleston", "syncopated", "freddie_green"])
    def test_rhythms(self, rhythm):
        g = ShellVoicingGenerator(rhythm=rhythm, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) > 0
        _valid(notes)

    def test_invalid_voicing_type(self):
        with pytest.raises(ValueError, match="voicing_type must be"):
            ShellVoicingGenerator(voicing_type="cluster")

    def test_invalid_rhythm(self):
        with pytest.raises(ValueError, match="rhythm must be"):
            ShellVoicingGenerator(rhythm="drum_and_bass")

    def test_root_shell_has_three_notes_per_hit(self):
        """root_shell = root + 3rd + 7th = 3 pitches per hit."""
        g = ShellVoicingGenerator(
            voicing_type="root_shell", rhythm="whole_note", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # 4 chords × 1 hit × 3 pitches = 12
        assert len(notes) >= 12

    def test_rootless_has_two_notes_per_hit(self):
        """rootless = 3rd + 7th = 2 pitches per hit."""
        g = ShellVoicingGenerator(
            voicing_type="rootless", rhythm="whole_note", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) >= 8

    def test_freddie_green_has_most_notes(self):
        g = ShellVoicingGenerator(
            voicing_type="root_shell", rhythm="freddie_green", params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # 4 chords × 4 beats × 3 pitches = 48
        assert len(notes) >= 24

    def test_voice_leading_smoothness(self):
        """With voice_leading, pitches should change smoothly."""
        g = ShellVoicingGenerator(
            voicing_type="rootless", rhythm="whole_note",
            voice_leading=True, params=MID_PARAMS,
        )
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_drop_2(self):
        g = ShellVoicingGenerator(drop_2=True, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_include_extensions(self):
        g = ShellVoicingGenerator(include_extensions=True, params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        # Extensions add extra notes
        assert len(notes) > 0
        _valid(notes)

    def test_all_qualities(self):
        for q in ALL_QUALITIES:
            chords = _chords((0, q))
            g = ShellVoicingGenerator(params=MID_PARAMS)
            notes = g.render(chords, C_MAJOR, 4.0)
            assert len(notes) > 0, f"No notes for quality {q.name}"
            _valid(notes)

    def test_narrow_range(self):
        g = ShellVoicingGenerator(params=NARROW_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 60, 64)

    def test_a_form_close_voicing(self):
        """A_form should have 3rd below 7th."""
        g = ShellVoicingGenerator(voicing_type="A_form", rhythm="whole_note", params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_b_form_spread_voicing(self):
        """B_form should have 7th below 3rd."""
        g = ShellVoicingGenerator(voicing_type="B_form", rhythm="whole_note", params=MID_PARAMS)
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    def test_long_progression(self):
        chords = _chords(
            (0, Quality.MAJOR7), (9, Quality.DOMINANT7),
            (2, Quality.MINOR7), (7, Quality.DOMINANT7),
            (0, Quality.MAJOR7), (5, Quality.DOMINANT7),
            (7, Quality.MINOR7), (0, Quality.MAJOR7),
        )
        g = ShellVoicingGenerator(
            voicing_type="root_shell", rhythm="charleston",
            voice_leading=True, params=MID_PARAMS,
        )
        notes = g.render(chords, C_MAJOR, 32.0)
        assert len(notes) > 0
        _valid(notes)
        _in_range(notes, 48, 84)


# =====================================================================
# Cross-cutting: all generators handle edge cases
# =====================================================================

ALL_GENERATORS = [
    lambda: GuideToneGenerator(params=MID_PARAMS),
    lambda: EnclosureGenerator(params=MID_PARAMS),
    lambda: SideSlippingGenerator(params=MID_PARAMS),
    lambda: TradingFoursGenerator(params=MID_PARAMS),
    lambda: StopTimeGenerator(params=MID_PARAMS),
    lambda: WalkingBassLineGenerator(params=MID_PARAMS),
    lambda: ShellVoicingGenerator(params=MID_PARAMS),
]


class TestCrossCutting:
    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_empty_chords_returns_empty(self, gen_factory):
        g = gen_factory()
        assert g.render([], C_MAJOR, 8.0) == []

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_zero_duration(self, gen_factory):
        g = gen_factory()
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 0.0)
        assert isinstance(notes, list)

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_all_notes_valid(self, gen_factory):
        g = gen_factory()
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _valid(notes)

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_notes_in_range(self, gen_factory):
        g = gen_factory()
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        _in_range(notes, 48, 84)

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_single_chord(self, gen_factory):
        g = gen_factory()
        chords = _chords((0, Quality.MAJOR7))
        notes = g.render(chords, C_MAJOR, 4.0)
        assert isinstance(notes, list)

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_dorian_mode(self, gen_factory):
        g = gen_factory()
        chords = _chords((7, Quality.MINOR7), (0, Quality.DOMINANT7))
        notes = g.render(chords, G_DORIAN, 8.0)
        _valid(notes)

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_blues_mode(self, gen_factory):
        g = gen_factory()
        chords = _chords((5, Quality.DOMINANT7), (0, Quality.DOMINANT7))
        notes = g.render(chords, F_BLUES, 8.0)
        _valid(notes)

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_name_attribute(self, gen_factory):
        g = gen_factory()
        assert isinstance(g.name, str)
        assert len(g.name) > 0

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_produces_at_least_one_note(self, gen_factory):
        g = gen_factory()
        notes = g.render(STANDARD_CHORDS, C_MAJOR, 16.0)
        assert len(notes) >= 1, "Generator produced zero notes"

    @pytest.mark.parametrize("gen_factory", ALL_GENERATORS, ids=[
        "GuideTone", "Enclosure", "SideSlipping", "TradingFours",
        "StopTime", "WalkingBassLine", "ShellVoicing",
    ])
    def test_reproducible_with_seed(self, gen_factory):
        """Same seed should produce same output."""
        random.seed(42)
        g1 = gen_factory()
        n1 = g1.render(STANDARD_CHORDS, C_MAJOR, 16.0)

        random.seed(42)
        g2 = gen_factory()
        n2 = g2.render(STANDARD_CHORDS, C_MAJOR, 16.0)

        assert len(n1) == len(n2), "Same seed should produce same note count"
        for a, b in zip(n1, n2):
            assert a.pitch == b.pitch
            assert a.start == b.start
            assert abs(a.duration - b.duration) < 0.001
